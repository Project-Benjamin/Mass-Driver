"""Audited retail donors and isolated resources for Rico Chapter 2.

Coordinates are (x, z, layer-0 triangle). They were checked against the
original retail walkmesh and its entry-connected triangle component.
These metadata do not retain the donor's retail story managers or actions.
"""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Callable, Mapping

from shared.tools.xgfield import parse_field


class ChapterTwoResourceError(ValueError):
    """A Chapter 2 donor, target allocation, or resource changed."""


# Every target is a 24-byte CDMAKE dummy on retail/PW Disc 2. Disc 1 has no
# paired empty fields: these twelve fields are deliberately disposable in this
# self-contained anthology, whose routes never enter their original scenes.
# This allocation is not compatible with ordinary retail-save progression.
WORLD_FIELDS = {
    "intake": 68,
    "commons": 69,
    "baptism": 70,
    "prep": 71,
    "sewer_entry": 72,
    "sewer_hub": 73,
    "sewer_key": 74,
    "sewer_drain": 75,
    "central": 76,
    "arena": 77,
    "bar": 78,
    "street": 79,
}

# Field 213 entry 3 places Fei on the hospital mattress: triangle 94 is
# Y=-24, matching static bed model 0 (X[-352,-220], Z[-308,-220]). OP19/1A
# resolve that actual raised surface; the old rest-return point was Y=0.
ARRIVAL_PATIENT = (-291, -259, 94)
# Native entries 5/6 are the adjacent floor, with room for both witnesses.
ARRIVAL_ATTENDANT = (-200, -175, 92)
ARRIVAL_GUARD = (-162, -261, 90)
# Native e14:s7 final bedside shot, PC 0FE5 / 0FEE, in x,z,y order.
ARRIVAL_CAMERA_TARGET = (-205, -201, -64)
ARRIVAL_CAMERA_EYE = (-1003, -748, -420)

