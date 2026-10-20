#!/usr/bin/env python3
"""Build the first playable slice of the Disc 2 Surface Soylent facility.

Retail fields 620--626 contain the real Surface Soylent geometry, textures,
walkmeshes, actors, and cinematic machinery.  They were shipped as narrated
field scenes rather than as an explorable dungeon.  This builder freezes all
seven source fields and makes the first four-room route player controlled:

    623 approach -> 621 intake -> 620 quarantine -> 622 generation chamber

The complete build changes ATEL stream 5, appends field dialogue in stream 7,
inserts header records for newly scripted door carriers, and promotes only
the authentic model-backed door leaves that visibly animate.  Every other
retail static record and every other decoded stream remain byte-identical to
the Perfect Works source.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import modules.mass_driver.build as mass_driver  # noqa: E402
from modules.mass_driver.tools.build_mass_driver_graybox import xenoiso_wrapper_command  # noqa: E402
from shared.tools.xgdisc import (  # noqa: E402
    FIELD_DIRECTORY,
    FIRST_FIELD_LOCAL_FILE,
    Mode2Image,
    directory_file_fat_index,
)
from shared.tools.xgfield import (  # noqa: E402
    STREAM_NAMES,
    FieldFormatError,
    build_field_preserving,
    parse_field,
)
from shared.tools.xgdialog import (  # noqa: E402
    DialogueBlockSpec,
    DialogueFormatError,
    encode_dialogue,
    parse_dialogue,
)
from shared.tools.xgmode2 import verify_retail_title_boot  # noqa: E402
from shared.tools.xgscript import AtelScript as ScriptEditor  # noqa: E402
from shared.tools.xgscript import ScriptFormatError  # noqa: E402


SCRIPT_INDEX = 5
OUTPUT_FORMAT = "xenogears-surface-soylent-v1"
PARTY_SELECTORS = (0xFD, 0xFE, 0xFF)
POSITION_VARIABLES = {"x": 0x07E8, "z": 0x07EA, "y": 0x07EC}
SURFACE_ENTRY_FIELD = 623
SURFACE_ENTRY_PARAMETER = 0
MASS_DRIVER_ENTRY_FIELD = 728
TITLE_ROUTE_TAG_OPERAND = 0x0402
TITLE_ROUTE_TAG_RUNTIME_ADDRESS = 0x800C3E6A

TITLE_BASE_IDENTITIES = {
    1586: (4340, "573b7f268826c77dad1264445b76f2185cba6e1b1e183e84efff76ad0a1cb2bc"),
    1587: (182272, "b9e436ae84cae9c40daa7032ab16cb421172eea5b871aba4d42ee9f6f983204f"),
    2593: (65528, "b79a34a6db74235a2423cab748155c00eb4b7c69e367cbd59a06fbea683467a6"),
    2595: (9048, "c8d444b056e86679f6ac1ef1d60a42bf7f9bd41425c619c19dd35154e065513e"),
    2599: (153864, "92da8abf01921e330a7d02d6cd08b77ee65b820fc52f5ea150dc112b97e373a8"),
}
TITLE_FINAL_IDENTITIES = {
    1586: (4348, "c9ad354fd31c3d86909b24e758c7b65faf8a6d753a562000de17c4814c433239"),
    1587: (182272, "79faead20b575ff3889522671cc7852e24e3b38153288153fa31ab133272f131"),
    2593: (65524, "47ecaf96050d48c311b2be0aa5c1860ebe615f0b6b4860e68fca6addfb4c8dc6"),
    2599: (153864, "e7725abc12654ddc0ce739d01dab79b0ad98a4577c10dd271a71f7bed2358019"),
}
TITLE_FIELD_SCRIPT_SIZE = 570
TITLE_FIELD_SCRIPT_SHA256 = (
    "4c48cb17da95e4a67f43502aba92cbb5bd2fbf5ff7f433d3f501b92cd58654b8"
)
COMPLETE_TITLE_FIELD_SCRIPT_SIZE = 671
COMPLETE_TITLE_FIELD_SCRIPT_SHA256 = (
    "6e992a1c821ac457b8bdb63965f8abdd8354ece817d6e3f1f6076402aef84617"
)
COMPLETE_TITLE_FIELD_BUNDLE_SIZE = 4424
COMPLETE_TITLE_FIELD_BUNDLE_SHA256 = (
    "aadc67e0b96649ae3fd2d8acba24d3b84cac426872f43a2788ed10e2c68030ae"
)
SURFACE_STATE_RESET_PC = 0x0176
SURFACE_SHORTCUT_STATE_OPERAND = 0x03FA
SURFACE_SHORTCUT_DISCOVERED_BIT = 0x0400
SURFACE_SHORTCUT_DISCOVERED_BIT_INDEX = 10
SURFACE_STATE_RESET_ROUTINE = bytes.fromhex(
    "3B 1A 02 00 00 40 3B 1A 02 08 00 40 3B 1A 02 09 00 40 "
    "3B 1C 02 04 00 40 3B 1C 02 05 00 40 "
    "3B 1E 02 08 00 40 3B 1E 02 09 00 40 3B 1E 02 0A 00 40 "
    "3B 22 02 0F 00 40 "
    "3B FA 03 04 00 40 3B FA 03 05 00 40 3B FA 03 06 00 40 "
    "3B FA 03 07 00 40 3B FA 03 08 00 40 3B FA 03 09 00 40 "
    "3B FA 03 0A 00 40 "
    "98 6F 82 00 80"
)
SURFACE_TITLE_ATLAS_SHA256 = (
    "f3cf6cd71900e7422dd708b883b94f5d2b31c3c4f0fb70534b69b30e6d41e938"
)
SURFACE_TITLE_FONT_SHA256 = (
    "5d93d1cdbe95bf6942e8d86beb9685d5438ba04f6587f783f0ff9f84d120deb8"
)


class SurfaceSoylentBuildError(RuntimeError):
    """Raised when a source identity or authored route contract changes."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _u16(value: int) -> bytes:
    if not 0 <= value <= 0xFFFF:
        raise SurfaceSoylentBuildError(f"u16 value is outside range: {value}")
    return struct.pack("<H", value)


def _s16(value: int) -> bytes:
    if not -0x8000 <= value <= 0x7FFF:
        raise SurfaceSoylentBuildError(f"s16 value is outside range: {value}")
    return struct.pack("<h", value)


def _immediate(value: int) -> bytes:
    if not 0 <= value <= 0x7FFF:
        raise SurfaceSoylentBuildError(
            f"ATEL immediate is outside 0..32767: {value}"
        )
    return _u16(value | 0x8000)


def _change_field(field: int, parameter: int) -> bytes:
    return b"\x98" + _immediate(field) + _immediate(parameter)


@dataclass(frozen=True)
class FieldEntry:
    x: int
    z: int
    walkmesh: int
    camera_direction: int
    actor_direction: int

    def pack(self) -> bytes:
        if not all(
            0 <= value <= 0xFF
            for value in (
                self.walkmesh,
                self.camera_direction,
                self.actor_direction,
            )
        ):
            raise SurfaceSoylentBuildError("Field-entry byte is outside range")
        return struct.pack(
            "<hhBBB",
            self.x,
            self.z,
            self.walkmesh,
            self.camera_direction,
            self.actor_direction,
        )


@dataclass(frozen=True)
class EntryEdit:
    parameter: int
    source: FieldEntry
    playable: FieldEntry
    triangle: int


@dataclass(frozen=True)
class PartyEntity:
    entity: int
    source_character: int
    init_pc: int
    update_pc: int


@dataclass(frozen=True)
class Edge:
    axis: str
    threshold: int
    comparison: int
    destination_field: int
    destination_parameter: int
    sample: tuple[int, int]
    triangle: int

    @property
    def direction(self) -> str:
        return "at_or_above" if self.comparison == 0x44 else "at_or_below"


@dataclass(frozen=True)
class DoorController:
    """One model-less native X-action carrier at a field threshold."""

    x: int
    z: int
    interaction_half_width: int
    interaction_half_depth: int
    destination_field: int
    destination_parameter: int
    triangle: int
    action_kind: str = "transition"
    carrier_entity: int | None = None
    init_prefix: bytes = b"\xBC"


@dataclass(frozen=True)
class DoorLeafAnimation:
    """One authentic field-model leaf promoted to a finite script helper."""

    source_header_entity: int
    helper_entity: int
    source_flags: int
    model_index: int
    delta_x: int
    delta_z: int


@dataclass(frozen=True)
class DoorAnimation:
    destination_field: int
    destination_parameter: int
    leaves: tuple[DoorLeafAnimation, ...]
    frames: int = 32


@dataclass(frozen=True)
class SourceIdentity:
    scene: int
    bundle_id: int
    graphics_id: int
    bundle_size: int
    bundle_sha256: str
    graphics_size: int
    graphics_sha256: str
    script_size: int
    script_sha256: str
    header_size: int
    header_sha256: str


@dataclass(frozen=True)
class PlayableScene:
    identity: SourceIdentity
    role: str
    entry_edits: tuple[EntryEdit, ...]
    party: tuple[PartyEntity, ...]
    director_entity: int
    director_update_pc: int
    edges: tuple[Edge, ...]
    playable_update_pc: int
    poll_pc: int
    patched_script_size: int
    patched_script_sha256: str
    patched_bundle_size: int
    patched_bundle_sha256: str
    force_party_direction: int | None = None


@dataclass(frozen=True)
class PreparedField:
    spec: PlayableScene
    source_bundle: bytes
    graphics: bytes
    header: bytes
    components: tuple[bytes, ...]
    bundle: bytes


@dataclass(frozen=True)
class PreparedTitleResource:
    canonical_id: int
    name: str
    filename: str
    source_sha256: str
    data: bytes


@dataclass(frozen=True)
class PreparedDonorField:
    identity: SourceIdentity
    role: str
    source_bundle: bytes
    graphics: bytes
    header: bytes
    components: tuple[bytes, ...]
    bundle: bytes
    entry_triangles: tuple[tuple[int, int], ...]


SOURCE_FIELDS = (
    SourceIdentity(620, 1846, 1847, 145132, "6d35b720af7f116064af42692e5f4975dfe6b3231d641318df79240d78caabbc", 67584, "73c455a2c51ba525d64a1d65ff837481d5cdb6419b58332175eb4fad78505c40", 2940, "da4ced4efab3f2847ec7f637ec1d146bb7d0f6acec70f35bc5681f9b8c93905b", 864, "7995cc094488b8a49558b7762b3b01fde9724d02abeaf9feac4df403daff4dcc"),
    SourceIdentity(621, 1848, 1849, 128452, "11f6727de949c6441aee587efcf87706a63c2c33f1616e9d214fb710afd534b9", 186368, "f7eb4994058f4c2c5c6ae76410ee80b6097dbd4e633c2842f2d847a0d8827b46", 1924, "02e4bef182dc9c481e42d251e7d5c87642f526b1cedc7962de7604daa5a2e423", 1024, "4c3d63916caccaae524a53040dd43e03d5d37822cda456ab3dbbe9d4bbab8ec3"),
    SourceIdentity(622, 1850, 1851, 103224, "05bda1cd9f74037a915c03a7b5a6ccf24f569c1827c883ded213e2eac8a42319", 350208, "141196e9735e50b97335c302352346c28f08196881982816f827b6e93d2de013", 5360, "1621ee10e3fb4d4d720076cd66cb21dc9a04262351724b73c4feda5d57ebddbc", 1152, "70460c013205e83da1bf2f3a47a564fc4ef71c0a5766c8b4e79b2fb46c27d3b7"),
    SourceIdentity(623, 1852, 1853, 30872, "55194f3341402756635b6a4fd63df453d7816b2282a68b60139e704f30150c65", 202752, "6f05b49991e7ff45aea8f9e59ebe123a0a5cfa1402c608965086ba4db52c3220", 4820, "9e7960064dfd334226ebd02e066a5d8ceb268771bdaa87301ff1e6ca468f244e", 1248, "a9529e7be398819fc21c018102f73c8aa99b54c6667e3b131a86abcc05a3aee4"),
    SourceIdentity(624, 1854, 1855, 61632, "0bd61c9415600b300e727e0d9864ab09dd1b8a42f84568b9f7081b2b0c124502", 200704, "13a4d8a73259dead1460473e3b88e734c095099cc03b67a94511ca7b166a0c25", 9908, "f39810d3595d473dace492fb000ec8de4f50618963823509dbca4b4db69596d3", 2384, "2f8d6075711c39448cbdac5969217fddec7b1f4b5a85d80c0ad9dc7f371875bf"),
    SourceIdentity(625, 1856, 1857, 44736, "923ead7c5a0680c57b0f4e1b377c0562d9d1d66099ba24714f8744aa165fbe61", 110592, "40a8417d4a19e3743ad0ff8fc40d79a330f8cb4154747c5ba9f6f264200e2933", 4932, "d35ec6256a76af816d1f2ac7ba066841b4ad3f6400364bdd6c9797c84e4da298", 944, "356103961ba9cee7bfc999e9e2c890885a81b338fac1a513e6e8ce06f1e1946a"),
    SourceIdentity(626, 1858, 1859, 34688, "bb8402ba8e4685f7bceac26ab8203bb048a2cd0335caf1a6a1a61f56c76a6c3b", 98304, "2433e553290f261601ab2b675d626e4734241c2c5b3606b50246865da7052d74", 7488, "b236d6675456f6614fbffee5f868e1d2b64fe15dc2fca2355d5592f29f326cd1", 1808, "06ea3b0ebd547fc5e0118e161467da71eb60b9bc4f03c0405d2a110eee620073"),
)


SOURCE_BY_SCENE = {item.scene: item for item in SOURCE_FIELDS}

DONOR_FIELDS = (
    SourceIdentity(549, 1704, 1705, 22348, "704d48ff5c9661c66bfe27669aac0ea140108cd04168fc861cfbe481b4408734", 161792, "6c4ae880e1520c174d88716008bf7c881a797e8eafb2e6b0c12b59cd050b3249", 3080, "e2b1fd46936dec59da644d999de2b36864d9703f117f4ded5248c2bb374dc99e", 736, "596c32f300e34a8edafd39957ade33b4b790b9bc9cce05e0d5de644e6f59b985"),
    SourceIdentity(550, 1706, 1707, 24404, "9965ad1d0b75587555d43cb5c8d22b0c659a0d4923e02f8da34261b102351f3d", 194560, "31357196264f75a1831772476dabb37f4759048ba97359d93f062a018ec61241", 4572, "7fa1515799718f45bfad14bd206285cc122940d467dc0b4c5f5d442b6f05ed7c", 960, "80426b3ab2bb8d7a1283481733bea60505874036d827c3c2eddf3d18f12c4c0d"),
    SourceIdentity(565, 1736, 1737, 80904, "9eab95f706083ee1d1a16743b4da0d6df1948da48e47172aa30b0c98c5b78d7f", 59392, "520014b6f3ae0a96e0bd562785bce50166373836fff94e45126e16154af903bb", 3040, "ff1bb34dabf93964a6278a1b8505767eda2e4e581848dcaee634306f29eebfe1", 880, "c195804d2a8100e6a6b08e26309a2df52d2e068ad76ea398189fb8ea0a031266"),
    SourceIdentity(589, 1784, 1785, 50704, "20f58cb7d8f9244c2d9d6adfca11561e8d3056014af31e8b0799cccdbc2ed00b", 288768, "7f96a711fa379652822b9921628d06deb08260c81a7319e82ff96a06dd3b9fd0", 4032, "56f68c83ae12d1e39f9eaf83e532043512059b2a1f7358d98bf284be3233da7b", 816, "2b20fb7cdcdce580b70d3f75cb670051789862ad94e0b48dc2595fd689d93b7c"),
)
DONOR_BY_SCENE = {item.scene: item for item in DONOR_FIELDS}
DONOR_DUMMY = b"It's CDMAKE Dummy !\r\n\r\n "
DONOR_DUMMY_SHA256 = "aafefb97ceb8e4667c719b99c4250b286e03087315b61848d196300140a95a2c"
DONOR_FINAL_IDENTITIES = {
    549: (3080, "bbe3a8d7e7d6a2e305210a308c6f3b612f7c7d6ac4f0a5c527631d7eb1c3f3d3", 22332, "5f7c668a32796eef8c92393340b72f69d590f9ed7bed99ab8daf11aab4e4db5d"),
    550: (4572, "c0116a50b17129a9a97d10cbef26cf1b12b8dace340d8bfc1b2ceeb05f9d6dd4", 24396, "731c5ed0ca8d9a62d44083154af30fda18c8301bccb041dd35de361f9bec30d2"),
    565: (3040, "9d4a598790b179731a8124a193baf94c3007e3d2b2753d689367f2f4a15eb464", 80908, "e01ea1118923b0a46d1e4113f79dd20f4dd2c34e50d995fc2b11f3fec5b816c4"),
    589: (4032, "24bde9884aaf73c2b7e268a3f7b4218cdebe068c457e4eadaac2148aed236807", 50704, "56e603701378ff2839bc9ac3465bc632857c8e175e3456b05b086fed7248cf71"),
}


PLAYABLE_SCENES = (
    PlayableScene(
        SOURCE_BY_SCENE[623],
        "surface approach and tissue-processing threshold",
        (
            EntryEdit(0, FieldEntry(0, -665, 0, 0xFF, 0xFF), FieldEntry(0, -665, 0, 0, 0), 16),
            EntryEdit(1, FieldEntry(0, 1053, 0, 0xFF, 0xFF), FieldEntry(0, 1053, 0, 4, 4), 0),
        ),
        (PartyEntity(2, 0, 0x00B6, 0x00BE), PartyEntity(3, 1, 0x00C1, 0x00C9), PartyEntity(4, 2, 0x00CC, 0x00D4)),
        1, 0x001D,
        (Edge("z", 1200, 0x44, 621, 6, (0, 1200), 0),),
        0x0910, 0x0912, 4850, "64ca83be5889559d5a6296f1424899566db3ced7c31ec6ee26a95f604ada037b", 30896, "0af3dd688729934bd905e530a8130b7a5380657da38a989526f3b97be3c2562e",
    ),
    PlayableScene(
        SOURCE_BY_SCENE[621],
        "intake circulation spine",
        (
            EntryEdit(0, FieldEntry(870, 1781, 0, 0xFF, 0xFF), FieldEntry(870, 1781, 0, 4, 4), 63),
            # Center the playable arrival on the real south doorway and move
            # it far enough inward for camera 0 to look through the vestibule
            # instead of intersecting its exterior wall.
            EntryEdit(6, FieldEntry(125, 0, 0, 0xFF, 0xFF), FieldEntry(32, 100, 0, 0, 0), 2),
        ),
        (PartyEntity(3, 0, 0x0137, 0x013F), PartyEntity(4, 1, 0x0142, 0x014A), PartyEntity(5, 2, 0x014D, 0x0155)),
        1, 0x0040,
        (Edge("z", -100, 0x45, 623, 1, (125, -100), 2), Edge("z", 1830, 0x44, 620, 0, (870, 1830), 65)),
        0x0200, 0x0202, 1970, "24706266e675f134296620b5c6d03a3758e64b8ee04bfcd0a5b3f64368687526", 128496, "9726b7cfc59e39e707880b7803946a49c8760872b3db66e491c70b212c6a1163",
    ),
    PlayableScene(
        SOURCE_BY_SCENE[620],
        "quarantine and mutation assessment chamber",
        (
            EntryEdit(0, FieldEntry(-300, 0, 0, 0xFF, 0xFF), FieldEntry(-300, 0, 0, 2, 2), 104),
            EntryEdit(1, FieldEntry(300, 0, 0, 0xFF, 0xFF), FieldEntry(300, 0, 0, 6, 6), 183),
        ),
        (PartyEntity(2, 0, 0x01AF, 0x01B7), PartyEntity(3, 1, 0x01BA, 0x01C2), PartyEntity(4, 2, 0x01C5, 0x01CD)),
        1, 0x0070,
        (Edge("x", -430, 0x45, 621, 0, (-430, 0), 222), Edge("x", 480, 0x44, 622, 0, (480, 0), 246)),
        0x0538, 0x053A, 2986, "75272af484a9e4b17a72758949e1dd97e305e6c6e5f007fec8f90cbe3e24bc76", 145180, "405e57bc30956028e56ecca457539036b0a42a0ec09af7c6db174f1f7e83e592",
    ),
    PlayableScene(
        SOURCE_BY_SCENE[622],
        "generation chamber and vertical-slice endpoint",
        (EntryEdit(0, FieldEntry(-885, -136, 0, 0xFF, 0xFF), FieldEntry(-700, -136, 0, 2, 2), 15),),
        (PartyEntity(2, 0, 0x015C, 0x0166), PartyEntity(3, 1, 0x021C, 0x0226), PartyEntity(4, 9, 0x02C1, 0x02CB)),
        5, 0x0346,
        (Edge("x", -850, 0x45, 620, 1, (-850, -136), 16),),
        0x0DEC, 0x0DEE, 5390, "9dbb8a4c7050a9cee107e9fdb898aa30d885550f5f66465fe3aa662b467539a0", 103252, "b6161aeef2a2fb7602b37c0d46d5dc4cc4666880200d5707eb408233f6a74780",
        force_party_direction=2,
    ),
)


PLAYABLE_BY_SCENE = {item.identity.scene: item for item in PLAYABLE_SCENES}

NATIVE_WING_SCENES = (
    PlayableScene(
        SOURCE_BY_SCENE[624],
        "molecular sorting line",
        (
            EntryEdit(0, FieldEntry(265, -621, 0, 0xFF, 0xFF), FieldEntry(265, -621, 0, 0, 0), 34),
            EntryEdit(1, FieldEntry(-1060, -5, 0, 0xFF, 0xFF), FieldEntry(-1060, -5, 0, 2, 2), 12),
        ),
        (PartyEntity(2, 0, 0x0093, 0x009B), PartyEntity(3, 1, 0x009E, 0x00A6), PartyEntity(4, 2, 0x00A9, 0x00B1)),
        1, 0x001D,
        (Edge("z", -800, 0x45, 565, 1, (265, -800), 35), Edge("x", -1200, 0x45, 626, 0, (-1200, -5), 13)),
        0x12F0, 0x12F2, 9954, "84969240e67378ce3f7cadfe404a5d3339f6bc6d7ec73f5f5d1f9019bd2a6066", 61680, "5cba83954020eb890af2167f24faf7a5812cbc5f2cf9311242e356a8f294b9da",
    ),
    PlayableScene(
        SOURCE_BY_SCENE[626],
        "M-Project vat and ring core",
        (
            EntryEdit(0, FieldEntry(0, 0, 0, 0xFF, 0xFF), FieldEntry(0, -400, 0, 0, 0), 1),
            EntryEdit(1, FieldEntry(0, 0, 0, 0xFF, 0xFF), FieldEntry(0, 350, 0, 4, 4), 0),
        ),
        (PartyEntity(2, 0, 0x00C2, 0x00CA), PartyEntity(3, 1, 0x00CD, 0x00D5), PartyEntity(4, 2, 0x00D8, 0x00E0)),
        1, 0x001D,
        (Edge("z", -550, 0x45, 624, 1, (0, -550), 1), Edge("z", 500, 0x44, 625, 0, (0, 500), 0)),
        0x0DFC, 0x0DFE, 7534, "2a0e8e8fbbed7842122be3bcf4e7518a601ee4830ff81670ecfc6f9efab3c368", 34736, "b500ab873007e1bff08b4d8b0198a68ea8a6d2b85afa7da2d6f9cf279cf12757",
    ),
    PlayableScene(
        SOURCE_BY_SCENE[625],
        "Meld reveal vestibule",
        (
            EntryEdit(0, FieldEntry(387, 0, 0, 2, 0xFF), FieldEntry(0, -300, 0, 0, 0), 1),
            EntryEdit(1, FieldEntry(0, 0, 0, 0xFF, 0xFF), FieldEntry(0, 300, 0, 4, 4), 0),
        ),
        (PartyEntity(1, 0, 0x0231, 0x0239), PartyEntity(2, 1, 0x024D, 0x0255), PartyEntity(3, 9, 0x0258, 0x0260)),
        0, 0x0020,
        (Edge("z", -400, 0x45, 626, 1, (0, -400), 1), Edge("z", 400, 0x44, 622, 0, (0, 400), 0)),
        0x0A80, 0x0A82, 4978, "7ad9b984b07f208f52358768c2a1ac29f1eadd7302c5fe3857bc8e0f041dcd01", 44772, "c3bb4468fa1d1b7fea7026d4ea9a3de4e50f1f99ffd4f7a90cb452bbd4aeee06",
    ),
)

FINAL_GENERATION_SCENE = replace(
    PLAYABLE_BY_SCENE[622],
    role="generation chamber and complete-route endpoint",
    entry_edits=(
        *PLAYABLE_BY_SCENE[622].entry_edits,
        EntryEdit(
            1,
            FieldEntry(0, 0, 0, 0xFF, 0xFF),
            FieldEntry(0, -800, 0, 0, 0),
            65,
        ),
    ),
    edges=(
        Edge("x", -794, 0x45, 625, 1, (-794, -132), 16),
        Edge("z", -926, 0x45, 623, 0, (0, -926), 64),
    ),
    patched_script_size=5406,
    patched_script_sha256="39994929c0be0b47547c75f1a8e457200ff0bafcca9531ab50310184960f05a6",
    patched_bundle_size=103264,
    patched_bundle_sha256="d2b7cfdc004fe0278b4c0561aa142a3316173f7f4bc6a297c2833045a3c77f6e",
)

COMPLETE_APPROACH_SCENE = replace(
    PLAYABLE_BY_SCENE[623],
    role="surface approach with discovered generation-service shortcut",
    edges=(
        *PLAYABLE_BY_SCENE[623].edges,
        Edge("z", -881, 0x45, 622, 1, (0, -881), 17),
    ),
    patched_script_size=4866,
    patched_script_sha256="f87491e52be9ffbd9ee0823f014f6e5acfc0ca5928dd5e74f626b35cc7588ea2",
    patched_bundle_size=30904,
    patched_bundle_sha256="51f68e23eadda78f230ea5a718b4f27fd8399f5fa393bad641fee39e2ff78009",
)

QUARANTINE_STATE_OPERAND = SURFACE_SHORTCUT_STATE_OPERAND
QUARANTINE_SELECTION_MASK = 0x00F0
QUARANTINE_VALID_SELECTION = 0x0070
QUARANTINE_COMPLETE_BIT = 0x0100
QUARANTINE_INTRO_SEEN_BIT = 0x0200
QUARANTINE_GATE_PC = 0x07E2
QUARANTINE_SCRIPT_SIZE = 3788
QUARANTINE_SCRIPT_SHA256 = (
    "f4975486174eb61c3e12b0dfd9c1b513a7eb02886911ad52b61fd425b4bfc714"
)
QUARANTINE_DIALOGUE_SIZE = 1195
QUARANTINE_DIALOGUE_SHA256 = (
    "7a5247bbf5ec53291537e9143d11d6d89dad34897134d91a11d40b3523318f14"
)
QUARANTINE_BUNDLE_SIZE = 146036
QUARANTINE_BUNDLE_SHA256 = (
    "5f941f1429928a3ae071c4210d8a72ca73eddc440c1f076dc4dff10306bfe11a"
)
QUARANTINE_SOURCE_GATE_SHA256 = (
    "d51fc7dc6112cf59792f17d6b72ec44d08fbcec1ec2a92ff0773b42a654a03b3"
)
QUARANTINE_RING_ROUTINES = (
    (
        17,
        (0x02D9, 0x02EA, 0x0317),
        0x0566,
        0x0596,
        bytes.fromhex(
            "BC 2D FB 0E 04 10 04 12 04 35 14 04 00 04 40 "
            "F8 00 00 20 F8 03 04 00 18 18 18 64 00 20 01 80 "
            "02 FA 03 10 00 46 95 05 FE 08 00 94 00 94 00 94 00"
        ),
        bytes.fromhex(
            "33 FE 54 31 20 00 A4 05 26 01 80 01 99 05 26 01 80 "
            "02 FA 03 00 01 46 B7 05 F5 0B 00 01 9C FE 53 00 "
            "02 FA 03 00 02 46 C2 05 01 D0 05 F5 04 00 01 9C "
            "3A FA 03 09 00 40 26 01 80 F5 05 00 01 9C "
            "02 FA 03 10 00 46 F1 05 3B FA 03 04 00 40 74 5F 80 "
            "FE 08 00 90 00 90 00 90 FE 53 00 "
            "3A FA 03 04 00 40 74 50 80 FE 08 00 94 00 94 00 94 FE 53 00"
        ),
    ),
    (
        18,
        (0x0318, 0x0329, 0x0350),
        0x0605,
        0x0635,
        bytes.fromhex(
            "BC 2D FB 18 04 1A 04 1C 04 35 1E 04 00 04 40 "
            "F8 00 00 20 F8 03 04 00 18 18 18 64 00 20 01 80 "
            "02 FA 03 20 00 46 34 06 FE 08 00 94 00 94 00 94 00"
        ),
        bytes.fromhex(
            "33 FE 54 31 20 00 43 06 26 01 80 01 38 06 26 01 80 "
            "02 FA 03 00 01 46 56 06 F5 0B 00 01 9C FE 53 00 "
            "02 FA 03 00 02 46 61 06 01 6F 06 F5 04 00 01 9C "
            "3A FA 03 09 00 40 26 01 80 F5 06 00 01 9C "
            "02 FA 03 20 00 46 90 06 3B FA 03 05 00 40 74 5F 80 "
            "FE 08 00 90 00 90 00 90 FE 53 00 "
            "3A FA 03 05 00 40 74 50 80 FE 08 00 94 00 94 00 94 FE 53 00"
        ),
    ),
    (
        19,
        (0x0351, 0x0362, 0x0389),
        0x06A4,
        0x06D4,
        bytes.fromhex(
            "BC 2D FB 22 04 24 04 26 04 35 28 04 00 04 40 "
            "F8 00 00 20 F8 03 04 00 18 18 18 64 00 20 01 80 "
            "02 FA 03 40 00 46 D3 06 FE 08 00 94 00 94 00 94 00"
        ),
        bytes.fromhex(
            "33 FE 54 31 20 00 E2 06 26 01 80 01 D7 06 26 01 80 "
            "02 FA 03 00 01 46 F5 06 F5 0B 00 01 9C FE 53 00 "
            "02 FA 03 00 02 46 00 07 01 0E 07 F5 04 00 01 9C "
            "3A FA 03 09 00 40 26 01 80 F5 07 00 01 9C "
            "02 FA 03 40 00 46 2F 07 3B FA 03 06 00 40 74 5F 80 "
            "FE 08 00 90 00 90 00 90 FE 53 00 "
            "3A FA 03 06 00 40 74 50 80 FE 08 00 94 00 94 00 94 FE 53 00"
        ),
    ),
    (
        20,
        (0x038A, 0x039B, 0x03C8),
        0x0743,
        0x0773,
        bytes.fromhex(
            "BC 2D FB 2C 04 2E 04 30 04 35 32 04 00 04 40 "
            "F8 00 00 20 F8 03 04 00 18 18 18 64 00 20 01 80 "
            "02 FA 03 80 00 46 72 07 FE 08 00 94 00 94 00 94 00"
        ),
        bytes.fromhex(
            "33 FE 54 31 20 00 81 07 26 01 80 01 76 07 26 01 80 "
            "02 FA 03 00 01 46 94 07 F5 0B 00 01 9C FE 53 00 "
            "02 FA 03 00 02 46 9F 07 01 AD 07 F5 04 00 01 9C "
            "3A FA 03 09 00 40 26 01 80 F5 08 00 01 9C "
            "02 FA 03 80 00 46 CE 07 3B FA 03 07 00 40 74 5F 80 "
            "FE 08 00 90 00 90 00 90 FE 53 00 "
            "3A FA 03 07 00 40 74 50 80 FE 08 00 94 00 94 00 94 FE 53 00"
        ),
    ),
)
QUARANTINE_GATE_ROUTINE = bytes.fromhex(
    "2D 02 E8 07 EA 07 EC 07 02 E8 07 C2 01 44 F5 07 01 F8 07 37 E0 07 "
    "02 E8 07 52 FE 45 08 08 FE 54 98 6D 82 00 80 5B "
    "02 E8 07 E0 01 44 84 08 02 FA 03 00 01 46 20 08 "
    "FE 54 98 35 82 06 80 5B 02 E0 07 00 00 40 84 08 "
    "35 E2 07 FA 03 00 3E E2 07 F0 00 40 02 E2 07 70 00 41 5D 08 "
    "36 E0 07 74 5F 80 33 FE 54 31 20 00 50 08 26 01 80 01 45 08 "
    "26 01 80 F5 09 00 01 9C FE 53 01 84 08 "
    "3A FA 03 08 00 40 74 50 80 33 FE 54 31 20 00 74 08 26 01 80 "
    "01 69 08 26 01 80 F5 0A 00 01 9C FE 54 98 35 82 06 80 5B "
    "5A 01 E2 07"
)
INTAKE_SIDE_WING_TAIL_PC = 0x022A
INTAKE_SIDE_WING_TAIL = bytes.fromhex(
    "02 E8 07 00 00 45 3A 02 FE 54 98 25 82 00 80 5B "
    "02 E8 07 C2 06 44 4A 02 FE 54 98 26 82 00 80 5B "
    "5A 01 02 02"
)
INTAKE_COMPLETE_SCRIPT_SIZE = 2002
INTAKE_COMPLETE_SCRIPT_SHA256 = (
    "e632a893ec8a3634ef9b008a26a44bd3faec71b5e49c7de9338863b977e2bf2c"
)
INTAKE_COMPLETE_BUNDLE_SIZE = 128524
INTAKE_COMPLETE_BUNDLE_SHA256 = (
    "1c6fab8a383ffb01054569ecdf73c4ad629bc832de4433b01be702cd7ece783c"
)


# Complete-route doors use the same model-less, flag-0x2000 spatial action
# carrier as the retail Solaris donor doors.  The field walkmesh remains the
# physical boundary; crossing a coordinate can no longer change fields.
NATIVE_DOOR_CONTROLLERS = {
    623: (
        # The endpoint spans x=-63..66.  Operand 0x21 gives the hidden,
        # immovable carrier an exact +/-66 physical seal across that width.
        DoorController(0, 1259, 0x21, 0x18, 621, 6, 0),
        # The authentic south leaves sit one unit beyond the walkmesh end.
        # Anchor the carrier on the final valid row and keep this reverse side
        # locked until the generation chamber discovers the service shortcut.
        DoorController(
            0, -881, 0x21, 0x10, 622, 1, 17, "discovery_gate"
        ),
    ),
    621: (
        # Seven authentic intake panels now own seven reciprocal X routes.
        # The side-wing carriers sit on the visible leaf planes, while their
        # x-normal volume leaves each audited circulation-side return outside
        # held-Cross range after the leaf is reclosed on field load.
        DoorController(176, 0, 0x0E, 0x2C, 623, 1, 6),
        DoorController(867, 1832, 0x2C, 0x10, 620, 0, 65),
        DoorController(88, 840, 0x10, 0x18, 549, 0, 18),
        DoorController(1645, 840, 0x10, 0x18, 550, 0, 86),
        DoorController(866, 1131, 0x16, 0x0E, 565, 0, 45),
        DoorController(88, 396, 0x10, 0x18, 565, 2, 14),
        DoorController(1645, 396, 0x10, 0x18, 565, 3, 85),
    ),
    620: (
        # The two model-0 leaves occupy the exact x=-352/+352 planes.  Narrow
        # x-normal carriers seal each leaf without covering the safe arrival
        # points at x=-300/+300 on the room side of the closed panels.
        DoorController(-352, 0, 0x10, 0x18, 621, 0, 100),
        DoorController(352, 0, 0x10, 0x18, 565, 6, 182, "quarantine_gate"),
    ),
    624: (
        DoorController(
            265, -840, 0x18, 0x10, 565, 1, 35,
            carrier_entity=0,
            init_prefix=bytes.fromhex("BC A0 FF 80 1E 80 00 83"),
        ),
        DoorController(-1280, 0, 0x10, 0x18, 626, 0, 13, carrier_entity=1),
    ),
    626: (
        DoorController(
            0, -610, 0x30, 0x18, 624, 1, 1,
            carrier_entity=0,
            init_prefix=bytes.fromhex("BC A0 FF 80 0F 80 00 83"),
        ),
        DoorController(0, 560, 0x30, 0x18, 625, 0, 0, carrier_entity=1),
    ),
    625: (
        DoorController(
            0, -390, 0x30, 0x10, 626, 1, 1,
            carrier_entity=0,
            init_prefix=bytes.fromhex(
                "BC A0 FF 80 0F 80 60 80 E7 08 80 08 80 08 80"
            ),
        ),
        DoorController(0, 450, 0x30, 0x10, 622, 0, 0, carrier_entity=6),
    ),
    622: (
        DoorController(
            -794, -132, 0x10, 0x18, 625, 1, 16,
            carrier_entity=0,
            init_prefix=bytes.fromhex("BC A0 FF 80 1E 80 00 83"),
        ),
        DoorController(
            0, -926, 0x1F, 0x10, 623, 0, 64,
            action_kind="discovery_unlock",
        ),
    ),
}

# These are the real panels visible at the tested quarantine/reception
# thresholds.  Field 621 inserts seven carriers at its old e20 ATEL boundary,
# shifting retail static nodes 23--30 to e30--37.  The eight leaves below are
# then rehomed contiguously as e27--34.  Retail e2/model 6 already owns a
# native finite script-4 movement and is deliberately reused in place.
# Field 620's west panel is retail node 23, shifted to e25 by its two carriers.
NATIVE_DOOR_ANIMATIONS = {
    623: (
        DoorAnimation(
            622,
            1,
            (
                DoorLeafAnimation(49, 39, 0x0010, 10, 2, 0),
                DoorLeafAnimation(50, 40, 0x0010, 11, -2, 0),
            ),
        ),
    ),
    621: (
        DoorAnimation(
            623,
            1,
            (
                DoorLeafAnimation(36, 27, 0x0010, 10, 0, 2),
                DoorLeafAnimation(37, 28, 0x0010, 11, 0, -2),
            ),
        ),
        DoorAnimation(
            620,
            0,
            (
                DoorLeafAnimation(34, 29, 0x0010, 8, -2, 0),
                DoorLeafAnimation(35, 30, 0x0010, 9, 2, 0),
            ),
        ),
        DoorAnimation(
            550,
            0,
            # Retail model 4 is the exact single panel at x=1645,
            # z=793..882.  Slide it north into the adjacent wall pocket.
            (DoorLeafAnimation(31, 31, 0x0010, 4, 0, 2),),
        ),
        DoorAnimation(
            565,
            0,
            (DoorLeafAnimation(30, 32, 0x0010, 3, 2, 0),),
        ),
        DoorAnimation(
            565,
            2,
            (DoorLeafAnimation(33, 33, 0x0010, 7, 0, -2),),
        ),
        DoorAnimation(
            565,
            3,
            (DoorLeafAnimation(32, 34, 0x0010, 5, 0, -2),),
        ),
    ),
    620: (
        DoorAnimation(
            621,
            0,
            (DoorLeafAnimation(25, 25, 0x0290, 0, 0, 2),),
        ),
    ),
    622: (
        DoorAnimation(
            623,
            0,
            (DoorLeafAnimation(36, 27, 0x0010, 2, 2, 0),),
        ),
    ),
}

# Field 621 e2/model 6 is the one side-wing leaf already backed by an
# authentic finite helper.  Its script 4 starts at 0x00F7 and moves the panel
# clear in the same field coordinate system as the promoted static leaves.
NATIVE_EXISTING_DOOR_HELPERS = {
    621: (
        (549, 0, 2, 0x00F7, 0x0122),
    ),
    622: (
        # Retail e7/model 2 is the exact west panel.  Its checked finite
        # script-4 helper is reused in place and blocked before returning to
        # the Meld vestibule.
        (625, 1, 7, 0x07A7, 0x07CA),
    ),
}
NATIVE_EXISTING_DOOR_HELPER_BODY = bytes.fromhex(
    "2D FB 04 04 06 04 08 04 38 04 04 0A 00 40 10 00 "
    "04 04 06 04 08 04 00 10 01 38 06 04 64 00 40 10 "
    "00 04 04 06 04 08 04 00 10 01 00"
)
GENERATION_NATIVE_DOOR_HELPER_BODY = bytes.fromhex(
    "39 0E 04 0F 00 40 10 00 0E 04 10 04 12 04 00 10 01 "
    "38 10 04 C8 00 40 10 00 0E 04 10 04 12 04 00 10 01 00"
)
NATIVE_EXISTING_DOOR_HELPER_BODIES = {
    (621, 2): NATIVE_EXISTING_DOOR_HELPER_BODY,
    (622, 7): GENERATION_NATIVE_DOOR_HELPER_BODY,
}

NATIVE_ROUTE_STOP_PCS = {
    624: 0x0092,
    626: 0x00C1,
    625: 0x0230,
}


INTAKE_NPC_DIALOGUES = (
    (
        6,
        "They told us this place could\nseparate the sick from the well.\n"
        "Now every lane leads inward.<Close>",
    ),
    (
        7,
        "The Solaris signs still call us\nsamples. We were people before\n"
        "the limiter failed.<Close>",
    ),
    (
        8,
        "Some came here hoping to be\ncured. The doors only sorted us\n"
        "into different holding rooms.<Close>",
    ),
    (
        9,
        "My brother was sent through the\nred lane. No one has come back\n"
        "from the processing floor.<Close>",
    ),
    (
        10,
        "The machines keep asking for a\ncaste index. Surface people were\n"
        "never meant to pass that test.<Close>",
    ),
    (
        11,
        "Nanomachines are in everyone\nnow. The scanners still pretend\n"
        "that makes us different.<Close>",
    ),
    (
        12,
        "Do not trust the clean voices.\nThey call containment mercy while\n"
        "the walls close around us.<Close>",
    ),
    (
        14,
        "The north passage reaches the\nquarantine rings. Three readings\n"
        "open the service route.<Close>",
    ),
    (
        15,
        "The side laboratories kept old\nrecords. They may explain what\n"
        "this facility was built to do.<Close>",
    ),
)


QUARANTINE_NPC_DIALOGUES = (
    (
        5,
        "It hurts less when I keep moving.\nPlease... do not let the scanners\n"
        "decide I am no longer human.<Close>",
    ),
    (
        6,
        "The change came after the sky\nfilled with light. We came here\n"
        "because Solaris promised relief.<Close>",
    ),
    (
        7,
        "Some of us still remember our\nnames. The system records only\n"
        "mutation stages.<Close>",
    ),
    (
        8,
        "Those rings are not a cure. They\nmeasure what is happening, then\n"
        "send us deeper into the plant.<Close>",
    ),
    (
        9,
        "Pod A still detects an ordinary\nhuman genome beneath the changes.\n"
        "That should count for something.<Close>",
    ),
    (
        10,
        "The limiter signal is gone. The\nmachine calls that failure. I call\n"
        "it the truth finally surfacing.<Close>",
    ),
    (
        11,
        "Nanomachines are rewriting us\nfaster than this facility can\n"
        "classify the damage.<Close>",
    ),
    (
        12,
        "Solaris divided people by caste.\nPain does not recognize any of\n"
        "those categories.<Close>",
    ),
    (
        13,
        "Choose the biological readings:\ngenome, limiter, nanomachines.\n"
        "Leave the caste index out.<Close>",
    ),
    (
        14,
        "The service route opens only when\nthree relays agree on what remains\n"
        "human.<Close>",
    ),
    (
        15,
        "I heard machinery beyond the east\ndoor. Whatever it is processing,\n"
        "it has not stopped.<Close>",
    ),
    (
        16,
        "If you reach the deeper chambers,\nshut this place down. Do not let it\n"
        "turn anyone else into material.<Close>",
    ),
)