# NPC positions use a landmark of the same name. Entity/bank refer to the
# donor's original actor; optional palette identifies native FE15 variants.
# "exit" landmarks are walkable approaches, not instructions to reuse retail
# transition scripts. The engine must emit the anthology's explicit targets.
ROOM_SPECS = {
    "bar": {
        "donor": 217, "entry": (-67, -44, 234), "native_entries": True,
        "landmarks": {"room_exit": (240, -330, 18), "street_exit": (-23, -44, 68)},
        "npcs": {}, "native_actions": {"room_exit": 3, "street_exit": 2},
    },
    "street": {
        "donor": 196, "entry": (787, -1403, 146), "native_entries": True,
        "landmarks": {"bar_exit": (787, -1403, 146),
                      "east_dorm": (416, 220, 201), "west_dorm": (-453, 214, 335)},
        "npcs": {}, "native_actions": {"bar_exit": 31, "east_dorm": 29, "west_dorm": 34},
    },
    "intake": {
        "donor": 213, "entry": ARRIVAL_PATIENT,
        "landmarks": {"patient": ARRIVAL_PATIENT, "doctor": ARRIVAL_ATTENDANT,
                      "guard": ARRIVAL_GUARD, "exit": (311, 41, 104)},
        "npcs": {"doctor": {"entity": 8, "bank": 2, "palette": 1},
                 # The intake guard installer supplies retail 230's bank.
                 "guard": {"entity": 10, "bank": 0}},
        "cast": {"rico": ARRIVAL_PATIENT[:2], "fei": ARRIVAL_PATIENT[:2]},
    },
    "commons": {
        "donor": 211, "entry": (394, 86, 124), "native_entries": True,
        "landmarks": {"worker": (169, 176, 62), "battler": (257, 116, 76),
                      "prisoner": (-3, -108, 30), "fei": (-406, -149, 175),
                      "citan": (-335, -155, 1),
                      "official": (490, -229, 114), "yard_exit": (250, -30, 102),
                      "east_exit": (474, 86, 125),
                      "room_exit": (-502, 89, 220), "sewer_exit": (-397, 155, 189)},
        "npcs": {"worker": {"entity": 14, "bank": 0},
                 "battler": {"entity": 18, "bank": 1},
                 "prisoner": {"entity": 16, "bank": 0},
                 "official": {"entity": 10, "bank": 2}},
        "cast": {"fei": (-406, -149), "citan": (-335, -155)},
        "native_actions": {"room_exit": 4, "east_exit": 5},
    },
    "baptism": {
        "donor": 199, "entry": (-1655, 169, 177),
        "landmarks": {"baptism": (-1655, 169, 177), "rico": (-1799, -327, 175),
                      "exit": (-1965, -380, 175)},
        "npcs": {},
    },
    "prep": {
        "donor": 223, "entry": (-800, 65, 0),
        "landmarks": {"stier": (-385, -3, 6),
                      "exit": (-880, 65, 0)},
        # install_prep_hammer supplies the exact Hammer actor/sprite bank.
        "npcs": {"stier": {"entity": 4, "bank": 0}},
    },
    "sewer_entry": {
        "donor": 239, "entry": (480, -171, 168),
        "landmarks": {"message": (1187, 606, 202), "slime": (-438, -1124, 40),
                      "forward": (325, 1682, 175), "exit": (560, -171, 157)},
        "npcs": {},
    },
    "sewer_hub": {
        "donor": 240, "entry": (-936, 2325, 182),
        "landmarks": {"bell": (54, 2377, 225), "forward": (1934, 1403, 124),
                      "key_exit": (-2210, 1805, 19), "exit": (-1016, 2315, 257),
                      "gramps": (-40, 180, 50)},
        "npcs": {"gramps": {"entity": 42, "bank": 0}},
    },
    "sewer_key": {
        "donor": 241, "entry": (397, -314, 134),
        "landmarks": {"key": (-1468, 1055, 194), "burnt": (260, -1885, 164),
                      "plant": (1923, 812, 122),
                      "exit": (397, -234, 46)},
        "npcs": {},
    },
    "sewer_drain": {
        "donor": 242, "entry": (0, 47, 179),
        "landmarks": {"drain": (0, -80, 119), "exit": (0, 127, 20)},
        "npcs": {},
    },
    "central": {
        "donor": 231, "entry": (-84, -291, 12),
        "landmarks": {"checkpoint": (-84, 34, 7), "concealment": (-175, 32, 7),
                      "gate": (397, 24, 19), "exit": (397, 24, 19)},
        "npcs": {},
    },
    "arena": {
        "donor": 225, "entry": (-500, 0, 379),
        "landmarks": {"rico": (-500, 0, 379), "fei": (500, 0, 473),
                      "center": (0, 0, 212)},
        "npcs": {},
        "cast": {"rico": (-500, 0), "fei": (500, 0)},
    },
}

# Header-bound 3D models whose original coordinates/rotation are sufficient.
# OP23 hides these models too: their sanitized init must omit that opcode.
# Central's corridor is built from scripted models12..36, while the sewer
# lists contain doors, grates and fixed props. Their native managers/actions
# remain retired. Baptism31..45 are actor-attached models with F9/FE1C staging;
# they intentionally stay hidden rather than appear at uninitialized origins.
SAFE_STATIC_MODELS = {
    "bar": (), "street": (),
    "intake": (2,), "commons": (3,), "baptism": (), "prep": (),
    "sewer_entry": (14, 15, 16, 17, 18, 19, 22),
    "sewer_hub": (4, 5, 6, 7, 8, 9, 13, 14, 15, 18, 19, 20),
    "sewer_key": (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 18, 19),
    "sewer_drain": (4,), "central": tuple(range(12, 37)), "arena": (),
}
for _role, _models in SAFE_STATIC_MODELS.items():
    ROOM_SPECS[_role]["safe_static_models"] = _models


def fields_for(disc: int, *, combined: bool = False) -> dict[str, int]:
    if disc not in (1, 2) or (combined and disc != 2):
        raise ChapterTwoResourceError("Chapter 2 needs Disc 1/2; combined uses Disc 2")
    return dict(WORLD_FIELDS)