GENERATION_NPC_DIALOGUES = (
    (8, "Solaris said this place\ncould reverse the mutations.\nI wanted to believe them.<Close>"),
    (9, "They sorted us into 'haves'\nand 'have-nots.' We are all\njust trying to stay alive.<Close>"),
    (10, "The Ministry calls this\nsalvation. I can hear the\nmachines beneath us.<Close>"),
    (11, "My body changes every day.\nI only wanted a little\nmore time.<Close>"),
    (12, "They asked the healthy ones\nto share flesh and blood.\nThen the shouting began.<Close>"),
    (13, "Please do not look away.\nThat is how Solaris made\nthis place possible.<Close>"),
    (14, "They promised to make me\nhuman again. Why are they\nmeasuring me for a weapon?<Close>"),
    (15, "Some of us still have time.\nThat does not make our\nlives worth more.<Close>"),
    (16, "The generation equipment\nhas started cycling by\nitself.<Close>"),
    (17, "Something is moving inside\nthe chamber. It was one\nof us once.<Close>"),
    (18, "The barrier will not hold.\nPlease shut the System\ndown.<Close>"),
    (19, "The people who ran this\nfacility are gone. The\nSystem is still feeding.<Close>"),
    (20, "The Meld was a person.\nI saw its eyes before it\nlost its shape.<Close>"),
    (21, "It is not hunting us.\nIt is begging for the pain\nto end.<Close>"),
    (22, "If you reach the controls,\nstop the generation cycle.\nPlease.<Close>"),
    (23, "That sound came from the\namalgamation chamber.\nSomething broke loose.<Close>"),
    (24, "Remember us as people,\nnot as failures of their\nexperiment.<Close>"),
)

SURFACE_SHORTCUT_DENIAL_DIALOGUE_ID = 1
SURFACE_SHORTCUT_DENIAL_DIALOGUE = (
    "EMERGENCY SERVICE LATCH\n"
    "Sealed from the generation side.<Close>"
)


NATIVE_NPC_DIALOGUES = {
    621: INTAKE_NPC_DIALOGUES,
    620: QUARANTINE_NPC_DIALOGUES,
    622: GENERATION_NPC_DIALOGUES,
}

# Field 622's visible crowd actors are initialized with one 0x2A
# DISABLE_DIALOG_ACTIVATION each.  Replacing that one-byte init operation with
# RESET_ACCUMULATED_INPUT_MASK preserves every following PC while enabling X.
GENERATION_NPC_ENABLE_PCS = (
    0x07F6, 0x0832, 0x086E, 0x08AC, 0x08EA, 0x0928,
    0x096E, 0x0994, 0x09D0, 0x0A0C, 0x0A91, 0x0B16,
    0x0B54, 0x0BDB, 0x0C19, 0x0C57, 0x0C85,
)

# Final identities describe the playable interaction pass, not the earlier
# cinematic-to-playable intermediate bundles.
COMPLETE_INTERACTION_FINAL_IDENTITIES = {
    623: (5846, "78584ce2a934ae372cd9d2e1d579b4b830574cf17f0efe6e3dd2d2a02159d9c0", 31384, "0c87a78fa5ee1430e91169b999239b33d634f3fb7479082183026d73cac657ac"),
    621: (5808, "80538d81c7fe6180dd025e8a0370d4d8f0641958c37aa573b9d551fbc9183b17", 130308, "01262d1b98f02617bb7aa7a0ae38d1324c68916fac24f3d032c3fbc5d3ec4508"),
    620: (4877, "08194e5d8b5a33510237131040462a9d49f133990981b6404121533c10dcd755", 147196, "4ce00e6c2d08d3f8847c249513ab9a5bebb42af19a7bc803c2a4c6f66034676d"),
    624: (10029, "4923042132729bd9ddfd4620c6ad5cab826dfc7ee00020776ee9633c6dc67d08", 61728, "92893203be3e8174fc486229669c631b2bc8cc24fc7ab64ec9a97b367816be79"),
    626: (7609, "357d24cf33b124b4969691ce08886ba403d65c9cc5daab02a3891513c8ed6d70", 34780, "d05cdfcc0c752772bbbca09580ee55dbaed76e4103d9b88037816b866001b5b3"),
    625: (5060, "4f277dab6d873329af5b46b1057d4b96a7f445ada922b82a05b12314ffd0eadc", 44816, "0aeaf6d54e2f73aa36f3c1d7febb7cc809a3f025ebe7b44c8e91a28b3ff6c287"),
    622: (6067, "7bd4d4eb27bfd1499514063fee54d336812754a633a78a71c2a735f747e73d39", 104212, "eb0a10ee62da36d67f79b672818cdbeb244965158973cc4536de32ecbd0a7c9b"),
}

# The retail ATEL tables end before these fields' header actor tables: every
# later header record is a static model node.  Added scripted door entities
# therefore need matching header records inserted at the old ATEL boundary;
# merely extending ATEL would reinterpret and hide the first static models.
INTERACTION_HEADER_IDENTITIES = {
    623: (1280, "ccd7e6ee77014000cc2743b8f5ac041be086ec9d9f8e28509869a8cc5ffd09e5"),
    621: (1136, "ab873323f57b9092eda19443b1329942846704577fd6c24e4b1dbf879d6b571e"),
    620: (896, "24ac04fcafeb0301d50dbb2d3d7843255baea2c20c52f9390eca8d4470361a4e"),
    622: (1168, "bc97113cddc4eb4430803f4e66870bcb5fe130aa4d9478ee2ab1d51e7a962466"),
}
# Header identities after authentic static door leaves are promoted into the
# contiguous scripted range.  Filled only for rooms with visible model-backed
# reciprocal doors; packed identities below include rebuilt stream offsets.
ANIMATED_INTERACTION_HEADER_IDENTITIES = {
    623: (1280, "8de1f0130303b2714ec899dd5b4184f7effd87f1a9f3285ee092a4c0680ec04b"),
    621: (1136, "5d37c58ff7ef61c51de4055d3fc809a2b0fb71228f325d49bcda79dff7b1dfc4"),
    620: (896, "24ac04fcafeb0301d50dbb2d3d7843255baea2c20c52f9390eca8d4470361a4e"),
    622: (1168, "afd2e198a8dfafd142ecf53b1fafbfe95a15f49ba21034b0fc4465145796f2fe"),
}
PACKED_INTERACTION_HEADER_IDENTITIES = {
    623: (1280, "873e0c78f24d17f0ac77acdbb73c3f814922e837a54cc93c7f92ecfbaaac48e9"),
    621: (1136, "4223000fcfa4d6fa9d939824792470cb5b672f59dea364b47041b27b6029f1e5"),
    620: (896, "b685089cbaf0af14712df6a33071807ecdeeb1c4dcaa8131cf1cffc47d71b8c5"),
    622: (1168, "02de63811b1f117f264a4f19d24e321545c433bf2f3e910eb43decb91378b29e"),
}
NATIVE_NPC_DIALOGUE_IDENTITIES = {
    621: (1076, "0dd8e053e816e9568aad7b81d080b8b0e9b1c4d1246f298a561f2a6b0658df0b"),
    620: (2325, "d70b69c32070488c143a33eec641b2b84d3bc67f6a231b096e3472ad7ad5229a"),
    622: (4354, "ebc3d9bc03c73b66eec1cd8cb169016a943df5b53ad239aaef099c84d3613a2f"),
}
SURFACE_SHORTCUT_DIALOGUE_IDENTITIES = {
    623: (156, "b371f3d019f4cebb6fd494fa3f81c15e8568adad6f7a1539ef7bd8a1698ab43a"),
}
INTERACTIVE_DONOR_FINAL_IDENTITIES = {
    549: (
        3106,
        "a4916d24803e4dc37e6262bb0c6407495f13cd7a36058434f6586143fdd36733",
        22336,
        "95c895409365e53108068f2e687de91e5e4886e4e9cd65485f37fb1587f3ae32",
    ),
    550: (
        4598,
        "0bdf23559f4df81a1adb49a7fa5ccb46811b584bf54fea634cf2ff7209804e1a",
        24400,
        "a0ce91d55a7935e932355ae21168c39a43df8ff7cfb32e33650f9f8b96c46d50",
    ),
    565: (
        3478,
        "d3902f6f4ce8835cea76071197cc63aa73deb4594cb0c15568e52728f5365e37",
        759,
        "7e28313160ef9b6792915228208d1c099fea00e392b0709f726eec5dbdcb0b5f",
        81188,
        "abfcc423e22599228a0b2b114ab141ed323f63bcd972ead558cc118d0be44cb6",
    ),
    589: (
        4058,
        "bf77ce8a8ab186690796923f22cd373130bc8bf3d3e29b8da2f7a3c14ad85bf0",
        50720,
        "bb6a24975644eb4b02f6cd99915d5b45119e3ddeed5d751a30e421c76235b740",
    ),
}
INTERACTIVE_DONOR_HEADER_IDENTITIES = {
    549: (736, "a17b189e46125eacff98018d3441acfb5bd30fa0f6a620203b0de095bbb201cf"),
    550: (960, "165f4ac61eb320d76fc4ae7016728f0d9d275e4713541aaaf6c187427de5660c"),
    565: (880, "5d4073d632b3e6d9ef3f17d0a9ccb303442555c8044c4f1c9fa8875f34629e5c"),
    589: (816, "ef1774caac105e945e0415c06eeeec57db594a993ee699973ba3fffe508cad25"),
}


def _extract_field_pair(
    image: Mode2Image,
    entries: Sequence[object],
    directory_first_file: int,
    identity: SourceIdentity,
) -> tuple[bytes, bytes]:
    local = FIRST_FIELD_LOCAL_FILE + 2 * identity.scene
    result: list[bytes] = []
    for expected_id, local_file in (
        (identity.bundle_id, local),
        (identity.graphics_id, local + 1),
    ):
        fat_index = directory_file_fat_index(directory_first_file, local_file)
        if fat_index + 5 != expected_id:
            raise SurfaceSoylentBuildError(
                f"Field {identity.scene} resolved to canonical {fat_index + 5}, "
                f"expected {expected_id}"
            )
        result.append(image.extract_entry(entries[fat_index]))
    return result[0], result[1]


def load_source_fields(source_disc: Path | str) -> dict[int, tuple[bytes, bytes]]:
    image = Mode2Image(source_disc)
    entries = image.read_index()
    first = image.read_directories()[FIELD_DIRECTORY].first_file
    result: dict[int, tuple[bytes, bytes]] = {}
    for identity in SOURCE_FIELDS:
        bundle, graphics = _extract_field_pair(image, entries, first, identity)
        if len(bundle) != identity.bundle_size or _sha256(bundle) != identity.bundle_sha256:
            raise SurfaceSoylentBuildError(
                f"Field {identity.scene} bundle does not match the frozen Disc 2 source"
            )
        if len(graphics) != identity.graphics_size or _sha256(graphics) != identity.graphics_sha256:
            raise SurfaceSoylentBuildError(
                f"Field {identity.scene} graphics do not match the frozen Disc 2 source"
            )
        parsed = parse_field(bundle)
        script = parsed.parts[SCRIPT_INDEX].data
        if len(script) != identity.script_size or _sha256(script) != identity.script_sha256:
            raise SurfaceSoylentBuildError(
                f"Field {identity.scene} ATEL script changed from its audit"
            )
        if len(parsed.header) != identity.header_size or _sha256(parsed.header) != identity.header_sha256:
            raise SurfaceSoylentBuildError(
                f"Field {identity.scene} header changed from its audit"
            )
        result[identity.scene] = (bundle, graphics)
    return result


def load_donor_fields(donor_disc: Path | str) -> dict[int, tuple[bytes, bytes]]:
    """Load the Solaris/Krelian donor rooms from their natural Disc 1 fields."""

    image = Mode2Image(donor_disc)
    entries = image.read_index()
    first = image.read_directories()[FIELD_DIRECTORY].first_file
    result: dict[int, tuple[bytes, bytes]] = {}
    for identity in DONOR_FIELDS:
        local = FIRST_FIELD_LOCAL_FILE + 2 * identity.scene
        bundle_index = directory_file_fat_index(first, local)
        graphics_index = directory_file_fat_index(first, local + 1)
        bundle = image.extract_entry(entries[bundle_index])
        graphics = image.extract_entry(entries[graphics_index])
        if len(bundle) != identity.bundle_size or _sha256(bundle) != identity.bundle_sha256:
            raise SurfaceSoylentBuildError(
                f"Disc 1 donor field {identity.scene} bundle changed"
            )
        if len(graphics) != identity.graphics_size or _sha256(graphics) != identity.graphics_sha256:
            raise SurfaceSoylentBuildError(
                f"Disc 1 donor field {identity.scene} graphics changed"
            )
        parsed = parse_field(bundle)
        script = parsed.parts[SCRIPT_INDEX].data
        if len(script) != identity.script_size or _sha256(script) != identity.script_sha256:
            raise SurfaceSoylentBuildError(
                f"Disc 1 donor field {identity.scene} script changed"
            )
        if len(parsed.header) != identity.header_size or _sha256(parsed.header) != identity.header_sha256:
            raise SurfaceSoylentBuildError(
                f"Disc 1 donor field {identity.scene} header changed"
            )
        result[identity.scene] = (bundle, graphics)
    return result


def verify_donor_targets_are_dummy(source_disc: Path | str) -> None:
    identities = {
        canonical_id: (len(DONOR_DUMMY), DONOR_DUMMY_SHA256)
        for identity in DONOR_FIELDS
        for canonical_id in (identity.bundle_id, identity.graphics_id)
    }
    resources = _load_canonical_resources(source_disc, identities)
    if any(data != DONOR_DUMMY for data in resources.values()):
        raise SurfaceSoylentBuildError("Disc 2 donor target is not the checked dummy")


def _load_canonical_resources(
    source_disc: Path | str,
    identities: dict[int, tuple[int, str]],
) -> dict[int, bytes]:
    """Extract checked canonical resources from an already-built base disc."""

    image = Mode2Image(source_disc)
    entries = image.read_index()
    result: dict[int, bytes] = {}
    for canonical_id, (expected_size, expected_sha256) in identities.items():
        fat_index = canonical_id - 5
        if not 0 <= fat_index < len(entries):
            raise SurfaceSoylentBuildError(
                f"Canonical resource {canonical_id} lies outside the disc index"
            )
        data = image.extract_entry(entries[fat_index])
        if len(data) != expected_size or _sha256(data) != expected_sha256:
            raise SurfaceSoylentBuildError(
                f"Base resource {canonical_id} is not the checked Mass-Driver release"
            )
        result[canonical_id] = data
    return result


def _split_menu_archive(data: bytes) -> tuple[bytes, list[bytes]]:
    if len(data) < 8:
        raise SurfaceSoylentBuildError("Shared menu archive is truncated")
    count = struct.unpack_from("<I", data, 0)[0]
    header_size = 4 + 4 * count
    if count != len(mass_driver.MENU_SHOP_ARCHIVE_OFFSETS) or header_size > len(data):
        raise SurfaceSoylentBuildError("Shared menu archive entry count changed")
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    if (
        offsets[0] < header_size
        or any(offset % 4 or offset >= len(data) for offset in offsets)
        or any(left >= right for left, right in zip(offsets, offsets[1:]))
    ):
        raise SurfaceSoylentBuildError("Shared menu archive offsets are invalid")
    entries = [
        data[start : offsets[index + 1] if index + 1 < count else len(data)]
        for index, start in enumerate(offsets)
    ]
    return data[: offsets[0]], entries


def _rebuild_menu_archive(header: bytes, entries: Sequence[bytes]) -> bytes:
    result = bytearray(header)
    offsets: list[int] = []
    for entry in entries:
        if len(result) % 4:
            result.extend(bytes((-len(result)) % 4))
        offsets.append(len(result))
        result.extend(entry)
    struct.pack_into(f"<{len(offsets)}I", result, 4, *offsets)
    return bytes(result)