REDRUM_FORMATION_SLOT = 15
REDRUM_FORMATION = bytes.fromhex(
    "43 C0 09 00 00 00 00 00 00 FF FF FF FF FF FF FF "
    "00 00 00 00 FF FF FF FF 00 00 00 00 FF FF FF FF"
)
REDRUM_RESOURCE_IDENTITIES = {
    2752: (4919, "3f58e20dddd2837cb8fddd2b4f35183ee4121e88bdf1e62a4fb7e186027c12b4"),
    2753: (131836, "17efb6aaa5640bdbe605ddfa21d59f799557db8e9a7b9a33ef3d0442ad7436ed"),
    2793: (209748, "8c67032ccc61947a5f8ad7d6d1b4f125815b3c8b9c16c3233c244e865a33c9f3"),
    2794: (2168, "9e421f613be489804cbc4472d8d4bff4e596314b0e3db8eb813767a1171c8233"),
}


def prepare_redrum_resources(
    canonical_reader: Callable[[int], bytes],
    *,
    existing: Mapping[int, bytes] | None = None,
) -> dict[int, bytes]:
    """Return verified local boss/arena copies; keep existing identical data.

    2752 contains the original Redrum stats/AI (4242 HP), 2753 embeds its
    on-foot sprite/animation, and 2793/2794 provide arena 9. No global battle
    overlays or player/enemy attack archives are replaced by this helper.
    """
    result = {}
    for resource, expected in REDRUM_RESOURCE_IDENTITIES.items():
        data = canonical_reader(resource)
        if (len(data), hashlib.sha256(data).hexdigest()) != expected:
            raise ChapterTwoResourceError(f"Redrum resource {resource} changed")
        if existing is not None and resource in existing:
            if existing[resource] != data:
                raise ChapterTwoResourceError(f"Conflicting Redrum resource {resource}")
        else:
            result[resource] = data
    return result


def install_redrum_formation(encounters: bytes, *, slot: int = 15) -> bytes:
    """Install the exact native boss formation and disable random fights."""
    if len(encounters) != 528 or type(slot) is not int or not 0 <= slot < 16:
        raise ChapterTwoResourceError("Expected 528-byte encounters and formation 0..15")
    result = bytearray(encounters)
    result[slot * 32:(slot + 1) * 32] = REDRUM_FORMATION
    result[512:] = bytes(16)
    return bytes(result)


# Complete bundle/graphics identities from the original retail Disc 1.
DONOR_RESOURCE_IDENTITIES = {
 998: (154232, '09b2a7c713c94184fcd528856395e4207d2ee81863b5018b77077eabb5d0124b'),
 999: (442368, 'a718e5c651339ab572fe342dc5003999adaa280f6abbe0d383ff53c84f6eada2'),
 1040: (62100, '43505f75dd85061fcf7a30fe0e97cfb00b5fe62dc7f0b130ce460a3796ed6e73'),
 1041: (438272, '4090d5a895d20ce23b20462fed7e90a84bf10bc34949212b3d23d8e56a656989'),
 1004: (160504, 'bc3a0700a6eaca262d8350bd3bad3b7943bc475ed46d10fbc066aca6d6e12ba9'),
 1005: (311296, '09b85a270a107d425c532ec5d9206f541e4cdb13b2cab503926e0a026f064865'),
 1028: (68940, 'c66d6e627fc9ed5a47f6d307e4f70617078953a6ce7487cd15cc3d025ab7d826'),
 1029: (491520, '3b73499e68f5300fe653ff46a5c2869728cda91a82742bfaa88882e39309da59'),
 1032: (77332, '3c0b104d070a6355a1b3b43ef4af940fb22c9b68ce44762fbb7ec11266c810c3'),
 1033: (436224, '0a4d2e8b715a7bf584251f2c4a4f728d5022970f896d97c49193b70a051e93f6'),
 1052: (67128, 'b9925d5672baed18ed1dfa6cc64931defe90d3aca8152ee3905f3298439b62aa'),
 1053: (266240, '3d4a778650dccf6770fd26e0fbebba763e638b8b1b9646c01bbb27bd976c9267'),
 1056: (76704, '2cbca37795aec0230d6b843a17cbe2ef02bec030ab7b6aae4f647ee879614f27'),
 1057: (79872, '08129c6686ceb20f8a4b3a11ef8956ab0d12e4dd75a28ae0300405a1aac1c130'),
 1068: (91468, 'a6497dd79fc68ca3ace273c7ed02a7d1aa93a226d0980572a62caca0239b7008'),
 1069: (272384, '898820586fd30c479495dca8faecfe2dbde56ac4803a5b093859b6fec4e250bc'),
 1084: (92320, '5de68110340d8d98fb13b40c13e32266a0adeedf579c47710de3f7082be51123'),
 1085: (241664, '26631b61c890b30d52b5efc2c937a40a5be641fdbb8da9d2198bc508a401b238'),
 1086: (107980, '1fe15ec26d26455bb66e0dc301ece0ffca61a11619c19bd9fc17cfee67be5f28'),
 1087: (264192, 'a1a63d1cd3b3e1724d79f8b6dae7d3575b992bfb5a505735c7a0712d2658dbb3'),
 1088: (82832, '043b5b47cbb510243a287fee5da388e4bd6fc72e5c7bba851f974d01ee2baa1f'),
 1089: (333824, '6eae13bb58d612f7806ade5ffb6b6cb0aa534f343f71fc1bd69946d86da3763a'),
 1090: (59372, 'e87979418d43705a76ac1195d39caea9a1c44a4b33afe96a280eee5ca6fc20af'),
 1091: (274432, 'b1ee4d9f905997fa8b9cc12ba6d89808cd2349469978d7ca072254543811c3c7')}

# Original Disc 1 resources explicitly displaced by WORLD_FIELDS.
DISC_ONE_DISPOSABLE_IDENTITIES = {
 762: (64356, 'cae9165a115f9955bf5eaf92732d231cf27f640f3ee21b4f9474761d101369dd'),
 763: (387072, 'bcff0318e1ae853b1bdda754e9e40b28422c6a4039d43dc517250377df737f84'),
 764: (177968, '080d9ce92267a963a721f1b1acb830e7f255da4ee9b47a571484ee61a13848cb'),
 765: (444416, 'f15b1cb4f4d87586276b4ff66bf3fe1010787092aeac9ae13350e6f24a9b7a14'),
 742: (110928, '1ce97684b47409ef92b65a4b0e80eb77ab85dca564f7ddd4d973c2697a5892ff'),
 743: (268288, '5cced3f20502d5c3c2249a3eef34a704c31b24ad66da1402871267dc149159c4'),
 744: (135864, '34ac3eca001aa9158424c45341aeb767499238335c0b8239db47c868f3e14dc3'),
 745: (299008, '8c89e1101eae48a1df7e02396fafb9885ada6cbd780b98aa99734b376f55a936'),
 746: (123672, '92c9c1ff09ebac87d1164d1fee4fe94e9c30582e558ea7449ee531d401c88f0e'),
 747: (131072, 'af8ab54a597b2a145af35309b46e8496cb5aa509cd5add1fe8062b9cdb3b3be9'),
 748: (86596, '959feb6eb6e2c4d0ca9004b31072faaeeb48df87c3e7f2f70b501ca6de10db1b'),
 749: (278528, 'c02bc3b2101a6384700ca20749d25c1f4c67cf55040103dafbd99473348988fb'),
 750: (41976, '4178c1b5d15e027ef4577711313388a4e79310e670954b935aed0c3c895ff12f'),
 751: (147456, '78d370c61f33c839f1b953e2d6f17ef797b36e086e08beefd84f5846ee0605bb'),
 752: (60092, '43bc7e883be51aa56a86d99f3e1a85d07e2b1b5ab5663f3824fe68eba9990afd'),
 753: (503808, '32ef1a161000de88f3f6b83869c23ad06daecc04fc669f8d1260b759c07feaf7'),
 754: (138120, 'ed19a4dfa8bb352f1f319a45464d05099e069ceabe2d0ba0c6ba6e8213bac954'),
 755: (327680, 'c8b99b1210d4abec2d0dae75c97fa622b7aa66b18b5a56bc347546726f8cad6f'),
 756: (172716, 'e1930bc89e24d1e9c46f0ca9b1735e1dba86b4224558bb25e606aee82a8a86ac'),
 757: (344064, '109b84fa67004484be2c8400fcd91693a67742a2688b727c5f5c2225381c7659'),
 758: (93660, 'ece74c5f4a532e5ae65cb6ebb4919ceb52311d1873abe1a24b151dcca03b4747'),
 759: (374784, '85b4fd0cfdf039c30bfa079f328097e35b428deb72729a1b62350cb2de525c08'),
 760: (23020, 'a92e58773d529e13c2a0a5b16ffc1b00a83d2363b3b7996d16236fba114c4c6f'),
 761: (147456, '48bb1df5fcadbe628ab01614e37c3cde884cf9f7c06be73bec77d35d819bc38a')}