def _build_surface_active_labels(image_bundle: bytes, font: bytes) -> tuple[bytes, bytes]:
    """Enable the existing Surface label without changing the frozen Mass builder."""

    base_atlas, base_font = mass_driver._build_title_menu_labels(image_bundle, font)
    if (
        _sha256(base_atlas) != mass_driver.TITLE_MENU_LABEL_TEXTURE_SHA256
        or _sha256(base_font) != mass_driver.TITLE_MENU_PATCHED_FONT_SHA256
    ):
        raise SurfaceSoylentBuildError("Mass-Driver title-label base changed")
    image_x, image_y, width_words, image_height, source_pixels = (
        mass_driver._title_menu_standard_font_pixels(image_bundle)
    )
    _count, _offsets, source_records = mass_driver._title_menu_font_records(font)

    def source_pixel(x: int, y: int) -> int:
        if not (0 <= x < width_words * 4 and 0 <= y < image_height):
            raise SurfaceSoylentBuildError("Surface label glyph left its source TIM")
        pixel_index = y * width_words * 4 + x
        packed = source_pixels[pixel_index // 2]
        return (packed >> 4) & 0x0F if pixel_index & 1 else packed & 0x0F

    def menu_font_index(character: str) -> int:
        if "0" <= character <= "9":
            return ord(character) - ord("0")
        if "A" <= character <= "Z":
            return 0x0A + ord(character) - ord("A")
        if "a" <= character <= "z":
            return 0x24 + ord(character) - ord("a")
        if character == "-":
            return 0x92
        raise SurfaceSoylentBuildError(
            f"Surface title label contains unsupported character {character!r}"
        )

    def glyph_canvas(character: str) -> list[list[int]]:
        if character == " ":
            return [[0] * 3 for _ in range(mass_driver.TITLE_MENU_LABEL_TEXTURE_HEIGHT)]
        record = source_records[menu_font_index(character)]
        if len(record) != 32 or struct.unpack_from("<HH", record, 0) != (1, 0):
            raise SurfaceSoylentBuildError("Surface label source glyph changed")
        values = struct.unpack_from("<14h", record, 4)
        texture_u, texture_v, width, height, offset_x, offset_y = values[:6]
        clut_x, clut_y, tpage_x, tpage_y = values[9:13]
        if (
            values[6:9] != (4, 0, 0)
            or (clut_x, clut_y) != mass_driver.TITLE_MENU_STANDARD_CLUT
            or (tpage_x, tpage_y) != (479, 120)
            or offset_x < 0
            or offset_y < 0
            or width <= 0
            or height <= 0
            or offset_y + height > mass_driver.TITLE_MENU_LABEL_TEXTURE_HEIGHT
        ):
            raise SurfaceSoylentBuildError("Surface label glyph layout changed")
        page_x = (tpage_x // 64) * 256
        page_y = (tpage_y // 256) * 256
        local_x = page_x + texture_u - image_x * 4
        local_y = page_y + texture_v - image_y
        canvas = [
            [0] * max(1, offset_x + width)
            for _ in range(mass_driver.TITLE_MENU_LABEL_TEXTURE_HEIGHT)
        ]
        for y in range(height):
            for x in range(width):
                canvas[offset_y + y][offset_x + x] = source_pixel(
                    local_x + x,
                    local_y + y,
                )
        occupied_x = [
            x for row in canvas for x, value in enumerate(row) if value != 0
        ]
        if not occupied_x:
            raise SurfaceSoylentBuildError("Surface label glyph has no visible pixels")
        left, right = min(occupied_x), max(occupied_x)
        return [row[left : right + 1] for row in canvas]

    glyphs = [glyph_canvas(character) for character in mass_driver.TITLE_MENU_LABELS[1]]
    rendered_width = sum(len(glyph[0]) for glyph in glyphs) + len(glyphs) - 1
    rendered = [
        [0] * rendered_width
        for _ in range(mass_driver.TITLE_MENU_LABEL_TEXTURE_HEIGHT)
    ]
    cursor = 0
    for glyph in glyphs:
        for y, row in enumerate(glyph):
            rendered[y][cursor : cursor + len(row)] = row
        cursor += len(glyph[0]) + 1
    if rendered_width != mass_driver.TITLE_MENU_LABEL_SOURCE_WIDTHS[1]:
        raise SurfaceSoylentBuildError("Surface title label width changed")

    atlas_rows: list[list[int]] = []
    for row_index in range(mass_driver.TITLE_MENU_LABEL_TEXTURE_HEIGHT):
        packed_row = base_atlas[
            row_index * (mass_driver.TITLE_MENU_LABEL_TEXTURE_WIDTH // 2) :
            (row_index + 1) * (mass_driver.TITLE_MENU_LABEL_TEXTURE_WIDTH // 2)
        ]
        row: list[int] = []
        for packed in packed_row:
            row.extend((packed & 0x0F, (packed >> 4) & 0x0F))
        atlas_rows.append(row)
    texture_u = mass_driver.TITLE_MENU_LABEL_TEXTURE_U[1]
    for y, row in enumerate(rendered):
        atlas_rows[y][texture_u : texture_u + len(row)] = row
    active_atlas = bytearray()
    for row in atlas_rows:
        for x in range(0, len(row), 2):
            active_atlas.append(row[x] | (row[x + 1] << 4))
    if _sha256(active_atlas) != SURFACE_TITLE_ATLAS_SHA256:
        raise SurfaceSoylentBuildError("Surface-active title atlas changed")

    count, _offsets, records = mass_driver._title_menu_font_records(base_font)
    records = list(records)
    glyph_index = mass_driver.TITLE_MENU_LABEL_GLYPHS[1]
    header_values = struct.unpack_from("<HH", records[glyph_index], 0)
    values = list(struct.unpack_from("<14h", records[glyph_index], 4))
    if tuple(values[9:11]) != mass_driver.TITLE_MENU_DISABLED_CLUT:
        raise SurfaceSoylentBuildError("Surface title label is no longer disabled in base")
    values[9:11] = mass_driver.TITLE_MENU_STANDARD_CLUT
    records[glyph_index] = struct.pack("<HH14h", *header_values, *values)
    rebuilt_font = bytearray(struct.pack("<I", count))
    rebuilt_font.extend(bytes(count * 2))
    offsets: list[int] = []
    for record in records:
        offsets.append(len(rebuilt_font))
        rebuilt_font.extend(record)
    struct.pack_into(f"<{count}H", rebuilt_font, 4, *offsets)
    active_font = bytes(rebuilt_font)
    if (
        len(active_font) != mass_driver.TITLE_MENU_PATCHED_FONT_SIZE
        or _sha256(active_font) != SURFACE_TITLE_FONT_SHA256
    ):
        raise SurfaceSoylentBuildError("Surface-active title font changed")
    return bytes(active_atlas), active_font


def _surface_title_labels(shared: bytes) -> tuple[bytes, bytes]:
    header, entries = _split_menu_archive(shared)
    images = mass_driver._decode_menu_archive_entry(
        entries[mass_driver.TITLE_MENU_IMAGE_ARCHIVE_ENTRY],
        expected_size=mass_driver.TITLE_MENU_IMAGE_DECODED_SIZE,
        expected_sha256=mass_driver.TITLE_MENU_IMAGE_DECODED_SHA256,
        label="title-menu image bundle",
    )
    font, consumed = mass_driver._decode_lzss_complete_groups(
        entries[mass_driver.TITLE_MENU_FONT_ARCHIVE_ENTRY]
    )
    if (
        consumed > len(entries[mass_driver.TITLE_MENU_FONT_ARCHIVE_ENTRY])
        or len(font) != mass_driver.TITLE_MENU_PATCHED_FONT_SIZE
        or _sha256(font) != mass_driver.TITLE_MENU_PATCHED_FONT_SHA256
    ):
        raise SurfaceSoylentBuildError("Mass-Driver title font changed")
    atlas, active_font = _build_surface_active_labels(images, font)
    packed_font = mass_driver._compress_lzss_exact_complete_groups(active_font)
    decoded_font, consumed = mass_driver._decode_lzss_complete_groups(packed_font)
    if decoded_font != active_font or consumed > len(packed_font):
        raise SurfaceSoylentBuildError("Surface-active title font failed decoding")
    entries[mass_driver.TITLE_MENU_FONT_ARCHIVE_ENTRY] = packed_font
    result = _rebuild_menu_archive(header, entries)
    expected_size, expected_sha256 = TITLE_FINAL_IDENTITIES[2593]
    if len(result) != expected_size or _sha256(result) != expected_sha256:
        raise SurfaceSoylentBuildError("Surface-active shared menu archive changed")
    return atlas, result


def _patch_surface_title_graphics(source: bytes, atlas: bytes) -> bytes:
    offset = mass_driver.TITLE_MENU_GRAPHICS_LABEL_PIXELS_OFFSET
    end = offset + len(atlas)
    if (
        len(atlas) != 1152
        or _sha256(atlas) != SURFACE_TITLE_ATLAS_SHA256
        or _sha256(source[offset:end]) != mass_driver.TITLE_MENU_LABEL_TEXTURE_SHA256
    ):
        raise SurfaceSoylentBuildError("Mass-Driver title label atlas changed")
    patched = bytearray(source)
    patched[offset:end] = atlas
    result = bytes(patched)
    expected_size, expected_sha256 = TITLE_FINAL_IDENTITIES[1587]
    if len(result) != expected_size or _sha256(result) != expected_sha256:
        raise SurfaceSoylentBuildError("Surface-active title graphics changed")
    return result


def _patch_surface_title_field(source_bundle: bytes) -> bytes:
    parsed = parse_field(source_bundle)
    components = [part.data for part in parsed.parts]
    script = components[SCRIPT_INDEX]
    if (
        len(script) != mass_driver.TITLE_MENU_FIELD_SCRIPT_PATCHED_SIZE
        or _sha256(script) != mass_driver.TITLE_MENU_FIELD_SCRIPT_PATCHED_SHA256
    ):
        raise SurfaceSoylentBuildError("Mass-Driver title field script changed")
    editor = ScriptEditor(script)
    mass_pc = 0x016C
    if editor.bytecode[mass_pc : mass_pc + 5] != _change_field(MASS_DRIVER_ENTRY_FIELD, 0):
        raise SurfaceSoylentBuildError("Mass-Driver title destination moved")
    patched_script = bytearray(script)
    bytecode_offset = editor.bytecode_offset
    patched_script[
        bytecode_offset + mass_pc : bytecode_offset + mass_pc + 5
    ] = _change_field(SURFACE_ENTRY_FIELD, SURFACE_ENTRY_PARAMETER)
    editor = ScriptEditor(bytes(patched_script))
    appended_mass_pc = editor.append_raw_routine(_change_field(MASS_DRIVER_ENTRY_FIELD, 0))
    if appended_mass_pc != 0x0171:
        raise SurfaceSoylentBuildError("Combined title Mass-Driver routine moved")
    patched_script = bytearray(editor.to_bytes())
    bytecode_offset = editor.bytecode_offset
    route_branch = bytes.fromhex("02 02 04 00 00 40 6C 01")
    route_jump = bytes.fromhex("01 71 01")
    current_branch = mass_driver.TITLE_MENU_FIELD_MASS_DRIVER_FALLTHROUGH_PATCHED
    branch_start = bytecode_offset + mass_driver.TITLE_MENU_FIELD_MASS_DRIVER_FALLTHROUGH_PC
    if patched_script[branch_start : branch_start + 8] != current_branch:
        raise SurfaceSoylentBuildError("Mass-Driver title route branch changed")
    if patched_script[branch_start + 8 : branch_start + 11] != bytes.fromhex("FE 60 0D"):
        raise SurfaceSoylentBuildError("Title route continuation changed")
    patched_script[branch_start : branch_start + 8] = route_branch
    patched_script[branch_start + 8 : branch_start + 11] = route_jump
    script = bytes(patched_script)
    if len(script) != TITLE_FIELD_SCRIPT_SIZE or _sha256(script) != TITLE_FIELD_SCRIPT_SHA256:
        raise SurfaceSoylentBuildError("Combined title field script changed")
    components[SCRIPT_INDEX] = script
    bundle = build_field_preserving(
        source_bundle,
        components,
        (SCRIPT_INDEX,),
        compact_changed=True,
    )
    expected_size, expected_sha256 = TITLE_FINAL_IDENTITIES[1586]
    if len(bundle) != expected_size or _sha256(bundle) != expected_sha256:
        raise SurfaceSoylentBuildError("Combined title field bundle changed")
    if tuple(part.data for part in parse_field(bundle).parts) != tuple(components):
        raise SurfaceSoylentBuildError("Combined title field failed round trip")
    return bundle


def _patch_complete_surface_title_field(combined_bundle: bytes) -> bytes:
    """Clear only Surface puzzle bits before entering the complete route."""

    expected_size, expected_sha256 = TITLE_FINAL_IDENTITIES[1586]
    if len(combined_bundle) != expected_size or _sha256(combined_bundle) != expected_sha256:
        raise SurfaceSoylentBuildError("Two-choice title field base changed")
    parsed = parse_field(combined_bundle)
    components = [part.data for part in parsed.parts]
    script = components[SCRIPT_INDEX]
    editor = ScriptEditor(script)
    reset_pc = editor.append_raw_routine(SURFACE_STATE_RESET_ROUTINE)
    if reset_pc != SURFACE_STATE_RESET_PC:
        raise SurfaceSoylentBuildError("Surface puzzle reset routine moved")
    patched_script = bytearray(editor.to_bytes())
    target_offset = editor.bytecode_offset + 0x00BE
    if patched_script[target_offset : target_offset + 2] != bytes.fromhex("6C 01"):
        raise SurfaceSoylentBuildError("Surface title dispatch target changed")
    patched_script[target_offset : target_offset + 2] = _u16(SURFACE_STATE_RESET_PC)
    script = bytes(patched_script)
    if (
        len(script) != COMPLETE_TITLE_FIELD_SCRIPT_SIZE
        or _sha256(script) != COMPLETE_TITLE_FIELD_SCRIPT_SHA256
    ):
        raise SurfaceSoylentBuildError("Complete Surface title script changed")
    components[SCRIPT_INDEX] = script
    bundle = build_field_preserving(
        combined_bundle,
        components,
        (SCRIPT_INDEX,),
        compact_changed=True,
    )
    if (
        len(bundle) != COMPLETE_TITLE_FIELD_BUNDLE_SIZE
        or _sha256(bundle) != COMPLETE_TITLE_FIELD_BUNDLE_SHA256
    ):
        raise SurfaceSoylentBuildError("Complete Surface title field changed")
    if tuple(part.data for part in parse_field(bundle).parts) != tuple(components):
        raise SurfaceSoylentBuildError("Complete Surface title field failed round trip")
    return bundle


def _patch_surface_title_overlay(source: bytes) -> bytes:
    patched = bytearray(source)
    edits = (
        (0x001C, bytes.fromhex("50 54 1C 80")),
        (0x0020, bytes.fromhex("2C 5A 1C 80")),
        # The menu performs a second selection-indexed cleanup dispatch.  Its
        # retail case 8 tears down an initialized Load/Save screen; Surface
        # never opens that screen, so use case 9's intentional no-op cleanup.
        (0x01FC, bytes.fromhex("B0 31 1E 80")),
        (
            0x0380,
            bytes.fromhex(
                "36 03 82 90 01 00 03 34 AE 01 43 10 00 00 00 00 "
                "FF FF 42 24 91 16 07 08 36 03 82 A0"
            ),
        ),
        (
            0x039C,
            bytes.fromhex(
                "36 03 82 90 02 00 03 34 A7 01 43 10 00 00 00 00 "
                "01 00 42 24 91 16 07 08 36 03 82 A0"
            ),
        ),
        (0x0960, bytes.fromhex("8E FE 62 10")),
        (0x0970, bytes.fromhex("83 FE 71 10")),
        (
            0x09EC,
            bytes.fromhex(
                "06 80 02 3C 60 94 42 90 02 00 03 34 0A 00 43 14 "
                "01 00 02 32 08 00 40 10 06 80 02 3C A0 25 42 8C "
                "36 03 42 90 26 10 50 00 02 00 42 2C 02 00 40 10 "
                "00 00 00 00 04 00 04 34 5D 21 07 08 00 00 00 00"
            ),
        ),
        (
            0x0A2C,
            bytes.fromhex(
                "0C 80 01 3C 01 00 02 34 6A 3E 22 A4 "
                # Cold boot already loaded resource 2595.  Enter the native
                # case-9 close tail after tagging Surface, rather than calling
                # loadInitialGameState a second time from this custom case.
                "12 15 07 08 00 00 00 00"
            ),
        ),
        (0x0A40, bytes(4)),
    )
    for offset, replacement in edits:
        patched[offset : offset + len(replacement)] = replacement
    result = bytes(patched)
    expected_size, expected_sha256 = TITLE_FINAL_IDENTITIES[2599]
    if len(result) != expected_size or _sha256(result) != expected_sha256:
        raise SurfaceSoylentBuildError("Combined title-menu overlay changed")
    if (
        result[mass_driver.TITLE_MENU_CONFIRM_SOUND_DISPATCH_OFFSET :
               mass_driver.TITLE_MENU_CONFIRM_SOUND_DISPATCH_OFFSET + 8]
        != mass_driver.TITLE_MENU_CONFIRM_SOUND_DISPATCH
        or result[mass_driver.TITLE_MENU_DIRECTION_SOUND_DISPATCH_OFFSET :
                  mass_driver.TITLE_MENU_DIRECTION_SOUND_DISPATCH_OFFSET + 4]
        != mass_driver.TITLE_MENU_DIRECTION_SOUND_DISPATCH_PATCHED
    ):
        raise SurfaceSoylentBuildError("Combined title-menu native sound dispatch changed")
    return result


def prepare_title_integration(
    source_disc: Path | str,
    *,
    complete_dungeon: bool = False,
    include_initial_gamestate: bool = False,
) -> tuple[PreparedTitleResource, ...]:
    sources = _load_canonical_resources(source_disc, TITLE_BASE_IDENTITIES)
    atlas, shared = _surface_title_labels(sources[2593])
    title_field = _patch_surface_title_field(sources[1586])
    if complete_dungeon:
        title_field = _patch_complete_surface_title_field(title_field)
    patched = {
        1586: title_field,
        1587: _patch_surface_title_graphics(sources[1587], atlas),
        2593: shared,
        2595: sources[2595],
        2599: _patch_surface_title_overlay(sources[2599]),
    }
    names = {
        1586: (
            "Title field: Mass-Driver and Surface routes",
            (
                "1586_title_screen_complete_surface_route.bin"
                if complete_dungeon
                else "1586_title_screen_mass_driver_surface_routes.bin"
            ),
        ),
        1587: ("Title graphics: two active destinations", "1587_title_screen_two_active_destinations.bin"),
        2593: ("Shared menu: Surface title label enabled", "2593_menu_shared_surface_enabled.bin"),
        2595: ("Initial GameState: checked Mass-Driver foundation", "2595_surface_initial_gamestate.bin"),
        2599: ("Title overlay: two-row selection and route tag", "2599_title_menu_mass_driver_surface.bin"),
    }
    canonical_ids = (
        (1586, 1587, 2593, 2595, 2599)
        if include_initial_gamestate
        else (1586, 1587, 2593, 2599)
    )
    return tuple(
        PreparedTitleResource(
            canonical_id,
            names[canonical_id][0],
            names[canonical_id][1],
            TITLE_BASE_IDENTITIES[canonical_id][1],
            patched[canonical_id],
        )
        for canonical_id in canonical_ids
    )


def _patch_bytecode(data: bytes, pc: int, expected: bytes, replacement: bytes) -> bytes:
    if len(expected) != len(replacement):
        raise SurfaceSoylentBuildError("ATEL checked patch must preserve size")
    editor = ScriptEditor(data)
    absolute = editor.bytecode_offset + pc
    if editor.bytecode[pc : pc + len(expected)] != expected:
        raise SurfaceSoylentBuildError(
            f"ATEL PC 0x{pc:04X} changed; expected {expected.hex(' ')}"
        )
    result = bytearray(data)
    result[absolute : absolute + len(expected)] = replacement
    return bytes(result)


def _patch_raw(data: bytes, offset: int, expected: bytes, replacement: bytes) -> bytes:
    if len(expected) != len(replacement):
        raise SurfaceSoylentBuildError("Checked raw patch must preserve size")
    if data[offset : offset + len(expected)] != expected:
        raise SurfaceSoylentBuildError(
            f"Checked raw patch failed at 0x{offset:04X}; expected {expected.hex(' ')}"
        )
    result = bytearray(data)
    result[offset : offset + len(expected)] = replacement
    return bytes(result)


def _patch_entry(data: bytes, edit: EntryEdit) -> bytes:
    return _patch_bytecode(
        data,
        1 + 7 * edit.parameter,
        edit.source.pack(),
        edit.playable.pack(),
    )


def _edge_poll(base: int, player_entity: int, edges: Iterable[Edge]) -> bytes:
    edges = tuple(edges)
    if not edges:
        raise SurfaceSoylentBuildError("Playable field requires at least one edge")
    result = bytearray(
        b"\x2D"
        + bytes((player_entity,))
        + _u16(POSITION_VARIABLES["x"])
        + _u16(POSITION_VARIABLES["z"])
        + _u16(POSITION_VARIABLES["y"])
    )
    for edge in edges:
        if edge.axis not in ("x", "z") or edge.comparison not in (0x44, 0x45):
            raise SurfaceSoylentBuildError("Unsupported edge-poll contract")
        transition = (
            b"\xFE\x54"
            + _change_field(edge.destination_field, edge.destination_parameter)
            + b"\x5B"
        )
        retry_pc = base + len(result) + 8 + len(transition)
        result.extend(
            b"\x02"
            + _u16(POSITION_VARIABLES[edge.axis])
            + _s16(edge.threshold)
            + bytes((edge.comparison,))
            + _u16(retry_pc)
            + transition
        )
    result.extend(b"\x5A\x01" + _u16(base))
    return bytes(result)


def _walkmesh_layer(walkmesh: bytes, layer: int) -> tuple[tuple[tuple[int, int, int], ...], ...]:
    layer_count = struct.unpack_from("<I", walkmesh, 0)[0]
    if not 0 <= layer < layer_count:
        raise SurfaceSoylentBuildError(f"Walkmesh layer {layer} is absent")
    triangle_bytes = struct.unpack_from("<I", walkmesh, 4 + 4 * layer)[0]
    if triangle_bytes % 14:
        raise SurfaceSoylentBuildError("Walkmesh triangle stream is misaligned")
    triangle_offset, vertex_offset = struct.unpack_from(
        "<II", walkmesh, 0x18 + 8 * layer
    )
    indices = tuple(
        struct.unpack_from("<3H", walkmesh, triangle_offset + 14 * index)
        for index in range(triangle_bytes // 14)
    )
    maximum = max(vertex for triangle in indices for vertex in triangle)
    vertices = tuple(
        struct.unpack_from("<hhhh", walkmesh, vertex_offset + 8 * index)[:3]
        for index in range(maximum + 1)
    )
    return tuple(tuple(vertices[index] for index in triangle) for triangle in indices)


def _point_inside_triangle(point: tuple[int, int], triangle: Sequence[tuple[int, int, int]]) -> bool:
    x, z = point
    crosses = tuple(
        (end[0] - start[0]) * (z - start[2])
        - (end[2] - start[2]) * (x - start[0])
        for start, end in zip(triangle, (*triangle[1:], triangle[0]), strict=True)
    )
    return all(value >= 0 for value in crosses) or all(value <= 0 for value in crosses)


def validate_walkmesh_contract(spec: PlayableScene, walkmesh: bytes) -> None:
    layers: dict[int, tuple[tuple[tuple[int, int, int], ...], ...]] = {}
    for edit in spec.entry_edits:
        triangles = layers.setdefault(
            edit.playable.walkmesh,
            _walkmesh_layer(walkmesh, edit.playable.walkmesh),
        )
        if edit.triangle >= len(triangles) or not _point_inside_triangle(
            (edit.playable.x, edit.playable.z), triangles[edit.triangle]
        ):
            raise SurfaceSoylentBuildError(
                f"Field {spec.identity.scene} entry {edit.parameter} is outside "
                f"audited triangle {edit.triangle}"
            )
    triangles = layers.setdefault(0, _walkmesh_layer(walkmesh, 0))
    for edge in spec.edges:
        if edge.triangle >= len(triangles) or not _point_inside_triangle(
            edge.sample, triangles[edge.triangle]
        ):
            raise SurfaceSoylentBuildError(
                f"Field {spec.identity.scene} {edge.axis}-edge sample is outside "
                f"audited triangle {edge.triangle}"
            )


def prepare_playable_field(spec: PlayableScene, source_bundle: bytes, graphics: bytes) -> PreparedField:
    identity = spec.identity
    if len(source_bundle) != identity.bundle_size or _sha256(source_bundle) != identity.bundle_sha256:
        raise SurfaceSoylentBuildError(f"Field {identity.scene} source bundle drifted")
    if len(graphics) != identity.graphics_size or _sha256(graphics) != identity.graphics_sha256:
        raise SurfaceSoylentBuildError(f"Field {identity.scene} graphics drifted")
    parsed = parse_field(source_bundle)
    components = [part.data for part in parsed.parts]
    script = components[SCRIPT_INDEX]

    for edit in spec.entry_edits:
        script = _patch_entry(script, edit)

    for index, party in enumerate(spec.party):
        editor = ScriptEditor(script)
        if editor.get_script_pointer(party.entity, 0) != party.init_pc:
            raise SurfaceSoylentBuildError(
                f"Field {identity.scene} party e{party.entity} init pointer changed"
            )
        if editor.get_script_pointer(party.entity, 1) != party.update_pc:
            raise SurfaceSoylentBuildError(
                f"Field {identity.scene} party e{party.entity} update pointer changed"
            )
        selector = PARTY_SELECTORS[index]
        source = (
            b"\x16" + _immediate(party.source_character)
            + b"\xFE\x0D" + _immediate(party.source_character)
        )
        playable = b"\x16" + _immediate(selector) + b"\xFE\x0D" + _immediate(selector)
        script = _patch_bytecode(script, party.init_pc, source, playable)
        if spec.force_party_direction is not None:
            script = _patch_bytecode(
                script,
                party.init_pc + len(playable),
                b"\x5F\x03",
                b"\x5F" + bytes((spec.force_party_direction,)),
            )

    editor = ScriptEditor(script)
    playable_update_pc = editor.append_raw_routine(b"\xA7\x00")
    if playable_update_pc != spec.playable_update_pc:
        raise SurfaceSoylentBuildError(
            f"Field {identity.scene} playable update moved to 0x{playable_update_pc:04X}"
        )
    for party in spec.party:
        editor.set_script_pointer(party.entity, 1, playable_update_pc)

    if editor.get_script_pointer(spec.director_entity, 1) != spec.director_update_pc:
        raise SurfaceSoylentBuildError(
            f"Field {identity.scene} cinematic director pointer changed"
        )
    poll_pc = editor.bytecode_size
    poll = _edge_poll(poll_pc, spec.party[0].entity, spec.edges)
    if editor.append_raw_routine(poll) != spec.poll_pc:
        raise SurfaceSoylentBuildError(
            f"Field {identity.scene} edge poll moved from 0x{spec.poll_pc:04X}"
        )
    editor.set_script_pointer(spec.director_entity, 1, poll_pc)
    script = editor.to_bytes()
    if len(script) != spec.patched_script_size or _sha256(script) != spec.patched_script_sha256:
        raise SurfaceSoylentBuildError(
            f"Field {identity.scene} patched ATEL output changed: "
            f"{len(script)} bytes, SHA-256 {_sha256(script)}"
        )

    components[SCRIPT_INDEX] = script
    validate_walkmesh_contract(spec, components[1])
    bundle = build_field_preserving(
        source_bundle,
        components,
        (SCRIPT_INDEX,),
        compact_changed=True,
    )
    if len(bundle) != spec.patched_bundle_size or _sha256(bundle) != spec.patched_bundle_sha256:
        raise SurfaceSoylentBuildError(
            f"Field {identity.scene} packed output changed: "
            f"{len(bundle)} bytes, SHA-256 {_sha256(bundle)}"
        )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise SurfaceSoylentBuildError(
            f"Field {identity.scene} failed its decoded round trip"
        )
    return PreparedField(
        spec,
        source_bundle,
        graphics,
        parsed.header,
        tuple(components),
        bundle,
    )


def _quarantine_puzzle_dialogue() -> bytes:
    specs = (
        DialogueBlockSpec(
            0,
            58,
            4,
            "The people who had mutated\ninto what we called Verus...\n"
            "the essential human form...\ngathered at these facilities.<Close>",
        ),
        DialogueBlockSpec(
            1,
            58,
            4,
            "Among the humans-turned-\nVerus were those who attacked\n"
            "the unafflicted and devoured\ntheir flesh and blood.<Close>",
        ),
        DialogueBlockSpec(
            2,
            58,
            7,
            "That was because the flesh\nand blood of the unafflicted\n"
            "could ease the agony of the\nsudden molecular changes and\n"
            "prolong their lives a little.<Delay:30>\n \n"
            "Their lives were so short...<Close>",
        ),
        DialogueBlockSpec(
            3,
            56,
            4,
            "Before long, the severely\nmutated ones started to seek\n"
            "the flesh and blood of those\nwho were less mutated.<Close>",
        ),
        DialogueBlockSpec(
            4,
            58,
            4,
            "SURFACE QUARANTINE // BIOLOGICAL RELAYS\n"
            "Restore the three physiological markers.\n"
            "Caste clearance is administrative data.<Close>",
        ),
        DialogueBlockSpec(
            5,
            58,
            4,
            "POD A // GENOME\nHuman baseline retained.\nRelay toggled.<Close>",
        ),
        DialogueBlockSpec(
            6,
            58,
            4,
            "POD B // LIMITER\nLimiter collapse confirmed.\nRelay toggled.<Close>",
        ),
        DialogueBlockSpec(
            7,
            58,
            4,
            "POD C // NANOMACHINES\nSystemic contamination confirmed.\n"
            "Relay toggled.<Close>",
        ),
        DialogueBlockSpec(
            8,
            58,
            4,
            "POD D // CASTE INDEX\nSolaris clearance only.\n"
            "Not a biological marker.\nRelay toggled.<Close>",
        ),
        DialogueBlockSpec(
            9,
            58,
            4,
            "DIAGNOSTIC ROUTE DENIED\nThree biological relays are required.\n"
            "Exclude the caste index.<Close>",
        ),
        DialogueBlockSpec(
            10,
            58,
            4,
            "DIAGNOSTIC CONSENSUS ACCEPTED\nDesignation: HUMAN.\n"
            "Service route unsealed.<Close>",
        ),
        DialogueBlockSpec(
            11,
            58,
            4,
            "DIAGNOSTIC ROUTE COMPLETE\nBiological identity retained.\n"
            "Service route remains open.<Close>",
        ),
    )
    dialogue = encode_dialogue(specs)
    if (
        len(dialogue) != QUARANTINE_DIALOGUE_SIZE
        or _sha256(dialogue) != QUARANTINE_DIALOGUE_SHA256
    ):
        raise SurfaceSoylentBuildError("Surface quarantine dialogue changed")
    return dialogue


def prepare_intake_side_wings(prepared: PreparedField) -> PreparedField:
    """Add all audited reciprocal entries to the field-621 intake hub."""

    if prepared.spec.identity.scene != 621:
        raise SurfaceSoylentBuildError("Intake side-wing patch requires field 621")
    script = prepared.components[SCRIPT_INDEX]
    if (
        len(script) != prepared.spec.patched_script_size
        or _sha256(script) != prepared.spec.patched_script_sha256
    ):
        raise SurfaceSoylentBuildError("Playable intake baseline changed")
    side_entries = (
        EntryEdit(
            1,
            FieldEntry(870, 1190, 0, 0xFF, 0xFF),
            # The intake circulation is north of model 3.  Face away from
            # the reclosed leaf while camera 4 keeps its eye on that side.
            FieldEntry(870, 1190, 0, 4, 0),
            88,
        ),
        EntryEdit(
            2,
            FieldEntry(40, 840, 0, 0xFF, 0xFF),
            FieldEntry(0, 840, 0, 2, 6),
            17,
        ),
        EntryEdit(
            3,
            FieldEntry(1690, 840, 0, 0xFF, 0xFF),
            # Spawn far enough inside the vestibule that a held return press
            # cannot reselect the newly exact-plane x=1645 door carrier.
            FieldEntry(1730, 840, 0, 6, 2),
            81,
        ),
        EntryEdit(
            4,
            FieldEntry(40, 340, 0, 0xFF, 0xFF),
            FieldEntry(0, 396, 0, 2, 6),
            15,
        ),
        EntryEdit(
            5,
            FieldEntry(1690, 340, 0, 0xFF, 0xFF),
            FieldEntry(1730, 396, 0, 6, 2),
            84,
        ),
        EntryEdit(
            6,
            FieldEntry(32, 100, 0, 0, 0),
            # Camera 2 remains on the west circulation side; actor 6 faces
            # away from the model-10/11 vestibule panels.
            FieldEntry(112, 0, 0, 2, 6),
            2,
        ),
    )
    for edit in side_entries:
        script = _patch_entry(script, edit)
    editor = ScriptEditor(script)
    if (
        editor.bytecode_size != 0x022E
        or editor.bytecode[INTAKE_SIDE_WING_TAIL_PC:0x022E] != bytes.fromhex("5A 01 02 02")
    ):
        raise SurfaceSoylentBuildError("Intake edge-poll tail changed")
    if editor.append_raw_routine(INTAKE_SIDE_WING_TAIL[4:]) != 0x022E:
        raise SurfaceSoylentBuildError("Intake side-wing edge extension moved")
    script = _patch_bytecode(
        editor.to_bytes(),
        INTAKE_SIDE_WING_TAIL_PC,
        bytes.fromhex("5A 01 02 02"),
        INTAKE_SIDE_WING_TAIL[:4],
    )
    if len(script) != INTAKE_COMPLETE_SCRIPT_SIZE or _sha256(script) != INTAKE_COMPLETE_SCRIPT_SHA256:
        raise SurfaceSoylentBuildError("Complete intake script changed")
    components = list(prepared.components)
    components[SCRIPT_INDEX] = script
    bundle = build_field_preserving(
        prepared.bundle,
        components,
        (SCRIPT_INDEX,),
        compact_changed=True,
    )
    if len(bundle) != INTAKE_COMPLETE_BUNDLE_SIZE or _sha256(bundle) != INTAKE_COMPLETE_BUNDLE_SHA256:
        raise SurfaceSoylentBuildError("Complete intake bundle changed")
    if tuple(part.data for part in parse_field(bundle).parts) != tuple(components):
        raise SurfaceSoylentBuildError("Complete intake failed round trip")
    final_spec = replace(
        prepared.spec,
        role="intake hub with records and scanner branches",
        entry_edits=(
            tuple(edit for edit in prepared.spec.entry_edits if edit.parameter != 6)
            + side_entries
        ),
        edges=prepared.spec.edges + (
            Edge("x", 0, 0x45, 549, 0, (0, 840), 17),
            Edge("x", 1730, 0x44, 550, 0, (1730, 840), 81),
            Edge("z", 1131, 0x45, 565, 0, (866, 1131), 45),
            Edge("x", 88, 0x44, 565, 2, (88, 396), 14),
            Edge("x", 1645, 0x45, 565, 3, (1645, 396), 85),
        ),
        patched_script_size=INTAKE_COMPLETE_SCRIPT_SIZE,
        patched_script_sha256=INTAKE_COMPLETE_SCRIPT_SHA256,
        patched_bundle_size=INTAKE_COMPLETE_BUNDLE_SIZE,
        patched_bundle_sha256=INTAKE_COMPLETE_BUNDLE_SHA256,
    )
    validate_walkmesh_contract(final_spec, components[1])
    return PreparedField(
        final_spec,
        prepared.source_bundle,
        prepared.graphics,
        prepared.header,
        tuple(components),
        bundle,
    )


def prepare_quarantine_puzzle(prepared: PreparedField) -> PreparedField:
    """Turn field 620's four authentic rings into a biological relay puzzle."""

    if prepared.spec.identity.scene != 620:
        raise SurfaceSoylentBuildError("Quarantine puzzle requires prepared field 620")
    script = prepared.components[SCRIPT_INDEX]
    if (
        len(script) != prepared.spec.patched_script_size
        or _sha256(script) != prepared.spec.patched_script_sha256
    ):
        raise SurfaceSoylentBuildError("Quarantine playable baseline changed")
    editor = ScriptEditor(script)
    if (
        editor.bytecode_size != 0x0566
        or editor.get_script_pointer(1, 1) != 0x053A
        or _sha256(editor.bytecode[0x053A:0x0566]) != QUARANTINE_SOURCE_GATE_SHA256
    ):
        raise SurfaceSoylentBuildError("Quarantine edge controller changed")

    native_init_guards = (
        bytes.fromhex("BC 2A 2D FB 0E 04 10 04 12 04 35 14 04 00 04 40 00"),
        bytes.fromhex("BC 2A 2D FB 18 04 1A 04 1C 04 35 1E 04 00 04 40 00"),
        bytes.fromhex("BC 2A 2D FB 22 04 24 04 26 04 35 28 04 00 04 40 00"),
        bytes.fromhex("BC 2A 2D FB 2C 04 2E 04 30 04 35 32 04 00 04 40 00"),
    )
    for routine, guard in zip(QUARANTINE_RING_ROUTINES, native_init_guards, strict=True):
        entity, source_pointers, init_pc, action_pc, init_body, action_body = routine
        actual_pointers = tuple(editor.get_script_pointer(entity, index) for index in range(3))
        if actual_pointers != source_pointers:
            raise SurfaceSoylentBuildError(
                f"Quarantine ring e{entity} pointers changed: {actual_pointers!r}"
            )
        source_init = source_pointers[0]
        if editor.bytecode[source_init : source_init + len(guard)] != guard:
            raise SurfaceSoylentBuildError(f"Quarantine ring e{entity} init changed")
        if editor.append_raw_routine(init_body) != init_pc:
            raise SurfaceSoylentBuildError(f"Quarantine ring e{entity} init moved")
        if editor.append_raw_routine(action_body) != action_pc:
            raise SurfaceSoylentBuildError(f"Quarantine ring e{entity} action moved")
        editor.set_script_pointer(entity, 0, init_pc)
        editor.set_script_pointer(entity, 2, action_pc)
    if editor.append_raw_routine(QUARANTINE_GATE_ROUTINE) != QUARANTINE_GATE_PC:
        raise SurfaceSoylentBuildError("Quarantine relay gate moved")
    editor.set_script_pointer(1, 1, QUARANTINE_GATE_PC)
    script = editor.to_bytes()
    if len(script) != QUARANTINE_SCRIPT_SIZE or _sha256(script) != QUARANTINE_SCRIPT_SHA256:
        raise SurfaceSoylentBuildError("Surface quarantine puzzle script changed")

    components = list(prepared.components)
    components[SCRIPT_INDEX] = script
    components[7] = _quarantine_puzzle_dialogue()
    bundle = build_field_preserving(
        prepared.bundle,
        components,
        (SCRIPT_INDEX, 7),
        compact_changed=True,
    )
    if len(bundle) != QUARANTINE_BUNDLE_SIZE or _sha256(bundle) != QUARANTINE_BUNDLE_SHA256:
        raise SurfaceSoylentBuildError("Surface quarantine puzzle bundle changed")
    if tuple(part.data for part in parse_field(bundle).parts) != tuple(components):
        raise SurfaceSoylentBuildError("Surface quarantine puzzle failed round trip")

    final_spec = replace(
        prepared.spec,
        role="quarantine biological-relay puzzle",
        edges=(
            Edge("x", -352, 0x45, 621, 0, (-352, 0), 100),
            Edge("x", 352, 0x44, 565, 6, (352, 0), 182),
        ),
        poll_pc=QUARANTINE_GATE_PC,
        patched_script_size=QUARANTINE_SCRIPT_SIZE,
        patched_script_sha256=QUARANTINE_SCRIPT_SHA256,
        patched_bundle_size=QUARANTINE_BUNDLE_SIZE,
        patched_bundle_sha256=QUARANTINE_BUNDLE_SHA256,
    )
    return PreparedField(
        final_spec,
        prepared.source_bundle,
        prepared.graphics,
        prepared.header,
        tuple(components),
        bundle,
    )


def _door_controller_init(door: DoorController) -> bytes:
    """Build one hidden retail-style spatial X-action carrier."""

    if not all(
        1 <= value <= 0x7F
        for value in (door.interaction_half_width, door.interaction_half_depth)
    ):
        raise SurfaceSoylentBuildError("Door interaction bounds are outside 1..127")
    # A freshly appended entity has no native wrapper class.  INIT_ENTITY_SCRIPT
    # (BC) leaves that blank wrapper at 0x20, outside the scheduler's active
    # 0x0F00 classes: Cross can queue script 2, but the action never executes.
    # Give added carriers the same hidden, immovable bank-zero NPC setup used
    # by the proven Mass-Driver station controllers.  The final OP18 operand
    # supplies an explicit physical radius so the threshold cannot be walked
    # through or shoved out of alignment.  Reused entities keep their audited
    # native wrapper, but receive the same immovable bit: OP20/0x80 would make
    # an otherwise valid rectangular carrier non-colliding (a ghost door).
    if door.carrier_entity is None:
        collision_operand = min(
            door.interaction_half_width,
            door.interaction_half_depth,
        )
        return (
            b"\x0B\x00\x80"
            + b"\x19"
            + _s16(door.x)
            + _s16(door.z)
            + b"\xC0\x1A\x00"
            + b"\xF8\x00\x00\x20"
            + b"\xF8\x07\x04\x00"
            + b"\x18"
            + bytes(
                (
                    door.interaction_half_width,
                    door.interaction_half_depth,
                    0x64,
                    collision_operand,
                )
            )
            + b"\xF8\x00\x10\x00"
            + b"\x23"
            + b"\x00"
        )
    return (
        door.init_prefix
        + b"\x19"
        + _s16(door.x)
        + _s16(door.z)
        + b"\xC0"
        + b"\xF8\x00\x00\x20"
        # Do not require a narrow facing cone at irregular cinematic portals.
        # Proximity and a fresh native script-2 action press remain required.
        + b"\xF8\x07\x04\x00"
        + b"\x18"
        + bytes(
            (
                door.interaction_half_width,
                door.interaction_half_depth,
                0x64,
                0,
            )
        )
        + b"\xF8\x00\x10\x00"
        + b"\x23"
        + b"\x00"
    )


def _door_transition_action(door: DoorController) -> bytes:
    return (
        b"\xFE\x54"
        + _change_field(door.destination_field, door.destination_parameter)
        + b"\x5B"
    )


def _actor_dialogue_action(block_id: int) -> bytes:
    """Open actor-owned dialogue, wait for it to close, then stop."""

    return b"\xD2" + _u16(block_id) + b"\x00\x9C\x00"


def _append_dialogue_blocks(
    source: bytes,
    texts: Sequence[str],
    *,
    width: int,
    height: int,
) -> bytes:
    parsed = parse_dialogue(source)
    specs = [
        DialogueBlockSpec(block.block_id, block.width, block.height, block.text)
        for block in parsed.blocks
    ]
    for text in texts:
        specs.append(DialogueBlockSpec(len(specs), width, height, text))
    rebuilt = encode_dialogue(specs)
    reparsed = parse_dialogue(rebuilt)
    for before, after in zip(parsed.blocks, reparsed.blocks, strict=False):
        if (
            before.width,
            before.height,
            before.payload,
        ) != (
            after.width,
            after.height,
            after.payload,
        ):
            raise SurfaceSoylentBuildError("Existing dialogue changed while appending")
    return rebuilt


# Field 620's east door owns the relay result.  This is an actor action, not a
# coordinate poll: it drains the initiating Cross press before any denial or
# acceptance dialogue and unlocks input on failure.
QUARANTINE_DOOR_GATE_PC = 0x08CD
QUARANTINE_DOOR_GATE_ROUTINE = bytes.fromhex(
    "02 FA 03 00 01 46 DD 08 FE 54 98 35 82 06 80 5B "
    "35 E2 07 FA 03 00 3E E2 07 F0 00 40 02 E2 07 70 00 41 0D 09 "
    "74 5F 80 33 FE 54 31 20 00 02 09 26 01 80 01 F7 08 26 01 80 "
    "F5 09 00 01 9C FE 53 00 "
    "3A FA 03 08 00 40 74 50 80 33 FE 54 31 20 00 24 09 26 01 80 "
    "01 19 09 26 01 80 F5 0A 00 01 9C FE 54 98 35 82 06 80 5B"
)

# The east model-0 panel is the next retail header record after the west
# helper.  It can therefore become e26 in place: no static record is removed
# or reordered, and extending ATEL through it preserves every later node.
# Both success exits in the native relay action jump to one shared routine,
# which drains the initiating Cross press, slides the panel north 64 units,
# then performs the existing field-565/p6 transition.
QUARANTINE_EAST_DOOR_ANIMATION = DoorAnimation(
    565,
    6,
    (DoorLeafAnimation(26, 26, 0x0290, 0, 0, -2),),
)
QUARANTINE_EAST_DOOR_SUCCESS_SITES = (0x08D5, 0x092C)
QUARANTINE_EAST_DOOR_INIT_PC = 0x0A8B
QUARANTINE_EAST_DOOR_SLIDE_PC = 0x0A8E
QUARANTINE_EAST_DOOR_SUCCESS_PC = 0x0BAF
QUARANTINE_EAST_DOOR_ORIGINAL_SUCCESS = (
    b"\xFE\x54" + _change_field(565, 6) + b"\x5B"
)
QUARANTINE_EAST_DOOR_SUCCESS_REDIRECT = (
    b"\x01" + _u16(QUARANTINE_EAST_DOOR_SUCCESS_PC) + b"\x00" * 5
)
QUARANTINE_DOOR_GATE_FINAL_ROUTINE = (
    QUARANTINE_DOOR_GATE_ROUTINE[:0x08]
    + QUARANTINE_EAST_DOOR_SUCCESS_REDIRECT
    + QUARANTINE_DOOR_GATE_ROUTINE[0x10:0x5F]
    + QUARANTINE_EAST_DOOR_SUCCESS_REDIRECT
    + QUARANTINE_DOOR_GATE_ROUTINE[0x67:]
)


def _native_npc_dialogue_width(scene: int) -> int:
    return 56 if scene == 622 else 58


def _insert_added_door_header_records(
    header: bytes,
    *,
    scene: int,
    old_entity_count: int,
    doors: Sequence[DoorController],
) -> bytes:
    """Insert scripted carriers before every preserved static field node."""

    if len(header) < 0x190:
        raise SurfaceSoylentBuildError(f"Field {scene} header is truncated")
    actor_count = struct.unpack_from("<H", header, 0x18C)[0]
    if len(header) != 0x190 + actor_count * 16:
        raise SurfaceSoylentBuildError(
            f"Field {scene} actor table does not end at its header boundary"
        )
    if not old_entity_count < actor_count:
        raise SurfaceSoylentBuildError(
            f"Field {scene} has no audited static actors after ATEL"
        )
    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(actor_count)
    ]
    inserted = [
        mass_driver._field_actor_record(0x01E0, door.x, door.z, 0)
        for door in doors
    ]
    records[old_entity_count:old_entity_count] = inserted
    result = bytearray(header[:0x190] + b"".join(records))
    struct.pack_into("<H", result, 0x18C, len(records))
    identity = INTERACTION_HEADER_IDENTITIES.get(scene)
    if identity is not None and (len(result), _sha256(result)) != identity:
        raise SurfaceSoylentBuildError(
            f"Field {scene} interactive header identity changed"
        )
    return bytes(result)


def _promote_native_door_header_records(
    header: bytes,
    *,
    scene: int,
    first_helper_entity: int,
    animations: Sequence[DoorAnimation],
) -> bytes:
    """Rehome authentic static door leaves as contiguous script helpers."""

    actor_count = struct.unpack_from("<H", header, 0x18C)[0]
    if len(header) != 0x190 + actor_count * 16:
        raise SurfaceSoylentBuildError(
            f"Field {scene} animated-door header is malformed"
        )
    leaves = tuple(leaf for animation in animations for leaf in animation.leaves)
    if not leaves:
        return header
    expected_helpers = tuple(
        range(first_helper_entity, first_helper_entity + len(leaves))
    )
    if tuple(leaf.helper_entity for leaf in leaves) != expected_helpers:
        raise SurfaceSoylentBuildError(
            f"Field {scene} animated-door helpers are not contiguous after ATEL"
        )
    if first_helper_entity + len(leaves) > actor_count:
        raise SurfaceSoylentBuildError(
            f"Field {scene} lacks header records for its animated door helpers"
        )
    source_entities = tuple(leaf.source_header_entity for leaf in leaves)
    if len(set(source_entities)) != len(source_entities):
        raise SurfaceSoylentBuildError(
            f"Field {scene} repeats an animated door header record"
        )
    if any(entity < first_helper_entity or entity >= actor_count for entity in source_entities):
        raise SurfaceSoylentBuildError(
            f"Field {scene} animated door source is outside the static suffix"
        )

    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(actor_count)
    ]
    promoted: list[bytes] = []
    for leaf in leaves:
        record = records[leaf.source_header_entity]
        flags, _rx, _ry, _rz, x, y, z, model_index = struct.unpack(
            "<Hhhh hhh H", record
        )
        if flags != leaf.source_flags or model_index != leaf.model_index:
            raise SurfaceSoylentBuildError(
                f"Field {scene} door leaf e{leaf.source_header_entity} identity changed"
            )
        if (x, y, z) != (0, 0, 0):
            raise SurfaceSoylentBuildError(
                f"Field {scene} door leaf has an unaudited nonzero origin"
            )
        active = bytearray(record)
        # 0x0290 is the retail active 3D-model wrapper class.  Leaving the
        # field-621 leaves at their static 0x0010 class would let script 4 be
        # queued but never scheduled, deadlocking the blocking transition.
        struct.pack_into("<H", active, 0, 0x0290)
        promoted.append(bytes(active))

    source_set = set(source_entities)
    retained = [record for index, record in enumerate(records) if index not in source_set]
    retained[first_helper_entity:first_helper_entity] = promoted
    if len(retained) != actor_count:
        raise SurfaceSoylentBuildError(
            f"Field {scene} animated-door header count changed"
        )
    result = bytearray(header[:0x190] + b"".join(retained))
    identity = ANIMATED_INTERACTION_HEADER_IDENTITIES.get(scene)
    if identity is not None and (len(result), _sha256(result)) != identity:
        raise SurfaceSoylentBuildError(
            f"Field {scene} animated-door header identity changed"
        )
    return bytes(result)


def _animated_door_transition_action(
    door: DoorController,
    animation: DoorAnimation,
    routine_pc: int,
) -> bytes:
    """Drain Cross, open the real leaf models together, then change field."""

    if (
        animation.destination_field,
        animation.destination_parameter,
    ) != (
        door.destination_field,
        door.destination_parameter,
    ):
        raise SurfaceSoylentBuildError("Animated door destination changed")
    if not animation.leaves:
        raise SurfaceSoylentBuildError("Animated door has no leaf models")

    if door.action_kind == "discovery_gate":
        success_pc = routine_pc + 8
        success = _animated_door_transition_action(
            replace(door, action_kind="transition"),
            animation,
            success_pc,
        )
        denial_pc = success_pc + len(success)
        denial = _surface_shortcut_denial_action(
            SURFACE_SHORTCUT_DENIAL_DIALOGUE_ID,
            denial_pc,
        )
        return (
            b"\x02"
            + _u16(SURFACE_SHORTCUT_STATE_OPERAND)
            + _u16(SURFACE_SHORTCUT_DISCOVERED_BIT)
            + b"\x46"
            + _u16(denial_pc)
            + success
            + denial
        )

    release_pc = routine_pc + 3
    launches = bytearray()
    for leaf in animation.leaves[:-1]:
        launches.extend(b"\x07" + bytes((leaf.helper_entity, 0x24)))
    last = animation.leaves[-1]
    launches.extend(b"\x09" + bytes((last.helper_entity, 0x24)))
    discovery_write = (
        b"\x3A"
        + _u16(SURFACE_SHORTCUT_STATE_OPERAND)
        + _u16(SURFACE_SHORTCUT_DISCOVERED_BIT_INDEX)
        + b"\x40"
        if door.action_kind == "discovery_unlock"
        else b""
    )
    return (
        b"\x33\xFE\x54"
        + mass_driver._wait_for_pad_release(
            mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + discovery_write
        + b"\x74\x77\x80"
        + bytes(launches)
        + _change_field(door.destination_field, door.destination_parameter)
        + b"\x5B"
    )


def _surface_shortcut_denial_action(
    dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Drain Cross, explain the one-way latch, and restore player input."""

    release_pc = routine_pc + 3
    return (
        b"\x33\xFE\x54"
        + mass_driver._wait_for_pad_release(
            mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + b"\x26\x01\x80"
        + b"\xF5"
        + _u16(dialogue_id)
        + b"\x01\x9C\xFE\x53\x00"
    )


def _existing_helper_door_transition_action(
    door: DoorController,
    helper_entity: int,
    routine_pc: int,
) -> bytes:
    """Wrap one authentic in-place panel helper in a fresh-X transition."""

    release_pc = routine_pc + 3
    return (
        b"\x33\xFE\x54"
        + mass_driver._wait_for_pad_release(
            mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + b"\x74\x77\x80"
        + b"\x09" + bytes((helper_entity, 0x24))
        + _change_field(door.destination_field, door.destination_parameter)
        + b"\x5B"
    )


def _install_native_door_animations(
    editor: ScriptEditor,
    header: bytes,
    *,
    scene: int,
    door_entities: dict[tuple[int, int], tuple[DoorController, int]],
) -> tuple[ScriptEditor, bytes]:
    """Promote only the audited real panels and install finite slide scripts."""

    animations = NATIVE_DOOR_ANIMATIONS.get(scene, ())
    existing_helpers = NATIVE_EXISTING_DOOR_HELPERS.get(scene, ())
    if not animations and not existing_helpers:
        return editor, header
    leaves = tuple(leaf for animation in animations for leaf in animation.leaves)
    if leaves:
        first_helper_entity = editor.entity_count
        header = _promote_native_door_header_records(
            header,
            scene=scene,
            first_helper_entity=first_helper_entity,
            animations=animations,
        )
        editor = ScriptEditor(
            mass_driver._extend_atel_entity_table(
                editor.to_bytes(),
                first_helper_entity + len(leaves),
            )
        )
        stop_pc = editor.append_raw_routine(b"\x00")
        for leaf in leaves:
            for script_index in range(32):
                editor.set_script_pointer(leaf.helper_entity, script_index, stop_pc)
            init_pc = editor.append_raw_routine(b"\xBC\x2A\x00")
            slide_pc = editor.append_raw_routine(
                mass_driver._world_position_static_slide_body(
                    start_x=0,
                    start_z=0,
                    delta_x=leaf.delta_x,
                    delta_z=leaf.delta_z,
                    iterations=next(
                        animation.frames
                        for animation in animations
                        if leaf in animation.leaves
                    ),
                )
            )
            editor.set_script_pointer(leaf.helper_entity, 0, init_pc)
            editor.set_script_pointer(leaf.helper_entity, 4, slide_pc)

    for animation in animations:
        key = (animation.destination_field, animation.destination_parameter)
        if key not in door_entities:
            raise SurfaceSoylentBuildError(
                f"Field {scene} animated door has no matching X controller"
            )
        door, entity = door_entities[key]
        old_action_pc = editor.get_script_pointer(entity, 2)
        expected_old_action = _door_transition_action(door)
        if (
            editor.bytecode[
                old_action_pc : old_action_pc + len(expected_old_action)
            ]
            != expected_old_action
        ):
            raise SurfaceSoylentBuildError(
                f"Field {scene} animated door e{entity} action changed"
            )
        action_pc = editor.bytecode_size
        action = _animated_door_transition_action(door, animation, action_pc)
        if editor.append_and_repoint(entity, 2, action) != action_pc:
            raise SurfaceSoylentBuildError(
                f"Field {scene} animated door action moved"
            )

    for destination_field, destination_parameter, helper, start_pc, end_pc in existing_helpers:
        key = (destination_field, destination_parameter)
        if key not in door_entities:
            raise SurfaceSoylentBuildError(
                f"Field {scene} native helper has no matching X controller"
            )
        helper_body = NATIVE_EXISTING_DOOR_HELPER_BODIES.get((scene, helper))
        if helper_body is None:
            raise SurfaceSoylentBuildError(
                f"Field {scene} native door helper e{helper} lacks an audit body"
            )
        if (
            editor.get_script_pointer(helper, 4) != start_pc
            or editor.bytecode[start_pc:end_pc] != helper_body
        ):
            raise SurfaceSoylentBuildError(
                f"Field {scene} native door helper e{helper} changed"
            )
        door, entity = door_entities[key]
        old_action_pc = editor.get_script_pointer(entity, 2)
        expected_old_action = _door_transition_action(door)
        if (
            editor.bytecode[
                old_action_pc : old_action_pc + len(expected_old_action)
            ]
            != expected_old_action
        ):
            raise SurfaceSoylentBuildError(
                f"Field {scene} native-helper door e{entity} action changed"
            )
        action_pc = editor.bytecode_size
        action = _existing_helper_door_transition_action(
            door,
            helper,
            action_pc,
        )
        if editor.append_and_repoint(entity, 2, action) != action_pc:
            raise SurfaceSoylentBuildError(
                f"Field {scene} native-helper door action moved"
            )
    return editor, header


def _install_quarantine_east_door_animation(
    editor: ScriptEditor,
    header: bytes,
    *,
    door_entities: dict[tuple[int, int], tuple[DoorController, int]],
) -> tuple[ScriptEditor, bytes]:
    """Activate field 620's east leaf and share one animated success exit."""

    animation = QUARANTINE_EAST_DOOR_ANIMATION
    leaf = animation.leaves[0]
    key = (animation.destination_field, animation.destination_parameter)
    if key not in door_entities:
        raise SurfaceSoylentBuildError(
            "Field 620 east panel has no matching X controller"
        )
    door, carrier_entity = door_entities[key]
    if door.action_kind != "quarantine_gate":
        raise SurfaceSoylentBuildError("Field 620 east panel lost its relay gate")
    if editor.entity_count != leaf.helper_entity:
        raise SurfaceSoylentBuildError(
            "Field 620 east helper is not the next ATEL/header actor"
        )

    actor_count = struct.unpack_from("<H", header, 0x18C)[0]
    if (
        len(header) != 0x190 + actor_count * 16
        or leaf.source_header_entity >= actor_count
    ):
        raise SurfaceSoylentBuildError("Field 620 east-panel header is malformed")
    record_offset = 0x190 + leaf.source_header_entity * 16
    record = header[record_offset : record_offset + 16]
    flags, _rx, _ry, _rz, x, y, z, model_index = struct.unpack(
        "<Hhhh hhh H", record
    )
    if (
        flags != leaf.source_flags
        or model_index != leaf.model_index
        or (x, y, z) != (0, 0, 0)
    ):
        raise SurfaceSoylentBuildError("Field 620 east-panel model identity changed")

    gate_pc = editor.get_script_pointer(carrier_entity, 2)
    if (
        gate_pc != QUARANTINE_DOOR_GATE_PC
        or editor.bytecode[gate_pc : gate_pc + len(QUARANTINE_DOOR_GATE_ROUTINE)]
        != QUARANTINE_DOOR_GATE_ROUTINE
    ):
        raise SurfaceSoylentBuildError("Field 620 relay-gate action changed")
    for pc in QUARANTINE_EAST_DOOR_SUCCESS_SITES:
        if (
            editor.bytecode[
                pc : pc + len(QUARANTINE_EAST_DOOR_ORIGINAL_SUCCESS)
            ]
            != QUARANTINE_EAST_DOOR_ORIGINAL_SUCCESS
        ):
            raise SurfaceSoylentBuildError(
                f"Field 620 relay success at 0x{pc:04X} changed"
            )

    # Reuse the checked STOP already shared by the west helper.  The retail
    # east model is already header e26, so ATEL alone grows by one actor.
    west_helper = NATIVE_DOOR_ANIMATIONS[620][0].leaves[0].helper_entity
    stop_pc = editor.get_script_pointer(west_helper, 1)
    if stop_pc >= editor.bytecode_size or editor.bytecode[stop_pc] != 0:
        raise SurfaceSoylentBuildError("Field 620 animated-door STOP changed")
    editor = ScriptEditor(
        mass_driver._extend_atel_entity_table(
            editor.to_bytes(),
            leaf.helper_entity + 1,
        )
    )
    for script_index in range(32):
        editor.set_script_pointer(leaf.helper_entity, script_index, stop_pc)

    init_pc = editor.append_and_repoint(
        leaf.helper_entity,
        0,
        b"\xBC\x2A\x00",
    )
    slide_pc = editor.append_and_repoint(
        leaf.helper_entity,
        4,
        mass_driver._world_position_static_slide_body(
            start_x=0,
            start_z=0,
            delta_x=leaf.delta_x,
            delta_z=leaf.delta_z,
            iterations=animation.frames,
        ),
    )
    if (
        init_pc != QUARANTINE_EAST_DOOR_INIT_PC
        or slide_pc != QUARANTINE_EAST_DOOR_SLIDE_PC
    ):
        raise SurfaceSoylentBuildError(
            "Field 620 east-panel helper routines moved"
        )

    success_pc = editor.bytecode_size
    success = _animated_door_transition_action(
        door,
        animation,
        success_pc,
    )
    if (
        editor.append_raw_routine(success) != QUARANTINE_EAST_DOOR_SUCCESS_PC
    ):
        raise SurfaceSoylentBuildError("Field 620 shared success routine moved")
    script = editor.to_bytes()
    for pc in QUARANTINE_EAST_DOOR_SUCCESS_SITES:
        script = _patch_bytecode(
            script,
            pc,
            QUARANTINE_EAST_DOOR_ORIGINAL_SUCCESS,
            QUARANTINE_EAST_DOOR_SUCCESS_REDIRECT,
        )
    return ScriptEditor(script), header


def prepare_native_interactions(prepared: PreparedField) -> PreparedField:
    """Replace every native walk-through with X and dialogue every person."""

    scene = prepared.spec.identity.scene
    doors = NATIVE_DOOR_CONTROLLERS.get(scene)
    if not doors:
        raise SurfaceSoylentBuildError(f"Field {scene} has no door-controller audit")
    script = prepared.components[SCRIPT_INDEX]
    if (
        len(script) != prepared.spec.patched_script_size
        or _sha256(script) != prepared.spec.patched_script_sha256
    ):
        raise SurfaceSoylentBuildError(
            f"Field {scene} interactive-door baseline changed"
        )
    if tuple(
        (door.destination_field, door.destination_parameter) for door in doors
    ) != tuple(
        (edge.destination_field, edge.destination_parameter)
        for edge in prepared.spec.edges
    ):
        raise SurfaceSoylentBuildError(
            f"Field {scene} door destinations diverged from its route"
        )
    triangles = _walkmesh_layer(prepared.components[1], 0)
    for door in doors:
        if door.triangle >= len(triangles) or not _point_inside_triangle(
            (door.x, door.z), triangles[door.triangle]
        ):
            raise SurfaceSoylentBuildError(
                f"Field {scene} door carrier left triangle {door.triangle}"
            )

    # Enable the exact 17 visible generation-chamber actors without shifting
    # any of their animation PCs.
    if scene == 622:
        if len(GENERATION_NPC_ENABLE_PCS) != len(GENERATION_NPC_DIALOGUES):
            raise SurfaceSoylentBuildError("Generation NPC enable audit changed")
        for pc in GENERATION_NPC_ENABLE_PCS:
            script = _patch_bytecode(script, pc, b"\x2A", b"\x33")

    # Field 620 already owns compact actor-dialogue bodies for e9--e16. Move
    # those references away from the relay text IDs commandeered by the puzzle.
    if scene == 620:
        for pc, old_id, new_id in zip(
            (0x0221, 0x0244, 0x0267, 0x028A, 0x029D, 0x02AF, 0x02C1, 0x02D3),
            range(4, 12),
            range(16, 24),
            strict=True,
        ):
            script = _patch_bytecode(
                script,
                pc,
                b"\xD2" + _u16(old_id) + b"\x00\x9C",
                b"\xD2" + _u16(new_id) + b"\x00\x9C",
            )

    editor = ScriptEditor(script)
    old_count = editor.entity_count
    added_doors = tuple(door for door in doors if door.carrier_entity is None)
    if len({door.carrier_entity for door in doors if door.carrier_entity is not None}) != (
        len(doors) - len(added_doors)
    ):
        raise SurfaceSoylentBuildError(f"Field {scene} reuses a door carrier entity")
    if added_doors:
        header = _insert_added_door_header_records(
            prepared.header,
            scene=scene,
            old_entity_count=old_count,
            doors=added_doors,
        )
        script = mass_driver._extend_atel_entity_table(
            editor.to_bytes(), old_count + len(added_doors)
        )
        editor = ScriptEditor(script)
        stop_pc = editor.append_raw_routine(b"\x00")
    else:
        header = prepared.header
        stop_pc = NATIVE_ROUTE_STOP_PCS[scene]
        if stop_pc >= editor.bytecode_size or editor.bytecode[stop_pc] != 0:
            raise SurfaceSoylentBuildError(
                f"Field {scene} checked route STOP changed"
            )

    if editor.get_script_pointer(prepared.spec.director_entity, 1) != prepared.spec.poll_pc:
        raise SurfaceSoylentBuildError(f"Field {scene} active edge poll changed")
    editor.set_script_pointer(prepared.spec.director_entity, 1, stop_pc)

    next_added_entity = old_count
    door_entities: dict[tuple[int, int], tuple[DoorController, int]] = {}
    for door in doors:
        if door.carrier_entity is None:
            entity = next_added_entity
            next_added_entity += 1
            for script_index in range(32):
                editor.set_script_pointer(entity, script_index, stop_pc)
        else:
            entity = door.carrier_entity
            collision_pc = editor.get_script_pointer(entity, 3)
            if collision_pc >= editor.bytecode_size or editor.bytecode[collision_pc] != 0:
                raise SurfaceSoylentBuildError(
                    f"Field {scene} e{entity} door collision slot is not STOP"
                )
        init_pc = editor.append_and_repoint(
            entity,
            0,
            _door_controller_init(door),
        )
        if door.action_kind not in (
            "transition",
            "quarantine_gate",
            "discovery_gate",
            "discovery_unlock",
        ):
            raise SurfaceSoylentBuildError(
                f"Field {scene} has unsupported door action {door.action_kind!r}"
            )
        action = (
            QUARANTINE_DOOR_GATE_ROUTINE
            if door.action_kind == "quarantine_gate"
            else _door_transition_action(door)
        )
        action_pc = editor.append_and_repoint(entity, 2, action)
        if door.action_kind == "quarantine_gate" and action_pc != QUARANTINE_DOOR_GATE_PC:
            raise SurfaceSoylentBuildError(
                f"Quarantine door gate moved to 0x{action_pc:04X}"
            )
        if init_pc >= action_pc:
            raise SurfaceSoylentBuildError(f"Field {scene} door routine order changed")
        key = (door.destination_field, door.destination_parameter)
        if key in door_entities:
            raise SurfaceSoylentBuildError(
                f"Field {scene} repeats a door destination {key!r}"
            )
        door_entities[key] = (door, entity)

    npc_dialogues = NATIVE_NPC_DIALOGUES.get(scene, ())
    dialogue = prepared.components[7]
    if scene == 623:
        parsed_dialogue = parse_dialogue(dialogue)
        if len(parsed_dialogue.blocks) != SURFACE_SHORTCUT_DENIAL_DIALOGUE_ID:
            raise SurfaceSoylentBuildError(
                "Field 623 shortcut dialogue ID changed"
            )
        dialogue = _append_dialogue_blocks(
            dialogue,
            (SURFACE_SHORTCUT_DENIAL_DIALOGUE,),
            width=58,
            height=3,
        )
        dialogue_identity = SURFACE_SHORTCUT_DIALOGUE_IDENTITIES.get(scene)
        if dialogue_identity is not None and (
            len(dialogue),
            _sha256(dialogue),
        ) != dialogue_identity:
            raise SurfaceSoylentBuildError(
                "Field 623 shortcut dialogue identity changed"
            )
    if npc_dialogues:
        parsed_dialogue = parse_dialogue(dialogue)
        first_new_id = len(parsed_dialogue.blocks)
        expected_first = {621: 2, 620: 12, 622: 22}[scene]
        if first_new_id != expected_first:
            raise SurfaceSoylentBuildError(
                f"Field {scene} dialogue count changed before NPC append"
            )
        dialogue = _append_dialogue_blocks(
            dialogue,
            tuple(text for _entity, text in npc_dialogues),
            width=_native_npc_dialogue_width(scene),
            height=4,
        )
        if (len(dialogue), _sha256(dialogue)) != NATIVE_NPC_DIALOGUE_IDENTITIES[scene]:
            raise SurfaceSoylentBuildError(
                f"Field {scene} final NPC dialogue identity changed"
            )
        for index, (entity, _text) in enumerate(npc_dialogues):
            dialogue_id = first_new_id + index
            if scene == 620 and entity >= 9:
                if editor.get_script_pointer(entity, 2) not in (
                    0x0221, 0x0244, 0x0267, 0x028A,
                    0x029D, 0x02AF, 0x02C1, 0x02D3,
                ):
                    raise SurfaceSoylentBuildError(
                        f"Quarantine NPC e{entity} action pointer changed"
                    )
                continue
            old_action = editor.get_script_pointer(entity, 2)
            if old_action >= editor.bytecode_size or editor.bytecode[old_action] != 0:
                raise SurfaceSoylentBuildError(
                    f"Field {scene} NPC e{entity} action was not silent"
                )
            editor.append_and_repoint(
                entity,
                2,
                _actor_dialogue_action(dialogue_id),
            )

    editor, header = _install_native_door_animations(
        editor,
        header,
        scene=scene,
        door_entities=door_entities,
    )
    if scene == 620:
        editor, header = _install_quarantine_east_door_animation(
            editor,
            header,
            door_entities=door_entities,
        )

    script = editor.to_bytes()
    components = list(prepared.components)
    components[SCRIPT_INDEX] = script
    changed = [SCRIPT_INDEX]
    if dialogue != components[7]:
        components[7] = dialogue
        changed.append(7)
    bundle = build_field_preserving(
        prepared.bundle,
        components,
        tuple(changed),
        compact_changed=True,
        replacement_header=header,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise SurfaceSoylentBuildError(
            f"Field {scene} interactive output failed round trip"
        )
    packed_header_identity = PACKED_INTERACTION_HEADER_IDENTITIES.get(scene)
    if packed_header_identity is not None and (
        len(reparsed.header),
        _sha256(reparsed.header),
    ) != packed_header_identity:
        raise SurfaceSoylentBuildError(
            f"Field {scene} packed interactive header changed"
        )
    identity = COMPLETE_INTERACTION_FINAL_IDENTITIES.get(scene)
    if identity is not None:
        script_size, script_sha, bundle_size, bundle_sha = identity
        if (len(script), _sha256(script), len(bundle), _sha256(bundle)) != identity:
            raise SurfaceSoylentBuildError(
                f"Field {scene} final interaction identity changed"
            )
    else:
        script_size, script_sha = len(script), _sha256(script)
        bundle_size, bundle_sha = len(bundle), _sha256(bundle)
    final_spec = replace(
        prepared.spec,
        role=(
            prepared.spec.role
            + "; X-gated reciprocal doors"
            + (
                "; authentic panel animation"
                if (
                    scene in NATIVE_DOOR_ANIMATIONS
                    or scene in NATIVE_EXISTING_DOOR_HELPERS
                )
                else ""
            )
        ),
        poll_pc=stop_pc,
        patched_script_size=script_size,
        patched_script_sha256=script_sha,
        patched_bundle_size=bundle_size,
        patched_bundle_sha256=bundle_sha,
    )
    return PreparedField(
        final_spec,
        prepared.source_bundle,
        prepared.graphics,
        reparsed.header,
        tuple(components),
        bundle,
    )


SEALED_ROUTE_RESPONSE_PC = 0x05DC
SEALED_ROUTE_RESPONSE = bytes.fromhex(
    "33 FE 54 31 20 00 EA 05 26 01 80 01 DF 05 26 01 80 "
    "F5 0A 00 01 9C FE 53 00"
)
SEALED_ROUTE_ENTITIES = (9,)
DONOR_ROUTE_IMMOVABLE_CONTROLLER_INITS = {
    # scene: ((controller, audited native init start, terminal STOP), ...)
    # These are the only field-changing door controllers in the three donor
    # annexes.  Their script-two actions already run the authentic model-leaf
    # helpers and therefore must remain at their retail PCs.
    549: ((6, 0x019E, 0x01B3),),
    550: ((17, 0x0628, 0x063D),),
    589: ((4, 0x00CB, 0x00E0),),
}
DONOR_ROUTE_NATIVE_MOTION = {
    # scene: controller, action PC, leaf helper, helper script-four PC/body,
    # transition PC, reciprocal destination field/parameter
    549: (6, 0x01B4, 7, 0x01CC, bytes.fromhex("05 EE 06 00"), 0x01BF, 621, 2),
    550: (17, 0x063E, 18, 0x0656, bytes.fromhex("05 C2 00 00"), 0x0649, 621, 3),
    589: (4, 0x00E1, 5, 0x00F9, bytes.fromhex("05 67 09 00"), 0x00EC, 565, 4),
}
FIELD565_RECIPROCAL_DOORS = (
    # entity, authentic model helper, player walk script, field-621 parameter
    (4, 19, 4, 1),
    (6, 17, 6, 4),
    (7, 18, 7, 5),
)
FIELD565_IMMOVABLE_CONTROLLER_INITS = (
    # entity, audited native init start, its terminal STOP
    (4, 0x0251, 0x0266),
    (5, 0x027A, 0x028F),
    (6, 0x02A3, 0x02B8),
    (7, 0x02CC, 0x02E1),
    (8, 0x02F5, 0x030A),
    (9, 0x031E, 0x0333),
    (10, 0x0347, 0x035C),
    (11, 0x0370, 0x0384),
    (12, 0x0397, 0x03AB),
)
FIELD565_QUARANTINE_EXIT_ENTITY = 5
FIELD565_QUARANTINE_EXIT_GATE_PC = 0x064C
FIELD565_QUARANTINE_DENIAL_PC = 0x0671
FIELD565_INTERNAL_GATE_NATIVE_ACTION_PC = 0x0385
FIELD565_INTERNAL_GATE_ACTION_PC = 0x068A
FIELD565_TONE_GATE_ACTION_PC = 0x03AC
FIELD565_TONE_GATE_REOPEN_EXIT_PC = 0x03C1
FIELD565_TONE_GATE_SUCCESS_EXIT_PC = 0x0465
FIELD565_TONE_GATE_REOPEN_GHOST_PC = 0x069E
FIELD565_TONE_GATE_SUCCESS_GHOST_PC = 0x06A4


def _field565_reciprocal_action(
    helper_entity: int,
    player_script: int,
    destination_parameter: int,
    routine_pc: int,
) -> bytes:
    """Drain Cross, run the native 565 door/player motion, and return to 621."""

    release_pc = routine_pc + 3
    return (
        b"\x33\xFE\x54"
        + mass_driver._wait_for_pad_release(
            mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + b"\x09" + bytes((helper_entity, 0x24))
        + b"\x07\x01" + bytes((0x20 | player_script,))
        + b"\x26\x0A\x80"
        + _change_field(621, destination_parameter)
        + b"\x5B"
    )


def _field565_quarantine_exit_action(routine_pc: int) -> bytes:
    """Keep the 565->624 production route behind field 620's solved bit."""

    unlocked_pc = routine_pc + 8
    return (
        b"\x02" + _u16(QUARANTINE_STATE_OPERAND)
        + _u16(QUARANTINE_COMPLETE_BIT)
        + b"\x46" + _u16(FIELD565_QUARANTINE_DENIAL_PC)
        + _field565_native_door_action(
            helper_entity=16,
            player_script=5,
            destination_field=624,
            destination_parameter=0,
            routine_pc=unlocked_pc,
        )
    )


def _field565_native_door_action(
    *,
    helper_entity: int,
    player_script: int,
    destination_field: int,
    destination_parameter: int,
    routine_pc: int,
) -> bytes:
    """Wrap one native 565 model/player door sequence in fresh-Cross input."""

    release_pc = routine_pc + 3
    return (
        b"\x33\xFE\x54"
        + mass_driver._wait_for_pad_release(
            mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + b"\x09" + bytes((helper_entity, 0x24))
        + b"\x07\x01" + bytes((0x20 | player_script,))
        + b"\x26\x0A\x80"
        + _change_field(destination_field, destination_parameter)
        + b"\x5B"
    )


def _field565_repeatable_dialogue_action(
    block_id: int,
    routine_pc: int,
) -> bytes:
    """Drain Cross, show one field-565 status block, and restore control."""

    release_pc = routine_pc + 3
    return (
        b"\x33\xFE\x54"
        + mass_driver._wait_for_pad_release(
            mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + b"\x26\x01\x80"
        + b"\xF5" + _u16(block_id) + b"\x01\x9C\xFE\x53\x00"
    )


def _field565_internal_gate_action() -> bytes:
    """Preserve e11's native opening, then ghost its immovable carrier."""

    return bytes.fromhex(
        "FE 54 36 00 04 09 14 24 80 98 00 00 80 "
        "20 01 80 2A FE 53 00"
    )


def _field565_gate_ghost_trampoline(return_pc: int) -> bytes:
    """Ghost the current gate actor, then rejoin its native success path."""

    return b"\x20\x01\x80\x01" + _u16(return_pc)


def _install_field565_internal_gate_safety(editor: ScriptEditor) -> ScriptEditor:
    """Make e11/e12 solid while closed and passable only after native success."""

    native_e11 = bytes.fromhex(
        "FE 54 36 00 04 09 14 24 80 98 00 00 80 2A FE 53 00"
    )
    if (
        editor.get_script_pointer(11, 2)
        != FIELD565_INTERNAL_GATE_NATIVE_ACTION_PC
        or editor.bytecode[
            FIELD565_INTERNAL_GATE_NATIVE_ACTION_PC :
            FIELD565_INTERNAL_GATE_NATIVE_ACTION_PC + len(native_e11)
        ]
        != native_e11
    ):
        raise SurfaceSoylentBuildError("Field 565 internal gate action changed")

    # Both e12 jumps are success-only exits.  The first follows the stored-open
    # helper21 animation; the second follows a newly accepted five-tone input,
    # its helper21 animation, state writes, DISABLE_DIALOG_ACTIVATION and wait.
    script = editor.to_bytes()
    script = _patch_bytecode(
        script,
        FIELD565_TONE_GATE_REOPEN_EXIT_PC,
        b"\x01" + _u16(0x053C),
        b"\x01" + _u16(FIELD565_TONE_GATE_REOPEN_GHOST_PC),
    )
    script = _patch_bytecode(
        script,
        FIELD565_TONE_GATE_SUCCESS_EXIT_PC,
        b"\x01" + _u16(0x051D),
        b"\x01" + _u16(FIELD565_TONE_GATE_SUCCESS_GHOST_PC),
    )
    editor = ScriptEditor(script)
    if editor.get_script_pointer(12, 2) != FIELD565_TONE_GATE_ACTION_PC:
        raise SurfaceSoylentBuildError("Field 565 five-tone action moved")
    if editor.bytecode[0x03B6:0x03BE] != bytes.fromhex(
        "09 15 24 80 99 00 00 80"
    ):
        raise SurfaceSoylentBuildError("Field 565 stored-open success path changed")
    if editor.bytecode[0x0447:0x044F] != bytes.fromhex(
        "09 15 24 80 99 00 00 80"
    ):
        raise SurfaceSoylentBuildError("Field 565 five-tone success path changed")

    if editor.bytecode_size != FIELD565_INTERNAL_GATE_ACTION_PC:
        raise SurfaceSoylentBuildError("Field 565 internal gate append point moved")
    if editor.append_and_repoint(
        11,
        2,
        _field565_internal_gate_action(),
    ) != FIELD565_INTERNAL_GATE_ACTION_PC:
        raise SurfaceSoylentBuildError("Field 565 internal gate action append failed")
    if editor.append_raw_routine(
        _field565_gate_ghost_trampoline(0x053C)
    ) != FIELD565_TONE_GATE_REOPEN_GHOST_PC:
        raise SurfaceSoylentBuildError("Field 565 stored-open ghost moved")
    if editor.append_raw_routine(
        _field565_gate_ghost_trampoline(0x051D)
    ) != FIELD565_TONE_GATE_SUCCESS_GHOST_PC:
        raise SurfaceSoylentBuildError("Field 565 five-tone success ghost moved")
    return editor


def _make_field565_controllers_immovable(editor: ScriptEditor) -> ScriptEditor:
    """Retain native X volumes but prevent their hidden carriers being shoved."""

    for entity, start_pc, stop_pc in FIELD565_IMMOVABLE_CONTROLLER_INITS:
        if (
            editor.get_script_pointer(entity, 0) != start_pc
            or editor.bytecode[stop_pc] != 0
        ):
            raise SurfaceSoylentBuildError(
                f"Field 565 controller e{entity} init changed"
            )
        native_body = editor.bytecode[start_pc:stop_pc]
        if b"\xF8\x00\x10\x00" in native_body:
            raise SurfaceSoylentBuildError(
                f"Field 565 controller e{entity} is already immovable"
            )
        editor.append_and_repoint(
            entity,
            0,
            native_body + b"\xF8\x00\x10\x00\x00",
        )
    return editor


def _prepare_immovable_donor_route(
    prepared: PreparedDonorField,
) -> PreparedDonorField:
    """Make one annex return-door carrier solid without replacing its motion."""

    scene = prepared.identity.scene
    contracts = DONOR_ROUTE_IMMOVABLE_CONTROLLER_INITS[scene]
    baseline = DONOR_FINAL_IDENTITIES[scene]
    script = prepared.components[SCRIPT_INDEX]
    if (
        len(script),
        _sha256(script),
        len(prepared.bundle),
        _sha256(prepared.bundle),
    ) != baseline:
        raise SurfaceSoylentBuildError(
            f"Field {scene} reciprocal-door baseline changed"
        )

    editor = ScriptEditor(script)
    native_bytecode = editor.bytecode
    native_pointers = tuple(
        tuple(
            editor.get_script_pointer(entity, script_index)
            for script_index in range(32)
        )
        for entity in range(editor.entity_count)
    )
    appended_pcs: dict[int, int] = {}
    for entity, start_pc, stop_pc in contracts:
        if (
            editor.get_script_pointer(entity, 0) != start_pc
            or editor.get_script_pointer(entity, 2) != stop_pc + 1
            or stop_pc >= len(native_bytecode)
            or native_bytecode[stop_pc] != 0
        ):
            raise SurfaceSoylentBuildError(
                f"Field {scene} reciprocal door e{entity} init/action moved"
            )
        native_body = native_bytecode[start_pc:stop_pc]
        if b"\xF8\x00\x10\x00" in native_body:
            raise SurfaceSoylentBuildError(
                f"Field {scene} reciprocal door e{entity} is already immovable"
            )
        appended_pc = editor.bytecode_size
        if editor.append_and_repoint(
            entity,
            0,
            native_body + b"\xF8\x00\x10\x00\x00",
        ) != appended_pc:
            raise SurfaceSoylentBuildError(
                f"Field {scene} reciprocal door e{entity} hardened init moved"
            )
        appended_pcs[entity] = appended_pc

    # Prove that hardening only appended routines and changed their init slots.
    if editor.bytecode[: len(native_bytecode)] != native_bytecode:
        raise SurfaceSoylentBuildError(
            f"Field {scene} native door bytecode changed during hardening"
        )
    for entity in range(editor.entity_count):
        for script_index in range(32):
            expected = native_pointers[entity][script_index]
            if script_index == 0 and entity in appended_pcs:
                expected = appended_pcs[entity]
            if editor.get_script_pointer(entity, script_index) != expected:
                raise SurfaceSoylentBuildError(
                    f"Field {scene} e{entity}:s{script_index} changed during "
                    "door hardening"
                )

    (
        controller,
        action_pc,
        helper,
        helper_pc,
        helper_body,
        transition_pc,
        destination_field,
        destination_parameter,
    ) = DONOR_ROUTE_NATIVE_MOTION[scene]
    expected_action = (
        bytes.fromhex("FE 54")
        + bytes((0x09, helper, 0x24))
        + bytes.fromhex("07 01 24 26 0A 80")
        + _change_field(destination_field, destination_parameter)
        + b"\x5B"
    )
    if (
        editor.get_script_pointer(controller, 2) != action_pc
        or editor.bytecode[action_pc : action_pc + len(expected_action)]
        != expected_action
        or editor.get_script_pointer(helper, 4) != helper_pc
        or editor.bytecode[helper_pc : helper_pc + len(helper_body)] != helper_body
        or editor.bytecode[transition_pc : transition_pc + 5]
        != _change_field(destination_field, destination_parameter)
    ):
        raise SurfaceSoylentBuildError(
            f"Field {scene} native reciprocal-door motion changed"
        )

    script = editor.to_bytes()
    components = list(prepared.components)
    components[SCRIPT_INDEX] = script
    bundle = build_field_preserving(
        prepared.bundle,
        components,
        (SCRIPT_INDEX,),
        compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise SurfaceSoylentBuildError(
            f"Field {scene} hardened donor output failed round trip"
        )
    if (
        len(reparsed.header),
        _sha256(reparsed.header),
    ) != INTERACTIVE_DONOR_HEADER_IDENTITIES[scene]:
        raise SurfaceSoylentBuildError(
            f"Field {scene} hardened donor header changed"
        )
    actual = (len(script), _sha256(script), len(bundle), _sha256(bundle))
    if actual != INTERACTIVE_DONOR_FINAL_IDENTITIES[scene]:
        raise SurfaceSoylentBuildError(
            f"Field {scene} hardened donor identity changed"
        )
    return PreparedDonorField(
        prepared.identity,
        (
            prepared.role
            + "; reciprocal return-door carrier immovable"
            + "; native action and model-leaf animation preserved"
        ),
        prepared.source_bundle,
        prepared.graphics,
        reparsed.header,
        tuple(components),
        bundle,
        prepared.entry_triangles,
    )


def prepare_donor_interactions(prepared: PreparedDonorField) -> PreparedDonorField:
    """Harden reciprocal doors and open 565's formerly sealed intake routes."""

    if prepared.identity.scene in DONOR_ROUTE_IMMOVABLE_CONTROLLER_INITS:
        return _prepare_immovable_donor_route(prepared)
    if prepared.identity.scene != 565:
        return prepared
    baseline = DONOR_FINAL_IDENTITIES[565]
    script = prepared.components[SCRIPT_INDEX]
    if (len(script), _sha256(script), len(prepared.bundle), _sha256(prepared.bundle)) != baseline:
        raise SurfaceSoylentBuildError("Field 565 sealed-door baseline changed")
    editor = ScriptEditor(script)
    expected_stops = {4: 0x0266, 6: 0x02B8, 7: 0x02E1, 9: 0x0333}
    for entity, stop_pc in expected_stops.items():
        if editor.get_script_pointer(entity, 2) != stop_pc or editor.bytecode[stop_pc] != 0:
            raise SurfaceSoylentBuildError(
                f"Field 565 sealed door e{entity} no longer points to STOP"
            )
    if editor.append_raw_routine(SEALED_ROUTE_RESPONSE) != SEALED_ROUTE_RESPONSE_PC:
        raise SurfaceSoylentBuildError("Field 565 sealed-door response moved")
    for entity in SEALED_ROUTE_ENTITIES:
        editor.set_script_pointer(entity, 2, SEALED_ROUTE_RESPONSE_PC)
    for entity, helper, player_script, destination_parameter in FIELD565_RECIPROCAL_DOORS:
        action_pc = editor.bytecode_size
        action = _field565_reciprocal_action(
            helper,
            player_script,
            destination_parameter,
            action_pc,
        )
        if editor.append_and_repoint(entity, 2, action) != action_pc:
            raise SurfaceSoylentBuildError(
                f"Field 565 reciprocal door e{entity} action moved"
            )
    native_exit_pc = editor.get_script_pointer(FIELD565_QUARANTINE_EXIT_ENTITY, 2)
    native_exit = bytes.fromhex(
        "FE 54 09 10 24 07 01 25 26 0A 80 98 70 82 00 80 5B"
    )
    if (
        native_exit_pc != 0x0290
        or editor.bytecode[native_exit_pc:native_exit_pc + len(native_exit)]
        != native_exit
    ):
        raise SurfaceSoylentBuildError("Field 565 production exit action changed")
    gate_pc = editor.bytecode_size
    if gate_pc != FIELD565_QUARANTINE_EXIT_GATE_PC:
        raise SurfaceSoylentBuildError("Field 565 production-exit gate moved")
    gate = _field565_quarantine_exit_action(gate_pc)
    if editor.append_and_repoint(FIELD565_QUARANTINE_EXIT_ENTITY, 2, gate) != gate_pc:
        raise SurfaceSoylentBuildError("Field 565 production-exit gate repoint failed")
    denial_pc = editor.bytecode_size
    if denial_pc != FIELD565_QUARANTINE_DENIAL_PC:
        raise SurfaceSoylentBuildError("Field 565 production-exit denial moved")
    if editor.append_raw_routine(
        _field565_repeatable_dialogue_action(11, denial_pc)
    ) != denial_pc:
        raise SurfaceSoylentBuildError("Field 565 production-exit denial append failed")
    editor = _install_field565_internal_gate_safety(editor)
    editor = _make_field565_controllers_immovable(editor)
    dialogue = _append_dialogue_blocks(
        prepared.components[7],
        (
            "AUXILIARY ROUTE SEALED\n"
            "No authorization signal is present.<Close>",
            "QUARANTINE CONSENSUS REQUIRED\n"
            "Outbound sorting is still locked.<Close>",
        ),
        width=58,
        height=3,
    )
    script = editor.to_bytes()
    components = list(prepared.components)
    components[SCRIPT_INDEX] = script
    components[7] = dialogue
    bundle = build_field_preserving(
        prepared.bundle,
        components,
        (SCRIPT_INDEX, 7),
        compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise SurfaceSoylentBuildError("Field 565 sealed-door output failed round trip")
    header_identity = INTERACTIVE_DONOR_HEADER_IDENTITIES.get(565)
    if header_identity is not None and (
        len(reparsed.header),
        _sha256(reparsed.header),
    ) != header_identity:
        raise SurfaceSoylentBuildError("Field 565 packed header changed")
    identity = INTERACTIVE_DONOR_FINAL_IDENTITIES.get(565)
    actual = (
        len(script),
        _sha256(script),
        len(dialogue),
        _sha256(dialogue),
        len(bundle),
        _sha256(bundle),
    )
    if identity is not None and actual != identity:
        raise SurfaceSoylentBuildError("Field 565 sealed-door identity changed")
    return PreparedDonorField(
        prepared.identity,
        (
            prepared.role
            + "; three reciprocal intake doors; production exit requires relay consensus"
            + "; absent-resource wing sealed; native door carriers immovable"
        ),
        prepared.source_bundle,
        prepared.graphics,
        reparsed.header,
        tuple(components),
        bundle,
        prepared.entry_triangles,
    )


def _patch_donor_party(
    script: bytes,
    pcs: Sequence[int],
    source_operands: Sequence[int] | None = None,
) -> bytes:
    if source_operands is None:
        source_operands = tuple(0x8000 | index for index in range(len(pcs)))
    if len(source_operands) != len(pcs):
        raise SurfaceSoylentBuildError("Donor party source-operand count changed")
    for index, (pc, source_operand) in enumerate(zip(pcs, source_operands, strict=True)):
        source = b"\x16" + _u16(source_operand) + b"\xFE\x0D" + _u16(source_operand)
        selector = PARTY_SELECTORS[index]
        playable = b"\x16" + _immediate(selector) + b"\xFE\x0D" + _immediate(selector)
        script = _patch_bytecode(script, pc, source, playable)
    return script


def prepare_donor_field(
    identity: SourceIdentity,
    source_bundle: bytes,
    graphics: bytes,
) -> PreparedDonorField:
    if identity.scene not in DONOR_BY_SCENE:
        raise SurfaceSoylentBuildError(f"Unsupported Surface donor field {identity.scene}")
    if len(source_bundle) != identity.bundle_size or _sha256(source_bundle) != identity.bundle_sha256:
        raise SurfaceSoylentBuildError(f"Donor field {identity.scene} bundle changed")
    if len(graphics) != identity.graphics_size or _sha256(graphics) != identity.graphics_sha256:
        raise SurfaceSoylentBuildError(f"Donor field {identity.scene} graphics changed")
    parsed = parse_field(source_bundle)
    components = [part.data for part in parsed.parts]
    script = components[SCRIPT_INDEX]

    if identity.scene == 549:
        role = "binary records and scanner-code archive"
        script = _patch_bytecode(
            script, 0x0001,
            bytes.fromhex("38 FF C8 00 00 FF FF"),
            bytes.fromhex("38 FF C8 00 00 03 03"),
        )
        script = _patch_donor_party(
            script,
            (0x007F, 0x00B0, 0x00BB),
            (0x003E, 0x0040, 0x0042),
        )
        script = _patch_bytecode(script, 0x000F, bytes.fromhex("17 00"), bytes.fromhex("11 00"))
        script = _patch_bytecode(script, 0x001D, bytes.fromhex("25 00"), bytes.fromhex("1F 00"))
        script = _patch_bytecode(
            script, 0x01BF,
            _change_field(551, 2),
            _change_field(621, 2),
        )
        entries = ((0, 6),)
    elif identity.scene == 550:
        role = "four-bit diagnostic scanner"
        script = _patch_bytecode(
            script, 0x0001,
            bytes.fromhex("AB FF 1A FF 00 FF FF"),
            bytes.fromhex("AB FF 1A FF 00 07 07"),
        )
        script = _patch_donor_party(
            script,
            (0x01CE, 0x01F3, 0x01FE),
            (0x003E, 0x0040, 0x0042),
        )
        script = _patch_bytecode(script, 0x015E, bytes.fromhex("66 01"), bytes.fromhex("60 01"))
        script = _patch_bytecode(script, 0x016C, bytes.fromhex("74 01"), bytes.fromhex("6E 01"))
        script = _patch_bytecode(
            script, 0x0649,
            _change_field(551, 1),
            _change_field(621, 3),
        )
        entries = ((0, 14),)
    elif identity.scene == 565:
        role = "five-tone lock and service-wing hub"
        for pc, before, after in (
            (0x0001, "E8 FF 18 00 00 FF FF", "E8 FF 18 00 00 07 03"),
            (0x0008, "00 13 D6 F1 00 FF FF", "00 13 D6 F1 00 05 05"),
            (0x000F, "90 10 48 F4 00 FF FF", "90 10 48 F4 00 01 05"),
            (0x0016, "1F 0E AF F6 00 FF FF", "1F 0E AF F6 00 01 05"),
            (0x001D, "49 04 55 EE 00 FF FF", "49 04 55 EE 00 01 01"),
            (0x002B, "02 0D 73 E9 00 FF FF", "02 0D 73 E9 00 07 07"),
        ):
            script = _patch_bytecode(script, pc, bytes.fromhex(before), bytes.fromhex(after))
        script = _patch_donor_party(script, (0x01B4, 0x0218, 0x0223))
        script = _patch_bytecode(script, 0x029B, _change_field(584, 0), _change_field(624, 0))
        script = _patch_bytecode(script, 0x0368, _change_field(587, 0), _change_field(620, 1))
        for offset, before, after in (
            (0x0188, "67 02", "66 02"),
            (0x0208, "B9 02", "B8 02"),
            (0x0248, "E2 02", "E1 02"),
            (0x02C8, "34 03", "33 03"),
        ):
            script = _patch_raw(script, offset, bytes.fromhex(before), bytes.fromhex(after))
        entries = ((0, 75), (1, 8), (2, 12), (3, 17), (4, 57), (6, 68))
    else:
        role = "native five-tone audio-clue annex"
        script = _patch_bytecode(
            script, 0x0001,
            bytes.fromhex("54 01 78 00 00 FF FF"),
            bytes.fromhex("54 01 78 00 00 05 05"),
        )
        script = _patch_donor_party(script, (0x0050, 0x0085, 0x0090))
        script = _patch_bytecode(script, 0x0019, bytes.fromhex("21 00"), bytes.fromhex("1B 00"))
        entries = ((0, 57),)

    expected_script_size, expected_script_sha, expected_bundle_size, expected_bundle_sha = (
        DONOR_FINAL_IDENTITIES[identity.scene]
    )
    if len(script) != expected_script_size or _sha256(script) != expected_script_sha:
        raise SurfaceSoylentBuildError(
            f"Donor field {identity.scene} script changed: {len(script)} bytes, "
            f"SHA-256 {_sha256(script)}"
        )
    components[SCRIPT_INDEX] = script
    bundle = build_field_preserving(
        source_bundle,
        components,
        (SCRIPT_INDEX,),
        compact_changed=True,
    )
    if len(bundle) != expected_bundle_size or _sha256(bundle) != expected_bundle_sha:
        raise SurfaceSoylentBuildError(
            f"Donor field {identity.scene} bundle changed: {len(bundle)} bytes, "
            f"SHA-256 {_sha256(bundle)}"
        )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise SurfaceSoylentBuildError(f"Donor field {identity.scene} failed round trip")

    editor = ScriptEditor(script)
    layers: dict[int, tuple[tuple[tuple[int, int, int], ...], ...]] = {}
    for parameter, triangle in entries:
        x, z, walkmesh, _camera, _actor = struct.unpack_from(
            "<hhBBB", editor.bytecode, 1 + 7 * parameter
        )
        triangles = layers.setdefault(walkmesh, _walkmesh_layer(components[1], walkmesh))
        if triangle >= len(triangles) or not _point_inside_triangle((x, z), triangles[triangle]):
            raise SurfaceSoylentBuildError(
                f"Donor field {identity.scene} entry {parameter} left triangle {triangle}"
            )
    return PreparedDonorField(
        identity,
        role,
        source_bundle,
        graphics,
        reparsed.header,
        tuple(components),
        bundle,
        entries,
    )


def prepare_donors(donor_disc: Path | str) -> tuple[PreparedDonorField, ...]:
    sources = load_donor_fields(donor_disc)
    return tuple(
        prepare_donor_field(identity, *sources[identity.scene])
        for identity in DONOR_FIELDS
    )


def prepare_all(source_disc: Path | str) -> tuple[PreparedField, ...]:
    sources = load_source_fields(source_disc)
    prepared = tuple(
        prepare_playable_field(spec, *sources[spec.identity.scene])
        for spec in PLAYABLE_SCENES
    )
    entries = {
        (item.spec.identity.scene, edit.parameter): edit.playable
        for item in prepared
        for edit in item.spec.entry_edits
    }
    for item in prepared:
        for edge in item.spec.edges:
            destination = entries.get((edge.destination_field, edge.destination_parameter))
            if destination is None:
                raise SurfaceSoylentBuildError(
                    f"Route {item.spec.identity.scene}->{edge.destination_field}/"
                    f"{edge.destination_parameter} has no audited destination entry"
                )
    return prepared


def prepare_complete_route(
    source_disc: Path | str,
    donor_disc: Path | str,
) -> tuple[tuple[PreparedField, ...], tuple[PreparedDonorField, ...]]:
    verify_donor_targets_are_dummy(source_disc)
    sources = load_source_fields(source_disc)
    base_specs = {spec.identity.scene: spec for spec in PLAYABLE_SCENES}
    approach = prepare_playable_field(COMPLETE_APPROACH_SCENE, *sources[623])
    intake = prepare_intake_side_wings(
        prepare_playable_field(base_specs[621], *sources[621])
    )
    quarantine = prepare_quarantine_puzzle(
        prepare_playable_field(base_specs[620], *sources[620])
    )
    native_wings = tuple(
        prepare_playable_field(spec, *sources[spec.identity.scene])
        for spec in NATIVE_WING_SCENES
    )
    generation = prepare_playable_field(
        FINAL_GENERATION_SCENE,
        *sources[622],
    )
    prepared = tuple(
        prepare_native_interactions(item)
        for item in (approach, intake, quarantine, *native_wings, generation)
    )
    donors = tuple(
        prepare_donor_interactions(item)
        for item in prepare_donors(donor_disc)
    )

    destinations = {
        (item.spec.identity.scene, edit.parameter)
        for item in prepared
        for edit in item.spec.entry_edits
    }
    destinations.update(
        (item.identity.scene, parameter)
        for item in donors
        for parameter, _triangle in item.entry_triangles
    )
    for item in prepared:
        for edge in item.spec.edges:
            destination = (edge.destination_field, edge.destination_parameter)
            if destination not in destinations:
                raise SurfaceSoylentBuildError(
                    f"Complete route {item.spec.identity.scene}->{destination} "
                    "has no audited entry"
                )
    donor_routes = (
        (549, 621, 2),
        (550, 621, 3),
        (565, 621, 1),
        (565, 621, 4),
        (565, 621, 5),
        (565, 620, 1),
        (565, 589, 0),
        (565, 624, 0),
        (589, 565, 4),
    )
    for source_scene, destination_field, destination_parameter in donor_routes:
        if (destination_field, destination_parameter) not in destinations:
            raise SurfaceSoylentBuildError(
                f"Donor route {source_scene}->{destination_field}/"
                f"{destination_parameter} has no audited entry"
            )
    return prepared, donors


def _ensure_output(path: Path, force: bool) -> None:
    if path.exists() and not path.is_dir():
        raise SurfaceSoylentBuildError(f"Output is not a directory: {path}")
    if path.is_dir() and any(path.iterdir()) and not force:
        raise SurfaceSoylentBuildError(f"Output is not empty: {path}; pass --force")


def materialize(
    prepared: Sequence[PreparedField],
    output_root: Path | str,
    source_disc: Path | str,
    *,
    donor_fields: Sequence[PreparedDonorField] = (),
    donor_disc: Path | str | None = None,
    title_resources: Sequence[PreparedTitleResource] = (),
    complete_dungeon: bool = False,
    force: bool = False,
) -> tuple[tuple[int, Path], ...]:
    output = Path(output_root).resolve()
    _ensure_output(output, force)
    clones = output / "clones"
    replacements = output / "replacements"
    clones.mkdir(parents=True, exist_ok=True)
    replacements.mkdir(parents=True, exist_ok=True)

    emitted: list[tuple[int, Path]] = []
    jobs: list[dict[str, object]] = []
    for item in prepared:
        scene = item.spec.identity.scene
        source_parts = parse_field(item.source_bundle).parts
        changed_indices = [
            index
            for index, (before, after) in enumerate(
                zip(source_parts, item.components, strict=True)
            )
            if before.data != after
        ]
        clone = clones / f"field_{scene}"
        clone.mkdir(parents=True, exist_ok=True)
        (clone / "header.bin").write_bytes(item.header)
        for index, (name, component) in enumerate(zip(STREAM_NAMES, item.components, strict=True)):
            (clone / f"{index:02d}_{name}.bin").write_bytes(component)
        (clone / "graphics.bin").write_bytes(item.graphics)

        replacement = replacements / f"{item.spec.identity.bundle_id}_field_{scene}_playable.bin"
        replacement.write_bytes(item.bundle)
        emitted.append((item.spec.identity.bundle_id, replacement))
        jobs.append(
            {
                "scene": scene,
                "role": item.spec.role,
                "canonical_bundle_id": item.spec.identity.bundle_id,
                "canonical_graphics_id": item.spec.identity.graphics_id,
                "replacement": str(replacement.relative_to(output).as_posix()),
                "replacement_size": len(item.bundle),
                "replacement_sha256": _sha256(item.bundle),
                "graphics_preserved_sha256": _sha256(item.graphics),
                "changed_streams": changed_indices,
                "header_actor_records_added": (
                    len(
                        tuple(
                            door
                            for door in NATIVE_DOOR_CONTROLLERS.get(scene, ())
                            if door.carrier_entity is None
                        )
                    )
                    if complete_dungeon
                    else 0
                ),
                "party_selectors": list(PARTY_SELECTORS),
                "entries": [
                    {
                        "parameter": edit.parameter,
                        "position": [edit.playable.x, edit.playable.z],
                        "walkmesh": edit.playable.walkmesh,
                        "camera_direction": edit.playable.camera_direction,
                        "actor_direction": edit.playable.actor_direction,
                        "triangle": edit.triangle,
                    }
                    for edit in item.spec.entry_edits
                ],
                "edges": [
                    {
                        **asdict(edge),
                        "direction": edge.direction,
                    }
                    for edge in item.spec.edges
                ],
                "door_interactions": (
                    [
                        {
                            "position": [door.x, door.z],
                            "interaction_half_width": door.interaction_half_width,
                            "interaction_half_depth": door.interaction_half_depth,
                            "destination": [
                                door.destination_field,
                                door.destination_parameter,
                            ],
                            "triangle": door.triangle,
                            "input": "Cross",
                        }
                        for door in NATIVE_DOOR_CONTROLLERS[scene]
                    ]
                    if complete_dungeon
                    else []
                ),
            }
        )

    if donor_fields and donor_disc is None:
        raise SurfaceSoylentBuildError("Materializing donor fields requires donor_disc")
    donor_jobs: list[dict[str, object]] = []
    for item in donor_fields:
        scene = item.identity.scene
        source_parts = parse_field(item.source_bundle).parts
        changed_indices = [
            index
            for index, (before, after) in enumerate(
                zip(source_parts, item.components, strict=True)
            )
            if before.data != after
        ]
        clone = clones / f"field_{scene}_disc1_donor"
        clone.mkdir(parents=True, exist_ok=True)
        (clone / "header.bin").write_bytes(item.header)
        for index, (name, component) in enumerate(zip(STREAM_NAMES, item.components, strict=True)):
            (clone / f"{index:02d}_{name}.bin").write_bytes(component)
        (clone / "graphics.bin").write_bytes(item.graphics)

        bundle_path = replacements / f"{item.identity.bundle_id}_field_{scene}_donor.bin"
        graphics_path = replacements / f"{item.identity.graphics_id}_field_{scene}_graphics.bin"
        bundle_path.write_bytes(item.bundle)
        graphics_path.write_bytes(item.graphics)
        emitted.extend(
            (
                (item.identity.bundle_id, bundle_path),
                (item.identity.graphics_id, graphics_path),
            )
        )
        donor_jobs.append(
            {
                "scene": scene,
                "role": item.role,
                "source_disc": Path(donor_disc).resolve().name if donor_disc else None,
                "target_bundle_id": item.identity.bundle_id,
                "target_graphics_id": item.identity.graphics_id,
                "bundle_replacement": str(bundle_path.relative_to(output).as_posix()),
                "bundle_size": len(item.bundle),
                "bundle_sha256": _sha256(item.bundle),
                "graphics_replacement": str(graphics_path.relative_to(output).as_posix()),
                "graphics_size": len(item.graphics),
                "graphics_sha256": _sha256(item.graphics),
                "changed_streams": changed_indices,
                "entry_triangles": [list(value) for value in item.entry_triangles],
            }
        )

    title_jobs: list[dict[str, object]] = []
    for resource in title_resources:
        replacement = replacements / resource.filename
        replacement.write_bytes(resource.data)
        emitted.append((resource.canonical_id, replacement))
        title_jobs.append(
            {
                "canonical_id": resource.canonical_id,
                "name": resource.name,
                "replacement": str(replacement.relative_to(output).as_posix()),
                "source_sha256": resource.source_sha256,
                "replacement_size": len(resource.data),
                "replacement_sha256": _sha256(resource.data),
            }
        )

    canonical_ids = [canonical_id for canonical_id, _path in emitted]
    if len(canonical_ids) != len(set(canonical_ids)):
        raise SurfaceSoylentBuildError("Replacement list contains a duplicate canonical ID")

    manifest = {
        "format": OUTPUT_FORMAT,
        "name": "Surface Soylent System playable vertical slice",
        "source_disc": Path(source_disc).resolve().name,
        "source_fields": [asdict(identity) for identity in SOURCE_FIELDS],
        "playable_route": (
            [623, 621, 620, 565, 624, 626, 625, 622]
            if complete_dungeon
            else [623, 621, 620, 622]
        ),
        "optional_wings": [549, 550, 589] if complete_dungeon else [],
        "discovered_shortcuts": (
            [
                {
                    "name": "Generation emergency service latch",
                    "discovery_side": [622, 623, 0],
                    "gated_reverse_side": [623, 622, 1],
                    "persistent_operand": SURFACE_SHORTCUT_STATE_OPERAND,
                    "persistent_bit_mask": SURFACE_SHORTCUT_DISCOVERED_BIT,
                    "persistent_bit_index": SURFACE_SHORTCUT_DISCOVERED_BIT_INDEX,
                    "cold_surface_entry_denied": True,
                    "input": "Cross",
                    "authentic_panel_animation": True,
                }
            ]
            if complete_dungeon
            else []
        ),
        "future_native_wings": [] if complete_dungeon else [624, 626, 625],
        "preservation": {
            "changed_streams": (
                ["scripts", "dialogue"] if complete_dungeon else ["scripts"]
            ),
            "unchanged_streams": [
                name
                for index, name in enumerate(STREAM_NAMES)
                if index not in (
                    (SCRIPT_INDEX, 7) if complete_dungeon else (SCRIPT_INDEX,)
                )
            ],
            "graphics": "byte-identical",
            "source_header": (
                "retail static actor records preserved byte-for-byte; "
                "model-less scripted door records inserted where required"
                if complete_dungeon
                else "frozen and emitted separately"
            ),
            "container_header": (
                "deterministically resized/repacked for scripted door actors "
                "and longer streams"
                if complete_dungeon
                else "deterministically repacked for the longer script stream"
            ),
        },
        "jobs": jobs,
        "donor_jobs": donor_jobs,
        "puzzles": (
            [
                {
                    "field": 620,
                    "name": "Biological relay classification",
                    "solution": "Genome, Limiter, Nanomachines on; Caste Index off",
                    "persistent_operand": QUARANTINE_STATE_OPERAND,
                },
                {
                    "field": 550,
                    "name": "Four-bit diagnostic scanner",
                    "implementation": "preserved native controller",
                },
                {
                    "fields": [589, 565],
                    "name": "Five-tone audio lock",
                    "implementation": "preserved native clue and lock controllers",
                },
            ]
            if complete_dungeon
            else []
        ),
        "title_menu": (
            {
                "enabled_rows": ["Mass-Driver", "Surface Soylent System"],
                "disabled_rows": ["Mahanon"],
                "initial_row": "Mass-Driver",
                "surface_entry": [SURFACE_ENTRY_FIELD, SURFACE_ENTRY_PARAMETER],
                "mass_driver_entry": [MASS_DRIVER_ENTRY_FIELD, 0],
                "route_tag_operand": TITLE_ROUTE_TAG_OPERAND,
                "route_tag_runtime_address": TITLE_ROUTE_TAG_RUNTIME_ADDRESS,
                "initial_gamestate_2595": "verified and unchanged",
                "resources": title_jobs,
            }
            if title_jobs
            else {"status": "not integrated in this stage"}
        ),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return tuple(emitted)


def build_surface_soylent(
    source_disc: Path | str,
    output_root: Path | str,
    *,
    donor_disc: Path | str | None = None,
    complete_dungeon: bool = False,
    enable_title_menu: bool = False,
    force: bool = False,
) -> tuple[tuple[PreparedField, ...], tuple[tuple[int, Path], ...]]:
    if complete_dungeon:
        if donor_disc is None:
            raise SurfaceSoylentBuildError("Complete dungeon requires a Disc 1 donor disc")
        prepared, donor_fields = prepare_complete_route(source_disc, donor_disc)
    else:
        if donor_disc is not None:
            raise SurfaceSoylentBuildError("Donor disc requires complete-dungeon mode")
        prepared = prepare_all(source_disc)
        donor_fields = ()
    title_resources = (
        prepare_title_integration(
            source_disc,
            complete_dungeon=complete_dungeon,
        )
        if enable_title_menu
        else ()
    )
    replacements = materialize(
        prepared,
        output_root,
        source_disc,
        donor_fields=donor_fields,
        donor_disc=donor_disc,
        title_resources=title_resources,
        complete_dungeon=complete_dungeon,
        force=force,
    )
    return prepared, replacements


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-disc", type=Path, required=True)
    parser.add_argument(
        "--donor-disc",
        type=Path,
        help="Perfect Works Disc 1 source for whole-room Solaris/Krelian donors",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--enable-title-menu",
        action="store_true",
        help=(
            "enable Surface Soylent as the second title choice; the source "
            "disc must be the checked Mass-Driver release"
        ),
    )
    parser.add_argument(
        "--complete-dungeon",
        action="store_true",
        help="build the full native route, relay puzzle, and four donor wings",
    )
    parser.add_argument("--build-disc", action="store_true")
    parser.add_argument("--xenoiso", type=Path)
    parser.add_argument("--disc-output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.build_disc and not all((args.xenoiso, args.disc_output)):
        parser.error("--build-disc requires --xenoiso and --disc-output")
    if not args.build_disc and any((args.xenoiso, args.disc_output)):
        parser.error("--xenoiso and --disc-output require --build-disc")
    if args.build_disc and not args.enable_title_menu:
        parser.error("--build-disc requires --enable-title-menu so the route is reachable")
    if args.complete_dungeon and args.donor_disc is None:
        parser.error("--complete-dungeon requires --donor-disc")
    if args.donor_disc is not None and not args.complete_dungeon:
        parser.error("--donor-disc requires --complete-dungeon")
    try:
        prepared, replacements = build_surface_soylent(
            args.source_disc,
            args.output,
            donor_disc=args.donor_disc,
            complete_dungeon=args.complete_dungeon,
            enable_title_menu=args.enable_title_menu,
            force=args.force,
        )
        print(
            "Prepared player-controlled Surface Soylent fields: "
            + ", ".join(str(item.spec.identity.scene) for item in prepared)
        )
        for canonical_id, path in replacements:
            print(f"  canonical {canonical_id}: {path}")
        if args.enable_title_menu:
            print("Enabled title choices: Mass-Driver and Surface Soylent System")
        if args.complete_dungeon:
            print("Installed donor fields: 549, 550, 565, 589")
            print("Installed native Surface wings: 624, 626, 625")
        print(f"Wrote {Path(args.output).resolve() / 'manifest.json'}")
        if args.build_disc:
            command = xenoiso_wrapper_command(
                args.xenoiso,
                args.source_disc,
                args.disc_output,
                replacements,
                force=args.force,
            )
            completed = subprocess.run(command, check=False)
            if completed.returncode:
                raise SurfaceSoylentBuildError(
                    f"Xenoiso wrapper exited with code {completed.returncode}"
                )
            boot = verify_retail_title_boot(args.disc_output)
            print(
                f"Verified native publisher/title boot at raw LBA {boot.lba}: "
                f"{boot.sha256}"
            )
        return 0
    except (
        DialogueFormatError,
        FieldFormatError,
        OSError,
        ScriptFormatError,
        SurfaceSoylentBuildError,
    ) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