DISC_TWO_DUMMY_IDENTITY = (24, "aafefb97ceb8e4667c719b99c4250b286e03087315b61848d196300140a95a2c")


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


def _layer_zero_geometry(walkmesh: bytes):
    count = struct.unpack_from("<I", walkmesh, 4)[0] // 14
    triangle_offset, vertex_offset = struct.unpack_from("<II", walkmesh, 0x18)
    triangles, neighbours = [], []
    for index in range(count):
        record = triangle_offset + index * 14
        indices = struct.unpack_from("<3H", walkmesh, record)
        triangles.append(tuple(struct.unpack_from("<hhh", walkmesh, vertex_offset + vertex * 8)
                               for vertex in indices))
        neighbours.append(tuple(n for n in struct.unpack_from("<3H", walkmesh, record + 6)
                                if n < count))
    return triangles, neighbours


def _inside(point: tuple[int, int], triangle) -> bool:
    x, z = point
    crosses = [(b[0] - a[0]) * (z - a[2]) - (b[2] - a[2]) * (x - a[0])
               for a, b in zip(triangle, (*triangle[1:], triangle[0]))]
    return all(value >= 0 for value in crosses) or all(value <= 0 for value in crosses)


def validate_room_geometry(role: str, bundle: bytes) -> dict[str, int]:
    """Check landmarks and cast against the entry-connected native floor."""
    spec = ROOM_SPECS[role]
    parsed = parse_field(bundle)
    triangles, neighbours = _layer_zero_geometry(parsed.parts[1].data)
    entry_triangle = spec["entry"][2]
    connected, pending = {entry_triangle}, [entry_triangle]
    while pending:
        for neighbour in neighbours[pending.pop()]:
            if neighbour not in connected:
                connected.add(neighbour)
                pending.append(neighbour)
    for name, (x, z, triangle) in {"entry": spec["entry"], **spec["landmarks"]}.items():
        if triangle not in connected or not _inside((x, z), triangles[triangle]):
            raise ChapterTwoResourceError(f"{role}:{name} is outside the reachable audited floor")
    for name, point in spec.get("cast", {}).items():
        if not any(_inside(point, triangles[n]) for n in connected):
            raise ChapterTwoResourceError(f"{role}:{name} cast is outside the reachable floor")
    # NPC indices address the actor-control bank. The separate sprite archive
    # need not have the same count (commons uses external graphics entirely).
    bank_count = struct.unpack_from("<I", parsed.parts[3].data)[0]
    for name, actor in spec["npcs"].items():
        if name not in spec["landmarks"] or not 0 <= actor["bank"] < bank_count:
            raise ChapterTwoResourceError(f"{role}:{name} references an absent native NPC bank")
    for entity in spec["safe_static_models"]:
        if struct.unpack_from("<H", parsed.header, 0x190 + 16 * entity)[0] & 0x40:
            raise ChapterTwoResourceError(f"{role}:static model {entity} is a sprite/script actor")
    return {"triangles": len(triangles), "connected": len(connected),
            "landmarks": len(spec["landmarks"])}


def validate_allocations(disc1) -> dict[str, object]:
    """Pin all retail donors and the explicitly disposable Disc 1 targets.

    The reader follows build.DiscReader's canonical(id) contract. Disc 2
    dummy allocation checks are separate because its retail donors differ.
    """
    if getattr(disc1, "disc", 1) != 1:
        raise ChapterTwoResourceError("Donor/allocation validation requires original retail Disc 1")
    for resource, expected in {**DONOR_RESOURCE_IDENTITIES, **DISC_ONE_DISPOSABLE_IDENTITIES}.items():
        if _identity(disc1.canonical(resource)) != expected:
            raise ChapterTwoResourceError(f"Chapter 2 donor/allocation resource {resource} changed")
    rooms = {role: validate_room_geometry(role, disc1.canonical(606 + 2 * spec["donor"]))
             for role, spec in ROOM_SPECS.items()}
    return {"fields": dict(WORLD_FIELDS), "rooms": rooms,
            "disc_one_allocation": "explicitly disposable standalone anthology fields"}


def validate_disc_two_allocations(canonical_reader: Callable[[int], bytes]) -> None:
    """Reject overwriting any non-dummy Disc 2 field in the reserved range."""
    for field in WORLD_FIELDS.values():
        for resource in (606 + 2 * field, 607 + 2 * field):
            if _identity(canonical_reader(resource)) != DISC_TWO_DUMMY_IDENTITY:
                raise ChapterTwoResourceError(f"Chapter 2 Disc 2 target {resource} is not the audited dummy")


def battle_resources(disc1) -> dict[int, bytes]:
    """Build integration adapter for the four isolated Redrum resources."""
    return prepare_redrum_resources(disc1.canonical)


HAMMER_SOURCE_IDENTITY = (122892, "61c0a85ede3b528d77252808ebc66238ee5d938244f21e36cb934f4470a54895")
HAMMER_BANK_IDENTITIES = {
    3: (5788, "8efce6f4757622e7b060bffc5f5d1a241f457ab527f580f51c8e7f6b19fee910"),
    4: (29196, "c50aa038b697ba4f34567991b49eaf05afd1d17162a144fc200b9da20c663e3e"),
}
PREP_REPLACED_BANK_IDENTITIES = {
    3: (3720, "869a2722da8169f36b373932e749c8b417b05fdb06c7e24064fc7cda2a83eb13"),
    4: (28940, "929afe75b6af775aa479087fc77fa9db33d26d846ea4891ec9b0fe11b6efa0da"),
}


def install_prep_hammer(prep_bundle: bytes, hammer_source_bundle: bytes) -> bytes:
    """Put authentic Hammer in prep's bank0, preserving its native VRAM cell.

    Field223's replaced atlas occupies64x226 words at(832,0); Hammer needs
    64x228 in the same64x256 cell. Its actor/control bank includes the palette.
    No model, walkmesh, script, header mapping or external graphics changes.
    """
    from modules.mass_driver import build as native
    from shared.tools.xgfield import build_field_preserving

    if _identity(prep_bundle) != DONOR_RESOURCE_IDENTITIES[606 + 2 * 223]:
        raise ChapterTwoResourceError("Prep Hammer transplant requires the original field223")
    if _identity(hammer_source_bundle) != HAMMER_SOURCE_IDENTITY:
        raise ChapterTwoResourceError("Prep Hammer source field218 changed")
    target, source = parse_field(prep_bundle), parse_field(hammer_source_bundle)
    if struct.unpack_from("<4H", target.header, 0) != (832, 0, 0, 0):
        raise ChapterTwoResourceError("Prep bank0 VRAM mapping changed")
    if struct.unpack_from("<4H", source.header, 4 * 8) != (384, 256, 0, 0):
        raise ChapterTwoResourceError("Source Hammer VRAM mapping changed")
    components = [part.data for part in target.parts]
    for index in (3, 4):
        existing = native._indexed_bundle_entries(components[index])
        replacement = native._indexed_bundle_entries(source.parts[index].data)[4]
        if _identity(existing[0]) != PREP_REPLACED_BANK_IDENTITIES[index]:
            raise ChapterTwoResourceError(f"Prep bank0 component{index} changed")
        if _identity(replacement) != HAMMER_BANK_IDENTITIES[index]:
            raise ChapterTwoResourceError(f"Hammer component{index} changed")
        if index == 4:
            sheets = native._indexed_bundle_entries(replacement)
            if len(sheets) != 1 or struct.unpack_from("<2H", sheets[0]) != (64, 228):
                raise ChapterTwoResourceError("Hammer atlas exceeds the audited prep VRAM cell")
        components[index] = native._replace_indexed_bundle_entry(
            components[index], 0, replacement, PREP_REPLACED_BANK_IDENTITIES[index][1])
    result = build_field_preserving(prep_bundle, components, (3, 4), compact_changed=True)
    parsed = parse_field(result)
    if [part.data for part in parsed.parts] != components or parsed.header[:0x100] != target.header[:0x100]:
        raise ChapterTwoResourceError("Prep Hammer transplant failed round-trip")
    return result
