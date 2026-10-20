#!/usr/bin/env python3
"""Build the complete, cohesive Disc 2 Surface Soylent campaign.

This is intentionally a layer over :mod:`build_surface_soylent_dungeon`.
The v173 builder owns the difficult retail conversion work: playable party
entities, reciprocal spatial doors, real panel animation, donor-room safety,
and the two-choice title menu.  This module keeps that frozen foundation and
authors the missing campaign around it:

* all eighteen rooms form one reciprocal, X-button door graph;
* four unused Disc 2 field slots become bright, bed-equipped Intake clinical
  rooms with Solaris terminals, including a treatment-preparation room;
* Disc 1 field 550 supplies an independent, bright Soylent diagnostic
  laboratory reached from the restored Service Manifold threshold;
* Disc 1 field 352 also supplies an empty, bed-equipped examination annex;
* Disc 1 field 567's compact stabilization ward is recovered into unused
  logical field 590 as the clinical bridge into the production dungeon;
* four independent clearances protect the production floor;
* the sorting, M-Project, Meld, and Sufal rooms form an ordered back half;
* survivor dialogue stays inside Xenogears' Disc 2 continuity; and
* every room selects the native Krelian Lab corridor cue heard in retail
  fields 565 and 567 without restarting it on ordinary same-track field
  transitions;
* a Surface-only title bootstrap installs Fei, Elly, and Citan.

Most rooms retain their graphics, models, walkmeshes, encounters, and native
door helpers byte-for-byte.  Logical field 550 deliberately transplants the
Disc 1 field-352 Ethos infirmary room, replaces two retired local banks with
exact overworld Solaris Guard and Security Cube assets, disables its retail
random encounters, and reserves disabled configuration 15 for the matching
scripted fight.  Field 621 replaces only actor/sprite bank 6 with the office
physician's exact bank.  New interaction carriers are inserted at the current
ATEL boundary so every retained static model remains in order.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import modules.soylent_system.base as base  # noqa: E402
import modules.soylent_system.tools.surface_soylent_campaign_blueprint as blueprint  # noqa: E402
import modules.soylent_system.tools.surface_soylent_campaign_donor567 as donor567  # noqa: E402
import modules.soylent_system.tools.surface_soylent_campaign_empty_clinic567 as empty_clinic567  # noqa: E402
import modules.soylent_system.tools.surface_soylent_campaign_exam_rooms as exam_rooms  # noqa: E402
import modules.soylent_system.tools.surface_soylent_campaign_donor588 as donor588  # noqa: E402
import modules.soylent_system.tools.surface_soylent_campaign_stabilization590 as stabilization590  # noqa: E402
import modules.soylent_system.tools.surface_soylent_campaign_title as campaign_title  # noqa: E402
import shared.tools.xgdeathblows as deathblows  # noqa: E402
from modules.mass_driver.tools.build_mass_driver_graybox import (  # noqa: E402
    GrayboxBuildError,
    xenoiso_wrapper_command,
)
from shared.tools import atel_primitives as atel
from shared.tools.xgdialog import (  # noqa: E402
    CHARACTER_IDS,
    PLAIN_ENCODE,
    DialogueBlock,
    DialogueBlockSpec,
    encode_dialogue,
    parse_dialogue,
)
from shared.tools.xgdisc import (  # noqa: E402
    Mode2Image,
    directory_file_fat_index,
)
from shared.tools.xgfield import STREAM_NAMES, build_field_preserving, parse_field  # noqa: E402
from shared.tools.xgencounter import EncounterTable  # noqa: E402
from shared.tools.xgmode2 import verify_retail_title_boot  # noqa: E402
from shared.tools.xgscript import AtelScript as ScriptEditor  # noqa: E402


OUTPUT_FORMAT = "xenogears-surface-soylent-campaign-v1"
SCRIPT_INDEX = base.SCRIPT_INDEX
STATE_OPERAND = blueprint.STATE_OPERAND
LOCAL_PUZZLE_OPERAND = 0x07D0

DEATHBLOW_LEVEL_RESOURCE_CANONICAL_ID = 2607
DEATHBLOW_LEVEL_RESOURCE_SIZE = 31_436
DEATHBLOW_LEVEL_RESOURCE_SHA256 = (
    "aa9319a251700da9e25af71567628109f86268fb8a310af5abb2b5bf52adf03f"
)
DEATHBLOW_LEVEL_ARCHIVE_OFFSETS = (0x18, 0x674, 0x1050, 0x4800)
DEATHBLOW_LEVEL_FILE0_SIZE = 3_797
DEATHBLOW_LEVEL_FILE0_SHA256 = (
    "dbe291fb89501f708688bb4974436db0535bd2e6bfb539310102ad03709ca384"
)
DEATHBLOW_LEVEL_TABLE_OFFSETS = (
    0x0100,
    0x0210,
    0x0320,
    0x0430,
    0x0540,
    0x0650,
    0x0760,
    0x0A90,
    0x0BA0,
)

INTERFACE_BIT_INDEX = 11
INTERFACE_BIT_MASK = 0x0800
FINALE_EPILOGUE_PENDING_BIT_INDEX = 10
FINALE_EPILOGUE_PENDING_BIT_MASK = 0x0400
SORTER_BIT_INDEX = 12
SORTER_BIT_MASK = 0x1000
CORE_BIT_INDEX = 13
CORE_BIT_MASK = 0x2000
MELD_BIT_INDEX = 14
MELD_BIT_MASK = 0x4000
SECURED_BIT_INDEX = 15
SECURED_BIT_MASK = 0x8000

CHECKIN_BIT_INDEX = 7
CHECKIN_BIT_MASK = 0x0080

# V183 recorded only that check-in completed.  V184 keeps the selected alias
# and a modulo-0x4000 play-time snapshot in a separate persistent field word,
# then uses the newly isolated bits 4..6 of the campaign word for the clinic
# sequence.  The play-time modulus is four hours, thirty-three minutes, and
# four seconds: comfortably beyond the one-minute appointment while retaining
# exact wrap behavior at 0x3FFF -> 0.
APPOINTMENT_OPERAND = 0x03EE
APPOINTMENT_TIME_MASK = 0x3FFF
APPOINTMENT_ALIAS_MASK = 0xC000
APPOINTMENT_ALIAS_CODES = (0x4000, 0x8000, 0xC000)
APPOINTMENT_PHASE_MASK = 0x0070
APPOINTMENT_PHASE_NONE = 0x0000
APPOINTMENT_PHASE_REGISTERED = 0x0010
APPOINTMENT_PHASE_ARMED = 0x0020
APPOINTMENT_PHASE_CALLED = 0x0030
APPOINTMENT_PHASE_ENTERED = 0x0040
APPOINTMENT_PHASE_LEGACY_BRIEFED = 0x0050
APPOINTMENT_PHASE_OFFICE_ACTIVE = 0x0060
APPOINTMENT_PHASE_RESOLVED = 0x0070
# V184/V185 called phase 0x50 ``BRIEFED``. Keep the name as a compatibility
# alias, but V186 never writes it: an old state is migrated into the staged
# office sequence the next time field 550 updates.
APPOINTMENT_PHASE_BRIEFED = APPOINTMENT_PHASE_LEGACY_BRIEFED
APPOINTMENT_DELAY_SECONDS = 60

# Once the timer has fired, APPOINTMENT_OPERAND's low fourteen timestamp bits
# are no longer needed.  V186 reuses them as a save-safe office substage while
# preserving the selected alias in the high two bits.
APPOINTMENT_STAGE_MASK = APPOINTMENT_TIME_MASK
APPOINTMENT_STAGE_NONE = 0
APPOINTMENT_STAGE_AWAIT_REFUSAL = 1
APPOINTMENT_STAGE_FINAL_WARNING = 2
APPOINTMENT_STAGE_SECURITY_PENDING = 3
APPOINTMENT_STAGE_FLEE_PENDING = 4
APPOINTMENT_STAGE_COMPLETE = 5
APPOINTMENT_STAGE_SECURITY_ENTERING = 6
APPOINTMENT_STAGE_BATTLE_PENDING = 7

# Scratch words are field-local and intentionally clear on every field load.
# The persistent words above survive fields and savestates.
APPOINTMENT_PACKED_CLOCK_VARIABLE = 0x07C0
APPOINTMENT_MINUTE_VARIABLE = 0x07C2
APPOINTMENT_NOW_VARIABLE = 0x07C4
APPOINTMENT_SCRATCH_VARIABLE = 0x07C6
APPOINTMENT_DOCTOR_BUSY_VARIABLE = 0x07C8
CLINIC_DOOR_OPEN_VARIABLE = 0x07CA
# The same scratch address safely tracks field 621's independent lobby leaf:
# field-local variables reset on transition, and the clinic uses it only after
# field 550 has loaded.
INTAKE_DOCTOR_DOOR_OPEN_VARIABLE = CLINIC_DOOR_OPEN_VARIABLE
INTAKE_DIALOG_BUSY_VARIABLE = 0x07CC
CLINIC_SECURITY_DONE_VARIABLE = 0x07CE
# Entity scripts execute in eight-opcode slices.  The clinic exit action must
# retain its phase snapshot across frames while the lower-ID doctor update runs;
# sharing 0x07C6 let that update replace the phase with an appointment substage
# before the exit action resumed.  Field 550 can safely reuse field 620's local
# puzzle word because field-local storage is reset on every transition.
CLINIC_EXIT_SCRATCH_VARIABLE = LOCAL_PUZZLE_OPERAND

# Field 620's retail-derived relay menu formerly stored its four-bit selection
# in STATE_OPERAND bits 4..7.  Those bits now own the appointment phase and the
# established check-in flag, so only these audited operand sites move to the
# field-local puzzle word.  Completion/intro flags at other STATE_OPERAND sites
# remain persistent and are deliberately not touched.
QUARANTINE_RELAY_SELECTION_OPERAND_PCS = (
    0x0586,
    0x05D6,
    0x05DE,
    0x05F2,
    0x0625,
    0x0675,
    0x067D,
    0x0691,
    0x06C4,
    0x0714,
    0x071C,
    0x0730,
    0x0763,
    0x07B3,
    0x07BB,
    0x07CF,
    0x082B,
    0x08E0,
)

# Disc 1 field 565 is the Krelian Lab T-corridor leading to its musical lock;
# its entity-zero initializer selects music ID 0x3D.  Field 567, the lab's Wels
# surgery room, independently selects the same cue.  Field 551, the adjacent
# Etrenank Soylent entrance, is a third natural source.  This is deliberately
# distinct from ID 0x3C: Kislev Gear Dock fields 251/252/259 use 0x3C for the
# infiltration cue the user recognized as Nortune music, and Krelian Lab
# entrance thresholds 555 and 560 also use it.
# The requested cue is the one the player already heard in this campaign's
# native field-565 lab asset area.
#
# The retail loader maps ID 0x3D to wave/sequence files 0x8D/0x8E in directory
# 0x1C.  Both files are byte-identical on the checked Disc 1 and Disc 2 images.
KRELIAN_LAB_MUSIC_ID = 0x3D
KRELIAN_LAB_MUSIC_OPCODE = b"\x75\x3D\x80"
KRELIAN_LAB_MUSIC_TRACK = "Native Krelian Lab corridor cue (ID 0x3D)"
NORTUNE_STEALTH_MUSIC_ID = 0x3C
NORTUNE_STEALTH_MUSIC_OPCODE = b"\x75\x3C\x80"
MUSIC_DIRECTORY = 0x1C
KRELIAN_LAB_WAVE_LOCAL_FILE = 0x8D
KRELIAN_LAB_SEQUENCE_LOCAL_FILE = 0x8E
KRELIAN_LAB_MUSIC_ASSET_IDENTITIES = {
    KRELIAN_LAB_WAVE_LOCAL_FILE: (
        352_256,
        "16f0e17050f03ce616b0b1fabf75ab8f33b66608075c2f54f476b93610be9aca",
    ),
    KRELIAN_LAB_SEQUENCE_LOCAL_FILE: (
        2_352,
        "da95422b394acd3d46ee35f2c66b78abec46ee8616e070670c22e2f58de19b7b",
    ),
}

# (canonical bundle ID, bundle size, bundle SHA, script size, script SHA,
#  entity-zero initializer PC, PLAY_MUSIC PC).  These three natural Disc 1
# fields independently select the requested field-565 lab-area cue.
KRELIAN_LAB_MUSIC_SOURCE_EVIDENCE = {
    551: (
        1713,
        73_244,
        "b43a4deef95f64278374403fc6a877b9b8e9c12cd61fb2a0e6d382825d293f88",
        7_236,
        "acb0f1fa556af98d7c305890505f056562b0f2e947f6061b68ea75d55602fcc3",
        0x0032,
        0x0033,
    ),
    565: (
        1741,
        80_904,
        "9eab95f706083ee1d1a16743b4da0d6df1948da48e47172aa30b0c98c5b78d7f",
        3_040,
        "ff1bb34dabf93964a6278a1b8505767eda2e4e581848dcaee634306f29eebfe1",
        0x0181,
        0x0182,
    ),
    567: (
        1745,
        84_648,
        "c9648040ebd58d16218f2a1c75651cf2c34bda83fd8b9aa68b93115e3848b75d",
        4_496,
        "887a46dcf43b749ae1fd4698193a4a2ae2aab12a6f88927cc287feeabba26975",
        0x0016,
        0x0017,
    ),
}

# Negative provenance matters here: these two Krelian Lab entrance fields are
# the exact retail sources for the nearby but wrong ID 0x3C cue.  Freezing them
# prevents a future name-based audit from silently reintroducing Nortune music.
NORTUNE_STEALTH_MUSIC_SOURCE_EVIDENCE = {
    555: (
        1721,
        64_512,
        "c7825b74211a446bba5b48e0fda1ed64e06280f2acc4cd0fb995312af8dff051",
        2_576,
        "6cacfd339ae83ed787dce0b37bc5861a74e570cee4acb102dfdb07f4b26babe4",
        0x001D,
        0x001E,
    ),
    560: (
        1731,
        49_260,
        "08df7829028ebb550e194ca109e17641e3581fcf0090474fae9d5ee209f9fdff",
        2_744,
        "1f199c55f7d0dd717f6290e783ba9d04342ca12877a78e72d210632f3cc8ab41",
        0x0181,
        0x0182,
    ),
}

# Exact post-door/pre-music campaign scripts.  Keeping this table separate
# from the final output table prevents a future room transform from silently
# acquiring a second music selector or moving the initializer trampoline.
CAMPAIGN_PRE_MUSIC_SCRIPT_IDENTITIES = {
    623: (6836, "221ca7af4894988d925a9c67645c77eafe6feca8a35d898da538e45150dee123"),
    621: (10888, "964518df192c8ed5c8dd787f03a5e87a285155de8c73980ee9f4a5e36f07def0"),
    620: (6098, "043f0751e1baad44bad5de5c87df17343943a63b8ca9539a6ef5be0b6f746de4"),
    624: (12811, "cea86cc62eec58b87aec3be5804f17734429d51d7483a6f5529bd7698e573124"),
    626: (9299, "ae7fa7e36f4f4c60b7839f95b8af3859b07764ccaa312b1573d83a705ac5c64a"),
    625: (5581, "40a5199d1ab9b94e9b1049ddd5d3d3f82b97494765d20a0804ec251ceea8e267"),
    622: (7393, "f40bf392e532d1a9f16d068b19646b742eb298496b61870860db8594458cbe0c"),
    549: (3834, "6e1668fd3799f5212f759b837201caf811d1021c8cd747e7e61f0dd4514ae3e2"),
    550: (5407, "56e7c014b3dec31b9aca7acd8270cf569e6b6a8eeb9dbd707ad3af72ffa1564c"),
    565: (4931, "6856522f442c67b5d752ca9c099cc367d3501c7f40a3137a1efad721a5f11510"),
    567: (3274, "c2722a52e662418b20c4c373ba7994ceb550ccfeafc78bee9e7428874acb560a"),
    589: (4223, "0bcee861d4b19f1fdbfb2981534b31e99ace293b4e26ffc8fd3ce35947389284"),
    588: (4834, "9b95ec3e882125ff5b969db2405480d3e16428ed1b7a56b96098b9486f67c280"),
    590: (5755, "5cb97eb7e523a1fe7df006608a5cc68b41ddeb6c48ddbb974a7df65bb0307733"),
    591: (3698, "65fa3f0e14c7f3ce94cafb730988b3f59e1cfc75501dd3927af2c0c3d4f36c94"),
    592: (3698, "5a9a916e4ed16bb6fa29a9ad26f7304da96f74d6ce05cee498027d27f3f736e8"),
    593: (3508, "149a8c1e791776672e7fc0936a758eae026119fcc173a9615a78f05e90f54e79"),
    594: (3696, "e1e58b1d7785e494fc8cc2687416a023ecbfe62bf60781b4c3c415df31058057"),
}
CAMPAIGN_MUSIC_SOURCE_ENTRY_PCS = {
    623: 0x000F,
    621: 0x1838,
    620: 0x001D,
    624: 0x147B,
    626: 0x0F87,
    625: 0x0B62,
    622: 0x1121,
    549: 0x0008,
    550: 0x000F,
    565: 0x0181,
    567: empty_clinic567.GLOBAL_INIT_PC,
    591: empty_clinic567.GLOBAL_INIT_PC,
    592: empty_clinic567.GLOBAL_INIT_PC,
    593: empty_clinic567.GLOBAL_INIT_PC,
    594: empty_clinic567.GLOBAL_INIT_PC,
    589: 0x0008,
    588: 0x0157,
    590: 0x0016,
}
CAMPAIGN_MUSIC_WRAPPER_PCS = {
    623: 0x0EF0,
    621: 0x1DC4,
    620: 0x100E,
    624: 0x1d07,
    626: 0x13cf,
    625: 0x0C49,
    622: 0x145D,
    549: 0x0A36,
    550: 0x0E9B,
    567: 0x0746,
    591: 0x8ae,
    592: 0x8ae,
    593: 0x07F0,
    594: 0x8ac,
    589: 0x0A7B,
    588: 0x0ADE,
}
FIELD565_MUSIC_PC = 0x0182
FIELD565_SOURCE_MUSIC_OPCODE = b"\x75\x3D\x80"

# Frozen against the checked v173 foundation, Perfect Works Disc 1 donor,
# and the campaign transforms in this module.  Each tuple is
# (script size, script SHA, dialogue size, dialogue SHA, bundle size, bundle SHA).
CAMPAIGN_FINAL_IDENTITIES = {
    623: (6843, "9a0055bcc391e4b8aebf1f9ca14e0d15c8ad594cad9de98d4ad9f12c3d393887", 156, "79b95ed7bad65192e467ebf64d4ebdfbb0a33f3f05fb32fc286633dad06860b4", 31764, "3b5dcff71ef98543659f525d1ded5f2f3ec31ad3bb608460db10639aaaf86cb4"),
    621: (10895, "a7c52258a56f10a1bea9e8ee7cdc9c7730b78bd1c21f524a12a108302a2172f2", 2135, "2affc3b9e7ad27ae0e9be2b4e8f0d1362f3b37ef7218001aa995994cf6e5bb40", 135644, "168fb1fb14a0c4745725396aae8d5831d931cd30d0d1c67eb6e8d654708eb2bd"),
    620: (6105, "b99b6f6849cff6cf14d81abb61ba944819712660aad07eab5f3ac4852f107f8b", 3808, "1c86667be5c43d49860648799bf7e441efb9296abea97fc8188ea4e67e2a0b55", 148072, "0a80e3a2513628c4ba23f34ae432c01f8efaf06e19379a52001a98c2ea354154"),
    624: (12818, "a64492212e145df9406d9aeef9156716efdbca2fd9ac692e4660c944a6ff24d0", 3153, "9064a291a0e7d7fa21d76dafff6100995348fc1b3f2d21877599212febaff533", 64252, "a3a950faabaabf32652763336f2dc74a2fd12b2f580ca124fa10abf1f4494e15"),
    626: (9306, "67a89bc2a26a141f7f190ea97b0ef92f10be9869100d1e5bf4b864a3f7f414e6", 2174, "377cdd42bcea3e0865ec5c2956fcf96b6b00b6368d8b1a03a427711194028947", 36600, "6e0a39356936cd03ab4ece534fc82c14d1d180c7c1960190ebaa6f65cf6331c8"),
    625: (5588, "ca2cec5764b46e2bf448251ad2858fbde5cb68c77bc24a4365b4329a0e12446d", 911, "c90b81ba96cfe9bbef1245686b8dfa0cb9b1535e9a03a9d8c2f1387fd85d4485", 45520, "b65826f1d5abbd4d1d384387f1e50be280b982e33580d0a62149e273fe5f32ca"),
    622: (7400, "9b45623a0a752fb9f049b2f72f5ddbe2799ff1ee4d2ca6fcd253c2e40736cadd", 6710, "d4eacc5dbe19d6d92384cf9b9b7ac1469c486b7e7b09bb3e3ac0268edf56f321", 105988, "d722af696903c31bf350724509ffeede253b6493bfcf45a4e172a829a087072c"),
    549: (3841, "2dd2804d33004a52b66e676adb3ba9d978532ad21c80ca6da4d84f9ba1e3c999", 2125, "57ed56cde500d327df72112d7d47823b0e66ba25c969b90ce5d9c259a5c7401b", 23332, "8bdb39fab5c1e7dbd201c0f0d53368c3a754d36bf698fa717558202852bdeefe"),
    550: (5414, "83329cf20bf5bd16e217e7fb445d399ccb2301b612e54c4910a3f19ec91d9a85", 6056, "3c1f8cc6906384c6a9a0bb23ee5710bde6a524f656baa4b6ac8c49659d51bc4e", 78024, "b75339d2fdefc2291f2e130329adddafc29a3ca42941c5a24487b3ea6ab9a698"),
    565: (4931, "6856522f442c67b5d752ca9c099cc367d3501c7f40a3137a1efad721a5f11510", 1644, "a6e0cb57e23a1cdfb7fc7b385413ac7eb19bca341db7daaa4f9fcfbfd998fe3b", 82348, "c2fe1a96b4eb418e5f80b3ad527d348d3e0d8503a0cebb1ad896c212cbe234fa"),
    567: (3281, "24eb53d1aaa10678f2815cf5fe89e80455c592319d6d69712932f4941793790d", 5232, "2f15ffdeda92ec407a983737cd0acf550856725718b4fb6a05df046e47f2d8fd", 83548, "6f4be9fa9932c77094b2ff09875ee5a035e145662efd83ba50b1b879d5c36999"),
    591: (3705, "a9108d113e14bdba69f502144122417ba08b291e780158ea7eba50f94230557d", 6551, "12602410a7cfe27892d0f74b90b63c6241c4cc3b8ebaa7d72e8599321a076749", 64376, "c9a23a429fc405e3791fd4ace01634ffd9ee7cca347dd20466e19f8c8d54668b"),
    592: (3705, "49efd7d6fd50f0b44b9e6b614c4fdc2d3cf73fadaf7392f7d93db4d515c52387", 6431, "6bb8f64b93cdb48049a17ee90676ec4fbcd27724b407b37868baf300cc540980", 64860, "766d3db1dc8bc0c7ab74dd95e12cf59f42018395d88c94418a461a9884e224e3"),
    593: (3515, "69f6730f9526c3ea6eabdabf5cc260cdeaeb0393e31bf1dd84a650158ae8784a", 5766, "92d7f6d9ab86a53e8cabd300bc7bb84d8bbb04142f9aa9c4f91a9bd5578b828e", 69664, "67081150a2f7b4e5451249150a8b1188e9b2fdd3fdaa5b5e70fb44459c0b5ce0"),
    594: (3703, "cbcfd5d2929995f05016e1d85edb9f42e7e24a0214f4edffd59c8ec4af538a82", 6379, "838fea0a05a0273acfdeacf6f8b329c6d3967e8473c4f73d8e3f5fa87b5abdcc", 72776, "5a2f177fc12c3a670a047b25465365d02f10978738e4f472c9a9ff27a925bbf2"),
    589: (4230, "2fbca096ecea72b2d6da89b0fa2b51782af81f6f55d86eea8eddd74b8a7fdb49", 287, "2e76fdbe61c54c93518cd872c70baace8a5eeeb434e077edd1b42defe8e200e7", 50940, "e750a032bd1eef5b5b5b43154ce36725c7e890af6a11132bc38b53b6e8b1ed03"),
    588: (4841, "4e44b3b150b4d49eb4c05ad4474b86004a3c0e1506bd0b844069ed60c710123a", 521, "19ae6d86507799f79f6d888f0f79616942ae23e644080b23df7477abe3928ae2", 24504, "e757b401afed957cc4eee73442e8fb8587024d44a716e5871cfe767617909a05"),
    590: (5755, "5cb97eb7e523a1fe7df006608a5cc68b41ddeb6c48ddbb974a7df65bb0307733", 2292, "85aa945555fde5584b188605f4858e6abc32ab6d1e10c890cca7f1965539fe61", 86652, "8689c98465db7990385ca969e8bc8e945807c2a3f44a6d37a1536cfdf51aa492"),
}

# Retail's former scanner-approval bit is now the persistent security keycard.
# The security battle is its only writer in this campaign; that credential
# opens Intake's patient-service, treatment-preparation, and three examination
# thresholds and remains one of the production bulkhead's four required
# authorizations.  Bit 8 in the same audited word is independently cleared by
# the Surface title bootstrap and unused by every retained retail field script,
# so it now records the Quarantine-only credential removed from examination
# room 593's visible Solaris terminal.
SECURITY_KEYCARD_OPERAND = 0x021A
SECURITY_KEYCARD_BIT_INDEX = 0
SECURITY_KEYCARD_MASK = 0x0001
QUARANTINE_KEYCARD_OPERAND = 0x021A
QUARANTINE_KEYCARD_BIT_INDEX = 8
QUARANTINE_KEYCARD_MASK = 0x0100
SCANNER_OPERAND = SECURITY_KEYCARD_OPERAND
SCANNER_MASK = SECURITY_KEYCARD_MASK
TONE_OPERAND = 0x021E
TONE_BIT_INDEX = 9
TONE_MASK = 0x0200
QUARANTINE_MASK = 0x0100


class SurfaceCampaignBuildError(base.SurfaceSoylentBuildError):
    """Raised when the frozen v173 campaign foundation changes."""


@dataclass(frozen=True)
class Console:
    x: int
    z: int
    triangle: int
    bit_index: int
    text: str
    interaction_half_width: int = 0x18
    interaction_half_depth: int = 0x18
    requires_facing: bool = False


@dataclass(frozen=True)
class DoorCollisionContract:
    """Separate one forgiving X target from its thin physical door seal."""

    controller_entity: int
    normal_axis: str


@dataclass(frozen=True)
class DonorDoorCollisionContract:
    """One donor threshold split into an X target and a physical seal.

    Most donor walkmeshes meet their door leaves on diagonals.  An axis-aligned
    thin rectangle can therefore leave a corner gap, so those thresholds use
    the engine's native circular actor-to-actor collision mode.  The three
    straight examination-room exits instead opt into an explicitly positioned
    rectangular seal.  ``cut_*`` is frozen geometry evidence used by the
    focused tests to prove that the closed seal disconnects the local doorway
    chord.
    """

    endpoint_id: str
    controller_entity: int
    x: int
    z: int
    triangle: int
    seal_radius: int
    cut_triangles: tuple[int, ...]
    closed_side_probe: tuple[int, int]
    open_side_probe: tuple[int, int]
    arrival_parameter: int | None = None
    interaction_half_width: int = 0x0A
    interaction_half_depth: int = 0x0A
    action_half_width: int | None = None
    action_half_depth: int | None = None
    init_state_suffix: bytes = b""
    immovable_precedes_stop: bool = False
    circular_seal_position: tuple[int, int] | None = None
    rectangular_seal_position: tuple[int, int] | None = None
    rectangular_seal_half_extents: tuple[int, int] | None = None


@dataclass(frozen=True)
class RouteRetarget:
    """One checked campaign-layer field destination replacement."""

    field: int
    controller_entity: int
    action_pc: int | None
    change_pc: int | None
    source_destination: tuple[int, int]
    destination: tuple[int, int]


# The v173 foundation used each rectangular door carrier for both interaction
# and physical collision.  That is convenient at a straight-on threshold, but
# its broad rectangle protrudes into neighboring walkmesh corners.  In field
# 621's lower-east vestibule, for example, the x-normal carrier at (1645,396)
# catches a player walking along the adjoining north/south lane before they
# reach the panel.  Campaign builds therefore keep the existing broad carrier
# as a ghost X target and give collision to a distinct, action-disabled seal
# whose normal half-extent is eight script units (sixteen world units).  The
# resulting 32-unit-thick barrier is wider than a full-speed field step, so it
# cannot be tunneled through, while remaining clear of the reported jamb
# position 26 units from the lower-east panel plane.
#
# Controller IDs are frozen after the v173 native-door conversion.  The axis
# describes the authentic panel normal, not the retired coordinate-poll axis.
SURFACE_DOOR_COLLISION_CONTRACTS = {
    623: (
        DoorCollisionContract(37, "z"),
        DoorCollisionContract(38, "z"),
    ),
    621: (
        DoorCollisionContract(20, "x"),
        DoorCollisionContract(21, "z"),
        DoorCollisionContract(22, "x"),
        DoorCollisionContract(23, "x"),
        DoorCollisionContract(24, "z"),
        DoorCollisionContract(25, "x"),
        DoorCollisionContract(26, "x"),
    ),
    620: (
        DoorCollisionContract(23, "x"),
        DoorCollisionContract(24, "x"),
    ),
    624: (
        DoorCollisionContract(0, "z"),
        DoorCollisionContract(1, "x"),
    ),
    626: (
        DoorCollisionContract(0, "z"),
        DoorCollisionContract(1, "z"),
    ),
    625: (
        DoorCollisionContract(0, "z"),
        DoorCollisionContract(6, "z"),
    ),
    622: (
        DoorCollisionContract(0, "x"),
        DoorCollisionContract(26, "z"),
    ),
}
DOOR_SEAL_NORMAL_HALF_EXTENT = 0x08


# The user's slot-5 capture stands at field 623's north threshold, directly
# south of the existing e37 controller at (0,1259).  The reciprocal field-621
# side already shows the facility's blue paired door, while field 623's own
# model archive contains the same paired leaves in the correct north/south
# plane as models 10/11.  Those models are currently used at the south door:
# their local geometry lies at z=-882 and spans x=-88..88, y=-132..0.
# The source leaves face into the room from its south threshold.  Reusing that
# winding unchanged at the opposite wall exposes their culled back faces to a
# party approaching the north exit.  Duplicate the records with a half-turn on
# Y, then place their actor origin at z=377: yaw 0x0800 maps local z=-882 to
# world z=1259 exactly.  The half-turn also swaps the physical left/right leaf,
# so their X slide directions are reversed.  No model or graphics bytes are
# imported or rewritten.
TRANSFER_NORTH_DOOR_CONTROLLER_ENTITY = 37
TRANSFER_NORTH_DOOR_SOURCE_HELPER_ENTITIES = (39, 40)
TRANSFER_NORTH_DOOR_HELPER_ENTITIES = (41, 42)
TRANSFER_NORTH_DOOR_SEAL_ENTITY = 43
TRANSFER_NORTH_DOOR_MODEL_INDICES = (10, 11)
TRANSFER_NORTH_DOOR_SOURCE_PLANE_Z = -882
TRANSFER_NORTH_DOOR_CLOSED_PLANE_Z = 1259
TRANSFER_NORTH_DOOR_ROTATION_Y = 0x0800
TRANSFER_NORTH_DOOR_ORIGIN_Z = (
    TRANSFER_NORTH_DOOR_CLOSED_PLANE_Z + TRANSFER_NORTH_DOOR_SOURCE_PLANE_Z
)
TRANSFER_NORTH_DOOR_FRAMES = 32
TRANSFER_NORTH_DOOR_SOUND_ID = 0x77
TRANSFER_NORTH_DOOR_HELPER_PCS = (
    (0x0C12, 0x0C15),
    (0x0D36, 0x0D39),
)
TRANSFER_NORTH_DOOR_ACTION_PC = 0x0E5A
TRANSFER_NORTH_DOOR_ANIMATION = base.DoorAnimation(
    621,
    6,
    (
        base.DoorLeafAnimation(39, 41, 0x0290, 10, -2, 0),
        base.DoorLeafAnimation(40, 42, 0x0290, 11, 2, 0),
    ),
    frames=TRANSFER_NORTH_DOOR_FRAMES,
)


# Three additional examination rooms open from Intake's otherwise blank
# eastern circulation wall.  The user's slot-1 stance marks the diagonal
# upper bay (A); the two straight eastern-wall bays (B/C) keep the doors far
# enough apart that their deliberately forgiving Cross volumes cannot overlap.
# The surrounding retail walkmesh ends at all three walls, so the visible
# panels need no second physical seal: while closed, the wall itself remains
# the authoritative barrier.  Unlike Intake's native doors, however, these
# three bays sit over continuous white wall polygons instead of real shell
# apertures.  Model 1 is therefore cut only at the three exact panel rectangles
# (retaining a cropped strip of the native lintel texture).  The field's black
# clear supplies the same dark reveal as its authentic apertures after a leaf
# opens; a finite rear polygon cannot remain safe across this room's complete
# orbital-camera path.  Retail model 19 gives the native panels 44-unit
# textured floor aprons beyond their leaf planes.  Model 20 retains its
# 396-byte allocation and reproduces that top-facing detail on the far side of
# the three added doors as the same single whole-width FT4 used by the retail
# doorway, with no hall-side or vertical polygon.  The former two-half clone
# let the nearer half sort in front of a closed leaf at oblique camera angles;
# keeping the retail one-primitive topology removes that ordering ambiguity.
# Its far-depth V endpoint stops at the source texture's cyan shadow row rather
# than continuing into six near-black rows.
# Native model
# 2 also contains 138 solid-
# black F3/F4 ceiling-fascia primitives which sweep across the party at the
# user's saved camera angles.  Their index records are made degenerate in
# place, preserving the textured ceiling/wall groups and every model offset.
INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES = (43, 44, 45)
INTAKE_EXAM_ROOM_HELPER_ENTITIES = (46, 47, 48)
INTAKE_EXAM_ROOM_THRESHOLD_HEADER_ENTITIES = (60, 61, 62)
INTAKE_EXAM_ROOM_DESTINATIONS = ((591, 0), (592, 0), (593, 0))
INTAKE_EXAM_ROOM_DOORS = (
    base.DoorController(1650, 1246, 0x10, 0x10, 591, 0, 77),
    base.DoorController(1774, 840, 0x10, 0x18, 592, 0, 81),
    base.DoorController(1774, 396, 0x10, 0x18, 593, 0, 81),
)
INTAKE_EXAM_ROOM_ENTRY_ADDITIONS = (
    base.mass_driver.FieldEntryAddition(1598, 1194, 0, 6, 5),
    base.mass_driver.FieldEntryAddition(1720, 840, 0, 6, 6),
    base.mass_driver.FieldEntryAddition(1720, 396, 0, 6, 6),
)
# (1598,1194) is on triangle 76; triangle 77 begins farther east at the
# carrier position (1650,1246).  Entry records store the walkmesh layer, while
# this triangle tuple is the exact geometry proof used by the build/tests.
INTAKE_EXAM_ROOM_ENTRY_TRIANGLES = (76, 81, 84)
INTAKE_EXAM_ROOM_ENTRY_PARAMETERS = (7, 8, 9)
INTAKE_EXAM_ROOM_ENTRY_RESUME_PC = 0x00F2
INTAKE_EXAM_ROOM_MODEL_FLAGS = 0x0290
INTAKE_EXAM_ROOM_MODEL_PLACEMENTS = (
    # (model, yaw, origin x/y/z, slide dx/dz)
    # Model 3's rendered face is opposite its geometric -Z normal.  The
    # half-turn makes that face point southwest toward the saved hallway
    # stance.  The translated origin places its endpoints directly over the
    # rendered diagonal-wall bay instead of the inset walkmesh edge.
    (3, 0x0A00, 3088, 0, 1463, -2, 2),
    # Models 6 and 7 are the matching upper/lower east-wall bays.  Their
    # x=88 panel planes land exactly on the newly cut wall plane at x=1821.
    # This restores V209's native co-planarity instead of retaining V210's
    # deliberate two-unit hall-side offset for its superseded black reveal.
    (6, 0x0000, 1733, 0, 0, 0, -2),
    (7, 0x0000, 1733, 0, 0, 0, -2),
)
INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX = 20
INTAKE_EXAM_ROOM_THRESHOLD_MODEL_FLAGS = 0x0010
INTAKE_EXAM_ROOM_WALL_MODEL_INDEX = 1
INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX = 2
INTAKE_EXAM_ROOM_WALL_MODEL_SIZE = 16_280
INTAKE_EXAM_ROOM_WALL_MODEL_SHA256 = (
    "b577ca3070b92a763b32d90353add649011a123bb0f37bd4a1b94e2da709ae08"
)
INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SIZE = 396
INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SHA256 = (
    "8ef50d3f377c7b8caf2fdcfa0fcaecebe3d25ce5a51a90dfa0f14a734fdf3b52"
)
INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SIZE = 4_836
INTAKE_EXAM_ROOM_NATIVE_OCCLUDER_MODEL_SHA256 = (
    "b093460d49974a083f191442a2aaafb75983da7ed5ad78201b3d46f5b4b2bdd3"
)
INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SHA256 = (
    "2d0b40fb67720162fe93bb3fa522d33c3cf3db8333865f3f8d7c897688fad5d3"
)
# Keep the static record identities and 396-byte model-20 allocation frozen for
# live-state compatibility.  Reverse each transform so local +Z begins at the
# leaf plane and extends only onto the far side of the aperture, exactly like
# the native doorway floor.  The accessible hall remains on local -Z, where
# model 20 has no geometry to overlap model 1's existing floor.
INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS = (
    (0x0200, 1645, 0, 1307),
    (0x0400, 1821, 0, 882),
    (0x0400, 1821, 0, 441),
)
INTAKE_EXAM_ROOM_SLIDE_FRAMES = 32
INTAKE_EXAM_ROOM_SOUND_ID = 0x77
# Frozen to the existing generic security-keycard lock block; the installer
# also checks this against INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID once all
# campaign dialogue constants have been defined.
INTAKE_EXAM_ROOM_LOCK_DIALOGUE_ID = 22
INTAKE_EXAM_ROOM_ENTRY_EDITS = tuple(
    base.EntryEdit(
        parameter,
        base.FieldEntry(
            addition.x,
            addition.z,
            addition.walkmesh,
            addition.camera_direction,
            addition.actor_direction,
        ),
        base.FieldEntry(
            addition.x,
            addition.z,
            addition.walkmesh,
            addition.camera_direction,
            addition.actor_direction,
        ),
        triangle,
    )
    for parameter, addition, triangle in zip(
        INTAKE_EXAM_ROOM_ENTRY_PARAMETERS,
        INTAKE_EXAM_ROOM_ENTRY_ADDITIONS,
        INTAKE_EXAM_ROOM_ENTRY_TRIANGLES,
        strict=True,
    )
)
INTAKE_EXAM_ROOM_EDGES = tuple(
    base.Edge(
        "x",
        door.x,
        0x44,
        door.destination_field,
        door.destination_parameter,
        (door.x, door.z),
        door.triangle,
    )
    for door in INTAKE_EXAM_ROOM_DOORS
)
INTAKE_EXAM_ROOM_ANIMATIONS = tuple(
    base.DoorAnimation(
        door.destination_field,
        door.destination_parameter,
        (
            base.DoorLeafAnimation(
                helper_entity,
                helper_entity,
                INTAKE_EXAM_ROOM_MODEL_FLAGS,
                placement[0],
                placement[5],
                placement[6],
            ),
        ),
        frames=INTAKE_EXAM_ROOM_SLIDE_FRAMES,
    )
    for door, helper_entity, placement in zip(
        INTAKE_EXAM_ROOM_DOORS,
        INTAKE_EXAM_ROOM_HELPER_ENTITIES,
        INTAKE_EXAM_ROOM_MODEL_PLACEMENTS,
        strict=True,
    )
)


# Active campaign endpoints hosted by donor fields sit on diagonal panel
# planes.  Radius 0x0E becomes 28 world units; player contact adds Fei's
# audited 16-unit radius for an effective closed threshold of 44.  Field 565's
# two same-field mechanisms span wider apertures, so their seals use radius
# 0x12 (36 world / 52 effective) and are released only by a genuine native
# opening path.
DONOR_DOOR_SEAL_RADIUS = 0x0E
DONOR_INTERNAL_GATE_SEAL_RADIUS = 0x12
PLAYER_COLLISION_RADIUS = 0x10
FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT = 0x18

# Field 549's diagonal archive-return aperture lies beside the southwest
# circulation line.  Radius 0x08 is the minimum single circle that closes the
# threshold once Fei's 16-unit radius is included, but centering it directly
# on e6 still protrudes into the user's V229 southwest travel ray.  Move only
# the action-disabled physical actor four units west and eight north, deeper
# into triangle 12.  Its effective radius-32 disk then clears that exact ray
# by 5.639 world units, forms a boundary-to-boundary closed cut, and remains
# wholly inside e6's unchanged 36-by-40 deliberate-X shell.  The visible leaf,
# action carrier, native helper, and X-only behavior stay at (-240,240).
ARCHIVE_RETURN_SEAL_RADIUS = 0x08
ARCHIVE_RETURN_SEAL_CENTER = (-244, 248)
ARCHIVE_RETURN_SEAL_TRIANGLE = 12

# Field 352's straight north exit has a narrow walkmesh aperture centered on
# x=0.  Its former radius-0x0E seal at z=250 began touching Fei near z=232.
# Every field-352 examination room, including the doctor's office in logical
# field 550, therefore uses the same z-normal rectangle.  OP18 doubles both
# half-extents, while EntityMoveCheck0 passes an extra radius of zero to
# rectangular script volumes.  Its physical inner and outer planes are
# therefore z=250/z=282.  The separate ghost action carrier has an effective
# Cross reach of 64x48 world units, so both reported off-center z=228 stances
# and the straight field-592 z=224.99 stance can deliberately open the door
# without an automatic proximity action.  The audited arrival at z=200 and
# open-side probe at z=300 remain clear.
EXAM_RETURN_RECTANGULAR_SEAL_POSITION = (0, 266)
EXAM_RETURN_RECTANGULAR_SEAL_HALF_EXTENTS = (0x18, 0x08)
FIELD352_X_ONLY_SCENES = (550, 567, *exam_rooms.SCENES)
FIELD352_SIDE_TERMINAL_SCENES = (567, *exam_rooms.SCENES)

# All field-352 story actors are retired in the examination-room foundation.
# E14:s5's complete former routine is therefore a checked 87-byte cavity.
# Field 550 keeps it byte-identical and unreachable.  Empty field 567 and
# occupied fields 591-594 use it only for two exact side-computer carrier
# initializers; their action slots still point to the shared deliberate-X
# terminal routine, never into the cavity.  E0:s1 remains the shared STOP in
# every room, making e17:s2's broad collision-selected Cross action the only
# way to invoke the door.
EXAM_RETURN_RETIRED_CAVITY_PC = 0x044E
EXAM_RETURN_RETIRED_CAVITY_END_PC = 0x04A5
EXAM_RETURN_RETIRED_CAVITY_ENTITY = 14
EXAM_RETURN_RETIRED_CAVITY_SCRIPT = 5
EXAM_RETURN_RETIRED_CAVITY_SOURCE = bytes.fromhex(
    "21 30 81 4A 5A 00 3E 00 C0 4A 5A 00 C8 FF C0 69 06 80 "
    "26 0A 80 2C 04 FE 0D 01 80 D2 24 00 00 9C 09 FF C5 26 "
    "0A 80 2C 00 D2 25 00 00 9C 09 FE C6 26 0A 80 69 00 80 "
    "26 05 80 D2 26 00 00 9C 09 FF C7 FE 24 26 04 80 FE AA "
    "FF 35 E0 00 00 00 40 FE 53 2C 00 69 06 80 00"
)

# The wider field-565 ghost targets extend 64 world units from their centers
# after Fei's collision radius is included.  Each reciprocal arrival is moved
# farther into its audited source-side triangle so a held Cross press cannot
# immediately select the door again after a field transition.
FIELD565_CLEAR_ARRIVALS = {
    # parameter: (checked V200 entry, V201 entry, audited triangle)
    0: ((-24, 24, 0, 7, 3), (33, -33, 0, 7, 3), 75),
    1: ((4864, -3626, 0, 5, 5), (4813, -3671, 0, 5, 5), 8),
    2: ((4240, -3000, 0, 1, 5), (4190, -3044, 0, 1, 5), 12),
    3: ((3615, -2385, 0, 1, 5), (3570, -2430, 0, 1, 5), 17),
    4: ((1097, -4523, 0, 1, 1), (1152, -4468, 0, 1, 1), 57),
    5: ((3020, -4477, 0, 0xFF, 0xFF), (2970, -4520, 0, 5, 5), 64),
    6: ((3330, -5773, 0, 7, 7), (3270, -5718, 0, 7, 7), 68),
}

DONOR_DOOR_COLLISION_CONTRACTS = {
    549: (
        DonorDoorCollisionContract(
            "intake_archive.archive", 6, -240, 240,
            ARCHIVE_RETURN_SEAL_TRIANGLE,
            ARCHIVE_RETURN_SEAL_RADIUS, (6, 10, 11, 12, 13),
            (-200, 200), (-276, 276), arrival_parameter=0,
            # Slot 1 from v179 captured Fei at
            # (-13924297/65536, 13206107/65536).  The native 0x0A depth
            # misses that straight-on stance; 0x0B still reaches only 38
            # world units after Fei's radius, while 0x0C reaches 40.
            action_half_depth=0x0C,
            circular_seal_position=ARCHIVE_RETURN_SEAL_CENTER,
        ),
    ),
    550: (
        DonorDoorCollisionContract(
            "intake_scanner.scanner", 17, 0, 250, 34,
            DONOR_DOOR_SEAL_RADIUS, (16, 34, 35),
            (0, 200), (0, 300), arrival_parameter=0,
            interaction_half_width=0x18,
            interaction_half_depth=0x08,
            # The source carrier's narrow depth is retained as frozen evidence,
            # while the emitted ghost X target reaches past first seal contact.
            action_half_depth=0x10,
            rectangular_seal_position=(
                EXAM_RETURN_RECTANGULAR_SEAL_POSITION
            ),
            rectangular_seal_half_extents=(
                EXAM_RETURN_RECTANGULAR_SEAL_HALF_EXTENTS
            ),
        ),
    ),
    565: (
        DonorDoorCollisionContract(
            "intake_service_patient.service", 4, -62, 62, 74,
            DONOR_DOOR_SEAL_RADIUS, (75, 74),
            (33, -33), (-102, 102), arrival_parameter=0,
            action_half_width=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
            action_half_depth=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
        ),
        DonorDoorCollisionContract(
            "service_stabilization_production.service", 5, 4905, -3590, 9,
            DONOR_DOOR_SEAL_RADIUS, (8, 9),
            (4813, -3671), (4950, -3545), arrival_parameter=1,
            action_half_width=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
            action_half_depth=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
        ),
        DonorDoorCollisionContract(
            "service_stabilization_staff.service", 6, 4280, -2965, 13,
            DONOR_DOOR_SEAL_RADIUS, (12, 13),
            (4190, -3044), (4325, -2920), arrival_parameter=2,
            action_half_width=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
            action_half_depth=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
        ),
        DonorDoorCollisionContract(
            "field565.future_lab_handoff_sealed", 7, 3660, -2340, 16,
            DONOR_DOOR_SEAL_RADIUS, (17, 16),
            (3570, -2430), (3700, -2300), arrival_parameter=None,
            action_half_width=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
            action_half_depth=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
        ),
        DonorDoorCollisionContract(
            "service_resonance.service", 8, 1060, -4560, 56,
            DONOR_DOOR_SEAL_RADIUS, (57, 56),
            (1152, -4468), (1020, -4600), arrival_parameter=4,
            action_half_width=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
            action_half_depth=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
        ),
        DonorDoorCollisionContract(
            "service_interface_annex.service", 9, 3055, -4440, 65,
            DONOR_DOOR_SEAL_RADIUS, (64, 65),
            (2970, -4520), (3100, -4400), arrival_parameter=5,
            action_half_width=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
            action_half_depth=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
        ),
        DonorDoorCollisionContract(
            "quarantine_service.service", 10, 3370, -5810, 67,
            DONOR_DOOR_SEAL_RADIUS, (68, 67),
            (3270, -5718), (3410, -5850), arrival_parameter=6,
            action_half_width=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
            action_half_depth=FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT,
        ),
        DonorDoorCollisionContract(
            "field565.internal_gate_11", 11, 560, -560, 71,
            DONOR_INTERNAL_GATE_SEAL_RADIUS, (70, 71, 72),
            (798, -821), (495, -555),
            interaction_half_width=0x1E,
            interaction_half_depth=0x1E,
            init_state_suffix=bytes.fromhex("37 00 04"),
        ),
        DonorDoorCollisionContract(
            "field565.internal_gate_12", 12, 3500, -1060, 32,
            DONOR_INTERNAL_GATE_SEAL_RADIUS, (31, 32, 33),
            (3570, -1060), (3400, -980),
            interaction_half_width=0x1E,
            interaction_half_depth=0x1E,
            init_state_suffix=bytes.fromhex("37 16 04"),
        ),
    ),
    567: (
        DonorDoorCollisionContract(
            "intake_medical_examination.examination", 17, 0, 250, 34,
            DONOR_DOOR_SEAL_RADIUS, (16, 34, 35),
            (0, 200), (0, 300), arrival_parameter=0,
            interaction_half_width=0x18,
            interaction_half_depth=0x08,
            action_half_depth=0x10,
            rectangular_seal_position=(
                EXAM_RETURN_RECTANGULAR_SEAL_POSITION
            ),
            rectangular_seal_half_extents=(
                EXAM_RETURN_RECTANGULAR_SEAL_HALF_EXTENTS
            ),
        ),
    ),
    **{
        scene: (
            DonorDoorCollisionContract(
                exam_rooms.DOOR_ENDPOINT_IDS_BY_SCENE[scene],
                exam_rooms.RETURN_CONTROLLER,
                exam_rooms.RETURN_CONTROLLER_POSITION[0],
                exam_rooms.RETURN_CONTROLLER_POSITION[1],
                exam_rooms.RETURN_CONTROLLER_TRIANGLE,
                exam_rooms.DOOR_SEAL_RADIUS,
                exam_rooms.RETURN_CONTROLLER_TRIANGLES,
                exam_rooms.DOOR_CLOSED_SIDE_PROBE,
                exam_rooms.DOOR_OPEN_SIDE_PROBE,
                arrival_parameter=exam_rooms.ENTRY_PARAMETER,
                interaction_half_width=exam_rooms.DOOR_INTERACTION_HALF_WIDTH,
                interaction_half_depth=exam_rooms.DOOR_INTERACTION_HALF_DEPTH,
                action_half_depth=exam_rooms.DOOR_ACTION_HALF_DEPTH,
                rectangular_seal_position=(
                    EXAM_RETURN_RECTANGULAR_SEAL_POSITION
                ),
                rectangular_seal_half_extents=(
                    EXAM_RETURN_RECTANGULAR_SEAL_HALF_EXTENTS
                ),
            ),
        )
        for scene in exam_rooms.SCENES
    },
    588: (
        DonorDoorCollisionContract(
            "service_interface_annex.interface",
            donor588.RETURN_CONTROLLER,
            donor588.RETURN_CONTROLLER_POSITION[0],
            donor588.RETURN_CONTROLLER_POSITION[1],
            donor588.RETURN_CONTROLLER_TRIANGLE,
            DONOR_DOOR_SEAL_RADIUS,
            donor588.RETURN_CUT_TRIANGLES,
            donor588.RETURN_CLOSED_SIDE_PROBE,
            donor588.RETURN_OPEN_SIDE_PROBE,
            arrival_parameter=0,
            interaction_half_width=donor588.RETURN_INTERACTION_HALF_WIDTH,
            interaction_half_depth=donor588.RETURN_INTERACTION_HALF_DEPTH,
            action_half_width=donor588.RETURN_ACTION_HALF_WIDTH,
            action_half_depth=donor588.RETURN_ACTION_HALF_DEPTH,
            immovable_precedes_stop=True,
        ),
    ),
    589: (
        DonorDoorCollisionContract(
            "service_resonance.resonance", 4, 380, 160, 69,
            DONOR_DOOR_SEAL_RADIUS, (57, 69),
            (340, 120), (420, 200), arrival_parameter=0,
        ),
    ),
    590: (
        DonorDoorCollisionContract(
            "service_stabilization_production.stabilization",
            donor567.LOBBY_CONTROLLER,
            65,
            435,
            89,
            0x1C,
            (88, 89, 90),
            stabilization590.ENTRY_POSITIONS[0],
            (-25, 459),
            arrival_parameter=0,
            interaction_half_width=donor567.CONTROLLER_INTERACTION_HALF_EXTENTS[0],
            interaction_half_depth=donor567.CONTROLLER_INTERACTION_HALF_EXTENTS[1],
            action_half_width=stabilization590.ACTION_HALF_EXTENT,
            action_half_depth=stabilization590.ACTION_HALF_EXTENT,
            immovable_precedes_stop=True,
        ),
        DonorDoorCollisionContract(
            "service_stabilization_staff.stabilization",
            donor567.SERVICE_CONTROLLER,
            935,
            -440,
            45,
            DONOR_DOOR_SEAL_RADIUS,
            (45, 46, 51),
            stabilization590.ENTRY_POSITIONS[1],
            (1010, -520),
            arrival_parameter=1,
            interaction_half_width=donor567.CONTROLLER_INTERACTION_HALF_EXTENTS[0],
            interaction_half_depth=donor567.CONTROLLER_INTERACTION_HALF_EXTENTS[1],
            action_half_width=stabilization590.ACTION_HALF_EXTENT,
            action_half_depth=stabilization590.ACTION_HALF_EXTENT,
            immovable_precedes_stop=True,
        ),
        DonorDoorCollisionContract(
            "stabilization_sorting.stabilization",
            donor567.RESTRICTED_CONTROLLER,
            1000,
            -125,
            48,
            0x1C,
            (47, 48, 49, 52),
            stabilization590.ENTRY_POSITIONS[2],
            (1085, -50),
            arrival_parameter=2,
            interaction_half_width=donor567.CONTROLLER_INTERACTION_HALF_EXTENTS[0],
            interaction_half_depth=donor567.CONTROLLER_INTERACTION_HALF_EXTENTS[1],
            action_half_width=stabilization590.ACTION_HALF_EXTENT,
            action_half_depth=stabilization590.ACTION_HALF_EXTENT,
            immovable_precedes_stop=True,
        ),
    ),
}


# The user's live V180 audit established that the visible side-corridor panel
# at field 621 e22 should own the crowded Quarantine Diagnostics room
# demonstrated in Step 2.  The matching Step-1 threshold is e21, the unique
# north-center double door with paired leaf models 8/9; e24 is a single-leaf
# service-manifold door and was the source of V181's hallway misroute.
# Retarget three checked in-place CHANGE_FIELD operands and the checked
# destination used to rebuild field 549's active seal-release wrapper.  Every
# physical leaf, helper animation, action carrier, seal, arrival, and walkmesh
# remains in its audited location.
ROOM_SWAP_RETARGETS = (
    # Donor field 565 routes are rebuilt as fresh-X wrappers after their
    # native leaf/player bodies have been frozen, so they intentionally have
    # no stable in-place action/change PCs.
    RouteRetarget(565, 5, None, None, (624, 0), (590, 0)),
    RouteRetarget(565, 6, None, None, (621, 4), (590, 1)),
    RouteRetarget(621, 21, 0x0CCD, 0x0CE4, (620, 0), (549, 0)),
    RouteRetarget(621, 22, 0x0D52, 0x0D66, (549, 0), (620, 0)),
    # Save State 1 marks the east-facing field-621 panel e25 at (88,396).
    # It now opens into a quiet one-door medical examination annex instead of
    # either the long service manifold or the reserved stabilization donor.
    RouteRetarget(621, 25, 0x0D1E, 0x0D32, (565, 2), (567, 0)),
    # Save State 1 identifies the original west-side freight door e26.  Keep
    # its checked keycard gate and authentic leaf, but route the threshold to
    # the new bright treatment-preparation room instead of Krelian's Lab.
    RouteRetarget(621, 26, 0x0D38, 0x0D4C, (565, 3), (594, 0)),
    RouteRetarget(620, 23, 0x0A71, 0x0A85, (621, 0), (621, 2)),
    # The recovered ward now owns the production-side threshold.  Field 624's
    # native south door remains the reciprocal endpoint, but returns to p2 of
    # logical field 590 rather than directly to the service manifold.
    RouteRetarget(624, 0, 0x133F, 0x1341, (565, 1), (590, 2)),
    # Field 549's native donor action is represented by an appended active
    # wrapper, so it deliberately has no stable in-place action/change PC.
    RouteRetarget(549, 6, None, None, (621, 2), (621, 0)),
    # The bright interface scanner is now a reciprocal Service-Manifold annex.
    # Its retained field-550-derived return action is wrapped after collision
    # separation, so this route also has no stable in-place action/change PC.
    RouteRetarget(
        588,
        donor588.RETURN_CONTROLLER,
        None,
        None,
        (donor588.RETURN_FIELD, donor588.RETURN_PARAMETER),
        (565, 5),
    ),
)


SORTER_CONSOLES = (
    Console(
        141,
        -528,
        67,
        0,
        "SORTING FEED A // LIVING TISSUE\n"
        "Diversion: stasis assay.\n"
        "Production feed isolated.<Close>",
    ),
    Console(
        -492,
        -131,
        73,
        1,
        "SORTING FEED B // NANOMACHINE MEDIUM\n"
        "Diversion: reclamation drain.\n"
        "Production feed isolated.<Close>",
    ),
    Console(
        -1103,
        312,
        58,
        2,
        "SORTING FEED C // UNSTABLE MELD\n"
        "Diversion: containment return.\n"
        "Production feed isolated.<Close>",
    ),
)
SORTER_SUCCESS_DIALOGUE = (
    "MOLECULAR DIVERSION COMPLETE\n"
    "All three living-material feeds\n"
    "are isolated from production.<Close>"
)

CORE_CONSOLES = (
    Console(
        -300,
        -250,
        0,
        0,
        "M-PROJECT RING A // FUSION LATTICE\n"
        "Power discharged.\n"
        "The reconstruction feed is interrupted.<Close>",
    ),
    Console(
        300,
        -250,
        1,
        1,
        "M-PROJECT RING B // PATTERN ALIGNMENT\n"
        "Template uncoupled.\n"
        "No weapon-form can be imposed.<Close>",
    ),
    Console(
        0,
        300,
        0,
        2,
        "M-PROJECT RING C // CONTAINMENT\n"
        "Containment remains active.\n"
        "The people inside are not released into the line.<Close>",
    ),
)
CORE_SUCCESS_DIALOGUE = (
    "M-PROJECT SAFE STATE RECORDED\n"
    "Fusion and pattern are offline.\n"
    "Containment remains active.<Close>"
)

MELD_CONSOLE = Console(
    0,
    0,
    1,
    MELD_BIT_INDEX,
    "Many faces move behind the containment glass.\n"
    "Meld is not one creature, but people forced together.\n"
    "Their eyes ask for the pain to end.<New>"
    "Elly\n"
    '"I can hear them. They know we are here."<New>'
    "Fei\n"
    '"Then we stop the generation line."<New>'
    "Citan\n"
    '"Keep containment stable until the node is shut down."<Close>',
    0x20,
    0x20,
)

SERVICE_PRODUCTION_DENIAL_DIALOGUE_ID = 12
SERVICE_QUARANTINE_DENIAL_DIALOGUE_ID = 13
SERVICE_INTERNAL_KEYCARD_DENIAL_DIALOGUE_ID = 14
SERVICE_NETWORK_BRIEFING_DIALOGUE_ID = 15
SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE_ID = 16
SERVICE_INTERNAL_KEYCARD_DENIAL_DIALOGUE = (
    "SERVICE PASSAGE LOCKED\n"
    "A security keycard is required.<Close>"
)
SERVICE_NETWORK_BRIEFING_DIALOGUE = (
    "FREIGHT SERVICE NETWORK\n"
    "Three production authorizations remain:\n"
    "quarantine consensus, organic resonance,\n"
    "and bio-interface cutoff.<Close>"
)
SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE = (
    "DEEP SERVICE ACCESS SEALED\n"
    "This transfer route is not\n"
    "currently authorized.<Close>"
)
# The user's exact Slot-1 stance in field 620 identifies the east continuation
# controller e24, not the west Intake return.  Until the next dungeon segment
# is authored, that one post-clearance action is a repeatable, non-opening
# content boundary.  Appending it after the generic seal pass keeps every
# existing door and seal routine PC frozen.
QUARANTINE_CURRENT_END_DOOR_ENTITY = 24
QUARANTINE_CURRENT_END_DOOR_ACTION_PC = 0x0C42
QUARANTINE_CURRENT_END_DIALOGUE_ID = 24
QUARANTINE_CURRENT_END_DIALOGUE = (
    "This is the end for now.\n"
    "The rest is coming soon...<Close>"
)
# V237 keeps the historical constants above for exact old-save migrations.
# The active door now validates the diagnostics and commits their clearance
# only after the acceptance receipt closes, before using the native animation.
QUARANTINE_COMPLETION_DIALOGUE = (
    "BIOLOGICAL CONSENSUS ACCEPTED\n"
    "Human identity is retained.\n"
    "Service access is available.<Close>"
)
RESONANCE_CLUE_BIT_INDEX = 8
RESONANCE_CLUE_BIT_MASK = 0x0100
RESONANCE_CLUE_ENTITY = 9
RESONANCE_CLUE_ACTION_PC = 0x01EE
RESONANCE_CLUE_TAIL_PC = 0x022F
RESONANCE_CLUE_TAIL = bytes.fromhex("FE 0E 7F 80 14 80 2B FE 53 00")
RESONANCE_CLUE_RECEIPT_ACTION_PC = 0x0A16
RESONANCE_CLUE_RECEIPT_DIALOGUE_ID = 5
RESONANCE_CLUE_RECEIPT_DIALOGUE = (
    "RESONANCE PATTERN RECORDED\n"
    "Repeat the five directions at\n"
    "the service input panel.<Close>"
)
PROGRESSION_CONFIRM_SOUND_ID = 0x50
PROGRESSION_CONFIRM_SOUND = b"\x74\x50\x80"

INTERFACE_CONSOLE = Console(
    donor588.CONSOLE_POSITION[0],
    donor588.CONSOLE_POSITION[1],
    donor588.CONSOLE_TRIANGLE,
    INTERFACE_BIT_INDEX,
    "DIAGNOSTIC CLEARANCE COMPLETE\n"
    "Patient profile matched.\n"
    "Living-subject cutoff armed.<Close>",
    donor588.CONSOLE_INTERACTION_HALF_WIDTH,
    donor588.CONSOLE_INTERACTION_HALF_DEPTH,
)
INTERFACE_DIAGNOSTIC_DIALOGUE_ID = 10
# Field 588's donor retires its retail scanner action by repointing every live
# slot to STOP, but the old body at this checked PC still contains a raw write
# to operand 0x021A bit 8.  Neutralize that dead instruction as well so the
# examination-room terminal in field 593 is the sole writer in the complete
# staged bytecode inventory, not merely the sole reachable writer.
INTERFACE_RETIRED_KEYCARD_WRITE_PC = 0x03CE
QUARANTINE_KEYCARD_DIALOGUE_ID = 11
QUARANTINE_KEYCARD_DIALOGUE = (
    "QUARANTINE KEYCARD ACQUIRED\n"
    "Access authorization:\n"
    "QUARANTINE DIAGNOSTICS.<Close>"
)
GENERATION_SAVE_CONSOLE = Console(
    -250,
    -132,
    177,
    0,
    "",
    0x18,
    0x18,
)
GENERATION_BOSS_CONSOLE = Console(
    250,
    -132,
    185,
    SECURED_BIT_INDEX,
    "",
    0x18,
    0x18,
)

INTAKE_BOY_ENTITY = 11
INTAKE_BOY_DIALOGUE_ID = 7
INTAKE_BOY_DIALOGUE = "I like turtles!<Close>"

# The Intake lobby is still a public-facing waiting area.  These patients
# believe the screening and treatment program is legitimate; they do not yet
# know what the deeper Soylent machinery does with them.  Keep that later
# revelation out of their ambient dialogue while preserving the boy separately.
INTAKE_WAITING_AREA_HOPEFUL_DIALOGUES = {
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

# The user's saved stance identifies the actual desk receptionist, rather than
# the nearby survivor who already owns dialogue 2.  The receptionist's retail
# action is a STOP-only slot; the north door directly behind the saved Fei
# stance is e21 and leads to the archive terminal below.  Retail's default
# 64-unit circular X reach cannot cross the desk to the saved 131.61-unit
# stance, so e13 also receives a bounded rectangular, collision-ghosted init.
INTAKE_RECEPTIONIST_ENTITY = 13
INTAKE_RECEPTIONIST_RETAIL_INIT_PC = 0x01B3
INTAKE_RECEPTIONIST_RETAIL_ACTION_PC = 0x01C3
INTAKE_RECEPTIONIST_ACTION_PC = 0x0D6C
INTAKE_RECEPTIONIST_WIDE_INIT_PC = 0x0DAF
INTAKE_RECEPTIONIST_INTERACTION_HALF_WIDTH = 0x20
INTAKE_RECEPTIONIST_INTERACTION_HALF_DEPTH = 0x40
INTAKE_RECEPTIONIST_RETAIL_INIT = bytes.fromhex(
    "FE 15 07 80 01 80 19 66 03 16 05 C0 5F 00 00"
)
INTAKE_ARCHIVE_DOOR_ENTITY = 21
INTAKE_ARCHIVE_DOOR_ACTION_PC = 0x0CCD
INTAKE_QUARANTINE_DOOR_ENTITY = 22
INTAKE_QUARANTINE_DOOR_ACTION_PC = 0x0D52
INTAKE_QUARANTINE_DOOR_CHANGE_PC = 0x0D66
INTAKE_QUARANTINE_DESTINATION = (620, 0)
INTAKE_QUARANTINE_LOCK_ACTION_PC = 0x15D9
INTAKE_QUARANTINE_LOCK_DIALOGUE_ID = 21
INTAKE_QUARANTINE_UNLOCKED_ACTION = bytes.fromhex(
    "33 FE 54 31 20 00 60 0D 26 01 80 01 55 0D 74 77 80 "
    "09 02 24 98 6C 82 00 80 5B"
)
INTAKE_QUARANTINE_LOCK_DIALOGUE = (
    "QUARANTINE ACCESS SEALED\n"
    "A Quarantine keycard is\n"
    "required for entry.<Close>"
)
INTAKE_PATIENT_DOOR_ENTITY = 24
INTAKE_PATIENT_DOOR_ACTION_PC = 0x0D04
INTAKE_PATIENT_DOOR_CHANGE_PC = 0x0D18
INTAKE_PATIENT_DESTINATION = (565, 0)
INTAKE_PATIENT_UNLOCKED_ACTION = bytes.fromhex(
    "33 FE 54 31 20 00 12 0D 26 01 80 01 07 0D 74 77 80 "
    "09 20 24 98 35 82 00 80 5B"
)
INTAKE_FREIGHT_DOOR_ENTITY = 26
INTAKE_FREIGHT_DOOR_ACTION_PC = 0x0D38
INTAKE_FREIGHT_DOOR_CHANGE_PC = 0x0D4C
INTAKE_FREIGHT_DESTINATION = (594, 0)
INTAKE_FREIGHT_KEYCARD_GATE_ACTION_PC = 0x1617
INTAKE_PATIENT_KEYCARD_GATE_ACTION_PC = 0x1655
INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID = 22
INTAKE_FREIGHT_AUTHORIZATION_LOCK_DIALOGUE_ID = 23
INTAKE_FREIGHT_UNLOCKED_ACTION = bytes.fromhex(
    "33 FE 54 31 20 00 46 0D 26 01 80 01 3B 0D 74 77 80 "
    "09 22 24 98 52 82 00 80 5B"
)
INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE = (
    "The door is locked.\n"
    "A security keycard is\n"
    "required.<Close>"
)
INTAKE_FREIGHT_AUTHORIZATION_LOCK_DIALOGUE = (
    "CREDENTIAL LAB SEALED\n"
    "Security keycard plus\n"
    "five-tone authorization\n"
    "required.<Close>"
)
ARCHIVE_TERMINAL_ENTITY = 4
ARCHIVE_TERMINAL_RETAIL_ACTION_PC = 0x00D8
ARCHIVE_CHECKIN_ACTION_PC = 0x079E
ARCHIVE_TERMINAL_NATIVE_MENU_DIALOGUE_ID = 1
ARCHIVE_TERMINAL_NATIVE_MENU_PC = 0x010F
ARCHIVE_TERMINAL_NATIVE_CLOSE_PC = 0x0161
ARCHIVE_TERMINAL_NATIVE_STOP_PC = 0x0179
ARCHIVE_TERMINAL_SCREEN_ENTITIES = (8, 9, 10, 11, 12, 13)
ARCHIVE_TERMINAL_SCREEN_OPEN_SCRIPT = 4
ARCHIVE_TERMINAL_SCREEN_CLOSE_SCRIPT = 5
ARCHIVE_TERMINAL_SCREEN_OPEN_PCS = (
    0x01D6,
    0x025A,
    0x02DE,
    0x0362,
    0x03E6,
    0x046A,
)
ARCHIVE_TERMINAL_SCREEN_CLOSE_PCS = (
    0x0212,
    0x0296,
    0x031A,
    0x039E,
    0x0422,
    0x04A6,
)
ARCHIVE_TERMINAL_NATIVE_ACTION_SHA256 = (
    "c66459205592d5cb516c333ebc7fee66eb3257c76702a1ba61ba08fc45dc94e8"
)
ARCHIVE_CHECKIN_ACTION_SHA256 = (
    "4a066a9d68b311782325256332014d9148abb727fe1c7ce9fcb886b1434d5d28"
)
ARCHIVE_TERMINAL_NATIVE_SCREEN_OPEN_BODY = bytes.fromhex(
    "67 01 03 80 09 01 25 74 97 80 07 08 24 26 0A 80 "
    "07 09 24 26 05 80 74 97 80 07 0A 24 26 03 80 "
    "07 0B 24 26 05 80 74 97 80 07 0C 24 26 0F 80 "
    "74 97 80 07 0D 24 26 05 80"
)
ARCHIVE_TERMINAL_NATIVE_SCREEN_CLOSE_LAUNCH_BODY = bytes.fromhex(
    "74 97 80 07 08 25 07 09 25 07 0A 25 07 0B 25 "
    "07 0C 25 07 0D 25"
)

CHECKIN_ALIASES = ("Aron Voss", "Noel Ardan", "Kiro Dalen")
LEGACY_ALIAS_CONFIRM_DIALOGUE = (
    "CONFIRM REGISTERED ALIAS\n"
    "<Opcode:01:FF>    Aron Voss\n"
    "    Noel Ardan\n"
    "    Kiro Dalen<Close>"
)
DOCTOR_CALL_DIALOGUES = tuple(
    (
        "CLINIC CALL\n"
        f"{alias}, please report\n"
        "to the intake physician.<Close>"
    )
    for alias in CHECKIN_ALIASES
)
DOCTOR_INSTRUCTION_DIALOGUES = tuple(
    (
        "Doctor\n"
        f'"{alias}? Your chart\n'
        "is ready. Follow me into\n"
        'the examination room."<Close>'
    )
    for alias in CHECKIN_ALIASES
)
CLINIC_DOOR_DENIAL_DIALOGUE = (
    "EXAMINATION ROOM\n"
    "Please wait for the doctor.\n"
    "Your registered alias will\n"
    "be called.<Close>"
)
CLINIC_BRIEFING_DIALOGUE = (
    "Doctor\n"
    '"Take a seat. We will begin\n'
    "with bloodwork, followed by\n"
    'a standard injection series."<New>'
    "Fei\n"
    '"Injections? What are they\n'
    'for?"<New>'
    "Doctor\n"
    '"Nutrient tracers, immune\n'
    "response, and nanomachine\n"
    "compatibility. You may feel\n"
    'some pressure."<Close>'
)
CLINIC_EXIT_INSISTENCE_DIALOGUE = (
    "The door is locked.<New>"
    "Doctor\n"
    '"We need to continue the\n'
    'procedure before you leave."<Close>'
)
CLINIC_FIRST_REFUSAL_DIALOGUE = (
    "Doctor\n"
    '"Roll up your sleeve. We are\n'
    'ready to draw the sample."<New>'
    "Fei\n"
    '"No. I will not take an\n'
    "injection until you tell me\n"
    'what is in it."<Close>'
)
CLINIC_SECURITY_CALL_DIALOGUE = (
    "Doctor\n"
    '"The contents are not open to\n'
    'discussion. Sit down."<New>'
    "Fei\n"
    '"Then my answer is no."<New>'
    "Doctor\n"
    '"Refusal is not permitted.\n'
    "Security, report to the\n"
    'examination room."<Close>'
)
CLINIC_SECURITY_ARRIVAL_DIALOGUE = (
    "Solaris Guard\n"
    '"Step away from the physician\n'
    'and submit to the procedure."<Close>'
)
CLINIC_DOCTOR_ESCAPE_DIALOGUE = (
    "Doctor\n"
    '"Stay back! This is beyond\n'
    'my authority!"<Close>'
)
CLINIC_ESCAPE_IN_PROGRESS_DIALOGUE = (
    "The doctor is fleeing through\n"
    "the doorway.<Close>"
)
CLINIC_SECURITY_KEYCARD_DIALOGUE = (
    "SECURITY KEYCARD ACQUIRED\n"
    "Access authorization:\n"
    "FREIGHT / SERVICE.<Close>"
)
SECURITY_KEYCARD_ACQUIRED_SOUND_ID = 0x37
SECURITY_KEYCARD_ACQUIRED_SOUND = b"\x74\x37\x80"

# The doctor is a new sprite actor in field 621.  V186 replaces local actor and
# sprite bank 6 with the exact physician bank used by field 352's office.  The
# only previous bank-6 user (e12) moves to the existing civilian bank 3; the
# palette-selecting receptionist remains safely on bank 7.
# The path follows the audited curved walkmesh from the east examination door
# to a waiting point beside the reception desk.  Fei is never scripted to move.
INTAKE_DOCTOR_GRAPHIC = 6
INTAKE_DOCTOR_ENTITY = 35
INTAKE_DOCTOR_SOURCE_BANK = 3
INTAKE_DOCTOR_TARGET_BANK = INTAKE_DOCTOR_GRAPHIC
INTAKE_REASSIGNED_CIVILIAN_ENTITY = 12
INTAKE_REASSIGNED_CIVILIAN_GRAPHIC = 3
INTAKE_REASSIGNED_CIVILIAN_INIT_PC = 0x01A6
INTAKE_REASSIGNED_CIVILIAN_OLD_INIT = bytes.fromhex("0B 06 80")
INTAKE_REASSIGNED_CIVILIAN_NEW_INIT = bytes.fromhex("0B 03 80")
INTAKE_DOCTOR_TARGET_MAPPING = (512, 256, 0, 0)
INTAKE_TARGET_ACTOR_COMPONENT_SHA256 = (
    "7f36a871e87f7a927f5ea32b7a614aa5b6a0472e211cda8ef223c4759854c7f5"
)
INTAKE_TARGET_SPRITE_COMPONENT_SHA256 = (
    "ec2471a10fcfb0b60c90693c471879a97199aab5beecb6e330b6fe68b03c9815"
)
INTAKE_SOURCE_PHYSICIAN_ACTOR_SHA256 = (
    "30636fcb252091e3c65c5fdc584f46fae31c66522d794570dc02b79e3a1c1559"
)
INTAKE_SOURCE_PHYSICIAN_SPRITE_SHA256 = (
    "7c321cbd684a6205a779d10f01f5b832a10aeadb9edf60fb494e11c67544215a"
)
INTAKE_INSTALLED_ACTOR_COMPONENT_SHA256 = (
    "d1f14379b3179d1baec2ebc239cea70309144d3f7b3c366044aa18dd09c27770"
)
INTAKE_INSTALLED_SPRITE_COMPONENT_SHA256 = (
    "f5b083c238c90ec8cca8b554a15e8f3b1b94bede0c4b4f0322a7808c89453a23"
)
INTAKE_CLINIC_DOOR_ENTITY = 23
INTAKE_CLINIC_DOOR_ACTION_PC = 0x0CEA
INTAKE_CLINIC_DOOR_ACTION = bytes.fromhex(
    "33 FE 54 31 20 00 F8 0C 26 01 80 01 ED 0C "
    "74 77 80 09 1F 24 98 26 82 00 80 5B"
)
INTAKE_CLINIC_DESTINATION = (550, 0)
INTAKE_DOCTOR_DOOR_HELPER_ENTITY = 31
INTAKE_DOCTOR_DOOR_OPEN_SCRIPT = 4
INTAKE_DOCTOR_DOOR_OPEN_PC = 0x0823
INTAKE_DOCTOR_DOOR_CLOSE_SCRIPT = 5
INTAKE_DOCTOR_DOOR_RETAIL_CLOSE_STOP_PC = 0x038F
INTAKE_DOCTOR_DOOR_SLIDE_FRAMES = 32
INTAKE_DOCTOR_DOOR_OPEN_OFFSET_Z = 64
INTAKE_DOCTOR_STAGING_POSITION = (1608, 840)
# V184 ended at (1080,1375), which runtime resolved onto sloped triangle 191
# at y=-20 and into the user's waiting party/desk cluster.  This point is on
# flat triangle 36 at y=0 and remains visibly beside reception without
# overlapping the captured leader position (1102,1412).
INTAKE_DOCTOR_WAITING_POSITION = (1200, 1400)
INTAKE_DOCTOR_WAITING_TRIANGLE = 36
INTAKE_DOCTOR_OUTBOUND_WAYPOINTS = (
    (1665, 840),
    (1720, 970),
    (1700, 1100),
    (1580, 1240),
    (1450, 1390),
    (1280, 1390),
    (1240, 1390),
    INTAKE_DOCTOR_WAITING_POSITION,
)
INTAKE_DOCTOR_RETURN_WAYPOINTS = (
    (1240, 1390),
    (1280, 1390),
    (1450, 1390),
    (1580, 1240),
    (1700, 1100),
    (1720, 970),
    (1665, 840),
    INTAKE_DOCTOR_STAGING_POSITION,
)
INTAKE_DOCTOR_WAYPOINT_MAX_STEPS = 180
# OP20 rewrites the current actor's low movement flags. Immediate 0x01 keeps
# the physician collision-ghosted while a scripted route crosses a still-solid
# doorway seal. Immediate 0x0C clears that ghost bit and restores the same
# 0x20/0x10 solid, immovable collision class used by ordinary waiting NPCs.
# Both actors retain rectangular, no-facing interaction mode, but OP18 0x10
# gives it 32-world-unit X/Z half-extents: the same axial separation as two
# ordinary radius-16 actors, rather than an oversized invisible 96-unit body.
DOCTOR_TRANSIT_COLLISION_FLAGS = b"\x20\x01\x80"
DOCTOR_STATIONARY_COLLISION_FLAGS = b"\x20\x0C\x80"
DOCTOR_RECTANGULAR_BOUNDING_VOLUME = b"\x18\x10\x10\x00\x00"
# These nine retained lobby actors each own the audited six-byte retail action
# ``D2 <dialogue> 00 9C 00``. V186 wraps them in a field-local dialogue mutex
# so the automatic physician call waits instead of opening a second window.
INTAKE_NATIVE_DIALOGUE_ACTIONS = {
    6: (0x0359, 2),
    7: (0x035F, 3),
    8: (0x0365, 4),
    9: (0x036B, 5),
    10: (0x0371, 6),
    11: (0x0377, 7),
    12: (0x037D, 8),
    14: (0x0383, 9),
    15: (0x0389, 10),
}
# Slot 1 on these same actors is retail ``WALK_RANDOM_DIRECTION``.  V188 gave
# all nine actors one X500..1250/Z1350..1680 OP17 rectangle.  Slot-1 runtime
# evidence later proved that rectangle extended through the true west/east
# walkmesh walls at X541/X1190: e9, e12, and e15 slid into the same east-wall
# vertex while e8 pressed against them, and west-side actors exhibited the
# same failure.  V198 retains native ambient motion but gives every actor a
# disjoint clockwise microzone.  Every zone plus a conservative 24-unit halo
# is contained by the waiting-room walkmesh, and the zones remain farther apart
# than two actors' combined 16-unit collision radii.
INTAKE_WANDERING_SURVIVOR_SPECS = {
    # entity: (retail init PC, graphic bank, retail position, bounded position)
    6: (0x0158, 0, (617, 1471), (617, 1450)),
    7: (0x0165, 1, (1134, 1616), (1122, 1600)),
    8: (0x0172, 2, (1022, 1634), (1020, 1650)),
    9: (0x017F, 3, (726, 1799), (650, 1635)),
    10: (0x018C, 4, (882, 1732), (1020, 1550)),
    11: (0x0199, 5, (1127, 1414), (1090, 1450)),
    # V186 reassigns this former bank-6 user to the existing bank 3.
    12: (0x01A6, 3, (843, 1486), (760, 1460)),
    14: (0x01C4, 1, (746, 1661), (760, 1580)),
    15: (0x01D1, 2, (574, 1637), (595, 1545)),
}
INTAKE_SURVIVOR_MOVEMENT_ZONES = {
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
INTAKE_SURVIVOR_COLLISION_RADIUS = 16
INTAKE_SURVIVOR_WALKMESH_HALO = 24
INTAKE_SURVIVOR_MIN_ZONE_SEPARATION = 50
INTAKE_SURVIVOR_CENTER_AISLE = (824, 946)
INTAKE_SURVIVOR_MIN_DOCTOR_CLEARANCE = 80
INTAKE_ARCHIVE_DOOR_POSITION = (867, 1832)
INTAKE_SURVIVOR_DOOR_CLEARANCE = (
    INTAKE_ARCHIVE_DOOR_POSITION[1]
    - max(
        point[1]
        for zone in INTAKE_SURVIVOR_MOVEMENT_ZONES.values()
        for point in zone
    )
)

# Logical field 550 keeps its canonical target slots and reciprocal topology,
# but now clones the compact Disc 1 field-352 Ethos infirmary instead of the
# former scanner.  The source is a self-contained room/graphics pair.
CLINIC_SOURCE_SCENE = 352
CLINIC_SOURCE_BUNDLE_ID = 1315
CLINIC_SOURCE_GRAPHICS_ID = 1316
CLINIC_SOURCE_BUNDLE_SIZE = 83_720
CLINIC_SOURCE_BUNDLE_SHA256 = (
    "99fe2c065c60176f5199ac672f7cf513f1f0a81df4af5dfe31020e0610112074"
)
CLINIC_SOURCE_GRAPHICS_SIZE = 131_072
CLINIC_SOURCE_GRAPHICS_SHA256 = (
    "d151035c6523091d22255ebf587e463748a74d1db521cce852a8d85f6e197d41"
)
CLINIC_SOURCE_WALKMESH_SIZE = 1_948
CLINIC_SOURCE_WALKMESH_SHA256 = (
    "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"
)
CLINIC_SOURCE_SCRIPT_SIZE = 3_024
CLINIC_SOURCE_SCRIPT_SHA256 = (
    "37fdf199d4839fd0b9d6ca23067b4b4fccabf9b173fcfa367761f369075520e6"
)
CLINIC_SOURCE_HEADER_SIZE = 928
CLINIC_SOURCE_HEADER_SHA256 = (
    "01337fb6045d01fc6072e776dee6e65ef38bb110ccd2af9ae90cc39a45c8cb8b"
)
CLINIC_SOURCE_DIALOGUE_SIZE = 5_177
CLINIC_SOURCE_DIALOGUE_SHA256 = (
    "6d9ae403fabe60061966a43a50c5d970317a2f0997bf5554e0dab588866ce518"
)
CLINIC_DISABLED_ENCOUNTER_SHA256 = (
    "48018da2ff103e2890c170b83d4fbb677011e085587dfe1bc4fbcea3f246ce12"
)
CLINIC_ENTRY_PARAMETER = 0
CLINIC_ENTRY_SOURCE = bytes.fromhex("00 00 C8 00 00 FF FF")
CLINIC_ENTRY_PLAYABLE = bytes.fromhex("00 00 C8 00 00 04 04")
CLINIC_ENTRY_TRIANGLE = 16
CLINIC_PARTY_ENTITIES = (1, 2, 3)
CLINIC_PARTY_INIT_PCS = (0x0157, 0x016A, 0x0191)
CLINIC_DOCTOR_ENTITY = 16
CLINIC_DOCTOR_GRAPHIC = 3
CLINIC_DOCTOR_POSITION = (76, -48)
# The side computer bank is a baked wall prop rather than an ATEL actor.  Its
# static node-27/model-3 world AABB is X[11,164], Z[-220,-167] after the native
# 0x0400 Y rotation; node-29/model-5 is instead the screen assembly behind the
# examination bed.  Entities 4-6 are field 352's fully retired story actors,
# so they safely carry three hidden, collision-ghosted X targets along model
# 3's room-facing Z=-167 plane.  Their overlapping 18-unit effective X reaches
# span every accessible point from x=70 through x=164 without requiring one
# unsafe diagonal target.  V214 enables the engine's native narrow facing cone
# on all three: the user's saved bed-facing 0x0800 heading is rejected over the
# entire frontage, while the leftward 0x0400 heading points at at least one
# carrier.  Their compact Z reaches remain disjoint from the physician's
# interaction volume, so these lower-numbered carriers cannot steal Cross from
# doctor dialogue.  All three initializers and their shared action live inside
# the retired physician's original 0x054B..0x0648 bytecode cavity; keeping both
# ATEL and dialogue components exactly the V212 lengths lets a resident
# field-550 savestate be migrated without relocating the field heap.
CLINIC_RECORD_TERMINAL_ENTITY = 4
CLINIC_RECORD_TERMINAL_ENTITIES = (4, 5, 6)
CLINIC_RECORD_TERMINAL_STATIC_NODE = 27
CLINIC_RECORD_TERMINAL_STATIC_MODEL = 3
CLINIC_RECORD_TERMINALS = (
    Console(
        80,
        -167,
        31,
        0,
        "",
        interaction_half_width=0x01,
        interaction_half_depth=0x0F,
        requires_facing=True,
    ),
    Console(
        116,
        -167,
        6,
        0,
        "",
        interaction_half_width=0x01,
        interaction_half_depth=0x0F,
        requires_facing=True,
    ),
    Console(
        152,
        -167,
        6,
        0,
        "",
        interaction_half_width=0x01,
        interaction_half_depth=0x0F,
        requires_facing=True,
    ),
)
CLINIC_RECORD_TERMINAL = CLINIC_RECORD_TERMINALS[0]
CLINIC_RECORD_TERMINAL_OPERATOR_TRIANGLES = (31, 30, 6, 7)
CLINIC_RECORD_TERMINAL_INIT_PC = 0x054B
CLINIC_RECORD_TERMINAL_ACTION_PC = 0x0568
CLINIC_RECORD_TERMINAL_AUX_INIT_PCS = (0x05F1, 0x060E)
CLINIC_RECORD_TERMINAL_PAYLOAD_END_PC = 0x062B
CLINIC_RECORD_TERMINAL_CAVITY_END_PC = 0x0649
CLINIC_RECORD_TERMINAL_CAVITY_SHA256 = (
    "83078ed5687ea73ec5532edf4b7affeb5ed1efe211ce1d83b3b394848982b5bb"
)
CLINIC_RECORD_ALIAS_DIALOGUE_IDS = (2, 10, 33)
CLINIC_RECORD_MISSING_DIALOGUE_ID = 45
CLINIC_RECORD_DIALOGUE_PADDING_ID = 50
CLINIC_BRIEFING_DIALOGUE_ID = 53
CLINIC_EXIT_INSISTENCE_DIALOGUE_ID = 54
CLINIC_FIRST_REFUSAL_DIALOGUE_ID = 55
CLINIC_SECURITY_CALL_DIALOGUE_ID = 56
CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID = 57
CLINIC_DOCTOR_ESCAPE_DIALOGUE_ID = 58
CLINIC_ESCAPE_IN_PROGRESS_DIALOGUE_ID = 59
CLINIC_SECURITY_KEYCARD_DIALOGUE_ID = 60
CLINIC_DOCTOR_ESCAPE_APPROACH_WAYPOINTS = (
    (84, -9),
    (112, 19),
    (146, 87),
    (141, 167),
    (84, 178),
    (0, 200),
)
CLINIC_DOCTOR_ESCAPE_THRESHOLD_WAYPOINTS = (
    (-1, 237),
    (8, 261),
    (1, 300),
)
CLINIC_DOCTOR_THRESHOLD_WAYPOINT_MAX_STEPS = 16
CLINIC_DOCTOR_ESCAPE_WAYPOINTS = (
    *CLINIC_DOCTOR_ESCAPE_APPROACH_WAYPOINTS,
    *CLINIC_DOCTOR_ESCAPE_THRESHOLD_WAYPOINTS,
)
CLINIC_DOCTOR_ESCAPE_TRIANGLE_ROUTE = (8, 13, 12, 11, 9, 15, 16, 3, 34, 34)
CLINIC_DOCTOR_ESCAPE_TRIANGLES = (34,)
CLINIC_EXIT_ENTITY = 17
CLINIC_SHARED_STOP_PC = 0x068C
CLINIC_EXIT_INIT_PC = 0x068D
CLINIC_EXIT_ACTION_PC = 0x06A7
CLINIC_EXIT_HELPER_ENTITY = 18
CLINIC_EXIT_HELPER_OPEN_SCRIPT = 4
CLINIC_EXIT_HELPER_CLOSE_SCRIPT = 5
CLINIC_EXIT_HELPER_PC = 0x066E
CLINIC_EXIT_HELPER_BODY = bytes.fromhex(
    "35 0E 04 00 00 40 02 0E 04 1E 00 43 8B 06 FE 1B "
    "FF FF 00 00 26 00 80 3C 0E 04 01 74 06 00"
)
CLINIC_SOURCE_RETURN_FIELD = 353
CLINIC_SOURCE_RETURN_PARAMETER = 1
CLINIC_RETURN_FIELD = 621
CLINIC_RETURN_PARAMETER = 3
CLINIC_TARGET_IDENTITY = replace(
    base.DONOR_BY_SCENE[550],
    bundle_size=CLINIC_SOURCE_BUNDLE_SIZE,
    bundle_sha256=CLINIC_SOURCE_BUNDLE_SHA256,
    graphics_size=CLINIC_SOURCE_GRAPHICS_SIZE,
    graphics_sha256=CLINIC_SOURCE_GRAPHICS_SHA256,
    script_size=CLINIC_SOURCE_SCRIPT_SIZE,
    script_sha256=CLINIC_SOURCE_SCRIPT_SHA256,
    header_size=CLINIC_SOURCE_HEADER_SIZE,
    header_sha256=CLINIC_SOURCE_HEADER_SHA256,
)
CLINIC_EXIT_PLAYER_SCRIPT = 4
CLINIC_EXIT_POSITION = (0, 250)
CLINIC_EXIT_SOURCE_ACTION_PC = 0x065C
CLINIC_EXIT_SOURCE_DESTINATION = (353, 1)
CLINIC_EXIT_DESTINATION = (621, 3)
CLINIC_EXIT_SEAL_ENTITY = 19

# The visible response team uses the exact field-538 Solaris Imperial escort
# and field-510 Security Cube overworld banks.  Field 352's retired banks 1/2
# already own the donors' native 896/960 texture slots, so the physician in
# bank 3 and the room graphics remain untouched.  Four ghost actors are added
# after the generated exit seal and enter through the retained leaf before the
# matching two-guard/two-cube fixed battle.
CLINIC_SECURITY_GUARD_SOURCE_SCENE = 538
CLINIC_SECURITY_GUARD_SOURCE_BUNDLE_ID = 1687
CLINIC_SECURITY_GUARD_SOURCE_BUNDLE_SIZE = 88_560
CLINIC_SECURITY_GUARD_SOURCE_BUNDLE_SHA256 = (
    "53eb064ddd5f0bca6f49fc7d6da3bd980ae808bfe81bda7eb404eed413f6edce"
)
CLINIC_SECURITY_GUARD_SOURCE_BANK = 2
CLINIC_SECURITY_GUARD_ACTOR_SIZE = 3_372
CLINIC_SECURITY_GUARD_ACTOR_SHA256 = (
    "13096e659258ec1ab95fc72ed47ed24240017ffde07667af453e52eb815892f7"
)
CLINIC_SECURITY_GUARD_SPRITE_SIZE = 20_492
CLINIC_SECURITY_GUARD_SPRITE_SHA256 = (
    "27ac6b2a78f1dbd5d40cd1f7be31a6939e26fbe394532df5dd1eba6ee7e771a8"
)
CLINIC_SECURITY_GUARD_MAPPING = (960, 0, 0, 0)
CLINIC_SECURITY_GUARD_PALETTE = 3
CLINIC_SECURITY_GUARD_PALETTE_SHA256 = (
    "293ed6964a2895fcdad20e6f3354ea5f101610426b3c707eae4d1d25bb0170c2"
)
CLINIC_SECURITY_CUBE_SOURCE_SCENE = 510
CLINIC_SECURITY_CUBE_SOURCE_BUNDLE_ID = 1631
CLINIC_SECURITY_CUBE_SOURCE_BUNDLE_SIZE = 66_572
CLINIC_SECURITY_CUBE_SOURCE_BUNDLE_SHA256 = (
    "5e3308c464ecba542310c35cca0aab7879b8bb7f40cecdc4726bd6bd7f886045"
)
CLINIC_SECURITY_CUBE_SOURCE_BANK = 0
CLINIC_SECURITY_CUBE_ACTOR_SIZE = 4_092
CLINIC_SECURITY_CUBE_ACTOR_SHA256 = (
    "bb378d61e8b050663f9fda3e3e89a82418bbff93c0f583b17639e944f2441557"
)
CLINIC_SECURITY_CUBE_SPRITE_SIZE = 3_084
CLINIC_SECURITY_CUBE_SPRITE_SHA256 = (
    "a45b4e5617859a4b3983bd8439f3c389e4ea38fef158d39b451c301688cc135e"
)
CLINIC_SECURITY_CUBE_SOURCE_MAPPING = (832, 0, 0, 0)
CLINIC_SECURITY_CUBE_MAPPING = (896, 0, 0, 0)
CLINIC_SECURITY_GUARD_TARGET_BANK = 2
CLINIC_SECURITY_CUBE_TARGET_BANK = 1
CLINIC_SECURITY_TARGET_ACTOR_COMPONENT_SHA256 = (
    "080399f5e7a2c6a129f46ca7dd21c40ad6beb5ed3c14840c0cdca6a4b749514a"
)
CLINIC_SECURITY_TARGET_SPRITE_COMPONENT_SHA256 = (
    "891c7eba778f1dba2c01e3a7b6895200f7901103a02e8e6e1f029229e61973f9"
)
CLINIC_SECURITY_INSTALLED_ACTOR_COMPONENT_SIZE = 21_324
CLINIC_SECURITY_INSTALLED_ACTOR_COMPONENT_SHA256 = (
    "d8b2305aff2918421d446b83a5954d4acd5b3a881bab81b54c2ecef467ea93aa"
)
CLINIC_SECURITY_INSTALLED_SPRITE_COMPONENT_SIZE = 83_140
CLINIC_SECURITY_INSTALLED_SPRITE_COMPONENT_SHA256 = (
    "ee18e18d8e09262abcfa832d5be024a2e6c9efe19267565ae75a093f84836771"
)
CLINIC_SECURITY_ENTITIES = (20, 21, 22, 23)
CLINIC_SECURITY_GUARD_ENTITIES = (20, 21)
CLINIC_SECURITY_CUBE_ENTITIES = (22, 23)
CLINIC_SECURITY_ENTRY_SCRIPT = 4
CLINIC_SECURITY_HIDE_SCRIPT = 5
CLINIC_SECURITY_STAGING_POSITION = (1, 300)
CLINIC_SECURITY_REVEAL_POSITION = (8, 261)
CLINIC_SECURITY_FIRST_INTERIOR_POSITION = (-1, 237)
CLINIC_SECURITY_OVERRIDE_CLEAR_POSITION = (0, 200)
CLINIC_SECURITY_DOOR_PLANE_Z = 250
CLINIC_SECURITY_WAYPOINT_MAX_STEPS = 16
CLINIC_ACTOR_WALK_STEP_UNITS = 8
CLINIC_ACTOR_WALK_SAFETY_STEPS = 8
CLINIC_DOORWAY_WALKMESH_OVERRIDE_FLAGS = 0x0038
CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET = bytes.fromhex("F8 02 38 00")
CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR = bytes.fromhex("F8 06 38 00")
CLINIC_WALKMESH_LAYER_COUNT = 2
CLINIC_WALKMESH_LAYER0_TRIANGLE_BYTES = 0x0230
CLINIC_WALKMESH_LAYER0_TRIANGLE_OFFSET = 0x0028
CLINIC_WALKMESH_MATERIAL_OFFSET = 0x039C
CLINIC_WALKMESH_FORBIDDEN_MATERIAL_FLAG = 0x00800000
CLINIC_WALKMESH_EXTERIOR_TRIANGLES = (34, 35)
CLINIC_WALKMESH_EXTERIOR_MATERIAL = 0
CLINIC_WALKMESH_INTERIOR_MATERIAL = 1
CLINIC_SECURITY_ROUTES = {
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
}
CLINIC_SECURITY_ENTRY_DELAYS = {20: 0, 21: 6, 22: 12, 23: 18}
CLINIC_SECURITY_FINAL_TRIANGLES = {20: 14, 21: 15, 22: 18, 23: 16}
CLINIC_SECURITY_TRIANGLE_ROUTES = {
    20: (34, 34, 3, 16, 18, 17, 14),
    21: (34, 34, 3, 16, 16, 15, 15),
    22: (34, 34, 3, 16, 18, 18),
    23: (34, 34, 3, 16, 16, 16),
}

# Field 551's fourth weighted formation is an authentic Solaris security team:
# two Solaris Guards and two Security Cubes using resource set 0x21.  Its dark
# arena 0x3B is replaced with field 551 configuration 15's retail-proven arena
# 0x30: a bright silver-white technological room which already pairs resource
# set 0x21, Security Cubes, and the no-Escape flag.  The resulting 32-byte
# record occupies disabled clinic slot 15 and cannot be escaped.
CLINIC_SECURITY_SOURCE_SCENE = 551
CLINIC_SECURITY_SOURCE_BUNDLE_ID = 1713
CLINIC_SECURITY_SOURCE_BUNDLE_SIZE = 73_244
CLINIC_SECURITY_SOURCE_BUNDLE_SHA256 = (
    "b43a4deef95f64278374403fc6a877b9b8e9c12cd61fb2a0e6d382825d293f88"
)
CLINIC_SECURITY_SOURCE_ENCOUNTER_SHA256 = (
    "a7dacd9fc86d36309e2d4d1a805321404457d5430cf4107bca2c62081b68a6f8"
)
CLINIC_SECURITY_SOURCE_CONFIGURATION = 4
CLINIC_SECURITY_BRIGHT_ARENA_CONFIGURATION = 15
CLINIC_SECURITY_CONFIGURATION = 15
CLINIC_SECURITY_ARENA = 0x30
CLINIC_SECURITY_SOURCE_FORMATION = bytes.fromhex(
    "21 40 3B 00 00 00 00 00 02 02 01 01 FF FF FF FF "
    "00 00 00 00 FF FF FF FF 00 00 00 00 FF FF FF FF"
)
CLINIC_SECURITY_BRIGHT_ARENA_PROOF_FORMATION = bytes.fromhex(
    "21 C0 30 00 00 00 00 00 02 02 FF FF FF FF FF FF "
    "00 00 FF FF FF FF FF FF 00 00 FF FF FF FF FF FF"
)
CLINIC_SECURITY_FORMATION = bytes.fromhex(
    "21 C0 30 00 00 00 00 00 02 02 01 01 FF FF FF FF "
    "00 00 00 00 FF FF FF FF 00 00 00 00 FF FF FF FF"
)
CLINIC_RETAIL_SLOT15_FORMATION = bytes.fromhex(
    "43 C0 15 00 00 00 00 00 01 FF FF FF FF FF FF FF "
    "00 FF FF FF FF FF FF FF 00 FF FF FF FF FF FF FF"
)
CLINIC_SECURITY_ENCOUNTER_SHA256 = (
    "3f27bb2a6ea88aa7ad90efc811e887ec69716121128f01acce2b8b178d907d49"
)
# The fixed formation references these already-normalized Disc 2 resources in
# place.  Freeze all four archive identities so a future base-disc change
# cannot silently turn the clinic encounter into a different enemy set or
# arena.  Canonical IDs are Xenoiso's file numbers; their physical FAT entries
# are exactly ``canonical_id - 5``.
CLINIC_SECURITY_NORMALIZED_CD2_RESOURCES = {
    2684: (
        "resource_set_0x21_stats_scripts_and_names",
        4_533,
        "c7c46e83cf2383de1809f9d6d6faa90617906f0fa56acfea687d6adae248a862",
    ),
    2685: (
        "resource_set_0x21_models",
        163_896,
        "aa52030cab6b852ce67ae53213f1c70f060d5891e0d08448386f480b2ce31b3f",
    ),
    2871: (
        "arena_0x30_geometry_and_textures",
        200_064,
        "4fc4ab2b66e8b701d89ddb7e9b2806d74d1320aa30524e2ff38cbe2e451e2d52",
    ),
    2872: (
        "arena_0x30_layout",
        1_556,
        "06099720b9683a2e18b0565c62aed99723a0707ba1ab3e0e08a540bd2dcd7ede",
    ),
}

RECEPTIONIST_PRECHECK_DIALOGUE = (
    "Receptionist\n"
    '"Before intake can begin,\n'
    "register at the records\n"
    "terminal in the room directly\n"
    'behind you."<Close>'
)
RECEPTIONIST_POSTCHECK_DIALOGUE = (
    "Receptionist\n"
    '"I see you have signed in.\n'
    "Please wait here until your\n"
    'name is called."<Close>'
)
CHECKIN_ALIAS_MENU_DIALOGUE = (
    "REGISTER UNDER WHICH NAME?\n"
    "<Opcode:01:FF>    Aron Voss\n"
    "    Noel Ardan\n"
    "    Kiro Dalen\n"
    "    Cancel<Close>"
)
CHECKIN_REPEAT_MENU_DIALOGUE = (
    "VIEW WHICH PATIENT RECORD?\n"
    "<Opcode:01:FF>    Fei\n"
    "    Elly\n"
    "    Citan\n"
    "    Exit<Close>"
)
CHECKIN_CANCELLED_DIALOGUE = (
    "REGISTRATION CANCELLED\n"
    "No intake record was created.<Close>"
)

# Height is the fixed character-profile measurement.  Weight is deliberately
# not stored here: Xenogears has a mutable Status-weight system, so the action
# reads each live character record with retail EX69, converts it with the
# game's x2.20 Status-screen convention, and renders decimal pounds.  Pulse,
# pressure, temperature, respiration, and clinical observations are authored
# for this terminal.
PATIENT_PROFILE_MEASUREMENTS = {
    "Fei": ("FEI FONG WONG", 18, "Male", 177),
    "Elly": ("ELHAYM VAN HOUTEN", 18, "Female", 164),
    "Citan": ("CITAN UZUKI", 29, "Male", 182),
}
PATIENT_RETAIL_INITIAL_WEIGHT_HUNDREDTHS_LB = {
    "Fei": 16_720,
    "Elly": 9_240,
    "Citan": 15_840,
}
PATIENT_WEIGHT_WHOLE_DIALOG_VARIABLE = 0x0016
PATIENT_WEIGHT_FRACTION_DIALOG_VARIABLE = 0x0018
PATIENT_WEIGHT_DIALOG_VARIABLES = (
    PATIENT_WEIGHT_WHOLE_DIALOG_VARIABLE,
    PATIENT_WEIGHT_FRACTION_DIALOG_VARIABLE,
)
POUNDS_TENTHS_PER_NATIVE_WHOLE = 22
POUNDS_DECIMAL_BASE = 10
PATIENT_CHARACTER_IDS = {"Fei": 0, "Elly": 1, "Citan": 2}
PATIENT_AUTHORED_VITALS = {
    "Fei": (64, "118/72", "36.8", 14, "Neural activity: elevated."),
    "Elly": (70, "108/68", "36.7", 15, "Ether response: elevated."),
    "Citan": (56, "116/70", "36.6", 12, "Condition: stable."),
}


def _patient_vitals_dialogue(patient: str) -> str:
    display_name, age, sex, height_cm = PATIENT_PROFILE_MEASUREMENTS[
        patient
    ]
    pulse, blood_pressure, temperature, respiration, observation = (
        PATIENT_AUTHORED_VITALS[patient]
    )
    return (
        f"{display_name}\n"
        f"Age {age} / {sex}\n"
        f"Height {height_cm} cm\n"
        "Weight <Opcode:0A:00>.<Opcode:0A:01>0 lbs<New>"
        f"Pulse {pulse} bpm / BP {blood_pressure}\n"
        f"Temp {temperature} C\n"
        f"Respiration {respiration}/min\n"
        f"{observation}<Close>"
    )


PATIENT_VITALS_DIALOGUES = {
    patient: _patient_vitals_dialogue(patient)
    for patient in PATIENT_PROFILE_MEASUREMENTS
}
CHECKIN_ALIAS_RESULT_DIALOGUES = tuple(
    (
        "REGISTRATION ACCEPTED\n"
        f"Alias: {alias}\n"
        "Age 18 / Male\n"
        "Height 177 cm\n"
        "Weight <Opcode:0A:00>.<Opcode:0A:01>0 lbs<New>"
        "Pulse 64 bpm / BP 118/72\n"
        "Temp 36.8 C\n"
        "Respiration 14/min\n"
        "Neural activity: elevated."
        "<New>No acute trauma detected.\n"
        "Return to reception.<Close>"
    )
    for alias in CHECKIN_ALIASES
)


def _clinic_record_dialogue(alias: str) -> str:
    """Render the office reader without exposing Fei's real identity."""

    return (
        "SOLARIS MEDICAL RECORD\n"
        f"Registered: {alias}\n"
        "Weight <Opcode:0A:00>.<Opcode:0A:01>0 lbs\n"
        "Pulse 64 bpm / BP 118/72<New>"
        "Temp 36.8 C / Resp. 14/min\n"
        "Neural activity: elevated.\n"
        "BIOLOGICAL COMPATIBILITY\n"
        "Index: 100% / PERFECT FIT<Close>"
    )


CLINIC_RECORD_DIALOGUES = tuple(
    _clinic_record_dialogue(alias) for alias in CHECKIN_ALIASES
)
CLINIC_RECORD_MISSING_DIALOGUE = (
    "NO ACTIVE PATIENT RECORD\n"
    "Complete Intake registration\n"
    "before requesting analysis.<Close>"
)


# Dialogue authored by the Surface reconstruction is deliberately isolated
# from retained retail text.  Xenogears does not wrap prose at word
# boundaries: the renderer advances encoded glyphs until the declared window
# width is exhausted and then continues on the next row.  A width-58 window
# therefore holds 59 internal font units, or only 29 ordinary US glyphs.  The
# v178 text exceeded that grid in 45 of these originally 66 blocks and could split a word
# between any two letters (for example ``t`` / ``o`` in "to").
CAMPAIGN_AUTHORED_DIALOGUE_IDS = {
    565: tuple(range(10, 17)),
    588: (10, 11),
    589: (5,),
    620: tuple(range(4, 25)),
    621: tuple(range(2, 11)) + (INTAKE_FREIGHT_AUTHORIZATION_LOCK_DIALOGUE_ID,),
    622: tuple(range(22, 43)),
    623: (1,),
    624: tuple(range(1, 6)),
    625: tuple(range(3, 5)),
    626: tuple(range(1, 6)),
}
CAMPAIGN_V178_OVERFLOW_LINES_BY_SCENE = {
    565: 8,
    588: 0,
    589: 0,
    620: 29,
    621: 16,
    622: 11,
    623: 1,
    624: 7,
    625: 7,
    626: 8,
}
CAMPAIGN_V178_OVERFLOW_LINE_COUNT = sum(
    CAMPAIGN_V178_OVERFLOW_LINES_BY_SCENE.values()
)

# Frozen dialogue inputs immediately before the layout pass.  Guarding the
# complete component makes a block-ID shift or an upstream wording change fail
# closed instead of silently rewriting the wrong speaker.
CAMPAIGN_PRE_LAYOUT_DIALOGUE_IDENTITIES = {
    565: (1230, "0d51b17973b9fb33cac3d0f8c11d7081d9ab386cd0d76329b07718e1be50e93f"),
    588: (521, "19ae6d86507799f79f6d888f0f79616942ae23e644080b23df7477abe3928ae2"),
    589: (257, "9779420312d76a566ee09878bbb47381ddd8ab723d9b4c8880415155cb3166e9"),
    620: (2415, "56cd8c15f8347b998649ee7bedb43820b7492f571590a1e90baf21c5b95c13d5"),
    621: (2217, "1e72c8ba9276750f4a8ca99f1f5802a33d19a21ba06ebc668636ca6f479a2486"),
    622: (4982, "7ff34606d5313bba3eae60ce578cb6fbf7e85b76fb484eb228794908de8b7f85"),
    623: (156, "b371f3d019f4cebb6fd494fa3f81c15e8568adad6f7a1539ef7bd8a1698ab43a"),
    624: (594, "2c9605b63a39b1e288cda1eacb18299393cde223e0f208a554dfe29c24806b06"),
    625: (732, "4dc7b20b2ddc99c89de3d6348ca15ab7bd4e933e0353e939675009f7b02cbb4a"),
    626: (561, "ad35dac80d511a9b335d9974b482cd940ead7a1a16dfb256a99d44400fb1c96b"),
}

# Exact, hand-reviewed word-boundary repairs for every v178 overflow.  Explicit
# <New> tokens paginate prose that needs more rows than the original window.
# Field 621 block 7 is the intake boy (entity 11) and intentionally contains
# the user's exact replacement line.
CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS = {
    565: {
        10: "AUXILIARY ROUTE SEALED\nNo authorization signal is\npresent.<Close>",
        11: "QUARANTINE CONSENSUS REQUIRED\nOutbound sorting is still\nlocked.<Close>",
        12: (
            "PRODUCTION BULKHEAD LOCKED\nRequired: keycard,\n"
            "quarantine consensus,\nresonance authorization,"
            "<New>and bio-interface cutoff.<Close>"
        ),
        13: (
            "QUARANTINE AIRLOCK SEALED\nA quarantine keycard is\n"
            "required for entry.<Close>"
        ),
        14: (
            "SERVICE PASSAGE LOCKED\nA security keycard is\n"
            "required.<Close>"
        ),
        15: (
            "FREIGHT SERVICE NETWORK\nThree production\n"
            "authorizations remain:<New>quarantine consensus,\n"
            "organic resonance, and\nbio-interface cutoff.<Close>"
        ),
    },
    588: {},
    589: {},
    620: {
        4: (
            "SURFACE QUARANTINE //\nBIOLOGICAL RELAYS\nRestore the three\n"
            "physiological markers.<New>Caste clearance is\n"
            "administrative data.<Close>"
        ),
        7: (
            "POD C // NANOMACHINES\nSystemic contamination\nconfirmed.\n"
            "Relay toggled.<Close>"
        ),
        9: (
            "DIAGNOSTIC ROUTE DENIED\nThree biological relays are\n"
            "required.\nExclude the caste index.<Close>"
        ),
        12: (
            "It hurts less when I keep\nmoving. Please... do not let\n"
            "the scanners decide I am no\nlonger human.<Close>"
        ),
        13: (
            "Word spread that flesh from\nthe unafflicted could quiet\n"
            "the pain. That desperate\nrumor led many of us here.<Close>"
        ),
        14: (
            "Some of us still remember our\nnames. The system records\n"
            "only mutation stages.<Close>"
        ),
        15: (
            "Those rings are not a cure.\nThey measure what is\n"
            "happening, then send us\ndeeper into the plant.<Close>"
        ),
        16: (
            "Pod A still detects an\nordinary human genome beneath\n"
            "the changes. That should\ncount for something.<Close>"
        ),
        17: (
            "The limiter is gone. The\nmachine calls that failure.\n"
            "I call it the truth finally\nsurfacing.<Close>"
        ),
        19: (
            "Solaris divided people by\ncaste. Pain does not\n"
            "recognize those categories.<Close>"
        ),
        20: (
            "Choose the biological\nreadings: genome, limiter,\n"
            "nanomachines.\nLeave the caste index out.<Close>"
        ),
        21: (
            "The service route opens only\nwhen three relays agree on\n"
            "what remains human.<Close>"
        ),
        22: (
            "I heard machinery beyond the\neast door. Whatever it is\n"
            "processing, it has not\nstopped.<Close>"
        ),
        23: (
            "If you reach the deeper\nchambers, shut this place\n"
            "down. Do not let it turn\nanyone else into material.<Close>"
        ),
    },
    621: {
        **INTAKE_WAITING_AREA_HOPEFUL_DIALOGUES,
        INTAKE_BOY_DIALOGUE_ID: INTAKE_BOY_DIALOGUE,
    },
    622: {
        22: (
            "Word spread that this place\ncould arrest the mutations.\n"
            "I wanted to believe it.<Close>"
        ),
        34: (
            "Meld is made from people.\nI saw their eyes before\n"
            "their shapes were forced\ntogether.<Close>"
        ),
        39: (
            "The barrier ruptures.\nThe Sufal Mass rises from\n"
            "people consumed by the\ngeneration line.<New>"
            "Their remaining voices ask\nfor release.<New>"
            "Elly\n\"We will not leave them\n"
            "trapped inside this machine.\"<New>Fei\n"
            "\"Then we end it here.\"<Close>"
        ),
        40: (
            "The generation cycle stops.\nThis Ignas node is silent.\n"
            "Other Surface systems\nremain.<New>"
            "Elly\n\"The voices are quiet now.\"<New>"
            "Fei\n\"We stopped this node.\n"
            "We keep going until none\nremain.\"<New>Citan\n"
            "\"Containment is stable.\nThe emergency return is\n"
            "online.\"<Close>"
        ),
        41: (
            "The Sufal Mass is gone.\nEmergency return and save\n"
            "controls remain online.<Close>"
        ),
        42: (
            "EMERGENCY RETURN SEALED\nThe generation hall remains\n"
            "active.<Close>"
        ),
    },
    623: {
        1: "EMERGENCY SERVICE LATCH\nSealed from the generation\nside.<Close>",
    },
    624: {
        1: (
            "SORTING FEED A // LIVING\nTISSUE\nDiversion: stasis assay.\n"
            "Production feed isolated.<Close>"
        ),
        2: (
            "SORTING FEED B // NANOMACHINE\nMEDIUM\n"
            "Diversion: reclamation drain.\nProduction feed isolated.<Close>"
        ),
        3: (
            "SORTING FEED C // UNSTABLE\nMELD\nDiversion: containment\n"
            "return.<New>Production feed isolated.<Close>"
        ),
        4: (
            "MOLECULAR SORTER INTERLOCK\nDivert all three\n"
            "living-material feeds before\nentering the M-Project core.<Close>"
        ),
        5: (
            "MOLECULAR DIVERSION COMPLETE\nAll three living-material\n"
            "feeds are isolated from\nproduction.<Close>"
        ),
    },
    625: {
        3: (
            "Many faces move behind the\ncontainment glass. Meld is\n"
            "not one creature, but people\nforced together.<New>"
            "Their eyes ask for the pain\nto end.<New>Elly\n"
            "\"I can hear them. They know\nwe are here.\"<New>Fei\n"
            "\"Then we stop the generation\nline.\"<New>Citan\n"
            "\"Keep containment stable\nuntil the node is shut down.\"<Close>"
        ),
        4: (
            "GENERATION ROUTE DENIED\nThe voices within Meld\n"
            "have not been heard.<Close>"
        ),
    },
    626: {
        1: (
            "M-PROJECT RING A //\nFUSION LATTICE\nPower discharged."
            "<New>The reconstruction feed is\ninterrupted.<Close>"
        ),
        2: (
            "M-PROJECT RING B //\nPATTERN ALIGNMENT\nTemplate uncoupled."
            "<New>No weapon-form can be\nimposed.<Close>"
        ),
        3: (
            "M-PROJECT RING C //\nCONTAINMENT\nContainment remains active."
            "<New>The people inside are not\nreleased into the line.<Close>"
        ),
        4: (
            "M-PROJECT CORE INTERLOCK\nDischarge fusion, uncouple\n"
            "the pattern, and retain\ncontainment.<Close>"
        ),
        5: (
            "M-PROJECT SAFE STATE RECORDED\nFusion and pattern are\n"
            "offline. Containment\nremains active.<Close>"
        ),
    },
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _u16(value: int) -> bytes:
    if not 0 <= value <= 0xFFFF:
        raise SurfaceCampaignBuildError(f"u16 value is outside range: {value}")
    return struct.pack("<H", value)


def _s16(value: int) -> bytes:
    return struct.pack("<h", value)


def _set_bit(operand: int, bit_index: int) -> bytes:
    return b"\x3A" + _u16(operand) + _u16(bit_index) + b"\x40"


def _clear_bit(operand: int, bit_index: int) -> bytes:
    return b"\x3B" + _u16(operand) + _u16(bit_index) + b"\x40"


def _bit_test(operand: int, mask: int, failure_pc: int) -> bytes:
    # OP02 control 0x46 is immediate bitwise-AND.  A successful test falls
    # through; a failed one branches to failure_pc.
    return b"\x02" + _u16(operand) + _u16(mask) + b"\x46" + _u16(failure_pc)


def _exact_test(operand: int, value: int, failure_pc: int) -> bytes:
    # OP02 control 0x40 is immediate equality, used when every local switch
    # must be set rather than merely any bit in the mask.
    return b"\x02" + _u16(operand) + _u16(value) + b"\x40" + _u16(failure_pc)


def _jump(pc: int) -> bytes:
    return b"\x01" + _u16(pc)


def _signed_word(value: int) -> int:
    """Return one 16-bit pattern as the signed literal expected by OP35/math."""

    if not 0 <= value <= 0xFFFF:
        raise SurfaceCampaignBuildError(f"word is outside 0..65535: {value}")
    return value if value < 0x8000 else value - 0x10000


def _appointment_phase_body(phase: int) -> bytes:
    """Replace only appointment phase bits while preserving campaign state."""

    if phase not in {
        APPOINTMENT_PHASE_NONE,
        APPOINTMENT_PHASE_REGISTERED,
        APPOINTMENT_PHASE_ARMED,
        APPOINTMENT_PHASE_CALLED,
        APPOINTMENT_PHASE_ENTERED,
        APPOINTMENT_PHASE_LEGACY_BRIEFED,
        APPOINTMENT_PHASE_OFFICE_ACTIVE,
        APPOINTMENT_PHASE_RESOLVED,
    }:
        raise SurfaceCampaignBuildError(f"Unsupported appointment phase {phase:#x}")
    return (
        atel.variable_math(
            0x3E,
            STATE_OPERAND,
            _signed_word((~APPOINTMENT_PHASE_MASK) & 0xFFFF),
        )
        + atel.variable_math(0x38, STATE_OPERAND, phase)
    )


def _appointment_stage_body(stage: int) -> bytes:
    """Replace the retired timestamp with one office substage and keep alias."""

    if stage not in {
        APPOINTMENT_STAGE_NONE,
        APPOINTMENT_STAGE_AWAIT_REFUSAL,
        APPOINTMENT_STAGE_FINAL_WARNING,
        APPOINTMENT_STAGE_SECURITY_PENDING,
        APPOINTMENT_STAGE_FLEE_PENDING,
        APPOINTMENT_STAGE_COMPLETE,
        APPOINTMENT_STAGE_SECURITY_ENTERING,
        APPOINTMENT_STAGE_BATTLE_PENDING,
    }:
        raise SurfaceCampaignBuildError(f"Unsupported appointment stage {stage}")
    return (
        atel.variable_math(
            0x3E,
            APPOINTMENT_OPERAND,
            _signed_word(APPOINTMENT_ALIAS_MASK),
        )
        + atel.variable_math(0x38, APPOINTMENT_OPERAND, stage)
    )


def _appointment_stage_snapshot_body(
    scratch_variable: int = APPOINTMENT_SCRATCH_VARIABLE,
) -> bytes:
    return (
        atel.copy_variable(scratch_variable, APPOINTMENT_OPERAND)
        + atel.variable_math(
            0x3E, scratch_variable, APPOINTMENT_STAGE_MASK
        )
    )


def _appointment_alias_body(alias_index: int) -> bytes:
    """Persist one alias without starting its timer."""

    if not 0 <= alias_index < len(APPOINTMENT_ALIAS_CODES):
        raise SurfaceCampaignBuildError("Appointment alias index is invalid")
    return (
        atel.set_variable_s16(
            APPOINTMENT_OPERAND,
            _signed_word(APPOINTMENT_ALIAS_CODES[alias_index]),
        )
        + _appointment_phase_body(APPOINTMENT_PHASE_REGISTERED)
    )


def _appointment_current_time_body() -> bytes:
    """Compute native play time in seconds modulo 0x4000 into NOW."""

    return (
        atel.copy_variable(APPOINTMENT_NOW_VARIABLE, 0x000E)
        + atel.variable_math(
            0xDE, APPOINTMENT_NOW_VARIABLE, 3_600
        )
        + atel.copy_variable(
            APPOINTMENT_PACKED_CLOCK_VARIABLE, 0x000C
        )
        + atel.copy_variable(
            APPOINTMENT_MINUTE_VARIABLE,
            APPOINTMENT_PACKED_CLOCK_VARIABLE,
        )
        + base.mass_driver._shift_variable_right(
            APPOINTMENT_MINUTE_VARIABLE, 8
        )
        + atel.variable_math(
            0x3E, APPOINTMENT_PACKED_CLOCK_VARIABLE, 0x00FF
        )
        + atel.variable_math(
            0xDE, APPOINTMENT_MINUTE_VARIABLE, 60
        )
        + atel.variable_math(
            0x38,
            APPOINTMENT_NOW_VARIABLE,
            APPOINTMENT_MINUTE_VARIABLE,
            operand_is_variable=True,
        )
        + atel.variable_math(
            0x38,
            APPOINTMENT_NOW_VARIABLE,
            APPOINTMENT_PACKED_CLOCK_VARIABLE,
            operand_is_variable=True,
        )
        + atel.variable_math(
            0x3E, APPOINTMENT_NOW_VARIABLE, APPOINTMENT_TIME_MASK
        )
    )


def _appointment_store_timestamp_body() -> bytes:
    """Combine NOW's low fourteen bits with the already-selected alias."""

    return (
        atel.copy_variable(
            APPOINTMENT_SCRATCH_VARIABLE, APPOINTMENT_OPERAND
        )
        + atel.variable_math(
            0x3E,
            APPOINTMENT_SCRATCH_VARIABLE,
            _signed_word(APPOINTMENT_ALIAS_MASK),
        )
        + atel.variable_math(
            0x38,
            APPOINTMENT_NOW_VARIABLE,
            APPOINTMENT_SCRATCH_VARIABLE,
            operand_is_variable=True,
        )
        + atel.copy_variable(
            APPOINTMENT_OPERAND, APPOINTMENT_NOW_VARIABLE
        )
    )


def _appointment_phase_snapshot_body(
    scratch_variable: int = APPOINTMENT_SCRATCH_VARIABLE,
) -> bytes:
    return (
        atel.copy_variable(scratch_variable, STATE_OPERAND)
        + atel.variable_math(
            0x3E, scratch_variable, APPOINTMENT_PHASE_MASK
        )
    )


def _appointment_arm_guarded_body(routine_pc: int) -> bytes:
    """Snapshot the clock once, only while phase is REGISTERED."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(_appointment_phase_snapshot_body())
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_REGISTERED,
        "finish",
    )
    routine.emit(_appointment_current_time_body())
    routine.emit(_appointment_store_timestamp_body())
    routine.emit(_appointment_phase_body(APPOINTMENT_PHASE_ARMED))
    routine.label("finish")
    return routine.finish()


def _actor_waypoint_body(
    waypoints: Sequence[tuple[int, int]],
    *,
    final_direction: int,
    max_steps: int = INTAKE_DOCTOR_WAYPOINT_MAX_STEPS,
) -> bytes:
    """Walk one NPC along audited straight chords and snap its final point."""

    if (
        not waypoints
        or not 0 <= final_direction <= 7
        or not 1 <= max_steps <= 0x7FFF
    ):
        raise SurfaceCampaignBuildError("Actor waypoint contract is invalid")
    result = bytearray()
    for x, z in waypoints:
        result.extend(
            b"\x4B"
            + _s16(x)
            + _s16(z)
            + b"\xC0"
            + base._immediate(max_steps)
        )
    final_x, final_z = waypoints[-1]
    result.extend(
        b"\x19"
        + _s16(final_x)
        + _s16(final_z)
        + b"\xC0\x1A\x00\x5F"
        + bytes((final_direction,))
    )
    return bytes(result)


def _validate_intake_doctor_route(prepared: base.PreparedField) -> None:
    """Prove every sampled approach point stays on the lobby walkmesh."""

    expected_return = tuple(reversed(INTAKE_DOCTOR_OUTBOUND_WAYPOINTS[:-1])) + (
        INTAKE_DOCTOR_STAGING_POSITION,
    )
    if INTAKE_DOCTOR_RETURN_WAYPOINTS != expected_return:
        raise SurfaceCampaignBuildError("Doctor return route is not reciprocal")

    triangles = base._walkmesh_layer(prepared.components[1], 0)
    route = (INTAKE_DOCTOR_STAGING_POSITION, *INTAKE_DOCTOR_OUTBOUND_WAYPOINTS)
    for start, finish in zip(route, route[1:], strict=False):
        span = max(abs(finish[0] - start[0]), abs(finish[1] - start[1]))
        samples = max(1, (span + 3) // 4)
        for index in range(samples + 1):
            point = (
                round(start[0] + (finish[0] - start[0]) * index / samples),
                round(start[1] + (finish[1] - start[1]) * index / samples),
            )
            if not any(
                base._point_inside_triangle(point, triangle)
                for triangle in triangles
            ):
                raise SurfaceCampaignBuildError(
                    f"Doctor route leaves the walkmesh at {point}"
                )

    waiting_hits = tuple(
        index
        for index, triangle in enumerate(triangles)
        if base._point_inside_triangle(INTAKE_DOCTOR_WAITING_POSITION, triangle)
    )
    if waiting_hits != (INTAKE_DOCTOR_WAITING_TRIANGLE,) or any(
        vertex[1] != 0
        for vertex in triangles[INTAKE_DOCTOR_WAITING_TRIANGLE]
    ):
        raise SurfaceCampaignBuildError(
            "Doctor reception endpoint is not on its audited flat triangle"
        )


def _clinic_walkmesh_material(
    walkmesh: bytes,
    triangle: int,
) -> tuple[int, int]:
    """Return one field-550 layer-0 triangle's material and runtime flags."""

    triangle_offset = struct.unpack_from("<I", walkmesh, 0x18)[0]
    material_offset = struct.unpack_from("<I", walkmesh, 0x14)[0]
    material = struct.unpack_from(
        "<H", walkmesh, triangle_offset + triangle * 14 + 12
    )[0]
    flags = struct.unpack_from("<I", walkmesh, material_offset + material * 4)[0]
    return material, flags


def _validate_clinic_walkmesh_material_contract(walkmesh: bytes) -> None:
    """Freeze the non-walkable exterior strip that needs a scoped override."""

    if (
        len(walkmesh) != CLINIC_SOURCE_WALKMESH_SIZE
        or _sha256(walkmesh) != CLINIC_SOURCE_WALKMESH_SHA256
        or struct.unpack_from("<I", walkmesh, 0)[0]
        != CLINIC_WALKMESH_LAYER_COUNT
        or struct.unpack_from("<I", walkmesh, 4)[0]
        != CLINIC_WALKMESH_LAYER0_TRIANGLE_BYTES
        or struct.unpack_from("<I", walkmesh, 0x14)[0]
        != CLINIC_WALKMESH_MATERIAL_OFFSET
        or struct.unpack_from("<I", walkmesh, 0x18)[0]
        != CLINIC_WALKMESH_LAYER0_TRIANGLE_OFFSET
    ):
        raise SurfaceCampaignBuildError("Clinic walkmesh layout changed")

    for triangle in CLINIC_WALKMESH_EXTERIOR_TRIANGLES:
        material, flags = _clinic_walkmesh_material(walkmesh, triangle)
        if (
            material != CLINIC_WALKMESH_EXTERIOR_MATERIAL
            or flags != CLINIC_WALKMESH_FORBIDDEN_MATERIAL_FLAG
        ):
            raise SurfaceCampaignBuildError(
                f"Clinic exterior triangle {triangle} is no longer the "
                "audited non-walkable doorway strip"
            )

    interior_triangles = (
        set(CLINIC_DOCTOR_ESCAPE_TRIANGLE_ROUTE)
        | {
            triangle
            for route in CLINIC_SECURITY_TRIANGLE_ROUTES.values()
            for triangle in route
        }
    ) - set(CLINIC_WALKMESH_EXTERIOR_TRIANGLES)
    for triangle in interior_triangles:
        material, flags = _clinic_walkmesh_material(walkmesh, triangle)
        if material != CLINIC_WALKMESH_INTERIOR_MATERIAL or flags != 0:
            raise SurfaceCampaignBuildError(
                f"Clinic interior route triangle {triangle} is not ordinary floor"
            )


def _required_clinic_waypoint_steps(
    start: tuple[int, int],
    finish: tuple[int, int],
) -> int:
    """Conservative OP4B budget: chord travel plus eight settling updates."""

    distance = math.hypot(finish[0] - start[0], finish[1] - start[1])
    return math.ceil(distance / CLINIC_ACTOR_WALK_STEP_UNITS) + (
        CLINIC_ACTOR_WALK_SAFETY_STEPS
    )


def _validate_clinic_doctor_escape_route(walkmesh: bytes) -> None:
    """Prove the physician follows real edges from the office through the door."""

    _validate_clinic_walkmesh_material_contract(walkmesh)
    triangles = base._walkmesh_layer(walkmesh, 0)
    route = (CLINIC_DOCTOR_POSITION, *CLINIC_DOCTOR_ESCAPE_WAYPOINTS)
    if len(route) != len(CLINIC_DOCTOR_ESCAPE_TRIANGLE_ROUTE):
        raise SurfaceCampaignBuildError("Clinic doctor triangle route changed")
    for point, triangle_index in zip(
        route, CLINIC_DOCTOR_ESCAPE_TRIANGLE_ROUTE, strict=True
    ):
        hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if base._point_inside_triangle(point, triangle)
        )
        if hits != (triangle_index,):
            raise SurfaceCampaignBuildError(
                f"Clinic doctor waypoint {point} left triangle {triangle_index}: {hits}"
            )

    for (start, finish), (start_triangle, finish_triangle) in zip(
        zip(route, route[1:], strict=False),
        zip(
            CLINIC_DOCTOR_ESCAPE_TRIANGLE_ROUTE,
            CLINIC_DOCTOR_ESCAPE_TRIANGLE_ROUTE[1:],
            strict=False,
        ),
        strict=True,
    ):
        if start_triangle != finish_triangle and len(
            set(triangles[start_triangle]) & set(triangles[finish_triangle])
        ) != 2:
            raise SurfaceCampaignBuildError(
                "Clinic doctor route crosses nonadjacent triangles "
                f"{start_triangle}->{finish_triangle}"
            )
        span = max(abs(finish[0] - start[0]), abs(finish[1] - start[1]))
        samples = max(1, (span + 3) // 4)
        for index in range(samples + 1):
            point = (
                round(start[0] + (finish[0] - start[0]) * index / samples),
                round(start[1] + (finish[1] - start[1]) * index / samples),
            )
            if not any(
                base._point_inside_triangle(point, triangles[triangle_index])
                for triangle_index in (start_triangle, finish_triangle)
            ):
                raise SurfaceCampaignBuildError(
                    f"Clinic doctor escape route leaves the walkmesh at {point}"
                )

    endpoint = CLINIC_DOCTOR_ESCAPE_WAYPOINTS[-1]
    endpoint_hits = tuple(
        index
        for index, triangle in enumerate(triangles)
        if base._point_inside_triangle(endpoint, triangle)
    )
    if endpoint_hits != CLINIC_DOCTOR_ESCAPE_TRIANGLES or any(
        vertex[1] != 0
        for triangle_index in endpoint_hits
        for vertex in triangles[triangle_index]
    ):
        raise SurfaceCampaignBuildError(
            "Clinic doctor escape endpoint left its audited flat doorway strip"
        )

    threshold_route = (
        CLINIC_DOCTOR_ESCAPE_APPROACH_WAYPOINTS[-1],
        *CLINIC_DOCTOR_ESCAPE_THRESHOLD_WAYPOINTS,
    )
    for start, finish in zip(
        threshold_route, threshold_route[1:], strict=False
    ):
        required = _required_clinic_waypoint_steps(start, finish)
        if CLINIC_DOCTOR_THRESHOLD_WAYPOINT_MAX_STEPS < required:
            raise SurfaceCampaignBuildError(
                "Clinic doctor threshold bound cannot complete "
                f"{start}->{finish}: {required} updates required"
            )


def _validate_clinic_security_routes(walkmesh: bytes) -> None:
    """Prove every response route crosses real edges to distinct room mesh."""

    _validate_clinic_walkmesh_material_contract(walkmesh)
    triangles = base._walkmesh_layer(walkmesh, 0)
    if (
        set(CLINIC_SECURITY_ROUTES) != set(CLINIC_SECURITY_ENTITIES)
        or set(CLINIC_SECURITY_TRIANGLE_ROUTES) != set(CLINIC_SECURITY_ENTITIES)
    ):
        raise SurfaceCampaignBuildError("Clinic security route inventory changed")
    if any(
        route[:2]
        != (
            CLINIC_SECURITY_REVEAL_POSITION,
            CLINIC_SECURITY_FIRST_INTERIOR_POSITION,
        )
        for route in CLINIC_SECURITY_ROUTES.values()
    ):
        raise SurfaceCampaignBuildError(
            "Clinic security routes no longer cross the audited doorway"
        )
    if any(
        route[2] != CLINIC_SECURITY_OVERRIDE_CLEAR_POSITION
        for route in CLINIC_SECURITY_ROUTES.values()
    ):
        raise SurfaceCampaignBuildError(
            "Clinic security override no longer clears on deep interior floor"
        )
    reveal_triangle = CLINIC_SECURITY_TRIANGLE_ROUTES[
        CLINIC_SECURITY_ENTITIES[0]
    ][1]
    interior_triangle = CLINIC_SECURITY_TRIANGLE_ROUTES[
        CLINIC_SECURITY_ENTITIES[0]
    ][2]
    if (
        CLINIC_SECURITY_REVEAL_POSITION[1]
        <= CLINIC_SECURITY_DOOR_PLANE_Z
        or CLINIC_SECURITY_FIRST_INTERIOR_POSITION[1]
        >= CLINIC_SECURITY_DOOR_PLANE_Z
        or len(
            set(triangles[reveal_triangle])
            & set(triangles[interior_triangle])
        )
        != 2
    ):
        raise SurfaceCampaignBuildError(
            "Clinic security reveal no longer straddles the real doorway edge"
        )
    endpoints: set[tuple[int, int]] = set()
    for entity, waypoints in CLINIC_SECURITY_ROUTES.items():
        route = (CLINIC_SECURITY_STAGING_POSITION, *waypoints)
        triangle_route = CLINIC_SECURITY_TRIANGLE_ROUTES[entity]
        if len(route) != len(triangle_route):
            raise SurfaceCampaignBuildError(
                f"Clinic security e{entity} triangle route changed"
            )
        for point, triangle_index in zip(route, triangle_route, strict=True):
            hits = tuple(
                index
                for index, triangle in enumerate(triangles)
                if base._point_inside_triangle(point, triangle)
            )
            if hits != (triangle_index,):
                raise SurfaceCampaignBuildError(
                    f"Clinic security e{entity} waypoint {point} left triangle "
                    f"{triangle_index}: {hits}"
                )

        for (start, finish), (start_triangle, finish_triangle) in zip(
            zip(route, route[1:], strict=False),
            zip(triangle_route, triangle_route[1:], strict=False),
            strict=True,
        ):
            if start_triangle != finish_triangle and len(
                set(triangles[start_triangle]) & set(triangles[finish_triangle])
            ) != 2:
                raise SurfaceCampaignBuildError(
                    f"Clinic security e{entity} route crosses nonadjacent "
                    f"triangles {start_triangle}->{finish_triangle}"
                )
            span = max(abs(finish[0] - start[0]), abs(finish[1] - start[1]))
            samples = max(1, (span + 3) // 4)
            for index in range(samples + 1):
                point = (
                    round(start[0] + (finish[0] - start[0]) * index / samples),
                    round(start[1] + (finish[1] - start[1]) * index / samples),
                )
                if not any(
                    base._point_inside_triangle(point, triangles[triangle_index])
                    for triangle_index in (start_triangle, finish_triangle)
                ):
                    raise SurfaceCampaignBuildError(
                        f"Clinic security e{entity} route leaves the walkmesh at {point}"
                    )
            required = _required_clinic_waypoint_steps(start, finish)
            if CLINIC_SECURITY_WAYPOINT_MAX_STEPS < required:
                raise SurfaceCampaignBuildError(
                    f"Clinic security e{entity} bound cannot complete "
                    f"{start}->{finish}: {required} updates required"
                )
        endpoint = waypoints[-1]
        hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if base._point_inside_triangle(endpoint, triangle)
        )
        if hits != (CLINIC_SECURITY_FINAL_TRIANGLES[entity],):
            raise SurfaceCampaignBuildError(
                f"Clinic security e{entity} endpoint changed: {hits}"
            )
        endpoints.add(endpoint)
    if len(endpoints) != len(CLINIC_SECURITY_ENTITIES):
        raise SurfaceCampaignBuildError("Clinic security endpoints overlap")

    # OP4B completes within one 8-unit movement step plus its one-unit
    # tolerance.  Prove every possible clearing point around (0,200) is on
    # ordinary material before the actor-local 0x0038 override is removed.
    radius = CLINIC_ACTOR_WALK_STEP_UNITS + 1
    center_x, center_z = CLINIC_SECURITY_OVERRIDE_CLEAR_POSITION
    for dx in range(-radius, radius + 1):
        for dz in range(-radius, radius + 1):
            if dx * dx + dz * dz > radius * radius:
                continue
            point = (center_x + dx, center_z + dz)
            hits = tuple(
                index
                for index, triangle in enumerate(triangles)
                if base._point_inside_triangle(point, triangle)
            )
            if not hits or any(
                _clinic_walkmesh_material(walkmesh, triangle)[1]
                & CLINIC_WALKMESH_FORBIDDEN_MATERIAL_FLAG
                for triangle in hits
            ):
                raise SurfaceCampaignBuildError(
                    f"Clinic security override could clear on unsafe floor at {point}"
                )


def _repeatable_dialogue_action(dialogue_id: int, routine_pc: int) -> bytes:
    release_pc = routine_pc + 3
    return (
        b"\x33\xFE\x54"
        + base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + b"\x26\x01\x80"
        + b"\xF5"
        + _u16(dialogue_id)
        + b"\x01\x9C\xFE\x53\x00"
    )


def _current_end_door_notice_action(dialogue_id: int, routine_pc: int) -> bytes:
    """Show the current-content notice without opening or retriggering.

    The first release loop drains the press that started the interaction.  The
    second drains the press that closes the window, so the invisible door
    controller cannot immediately reopen the same notice on the next VM tick.
    """

    prefix = (
        b"\x33\xFE\x54"
        + base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            routine_pc + 3,
        )
        + b"\x26\x01\x80"
        + b"\xF5"
        + _u16(dialogue_id)
        + b"\x01\x9C"
    )
    close_release_pc = routine_pc + len(prefix)
    return (
        prefix
        + base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            close_release_pc,
        )
        + b"\x26\x01\x80"
        + b"\xFE\x53\x00"
    )


def _actor_dialogue(dialogue_id: int) -> bytes:
    """Show one actor-owned retail dialogue and wait for its close."""

    return base.mass_driver._choice_dialog(dialogue_id) + b"\x9C"


def _read_character_weight_lbs(character_id: int) -> bytes:
    """Read one live Status weight and format decimal pounds for dialogue."""

    if character_id not in PATIENT_CHARACTER_IDS.values():
        raise SurfaceCampaignBuildError(
            "Weight character ID is outside the intake party"
        )
    whole = PATIENT_WEIGHT_WHOLE_DIALOG_VARIABLE
    fraction = PATIENT_WEIGHT_FRACTION_DIALOG_VARIABLE
    return (
        b"\xFE\x69" + _u16(whole) + bytes((character_id, 0x80))
        + atel.variable_math(
            0xDE,
            whole,
            POUNDS_TENTHS_PER_NATIVE_WHOLE,
        )
        + atel.copy_variable(fraction, whole)
        + atel.variable_math(
            0xDF,
            whole,
            POUNDS_DECIMAL_BASE,
        )
        + atel.variable_math(
            0xDE,
            whole,
            POUNDS_DECIMAL_BASE,
        )
        + atel.variable_math(
            0x39,
            fraction,
            whole,
            operand_is_variable=True,
        )
        + atel.variable_math(
            0xDF,
            whole,
            POUNDS_DECIMAL_BASE,
        )
    )


def _intake_receptionist_init() -> bytes:
    """Keep the visible receptionist while covering the saved desk stance.

    Retail leaves e13 on the default 16-unit circular body.  Together with
    Fei's radius and the engine's fixed interaction allowance, that reaches
    only 64 units; the user's exact straight-on save is 131 units away across
    the counter.  A rectangular, no-facing action volume reaches that stance.
    OP20 makes only the actor collision ghosted, so the existing sprite still
    renders and the counter geometry remains authoritative.
    """

    if not INTAKE_RECEPTIONIST_RETAIL_INIT.endswith(b"\x00"):
        raise SurfaceCampaignBuildError("Receptionist retail init lost STOP")
    return (
        INTAKE_RECEPTIONIST_RETAIL_INIT[:-1]
        + b"\xF8\x00\x00\x20"
        + b"\xF8\x07\x04\x00"
        + b"\x18"
        + bytes(
            (
                INTAKE_RECEPTIONIST_INTERACTION_HALF_WIDTH,
                INTAKE_RECEPTIONIST_INTERACTION_HALF_DEPTH,
                0,
                0,
            )
        )
        + b"\x20\x01\x80\x00"
    )


def _intake_native_dialogue_mutex_action(dialogue_id: int) -> bytes:
    """Preserve one retail lobby line while publishing its window lifetime."""

    return (
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 1)
        + _actor_dialogue(dialogue_id)
        + atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 0)
        + b"\x00"
    )


def _intake_receptionist_action(
    *,
    precheck_dialogue_id: int,
    postcheck_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Build the input-safe, state-aware receptionist conversation."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 1)
    )
    routine.emit(b"\x33\xFE\x54")
    release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "precheck")
    routine.emit(_actor_dialogue(postcheck_dialogue_id))
    routine.jump("finish")

    routine.label("precheck")
    routine.emit(_actor_dialogue(precheck_dialogue_id))

    routine.label("finish")
    close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 0)
    )
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def _intake_quarantine_locked_action(
    *,
    dialogue_id: int,
    unlocked_action_pc: int,
    routine_pc: int,
) -> bytes:
    """Open Intake's Quarantine entrance with the Quarantine keycard.

    Entity 22 is an invisible X-action carrier, so its denial uses the same
    hidden-owner mode-3 dialogue form as the examination-room gate.  Publish
    the lobby mutex for the complete interaction so the timed physician call
    cannot overlap the lock notice, and drain both the initiating and closing
    Cross presses before returning control.
    """

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.jump_if_bit_clear(
        QUARANTINE_KEYCARD_OPERAND,
        QUARANTINE_KEYCARD_MASK,
        "locked",
    )
    routine.emit(_jump(unlocked_action_pc))

    routine.label("locked")
    routine.emit(
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 1)
    )
    routine.emit(b"\x33\xFE\x54")
    open_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            open_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(b"\xF5" + _u16(dialogue_id) + b"\x01\x9C")
    close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 0)
    )
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def _intake_freight_keycard_gate_action(
    *,
    dialogue_id: int,
    unlocked_action_pc: int,
    routine_pc: int,
    require_tone_authorization: bool = False,
) -> bytes:
    """Gate an Intake route behind its required persistent credentials.

    Intake's patient-service, service-manifold, and examination-room doors all
    require the clinic security keycard.  The optional tone check remains for
    callers that deliberately compose a later two-credential threshold.
    """

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.jump_if_bit_clear(
        SECURITY_KEYCARD_OPERAND,
        SECURITY_KEYCARD_MASK,
        "locked",
    )
    if require_tone_authorization:
        routine.jump_if_bit_clear(TONE_OPERAND, TONE_MASK, "locked")
    routine.emit(_jump(unlocked_action_pc))

    # Keep the locked interaction serialized with every other lobby dialogue.
    # The hidden carrier owns a mode-3 window, and both Cross edges are drained
    # before control returns so one held press cannot immediately retry it.
    routine.label("locked")
    routine.emit(
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 1)
    )
    routine.emit(b"\x33\xFE\x54")
    open_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            open_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(b"\xF5" + _u16(dialogue_id) + b"\x01\x9C")
    close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 0)
    )
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def _appointment_store_new_alias_timestamp_body(alias_index: int) -> bytes:
    if not 0 <= alias_index < len(APPOINTMENT_ALIAS_CODES):
        raise SurfaceCampaignBuildError("Appointment alias index is invalid")
    return (
        _appointment_current_time_body()
        + atel.variable_math(
            0x38,
            APPOINTMENT_NOW_VARIABLE,
            _signed_word(APPOINTMENT_ALIAS_CODES[alias_index]),
        )
        + atel.copy_variable(
            APPOINTMENT_OPERAND, APPOINTMENT_NOW_VARIABLE
        )
    )


def _routine_jump_if_less_than(
    routine: object,
    variable: int,
    value: int,
    label: str,
) -> None:
    """Emit OP02/control44 and register an absolute label fixup."""

    if not isinstance(routine, base.mass_driver._RoutineBuilder):
        raise SurfaceCampaignBuildError("Appointment branch builder changed")
    if not -0x8000 <= value <= 0x7FFF:
        raise SurfaceCampaignBuildError("Appointment comparison is outside s16")
    routine.data.extend(b"\x02" + _u16(variable) + _s16(value) + b"\x44")
    routine.fixups.append((len(routine.data), label))
    routine.data.extend(b"\x00\x00")


def _intake_doctor_init(*, routine_pc: int) -> bytes:
    """Stage a ghosted doctor or restore a solid doctor at reception."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(
        atel.set_variable_s16(
            APPOINTMENT_DOCTOR_BUSY_VARIABLE, 0
        )
    )
    routine.emit(
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 0)
    )
    routine.emit(
        atel.set_variable_s16(
            INTAKE_DOCTOR_DOOR_OPEN_VARIABLE, 0
        )
    )
    routine.emit(b"\x0B" + base._immediate(INTAKE_DOCTOR_GRAPHIC))
    routine.emit(b"\xF8\x00\x00\x20\xF8\x07\x04\x00")
    routine.emit(
        DOCTOR_RECTANGULAR_BOUNDING_VOLUME + DOCTOR_TRANSIT_COLLISION_FLAGS
    )
    routine.emit(_appointment_phase_snapshot_body())
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_CALLED,
        "staged",
    )
    routine.emit(
        atel.copy_variable(
            APPOINTMENT_SCRATCH_VARIABLE, APPOINTMENT_OPERAND
        )
    )
    routine.emit(
        atel.variable_math(
            0x3E,
            APPOINTMENT_SCRATCH_VARIABLE,
            _signed_word(APPOINTMENT_ALIAS_MASK),
        )
    )
    routine.jump_if_equal(APPOINTMENT_SCRATCH_VARIABLE, 0, "staged")
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "staged")
    routine.emit(
        b"\x19"
        + _s16(INTAKE_DOCTOR_WAITING_POSITION[0])
        + _s16(INTAKE_DOCTOR_WAITING_POSITION[1])
        + b"\xC0\x1A\x00\x69\x06\x80"
    )
    routine.emit(DOCTOR_STATIONARY_COLLISION_FLAGS)
    routine.jump("finish")
    routine.label("staged")
    routine.emit(
        b"\x19"
        + _s16(INTAKE_DOCTOR_STAGING_POSITION[0])
        + _s16(INTAKE_DOCTOR_STAGING_POSITION[1])
        + b"\xC0\x1A\x00\x69\x06\x80\x23"
    )
    routine.label("finish")
    routine.emit(b"\x00")
    return routine.finish()


def _intake_doctor_update(
    *,
    legacy_menu_dialogue_id: int,
    call_dialogue_ids: Sequence[int],
    routine_pc: int,
) -> bytes:
    """Migrate V183 saves, poll one minute, emerge, and call the alias."""

    if len(call_dialogue_ids) != len(CHECKIN_ALIASES):
        raise SurfaceCampaignBuildError("Doctor call dialogue count changed")
    routine = base.mass_driver._RoutineBuilder(routine_pc)

    # A V183 save has check-in bit 7 but no persisted alias.  Prompt once on
    # the first updated reception load and start its timer from that moment.
    routine.emit(
        atel.copy_variable(
            APPOINTMENT_SCRATCH_VARIABLE, APPOINTMENT_OPERAND
        )
    )
    routine.emit(
        atel.variable_math(
            0x3E,
            APPOINTMENT_SCRATCH_VARIABLE,
            _signed_word(APPOINTMENT_ALIAS_MASK),
        )
    )
    routine.jump_if_equal(APPOINTMENT_SCRATCH_VARIABLE, 0, "missing_alias")
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "unregistered")
    routine.jump("phase_check")

    routine.label("missing_alias")
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "unregistered")

    routine.label("legacy_prompt")
    routine.emit(b"\x33\xFE\x54")
    release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(base.mass_driver._choice_dialog(legacy_menu_dialogue_id))
    routine.emit(b"\xA9\x14\x9C")
    for selection, alias in enumerate(CHECKIN_ALIASES, start=1):
        next_label = f"legacy_after_{alias.lower()}"
        routine.jump_if_not_equal(0x0014, selection, next_label)
        routine.emit(_appointment_store_new_alias_timestamp_body(selection - 1))
        routine.emit(_appointment_phase_body(APPOINTMENT_PHASE_ARMED))
        routine.emit(b"\xFE\x53")
        routine.jump("phase_check")
        routine.label(next_label)
    routine.jump("legacy_prompt")

    routine.label("unregistered")
    routine.emit(_appointment_phase_body(APPOINTMENT_PHASE_NONE))
    routine.jump("finish")

    routine.label("phase_check")
    routine.emit(_appointment_phase_snapshot_body())
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_REGISTERED,
        "recover_arm",
    )
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_ARMED,
        "finish",
    )
    routine.jump("poll")

    # Recovery for a direct/debug field change that bypassed the archive exit.
    routine.label("recover_arm")
    routine.emit(_appointment_current_time_body())
    routine.emit(_appointment_store_timestamp_body())
    routine.emit(_appointment_phase_body(APPOINTMENT_PHASE_ARMED))

    routine.label("poll")
    routine.emit(_appointment_current_time_body())
    routine.emit(
        atel.copy_variable(
            APPOINTMENT_SCRATCH_VARIABLE, APPOINTMENT_OPERAND
        )
    )
    routine.emit(
        atel.variable_math(
            0x3E, APPOINTMENT_SCRATCH_VARIABLE, APPOINTMENT_TIME_MASK
        )
    )
    routine.emit(
        atel.variable_math(
            0x39,
            APPOINTMENT_NOW_VARIABLE,
            APPOINTMENT_SCRATCH_VARIABLE,
            operand_is_variable=True,
        )
    )
    routine.emit(
        atel.variable_math(
            0x3E, APPOINTMENT_NOW_VARIABLE, APPOINTMENT_TIME_MASK
        )
    )
    _routine_jump_if_less_than(
        routine,
        APPOINTMENT_NOW_VARIABLE,
        APPOINTMENT_DELAY_SECONDS,
        "wait",
    )

    # Ghost the doctor only for the scripted route so the still-solid player
    # seal cannot block his passage through the animated panel.  Mark only his
    # own action busy: Fei remains controllable throughout the outbound walk.
    routine.emit(
        atel.set_variable_s16(
            APPOINTMENT_DOCTOR_BUSY_VARIABLE, 1
        )
    )
    routine.emit(DOCTOR_TRANSIT_COLLISION_FLAGS)
    routine.emit(
        b"\x09"
        + bytes(
            (
                INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
                0x20 | INTAKE_DOCTOR_DOOR_OPEN_SCRIPT,
            )
        )
    )
    routine.emit(
        atel.set_variable_s16(
            INTAKE_DOCTOR_DOOR_OPEN_VARIABLE, 1
        )
    )
    routine.emit(b"\x24" + bytes((INTAKE_DOCTOR_ENTITY,)))
    routine.emit(
        _actor_waypoint_body(
            INTAKE_DOCTOR_OUTBOUND_WAYPOINTS,
            final_direction=6,
        )
    )
    routine.emit(
        b"\x09"
        + bytes(
            (
                INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
                0x20 | INTAKE_DOCTOR_DOOR_CLOSE_SCRIPT,
            )
        )
    )
    routine.emit(
        atel.set_variable_s16(
            INTAKE_DOCTOR_DOOR_OPEN_VARIABLE, 0
        )
    )
    # Once the panel has finished closing, restore normal NPC collision before
    # the alias call. Save/reload in the called phase applies the same state.
    routine.emit(DOCTOR_STATIONARY_COLLISION_FLAGS)
    # Fei may talk to any retained lobby survivor while the physician walks.
    # Those actions publish their dialogue lifetime in a field-local mutex.
    # Stay controllable and yield here until the existing window has closed;
    # actor 35 then opens the automatic alias call without overlapping it or
    # restoring control out from under the other actor's WAIT_DIALOG.
    routine.label("wait_dialog_idle")
    routine.jump_if_equal(
        INTAKE_DIALOG_BUSY_VARIABLE, 0, "choose_alias_call"
    )
    routine.emit(base.mass_driver._yield_tick())
    routine.jump("wait_dialog_idle")
    routine.label("choose_alias_call")
    # Lock before automatic_dialogue_body's F4 reset yields. Without this
    # leading lock, collision dispatch could schedule a new X action in the
    # one frame between the successful mutex check and the helper's FE54.
    routine.emit(b"\x33\xFE\x54")
    routine.jump_if_bit_clear(APPOINTMENT_OPERAND, 0x8000, "call_aron")
    routine.jump_if_bit_clear(APPOINTMENT_OPERAND, 0x4000, "call_noel")
    routine.emit(
        base.mass_driver._automatic_dialogue_body(
            (call_dialogue_ids[2],),
            routine_pc=routine.pc,
            reset_actor_dialog_state=True,
        )
    )
    routine.jump("call_finish")
    routine.label("call_aron")
    routine.emit(
        base.mass_driver._automatic_dialogue_body(
            (call_dialogue_ids[0],),
            routine_pc=routine.pc,
            reset_actor_dialog_state=True,
        )
    )
    routine.jump("call_finish")
    routine.label("call_noel")
    routine.emit(
        base.mass_driver._automatic_dialogue_body(
            (call_dialogue_ids[1],),
            routine_pc=routine.pc,
            reset_actor_dialog_state=True,
        )
    )
    routine.label("call_finish")
    # Commit only after WAIT_DIALOG.  A savestate made during the call safely
    # repeats the arrival instead of permanently skipping the requested name.
    call_close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            call_close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_appointment_phase_body(APPOINTMENT_PHASE_CALLED))
    routine.emit(
        atel.set_variable_s16(
            APPOINTMENT_DOCTOR_BUSY_VARIABLE, 0
        )
    )
    routine.jump("finish")

    routine.label("wait")
    routine.emit(base.mass_driver._yield_tick())
    routine.jump("poll")
    routine.label("finish")
    routine.emit(b"\x00")
    return routine.finish()


def _intake_doctor_action(
    *,
    instruction_dialogue_ids: Sequence[int],
    routine_pc: int,
) -> bytes:
    """Tell Fei to follow, then return the doctor through the office door."""

    if len(instruction_dialogue_ids) != len(CHECKIN_ALIASES):
        raise SurfaceCampaignBuildError("Doctor instruction dialogue count changed")
    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.jump_if_not_equal(
        APPOINTMENT_DOCTOR_BUSY_VARIABLE, 0, "finish_unlocked"
    )
    routine.emit(_appointment_phase_snapshot_body())
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_CALLED,
        "finish_unlocked",
    )
    routine.emit(b"\x33\xFE\x54")
    release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.jump_if_bit_clear(APPOINTMENT_OPERAND, 0x8000, "talk_aron")
    routine.jump_if_bit_clear(APPOINTMENT_OPERAND, 0x4000, "talk_noel")
    routine.emit(_actor_dialogue(instruction_dialogue_ids[2]))
    routine.jump("enter")
    routine.label("talk_aron")
    routine.emit(_actor_dialogue(instruction_dialogue_ids[0]))
    routine.jump("enter")
    routine.label("talk_noel")
    routine.emit(_actor_dialogue(instruction_dialogue_ids[1]))

    routine.label("enter")
    routine.emit(
        atel.set_variable_s16(
            APPOINTMENT_DOCTOR_BUSY_VARIABLE, 1
        )
    )
    # Release collision before returning control: Fei may keep moving while the
    # doctor follows his route through the still-solid doorway seal.
    routine.emit(DOCTOR_TRANSIT_COLLISION_FLAGS)
    # Dialogue is over and the doctor owns no player waypoint.  Restore field
    # control before he opens the panel and walks back into the office.
    routine.emit(b"\xFE\x53")
    routine.emit(
        b"\x09"
        + bytes(
            (
                INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
                0x20 | INTAKE_DOCTOR_DOOR_OPEN_SCRIPT,
            )
        )
    )
    routine.emit(
        atel.set_variable_s16(
            INTAKE_DOCTOR_DOOR_OPEN_VARIABLE, 1
        )
    )
    routine.emit(
        _actor_waypoint_body(
            INTAKE_DOCTOR_RETURN_WAYPOINTS,
            final_direction=6,
        )
    )
    routine.emit(b"\x23")
    # Leave the panel at its fully open +64 endpoint. Fei remains in control
    # and can follow through the unobstructed-looking doorway without watching
    # it close and immediately replay its opening animation.
    routine.emit(_appointment_phase_body(APPOINTMENT_PHASE_ENTERED))
    routine.emit(
        atel.set_variable_s16(
            APPOINTMENT_DOCTOR_BUSY_VARIABLE, 0
        )
    )
    routine.jump("finish_unlocked")
    routine.label("finish_unlocked")
    routine.emit(b"\x00")
    return routine.finish()


def _clinic_door_gate_action(
    *,
    old_action_pc: int,
    denial_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Gate the office, preserving the open panel after the doctor enters."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(
        atel.copy_variable(
            APPOINTMENT_SCRATCH_VARIABLE, APPOINTMENT_OPERAND
        )
    )
    routine.emit(
        atel.variable_math(
            0x3E,
            APPOINTMENT_SCRATCH_VARIABLE,
            _signed_word(APPOINTMENT_ALIAS_MASK),
        )
    )
    routine.jump_if_equal(APPOINTMENT_SCRATCH_VARIABLE, 0, "denied")
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "denied")
    routine.emit(_appointment_phase_snapshot_body())
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_ENTERED,
        "entered",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_LEGACY_BRIEFED,
        "allowed",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_OFFICE_ACTIVE,
        "allowed",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_RESOLVED,
        "allowed",
    )
    routine.label("denied")
    routine.emit(
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 1)
    )
    routine.emit(b"\x33\xFE\x54")
    denial_open_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            denial_open_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    # The gate carrier is invisible, so retain the mode-3 flag-1 form that
    # keeps WAIT_DIALOG alive for a hidden owner.
    routine.emit(b"\xF5" + _u16(denial_dialogue_id) + b"\x01\x9C")
    denial_close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            denial_close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(
        atel.set_variable_s16(INTAKE_DIALOG_BUSY_VARIABLE, 0)
    )
    routine.emit(b"\xFE\x53\x00")
    routine.label("entered")
    routine.jump_if_not_equal(
        INTAKE_DOCTOR_DOOR_OPEN_VARIABLE, 1, "allowed"
    )
    routine.jump("follow_open")
    routine.label("allowed")
    routine.emit(_jump(old_action_pc))
    routine.label("follow_open")
    # The physician's return walk deliberately leaves helper entity 31 at the
    # native open endpoint. Drain the player's fresh Cross press, then enter
    # the office directly; rerunning the retail action here would snap the leaf
    # closed and animate it open a second time.
    routine.emit(b"\x33\xFE\x54")
    follow_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            follow_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(base._change_field(*INTAKE_CLINIC_DESTINATION) + b"\x5B")
    return routine.finish()


def _clinic_doctor_init(*, routine_pc: int) -> bytes:
    """Restore a solid physician for every unresolved office substage."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(
        atel.set_variable_s16(CLINIC_DOOR_OPEN_VARIABLE, 0)
    )
    routine.emit(b"\x0B" + base._immediate(CLINIC_DOCTOR_GRAPHIC))
    routine.emit(
        b"\x19"
        + _s16(CLINIC_DOCTOR_POSITION[0])
        + _s16(CLINIC_DOCTOR_POSITION[1])
        + b"\xC0\x1A\x00\x69\x05\x80"
        + b"\xF8\x00\x00\x20\xF8\x07\x04\x00"
        + DOCTOR_RECTANGULAR_BOUNDING_VOLUME
        + DOCTOR_TRANSIT_COLLISION_FLAGS
    )
    routine.emit(
        atel.copy_variable(
            APPOINTMENT_SCRATCH_VARIABLE, APPOINTMENT_OPERAND
        )
    )
    routine.emit(
        atel.variable_math(
            0x3E,
            APPOINTMENT_SCRATCH_VARIABLE,
            _signed_word(APPOINTMENT_ALIAS_MASK),
        )
    )
    routine.jump_if_equal(APPOINTMENT_SCRATCH_VARIABLE, 0, "hidden")
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "hidden")
    routine.emit(_appointment_phase_snapshot_body())
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_ENTERED,
        "visible",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_LEGACY_BRIEFED,
        "visible",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_OFFICE_ACTIVE,
        "visible",
    )
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_RESOLVED,
        "hidden",
    )
    routine.emit(_appointment_stage_snapshot_body())
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_FLEE_PENDING,
        "visible",
    )
    routine.label("hidden")
    routine.emit(b"\x23")
    routine.jump("finish")
    routine.label("visible")
    routine.emit(DOCTOR_STATIONARY_COLLISION_FLAGS)
    routine.emit(b"\x24" + bytes((CLINIC_DOCTOR_ENTITY,)))
    routine.label("finish")
    routine.emit(b"\x00")
    return routine.finish()


def _clinic_security_actor_init(*, entity: int, routine_pc: int) -> bytes:
    """Stage one hidden response actor or restore the final battle tableau."""

    if entity not in CLINIC_SECURITY_ENTITIES:
        raise SurfaceCampaignBuildError(f"Unknown clinic security entity {entity}")
    graphic = (
        CLINIC_SECURITY_GUARD_TARGET_BANK
        if entity in CLINIC_SECURITY_GUARD_ENTITIES
        else CLINIC_SECURITY_CUBE_TARGET_BANK
    )
    final_x, final_z = CLINIC_SECURITY_ROUTES[entity][-1]
    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(b"\x0B" + base._immediate(graphic))
    if entity in CLINIC_SECURITY_GUARD_ENTITIES:
        routine.emit(
            b"\xFE\x15"
            + base._immediate(CLINIC_SECURITY_GUARD_TARGET_BANK)
            + base._immediate(CLINIC_SECURITY_GUARD_PALETTE)
        )
    routine.emit(
        b"\xF8\x00\x00\x20\xF8\x07\x04\x00"
        + b"\x18\x18\x18\x00\x00\x20\x01\x80\x2A"
    )
    routine.emit(_appointment_phase_snapshot_body())
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_OFFICE_ACTIVE,
        "staged_hidden",
    )
    routine.emit(_appointment_stage_snapshot_body())
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_BATTLE_PENDING,
        "staged_hidden",
    )
    routine.emit(
        b"\x19"
        + _s16(final_x)
        + _s16(final_z)
        + b"\xC0\x1A\x00\x69\x05\x80\x5F\x04"
        + b"\x24"
        + bytes((entity,))
        + b"\xFE\x17"
        + bytes((entity, 0xFF))
        + base.mass_driver._wait(4)
    )
    routine.jump("finish")
    routine.label("staged_hidden")
    routine.emit(
        b"\x19"
        + _s16(CLINIC_SECURITY_STAGING_POSITION[0])
        + _s16(CLINIC_SECURITY_STAGING_POSITION[1])
        + b"\xC0\x1A\x00\x69\x05\x80\x23"
    )
    routine.label("finish")
    routine.emit(b"\x00")
    return routine.finish()


def _clinic_security_actor_entrance_body(*, entity: int) -> bytes:
    """Cross the open leaf promptly, face Fei, and publish completion."""

    if entity not in CLINIC_SECURITY_ENTITIES:
        raise SurfaceCampaignBuildError(f"Unknown clinic security entity {entity}")
    delay = CLINIC_SECURITY_ENTRY_DELAYS[entity]
    delay_body = b"" if delay == 0 else base.mass_driver._wait(delay)
    visible_route = CLINIC_SECURITY_ROUTES[entity][1:]
    crossing_route = visible_route[:2]
    formation_route = visible_route[2:]
    if (
        crossing_route[-1] != CLINIC_SECURITY_OVERRIDE_CLEAR_POSITION
        or not formation_route
    ):
        raise SurfaceCampaignBuildError(
            f"Clinic security e{entity} override scope changed"
        )
    return (
        delay_body
        # Move to the last exterior point while still hidden.  The old visible
        # leg began with all four actors stacked at the same narrow apex and
        # could spend every 180-step timeout walking in place behind the leaf.
        + b"\x19"
        + _s16(CLINIC_SECURITY_REVEAL_POSITION[0])
        + _s16(CLINIC_SECURITY_REVEAL_POSITION[1])
        + b"\xC0\x1A\x00"
        # The exterior strip is material 0/0x800000.  This actor-local native
        # override permits only the response actor to cross it; Fei's solid
        # doorway seal and the global walkmesh remain unchanged.
        + b"\x20\x01\x80"
        + CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET
        + b"\x24"
        + bytes((entity,))
        + _actor_waypoint_body(
            crossing_route,
            final_direction=0,
            max_steps=CLINIC_SECURITY_WAYPOINT_MAX_STEPS,
        )
        # OP4B stops within nine units of its target.  The validator proves
        # that complete radius around (0,200) is ordinary interior floor.
        + CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR
        + _actor_waypoint_body(
            formation_route,
            final_direction=4,
            max_steps=CLINIC_SECURITY_WAYPOINT_MAX_STEPS,
        )
        # FE17 computes actor-to-actor yaw at runtime; unlike a shared 5F
        # cardinal pose, this keeps every distinct endpoint aimed at Fei.
        + b"\xFE\x17"
        + bytes((entity, 0xFF))
        + base.mass_driver._wait(4)
        + _set_bit(
            CLINIC_SECURITY_DONE_VARIABLE,
            CLINIC_SECURITY_ENTITIES.index(entity),
        )
        + b"\x00"
    )


def _clinic_security_actor_hide_body() -> bytes:
    """Hide one response actor immediately after the fixed battle returns."""

    return b"\x23\x00"


def _clinic_exit_close_helper(*, routine_pc: int) -> bytes:
    """Reverse the retained 30-frame office-leaf slide at an appended PC."""

    return base.mass_driver._relocatable_static_slide_body(
        routine_pc,
        variable=0x040E,
        iterations=30,
        delta_x=1,
        delta_y=0,
    )


def _clinic_doctor_escape_body() -> bytes:
    """Walk to the leaf, cross it, and visibly close it behind the physician."""

    return (
        # FE7F may reset runtime collision flags without rerunning e16:s0.
        # Reassert the ghost flag so the deliberate player seal remains solid
        # to Fei but cannot hold the fleeing doctor at the threshold.
        DOCTOR_TRANSIT_COLLISION_FLAGS
        + _actor_waypoint_body(
            CLINIC_DOCTOR_ESCAPE_APPROACH_WAYPOINTS,
            final_direction=0,
        )
        + b"\x74\x77\x80"
        + b"\x09"
        + bytes(
            (
                CLINIC_EXIT_HELPER_ENTITY,
                0xC0 | CLINIC_EXIT_HELPER_OPEN_SCRIPT,
            )
        )
        + atel.set_variable_s16(CLINIC_DOOR_OPEN_VARIABLE, 1)
        # Field 352's exterior threshold is deliberately non-walkable.  Use
        # the same actor-local override as retail walk-and-change-field only
        # after the blocking leaf-open helper has finished.
        + CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET
        + _actor_waypoint_body(
            CLINIC_DOCTOR_ESCAPE_THRESHOLD_WAYPOINTS,
            final_direction=0,
            max_steps=CLINIC_DOCTOR_THRESHOLD_WAYPOINT_MAX_STEPS,
        )
        # Keep the physician visible and stationary outside while the leaf
        # closes behind him, then retire the now-occluded sprite.
        + b"\x09"
        + bytes(
            (
                CLINIC_EXIT_HELPER_ENTITY,
                0xC0 | CLINIC_EXIT_HELPER_CLOSE_SCRIPT,
            )
        )
        + atel.set_variable_s16(CLINIC_DOOR_OPEN_VARIABLE, 0)
        + b"\x23"
        + CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR
        + _appointment_stage_body(APPOINTMENT_STAGE_COMPLETE)
    )


def _clinic_doctor_update(
    *,
    briefing_dialogue_id: int,
    security_arrival_dialogue_id: int,
    keycard_dialogue_id: int,
    escape_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Own briefing, security combat, keycard recovery, and doctor escape."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(
        atel.copy_variable(
            APPOINTMENT_SCRATCH_VARIABLE, APPOINTMENT_OPERAND
        )
    )
    routine.emit(
        atel.variable_math(
            0x3E,
            APPOINTMENT_SCRATCH_VARIABLE,
            _signed_word(APPOINTMENT_ALIAS_MASK),
        )
    )
    routine.jump_if_equal(APPOINTMENT_SCRATCH_VARIABLE, 0, "finish")
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "finish")
    routine.emit(_appointment_phase_snapshot_body())
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_ENTERED,
        "briefing",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_LEGACY_BRIEFED,
        "briefing",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_OFFICE_ACTIVE,
        "office_active",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_RESOLVED,
        "resolved",
    )
    routine.jump("finish")

    routine.label("briefing")
    routine.emit(
        base.mass_driver._automatic_dialogue_body(
            (briefing_dialogue_id,),
            routine_pc=routine.pc,
            reset_actor_dialog_state=True,
        )
    )
    # Stage first, phase second, both after WAIT_DIALOG. A tear before the phase
    # write repeats only this harmless briefing; no refusal or fight is lost.
    routine.emit(_appointment_stage_body(APPOINTMENT_STAGE_AWAIT_REFUSAL))
    routine.emit(_appointment_phase_body(APPOINTMENT_PHASE_OFFICE_ACTIVE))
    routine.jump("finish")

    routine.label("office_active")
    routine.emit(_appointment_stage_snapshot_body())
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_SECURITY_PENDING,
        "security_entrance",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_SECURITY_ENTERING,
        "security_entrance",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_BATTLE_PENDING,
        "security_battle",
    )
    # If victory's stage word persisted but its phase word did not, promote to
    # resolved and flee.  Never replay an already-returned fixed battle.
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_FLEE_PENDING,
        "promote_victory",
    )
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_NONE,
        "finish",
    )
    routine.emit(_appointment_stage_body(APPOINTMENT_STAGE_AWAIT_REFUSAL))
    routine.jump("finish")

    routine.label("security_entrance")
    # The refusal action deliberately transfers its control lock to this short
    # entrance cinematic. A field reload at stage 3 or 6 starts here with the
    # physical leaf closed and all four actors hidden at their outside point.
    routine.emit(b"\x33\xFE\x54")
    routine.emit(_appointment_stage_body(APPOINTMENT_STAGE_SECURITY_ENTERING))
    routine.emit(
        atel.set_variable_s16(CLINIC_SECURITY_DONE_VARIABLE, 0)
    )
    routine.emit(b"\x74\x77\x80")
    routine.emit(
        b"\x09"
        + bytes(
            (
                CLINIC_EXIT_HELPER_ENTITY,
                0xC0 | CLINIC_EXIT_HELPER_OPEN_SCRIPT,
            )
        )
    )
    routine.emit(
        atel.set_variable_s16(CLINIC_DOOR_OPEN_VARIABLE, 1)
    )
    for entity in CLINIC_SECURITY_ENTITIES:
        routine.emit(
            b"\x07"
            + bytes((entity, 0x20 | CLINIC_SECURITY_ENTRY_SCRIPT))
        )
    routine.label("wait_for_security")
    routine.jump_if_equal(
        CLINIC_SECURITY_DONE_VARIABLE,
        (1 << len(CLINIC_SECURITY_ENTITIES)) - 1,
        "security_arrived",
    )
    routine.emit(base.mass_driver._yield_tick())
    routine.jump("wait_for_security")
    routine.label("security_arrived")
    routine.emit(
        b"\x09"
        + bytes(
            (
                CLINIC_EXIT_HELPER_ENTITY,
                0xC0 | CLINIC_EXIT_HELPER_CLOSE_SCRIPT,
            )
        )
    )
    routine.emit(
        atel.set_variable_s16(CLINIC_DOOR_OPEN_VARIABLE, 0)
    )
    routine.emit(_appointment_stage_body(APPOINTMENT_STAGE_BATTLE_PENDING))
    routine.jump("security_battle_locked")

    routine.label("security_battle")
    routine.emit(b"\x33\xFE\x54")
    routine.label("security_battle_locked")
    release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_actor_dialogue(security_arrival_dialogue_id))
    routine.emit(base.mass_driver._wait(15))
    routine.emit(base.mass_driver._play_music(0x14))
    routine.emit(
        base.mass_driver._fixed_battle(CLINIC_SECURITY_CONFIGURATION)
    )
    routine.emit(b"\xFE\x7F")
    # The no-Escape formation can return normally only after victory. Commit
    # the single-word victory marker as the first persistent write after FE7F,
    # before either idempotent reward, phase, music restoration, or movement.
    routine.emit(_appointment_stage_body(APPOINTMENT_STAGE_FLEE_PENDING))
    for entity in CLINIC_SECURITY_ENTITIES:
        routine.emit(
            b"\x07"
            + bytes((entity, 0x20 | CLINIC_SECURITY_HIDE_SCRIPT))
        )
    routine.jump_if_bit_clear(
        SECURITY_KEYCARD_OPERAND,
        SECURITY_KEYCARD_MASK,
        "award_keycard",
    )
    routine.jump("finish_victory")

    routine.label("promote_victory")
    routine.jump_if_bit_clear(
        SECURITY_KEYCARD_OPERAND,
        SECURITY_KEYCARD_MASK,
        "award_keycard",
    )
    routine.emit(_appointment_phase_body(APPOINTMENT_PHASE_RESOLVED))
    routine.jump("flee_notice")

    routine.label("resolved")
    routine.emit(_appointment_stage_snapshot_body())
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_FLEE_PENDING,
        "recover_flee",
    )
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_COMPLETE,
        "finish",
    )
    routine.emit(b"\x23")
    routine.jump("finish")

    routine.label("recover_flee")
    routine.jump_if_bit_clear(
        SECURITY_KEYCARD_OPERAND,
        SECURITY_KEYCARD_MASK,
        "award_keycard",
    )
    routine.jump("flee_notice")

    routine.label("award_keycard")
    # Sound 0x37 is the retail item-acquisition chime.  Persist the credential
    # only after the receipt window closes: an interrupted savestate may repeat
    # the harmless receipt, but can never unlock the freight door silently.
    routine.emit(b"\x33\xFE\x54")
    routine.emit(SECURITY_KEYCARD_ACQUIRED_SOUND)
    routine.emit(_actor_dialogue(keycard_dialogue_id))
    routine.emit(
        _set_bit(
            SECURITY_KEYCARD_OPERAND,
            SECURITY_KEYCARD_BIT_INDEX,
        )
    )

    routine.label("finish_victory")
    routine.emit(_appointment_phase_body(APPOINTMENT_PHASE_RESOLVED))
    routine.emit(KRELIAN_LAB_MUSIC_OPCODE)
    routine.emit(b"\xFE\x53")
    routine.jump("flee_notice")

    routine.label("flee_notice")
    routine.emit(
        base.mass_driver._automatic_dialogue_body(
            (escape_dialogue_id,),
            routine_pc=routine.pc,
            reset_actor_dialog_state=True,
        )
    )
    # automatic_dialogue_body has restored control. Only the doctor and native
    # leaf move from this point; Fei remains freely playable during the run.
    routine.emit(_clinic_doctor_escape_body())
    routine.label("finish")
    routine.emit(b"\x00")
    return routine.finish()


def _clinic_doctor_action(
    *,
    first_refusal_dialogue_id: int,
    security_call_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Advance two explicit refusals; slot 1 alone owns the security battle."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    # Phase and substage checks precede FE54, so catching the physician during
    # any of his walks cannot momentarily steal player control.
    routine.emit(_appointment_phase_snapshot_body())
    routine.jump_if_not_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_OFFICE_ACTIVE,
        "finish",
    )
    routine.emit(_appointment_stage_snapshot_body())
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_AWAIT_REFUSAL,
        "first_refusal",
    )
    routine.jump_if_equal(
        APPOINTMENT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_FINAL_WARNING,
        "security_call",
    )
    routine.jump("finish")

    routine.label("first_refusal")
    routine.emit(b"\x33\xFE\x54")
    first_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            first_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_actor_dialogue(first_refusal_dialogue_id))
    first_close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            first_close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_appointment_stage_body(APPOINTMENT_STAGE_FINAL_WARNING))
    routine.emit(b"\xFE\x53\x00")

    routine.label("security_call")
    routine.emit(b"\x33\xFE\x54")
    second_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            second_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_actor_dialogue(security_call_dialogue_id))
    security_close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            security_close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_appointment_stage_body(APPOINTMENT_STAGE_SECURITY_PENDING))

    routine.label("finish")
    routine.emit(b"\x00")
    return routine.finish()


def _clinic_post_escape_field_change_action(*, seal_entity: int) -> bytes:
    """Leave through an already-open leaf without sliding it a second time."""

    return (
        b"\xFE\x54"
        + b"\x09"
        + bytes((seal_entity, 0x24))
        + base._change_field(CLINIC_RETURN_FIELD, CLINIC_RETURN_PARAMETER)
        + b"\x00"
    )


def _clinic_exit_gate_action(
    *,
    native_action_pc: int,
    already_open_action_pc: int,
    insistence_dialogue_id: int,
    escape_in_progress_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Deny departure until victory and select the correct leaf state."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    # Invalid/debug states fail open so a transplanted old savestate cannot be
    # trapped in the office. Valid intake states remain strictly phase-gated.
    routine.emit(
        atel.copy_variable(
            CLINIC_EXIT_SCRATCH_VARIABLE, APPOINTMENT_OPERAND
        )
    )
    routine.emit(
        atel.variable_math(
            0x3E,
            CLINIC_EXIT_SCRATCH_VARIABLE,
            _signed_word(APPOINTMENT_ALIAS_MASK),
        )
    )
    routine.jump_if_equal(CLINIC_EXIT_SCRATCH_VARIABLE, 0, "native_exit")
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "native_exit")
    routine.emit(
        _appointment_phase_snapshot_body(CLINIC_EXIT_SCRATCH_VARIABLE)
    )
    routine.jump_if_equal(
        CLINIC_EXIT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_ENTERED,
        "insist",
    )
    routine.jump_if_equal(
        CLINIC_EXIT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_LEGACY_BRIEFED,
        "insist",
    )
    routine.jump_if_equal(
        CLINIC_EXIT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_OFFICE_ACTIVE,
        "insist",
    )
    routine.jump_if_not_equal(
        CLINIC_EXIT_SCRATCH_VARIABLE,
        APPOINTMENT_PHASE_RESOLVED,
        "native_exit",
    )
    routine.emit(
        _appointment_stage_snapshot_body(CLINIC_EXIT_SCRATCH_VARIABLE)
    )
    routine.jump_if_equal(
        CLINIC_EXIT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_FLEE_PENDING,
        "escaping",
    )
    routine.jump_if_not_equal(
        CLINIC_EXIT_SCRATCH_VARIABLE,
        APPOINTMENT_STAGE_COMPLETE,
        "native_exit",
    )
    routine.jump_if_equal(CLINIC_DOOR_OPEN_VARIABLE, 1, "open_exit")

    routine.label("native_exit")
    routine.emit(_jump(native_action_pc))
    routine.label("open_exit")
    routine.emit(_jump(already_open_action_pc))

    routine.label("insist")
    routine.emit(b"\x33\xFE\x54")
    insist_open_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            insist_open_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_actor_dialogue(insistence_dialogue_id))
    insist_close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            insist_close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(b"\xFE\x53\x00")

    routine.label("escaping")
    routine.emit(b"\x33\xFE\x54")
    escape_open_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            escape_open_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_actor_dialogue(escape_in_progress_dialogue_id))
    escape_close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            escape_close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def _clinic_record_terminal_action(
    *,
    alias_dialogue_ids: Sequence[int],
    missing_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Show Fei's alias-aware live record without mutating clinic progress."""

    if len(alias_dialogue_ids) != len(CHECKIN_ALIASES):
        raise SurfaceCampaignBuildError("Clinic terminal alias count changed")

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(b"\x33\xFE\x54")
    opening_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            opening_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "missing")
    routine.jump_if_bit_clear(
        APPOINTMENT_OPERAND, APPOINTMENT_ALIAS_MASK, "missing"
    )
    routine.emit(_read_character_weight_lbs(PATIENT_CHARACTER_IDS["Fei"]))

    # Alias bits are deliberately tested directly.  Unlike a copied scratch
    # value, these branches cannot be changed by another actor between the
    # field VM's eight-opcode scheduler slices.
    routine.jump_if_bit_clear(APPOINTMENT_OPERAND, 0x8000, "aron")
    routine.jump_if_bit_clear(APPOINTMENT_OPERAND, 0x4000, "noel")
    routine.emit(_actor_dialogue(alias_dialogue_ids[2]))
    routine.jump("finish")

    routine.label("aron")
    routine.emit(_actor_dialogue(alias_dialogue_ids[0]))
    routine.jump("finish")

    routine.label("noel")
    routine.emit(_actor_dialogue(alias_dialogue_ids[1]))
    routine.jump("finish")

    routine.label("missing")
    routine.emit(_actor_dialogue(missing_dialogue_id))

    routine.label("finish")
    closing_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            closing_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def _archive_checkin_action(
    *,
    alias_menu_dialogue_id: int,
    alias_result_dialogue_ids: Sequence[int],
    cancelled_dialogue_id: int,
    repeat_menu_dialogue_id: int,
    patient_dialogue_ids: Sequence[int],
    routine_pc: int,
) -> bytes:
    """Build one-time alias registration plus repeatable patient records.

    Every path first runs the retained retail six-panel opening sequence.  The
    custom registration, vitals, and Exit paths launch the matching native
    closes before restoring control.  The retail binary-code archive menu is
    deliberately unreachable: it is unrelated to intake registration or the
    Quarantine keycard.
    """

    if len(alias_result_dialogue_ids) != len(CHECKIN_ALIASES):
        raise SurfaceCampaignBuildError("Check-in alias result count changed")
    if len(patient_dialogue_ids) != 3:
        raise SurfaceCampaignBuildError("Check-in patient record count changed")

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(b"\x33\xFE\x54")
    release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(ARCHIVE_TERMINAL_NATIVE_SCREEN_OPEN_BODY)
    # D2 snapshots field variables 0x16/0x18 into dialogue parameters 0/1.
    # Format Fei immediately for registration and repeat-Fei; Elly and Citan
    # are formatted only on their selected repeat branches.  Every read stays
    # live, so food-driven changes remain visible.
    routine.emit(_read_character_weight_lbs(PATIENT_CHARACTER_IDS["Fei"]))
    routine.jump_if_bit_clear(STATE_OPERAND, CHECKIN_BIT_MASK, "first_use")
    # V183 set only bit 7.  An alias cannot be reconstructed from shared menu
    # variable 0x0014, so a legacy save returns to the registration choices
    # once instead of silently guessing the name the doctor should call.
    routine.emit(
        atel.copy_variable(
            APPOINTMENT_SCRATCH_VARIABLE, APPOINTMENT_OPERAND
        )
    )
    routine.emit(
        atel.variable_math(
            0x3E,
            APPOINTMENT_SCRATCH_VARIABLE,
            _signed_word(APPOINTMENT_ALIAS_MASK),
        )
    )
    routine.jump_if_equal(APPOINTMENT_SCRATCH_VARIABLE, 0, "first_use")

    # WAIT_DIALOG writes the chosen absolute line to field variable 0x0014.
    # The menu title is line zero, so Fei/Elly/Citan/Exit are 1..4.
    routine.emit(base.mass_driver._choice_dialog(repeat_menu_dialogue_id))
    routine.emit(b"\xA9\x15\x9C")
    for selection, (patient, dialogue_id) in enumerate(
        zip(("Fei", "Elly", "Citan"), patient_dialogue_ids, strict=True),
        start=1,
    ):
        next_label = f"repeat_after_{patient.lower()}"
        routine.jump_if_not_equal(0x0014, selection, next_label)
        if patient != "Fei":
            routine.emit(
                _read_character_weight_lbs(PATIENT_CHARACTER_IDS[patient])
            )
        routine.emit(base.mass_driver._wait())
        routine.emit(_actor_dialogue(dialogue_id))
        routine.jump("finish")
        routine.label(next_label)
    routine.jump("finish")
    routine.label("first_use")
    routine.emit(base.mass_driver._choice_dialog(alias_menu_dialogue_id))
    routine.emit(b"\xA9\x14\x9C")
    for selection, (alias, dialogue_id) in enumerate(
        zip(CHECKIN_ALIASES, alias_result_dialogue_ids, strict=True),
        start=1,
    ):
        next_label = f"first_after_{alias.lower()}"
        routine.jump_if_not_equal(0x0014, selection, next_label)
        # Yield after the choice so its confirming Cross edge cannot dismiss
        # the selected registration report in the same scheduler tick.
        routine.emit(base.mass_driver._wait())
        routine.emit(_actor_dialogue(dialogue_id))
        routine.emit(_appointment_alias_body(selection - 1))
        routine.emit(_set_bit(STATE_OPERAND, CHECKIN_BIT_INDEX))
        routine.jump("finish")
        routine.label(next_label)
    routine.jump_if_not_equal(0x0014, 4, "finish")
    routine.emit(base.mass_driver._wait())
    routine.emit(_actor_dialogue(cancelled_dialogue_id))

    routine.label("finish")
    routine.emit(ARCHIVE_TERMINAL_NATIVE_SCREEN_CLOSE_LAUNCH_BODY)
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def _state_console_action(
    *,
    operand: int,
    bit_index: int,
    dialogue_id: int,
    routine_pc: int,
) -> bytes:
    release_pc = routine_pc + 3
    return (
        b"\x33\xFE\x54"
        + base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + _set_bit(operand, bit_index)
        + b"\x74\x50\x80"
        + b"\xF5"
        + _u16(dialogue_id)
        + b"\x01\x9C\xFE\x53\x00"
    )


def _interface_cutoff_action(
    *,
    interface_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Arm the interface cutoff once without issuing a credential.

    Examination Room C is the campaign's sole Quarantine-keycard writer.  The
    bright field-588 scanner remains useful as an independent, save-safe
    production authorization reached from the Service Manifold.
    """

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(b"\x33\xFE\x54")
    initial_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            initial_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.jump_if_bit_clear(STATE_OPERAND, INTERFACE_BIT_MASK, "arm_cutoff")
    routine.emit(b"\xF5" + _u16(interface_dialogue_id) + b"\x01\x9C")
    routine.jump("finish")

    routine.label("arm_cutoff")
    routine.emit(PROGRESSION_CONFIRM_SOUND)
    routine.emit(b"\xF5" + _u16(interface_dialogue_id) + b"\x01\x9C")
    cutoff_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            cutoff_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_set_bit(STATE_OPERAND, INTERFACE_BIT_INDEX))

    routine.label("finish")
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def _console_init(console: Console) -> bytes:
    """Build a visible-prop-aligned, non-colliding X carrier.

    INIT_ENTITY_NPC supplies an active scheduler class.  Flag 0x2000 selects
    the rectangular action volume; OP20/0x80 makes this carrier a ghost so it
    cannot add invisible collision on top of the authentic console/model.
    """

    return (
        b"\x0B\x00\x80"
        + b"\x19"
        + _s16(console.x)
        + _s16(console.z)
        + b"\xC0\x1A\x00"
        + b"\xF8\x00\x00\x20"
        + (
            b"\xF8\x03\x04\x00"
            if console.requires_facing
            else b"\xF8\x07\x04\x00"
        )
        + b"\x18"
        + bytes(
            (
                console.interaction_half_width,
                console.interaction_half_depth,
                0x64,
                min(console.interaction_half_width, console.interaction_half_depth),
            )
        )
        + b"\x20\x01\x80\x23\x00"
    )


def _ghost_door_controller_init(door: base.DoorController) -> bytes:
    """Recreate one broad door action volume without physical collision."""

    if not all(
        1 <= value <= 0x7F
        for value in (door.interaction_half_width, door.interaction_half_depth)
    ):
        raise SurfaceCampaignBuildError("Door action bounds are outside 1..127")
    if door.carrier_entity is None:
        prefix = b"\x0B\x00\x80"
        position_suffix = b"\xC0\x1A\x00"
        collision_operand = min(
            door.interaction_half_width,
            door.interaction_half_depth,
        )
    else:
        # Reused field directors retain their audited visual/camera setup.
        prefix = door.init_prefix
        position_suffix = b"\xC0"
        collision_operand = 0
    return (
        prefix
        + b"\x19"
        + _s16(door.x)
        + _s16(door.z)
        + position_suffix
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
        # OP20 immediate 1 sets field flag 0x80.  EntityMoveCheck0 ignores
        # such actors, while startScriptsForCollisions still selects script 2.
        + b"\x20\x01\x80"
        + b"\x23\x00"
    )


def _door_seal_bounds(
    door: base.DoorController,
    normal_axis: str,
) -> tuple[int, int]:
    if normal_axis == "x":
        return DOOR_SEAL_NORMAL_HALF_EXTENT, door.interaction_half_depth
    if normal_axis == "z":
        return door.interaction_half_width, DOOR_SEAL_NORMAL_HALF_EXTENT
    raise SurfaceCampaignBuildError(f"Unsupported door normal axis {normal_axis!r}")


def _door_seal_init(
    door: base.DoorController,
    normal_axis: str,
) -> bytes:
    """Build an immovable, action-disabled seal exactly on a door plane."""

    half_width, half_depth = _door_seal_bounds(door, normal_axis)
    return (
        b"\x0B\x00\x80"
        + b"\x19"
        + _s16(door.x)
        + _s16(door.z)
        + b"\xC0\x1A\x00"
        + b"\xF8\x00\x00\x20"
        + b"\xF8\x07\x04\x00"
        + b"\x18"
        + bytes((half_width, half_depth, 0x64, min(half_width, half_depth)))
        + b"\xF8\x00\x10\x00"
        # DISABLE_DIALOG_ACTIVATION suppresses both proximity script 3 and
        # Cross script 2.  The seal therefore cannot steal X from the broad,
        # lower-ID action carrier that occupies the same doorway.
        + b"\x2A"
        + b"\x23\x00"
    )


def _expected_donor_door_controller_init(
    contract: DonorDoorCollisionContract,
) -> bytes:
    """Return the exact v173/v174 donor init that this campaign replaces."""

    body = (
        b"\xBC\x19"
        + _s16(contract.x)
        + _s16(contract.z)
        + b"\xC0"
        + b"\xF8\x00\x00\x20"
        + (
            b""
            if contract.init_state_suffix
            else b"\xF8\x03\x04\x00"
        )
        + b"\x18"
        + bytes(
            (
                contract.interaction_half_width,
                contract.interaction_half_depth,
                0x1E,
                0,
            )
        )
        + contract.init_state_suffix
    )
    immovable = b"\xF8\x00\x10\x00"
    if contract.immovable_precedes_stop:
        return body + immovable + b"\x00"
    # The v173 donor hardening accidentally placed IMMOBILE after a terminal
    # STOP.  Guard both bytes so this repair cannot silently target a changed
    # foundation.
    return body + b"\x00" + immovable + b"\x00"


def _donor_door_action_bounds(
    contract: DonorDoorCollisionContract,
) -> tuple[int, int]:
    """Resolve the campaign X target independently of its frozen source init."""

    return (
        contract.interaction_half_width
        if contract.action_half_width is None
        else contract.action_half_width,
        contract.interaction_half_depth
        if contract.action_half_depth is None
        else contract.action_half_depth,
    )


def _ghost_donor_door_controller_init(
    contract: DonorDoorCollisionContract,
) -> bytes:
    """Keep the native rectangular X shell, but remove facing and collision."""

    action_half_width, action_half_depth = _donor_door_action_bounds(contract)
    return (
        b"\xBC\x19"
        + _s16(contract.x)
        + _s16(contract.z)
        + b"\xC0"
        + b"\xF8\x00\x00\x20"
        + b"\xF8\x07\x04\x00"
        + b"\x18"
        + bytes(
            (
                action_half_width,
                action_half_depth,
                0x1E,
                0,
            )
        )
        + contract.init_state_suffix
        # A field-flag 0x80 actor is ignored by EntityMoveCheck0 but remains
        # eligible for startScriptsForCollisions and therefore deliberate X.
        + b"\x20\x01\x80\x00"
    )


def _donor_circle_seal_init(contract: DonorDoorCollisionContract) -> bytes:
    """Create a round, immovable, action-disabled diagonal doorway seal."""

    seal_x, seal_z = _donor_seal_position(contract)
    seal_radius = contract.seal_radius
    if not 1 <= seal_radius <= 0x7F:
        raise SurfaceCampaignBuildError("Donor seal radius is outside 1..127")
    return (
        b"\x0B\x00\x80"
        + b"\x19"
        + _s16(seal_x)
        + _s16(seal_z)
        + b"\xC0\x1A\x00"
        # Circle mode is selected by explicitly clearing field flag 0x2000.
        + b"\xF8\x04\x00\x20"
        + b"\xF8\x07\x04\x00"
        # X/Z rectangular operands are intentionally zero.  The fourth OP18
        # operand is doubled by the engine into m1E_collisionRadius.
        + b"\x18\x00\x00\x64"
        + bytes((seal_radius,))
        + b"\xF8\x00\x10\x00"
        + b"\x2A\x23\x00"
    )


def _donor_seal_position(
    contract: DonorDoorCollisionContract,
) -> tuple[int, int]:
    """Resolve the physical seal independently of its ghost X carrier."""

    if (
        contract.circular_seal_position is not None
        and contract.rectangular_seal_position is not None
    ):
        raise SurfaceCampaignBuildError(
            "Donor seal cannot have circular and rectangular positions"
        )
    if contract.circular_seal_position is not None:
        if contract.rectangular_seal_half_extents is not None:
            raise SurfaceCampaignBuildError(
                "Circular donor seal cannot have rectangular half-extents"
            )
        return contract.circular_seal_position
    if contract.rectangular_seal_position is not None:
        return contract.rectangular_seal_position
    return (contract.x, contract.z)


def _donor_rectangular_seal_init(
    contract: DonorDoorCollisionContract,
) -> bytes:
    """Create one thin, immovable, action-disabled rectangular seal."""

    position = contract.rectangular_seal_position
    half_extents = contract.rectangular_seal_half_extents
    if position is None or half_extents is None:
        raise SurfaceCampaignBuildError(
            "Rectangular donor seal lacks a position or half-extents"
        )
    half_width, half_depth = half_extents
    if not 1 <= half_width <= 0x7F or not 1 <= half_depth <= 0x7F:
        raise SurfaceCampaignBuildError(
            "Rectangular donor seal half-extents are outside 1..127"
        )
    return (
        b"\x0B\x00\x80"
        + b"\x19"
        + _s16(position[0])
        + _s16(position[1])
        + b"\xC0\x1A\x00"
        # Rectangle mode is selected by explicitly setting field flag 0x2000.
        + b"\xF8\x00\x00\x20"
        + b"\xF8\x07\x04\x00"
        + b"\x18"
        + bytes((half_width, half_depth, 0x64, min(half_extents)))
        + b"\xF8\x00\x10\x00"
        + b"\x2A\x23\x00"
    )


def _donor_seal_init(contract: DonorDoorCollisionContract) -> bytes:
    """Dispatch to the one shape explicitly frozen by a donor contract."""

    rectangular = (
        contract.rectangular_seal_position,
        contract.rectangular_seal_half_extents,
    )
    if rectangular == (None, None):
        return _donor_circle_seal_init(contract)
    if None in rectangular:
        raise SurfaceCampaignBuildError(
            "Donor rectangular seal contract is only partially specified"
        )
    return _donor_rectangular_seal_init(contract)


def _validate_exam_return_x_only(
    editor: ScriptEditor,
    contract: DonorDoorCollisionContract,
    scene: int,
) -> ScriptEditor:
    """Prove that a field-352 return can run only from deliberate Cross."""

    cavity = editor.bytecode[
        EXAM_RETURN_RETIRED_CAVITY_PC:EXAM_RETURN_RETIRED_CAVITY_END_PC
    ]
    expected_cavity = (
        exam_rooms.EMPTY_ROOM_TERMINAL_AUX_CAVITY
        if scene == 567
        else (
            exam_rooms.TERMINAL_AUX_CAVITY
            if scene in exam_rooms.SCENES
            else EXAM_RETURN_RETIRED_CAVITY_SOURCE
        )
    )
    if (
        contract.controller_entity != exam_rooms.RETURN_CONTROLLER
        or editor.get_script_pointer(0, 1) != empty_clinic567.SHARED_STOP_PC
        or cavity != expected_cavity
    ):
        raise SurfaceCampaignBuildError(
            "Examination-room X-only foundation changed"
        )

    allowed_cavity_pointers = (
        {
            (entity, 0): pc
            for entity, pc in zip(
                exam_rooms.TERMINAL_AUX_ENTITIES,
                exam_rooms.TERMINAL_AUX_INIT_PCS,
                strict=True,
            )
        }
        if scene in FIELD352_SIDE_TERMINAL_SCENES
        else {}
    )
    # The old story routine remains unreachable.  Only e4:s0 and e5:s0 may
    # enter the replacement initializers in occupied rooms; no update, action,
    # door, or automatic slot may enter this span.
    for entity in range(editor.entity_count):
        for script_index in range(32):
            pointer = editor.get_script_pointer(entity, script_index)
            if (
                EXAM_RETURN_RETIRED_CAVITY_PC
                <= pointer
                < EXAM_RETURN_RETIRED_CAVITY_END_PC
                and allowed_cavity_pointers.get((entity, script_index))
                != pointer
            ):
                raise SurfaceCampaignBuildError(
                    "Active examination-room pointer enters the retired cavity"
                )
    if scene in FIELD352_SIDE_TERMINAL_SCENES:
        terminal_action_pc = (
            exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC
            if scene == 567
            else exam_rooms.TERMINAL_ACTION_PC
        )
        if scene in (591, 592, 594) and editor.get_script_pointer(exam_rooms.TERMINAL_ENTITY, 2) != terminal_action_pc:
            from modules.soylent_system.tools import surface_soylent_clinical_discoveries as discoveries
            terminal_action_pc = discoveries.TERMINAL_ACTION_PCS[scene]
            expected_action = discoveries.expected_terminal_action(scene)
            if (editor.get_script_pointer(exam_rooms.TERMINAL_ENTITY, 2) != terminal_action_pc
                    or editor.bytecode[terminal_action_pc:terminal_action_pc + len(expected_action)] != expected_action):
                raise SurfaceCampaignBuildError("Examination-room discovery action changed")
        for (entity, script_index), pointer in allowed_cavity_pointers.items():
            if (
                editor.get_script_pointer(entity, script_index) != pointer
                or editor.get_script_pointer(entity, 2)
                != terminal_action_pc
            ):
                raise SurfaceCampaignBuildError(
                    "Examination-room side-bank carrier pointer changed"
                )
        if scene == 567:
            third_entity = exam_rooms.EMPTY_ROOM_TERMINAL_ENTITIES[2]
            if (
                editor.get_script_pointer(third_entity, 0)
                != exam_rooms.EMPTY_ROOM_TERMINAL_INIT_PC
                or editor.get_script_pointer(third_entity, 2)
                != exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC
                or editor.bytecode[
                    exam_rooms.EMPTY_ROOM_TERMINAL_INIT_PC :
                    exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC
                ]
                != exam_rooms.TERMINAL_INIT_BODIES[2]
            ):
                raise SurfaceCampaignBuildError(
                    "Field 567 third side-bank carrier changed"
                )
    return editor


DONOR_SEAL_RELEASE_ACTION = b"\x20\x01\x80\x00"


def _clinic_native_field_change_action(
    *,
    destination_field: int,
    destination_parameter: int,
    seal_entity: int | None = None,
) -> bytes:
    """Retain field 352's sound and blocking native door-leaf helper."""

    seal_release = (
        b"" if seal_entity is None else b"\x09" + bytes((seal_entity, 0x24))
    )
    return (
        b"\xFE\x54\x74\x77\x80"
        + b"\x09"
        + bytes((CLINIC_EXIT_HELPER_ENTITY, 0xC4))
        + seal_release
        + base._change_field(destination_field, destination_parameter)
        + b"\x00"
    )


def _donor_native_field_change_action(
    *,
    helper_entity: int,
    player_script: int,
    destination_field: int,
    destination_parameter: int,
    seal_entity: int | None = None,
    routine_pc: int | None = None,
    arm_appointment: bool = False,
) -> bytes:
    """Encode one retail donor leaf/player/change-field action."""

    if seal_entity is not None and not 0 <= seal_entity <= 0xFF:
        raise SurfaceCampaignBuildError("Donor seal entity is outside one byte")
    seal_release = (
        b"" if seal_entity is None else b"\x09" + bytes((seal_entity, 0x24))
    )
    prefix = (
        b"\xFE\x54"
        + b"\x09" + bytes((helper_entity, 0x24))
        + seal_release
        + b"\x07\x01" + bytes((0x20 | player_script,))
        + b"\x26\x0A\x80"
    )
    if arm_appointment:
        if routine_pc is None:
            raise SurfaceCampaignBuildError(
                "Appointment-arming transition requires its absolute PC"
            )
        prefix += _appointment_arm_guarded_body(routine_pc + len(prefix))
    return (
        prefix
        + base._change_field(destination_field, destination_parameter)
        + b"\x5B"
    )


def _donor_fresh_cross_field_change_action(
    *,
    helper_entity: int,
    player_script: int,
    destination_field: int,
    destination_parameter: int,
    routine_pc: int,
    seal_entity: int | None = None,
) -> bytes:
    """Encode the guarded field-565 action with an optional seal release."""

    release_pc = routine_pc + 3
    seal_release = (
        b"" if seal_entity is None else b"\x09" + bytes((seal_entity, 0x24))
    )
    return (
        b"\x33\xFE\x54"
        + base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + b"\x09" + bytes((helper_entity, 0x24))
        + seal_release
        + b"\x07\x01" + bytes((0x20 | player_script,))
        + b"\x26\x0A\x80"
        + base._change_field(destination_field, destination_parameter)
        + b"\x5B"
    )


def _field567_fresh_cross_field_change_action(
    *,
    async_helper_entity: int,
    blocking_helper_entity: int,
    player_script: int,
    destination_field: int,
    destination_parameter: int,
    routine_pc: int,
    seal_entity: int,
) -> bytes:
    """Preserve both native field-567 leaves around a fresh-X transition."""

    release_pc = routine_pc + 3
    return (
        b"\x33\xFE\x54"
        + base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        # The surgery-room bulkheads use two different leaf actors.  The first
        # starts asynchronously and the second blocks until both meet their
        # open endpoints, exactly as in the retail action.
        + b"\x07" + bytes((async_helper_entity, 0x24))
        + b"\x09" + bytes((blocking_helper_entity, 0x24))
        + b"\x09" + bytes((seal_entity, 0x24))
        + b"\x07\x01" + bytes((0x20 | player_script,))
        + b"\x26\x0A\x80"
        + base._change_field(destination_field, destination_parameter)
        + b"\x5B"
    )


def _field565_internal_gate_action_with_seal(seal_entity: int) -> bytes:
    """Preserve e11's native open path and release both collision actors."""

    return (
        bytes.fromhex("FE 54 36 00 04 09 14 24")
        + b"\x09" + bytes((seal_entity, 0x24))
        + bytes.fromhex("80 98 00 00 80 20 01 80 2A FE 53 00")
    )


def _field565_gate_clearance_trampoline(
    seal_entity: int,
    return_pc: int,
) -> bytes:
    """Release e12's seal/current carrier, then rejoin native success."""

    return (
        b"\x09" + bytes((seal_entity, 0x24))
        + b"\x20\x01\x80\x01"
        + _u16(return_pc)
    )


def _field565_internal_keycard_gate_action(
    *,
    seal_entity: int,
    denial_dialogue_id: int,
    briefing_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Unlock e12 with the keycard and retain its authentic sliding leaf.

    The five-tone interaction now lives in its physical annex, field 589.
    Until that authorization is captured, the newly opened passage gives a
    concise objective briefing.  The briefing is intentionally not persistent:
    the physical gate remains open for the current field load, and after a
    reload it can be shown again until the tone credential exists.
    """

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.jump_if_bit_clear(
        SECURITY_KEYCARD_OPERAND,
        SECURITY_KEYCARD_MASK,
        "locked",
    )
    routine.emit(b"\x33\xFE\x54")
    release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.jump_if_bit_clear(TONE_OPERAND, TONE_MASK, "briefing")
    routine.jump("open")

    routine.label("briefing")
    routine.emit(
        b"\xF5" + _u16(briefing_dialogue_id) + b"\x01\x9C"
    )

    routine.label("open")
    routine.emit(b"\x09\x15\x24")
    routine.emit(b"\x09" + bytes((seal_entity, 0x24)))
    # Match the retained neighboring gate: once its leaf and physical seal are
    # released, disable this X carrier so the animation cannot be replayed
    # while the passage is already open.
    routine.emit(b"\x20\x01\x80\x2A\xFE\x53\x00")

    routine.label("locked")
    routine.emit(_repeatable_dialogue_action(denial_dialogue_id, routine.pc))
    return routine.finish()


def _append_dialogue(
    dialogue: bytes,
    texts: Sequence[str],
    *,
    width: int = 58,
    height: int = 4,
) -> tuple[bytes, tuple[int, ...]]:
    parsed = parse_dialogue(dialogue)
    specs = [
        DialogueBlockSpec(block.block_id, block.width, block.height, block.text)
        for block in parsed.blocks
    ]
    ids: list[int] = []
    for text in texts:
        ids.append(len(specs))
        specs.append(DialogueBlockSpec(len(specs), width, height, text))
    rebuilt = encode_dialogue(specs)
    reparsed = parse_dialogue(rebuilt)
    for before, after in zip(parsed.blocks, reparsed.blocks, strict=False):
        if (before.width, before.height, before.payload) != (
            after.width,
            after.height,
            after.payload,
        ):
            raise SurfaceCampaignBuildError("Existing dialogue changed while appending")
    return rebuilt, tuple(ids)


def _replace_dialogue_texts(dialogue: bytes, replacements: Mapping[int, str]) -> bytes:
    parsed = parse_dialogue(dialogue)
    unknown = set(replacements) - {block.block_id for block in parsed.blocks}
    if unknown:
        raise SurfaceCampaignBuildError(f"Dialogue replacements are missing IDs {unknown}")
    specs = [
        DialogueBlockSpec(
            block.block_id,
            block.width,
            block.height,
            replacements.get(block.block_id, block.text),
        )
        for block in parsed.blocks
    ]
    return encode_dialogue(specs)


def _replace_dialogue_blocks_same_size(
    dialogue: bytes,
    replacements: Mapping[int, tuple[int, int, str]],
    *,
    padding_id: int,
) -> bytes:
    """Replace retired blocks while preserving the resident component span."""

    parsed = parse_dialogue(dialogue)
    known = {block.block_id for block in parsed.blocks}
    unknown = set(replacements) - known
    if unknown or padding_id not in known or padding_id in replacements:
        raise SurfaceCampaignBuildError(
            "Same-size dialogue replacement IDs are invalid"
        )
    specs = [
        DialogueBlockSpec(
            block.block_id,
            replacements.get(
                block.block_id,
                (block.width, block.height, block.text),
            )[0],
            replacements.get(
                block.block_id,
                (block.width, block.height, block.text),
            )[1],
            replacements.get(
                block.block_id,
                (block.width, block.height, block.text),
            )[2],
        )
        for block in parsed.blocks
    ]
    rebuilt = encode_dialogue(specs)
    padding = len(dialogue) - len(rebuilt)
    if padding < 0:
        raise SurfaceCampaignBuildError(
            "Clinic record blocks exceed the resident dialogue component"
        )
    if padding:
        pad = specs[padding_id]
        specs[padding_id] = DialogueBlockSpec(
            pad.block_id,
            pad.width,
            pad.height,
            pad.text + "<Close>" * padding,
        )
        rebuilt = encode_dialogue(specs)
    if len(rebuilt) != len(dialogue):
        raise SurfaceCampaignBuildError(
            "Clinic record dialogue padding did not preserve component size"
        )
    return rebuilt


def _campaign_dialogue_layout_issues(block: DialogueBlock) -> tuple[str, ...]:
    """Return exact retail-grid violations for one authored dialogue block."""

    if block.width <= 0 or block.height <= 0:
        return ("nonpositive window dimensions",)

    capacity = block.width | 1
    page_id = 1
    line_id = 1
    line_units = 0
    line_overflow_reported = False
    line_text: list[str] = []
    issues: list[str] = []
    text = block.text
    position = 0

    def append_rendered(value: str) -> None:
        nonlocal line_overflow_reported, line_units
        for character in value:
            code = PLAIN_ENCODE.get(character)
            if code is None:
                issues.append(f"unsupported rendered character {character!r}")
                continue
            line_units += 2 if code <= 0x63 else 3
            line_text.append(character)
        if line_units > capacity and not line_overflow_reported:
            issues.append(
                f"page {page_id} line {line_id} uses {line_units} font units "
                f"but capacity is {capacity}: {''.join(line_text)!r}"
            )
            line_overflow_reported = True

    while position < len(text):
        character = text[position]
        if character == "\n":
            line_id += 1
            line_units = 0
            line_overflow_reported = False
            line_text.clear()
            if line_id > block.height:
                issues.append(
                    f"page {page_id} has {line_id} lines but height is {block.height}"
                )
            position += 1
            continue
        if character != "<":
            append_rendered(character)
            position += 1
            continue

        end = text.find(">", position + 1)
        if end == -1:
            issues.append(f"unterminated control at text offset {position}")
            break
        token = text[position + 1 : end]
        if token == "New":
            page_id += 1
            line_id = 1
            line_units = 0
            line_overflow_reported = False
            line_text.clear()
        elif token in ("Close", "Wait") or re.fullmatch(r"Delay:\d{1,3}", token):
            pass
        elif token in CHARACTER_IDS:
            append_rendered(token)
        else:
            issues.append(f"unmeasurable control <{token}>")
        position = end + 1

    if not text.endswith("<Close>") or text.count("<Close>") != 1:
        issues.append("authored block must have one terminal <Close>")
    return tuple(issues)


def _normalized_authored_dialogue_words(text: str) -> str:
    """Collapse layout controls so a rewrap cannot split or alter a word."""

    normalized = text.replace("<New>", " ").replace("<Close>", " ")
    if "<" in normalized or ">" in normalized:
        raise SurfaceCampaignBuildError(
            "Authored-dialogue semantic comparison found an opaque control"
        )
    return " ".join(normalized.split())


def _layout_campaign_dialogue(dialogue: bytes, scene: int) -> bytes:
    """Apply and verify the exact word-safe layout for one authored room."""

    expected_identity = CAMPAIGN_PRE_LAYOUT_DIALOGUE_IDENTITIES.get(scene)
    owned_ids = CAMPAIGN_AUTHORED_DIALOGUE_IDS.get(scene)
    replacements = CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS.get(scene)
    if expected_identity is None or owned_ids is None or replacements is None:
        raise SurfaceCampaignBuildError(
            f"Field {scene} lacks a complete authored-dialogue layout contract"
        )
    actual_identity = (len(dialogue), _sha256(dialogue))
    if actual_identity != expected_identity:
        raise SurfaceCampaignBuildError(
            f"Field {scene} pre-layout dialogue changed: {actual_identity}"
        )

    parsed = parse_dialogue(dialogue)
    if any(block_id >= len(parsed.blocks) for block_id in owned_ids):
        raise SurfaceCampaignBuildError(
            f"Field {scene} authored-dialogue IDs left the component"
        )
    overflow_issues = {
        block_id: _campaign_dialogue_layout_issues(parsed.blocks[block_id])
        for block_id in owned_ids
    }
    overflow_ids = {
        block_id for block_id, issues in overflow_issues.items() if issues
    }
    if overflow_ids != set(replacements):
        raise SurfaceCampaignBuildError(
            f"Field {scene} overflow set {sorted(overflow_ids)} does not match "
            f"repair set {sorted(replacements)}"
        )
    overflow_line_count = sum(len(overflow_issues[block_id]) for block_id in overflow_ids)
    if overflow_line_count != CAMPAIGN_V178_OVERFLOW_LINES_BY_SCENE[scene]:
        raise SurfaceCampaignBuildError(
            f"Field {scene} has {overflow_line_count} overwidth lines instead of "
            f"{CAMPAIGN_V178_OVERFLOW_LINES_BY_SCENE[scene]}"
        )
    for block_id, replacement_text in replacements.items():
        if (scene, block_id) == (621, INTAKE_BOY_DIALOGUE_ID):
            continue
        if _normalized_authored_dialogue_words(
            parsed.blocks[block_id].text
        ) != _normalized_authored_dialogue_words(replacement_text):
            raise SurfaceCampaignBuildError(
                f"Field {scene} dialogue {block_id} rewrap changed its wording"
            )

    rebuilt = _replace_dialogue_texts(dialogue, replacements)
    reparsed = parse_dialogue(rebuilt)
    for block_id in owned_ids:
        issues = _campaign_dialogue_layout_issues(reparsed.blocks[block_id])
        if issues:
            raise SurfaceCampaignBuildError(
                f"Field {scene} dialogue {block_id} violates the retail grid: "
                + "; ".join(issues)
            )
    for block_id, expected_text in replacements.items():
        if reparsed.blocks[block_id].text != expected_text:
            raise SurfaceCampaignBuildError(
                f"Field {scene} dialogue {block_id} failed its exact rewrap"
            )
    return rebuilt


def _validate_campaign_dialogue_contracts() -> None:
    if (
        CHECKIN_ALIASES != ("Aron Voss", "Noel Ardan", "Kiro Dalen")
        or tuple(alias.split()[0] for alias in CHECKIN_ALIASES)
        != ("Aron", "Noel", "Kiro")
        or any(len(alias.split()) != 2 for alias in CHECKIN_ALIASES)
        or APPOINTMENT_ALIAS_CODES != (0x4000, 0x8000, 0xC000)
        or any(
            {"fei", "fong", "wong"} & set(alias.casefold().split())
            for alias in CHECKIN_ALIASES
        )
    ):
        raise SurfaceCampaignBuildError("Intake alias identity contract changed")

    # The appointment blocks are appended after the core authored inventory
    # inventory.  Audit them independently so longer aliases cannot silently
    # overflow the five-line retail dialogue grid.
    alias_dialogues = (
        CHECKIN_ALIAS_MENU_DIALOGUE,
        *CHECKIN_ALIAS_RESULT_DIALOGUES,
        *CLINIC_RECORD_DIALOGUES,
        LEGACY_ALIAS_CONFIRM_DIALOGUE,
        *DOCTOR_CALL_DIALOGUES,
        *DOCTOR_INSTRUCTION_DIALOGUES,
    )
    for text in alias_dialogues:
        measurable_text = text.replace("<Opcode:01:FF>", "")
        measurable_text = re.sub(
            r"<Opcode:0A:(?:00|01|02)>", "255", measurable_text
        )
        measurable = parse_dialogue(
            encode_dialogue(
                (DialogueBlockSpec(0, 58, 5, measurable_text),)
            )
        ).blocks[0]
        issues = _campaign_dialogue_layout_issues(measurable)
        if issues:
            raise SurfaceCampaignBuildError(
                f"Intake alias dialogue exceeds the retail grid: {issues}"
            )

    if (
        set(CAMPAIGN_AUTHORED_DIALOGUE_IDS)
        != set(CAMPAIGN_PRE_LAYOUT_DIALOGUE_IDENTITIES)
        or set(CAMPAIGN_AUTHORED_DIALOGUE_IDS)
        != set(CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS)
        or set(CAMPAIGN_AUTHORED_DIALOGUE_IDS)
        != set(CAMPAIGN_V178_OVERFLOW_LINES_BY_SCENE)
    ):
        raise SurfaceCampaignBuildError("Authored-dialogue room contracts disagree")
    if sum(len(ids) for ids in CAMPAIGN_AUTHORED_DIALOGUE_IDS.values()) != 75:
        raise SurfaceCampaignBuildError("Authored-dialogue block inventory changed")
    if (
        sum(
            len(replacements)
            for replacements in CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS.values()
        )
        != 48
    ):
        raise SurfaceCampaignBuildError("Authored-dialogue repair inventory changed")
    for scene, replacements in CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS.items():
        if not set(replacements).issubset(CAMPAIGN_AUTHORED_DIALOGUE_IDS[scene]):
            raise SurfaceCampaignBuildError(
                f"Field {scene} dialogue repair targets an unowned retail block"
            )
    if (
        CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS[621].get(INTAKE_BOY_DIALOGUE_ID)
        != INTAKE_BOY_DIALOGUE
    ):
        raise SurfaceCampaignBuildError("Field 621 intake-boy dialogue changed")


def _prepare_campaign_dialogue_layout_field(
    prepared: base.PreparedField,
) -> base.PreparedField:
    scene = prepared.spec.identity.scene
    if scene not in CAMPAIGN_AUTHORED_DIALOGUE_IDS:
        return prepared
    return _rebuild_field(
        prepared,
        editor=ScriptEditor(prepared.components[SCRIPT_INDEX]),
        dialogue=_layout_campaign_dialogue(prepared.components[7], scene),
        role_suffix="word-safe authored dialogue pagination",
    )


def _prepare_campaign_dialogue_layout_donor(
    prepared: base.PreparedDonorField,
) -> base.PreparedDonorField:
    scene = prepared.identity.scene
    if scene not in CAMPAIGN_AUTHORED_DIALOGUE_IDS:
        return prepared
    return _rebuild_donor(
        prepared,
        editor=ScriptEditor(prepared.components[SCRIPT_INDEX]),
        dialogue=_layout_campaign_dialogue(prepared.components[7], scene),
        role_suffix="word-safe authored dialogue pagination",
    )


def _validate_console_points(prepared: base.PreparedField, consoles: Sequence[Console]) -> None:
    triangles = base._walkmesh_layer(prepared.components[1], 0)
    for console in consoles:
        if console.triangle >= len(triangles) or not base._point_inside_triangle(
            (console.x, console.z), triangles[console.triangle]
        ):
            raise SurfaceCampaignBuildError(
                f"Field {prepared.spec.identity.scene} console "
                f"({console.x},{console.z}) left triangle {console.triangle}"
            )


def _insert_controller_records(
    header: bytes,
    *,
    old_entity_count: int,
    consoles: Sequence[Console],
) -> bytes:
    if len(header) < 0x190:
        raise SurfaceCampaignBuildError("Campaign field header is truncated")
    actor_count = struct.unpack_from("<H", header, 0x18C)[0]
    if len(header) != 0x190 + actor_count * 16 or old_entity_count > actor_count:
        raise SurfaceCampaignBuildError("Campaign actor table boundary changed")
    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(actor_count)
    ]
    inserted = [
        base.mass_driver._field_actor_record(0x01E0, console.x, console.z, 0)
        for console in consoles
    ]
    records[old_entity_count:old_entity_count] = inserted
    result = bytearray(header[:0x190] + b"".join(records))
    struct.pack_into("<H", result, 0x18C, len(records))
    return bytes(result)


def _insert_transfer_north_door_leaf_records(
    header: bytes,
    *,
    old_entity_count: int,
) -> bytes:
    """Duplicate field 623's blue south leaves at the dark north threshold."""

    if len(header) < 0x190:
        raise SurfaceCampaignBuildError("Field 623 north-door header is truncated")
    actor_count = struct.unpack_from("<H", header, 0x18C)[0]
    if len(header) != 0x190 + actor_count * 16:
        raise SurfaceCampaignBuildError("Field 623 north-door actor table changed")
    if (
        old_entity_count != TRANSFER_NORTH_DOOR_HELPER_ENTITIES[0]
        or TRANSFER_NORTH_DOOR_HELPER_ENTITIES
        != tuple(
            range(
                old_entity_count,
                old_entity_count + len(TRANSFER_NORTH_DOOR_HELPER_ENTITIES),
            )
        )
        or old_entity_count > actor_count
    ):
        raise SurfaceCampaignBuildError(
            "Field 623 north-door helpers left the ATEL/header boundary"
        )

    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(actor_count)
    ]
    duplicated: list[bytes] = []
    for source_entity, helper_entity, model_index in zip(
        TRANSFER_NORTH_DOOR_SOURCE_HELPER_ENTITIES,
        TRANSFER_NORTH_DOOR_HELPER_ENTITIES,
        TRANSFER_NORTH_DOOR_MODEL_INDICES,
        strict=True,
    ):
        if source_entity >= old_entity_count or helper_entity < old_entity_count:
            raise SurfaceCampaignBuildError(
                "Field 623 north-door source/helper ordering changed"
            )
        source = records[source_entity]
        flags, rx, ry, rz, x, y, z, source_model = struct.unpack(
            "<Hhhh hhh H", source
        )
        if (
            flags != 0x0290
            or (rx, ry, rz) != (0, 0, 0)
            or (x, y, z) != (0, 0, 0)
            or source_model != model_index
        ):
            raise SurfaceCampaignBuildError(
                f"Field 623 blue door source e{source_entity} changed"
            )
        active = bytearray(source)
        struct.pack_into("<h", active, 4, TRANSFER_NORTH_DOOR_ROTATION_Y)
        struct.pack_into("<h", active, 12, TRANSFER_NORTH_DOOR_ORIGIN_Z)
        duplicated.append(bytes(active))

    records[old_entity_count:old_entity_count] = duplicated
    result = bytearray(header[:0x190] + b"".join(records))
    struct.pack_into("<H", result, 0x18C, len(records))
    return bytes(result)


def _extend_for_consoles(
    prepared: base.PreparedField | base.PreparedDonorField,
    consoles: Sequence[Console],
) -> tuple[ScriptEditor, bytes, tuple[int, ...], int]:
    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    old_count = editor.entity_count
    header = _insert_controller_records(
        prepared.header,
        old_entity_count=old_count,
        consoles=consoles,
    )
    editor = ScriptEditor(
        base.mass_driver._extend_atel_entity_table(
            editor.to_bytes(), old_count + len(consoles)
        )
    )
    stop_pc = editor.append_raw_routine(b"\x00")
    entities = tuple(range(old_count, old_count + len(consoles)))
    for entity in entities:
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)
    return editor, header, entities, stop_pc


def _rebuild_field(
    prepared: base.PreparedField,
    *,
    editor: ScriptEditor,
    header: bytes | None = None,
    dialogue: bytes | None = None,
    component_updates: Mapping[int, bytes] | None = None,
    role_suffix: str,
) -> base.PreparedField:
    components = list(prepared.components)
    components[SCRIPT_INDEX] = editor.to_bytes()
    changed = [SCRIPT_INDEX]
    if dialogue is not None and dialogue != components[7]:
        components[7] = dialogue
        changed.append(7)
    for index, replacement in (component_updates or {}).items():
        if index in (SCRIPT_INDEX, 7) or not 0 <= index < len(components):
            raise SurfaceCampaignBuildError(
                f"Invalid field component replacement index {index}"
            )
        if replacement != components[index]:
            components[index] = replacement
            changed.append(index)
    bundle = build_field_preserving(
        prepared.bundle,
        components,
        tuple(changed),
        compact_changed=True,
        replacement_header=header,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise SurfaceCampaignBuildError(
            f"Field {prepared.spec.identity.scene} campaign rebuild failed round trip"
        )
    spec = replace(
        prepared.spec,
        role=prepared.spec.role + "; " + role_suffix,
        patched_script_size=len(components[SCRIPT_INDEX]),
        patched_script_sha256=_sha256(components[SCRIPT_INDEX]),
        patched_bundle_size=len(bundle),
        patched_bundle_sha256=_sha256(bundle),
    )
    return base.PreparedField(
        spec,
        prepared.source_bundle,
        prepared.graphics,
        reparsed.header,
        tuple(components),
        bundle,
    )


def _prepare_door_clearance(prepared: base.PreparedField) -> base.PreparedField:
    """Split every Surface door's X target from its physical collision seal."""

    scene = prepared.spec.identity.scene
    doors = base.NATIVE_DOOR_CONTROLLERS.get(scene)
    contracts = SURFACE_DOOR_COLLISION_CONTRACTS.get(scene)
    if doors is None or contracts is None or len(doors) != len(contracts):
        raise SurfaceCampaignBuildError(
            f"Field {scene} lacks a complete door-collision contract"
        )

    triangles = base._walkmesh_layer(prepared.components[1], 0)
    for door, contract in zip(doors, contracts, strict=True):
        if (
            contract.controller_entity < 0
            or contract.controller_entity >= ScriptEditor(
                prepared.components[SCRIPT_INDEX]
            ).entity_count
            or door.triangle >= len(triangles)
            or not base._point_inside_triangle(
                (door.x, door.z), triangles[door.triangle]
            )
        ):
            raise SurfaceCampaignBuildError(
                f"Field {scene} door at ({door.x},{door.z}) left its contract"
            )

    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    old_count = editor.entity_count
    # Each thin seal needs its own model-less actor record at the current ATEL
    # boundary.  Later retail static records retain their exact bytes/order.
    header = _insert_controller_records(
        prepared.header,
        old_entity_count=old_count,
        consoles=doors,
    )
    editor = ScriptEditor(
        base.mass_driver._extend_atel_entity_table(
            editor.to_bytes(), old_count + len(doors)
        )
    )
    stop_pc = editor.append_raw_routine(b"\x00")
    seal_entities = tuple(range(old_count, old_count + len(doors)))
    for entity in seal_entities:
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)

    for door, contract, seal_entity in zip(
        doors, contracts, seal_entities, strict=True
    ):
        editor.append_and_repoint(
            contract.controller_entity,
            0,
            _ghost_door_controller_init(door),
        )
        editor.append_and_repoint(
            seal_entity,
            0,
            _door_seal_init(door, contract.normal_axis),
        )

    return _rebuild_field(
        prepared,
        editor=editor,
        header=header,
        role_suffix=(
            "broad ghost X targets with thin action-disabled doorway seals"
        ),
    )


def _intake_exam_room_two_axis_slide_body(
    *,
    start_x: int,
    start_z: int,
    delta_x: int,
    delta_z: int,
    iterations: int,
) -> bytes:
    """Move Intake's diagonal panel into its matching diagonal wall pocket.

    The shared native helper deliberately accepts movement on exactly one
    world axis.  Door A is the one rotated wall panel in this installation,
    so its visually correct open vector advances two units on both axes.  Keep
    the same finite, unrolled OP19/WAIT-0 timing as every other promoted panel.
    """

    if (delta_x, delta_z) not in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
        raise SurfaceCampaignBuildError(
            "Intake diagonal door must move two units on both axes"
        )
    if not 1 <= iterations <= base.mass_driver.DOOR_ANIMATION_GRACE_FRAMES:
        raise SurfaceCampaignBuildError(
            "Intake diagonal door slide duration is invalid"
        )
    end_x = start_x + delta_x * iterations
    end_z = start_z + delta_z * iterations
    if not all(
        -0x8000 <= value <= 0x7FFF
        for value in (start_x, start_z, end_x, end_z)
    ):
        raise SurfaceCampaignBuildError(
            "Intake diagonal door slide leaves signed world coordinates"
        )

    body = bytearray()
    for step in range(1, iterations + 1):
        body.extend(
            b"\x19"
            + _s16(start_x + delta_x * step)
            + _s16(start_z + delta_z * step)
            + b"\xC0\x26\x00\x80"
        )
    body.append(0x00)
    return bytes(body)


def _carve_intake_exam_room_wall_model(model: bytes) -> bytes:
    """Cut three exact apertures from Intake's native textured wall model.

    The retail wall represents each proposed bay with a lower ``-88..0`` FT4
    and an upper ``-147..-88`` FT4.  Removing the lower polygon alone would
    leave 28 units of the opening covered, so the upper polygon is cropped to
    ``-147..-116`` with UVs interpolated at the new edge.  New edge vertices
    are deliberately appended rather than moving shared retail vertices used
    by the neighbouring wall panels.
    """

    if (
        len(model) != 16_292
        or _sha256(model)
        != "cd68f3829845bf5f13e38c2f221c914ad0de88f45bea26f2fdc04fc739a10182"
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 native wall model changed before aperture carving"
        )

    block = 0x10
    vertex_count, primitive_count, mesh_count = struct.unpack_from(
        "<HHH", model, block + 2
    )
    vertex_offset, normal_offset, mesh_offset, display_offset = (
        struct.unpack_from("<IIII", model, block + 8)
    )
    if (
        (vertex_count, primitive_count, mesh_count)
        != (654, 578, 3)
        or (vertex_offset, normal_offset, mesh_offset, display_offset)
        != (0x48, 0x48, 0x14B8, 0x26D4)
        or struct.unpack_from("<I", model, block + 0x34)[0] != 0x5520
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 native wall block left its audited layout"
        )

    vertices = tuple(
        struct.unpack_from("<hhhh", model, vertex_offset + index * 8)
        for index in range(vertex_count)
    )
    new_edge_vertices = (
        (1821, -116, 441, 0),
        (1821, -116, 352, 0),
        (1821, -116, 882, 0),
        (1821, -116, 793, 0),
        (1645, -116, 1307, 0),
        (1707, -116, 1245, 0),
    )

    groups: list[tuple[int, int, tuple[tuple[int, int, int, int], ...]]] = []
    cursor = mesh_offset
    for _group_index in range(mesh_count):
        primitive_type, unknown, count = struct.unpack_from("<BBH", model, cursor)
        cursor += 4
        indices = tuple(
            struct.unpack_from("<HHHH", model, cursor + index * 8)
            for index in range(count)
        )
        cursor += count * 8
        groups.append((primitive_type, unknown, indices))
    if (
        cursor != display_offset
        or tuple((kind, unknown, len(indices)) for kind, unknown, indices in groups)
        != ((0x05, 0x77, 122), (0x0C, 0x77, 22), (0x0D, 0x77, 434))
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 native wall mesh groups left their audited layout"
        )

    removed_quads = {
        44: (20, 17, 16, 15),
        55: (33, 32, 31, 30),
        63: (46, 45, 47, 44),
    }
    cropped_quads = {
        45: ((17, 21, 15, 14), (654, 21, 655, 14)),
        54: ((32, 34, 30, 29), (656, 34, 657, 29)),
        62: ((45, 49, 44, 48), (658, 49, 659, 48)),
    }
    ft4_indices = groups[2][2]
    for ordinal, expected in removed_quads.items():
        if ft4_indices[ordinal] != expected:
            raise SurfaceCampaignBuildError(
                "Field 621 wall aperture quad indices changed"
            )
    for ordinal, (expected, _replacement) in cropped_quads.items():
        if ft4_indices[ordinal] != expected:
            raise SurfaceCampaignBuildError(
                "Field 621 wall lintel-cap indices changed"
            )
    carved_ft4 = tuple(
        cropped_quads[ordinal][1]
        if ordinal in cropped_quads
        else indices
        for ordinal, indices in enumerate(ft4_indices)
        if ordinal not in removed_quads
    )
    carved_groups = (*groups[:2], (0x0D, 0x77, carved_ft4))
    mesh_data = b"".join(
        struct.pack("<BBH", kind, unknown, len(indices))
        + b"".join(struct.pack("<HHHH", *item) for item in indices)
        for kind, unknown, indices in carved_groups
    )

    old_cap_packets = {
        45: bytes.fromhex("00 00 00 2D C0 66 D6 66 C0 85 D6 85"),
        54: bytes.fromhex("00 00 00 2D C0 66 D6 66 C0 85 D6 85"),
        62: bytes.fromhex("00 00 00 2D 01 24 01 0F 20 24 20 0F"),
    }
    new_cap_packets = {
        45: bytes.fromhex("00 00 00 2D CA 66 D6 66 CA 85 D6 85"),
        54: bytes.fromhex("00 00 00 2D CA 66 D6 66 CA 85 D6 85"),
        62: bytes.fromhex("00 00 00 2D 01 1A 01 0F 20 1A 20 0F"),
    }
    command_sizes = {0x25: 8, 0x28: 4, 0x2D: 12, 0xC4: 4, 0xC8: 4}
    command_counts: dict[int, int] = {}
    display_parts: list[bytes] = []
    ft4_ordinal = 0
    cursor = display_offset
    while cursor < len(model):
        if cursor + 4 > len(model):
            raise SurfaceCampaignBuildError(
                "Field 621 wall display list ends inside a command"
            )
        command = model[cursor + 3]
        try:
            size = command_sizes[command]
        except KeyError as exc:
            raise SurfaceCampaignBuildError(
                f"Unexpected field 621 wall display command 0x{command:02X}"
            ) from exc
        packet = model[cursor : cursor + size]
        if len(packet) != size:
            raise SurfaceCampaignBuildError(
                "Field 621 wall display command is truncated"
            )
        command_counts[command] = command_counts.get(command, 0) + 1
        if command == 0x2D:
            if ft4_ordinal in removed_quads:
                pass
            elif ft4_ordinal in cropped_quads:
                if packet != old_cap_packets[ft4_ordinal]:
                    raise SurfaceCampaignBuildError(
                        "Field 621 wall lintel-cap UVs changed"
                    )
                display_parts.append(new_cap_packets[ft4_ordinal])
            else:
                display_parts.append(packet)
            ft4_ordinal += 1
        else:
            display_parts.append(packet)
        cursor += size
    if command_counts != {0xC4: 8, 0xC8: 12, 0x25: 122, 0x28: 22, 0x2D: 434}:
        raise SurfaceCampaignBuildError(
            "Field 621 wall display-list inventory changed"
        )

    all_vertices = vertices + new_edge_vertices
    vertex_data = b"".join(struct.pack("<hhhh", *vertex) for vertex in all_vertices)
    new_mesh_offset = vertex_offset + len(vertex_data)
    new_display_offset = new_mesh_offset + len(mesh_data)
    result = bytearray(model[:vertex_offset])
    struct.pack_into("<H", result, block + 2, len(all_vertices))
    struct.pack_into("<H", result, block + 4, primitive_count - len(removed_quads))
    struct.pack_into("<I", result, block + 0x10, new_mesh_offset)
    struct.pack_into("<I", result, block + 0x14, new_display_offset)
    struct.pack_into(
        "<I",
        result,
        block + 0x34,
        0x5520 - len(removed_quads) * 0x28,
    )
    result.extend(vertex_data)
    result.extend(mesh_data)
    result.extend(b"".join(display_parts))
    built = bytes(result)
    if (
        len(built) != INTAKE_EXAM_ROOM_WALL_MODEL_SIZE
        or _sha256(built) != INTAKE_EXAM_ROOM_WALL_MODEL_SHA256
    ):
        raise SurfaceCampaignBuildError(
            "Intake examination-room wall carve is not deterministic: "
            f"{len(built)} bytes, SHA-256 {_sha256(built)}"
        )
    return built


def _remove_intake_black_camera_occluders(model: bytes) -> bytes:
    """Make Intake's solid-black ceiling fascia non-rendering in place.

    Model 2 has four black F3 corner caps and 134 black F4 fascia faces in
    mesh groups 0 and 2.  At the user's Door-A and Door-B camera angles those
    native foreground faces project across the party as a large black ribbon.
    Degenerate only their index records; the textured FT3/FT4 groups, display
    packets, primitive counts, model size, and runtime allocations stay fixed.
    """

    if (
        len(model) != INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SIZE
        or _sha256(model) != INTAKE_EXAM_ROOM_NATIVE_OCCLUDER_MODEL_SHA256
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 native camera-occluder model changed"
        )

    block = 0x10
    vertex_count, primitive_count, mesh_count = struct.unpack_from(
        "<HHH", model, block + 2
    )
    vertex_offset, normal_offset, mesh_offset, display_offset = (
        struct.unpack_from("<IIII", model, block + 8)
    )
    if (
        (vertex_count, primitive_count, mesh_count) != (213, 208, 4)
        or (vertex_offset, normal_offset, mesh_offset, display_offset)
        != (0x48, 0x48, 0x6F0, 0xD80)
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 native camera-occluder layout changed"
        )

    rebuilt = bytearray(model)
    cursor = mesh_offset
    inventory: list[tuple[int, int, int]] = []
    degenerate_groups = {0, 2}
    for group_index in range(mesh_count):
        primitive_type, unknown, count = struct.unpack_from(
            "<BBH", model, cursor
        )
        inventory.append((primitive_type, unknown, count))
        cursor += 4
        for _primitive_index in range(count):
            if group_index in degenerate_groups:
                rebuilt[cursor : cursor + 8] = bytes(8)
            cursor += 8
    if (
        cursor != display_offset
        or tuple(inventory)
        != (
            (0x04, 0x77, 4),
            (0x05, 0x77, 6),
            (0x0C, 0x77, 134),
            (0x0D, 0x77, 64),
        )
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 camera-occluder mesh inventory changed"
        )

    built = bytes(rebuilt)
    if _sha256(built) != INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SHA256:
        raise SurfaceCampaignBuildError(
            "Field 621 camera-occluder removal is not deterministic"
        )
    return built


def _build_intake_exam_room_threshold_model() -> bytes:
    """Clone retail model 19's visible floor apron into model slot 20.

    Retail model 19 gives the original e24 door one textured FT4 floor apron
    extending 44 units beyond its leaf.  This normalized clone keeps that same
    single whole-width primitive.  Splitting it into two lateral halves made
    the nearer half sort in front of a closed leaf under the PlayStation's
    ordering-table renderer, producing the persistent lower-left wedge.  Each
    static node rotates local +Z onto the far side of its added aperture; local
    -Z is the accessible hall and remains empty.  The far-depth V endpoint is
    clamped to row 0x8D, preserving the cyan shadow gradient while excluding
    the source texture's near-black rows 0x8E..0x95.  Fourteen retained
    untextured F3 slots stay degenerate so the 396-byte model keeps its exact
    0x140 GPU-packet allocation without any degenerate textured face or
    vertical rear plane.
    """

    vertices = (
        (0, 0, 0, 0),
        (0, 0, 44, 0),
        (44, 0, 0, 0),
        (44, 0, 44, 0),
        (89, 0, 0, 0),
        (89, 0, 44, 0),
        *((0, 0, 0, 0),) * 9,
    )
    floor_quads = ((0, 1, 4, 5),)
    inert_triangles = ((0, 0, 0, 0),) * 14
    vertex_offset = 0x48
    vertex_data = b"".join(
        struct.pack("<hhhh", *vertex) for vertex in vertices
    )
    mesh_offset = vertex_offset + len(vertex_data)
    mesh_data = (
        struct.pack("<BBH", 0x0D, 0x77, len(floor_quads))
        + b"".join(struct.pack("<HHHH", *quad) for quad in floor_quads)
        + struct.pack("<BBH", 0x04, 0x77, len(inert_triangles))
        + b"".join(
            struct.pack("<HHHH", *triangle) for triangle in inert_triangles
        )
    )
    display_offset = mesh_offset + len(mesh_data)
    # Exact model-19 e24 texture state and U span.  The normalized local frame
    # runs from the leaf at z=0 toward the far side at z=44, and V224 caps that
    # depth at the texture's cyan-shadow row rather than sampling its black
    # tail.  The single FT4 restores the retail primitive topology while its
    # texture page, CLUT, footprint, and packet allocation stay unchanged.
    display_data = bytes.fromhex(
        "A8 00 00 C4 00 79 00 C8 "
        "00 00 00 2D 97 89 97 8D B6 89 B6 8D"
    ) + bytes((0x00, 0x00, 0x00, 0x20)) * len(inert_triangles)

    result = bytearray(vertex_offset)
    struct.pack_into("<I", result, 0, 1)
    block = 0x10
    struct.pack_into("<H", result, block + 2, len(vertices))
    struct.pack_into(
        "<H", result, block + 4, len(floor_quads) + len(inert_triangles)
    )
    struct.pack_into("<H", result, block + 6, 2)
    struct.pack_into("<I", result, block + 8, vertex_offset)
    struct.pack_into("<I", result, block + 0x0C, vertex_offset)
    struct.pack_into("<I", result, block + 0x10, mesh_offset)
    struct.pack_into("<I", result, block + 0x14, display_offset)
    struct.pack_into("<hhh", result, block + 0x20, 0, 0, 0)
    struct.pack_into("<hhh", result, block + 0x28, 89, 0, 44)
    struct.pack_into("<I", result, block + 0x34, 0x140)
    result.extend(vertex_data)
    result.extend(mesh_data)
    result.extend(display_data)
    result.extend(bytes(INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SIZE - len(result)))
    built = bytes(result)
    if (
        len(built) != INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SIZE
        or _sha256(built) != INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SHA256
    ):
        raise SurfaceCampaignBuildError(
            "Intake examination-room threshold model is not deterministic"
        )
    return built


def _install_intake_exam_room_geometry(models: bytes) -> bytes:
    """Carve doors, remove black occluders, and append threshold model 20."""

    try:
        entries = base.mass_driver._indexed_bundle_entries(models)
    except base.mass_driver.DungeonBuildError as exc:
        raise SurfaceCampaignBuildError(
            f"Field 621 model archive is invalid: {exc}"
        ) from exc
    if (
        len(entries) != INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX
        or (len(models), _sha256(models))
        != (
            38_904,
            "26e5118ef296640624c742a2283f7b3e55f1253adaeda568016a6636792ef0a2",
        )
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 native model inventory changed before wall carving"
        )
    carved_wall = _carve_intake_exam_room_wall_model(
        entries[INTAKE_EXAM_ROOM_WALL_MODEL_INDEX]
    )
    occluder_free = _remove_intake_black_camera_occluders(
        entries[INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX]
    )
    rebuilt_entries = list(entries)
    rebuilt_entries[INTAKE_EXAM_ROOM_WALL_MODEL_INDEX] = carved_wall
    rebuilt_entries[INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX] = occluder_free
    rebuilt = base.mass_driver._rebuild_indexed_bundle(
        models,
        (*rebuilt_entries, _build_intake_exam_room_threshold_model()),
    )
    reparsed = base.mass_driver._indexed_bundle_entries(rebuilt)
    if (
        reparsed[INTAKE_EXAM_ROOM_WALL_MODEL_INDEX] != carved_wall
        or reparsed[INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX] != occluder_free
        or any(
            reparsed[index] != entry
            for index, entry in enumerate(entries)
            if index
            not in (
                INTAKE_EXAM_ROOM_WALL_MODEL_INDEX,
                INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX,
            )
        )
        or reparsed[-1] != _build_intake_exam_room_threshold_model()
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 geometry cleanup changed unrelated native models"
        )
    return rebuilt


def _insert_intake_exam_room_door_records(
    header: bytes,
    *,
    old_entity_count: int,
) -> bytes:
    """Insert three controls/leaves and append three static dark reveals."""

    if len(header) < 0x190:
        raise SurfaceCampaignBuildError(
            "Field 621 examination-door header is truncated"
        )
    actor_count = struct.unpack_from("<H", header, 0x18C)[0]
    if (
        len(header) != 0x190 + actor_count * 16
        or old_entity_count != INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES[0]
        or INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES
        != tuple(range(old_entity_count, old_entity_count + 3))
        or INTAKE_EXAM_ROOM_HELPER_ENTITIES
        != tuple(range(old_entity_count + 3, old_entity_count + 6))
        or not old_entity_count < actor_count
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 examination doors left the ATEL/static boundary"
        )

    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(actor_count)
    ]
    controller_records = [
        base.mass_driver._field_actor_record(0x01E0, door.x, door.z, 0)
        for door in INTAKE_EXAM_ROOM_DOORS
    ]
    helper_records = [
        struct.pack(
            "<Hhhh hhh H",
            INTAKE_EXAM_ROOM_MODEL_FLAGS,
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
        ) in INTAKE_EXAM_ROOM_MODEL_PLACEMENTS
    ]
    records[old_entity_count:old_entity_count] = [
        *controller_records,
        *helper_records,
    ]
    if tuple(range(len(records), len(records) + 3)) != (
        INTAKE_EXAM_ROOM_THRESHOLD_HEADER_ENTITIES
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 threshold aprons left their frozen static-node boundary"
        )
    records.extend(
        struct.pack(
            "<Hhhh hhh H",
            INTAKE_EXAM_ROOM_THRESHOLD_MODEL_FLAGS,
            0,
            yaw,
            0,
            origin_x,
            origin_y,
            origin_z,
            INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX,
        )
        for yaw, origin_x, origin_y, origin_z in (
            INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS
        )
    )
    result = bytearray(header[:0x190] + b"".join(records))
    struct.pack_into("<H", result, 0x18C, len(records))
    return bytes(result)


def _install_intake_exam_room_doors(
    prepared: base.PreparedField,
) -> base.PreparedField:
    """Add p7--p9 and three keycard-gated animated examination doors."""

    if prepared.spec.identity.scene != 621:
        raise SurfaceCampaignBuildError(
            "Intake examination-door installation requires field 621"
        )
    if (
        INTAKE_EXAM_ROOM_LOCK_DIALOGUE_ID
        != INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID
    ):
        raise SurfaceCampaignBuildError(
            "Intake examination doors lost the shared keycard lock dialogue"
        )
    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    old_entity_count = editor.entity_count
    if old_entity_count != INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES[0]:
        raise SurfaceCampaignBuildError(
            "Field 621 examination doors no longer begin after door clearance"
        )

    triangles = base._walkmesh_layer(prepared.components[1], 0)
    for door in INTAKE_EXAM_ROOM_DOORS:
        if door.triangle >= len(triangles) or not base._point_inside_triangle(
            (door.x, door.z), triangles[door.triangle]
        ):
            raise SurfaceCampaignBuildError(
                f"Field 621 examination door ({door.x},{door.z}) left "
                f"triangle {door.triangle}"
            )
    models = base.mass_driver._indexed_bundle_entries(prepared.components[2])
    if any(
        placement[0] >= len(models)
        for placement in INTAKE_EXAM_ROOM_MODEL_PLACEMENTS
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 no longer contains the selected existing door models"
        )
    models_with_thresholds = _install_intake_exam_room_geometry(
        prepared.components[2]
    )

    original_entries = tuple(
        base.mass_driver._read_field_entry(editor.to_bytes(), parameter)
        for parameter in range(INTAKE_EXAM_ROOM_ENTRY_PARAMETERS[0])
    )
    try:
        script = base.mass_driver._install_field_entry_additions(
            editor.to_bytes(),
            INTAKE_EXAM_ROOM_ENTRY_ADDITIONS,
            INTAKE_EXAM_ROOM_ENTRY_RESUME_PC,
        )
    except base.mass_driver.DungeonBuildError as exc:
        raise SurfaceCampaignBuildError(
            f"Field 621 p7-p9 installation failed: {exc}"
        ) from exc
    editor = ScriptEditor(script)
    if tuple(
        base.mass_driver._read_field_entry(editor.to_bytes(), parameter)
        for parameter in range(INTAKE_EXAM_ROOM_ENTRY_PARAMETERS[0])
    ) != original_entries or tuple(
        base.mass_driver._read_field_entry(editor.to_bytes(), parameter)
        for parameter in INTAKE_EXAM_ROOM_ENTRY_PARAMETERS
    ) != INTAKE_EXAM_ROOM_ENTRY_ADDITIONS:
        raise SurfaceCampaignBuildError(
            "Field 621 p7-p9 installation changed an existing arrival"
        )
    source_init_pc = editor.get_script_pointer(0, 0)
    if editor.bytecode[source_init_pc] != 0xBC:
        raise SurfaceCampaignBuildError(
            "Field 621 relocated initializer no longer begins with BC"
        )

    header = _insert_intake_exam_room_door_records(
        prepared.header,
        old_entity_count=old_entity_count,
    )
    editor = ScriptEditor(
        base.mass_driver._extend_atel_entity_table(
            editor.to_bytes(),
            old_entity_count
            + len(INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES)
            + len(INTAKE_EXAM_ROOM_HELPER_ENTITIES),
        )
    )
    stop_pc = editor.append_raw_routine(b"\x00")
    for entity in (
        *INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES,
        *INTAKE_EXAM_ROOM_HELPER_ENTITIES,
    ):
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)

    for (
        door,
        animation,
        controller_entity,
        helper_entity,
        placement,
    ) in zip(
        INTAKE_EXAM_ROOM_DOORS,
        INTAKE_EXAM_ROOM_ANIMATIONS,
        INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES,
        INTAKE_EXAM_ROOM_HELPER_ENTITIES,
        INTAKE_EXAM_ROOM_MODEL_PLACEMENTS,
        strict=True,
    ):
        editor.append_and_repoint(
            controller_entity,
            0,
            _ghost_door_controller_init(door),
        )
        editor.append_and_repoint(helper_entity, 0, b"\xBC\x2A\x00")
        (
            _model_index,
            _yaw,
            origin_x,
            _origin_y,
            origin_z,
            delta_x,
            delta_z,
        ) = placement
        if delta_x and delta_z:
            slide = _intake_exam_room_two_axis_slide_body(
                start_x=origin_x,
                start_z=origin_z,
                delta_x=delta_x,
                delta_z=delta_z,
                iterations=INTAKE_EXAM_ROOM_SLIDE_FRAMES,
            )
        else:
            slide = base.mass_driver._world_position_static_slide_body(
                start_x=origin_x,
                start_z=origin_z,
                delta_x=delta_x,
                delta_z=delta_z,
                iterations=INTAKE_EXAM_ROOM_SLIDE_FRAMES,
            )
        editor.append_and_repoint(helper_entity, 4, slide)

        unlocked_action_pc = editor.bytecode_size
        unlocked_action = base._animated_door_transition_action(
            door,
            animation,
            unlocked_action_pc,
        )
        if unlocked_action.count(
            bytes((0x74, INTAKE_EXAM_ROOM_SOUND_ID, 0x80))
        ) != 1:
            raise SurfaceCampaignBuildError(
                f"Field 621 examination door e{controller_entity} sound changed"
            )
        if editor.append_raw_routine(unlocked_action) != unlocked_action_pc:
            raise SurfaceCampaignBuildError(
                f"Field 621 examination door e{controller_entity} action moved"
            )
        gate_pc = editor.bytecode_size
        gate = _intake_freight_keycard_gate_action(
            dialogue_id=INTAKE_EXAM_ROOM_LOCK_DIALOGUE_ID,
            unlocked_action_pc=unlocked_action_pc,
            routine_pc=gate_pc,
        )
        if editor.append_and_repoint(controller_entity, 2, gate) != gate_pc:
            raise SurfaceCampaignBuildError(
                f"Field 621 examination door e{controller_entity} gate moved"
            )

    rebuilt = _rebuild_field(
        prepared,
        editor=editor,
        header=header,
        component_updates={2: models_with_thresholds},
        role_suffix=(
            "three security-keycard examination bays with existing Solaris "
            "panels, native textured threshold aprons, camera-safe open "
            "apertures, and reciprocal p7-p8-p9 arrivals"
        ),
    )
    spec = replace(
        rebuilt.spec,
        entry_edits=(
            *rebuilt.spec.entry_edits,
            *INTAKE_EXAM_ROOM_ENTRY_EDITS,
        ),
        edges=(
            *rebuilt.spec.edges,
            *INTAKE_EXAM_ROOM_EDGES,
        ),
    )
    base.validate_walkmesh_contract(spec, rebuilt.components[1])
    return replace(rebuilt, spec=spec)


def _rebuild_donor(
    prepared: base.PreparedDonorField,
    *,
    editor: ScriptEditor,
    header: bytes | None = None,
    dialogue: bytes | None = None,
    role_suffix: str,
    entry_triangles: tuple[tuple[int, int], ...] | None = None,
) -> base.PreparedDonorField:
    components = list(prepared.components)
    components[SCRIPT_INDEX] = editor.to_bytes()
    changed = [SCRIPT_INDEX]
    if dialogue is not None and dialogue != components[7]:
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
        raise SurfaceCampaignBuildError(
            f"Donor {prepared.identity.scene} campaign rebuild failed round trip"
        )
    return base.PreparedDonorField(
        prepared.identity,
        prepared.role + "; " + role_suffix,
        prepared.source_bundle,
        prepared.graphics,
        reparsed.header,
        tuple(components),
        bundle,
        prepared.entry_triangles if entry_triangles is None else entry_triangles,
    )


def _load_campaign_music_assets(
    source_disc: Path | str,
) -> dict[int, bytes]:
    """Load and freeze the Disc 2 assets selected by music ID ``0x3D``."""

    image = Mode2Image(source_disc)
    entries = image.read_index()
    directories = image.read_directories()
    if MUSIC_DIRECTORY >= len(directories):
        raise SurfaceCampaignBuildError(
            f"Music directory 0x{MUSIC_DIRECTORY:02X} is absent"
        )
    first = directories[MUSIC_DIRECTORY].first_file
    if first < 0:
        raise SurfaceCampaignBuildError(
            f"Music directory 0x{MUSIC_DIRECTORY:02X} is absent on Disc 2"
        )

    result: dict[int, bytes] = {}
    for local_file, expected in KRELIAN_LAB_MUSIC_ASSET_IDENTITIES.items():
        fat_index = directory_file_fat_index(first, local_file)
        if not 0 <= fat_index < len(entries):
            raise SurfaceCampaignBuildError(
                f"Krelian Lab music file 0x{local_file:02X} resolved outside the FAT"
            )
        data = image.extract_entry(entries[fat_index])
        actual = (len(data), _sha256(data))
        if actual != expected:
            raise SurfaceCampaignBuildError(
                f"Krelian Lab music file 0x{local_file:02X} changed: {actual}"
            )
        result[local_file] = data
    return result


def _validate_no_deathblow_level_requirements(
    source_disc: Path | str,
) -> bytes:
    """Freeze the Perfect Works level-one learning tables retained by V205."""

    image = Mode2Image(source_disc)
    entries = image.read_index()
    fat_index = DEATHBLOW_LEVEL_RESOURCE_CANONICAL_ID - 5
    if not 0 <= fat_index < len(entries):
        raise SurfaceCampaignBuildError(
            "Deathblow-level resource lies outside the Disc 2 FAT"
        )
    resource = image.extract_entry(entries[fat_index])
    if (
        len(resource) != DEATHBLOW_LEVEL_RESOURCE_SIZE
        or _sha256(resource) != DEATHBLOW_LEVEL_RESOURCE_SHA256
    ):
        raise SurfaceCampaignBuildError(
            "Surface deathblows require the checked Perfect Works level tables"
        )
    if struct.unpack_from("<4I", resource, 4) != DEATHBLOW_LEVEL_ARCHIVE_OFFSETS:
        raise SurfaceCampaignBuildError("Deathblow-level archive offsets changed")
    start, end = DEATHBLOW_LEVEL_ARCHIVE_OFFSETS[:2]
    decoded, _consumed = base.mass_driver._decode_lzss_complete_groups(
        resource[start:end] + bytes(16)
    )
    if (
        len(decoded) != DEATHBLOW_LEVEL_FILE0_SIZE
        or _sha256(decoded) != DEATHBLOW_LEVEL_FILE0_SHA256
    ):
        raise SurfaceCampaignBuildError("Deathblow-level table decode changed")

    native_profiles = tuple(
        profile for profile in deathblows.DEATHBLOW_PROFILES if profile.full_mask
    )
    if len(native_profiles) != len(DEATHBLOW_LEVEL_TABLE_OFFSETS):
        raise SurfaceCampaignBuildError("Deathblow profile/table count changed")
    for profile, offset in zip(
        native_profiles,
        DEATHBLOW_LEVEL_TABLE_OFFSETS,
        strict=True,
    ):
        count = len(profile.command_names)
        if (
            decoded[offset : offset + count] != bytes((1,)) * count
            or decoded[offset + count] not in (0x00, 0xFF)
        ):
            raise SurfaceCampaignBuildError(
                f"{profile.character} no longer has level-one deathblow gates"
            )
    return decoded


def _validate_clinic_security_resources(
    source_disc: Path | str,
    *,
    resource_overrides: Mapping[int, bytes] | None = None,
) -> None:
    """Freeze the final Disc 2 resources used by the clinic battle.

    A composed build may source fields from a clean image while another
    module installs one of the already-normalized battle resources in the
    final image.  ``resource_overrides`` lets that composition validate the
    exact bytes it will install; standalone builds continue to validate the
    source image itself.
    """

    image = Mode2Image(source_disc)
    entries = image.read_index()
    overrides = {} if resource_overrides is None else dict(resource_overrides)
    unknown = set(overrides) - set(CLINIC_SECURITY_NORMALIZED_CD2_RESOURCES)
    if unknown:
        raise SurfaceCampaignBuildError(
            "Unknown clinic security resource overrides: "
            + ", ".join(str(value) for value in sorted(unknown))
        )
    if any(not isinstance(data, bytes) for data in overrides.values()):
        raise SurfaceCampaignBuildError(
            "Clinic security resource overrides must be immutable bytes"
        )
    for canonical_id, (
        role,
        expected_size,
        expected_sha256,
    ) in CLINIC_SECURITY_NORMALIZED_CD2_RESOURCES.items():
        fat_index = canonical_id - 5
        if not 0 <= fat_index < len(entries):
            raise SurfaceCampaignBuildError(
                f"Clinic security resource {canonical_id} ({role}) lies "
                "outside the Disc 2 FAT"
            )
        data = (
            overrides[canonical_id]
            if canonical_id in overrides
            else image.extract_entry(entries[fat_index])
        )
        actual = (len(data), _sha256(data))
        expected = (expected_size, expected_sha256)
        if actual != expected:
            raise SurfaceCampaignBuildError(
                f"Normalized Disc 2 clinic security resource {canonical_id} "
                f"({role}) changed: {actual}"
            )


def _install_campaign_music(script: bytes, scene: int) -> ScriptEditor:
    """Select the native field-565 lab cue once from every room initializer.

    For sixteen rooms a seven-byte trampoline keeps ``BC`` first, executes
    ``PLAY_MUSIC 0x3D``, then jumps into the complete original initializer
    immediately after its own ``BC``.  Its native branches and terminal STOP
    therefore remain authoritative.  Field 565 already owns the requested
    ``PLAY_MUSIC 0x3D`` selector naturally, so it is retained byte-for-byte
    rather than acquiring a duplicate selector.  Logical field 567 now clones
    the Ethos infirmary and therefore receives the ordinary wrapper.

    The field engine compares the requested ID with ``currentlyPlayingMusic``
    during field initialization.  Equal IDs leave the loaded sequence in
    place, so putting this selector in all eighteen rooms also covers direct
    loads and save-state entry without restarting music on normal transitions.
    """

    expected_identity = CAMPAIGN_PRE_MUSIC_SCRIPT_IDENTITIES.get(scene)
    expected_entry_pc = CAMPAIGN_MUSIC_SOURCE_ENTRY_PCS.get(scene)
    if expected_identity is None or expected_entry_pc is None:
        raise SurfaceCampaignBuildError(
            f"Field {scene} is outside the campaign music room set"
        )
    actual_identity = (len(script), _sha256(script))
    if actual_identity != expected_identity:
        raise SurfaceCampaignBuildError(
            f"Field {scene} pre-music ATEL identity changed: {actual_identity}"
        )

    editor = ScriptEditor(script)
    entry_pc = editor.get_script_pointer(0, 0)
    if entry_pc != expected_entry_pc or editor.bytecode[entry_pc] != 0xBC:
        raise SurfaceCampaignBuildError(
            f"Field {scene} entity-zero initializer changed from "
            f"0x{expected_entry_pc:04X}/BC"
        )

    native_music_pc = {
        565: FIELD565_MUSIC_PC,
        stabilization590.SCENE: donor567.MUSIC_PC,
    }.get(scene)
    if native_music_pc is not None:
        if (
            entry_pc + 1 != native_music_pc
            or editor.bytecode[
                native_music_pc :
                native_music_pc + len(KRELIAN_LAB_MUSIC_OPCODE)
            ]
            != KRELIAN_LAB_MUSIC_OPCODE
        ):
            raise SurfaceCampaignBuildError(
                f"Field {scene} native music selector changed from "
                "PLAY_MUSIC 0x3D"
            )
        if (
            scene == 565
            and FIELD565_SOURCE_MUSIC_OPCODE != KRELIAN_LAB_MUSIC_OPCODE
        ):
            raise SurfaceCampaignBuildError(
                "Requested campaign cue no longer matches field 565's native cue"
            )
        return editor

    expected_wrapper_pc = CAMPAIGN_MUSIC_WRAPPER_PCS.get(scene)
    if expected_wrapper_pc is None:
        raise SurfaceCampaignBuildError(
            f"Field {scene} lacks a campaign music wrapper contract"
        )
    wrapper = (
        b"\xBC"
        + KRELIAN_LAB_MUSIC_OPCODE
        + b"\x01"
        + _u16(entry_pc + 1)
    )
    wrapper_pc = editor.append_and_repoint(0, 0, wrapper)
    if (
        wrapper_pc != expected_wrapper_pc
        or editor.get_script_pointer(0, 0) != wrapper_pc
        or editor.bytecode[wrapper_pc : wrapper_pc + len(wrapper)] != wrapper
    ):
        raise SurfaceCampaignBuildError(
            f"Field {scene} music wrapper changed from 0x{expected_wrapper_pc:04X}"
        )
    return editor


def _prepare_campaign_music_field(
    prepared: base.PreparedField,
) -> base.PreparedField:
    scene = prepared.spec.identity.scene
    return _rebuild_field(
        prepared,
        editor=_install_campaign_music(
            prepared.components[SCRIPT_INDEX], scene
        ),
        role_suffix="persistent native field-565 Krelian Lab corridor cue",
    )


def _prepare_campaign_music_donor(
    prepared: base.PreparedDonorField,
) -> base.PreparedDonorField:
    scene = prepared.identity.scene
    return _rebuild_donor(
        prepared,
        editor=_install_campaign_music(
            prepared.components[SCRIPT_INDEX], scene
        ),
        role_suffix="persistent native field-565 Krelian Lab corridor cue",
    )


DONOR_NATIVE_FIELD_CHANGE_ACTIONS = {
    # scene: entity, action PC, helper, player script, destination, parameter
    549: (6, 0x01B4, 7, 4, 621, 2),
    550: (17, CLINIC_EXIT_ACTION_PC, 18, 4, 621, 3),
    567: empty_clinic567.RETURN_ROUTE,
    **exam_rooms.RETURN_ROUTES_BY_SCENE,
    588: (
        donor588.RETURN_CONTROLLER,
        donor588.RETURN_CONTROLLER_ACTION_PC,
        donor588.RETURN_HELPER,
        donor588.RETURN_PLAYER_SCRIPT_INDEX,
        donor588.RETURN_FIELD,
        donor588.RETURN_PARAMETER,
    ),
    589: (4, 0x00E1, 5, 4, 565, 4),
}

FIELD565_FRESH_FIELD_CHANGE_ACTIONS = (
    # entity, action PC, helper, player script, destination, parameter
    (4, 0x05F5, 19, 4, 621, 1),
    (6, 0x0612, 17, 6, 621, 4),
    (7, 0x062F, 18, 7, 621, 5),
    (9, 0x0792, 14, 9, 588, 0),
)
FIELD565_FUTURE_LAB_HANDOFF_ENTITY = 7


def _final_route_destination(
    field: int,
    controller_entity: int,
    source_destination: tuple[int, int],
) -> tuple[int, int]:
    """Resolve a live-audited room swap while freezing its old foundation."""

    matches = tuple(
        retarget
        for retarget in ROOM_SWAP_RETARGETS
        if (
            retarget.field,
            retarget.controller_entity,
        )
        == (field, controller_entity)
    )
    if not matches:
        return source_destination
    if len(matches) != 1 or matches[0].source_destination != source_destination:
        raise SurfaceCampaignBuildError(
            f"Field {field} e{controller_entity} room-swap foundation changed"
        )
    return matches[0].destination


def _append_release_to_native_donor_action(
    editor: ScriptEditor,
    *,
    scene: int,
    entity: int,
    expected_pc: int,
    helper_entity: int,
    player_script: int,
    destination_field: int,
    destination_parameter: int,
    seal_entity: int,
) -> None:
    expected = (
        donor588.RETURN_ACTION
        if scene == donor588.SCENE
        else _clinic_native_field_change_action(
            destination_field=destination_field,
            destination_parameter=destination_parameter,
        )
        if scene in (550, 567, *exam_rooms.SCENES)
        else _donor_native_field_change_action(
            helper_entity=helper_entity,
            player_script=player_script,
            destination_field=destination_field,
            destination_parameter=destination_parameter,
        )
    )
    if (
        editor.get_script_pointer(entity, 2) != expected_pc
        or editor.bytecode[expected_pc : expected_pc + len(expected)] != expected
    ):
        raise SurfaceCampaignBuildError(
            f"Donor e{entity} native field-change action moved"
        )
    output_field, output_parameter = _final_route_destination(
        scene,
        entity,
        (destination_field, destination_parameter),
    )
    output_pc = editor.bytecode_size
    output_action = (
        _clinic_native_field_change_action(
            destination_field=output_field,
            destination_parameter=output_parameter,
            seal_entity=seal_entity,
        )
        if scene in (550, 567, *exam_rooms.SCENES)
        else _donor_native_field_change_action(
            helper_entity=helper_entity,
            player_script=player_script,
            destination_field=output_field,
            destination_parameter=output_parameter,
            seal_entity=seal_entity,
            routine_pc=output_pc,
            arm_appointment=(scene == 549),
        )
    )
    editor.append_and_repoint(entity, 2, output_action)


def _install_field565_donor_door_releases(
    editor: ScriptEditor,
    seal_by_controller: Mapping[int, int],
) -> ScriptEditor:
    """Release each 565 seal only on its animated transition success path."""

    # Freeze every branch and target before appending anything.  The four
    # simple routes use fresh-Cross wrappers with absolute loop PCs.
    for entity, action_pc, helper, player, destination, parameter in (
        FIELD565_FRESH_FIELD_CHANGE_ACTIONS
    ):
        expected = _donor_fresh_cross_field_change_action(
            helper_entity=helper,
            player_script=player,
            destination_field=destination,
            destination_parameter=parameter,
            routine_pc=action_pc,
        )
        if (
            editor.get_script_pointer(entity, 2) != action_pc
            or editor.bytecode[action_pc : action_pc + len(expected)] != expected
        ):
            raise SurfaceCampaignBuildError(
                f"Field 565 e{entity} fresh-Cross action changed"
            )

    e8_expected = _donor_native_field_change_action(
        helper_entity=13,
        player_script=8,
        destination_field=589,
        destination_parameter=0,
    )
    if (
        editor.get_script_pointer(8, 2) != 0x030B
        or editor.bytecode[0x030B : 0x030B + len(e8_expected)] != e8_expected
    ):
        raise SurfaceCampaignBuildError("Field 565 e8 resonance action changed")

    production_outer = _gate_existing_action(
        requirements=(
            (SECURITY_KEYCARD_OPERAND, SECURITY_KEYCARD_MASK),
            (TONE_OPERAND, TONE_MASK),
            (STATE_OPERAND, QUARANTINE_MASK),
            (STATE_OPERAND, INTERFACE_BIT_MASK),
        ),
        old_action_pc=0x064C,
        denial_dialogue_id=12,
        routine_pc=0x07D3,
    )
    production_inner = base._field565_quarantine_exit_action(0x064C)
    if (
        editor.get_script_pointer(5, 2) != 0x07D3
        or editor.bytecode[0x07D3 : 0x07D3 + len(production_outer)]
        != production_outer
        or editor.bytecode[0x064C : 0x064C + len(production_inner)]
        != production_inner
    ):
        raise SurfaceCampaignBuildError("Field 565 production gates changed")

    quarantine_gate = _gate_existing_action(
        requirements=((QUARANTINE_KEYCARD_OPERAND, QUARANTINE_KEYCARD_MASK),),
        old_action_pc=0x035D,
        denial_dialogue_id=13,
        routine_pc=0x07AF,
    )
    if (
        editor.get_script_pointer(10, 2) != 0x07AF
        or editor.bytecode[0x07AF : 0x07AF + len(quarantine_gate)]
        != quarantine_gate
    ):
        raise SurfaceCampaignBuildError("Field 565 quarantine gate changed")

    native_e11 = base._field565_internal_gate_action()
    if (
        editor.get_script_pointer(11, 2) != 0x068A
        or editor.bytecode[0x068A : 0x068A + len(native_e11)] != native_e11
    ):
        raise SurfaceCampaignBuildError("Field 565 internal e11 action changed")
    if (
        editor.get_script_pointer(12, 2) != 0x03AC
        or editor.bytecode[0x03C1:0x03C4] != b"\x01\x9E\x06"
        or editor.bytecode[0x0465:0x0468] != b"\x01\xA4\x06"
        or editor.bytecode[0x069E:0x06A4]
        != base._field565_gate_ghost_trampoline(0x053C)
        or editor.bytecode[0x06A4:0x06AA]
        != base._field565_gate_ghost_trampoline(0x051D)
    ):
        raise SurfaceCampaignBuildError("Field 565 five-tone success exits changed")

    for entity, _old_pc, helper, player, destination, parameter in (
        FIELD565_FRESH_FIELD_CHANGE_ACTIONS
    ):
        action_pc = editor.bytecode_size
        if entity == FIELD565_FUTURE_LAB_HANDOFF_ENTITY:
            editor.append_and_repoint(
                entity,
                2,
                _repeatable_dialogue_action(
                    SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE_ID,
                    action_pc,
                ),
            )
            continue
        output_destination, output_parameter = _final_route_destination(
            565,
            entity,
            (destination, parameter),
        )
        editor.append_and_repoint(
            entity,
            2,
            _donor_fresh_cross_field_change_action(
                helper_entity=helper,
                player_script=player,
                destination_field=output_destination,
                destination_parameter=output_parameter,
                routine_pc=action_pc,
                seal_entity=seal_by_controller[entity],
            ),
        )

    _append_release_to_native_donor_action(
        editor,
        scene=565,
        entity=8,
        expected_pc=0x030B,
        helper_entity=13,
        player_script=8,
        destination_field=589,
        destination_parameter=0,
        seal_entity=seal_by_controller[8],
    )

    # The former production panel is now the ward's primary circulation door.
    # Its checked four-clearance V200 gate remains frozen above as provenance,
    # but the active fresh-X wrapper is direct; the same gate is installed on
    # the ward's actual production-side e6 threshold below.
    production_action_pc = editor.bytecode_size
    production_destination = _final_route_destination(565, 5, (624, 0))
    editor.append_and_repoint(
        5,
        2,
        _donor_fresh_cross_field_change_action(
            helper_entity=16,
            player_script=5,
            destination_field=production_destination[0],
            destination_parameter=production_destination[1],
            routine_pc=production_action_pc,
            seal_entity=seal_by_controller[5],
        ),
    )

    quarantine_action_pc = editor.bytecode_size
    editor.append_raw_routine(
        _donor_fresh_cross_field_change_action(
            helper_entity=15,
            player_script=10,
            destination_field=620,
            destination_parameter=1,
            routine_pc=quarantine_action_pc,
            seal_entity=seal_by_controller[10],
        )
    )
    script = base._patch_bytecode(
        editor.to_bytes(),
        0x07B7,
        _jump(0x035D),
        _jump(quarantine_action_pc),
    )
    editor = ScriptEditor(script)

    editor.append_and_repoint(
        11,
        2,
        _field565_internal_gate_action_with_seal(seal_by_controller[11]),
    )
    # Restore e12's complete retail five-tone password action.  The v173
    # foundation already redirects its two success-only exits through compact
    # six-byte ghost trampolines.  Expand those exits out of line so both the
    # authentic carrier and V201's separate circular seal are released before
    # rejoining the original success path.  Failed inputs never reach either
    # trampoline and therefore leave the passage physically closed.
    tone_reopen_pc = editor.bytecode_size
    editor.append_raw_routine(
        _field565_gate_clearance_trampoline(
            seal_by_controller[12],
            0x053C,
        )
    )
    tone_success_pc = editor.bytecode_size
    editor.append_raw_routine(
        _field565_gate_clearance_trampoline(
            seal_by_controller[12],
            0x051D,
        )
    )
    script = editor.to_bytes()
    for trampoline_pc, return_pc, expanded_pc in (
        (0x069E, 0x053C, tone_reopen_pc),
        (0x06A4, 0x051D, tone_success_pc),
    ):
        script = base._patch_bytecode(
            script,
            trampoline_pc,
            base._field565_gate_ghost_trampoline(return_pc),
            _jump(expanded_pc) + b"\x00\x00\x00",
        )
    editor = ScriptEditor(script)
    if editor.get_script_pointer(12, 2) != base.FIELD565_TONE_GATE_ACTION_PC:
        raise SurfaceCampaignBuildError(
            "Field 565 five-tone controller was not restored"
        )
    return editor


def _install_field567_donor_door_releases(
    editor: ScriptEditor,
    seal_by_controller: Mapping[int, int],
) -> ScriptEditor:
    """Wrap both ward bulkheads while leaving its restricted door sealed."""

    for (
        controller,
        action_pc,
        async_helper,
        blocking_helper,
        player_script,
        destination_field,
        destination_parameter,
    ) in donor567.ACTIVE_DOORS:
        expected = donor567.paired_door_action(
            async_helper,
            blocking_helper,
            player_script,
            destination_field,
            destination_parameter,
        )
        if (
            editor.get_script_pointer(controller, 2) != action_pc
            or editor.bytecode[action_pc : action_pc + len(expected)] != expected
        ):
            raise SurfaceCampaignBuildError(
                f"Field 567 e{controller} prepared paired-door action changed"
            )

    restricted_pc = editor.get_script_pointer(
        donor567.RESTRICTED_CONTROLLER,
        2,
    )
    restricted = donor567.sealed_door_action(
        donor567.SEALED_DIALOGUE_ID,
        donor567.SEALED_ACTION_PC,
    )
    if (
        restricted_pc != donor567.SEALED_ACTION_PC
        or editor.bytecode[
            restricted_pc : restricted_pc + len(restricted)
        ] != restricted
    ):
        raise SurfaceCampaignBuildError(
            "Field 567 restricted-procedure response changed"
        )

    for (
        controller,
        _action_pc,
        async_helper,
        blocking_helper,
        player_script,
        destination_field,
        destination_parameter,
    ) in donor567.ACTIVE_DOORS:
        wrapper_pc = editor.bytecode_size
        wrapper = _field567_fresh_cross_field_change_action(
            async_helper_entity=async_helper,
            blocking_helper_entity=blocking_helper,
            player_script=player_script,
            destination_field=destination_field,
            destination_parameter=destination_parameter,
            routine_pc=wrapper_pc,
            seal_entity=seal_by_controller[controller],
        )
        if editor.append_and_repoint(controller, 2, wrapper) != wrapper_pc:
            raise SurfaceCampaignBuildError(
                f"Field 567 e{controller} active wrapper moved"
            )

    # No success path releases e6's collision seal.  The response itself also
    # contains neither a leaf-helper call nor CHANGE_FIELD, so the unused
    # procedure suite remains visibly shut and physically impassable.
    if editor.get_script_pointer(donor567.RESTRICTED_CONTROLLER, 2) != restricted_pc:
        raise SurfaceCampaignBuildError(
            "Field 567 restricted-procedure door was accidentally repointed"
        )
    return editor


def _install_field590_donor_door_releases(
    editor: ScriptEditor,
    seal_by_controller: Mapping[int, int],
) -> ScriptEditor:
    """Activate all three recovered-ward doors and gate only production."""

    for (
        controller,
        action_pc,
        async_helper,
        blocking_helper,
        player_script,
        destination_field,
        destination_parameter,
    ) in donor567.ACTIVE_DOORS:
        expected = donor567.paired_door_action(
            async_helper,
            blocking_helper,
            player_script,
            destination_field,
            destination_parameter,
        )
        if (
            editor.get_script_pointer(controller, 2) != action_pc
            or editor.bytecode[action_pc : action_pc + len(expected)] != expected
        ):
            raise SurfaceCampaignBuildError(
                f"Recovered field 590 e{controller} paired-door foundation changed"
            )

    restricted = donor567.sealed_door_action(
        donor567.SEALED_DIALOGUE_ID,
        donor567.SEALED_ACTION_PC,
    )
    if (
        editor.get_script_pointer(donor567.RESTRICTED_CONTROLLER, 2)
        != donor567.SEALED_ACTION_PC
        or editor.bytecode[
            donor567.SEALED_ACTION_PC :
            donor567.SEALED_ACTION_PC + len(restricted)
        ]
        != restricted
    ):
        raise SurfaceCampaignBuildError(
            "Recovered field 590 production-door foundation changed"
        )

    active_routes = (
        (
            donor567.LOBBY_CONTROLLER,
            donor567.LOBBY_ASYNC_HELPER,
            donor567.LOBBY_BLOCKING_HELPER,
            donor567.LOBBY_PLAYER_SCRIPT,
            stabilization590.MANIFOLD_BULKHEAD_DESTINATION,
        ),
        (
            donor567.SERVICE_CONTROLLER,
            donor567.SERVICE_ASYNC_HELPER,
            donor567.SERVICE_BLOCKING_HELPER,
            donor567.SERVICE_PLAYER_SCRIPT,
            stabilization590.MANIFOLD_STAFF_DESTINATION,
        ),
    )
    for controller, async_helper, blocking_helper, player_script, destination in (
        active_routes
    ):
        wrapper_pc = editor.bytecode_size
        editor.append_and_repoint(
            controller,
            2,
            _field567_fresh_cross_field_change_action(
                async_helper_entity=async_helper,
                blocking_helper_entity=blocking_helper,
                player_script=player_script,
                destination_field=destination[0],
                destination_parameter=destination[1],
                routine_pc=wrapper_pc,
                seal_entity=seal_by_controller[controller],
            ),
        )

    production_success_pc = editor.bytecode_size
    editor.append_raw_routine(
        _field567_fresh_cross_field_change_action(
            async_helper_entity=donor567.RESTRICTED_ASYNC_HELPER,
            blocking_helper_entity=donor567.RESTRICTED_BLOCKING_HELPER,
            player_script=donor567.RESTRICTED_PLAYER_SCRIPT,
            destination_field=stabilization590.SORTING_DESTINATION[0],
            destination_parameter=stabilization590.SORTING_DESTINATION[1],
            routine_pc=production_success_pc,
            seal_entity=seal_by_controller[donor567.RESTRICTED_CONTROLLER],
        )
    )
    production_gate_pc = editor.bytecode_size
    editor.append_and_repoint(
        donor567.RESTRICTED_CONTROLLER,
        2,
        _gate_existing_action(
            requirements=(
                (SECURITY_KEYCARD_OPERAND, SECURITY_KEYCARD_MASK),
                (TONE_OPERAND, TONE_MASK),
                (STATE_OPERAND, QUARANTINE_MASK),
                (STATE_OPERAND, INTERFACE_BIT_MASK),
            ),
            old_action_pc=production_success_pc,
            denial_dialogue_id=stabilization590.PRODUCTION_DENIAL_DIALOGUE_ID,
            routine_pc=production_gate_pc,
        ),
    )
    return editor


def _prepare_donor_door_clearance(
    prepared: base.PreparedDonorField,
) -> base.PreparedDonorField:
    """Split every donor door's X shell from its physical threshold seal."""

    scene = prepared.identity.scene
    contracts = DONOR_DOOR_COLLISION_CONTRACTS.get(scene)
    if contracts is None:
        raise SurfaceCampaignBuildError(
            f"Donor field {scene} lacks a door-collision contract"
        )
    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    triangles = base._walkmesh_layer(prepared.components[1], 0)
    endpoint_ids = {endpoint.id for endpoint in blueprint.ENDPOINTS}
    for contract in contracts:
        seal_position = _donor_seal_position(contract)
        if (
            contract.controller_entity >= editor.entity_count
            or contract.triangle >= len(triangles)
            or not base._point_inside_triangle(
                (contract.x, contract.z),
                triangles[contract.triangle],
            )
            or not base._point_inside_triangle(
                seal_position,
                triangles[contract.triangle],
            )
        ):
            raise SurfaceCampaignBuildError(
                f"Donor field {scene} e{contract.controller_entity} left walkmesh"
            )
        if (
            contract.arrival_parameter is not None
            and contract.endpoint_id not in endpoint_ids
        ):
            raise SurfaceCampaignBuildError(
                f"Donor endpoint {contract.endpoint_id!r} left the blueprint"
            )
        init_pc = editor.get_script_pointer(contract.controller_entity, 0)
        expected_init = _expected_donor_door_controller_init(contract)
        if editor.bytecode[init_pc : init_pc + len(expected_init)] != expected_init:
            raise SurfaceCampaignBuildError(
                f"Donor field {scene} e{contract.controller_entity} init changed"
            )
        if contract.arrival_parameter is not None:
            entry_pc = 1 + 7 * contract.arrival_parameter
            arrival_x, arrival_z = struct.unpack_from(
                "<hh", editor.bytecode, entry_pc
            )
            if (arrival_x, arrival_z) != contract.closed_side_probe:
                raise SurfaceCampaignBuildError(
                    f"Donor endpoint {contract.endpoint_id} arrival moved"
                )
            # Integer comparisons pin a strictly clear spawn without
            # introducing floating-point build behavior.  Circular actors
            # combine radii, while EntityMoveCheck0 supplies extraRadius=0 to
            # rectangular script volumes and therefore uses only OP18's
            # doubled X/Z half-extents.
            seal_x, seal_z = seal_position
            if contract.rectangular_seal_half_extents is None:
                effective_radius = (
                    2 * contract.seal_radius + PLAYER_COLLISION_RADIUS
                )
                arrival_hits_seal = (
                    (arrival_x - seal_x) ** 2
                    + (arrival_z - seal_z) ** 2
                    <= effective_radius ** 2
                )
            else:
                half_width, half_depth = contract.rectangular_seal_half_extents
                arrival_hits_seal = (
                    abs(arrival_x - seal_x) <= 2 * half_width
                    and abs(arrival_z - seal_z) <= 2 * half_depth
                )
            if arrival_hits_seal:
                raise SurfaceCampaignBuildError(
                    f"Donor endpoint {contract.endpoint_id} arrival hits its seal"
                )

    old_count = editor.entity_count
    seal_records = tuple(
        Console(
            *_donor_seal_position(contract),
            contract.triangle,
            0,
            "",
        )
        for contract in contracts
    )
    header = _insert_controller_records(
        prepared.header,
        old_entity_count=old_count,
        consoles=seal_records,
    )
    editor = ScriptEditor(
        base.mass_driver._extend_atel_entity_table(
            editor.to_bytes(), old_count + len(contracts)
        )
    )
    stop_pc = editor.append_raw_routine(b"\x00")
    release_pc = editor.append_raw_routine(DONOR_SEAL_RELEASE_ACTION)
    seal_entities = tuple(range(old_count, old_count + len(contracts)))
    for seal_entity in seal_entities:
        for script_index in range(32):
            editor.set_script_pointer(seal_entity, script_index, stop_pc)
        editor.set_script_pointer(seal_entity, 4, release_pc)

    seal_by_controller = {
        contract.controller_entity: seal_entity
        for contract, seal_entity in zip(contracts, seal_entities, strict=True)
    }
    if len(seal_by_controller) != len(contracts):
        raise SurfaceCampaignBuildError(
            f"Donor field {scene} reuses a door controller"
        )
    for contract, seal_entity in zip(contracts, seal_entities, strict=True):
        editor.append_and_repoint(
            contract.controller_entity,
            0,
            _ghost_donor_door_controller_init(contract),
        )
        editor.append_and_repoint(
            seal_entity,
            0,
            _donor_seal_init(contract),
        )

    if scene == 565:
        editor = _install_field565_donor_door_releases(
            editor,
            seal_by_controller,
        )
    elif scene == stabilization590.SCENE:
        editor = _install_field590_donor_door_releases(
            editor,
            seal_by_controller,
        )
    else:
        (
            entity,
            action_pc,
            helper,
            player,
            destination,
            parameter,
        ) = DONOR_NATIVE_FIELD_CHANGE_ACTIONS[scene]
        _append_release_to_native_donor_action(
            editor,
            scene=scene,
            entity=entity,
            expected_pc=action_pc,
            helper_entity=helper,
            player_script=player,
            destination_field=destination,
            destination_parameter=parameter,
            seal_entity=seal_by_controller[entity],
        )

    if scene in FIELD352_X_ONLY_SCENES:
        if len(contracts) != 1:
            raise SurfaceCampaignBuildError(
                f"Field {scene} field-352 door count changed"
            )
        editor = _validate_exam_return_x_only(editor, contracts[0], scene)

    return _rebuild_donor(
        prepared,
        editor=editor,
        header=header,
        role_suffix=(
            "broad ghost no-facing X targets with action-disabled doorway "
            "seals released only by native success paths"
        ),
    )


def _gate_existing_action(
    *,
    requirements: Sequence[tuple[int, int]],
    old_action_pc: int,
    denial_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    denial_probe = b"".join(_bit_test(op, mask, 0) for op, mask in requirements)
    denial_pc = routine_pc + len(denial_probe) + 3
    checks = b"".join(
        _bit_test(operand, mask, denial_pc) for operand, mask in requirements
    )
    return (
        checks
        + _jump(old_action_pc)
        + _repeatable_dialogue_action(denial_dialogue_id, denial_pc)
    )


def _gate_local_completion(
    *,
    progress_bit_index: int,
    progress_bit_mask: int,
    local_value: int,
    old_action_pc: int,
    denial_dialogue_id: int,
    success_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Gate one solved room and commit progress only after its receipt closes."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.jump_if_bit_clear(STATE_OPERAND, progress_bit_mask, "unsaved")
    routine.emit(_jump(old_action_pc))

    routine.label("unsaved")
    routine.jump_if_not_equal(LOCAL_PUZZLE_OPERAND, local_value, "denied")
    routine.emit(b"\x33\xFE\x54")
    open_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            open_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(PROGRESSION_CONFIRM_SOUND)
    routine.emit(
        b"\xF5" + _u16(success_dialogue_id) + b"\x01\x9C"
    )
    close_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            close_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_set_bit(STATE_OPERAND, progress_bit_index))
    routine.emit(_jump(old_action_pc))

    routine.label("denied")
    routine.emit(_repeatable_dialogue_action(denial_dialogue_id, routine.pc))
    return routine.finish()


def _install_switch_puzzle(
    prepared: base.PreparedField,
    *,
    consoles: Sequence[Console],
    door_entity: int,
    progress_bit_index: int,
    progress_bit_mask: int,
    denial_text: str,
    success_text: str,
    role_suffix: str,
) -> base.PreparedField:
    _validate_console_points(prepared, consoles)
    dialogue, ids = _append_dialogue(
        prepared.components[7],
        tuple(console.text for console in consoles)
        + (denial_text, success_text),
    )
    *console_ids, denial_id, success_id = ids
    editor, header, entities, _stop = _extend_for_consoles(prepared, consoles)
    for entity, console, dialogue_id in zip(
        entities, consoles, console_ids, strict=True
    ):
        editor.append_and_repoint(entity, 0, _console_init(console))
        action_pc = editor.bytecode_size
        editor.append_and_repoint(
            entity,
            2,
            _state_console_action(
                operand=LOCAL_PUZZLE_OPERAND,
                bit_index=console.bit_index,
                dialogue_id=dialogue_id,
                routine_pc=action_pc,
            ),
        )
    old_action = editor.get_script_pointer(door_entity, 2)
    gate_pc = editor.bytecode_size
    editor.append_and_repoint(
        door_entity,
        2,
        _gate_local_completion(
            progress_bit_index=progress_bit_index,
            progress_bit_mask=progress_bit_mask,
            local_value=(1 << len(consoles)) - 1,
            old_action_pc=old_action,
            denial_dialogue_id=denial_id,
            success_dialogue_id=success_id,
            routine_pc=gate_pc,
        ),
    )
    return _rebuild_field(
        prepared,
        editor=editor,
        header=header,
        dialogue=dialogue,
        role_suffix=role_suffix,
    )


def _prepare_sorting(prepared: base.PreparedField) -> base.PreparedField:
    puzzle = _install_switch_puzzle(
        prepared,
        consoles=SORTER_CONSOLES,
        door_entity=1,
        progress_bit_index=SORTER_BIT_INDEX,
        progress_bit_mask=SORTER_BIT_MASK,
        denial_text=(
            "MOLECULAR SORTER INTERLOCK\n"
            "Divert all three living-material feeds\n"
            "before entering the M-Project core.<Close>"
        ),
        success_text=SORTER_SUCCESS_DIALOGUE,
        role_suffix="three-feed molecular diversion puzzle",
    )
    editor = _retarget_surface_room_actions(
        puzzle.components[SCRIPT_INDEX],
        624,
    )
    rebuilt = _rebuild_field(
        puzzle,
        editor=editor,
        role_suffix=(
            "recovered stabilization-ward return replacing the direct "
            "service-manifold link"
        ),
    )
    return replace(
        rebuilt,
        spec=replace(
            rebuilt.spec,
            edges=_retarget_surface_edges(rebuilt.spec.edges, 624),
        ),
    )


def _prepare_core(prepared: base.PreparedField) -> base.PreparedField:
    return _install_switch_puzzle(
        prepared,
        consoles=CORE_CONSOLES,
        door_entity=1,
        progress_bit_index=CORE_BIT_INDEX,
        progress_bit_mask=CORE_BIT_MASK,
        denial_text=(
            "M-PROJECT CORE INTERLOCK\n"
            "Discharge fusion, uncouple the pattern,\n"
            "and retain containment.<Close>"
        ),
        success_text=CORE_SUCCESS_DIALOGUE,
        role_suffix="Gazel M-Project safe-state calibration",
    )


def _prepare_meld(prepared: base.PreparedField) -> base.PreparedField:
    _validate_console_points(prepared, (MELD_CONSOLE,))
    dialogue, (reveal_id, denial_id) = _append_dialogue(
        prepared.components[7],
        (
            MELD_CONSOLE.text,
            "GENERATION ROUTE DENIED\n"
            "The voices within Meld have not been heard.<Close>",
        ),
    )
    editor, header, (entity,), _stop = _extend_for_consoles(
        prepared, (MELD_CONSOLE,)
    )
    editor.append_and_repoint(entity, 0, _console_init(MELD_CONSOLE))
    action_pc = editor.bytecode_size
    editor.append_and_repoint(
        entity,
        2,
        _state_console_action(
            operand=STATE_OPERAND,
            bit_index=MELD_BIT_INDEX,
            dialogue_id=reveal_id,
            routine_pc=action_pc,
        ),
    )
    old_action = editor.get_script_pointer(6, 2)
    gate_pc = editor.bytecode_size
    editor.append_and_repoint(
        6,
        2,
        _gate_existing_action(
            requirements=((STATE_OPERAND, MELD_BIT_MASK),),
            old_action_pc=old_action,
            denial_dialogue_id=denial_id,
            routine_pc=gate_pc,
        ),
    )
    return _rebuild_field(
        prepared,
        editor=editor,
        header=header,
        dialogue=dialogue,
        role_suffix="one-time Meld witness and generation interlock",
    )


def _boss_action(
    *,
    pre_dialogue_id: int,
    post_dialogue_id: int,
    already_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Run Sufal, then a save-safe epilogue before committing completion."""

    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.jump_if_bit_clear(STATE_OPERAND, SECURED_BIT_MASK, "unsecured")
    # Completion is authoritative.  If a savestate was captured in the tiny
    # window after secured was committed but before pending was cleared, heal
    # that harmless torn state before showing the already-complete status.
    routine.emit(_clear_bit(STATE_OPERAND, FINALE_EPILOGUE_PENDING_BIT_INDEX))
    routine.emit(_repeatable_dialogue_action(already_dialogue_id, routine.pc))

    routine.label("unsecured")
    routine.jump_if_bit_clear(
        STATE_OPERAND,
        FINALE_EPILOGUE_PENDING_BIT_MASK,
        "battle",
    )
    # A torn save after the battle but before the epilogue commit resumes here
    # without replaying Sufal.  Drain the interaction press before the receipt.
    routine.emit(b"\x33\xFE\x54")
    resume_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            resume_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.jump("epilogue")

    routine.label("battle")
    routine.emit(b"\x33\xFE\x54")
    battle_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            battle_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(b"\xF5" + _u16(pre_dialogue_id) + b"\x01\x9C")
    # Retail field 622's exact Sufal battle configuration and postbattle field
    # synchronization.  The encounter/model streams stay untouched.
    routine.emit(bytes.fromhex("71 09 80 FE 7F"))
    routine.emit(_set_bit(STATE_OPERAND, FINALE_EPILOGUE_PENDING_BIT_INDEX))

    routine.label("epilogue")
    routine.emit(PROGRESSION_CONFIRM_SOUND)
    routine.emit(b"\xF5" + _u16(post_dialogue_id) + b"\x01\x9C")
    epilogue_release_pc = routine.pc
    routine.emit(
        base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS,
            epilogue_release_pc,
        )
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(_set_bit(STATE_OPERAND, SECURED_BIT_INDEX))
    routine.emit(_clear_bit(STATE_OPERAND, FINALE_EPILOGUE_PENDING_BIT_INDEX))
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def _prepare_generation(prepared: base.PreparedField) -> base.PreparedField:
    consoles = (GENERATION_SAVE_CONSOLE, GENERATION_BOSS_CONSOLE)
    _validate_console_points(prepared, consoles)
    corrected = _replace_dialogue_texts(
        prepared.components[7],
        {
            22: (
                "Word spread that this place could arrest the mutations.\n"
                "I wanted to believe it.<Close>"
            ),
            34: (
                "Meld is made from people.\n"
                "I saw their eyes before their shapes were forced together.<Close>"
            ),
        },
    )
    dialogue, ids = _append_dialogue(
        corrected,
        (
            "The barrier ruptures. The Sufal Mass rises from\n"
            "people consumed by the generation line.\n"
            "Their remaining voices ask for release.<New>"
            "Elly\n"
            '"We will not leave them trapped inside this machine."<New>'
            "Fei\n"
            '"Then we end it here."<Close>',
            "The generation cycle stops.\n"
            "This Ignas node is silent. Other Surface systems remain.<New>"
            "Elly\n"
            '"The voices are quiet now."<New>'
            "Fei\n"
            '"We stopped this node. We keep going until none remain."<New>'
            "Citan\n"
            '"Containment is stable. The emergency return is online."<Close>',
            "The Sufal Mass is gone.\n"
            "Emergency return and save controls remain online.<Close>",
            "EMERGENCY RETURN SEALED\n"
            "The generation hall remains active.<Close>",
        ),
    )
    pre_id, post_id, already_id, denial_id = ids
    editor, header, (save_entity, boss_entity), _stop = _extend_for_consoles(
        prepared, consoles
    )
    editor.append_and_repoint(save_entity, 0, _console_init(GENERATION_SAVE_CONSOLE))
    # Retail field 622's exact save-menu handoff, now attached to an audited
    # X carrier rather than the unreachable narrated director.
    editor.append_and_repoint(
        save_entity,
        2,
        bytes.fromhex("33 FE 99 00 FE 55 FE 87 00"),
    )
    editor.append_and_repoint(boss_entity, 0, _console_init(GENERATION_BOSS_CONSOLE))
    boss_pc = editor.bytecode_size
    editor.append_and_repoint(
        boss_entity,
        2,
        _boss_action(
            pre_dialogue_id=pre_id,
            post_dialogue_id=post_id,
            already_dialogue_id=already_id,
            routine_pc=boss_pc,
        ),
    )
    shortcut_entity = 26
    old_shortcut = editor.get_script_pointer(shortcut_entity, 2)
    gate_pc = editor.bytecode_size
    editor.append_and_repoint(
        shortcut_entity,
        2,
        _gate_existing_action(
            requirements=((STATE_OPERAND, SECURED_BIT_MASK),),
            old_action_pc=old_shortcut,
            denial_dialogue_id=denial_id,
            routine_pc=gate_pc,
        ),
    )
    return _rebuild_field(
        prepared,
        editor=editor,
        header=header,
        dialogue=dialogue,
        role_suffix=(
            "save console, Sufal Mass confrontation, recoverable epilogue, "
            "facility shutdown, and explorable emergency return"
        ),
    )


def _prepare_transfer_shortcut(prepared: base.PreparedField) -> base.PreparedField:
    """Make the return shortcut depend on the campaign finale itself.

    The v173 foundation used bit 10 as a one-sided discovery latch: leaving
    field 622 set it, and field 623 tested it.  The campaign has a stronger
    milestone in bit 15, written only after the native Sufal battle returns.
    Testing that milestone here makes both physical endpoints unlock together
    after victory while leaving the old bit-10 write harmless for v173 save
    compatibility.
    """

    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    shortcut_entity = 38
    gate_pc = editor.get_script_pointer(shortcut_entity, 2)
    expected = (
        b"\x02"
        + _u16(base.SURFACE_SHORTCUT_STATE_OPERAND)
        + _u16(base.SURFACE_SHORTCUT_DISCOVERED_BIT)
        + b"\x46"
    )
    if editor.bytecode[gate_pc : gate_pc + len(expected)] != expected:
        raise SurfaceCampaignBuildError("Field 623 legacy shortcut gate changed")
    script = bytearray(editor.to_bytes())
    mask_offset = editor.bytecode_offset + gate_pc + 3
    script[mask_offset : mask_offset + 2] = _u16(SECURED_BIT_MASK)

    editor = ScriptEditor(bytes(script))
    north_door = base.NATIVE_DOOR_CONTROLLERS[623][0]
    if (
        (north_door.x, north_door.z) != (0, TRANSFER_NORTH_DOOR_CLOSED_PLANE_Z)
        or (
            north_door.destination_field,
            north_door.destination_parameter,
        )
        != (
            TRANSFER_NORTH_DOOR_ANIMATION.destination_field,
            TRANSFER_NORTH_DOOR_ANIMATION.destination_parameter,
        )
    ):
        raise SurfaceCampaignBuildError("Field 623 north-door route changed")
    old_count = editor.entity_count
    old_action_pc = editor.get_script_pointer(
        TRANSFER_NORTH_DOOR_CONTROLLER_ENTITY, 2
    )
    old_action = base._door_transition_action(north_door)
    if (
        old_action_pc != 0x095D
        or editor.bytecode[old_action_pc : old_action_pc + len(old_action)]
        != old_action
    ):
        raise SurfaceCampaignBuildError(
            "Field 623 north-door controller action changed"
        )

    header = _insert_transfer_north_door_leaf_records(
        prepared.header,
        old_entity_count=old_count,
    )
    editor = ScriptEditor(
        base.mass_driver._extend_atel_entity_table(
            editor.to_bytes(),
            old_count + len(TRANSFER_NORTH_DOOR_HELPER_ENTITIES),
        )
    )
    stop_pc = editor.get_script_pointer(
        TRANSFER_NORTH_DOOR_SOURCE_HELPER_ENTITIES[0], 1
    )
    if stop_pc >= editor.bytecode_size or editor.bytecode[stop_pc] != 0:
        raise SurfaceCampaignBuildError("Field 623 blue door STOP changed")

    for leaf, expected_pcs in zip(
        TRANSFER_NORTH_DOOR_ANIMATION.leaves,
        TRANSFER_NORTH_DOOR_HELPER_PCS,
        strict=True,
    ):
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
            base.mass_driver._world_position_static_slide_body(
                start_x=0,
                start_z=TRANSFER_NORTH_DOOR_ORIGIN_Z,
                delta_x=leaf.delta_x,
                delta_z=leaf.delta_z,
                iterations=TRANSFER_NORTH_DOOR_ANIMATION.frames,
            ),
        )
        if (init_pc, slide_pc) != expected_pcs:
            raise SurfaceCampaignBuildError(
                f"Field 623 north-door helper e{leaf.helper_entity} moved"
            )

    action_pc = editor.bytecode_size
    action = base._animated_door_transition_action(
        north_door,
        TRANSFER_NORTH_DOOR_ANIMATION,
        action_pc,
    )
    sound = bytes((0x74, TRANSFER_NORTH_DOOR_SOUND_ID, 0x80))
    if action_pc != TRANSFER_NORTH_DOOR_ACTION_PC or action.count(sound) != 1:
        raise SurfaceCampaignBuildError("Field 623 north-door action identity changed")
    if (
        editor.append_and_repoint(
            TRANSFER_NORTH_DOOR_CONTROLLER_ENTITY,
            2,
            action,
        )
        != action_pc
    ):
        raise SurfaceCampaignBuildError("Field 623 north-door action moved")

    return _rebuild_field(
        prepared,
        editor=editor,
        header=header,
        role_suffix=(
            "post-Sufal emergency return gate and native paired north-door animation"
        ),
    )


def _retarget_surface_room_actions(script: bytes, scene: int) -> ScriptEditor:
    """Retarget checked room destinations at their audited physical doors."""

    for retarget in (
        item for item in ROOM_SWAP_RETARGETS if item.field == scene
    ):
        if retarget.action_pc is None or retarget.change_pc is None:
            raise SurfaceCampaignBuildError(
                f"Field {scene} e{retarget.controller_entity} uses a rebuilt "
                "route wrapper, not an in-place retarget"
            )
        editor = ScriptEditor(script)
        if editor.get_script_pointer(retarget.controller_entity, 2) != retarget.action_pc:
            raise SurfaceCampaignBuildError(
                f"Field {scene} e{retarget.controller_entity} room-swap action moved"
            )
        script = base._patch_bytecode(
            script,
            retarget.change_pc,
            base._change_field(*retarget.source_destination),
            base._change_field(*retarget.destination),
        )
    return ScriptEditor(script)


def _retarget_surface_edges(
    edges: tuple[base.Edge, ...],
    scene: int,
) -> tuple[base.Edge, ...]:
    retargets = tuple(item for item in ROOM_SWAP_RETARGETS if item.field == scene)
    applied: set[int] = set()
    result = []
    for edge in edges:
        source = (edge.destination_field, edge.destination_parameter)
        matches = tuple(item for item in retargets if item.source_destination == source)
        if len(matches) > 1:
            raise SurfaceCampaignBuildError(
                f"Field {scene} room-swap edge is ambiguous"
            )
        if matches:
            retarget = matches[0]
            applied.add(retarget.controller_entity)
            result.append(
                replace(
                    edge,
                    destination_field=retarget.destination[0],
                    destination_parameter=retarget.destination[1],
                )
            )
        else:
            result.append(edge)
    expected = {item.controller_entity for item in retargets}
    if applied != expected:
        raise SurfaceCampaignBuildError(f"Field {scene} room-swap edges changed")
    return tuple(result)


def _install_intake_physician_assets(
    prepared: base.PreparedField,
    clinic_office: base.PreparedDonorField,
) -> Mapping[int, bytes]:
    """Replace lobby bank 6 with the exact field-352 office physician."""

    actor_index = base.mass_driver.ACTOR_INDEX
    sprite_index = base.mass_driver.SPRITE_INDEX
    if (
        _sha256(prepared.components[actor_index])
        != INTAKE_TARGET_ACTOR_COMPONENT_SHA256
        or _sha256(prepared.components[sprite_index])
        != INTAKE_TARGET_SPRITE_COMPONENT_SHA256
        or struct.unpack_from(
            "<4H", prepared.header, INTAKE_DOCTOR_TARGET_BANK * 8
        )
        != INTAKE_DOCTOR_TARGET_MAPPING
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 physician-bank destination changed"
        )

    target_actors = base.mass_driver._indexed_bundle_entries(
        prepared.components[actor_index]
    )
    target_sprites = base.mass_driver._indexed_bundle_entries(
        prepared.components[sprite_index]
    )
    source_actors = base.mass_driver._indexed_bundle_entries(
        clinic_office.components[actor_index]
    )
    source_sprites = base.mass_driver._indexed_bundle_entries(
        clinic_office.components[sprite_index]
    )
    if (
        len(target_actors) != 8
        or len(target_sprites) != 8
        or len(source_actors) != 4
        or len(source_sprites) != 4
    ):
        raise SurfaceCampaignBuildError("Physician actor-bank inventory changed")
    physician_actor = source_actors[INTAKE_DOCTOR_SOURCE_BANK]
    physician_sprite = source_sprites[INTAKE_DOCTOR_SOURCE_BANK]
    if (
        len(physician_actor) != 2_396
        or _sha256(physician_actor) != INTAKE_SOURCE_PHYSICIAN_ACTOR_SHA256
        or len(physician_sprite) != 26_764
        or _sha256(physician_sprite) != INTAKE_SOURCE_PHYSICIAN_SPRITE_SHA256
        or struct.unpack_from("<IIHH", physician_sprite) != (1, 8, 64, 209)
    ):
        raise SurfaceCampaignBuildError("Field 352 physician bank changed")

    installed_actors = list(target_actors)
    installed_sprites = list(target_sprites)
    installed_actors[INTAKE_DOCTOR_TARGET_BANK] = physician_actor
    installed_sprites[INTAKE_DOCTOR_TARGET_BANK] = physician_sprite
    actor_component = base.mass_driver._rebuild_indexed_bundle(
        prepared.components[actor_index], installed_actors
    )
    sprite_component = base.mass_driver._rebuild_indexed_bundle(
        prepared.components[sprite_index], installed_sprites
    )
    reparsed_actors = base.mass_driver._indexed_bundle_entries(actor_component)
    reparsed_sprites = base.mass_driver._indexed_bundle_entries(sprite_component)
    if (
        _sha256(actor_component) != INTAKE_INSTALLED_ACTOR_COMPONENT_SHA256
        or _sha256(sprite_component) != INTAKE_INSTALLED_SPRITE_COMPONENT_SHA256
        or reparsed_actors[INTAKE_DOCTOR_TARGET_BANK] != physician_actor
        or reparsed_sprites[INTAKE_DOCTOR_TARGET_BANK] != physician_sprite
        or any(
            reparsed_actors[index] != target_actors[index]
            or reparsed_sprites[index] != target_sprites[index]
            for index in range(8)
            if index != INTAKE_DOCTOR_TARGET_BANK
        )
    ):
        raise SurfaceCampaignBuildError(
            "Exact office physician did not install deterministically"
        )
    return {actor_index: actor_component, sprite_index: sprite_component}


def _install_intake_native_dialogue_mutexes(editor: ScriptEditor) -> None:
    """Publish every retained lobby NPC window to the doctor's poll loop."""

    for entity, (old_action_pc, dialogue_id) in (
        INTAKE_NATIVE_DIALOGUE_ACTIONS.items()
    ):
        expected = _actor_dialogue(dialogue_id) + b"\x00"
        if (
            editor.get_script_pointer(entity, 2) != old_action_pc
            or editor.bytecode[
                old_action_pc : old_action_pc + len(expected)
            ]
            != expected
        ):
            raise SurfaceCampaignBuildError(
                f"Field 621 native dialogue action e{entity} changed"
            )
        wrapper = _intake_native_dialogue_mutex_action(dialogue_id)
        wrapper_pc = editor.append_and_repoint(entity, 2, wrapper)
        if (
            editor.get_script_pointer(entity, 2) != wrapper_pc
            or editor.bytecode[wrapper_pc : wrapper_pc + len(wrapper)]
            != wrapper
        ):
            raise SurfaceCampaignBuildError(
                f"Field 621 native dialogue mutex e{entity} failed"
            )


def _intake_survivor_zone_bounds(
    zone: tuple[tuple[int, int], ...],
) -> tuple[int, int, int, int]:
    """Return one audited clockwise OP17 rectangle as min/max X/Z."""

    if len(zone) != 4:
        raise SurfaceCampaignBuildError("Intake survivor movement zone changed")
    min_x = min(point[0] for point in zone)
    max_x = max(point[0] for point in zone)
    min_z = min(point[1] for point in zone)
    max_z = max(point[1] for point in zone)
    if zone != (
        (min_x, max_z),
        (max_x, max_z),
        (max_x, min_z),
        (min_x, min_z),
    ) or not min_x < max_x or not min_z < max_z:
        raise SurfaceCampaignBuildError(
            "Intake survivor movement zone is not a clockwise rectangle"
        )
    return min_x, max_x, min_z, max_z


def _intake_survivor_movement_zone_body(
    zone: tuple[tuple[int, int], ...],
) -> bytes:
    """Encode one survivor's retail four-corner movement limiter."""

    _intake_survivor_zone_bounds(zone)
    return (
        b"\x17"
        + b"".join(
            _s16(coordinate)
            for point in zone
            for coordinate in point
        )
        + b"\xFF"
    )


def _intake_wandering_survivor_init(
    *,
    graphic: int,
    position: tuple[int, int],
    zone: tuple[tuple[int, int], ...],
) -> bytes:
    """Place one survivor and retain random walking inside its private zone."""

    return (
        b"\x0B"
        + base._immediate(graphic)
        + b"\x19"
        + _s16(position[0])
        + _s16(position[1])
        + b"\xC0"
        + _intake_survivor_movement_zone_body(zone)
        + b"\x00"
    )


def _clip_intake_polygon_axis(
    polygon: tuple[tuple[Fraction, Fraction], ...],
    *,
    axis: int,
    boundary: int,
    keep_greater: bool,
) -> tuple[tuple[Fraction, Fraction], ...]:
    """Clip a rational X/Z polygon against one rectangle half-plane."""

    if not polygon:
        return ()
    threshold = Fraction(boundary)

    def inside(point: tuple[Fraction, Fraction]) -> bool:
        return (
            point[axis] >= threshold
            if keep_greater
            else point[axis] <= threshold
        )

    result: list[tuple[Fraction, Fraction]] = []
    previous = polygon[-1]
    previous_inside = inside(previous)
    for current in polygon:
        current_inside = inside(current)
        if current_inside != previous_inside:
            axis_delta = current[axis] - previous[axis]
            if axis_delta == 0:
                raise SurfaceCampaignBuildError(
                    "Intake walkmesh polygon clipping became vertical at a crossing"
                )
            ratio = (threshold - previous[axis]) / axis_delta
            result.append(
                (
                    previous[0] + ratio * (current[0] - previous[0]),
                    previous[1] + ratio * (current[1] - previous[1]),
                )
            )
        if current_inside:
            result.append(current)
        previous = current
        previous_inside = current_inside
    return tuple(result)


def _intake_walkmesh_rectangle_coverage_area2(
    triangles: Sequence[Sequence[tuple[int, int, int]]],
    bounds: tuple[int, int, int, int],
) -> Fraction:
    """Return exact doubled walkmesh area inside one X/Z rectangle."""

    min_x, max_x, min_z, max_z = bounds
    area2 = Fraction(0)
    for triangle in triangles:
        polygon = tuple(
            (Fraction(vertex[0]), Fraction(vertex[2])) for vertex in triangle
        )
        for axis, boundary, keep_greater in (
            (0, min_x, True),
            (0, max_x, False),
            (1, min_z, True),
            (1, max_z, False),
        ):
            polygon = _clip_intake_polygon_axis(
                polygon,
                axis=axis,
                boundary=boundary,
                keep_greater=keep_greater,
            )
            if not polygon:
                break
        if len(polygon) >= 3:
            area2 += abs(
                sum(
                    start[0] * end[1] - start[1] * end[0]
                    for start, end in zip(
                        polygon,
                        (*polygon[1:], polygon[0]),
                        strict=True,
                    )
                )
            )
    return area2


def _intake_survivor_zone_separation_squared(
    first: tuple[tuple[int, int], ...],
    second: tuple[tuple[int, int], ...],
) -> int:
    """Return squared minimum center separation between two OP17 zones."""

    first_min_x, first_max_x, first_min_z, first_max_z = (
        _intake_survivor_zone_bounds(first)
    )
    second_min_x, second_max_x, second_min_z, second_max_z = (
        _intake_survivor_zone_bounds(second)
    )
    delta_x = max(
        0,
        second_min_x - first_max_x,
        first_min_x - second_max_x,
    )
    delta_z = max(
        0,
        second_min_z - first_max_z,
        first_min_z - second_max_z,
    )
    return delta_x * delta_x + delta_z * delta_z


def _validate_intake_survivor_movement_zone(prepared: base.PreparedField) -> None:
    """Prove all private roaming zones are on-mesh, clear, and disjoint."""

    entities = set(INTAKE_WANDERING_SURVIVOR_SPECS)
    if (
        entities != set(INTAKE_NATIVE_DIALOGUE_ACTIONS)
        or entities != set(INTAKE_SURVIVOR_MOVEMENT_ZONES)
    ):
        raise SurfaceCampaignBuildError(
            "Intake wandering-survivor inventory changed"
        )
    if (
        INTAKE_SURVIVOR_COLLISION_RADIUS != 16
        or INTAKE_SURVIVOR_WALKMESH_HALO != 24
        or INTAKE_SURVIVOR_MIN_ZONE_SEPARATION != 50
        or INTAKE_SURVIVOR_CENTER_AISLE != (824, 946)
        or INTAKE_SURVIVOR_MIN_DOCTOR_CLEARANCE != 80
        or INTAKE_ARCHIVE_DOOR_POSITION != (867, 1832)
        or INTAKE_SURVIVOR_DOOR_CLEARANCE != 162
    ):
        raise SurfaceCampaignBuildError(
            "Intake survivor movement safety contract changed"
        )

    triangles = base._walkmesh_layer(prepared.components[1], 0)
    endpoints: set[tuple[int, int]] = set()
    for entity, (_pc, _graphic, _retail_position, position) in (
        INTAKE_WANDERING_SURVIVOR_SPECS.items()
    ):
        zone = INTAKE_SURVIVOR_MOVEMENT_ZONES[entity]
        min_x, max_x, min_z, max_z = _intake_survivor_zone_bounds(zone)
        if not min_x <= position[0] <= max_x or not min_z <= position[1] <= max_z:
            raise SurfaceCampaignBuildError(
                f"Intake survivor e{entity} starts outside its movement zone"
            )
        hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if base._point_inside_triangle(position, triangle)
        )
        if len(hits) != 1:
            raise SurfaceCampaignBuildError(
                f"Intake survivor e{entity} start {position} is ambiguous: {hits}"
            )
        if position in endpoints:
            raise SurfaceCampaignBuildError(
                f"Intake survivor e{entity} overlaps another bounded start"
            )
        endpoints.add(position)

        halo = INTAKE_SURVIVOR_WALKMESH_HALO
        halo_bounds = (
            min_x - halo,
            max_x + halo,
            min_z - halo,
            max_z + halo,
        )
        covered_area2 = _intake_walkmesh_rectangle_coverage_area2(
            triangles,
            halo_bounds,
        )
        expected_area2 = Fraction(
            2
            * (halo_bounds[1] - halo_bounds[0])
            * (halo_bounds[3] - halo_bounds[2])
        )
        if covered_area2 != expected_area2:
            raise SurfaceCampaignBuildError(
                f"Intake survivor e{entity} zone plus halo leaves the walkmesh: "
                f"{covered_area2} != {expected_area2} doubled area"
            )

        aisle_min_x, aisle_max_x = INTAKE_SURVIVOR_CENTER_AISLE
        if not (max_x < aisle_min_x or min_x > aisle_max_x):
            raise SurfaceCampaignBuildError(
                f"Intake survivor e{entity} blocks the central waiting-room aisle"
            )

        doctor_x, doctor_z = INTAKE_DOCTOR_WAITING_POSITION
        doctor_delta_x = max(0, min_x - doctor_x, doctor_x - max_x)
        doctor_delta_z = max(0, min_z - doctor_z, doctor_z - max_z)
        if (
            doctor_delta_x * doctor_delta_x
            + doctor_delta_z * doctor_delta_z
            < INTAKE_SURVIVOR_MIN_DOCTOR_CLEARANCE**2
        ):
            raise SurfaceCampaignBuildError(
                f"Intake survivor e{entity} can obstruct the physician route"
            )

    ordered_zones = sorted(INTAKE_SURVIVOR_MOVEMENT_ZONES.items())
    for index, (first_entity, first_zone) in enumerate(ordered_zones):
        for second_entity, second_zone in ordered_zones[index + 1 :]:
            separation_squared = _intake_survivor_zone_separation_squared(
                first_zone,
                second_zone,
            )
            if separation_squared < INTAKE_SURVIVOR_MIN_ZONE_SEPARATION**2:
                raise SurfaceCampaignBuildError(
                    f"Intake survivor zones e{first_entity}/e{second_entity} "
                    "can converge"
                )
            if separation_squared <= (2 * INTAKE_SURVIVOR_COLLISION_RADIUS) ** 2:
                raise SurfaceCampaignBuildError(
                    f"Intake survivor zones e{first_entity}/e{second_entity} "
                    "can collide"
                )


def _install_intake_survivor_movement_bounds(editor: ScriptEditor) -> None:
    """Retain ambient random walking while fencing it away from lobby doors."""

    for entity, (init_pc, graphic, retail_position, position) in (
        INTAKE_WANDERING_SURVIVOR_SPECS.items()
    ):
        expected_init = (
            b"\x0B"
            + base._immediate(graphic)
            + b"\x19"
            + _s16(retail_position[0])
            + _s16(retail_position[1])
            + b"\xC0\x00"
        )
        update_pc = init_pc + len(expected_init)
        idle_stop_pc = update_pc + 2
        if (
            editor.get_script_pointer(entity, 0) != init_pc
            or editor.bytecode[init_pc : init_pc + len(expected_init)]
            != expected_init
            or editor.get_script_pointer(entity, 1) != update_pc
            or editor.bytecode[update_pc : update_pc + 2] != b"\x59\x00"
            or editor.get_script_pointer(entity, 3) != idle_stop_pc
            or editor.bytecode[idle_stop_pc] != 0
        ):
            raise SurfaceCampaignBuildError(
                f"Field 621 wandering survivor e{entity} changed"
            )
        replacement = _intake_wandering_survivor_init(
            graphic=graphic,
            position=position,
            zone=INTAKE_SURVIVOR_MOVEMENT_ZONES[entity],
        )
        replacement_pc = editor.append_and_repoint(entity, 0, replacement)
        if (
            editor.get_script_pointer(entity, 0) != replacement_pc
            or editor.bytecode[
                replacement_pc : replacement_pc + len(replacement)
            ]
            != replacement
            or editor.get_script_pointer(entity, 1) != update_pc
        ):
            raise SurfaceCampaignBuildError(
                f"Field 621 survivor e{entity} movement bound failed"
            )


def _prepare_intake_lore(
    prepared: base.PreparedField,
    *,
    clinic_office: base.PreparedDonorField,
) -> base.PreparedField:
    physician_components = _install_intake_physician_assets(
        prepared, clinic_office
    )
    dialogue = _replace_dialogue_texts(
        prepared.components[7],
        {
            2: (
                "They say the treatment can slow the changes. For the first "
                "time in weeks, I feel hopeful.<Close>"
            ),
            3: (
                "The staff explained each step and promised to help us.\n"
                "I think we finally came to the right place.<Close>"
            ),
            4: (
                "My appointment is soon. Maybe the doctors can steady my "
                "hands and send me home feeling like myself again.<Close>"
            ),
            5: (
                "My brother went in first. He told me not to worry.\n"
                "By tonight, maybe we will both be feeling better.<Close>"
            ),
            6: (
                "They have a test for every symptom.\n"
                "Once my chart is ready, the doctors\n"
                "will know which treatment I need.<Close>"
            ),
            # The layout pass replaces this inherited adult placeholder with
            # the boy's exact, separately frozen line.
            7: (
                "The nanomachines were meant to control the change.\n"
                "These scanners only measure what escaped them.<Close>"
            ),
            8: (
                "The receptionist has been kind to everyone.\n"
                "Sign in at the terminal, and they will call when it is your "
                "turn.<Close>"
            ),
            9: (
                "They say the treatment rooms have the newest equipment. "
                "I hope I am cleared for my first session today.<Close>"
            ),
            10: (
                "Everything is so organized. Patients, staff, and supplies\n"
                "all have their own routes. They must help so many here.<Close>"
            ),
        },
    )
    dialogue, (precheck_id, postcheck_id) = _append_dialogue(
        dialogue,
        (
            RECEPTIONIST_PRECHECK_DIALOGUE,
            RECEPTIONIST_POSTCHECK_DIALOGUE,
        ),
        width=58,
        height=5,
    )
    dialogue, appointment_dialogue_ids = _append_dialogue(
        dialogue,
        (
            LEGACY_ALIAS_CONFIRM_DIALOGUE,
            *DOCTOR_CALL_DIALOGUES,
            *DOCTOR_INSTRUCTION_DIALOGUES,
            CLINIC_DOOR_DENIAL_DIALOGUE,
        ),
        width=58,
        height=5,
    )
    if len(appointment_dialogue_ids) != 8:
        raise SurfaceCampaignBuildError(
            "Field 621 appointment dialogue inventory changed"
        )
    legacy_alias_id = appointment_dialogue_ids[0]
    doctor_call_ids = appointment_dialogue_ids[1:4]
    doctor_instruction_ids = appointment_dialogue_ids[4:7]
    clinic_denial_id = appointment_dialogue_ids[7]
    dialogue, (quarantine_lock_id,) = _append_dialogue(
        dialogue,
        (INTAKE_QUARANTINE_LOCK_DIALOGUE,),
        width=58,
        height=5,
    )
    if quarantine_lock_id != INTAKE_QUARANTINE_LOCK_DIALOGUE_ID:
        raise SurfaceCampaignBuildError(
            "Field 621 Quarantine-shortcut lock dialogue ID changed"
        )
    dialogue, (freight_keycard_lock_id,) = _append_dialogue(
        dialogue,
        (INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE,),
        width=58,
        height=5,
    )
    if freight_keycard_lock_id != INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID:
        raise SurfaceCampaignBuildError(
            "Field 621 freight-keycard lock dialogue ID changed"
        )
    # Preserve the former compound-gate block as unreachable dialogue
    # inventory.  The active e26 and examination-room gates all use the generic
    # security-keycard block above, but keeping this slot freezes later IDs.
    dialogue, (freight_authorization_lock_id,) = _append_dialogue(
        dialogue,
        (INTAKE_FREIGHT_AUTHORIZATION_LOCK_DIALOGUE,),
        width=58,
        height=5,
    )
    if (
        freight_authorization_lock_id
        != INTAKE_FREIGHT_AUTHORIZATION_LOCK_DIALOGUE_ID
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 legacy authorization dialogue inventory changed"
        )
    editor = _retarget_surface_room_actions(
        prepared.components[SCRIPT_INDEX], 621
    )
    if (
        editor.get_script_pointer(INTAKE_REASSIGNED_CIVILIAN_ENTITY, 0)
        != INTAKE_REASSIGNED_CIVILIAN_INIT_PC
        or editor.bytecode[
            INTAKE_REASSIGNED_CIVILIAN_INIT_PC :
            INTAKE_REASSIGNED_CIVILIAN_INIT_PC
            + len(INTAKE_REASSIGNED_CIVILIAN_OLD_INIT)
        ]
        != INTAKE_REASSIGNED_CIVILIAN_OLD_INIT
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 bank-6 civilian initializer changed"
        )
    editor = ScriptEditor(
        base._patch_bytecode(
            editor.to_bytes(),
            INTAKE_REASSIGNED_CIVILIAN_INIT_PC,
            INTAKE_REASSIGNED_CIVILIAN_OLD_INIT,
            INTAKE_REASSIGNED_CIVILIAN_NEW_INIT,
        )
    )
    if (
        editor.get_script_pointer(INTAKE_RECEPTIONIST_ENTITY, 0)
        != INTAKE_RECEPTIONIST_RETAIL_INIT_PC
        or editor.bytecode[
            INTAKE_RECEPTIONIST_RETAIL_INIT_PC :
            INTAKE_RECEPTIONIST_RETAIL_INIT_PC
            + len(INTAKE_RECEPTIONIST_RETAIL_INIT)
        ]
        != INTAKE_RECEPTIONIST_RETAIL_INIT
        or
        editor.get_script_pointer(INTAKE_RECEPTIONIST_ENTITY, 2)
        != INTAKE_RECEPTIONIST_RETAIL_ACTION_PC
        or editor.bytecode[INTAKE_RECEPTIONIST_RETAIL_ACTION_PC] != 0x00
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 saved-stance receptionist action changed"
        )
    if (
        editor.get_script_pointer(INTAKE_ARCHIVE_DOOR_ENTITY, 2)
        != INTAKE_ARCHIVE_DOOR_ACTION_PC
        or editor.bytecode[0x0CE4 : 0x0CE9] != base._change_field(549, 0)
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 door directly behind the receptionist stance changed"
        )
    if (
        editor.get_script_pointer(INTAKE_QUARANTINE_DOOR_ENTITY, 2)
        != INTAKE_QUARANTINE_DOOR_ACTION_PC
        or editor.bytecode[
            INTAKE_QUARANTINE_DOOR_ACTION_PC :
            INTAKE_QUARANTINE_DOOR_ACTION_PC
            + len(INTAKE_QUARANTINE_UNLOCKED_ACTION)
        ]
        != INTAKE_QUARANTINE_UNLOCKED_ACTION
        or editor.bytecode[
            INTAKE_QUARANTINE_DOOR_CHANGE_PC :
            INTAKE_QUARANTINE_DOOR_CHANGE_PC + 5
        ]
        != base._change_field(*INTAKE_QUARANTINE_DESTINATION)
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 marked Quarantine door foundation changed"
        )
    if (
        editor.get_script_pointer(INTAKE_FREIGHT_DOOR_ENTITY, 2)
        != INTAKE_FREIGHT_DOOR_ACTION_PC
        or editor.bytecode[
            INTAKE_FREIGHT_DOOR_ACTION_PC :
            INTAKE_FREIGHT_DOOR_ACTION_PC + len(INTAKE_FREIGHT_UNLOCKED_ACTION)
        ]
        != INTAKE_FREIGHT_UNLOCKED_ACTION
        or editor.bytecode[
            INTAKE_FREIGHT_DOOR_CHANGE_PC :
            INTAKE_FREIGHT_DOOR_CHANGE_PC + 5
        ]
        != base._change_field(*INTAKE_FREIGHT_DESTINATION)
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 saved freight-door foundation changed"
        )
    if (
        editor.get_script_pointer(INTAKE_PATIENT_DOOR_ENTITY, 2)
        != INTAKE_PATIENT_DOOR_ACTION_PC
        or editor.bytecode[
            INTAKE_PATIENT_DOOR_ACTION_PC :
            INTAKE_PATIENT_DOOR_ACTION_PC + len(INTAKE_PATIENT_UNLOCKED_ACTION)
        ]
        != INTAKE_PATIENT_UNLOCKED_ACTION
        or editor.bytecode[
            INTAKE_PATIENT_DOOR_CHANGE_PC :
            INTAKE_PATIENT_DOOR_CHANGE_PC + 5
        ]
        != base._change_field(*INTAKE_PATIENT_DESTINATION)
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 patient-service door foundation changed"
        )
    if (
        editor.get_script_pointer(INTAKE_CLINIC_DOOR_ENTITY, 2)
        != INTAKE_CLINIC_DOOR_ACTION_PC
        or editor.bytecode[
            INTAKE_CLINIC_DOOR_ACTION_PC :
            INTAKE_CLINIC_DOOR_ACTION_PC + len(INTAKE_CLINIC_DOOR_ACTION)
        ]
        != INTAKE_CLINIC_DOOR_ACTION
        or editor.get_script_pointer(
            INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
            INTAKE_DOCTOR_DOOR_OPEN_SCRIPT,
        )
        != INTAKE_DOCTOR_DOOR_OPEN_PC
        or editor.bytecode[
            INTAKE_DOCTOR_DOOR_OPEN_PC :
            INTAKE_DOCTOR_DOOR_OPEN_PC
            + len(
                base.mass_driver._world_position_static_slide_body(
                    start_x=0,
                    start_z=0,
                    delta_x=0,
                    delta_z=2,
                    iterations=INTAKE_DOCTOR_DOOR_SLIDE_FRAMES,
                )
            )
        ]
        != base.mass_driver._world_position_static_slide_body(
            start_x=0,
            start_z=0,
            delta_x=0,
            delta_z=2,
            iterations=INTAKE_DOCTOR_DOOR_SLIDE_FRAMES,
        )
        or editor.get_script_pointer(
            INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
            INTAKE_DOCTOR_DOOR_CLOSE_SCRIPT,
        )
        != INTAKE_DOCTOR_DOOR_RETAIL_CLOSE_STOP_PC
        or editor.bytecode[INTAKE_DOCTOR_DOOR_RETAIL_CLOSE_STOP_PC] != 0
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 examination-room door foundation changed"
        )
    action_pc = editor.bytecode_size
    if action_pc != INTAKE_RECEPTIONIST_ACTION_PC:
        raise SurfaceCampaignBuildError("Field 621 receptionist append point moved")
    if editor.append_and_repoint(
        INTAKE_RECEPTIONIST_ENTITY,
        2,
        _intake_receptionist_action(
            precheck_dialogue_id=precheck_id,
            postcheck_dialogue_id=postcheck_id,
            routine_pc=action_pc,
        ),
    ) != action_pc:
        raise SurfaceCampaignBuildError("Field 621 receptionist action moved")
    wide_init_pc = editor.bytecode_size
    if wide_init_pc != INTAKE_RECEPTIONIST_WIDE_INIT_PC:
        raise SurfaceCampaignBuildError("Field 621 receptionist init append point moved")
    if (
        editor.append_and_repoint(
            INTAKE_RECEPTIONIST_ENTITY,
            0,
            _intake_receptionist_init(),
        )
        != wide_init_pc
    ):
        raise SurfaceCampaignBuildError("Field 621 receptionist init moved")

    if editor.entity_count != INTAKE_DOCTOR_ENTITY:
        raise SurfaceCampaignBuildError(
            "Field 621 doctor no longer begins at the pre-seal entity boundary"
        )
    _validate_intake_doctor_route(prepared)
    doctor_record = Console(
        INTAKE_DOCTOR_STAGING_POSITION[0],
        INTAKE_DOCTOR_STAGING_POSITION[1],
        86,
        0,
        "",
    )
    _validate_console_points(prepared, (doctor_record,))
    header = _insert_controller_records(
        prepared.header,
        old_entity_count=editor.entity_count,
        consoles=(doctor_record,),
    )
    editor = ScriptEditor(
        base.mass_driver._extend_atel_entity_table(
            editor.to_bytes(), editor.entity_count + 1
        )
    )
    doctor_stop_pc = editor.append_raw_routine(b"\x00")
    for script_index in range(32):
        editor.set_script_pointer(
            INTAKE_DOCTOR_ENTITY,
            script_index,
            doctor_stop_pc,
        )

    editor.append_and_repoint(
        INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
        INTAKE_DOCTOR_DOOR_CLOSE_SCRIPT,
        base.mass_driver._world_position_static_slide_body(
            start_x=0,
            start_z=INTAKE_DOCTOR_DOOR_OPEN_OFFSET_Z,
            delta_x=0,
            delta_z=-2,
            iterations=INTAKE_DOCTOR_DOOR_SLIDE_FRAMES,
        ),
    )
    doctor_init_pc = editor.bytecode_size
    editor.append_and_repoint(
        INTAKE_DOCTOR_ENTITY,
        0,
        _intake_doctor_init(routine_pc=doctor_init_pc),
    )
    doctor_action_pc = editor.bytecode_size
    editor.append_and_repoint(
        INTAKE_DOCTOR_ENTITY,
        2,
        _intake_doctor_action(
            instruction_dialogue_ids=doctor_instruction_ids,
            routine_pc=doctor_action_pc,
        ),
    )
    doctor_update_pc = editor.bytecode_size
    editor.append_and_repoint(
        INTAKE_DOCTOR_ENTITY,
        1,
        _intake_doctor_update(
            legacy_menu_dialogue_id=legacy_alias_id,
            call_dialogue_ids=doctor_call_ids,
            routine_pc=doctor_update_pc,
        ),
    )
    clinic_gate_pc = editor.bytecode_size
    editor.append_and_repoint(
        INTAKE_CLINIC_DOOR_ENTITY,
        2,
        _clinic_door_gate_action(
            old_action_pc=INTAKE_CLINIC_DOOR_ACTION_PC,
            denial_dialogue_id=clinic_denial_id,
            routine_pc=clinic_gate_pc,
        ),
    )
    _install_intake_native_dialogue_mutexes(editor)
    _validate_intake_survivor_movement_zone(prepared)
    _install_intake_survivor_movement_bounds(editor)
    lock_pc = editor.bytecode_size
    if lock_pc != INTAKE_QUARANTINE_LOCK_ACTION_PC:
        raise SurfaceCampaignBuildError(
            "Field 621 Quarantine-shortcut gate append point moved: "
            f"0x{lock_pc:04X}"
        )
    lock_action = _intake_quarantine_locked_action(
        dialogue_id=quarantine_lock_id,
        unlocked_action_pc=INTAKE_QUARANTINE_DOOR_ACTION_PC,
        routine_pc=lock_pc,
    )
    if (
        editor.append_and_repoint(
            INTAKE_QUARANTINE_DOOR_ENTITY,
            2,
            lock_action,
        )
        != lock_pc
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 Quarantine-shortcut gate action moved"
        )
    freight_gate_pc = editor.bytecode_size
    if freight_gate_pc != INTAKE_FREIGHT_KEYCARD_GATE_ACTION_PC:
        raise SurfaceCampaignBuildError(
            "Field 621 freight-keycard gate append point moved: "
            f"0x{freight_gate_pc:04X}"
        )
    freight_gate = _intake_freight_keycard_gate_action(
        dialogue_id=freight_keycard_lock_id,
        unlocked_action_pc=INTAKE_FREIGHT_DOOR_ACTION_PC,
        routine_pc=freight_gate_pc,
    )
    if (
        editor.append_and_repoint(
            INTAKE_FREIGHT_DOOR_ENTITY,
            2,
            freight_gate,
        )
        != freight_gate_pc
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 freight-keycard gate action moved"
        )
    patient_gate_pc = editor.bytecode_size
    if patient_gate_pc != INTAKE_PATIENT_KEYCARD_GATE_ACTION_PC:
        raise SurfaceCampaignBuildError(
            "Field 621 patient-keycard gate append point moved: "
            f"0x{patient_gate_pc:04X}"
        )
    patient_gate = _intake_freight_keycard_gate_action(
        dialogue_id=freight_keycard_lock_id,
        unlocked_action_pc=INTAKE_PATIENT_DOOR_ACTION_PC,
        routine_pc=patient_gate_pc,
    )
    if (
        editor.append_and_repoint(
            INTAKE_PATIENT_DOOR_ENTITY,
            2,
            patient_gate,
        )
        != patient_gate_pc
    ):
        raise SurfaceCampaignBuildError(
            "Field 621 patient-keycard gate action moved"
        )
    rebuilt = _rebuild_field(
        prepared,
        editor=editor,
        header=header,
        dialogue=dialogue,
        component_updates=physician_components,
        role_suffix=(
            "wide saved-stance receptionist interaction and state-aware "
            "check-in directions; exact office-physician asset, one-minute "
            "alias appointment, physician "
            "call, and player-controlled office follow-through; "
            "native survivor wandering bounded away from the north Archive leaf; "
            "pre-revelation hopeful intake testimony, signed circulation, and "
            "live-audited Archive/Quarantine room swap with the marked west "
            "e22 Quarantine entrance keyed by its dedicated credential; e24 "
            "patient service, e26 treatment preparation, and three bright "
            "examination rooms gated by the clinic security keycard"
        ),
    )
    return replace(
        rebuilt,
        spec=replace(
            rebuilt.spec,
            edges=_retarget_surface_edges(rebuilt.spec.edges, 621),
        ),
    )


def _isolate_quarantine_relay_selection(editor: ScriptEditor) -> ScriptEditor:
    """Move exactly the audited relay-selection operands out of campaign state."""

    script = editor.to_bytes()
    for pc in QUARANTINE_RELAY_SELECTION_OPERAND_PCS:
        script = base._patch_bytecode(
            script,
            pc,
            _u16(STATE_OPERAND),
            _u16(LOCAL_PUZZLE_OPERAND),
        )
    migrated = ScriptEditor(script)
    if migrated.bytecode_size != editor.bytecode_size:
        raise SurfaceCampaignBuildError(
            "Field 620 relay-state isolation changed bytecode size"
        )
    return migrated


def _prepare_quarantine_lore(prepared: base.PreparedField) -> base.PreparedField:
    dialogue = _replace_dialogue_texts(
        prepared.components[7],
        {
            13: (
                "Word spread that flesh from the unafflicted could quiet the pain.\n"
                "That desperate rumor led many of us here.<Close>"
            ),
            17: (
                "The limiter is gone. The machine calls that failure.\n"
                "I call it the truth finally surfacing.<Close>"
            ),
            19: (
                "Solaris divided people by caste.\n"
                "Pain does not recognize those categories.<Close>"
            ),
        },
    )
    dialogue, (current_end_dialogue_id,) = _append_dialogue(
        dialogue,
        (QUARANTINE_COMPLETION_DIALOGUE,),
        width=58,
        height=4,
    )
    if current_end_dialogue_id != QUARANTINE_CURRENT_END_DIALOGUE_ID:
        raise SurfaceCampaignBuildError(
            "Field 620 completion dialogue ID changed"
        )
    editor = _retarget_surface_room_actions(
        prepared.components[SCRIPT_INDEX], 620
    )
    if (
        editor.get_script_pointer(QUARANTINE_CURRENT_END_DOOR_ENTITY, 2)
        != base.QUARANTINE_DOOR_GATE_PC
        or editor.bytecode[
            base.QUARANTINE_DOOR_GATE_PC :
            base.QUARANTINE_DOOR_GATE_PC
            + len(base.QUARANTINE_DOOR_GATE_FINAL_ROUTINE)
        ]
        != base.QUARANTINE_DOOR_GATE_FINAL_ROUTINE
    ):
        raise SurfaceCampaignBuildError(
            "Field 620 east continuation-door foundation changed"
        )
    editor = _isolate_quarantine_relay_selection(editor)
    rebuilt = _rebuild_field(
        prepared,
        editor=editor,
        dialogue=dialogue,
        role_suffix=(
            "Verus testimony aligned to the limiter and virus timeline; "
            "relay selection isolated from appointment state; "
            "live-audited Archive/Quarantine room swap"
        ),
    )
    return replace(
        rebuilt,
        spec=replace(
            rebuilt.spec,
            edges=_retarget_surface_edges(rebuilt.spec.edges, 620),
        ),
    )


def _prepare_quarantine_completion(
    prepared: base.PreparedField,
) -> base.PreparedField:
    """Restore the diagnostic award and the native east-door continuation."""

    if prepared.spec.identity.scene != 620:
        raise SurfaceCampaignBuildError(
            "Current-end door transform received a non-Quarantine field"
        )
    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    expected_gate = bytearray(base.QUARANTINE_DOOR_GATE_FINAL_ROUTINE)
    relay_offset = (
        QUARANTINE_RELAY_SELECTION_OPERAND_PCS[-1]
        - base.QUARANTINE_DOOR_GATE_PC
    )
    expected_gate[relay_offset : relay_offset + 2] = _u16(
        LOCAL_PUZZLE_OPERAND
    )
    if (
        editor.bytecode_size != QUARANTINE_CURRENT_END_DOOR_ACTION_PC
        or editor.get_script_pointer(QUARANTINE_CURRENT_END_DOOR_ENTITY, 2)
        != base.QUARANTINE_DOOR_GATE_PC
        or editor.bytecode[
            base.QUARANTINE_DOOR_GATE_PC :
            base.QUARANTINE_DOOR_GATE_PC
            + len(base.QUARANTINE_DOOR_GATE_FINAL_ROUTINE)
        ]
        != bytes(expected_gate)
    ):
        raise SurfaceCampaignBuildError(
            "Field 620 post-clearance east continuation foundation changed"
        )
    routine = base.mass_driver._RoutineBuilder(QUARANTINE_CURRENT_END_DOOR_ACTION_PC)
    routine.jump_if_bit_clear(STATE_OPERAND, 0x0100, "diagnose")
    routine.emit(_jump(base.QUARANTINE_EAST_DOOR_SUCCESS_PC))
    routine.label("diagnose")
    routine.jump_if_not_equal(LOCAL_PUZZLE_OPERAND, 0x0070, "denied")
    routine.emit(b"\x33\xFE\x54")
    routine.emit(base.mass_driver._wait_for_pad_release(
        base.mass_driver.PAD_MASK_CROSS, routine.pc,
    ))
    routine.emit(base.mass_driver._wait())
    routine.emit(PROGRESSION_CONFIRM_SOUND)
    routine.emit(b"\xF5" + _u16(QUARANTINE_CURRENT_END_DIALOGUE_ID) + b"\x01\x9C")
    routine.emit(base.mass_driver._wait_for_pad_release(
        base.mass_driver.PAD_MASK_CROSS, routine.pc,
    ))
    routine.emit(base.mass_driver._wait())
    routine.emit(_set_bit(STATE_OPERAND, 8))
    routine.emit(_jump(base.QUARANTINE_EAST_DOOR_SUCCESS_PC))
    routine.label("denied")
    routine.emit(_repeatable_dialogue_action(9, routine.pc))
    action = routine.finish()
    if (
        editor.append_and_repoint(
            QUARANTINE_CURRENT_END_DOOR_ENTITY,
            2,
            action,
        )
        != QUARANTINE_CURRENT_END_DOOR_ACTION_PC
    ):
        raise SurfaceCampaignBuildError(
            "Field 620 completion door action moved"
        )
    return _rebuild_field(
        prepared,
        editor=editor,
        role_suffix=(
            "east e24 validates the three biological relays with caste excluded, "
            "commits quarantine clearance and opens the native Service door; "
            "west e23 Intake return preserved"
        ),
    )


def _load_clinic_source(donor_disc: Path | str) -> tuple[bytes, bytes]:
    """Load and freeze Disc 1 field 352, the compact Ethos infirmary."""

    image = Mode2Image(donor_disc)
    entries = image.read_index()
    directories = image.read_directories()
    if base.FIELD_DIRECTORY >= len(directories):
        raise SurfaceCampaignBuildError("Disc 1 field directory is absent")
    first = directories[base.FIELD_DIRECTORY].first_file
    local = base.FIRST_FIELD_LOCAL_FILE + 2 * CLINIC_SOURCE_SCENE
    resolved: list[bytes] = []
    for expected_id, local_file in (
        (CLINIC_SOURCE_BUNDLE_ID, local),
        (CLINIC_SOURCE_GRAPHICS_ID, local + 1),
    ):
        fat_index = directory_file_fat_index(first, local_file)
        if fat_index + 5 != expected_id or not 0 <= fat_index < len(entries):
            raise SurfaceCampaignBuildError(
                f"Clinic source file resolved to canonical {fat_index + 5}, "
                f"expected {expected_id}"
            )
        resolved.append(image.extract_entry(entries[fat_index]))

    bundle, graphics = resolved
    if (
        len(bundle),
        _sha256(bundle),
        len(graphics),
        _sha256(graphics),
    ) != (
        CLINIC_SOURCE_BUNDLE_SIZE,
        CLINIC_SOURCE_BUNDLE_SHA256,
        CLINIC_SOURCE_GRAPHICS_SIZE,
        CLINIC_SOURCE_GRAPHICS_SHA256,
    ):
        raise SurfaceCampaignBuildError("Disc 1 clinic source identity changed")
    parsed = parse_field(bundle)
    script = parsed.parts[SCRIPT_INDEX].data
    dialogue = parsed.parts[7].data
    if (
        len(parsed.header),
        _sha256(parsed.header),
        len(script),
        _sha256(script),
        len(dialogue),
        _sha256(dialogue),
    ) != (
        CLINIC_SOURCE_HEADER_SIZE,
        CLINIC_SOURCE_HEADER_SHA256,
        CLINIC_SOURCE_SCRIPT_SIZE,
        CLINIC_SOURCE_SCRIPT_SHA256,
        CLINIC_SOURCE_DIALOGUE_SIZE,
        CLINIC_SOURCE_DIALOGUE_SHA256,
    ):
        raise SurfaceCampaignBuildError("Disc 1 clinic field streams changed")
    return bundle, graphics


def _load_clinic_security_formation(donor_disc: Path | str) -> bytes:
    """Read and freeze the authentic field-551 Solaris security formation."""

    image = Mode2Image(donor_disc)
    entries = image.read_index()
    directories = image.read_directories()
    if base.FIELD_DIRECTORY >= len(directories):
        raise SurfaceCampaignBuildError("Disc 1 field directory is absent")
    local = base.FIRST_FIELD_LOCAL_FILE + 2 * CLINIC_SECURITY_SOURCE_SCENE
    fat_index = directory_file_fat_index(
        directories[base.FIELD_DIRECTORY].first_file,
        local,
    )
    if (
        fat_index + 5 != CLINIC_SECURITY_SOURCE_BUNDLE_ID
        or not 0 <= fat_index < len(entries)
    ):
        raise SurfaceCampaignBuildError(
            "Clinic security donor resolved to the wrong canonical file"
        )
    bundle = image.extract_entry(entries[fat_index])
    if (
        len(bundle) != CLINIC_SECURITY_SOURCE_BUNDLE_SIZE
        or _sha256(bundle) != CLINIC_SECURITY_SOURCE_BUNDLE_SHA256
    ):
        raise SurfaceCampaignBuildError("Field 551 security donor changed")
    encounters_data = parse_field(bundle).parts[6].data
    encounters = EncounterTable(encounters_data)
    formation = encounters.formation(CLINIC_SECURITY_SOURCE_CONFIGURATION)
    bright_arena_proof = encounters.formation(
        CLINIC_SECURITY_BRIGHT_ARENA_CONFIGURATION
    )
    if (
        _sha256(encounters_data)
        != CLINIC_SECURITY_SOURCE_ENCOUNTER_SHA256
        or encounters.get_weight(CLINIC_SECURITY_SOURCE_CONFIGURATION) != 4
        or formation != CLINIC_SECURITY_SOURCE_FORMATION
        or bright_arena_proof
        != CLINIC_SECURITY_BRIGHT_ARENA_PROOF_FORMATION
    ):
        raise SurfaceCampaignBuildError(
            "Field 551 Solaris security or bright-arena proof changed"
        )
    return formation


def _load_clinic_security_overworld_assets(
    donor_disc: Path | str,
) -> Mapping[int, tuple[bytes, bytes]]:
    """Load exact Imperial-escort and Security-Cube actor/sprite banks."""

    image = Mode2Image(donor_disc)
    entries = image.read_index()
    directories = image.read_directories()
    if base.FIELD_DIRECTORY >= len(directories):
        raise SurfaceCampaignBuildError("Disc 1 field directory is absent")
    first = directories[base.FIELD_DIRECTORY].first_file
    contracts = (
        (
            "Solaris Imperial escort",
            CLINIC_SECURITY_GUARD_SOURCE_SCENE,
            CLINIC_SECURITY_GUARD_SOURCE_BUNDLE_ID,
            CLINIC_SECURITY_GUARD_SOURCE_BUNDLE_SIZE,
            CLINIC_SECURITY_GUARD_SOURCE_BUNDLE_SHA256,
            CLINIC_SECURITY_GUARD_SOURCE_BANK,
            CLINIC_SECURITY_GUARD_ACTOR_SIZE,
            CLINIC_SECURITY_GUARD_ACTOR_SHA256,
            CLINIC_SECURITY_GUARD_SPRITE_SIZE,
            CLINIC_SECURITY_GUARD_SPRITE_SHA256,
            CLINIC_SECURITY_GUARD_MAPPING,
            CLINIC_SECURITY_GUARD_TARGET_BANK,
        ),
        (
            "Security Cube",
            CLINIC_SECURITY_CUBE_SOURCE_SCENE,
            CLINIC_SECURITY_CUBE_SOURCE_BUNDLE_ID,
            CLINIC_SECURITY_CUBE_SOURCE_BUNDLE_SIZE,
            CLINIC_SECURITY_CUBE_SOURCE_BUNDLE_SHA256,
            CLINIC_SECURITY_CUBE_SOURCE_BANK,
            CLINIC_SECURITY_CUBE_ACTOR_SIZE,
            CLINIC_SECURITY_CUBE_ACTOR_SHA256,
            CLINIC_SECURITY_CUBE_SPRITE_SIZE,
            CLINIC_SECURITY_CUBE_SPRITE_SHA256,
            CLINIC_SECURITY_CUBE_SOURCE_MAPPING,
            CLINIC_SECURITY_CUBE_TARGET_BANK,
        ),
    )
    result: dict[int, tuple[bytes, bytes]] = {}
    for (
        label,
        scene,
        canonical_id,
        expected_bundle_size,
        expected_bundle_sha256,
        source_bank,
        expected_actor_size,
        expected_actor_sha256,
        expected_sprite_size,
        expected_sprite_sha256,
        expected_mapping,
        target_bank,
    ) in contracts:
        local = base.FIRST_FIELD_LOCAL_FILE + 2 * scene
        fat_index = directory_file_fat_index(first, local)
        if fat_index + 5 != canonical_id or not 0 <= fat_index < len(entries):
            raise SurfaceCampaignBuildError(
                f"Clinic {label} donor resolved to the wrong canonical file"
            )
        bundle = image.extract_entry(entries[fat_index])
        if (
            len(bundle) != expected_bundle_size
            or _sha256(bundle) != expected_bundle_sha256
        ):
            raise SurfaceCampaignBuildError(f"Clinic {label} donor changed")
        parsed = parse_field(bundle)
        actors = base.mass_driver._indexed_bundle_entries(
            parsed.parts[base.mass_driver.ACTOR_INDEX].data
        )
        sprites = base.mass_driver._indexed_bundle_entries(
            parsed.parts[base.mass_driver.SPRITE_INDEX].data
        )
        if not 0 <= source_bank < min(len(actors), len(sprites)):
            raise SurfaceCampaignBuildError(f"Clinic {label} bank moved")
        actor = actors[source_bank]
        sprite = sprites[source_bank]
        mapping = struct.unpack_from("<4H", parsed.header, source_bank * 8)
        if (
            len(actor) != expected_actor_size
            or _sha256(actor) != expected_actor_sha256
            or len(sprite) != expected_sprite_size
            or _sha256(sprite) != expected_sprite_sha256
            or mapping != expected_mapping
        ):
            raise SurfaceCampaignBuildError(f"Clinic {label} assets changed")
        result[target_bank] = (actor, sprite)

    guard_actor = result[CLINIC_SECURITY_GUARD_TARGET_BANK][0]
    guard_sections = base.mass_driver._indexed_bundle_entries(guard_actor)
    if (
        len(guard_sections) != 3
        or len(guard_sections[2]) != 132
        or _sha256(guard_sections[2][100:132])
        != CLINIC_SECURITY_GUARD_PALETTE_SHA256
    ):
        raise SurfaceCampaignBuildError("Clinic Imperial escort palette 3 changed")
    if set(result) != {
        CLINIC_SECURITY_CUBE_TARGET_BANK,
        CLINIC_SECURITY_GUARD_TARGET_BANK,
    }:
        raise SurfaceCampaignBuildError("Clinic security target banks overlap")
    return result


def _install_clinic_security_overworld_assets(
    header: bytes,
    components: Sequence[bytes],
    assets: Mapping[int, tuple[bytes, bytes]],
) -> tuple[bytes, bytes]:
    """Replace only field 352's two retired local actor/sprite banks."""

    actor_index = base.mass_driver.ACTOR_INDEX
    sprite_index = base.mass_driver.SPRITE_INDEX
    if (
        _sha256(components[actor_index])
        != CLINIC_SECURITY_TARGET_ACTOR_COMPONENT_SHA256
        or _sha256(components[sprite_index])
        != CLINIC_SECURITY_TARGET_SPRITE_COMPONENT_SHA256
    ):
        raise SurfaceCampaignBuildError("Clinic security bank destination changed")
    actors = list(
        base.mass_driver._indexed_bundle_entries(components[actor_index])
    )
    sprites = list(
        base.mass_driver._indexed_bundle_entries(components[sprite_index])
    )
    if len(actors) != 4 or len(sprites) != 4:
        raise SurfaceCampaignBuildError("Clinic local actor inventory changed")
    for target_bank, (actor, sprite) in assets.items():
        expected_mapping = {
            CLINIC_SECURITY_CUBE_TARGET_BANK: CLINIC_SECURITY_CUBE_MAPPING,
            CLINIC_SECURITY_GUARD_TARGET_BANK: CLINIC_SECURITY_GUARD_MAPPING,
        }[target_bank]
        if struct.unpack_from("<4H", header, target_bank * 8) != expected_mapping:
            raise SurfaceCampaignBuildError(
                f"Clinic security target mapping {target_bank} changed"
            )
        actors[target_bank] = actor
        sprites[target_bank] = sprite
    actor_component = base.mass_driver._rebuild_indexed_bundle(
        components[actor_index], actors
    )
    sprite_component = base.mass_driver._rebuild_indexed_bundle(
        components[sprite_index], sprites
    )
    if (
        len(actor_component) != CLINIC_SECURITY_INSTALLED_ACTOR_COMPONENT_SIZE
        or _sha256(actor_component)
        != CLINIC_SECURITY_INSTALLED_ACTOR_COMPONENT_SHA256
        or len(sprite_component)
        != CLINIC_SECURITY_INSTALLED_SPRITE_COMPONENT_SIZE
        or _sha256(sprite_component)
        != CLINIC_SECURITY_INSTALLED_SPRITE_COMPONENT_SHA256
    ):
        raise SurfaceCampaignBuildError(
            "Clinic exact overworld security banks are not deterministic"
        )
    return actor_component, sprite_component


def _prepare_clinic_office(donor_disc: Path | str) -> base.PreparedDonorField:
    """Transplant field 352 into logical field 550 as the examination room."""

    source_bundle, graphics = _load_clinic_source(donor_disc)
    security_source_formation = _load_clinic_security_formation(donor_disc)
    security_overworld_assets = _load_clinic_security_overworld_assets(donor_disc)
    parsed = parse_field(source_bundle)
    components = [part.data for part in parsed.parts]
    (
        components[base.mass_driver.ACTOR_INDEX],
        components[base.mass_driver.SPRITE_INDEX],
    ) = _install_clinic_security_overworld_assets(
        parsed.header, components, security_overworld_assets
    )
    script = base._patch_bytecode(
        components[SCRIPT_INDEX],
        1,
        CLINIC_ENTRY_SOURCE,
        CLINIC_ENTRY_PLAYABLE,
    )
    script = base._patch_donor_party(script, CLINIC_PARTY_INIT_PCS)
    editor = ScriptEditor(script)
    if (
        editor.entity_count != 19
        or editor.bytecode_size != 0x068C
        or editor.get_script_pointer(0, 0) != 0x000F
        or tuple(
            editor.get_script_pointer(entity, 0)
            for entity in CLINIC_PARTY_ENTITIES
        )
        != CLINIC_PARTY_INIT_PCS
        or editor.get_script_pointer(CLINIC_DOCTOR_ENTITY, 0) != 0x054B
        or editor.get_script_pointer(CLINIC_DOCTOR_ENTITY, 1) != 0x058A
        or editor.get_script_pointer(CLINIC_EXIT_ENTITY, 0) != 0x0649
        or editor.get_script_pointer(CLINIC_EXIT_ENTITY, 2) != 0x065C
        or editor.bytecode[
            0x065C :
            0x065C
            + len(
                _clinic_native_field_change_action(
                    destination_field=CLINIC_SOURCE_RETURN_FIELD,
                    destination_parameter=CLINIC_SOURCE_RETURN_PARAMETER,
                )
            )
        ]
        != _clinic_native_field_change_action(
            destination_field=CLINIC_SOURCE_RETURN_FIELD,
            destination_parameter=CLINIC_SOURCE_RETURN_PARAMETER,
        )
        or editor.get_script_pointer(CLINIC_EXIT_HELPER_ENTITY, 4)
        != CLINIC_EXIT_HELPER_PC
        or editor.bytecode[
            CLINIC_EXIT_HELPER_PC :
            CLINIC_EXIT_HELPER_PC + len(CLINIC_EXIT_HELPER_BODY)
        ]
        != CLINIC_EXIT_HELPER_BODY
    ):
        raise SurfaceCampaignBuildError("Clinic native actor/door foundation changed")

    # Give every retired retail event an explicit terminal target.  Only the
    # safe field initializer, player initializers/updates, and native door-leaf
    # helper remain reachable from field 352's story scripting.
    stop_pc = editor.append_raw_routine(b"\x00")
    if stop_pc != CLINIC_SHARED_STOP_PC:
        raise SurfaceCampaignBuildError("Clinic shared STOP moved")
    retained_slots = {
        (0, 0),
        *((entity, slot) for entity in CLINIC_PARTY_ENTITIES for slot in (0, 1)),
        (CLINIC_EXIT_HELPER_ENTITY, 0),
        (CLINIC_EXIT_HELPER_ENTITY, 4),
    }
    for entity in range(editor.entity_count):
        for script_index in range(32):
            if (entity, script_index) not in retained_slots:
                editor.set_script_pointer(entity, script_index, stop_pc)

    contract = DONOR_DOOR_COLLISION_CONTRACTS[550][0]
    exit_init_pc = editor.append_and_repoint(
        CLINIC_EXIT_ENTITY,
        0,
        _expected_donor_door_controller_init(contract),
    )
    exit_action_pc = editor.append_and_repoint(
        CLINIC_EXIT_ENTITY,
        2,
        _clinic_native_field_change_action(
            destination_field=CLINIC_RETURN_FIELD,
            destination_parameter=CLINIC_RETURN_PARAMETER,
        ),
    )
    if (exit_init_pc, exit_action_pc) != (
        CLINIC_EXIT_INIT_PC,
        CLINIC_EXIT_ACTION_PC,
    ):
        raise SurfaceCampaignBuildError("Clinic reciprocal door routines moved")

    dialogue, clinic_dialogue_ids = _append_dialogue(
        components[7],
        (
            CLINIC_BRIEFING_DIALOGUE,
            CLINIC_EXIT_INSISTENCE_DIALOGUE,
            CLINIC_FIRST_REFUSAL_DIALOGUE,
            CLINIC_SECURITY_CALL_DIALOGUE,
            CLINIC_SECURITY_ARRIVAL_DIALOGUE,
            CLINIC_DOCTOR_ESCAPE_DIALOGUE,
            CLINIC_ESCAPE_IN_PROGRESS_DIALOGUE,
            CLINIC_SECURITY_KEYCARD_DIALOGUE,
        ),
        width=58,
        height=5,
    )
    expected_dialogue_ids = tuple(
        range(
            CLINIC_BRIEFING_DIALOGUE_ID,
            CLINIC_SECURITY_KEYCARD_DIALOGUE_ID + 1,
        )
    )
    if clinic_dialogue_ids != expected_dialogue_ids:
        raise SurfaceCampaignBuildError("Clinic sequence dialogue IDs changed")
    record_replacements = {
        dialogue_id: (58, 5, text)
        for dialogue_id, text in zip(
            CLINIC_RECORD_ALIAS_DIALOGUE_IDS,
            CLINIC_RECORD_DIALOGUES,
            strict=True,
        )
    }
    record_replacements[CLINIC_RECORD_MISSING_DIALOGUE_ID] = (
        58,
        3,
        CLINIC_RECORD_MISSING_DIALOGUE,
    )
    dialogue = _replace_dialogue_blocks_same_size(
        dialogue,
        record_replacements,
        padding_id=CLINIC_RECORD_DIALOGUE_PADDING_ID,
    )
    parsed_clinic_dialogue = parse_dialogue(dialogue)
    for dialogue_id in (
        *clinic_dialogue_ids,
        *CLINIC_RECORD_ALIAS_DIALOGUE_IDS,
        CLINIC_RECORD_MISSING_DIALOGUE_ID,
    ):
        block = parsed_clinic_dialogue.blocks[dialogue_id]
        if dialogue_id in CLINIC_RECORD_ALIAS_DIALOGUE_IDS:
            measurable_text = re.sub(
                r"<Opcode:0A:(?:00|01)>", "255", block.text
            )
            block = parse_dialogue(
                encode_dialogue(
                    (
                        DialogueBlockSpec(
                            0,
                            block.width,
                            block.height,
                            measurable_text,
                        ),
                    )
                )
            ).blocks[0]
        issues = _campaign_dialogue_layout_issues(block)
        if issues:
            raise SurfaceCampaignBuildError(
                f"Clinic dialogue {dialogue_id} exceeds its window: {issues}"
            )
    if tuple(
        parsed_clinic_dialogue.blocks[dialogue_id].text
        for dialogue_id in CLINIC_RECORD_ALIAS_DIALOGUE_IDS
    ) != CLINIC_RECORD_DIALOGUES or (
        parsed_clinic_dialogue.blocks[CLINIC_RECORD_MISSING_DIALOGUE_ID].text
        != CLINIC_RECORD_MISSING_DIALOGUE
    ):
        raise SurfaceCampaignBuildError("Clinic record dialogue changed on encode")
    (
        briefing_dialogue_id,
        _exit_insistence_dialogue_id,
        first_refusal_dialogue_id,
        security_call_dialogue_id,
        security_arrival_dialogue_id,
        escape_dialogue_id,
        _escape_in_progress_dialogue_id,
        keycard_dialogue_id,
    ) = clinic_dialogue_ids

    terminal_inits = tuple(
        _console_init(console) for console in CLINIC_RECORD_TERMINALS
    )
    terminal_action_pc = CLINIC_RECORD_TERMINAL_INIT_PC + len(terminal_inits[0])
    if terminal_action_pc != CLINIC_RECORD_TERMINAL_ACTION_PC:
        raise SurfaceCampaignBuildError("Clinic record terminal action moved")
    terminal_action = _clinic_record_terminal_action(
        alias_dialogue_ids=CLINIC_RECORD_ALIAS_DIALOGUE_IDS,
        missing_dialogue_id=CLINIC_RECORD_MISSING_DIALOGUE_ID,
        routine_pc=terminal_action_pc,
    )
    cavity = editor.bytecode[
        CLINIC_RECORD_TERMINAL_INIT_PC : CLINIC_RECORD_TERMINAL_CAVITY_END_PC
    ]
    terminal_aux_init_pc = terminal_action_pc + len(terminal_action)
    if terminal_aux_init_pc != CLINIC_RECORD_TERMINAL_AUX_INIT_PCS[0]:
        raise SurfaceCampaignBuildError(
            "Clinic record terminal auxiliary initializers moved"
        )
    terminal_aux_init_pcs = (
        terminal_aux_init_pc,
        terminal_aux_init_pc + len(terminal_inits[1]),
    )
    terminal_payload_end_pc = terminal_aux_init_pcs[1] + len(terminal_inits[2])
    if (
        terminal_aux_init_pcs != CLINIC_RECORD_TERMINAL_AUX_INIT_PCS
        or terminal_payload_end_pc != CLINIC_RECORD_TERMINAL_PAYLOAD_END_PC
    ):
        raise SurfaceCampaignBuildError(
            "Clinic record terminal carrier layout moved"
        )
    terminal_payload = (
        terminal_inits[0]
        + terminal_action
        + terminal_inits[1]
        + terminal_inits[2]
    )
    if (
        _sha256(cavity) != CLINIC_RECORD_TERMINAL_CAVITY_SHA256
        or len(terminal_payload) > len(cavity)
    ):
        raise SurfaceCampaignBuildError("Clinic retired terminal cavity changed")
    terminal_payload += b"\x00" * (len(cavity) - len(terminal_payload))
    editor = ScriptEditor(
        base._patch_bytecode(
            editor.to_bytes(),
            CLINIC_RECORD_TERMINAL_INIT_PC,
            cavity,
            terminal_payload,
        )
    )
    terminal_init_pcs = (
        CLINIC_RECORD_TERMINAL_INIT_PC,
        *CLINIC_RECORD_TERMINAL_AUX_INIT_PCS,
    )
    for entity, init_pc in zip(
        CLINIC_RECORD_TERMINAL_ENTITIES,
        terminal_init_pcs,
        strict=True,
    ):
        editor.set_script_pointer(entity, 0, init_pc)
        editor.set_script_pointer(
            entity,
            2,
            CLINIC_RECORD_TERMINAL_ACTION_PC,
        )
        if any(
            editor.get_script_pointer(entity, slot) != CLINIC_SHARED_STOP_PC
            for slot in range(32)
            if slot not in (0, 2)
        ):
            raise SurfaceCampaignBuildError(
                f"Clinic terminal carrier {entity} retained a retail script"
            )

    doctor_init_pc = editor.bytecode_size
    editor.append_and_repoint(
        CLINIC_DOCTOR_ENTITY,
        0,
        _clinic_doctor_init(routine_pc=doctor_init_pc),
    )
    doctor_action_pc = editor.bytecode_size
    editor.append_and_repoint(
        CLINIC_DOCTOR_ENTITY,
        2,
        _clinic_doctor_action(
            first_refusal_dialogue_id=first_refusal_dialogue_id,
            security_call_dialogue_id=security_call_dialogue_id,
            routine_pc=doctor_action_pc,
        ),
    )
    doctor_update_pc = editor.bytecode_size
    editor.append_and_repoint(
        CLINIC_DOCTOR_ENTITY,
        1,
        _clinic_doctor_update(
            briefing_dialogue_id=briefing_dialogue_id,
            security_arrival_dialogue_id=security_arrival_dialogue_id,
            keycard_dialogue_id=keycard_dialogue_id,
            escape_dialogue_id=escape_dialogue_id,
            routine_pc=doctor_update_pc,
        ),
    )

    _validate_clinic_doctor_escape_route(components[1])
    _validate_clinic_security_routes(components[1])
    triangles = base._walkmesh_layer(components[1], 0)
    if (
        CLINIC_ENTRY_TRIANGLE >= len(triangles)
        or not base._point_inside_triangle((0, 200), triangles[CLINIC_ENTRY_TRIANGLE])
        or 8 >= len(triangles)
        or not base._point_inside_triangle(CLINIC_DOCTOR_POSITION, triangles[8])
    ):
        raise SurfaceCampaignBuildError("Clinic entry or physician left its walkmesh")

    encounters = EncounterTable(components[6])
    if (
        encounters.weights != (1, 1, 1, 1, 1, 1) + (0,) * 10
        or encounters.formation(CLINIC_SECURITY_CONFIGURATION)
        != CLINIC_RETAIL_SLOT15_FORMATION
    ):
        raise SurfaceCampaignBuildError("Clinic retail encounter weights changed")
    retail_formations = components[6][:-16]
    for formation in range(len(encounters.weights)):
        encounters.set_weight(formation, 0)
    disabled_encounters = encounters.to_bytes()
    if (
        disabled_encounters[:-16] != retail_formations
        or _sha256(disabled_encounters) != CLINIC_DISABLED_ENCOUNTER_SHA256
    ):
        raise SurfaceCampaignBuildError(
            "Clinic encounter disable changed a retail formation"
        )
    security_formation = bytearray(security_source_formation)
    security_formation[1] |= 0x80
    security_formation[2] = CLINIC_SECURITY_ARENA
    if bytes(security_formation) != CLINIC_SECURITY_FORMATION:
        raise SurfaceCampaignBuildError(
            "Solaris security formation flags are not deterministic"
        )
    installed_encounters = bytearray(disabled_encounters)
    formation_start = CLINIC_SECURITY_CONFIGURATION * 0x20
    installed_encounters[
        formation_start : formation_start + 0x20
    ] = security_formation
    installed_encounters = bytes(installed_encounters)
    installed_table = EncounterTable(installed_encounters)
    if (
        installed_table.formation(CLINIC_SECURITY_CONFIGURATION)
        != CLINIC_SECURITY_FORMATION
        or installed_table.get_weight(CLINIC_SECURITY_CONFIGURATION) != 0
        or any(installed_table.weights)
        or _sha256(installed_encounters) != CLINIC_SECURITY_ENCOUNTER_SHA256
    ):
        raise SurfaceCampaignBuildError(
            "Clinic scripted security formation failed installation"
        )

    components[SCRIPT_INDEX] = editor.to_bytes()
    components[6] = installed_encounters
    components[7] = dialogue
    bundle = build_field_preserving(
        source_bundle,
        components,
        (
            base.mass_driver.ACTOR_INDEX,
            base.mass_driver.SPRITE_INDEX,
            SCRIPT_INDEX,
            6,
            7,
        ),
        compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise SurfaceCampaignBuildError("Clinic transplant failed round trip")
    return base.PreparedDonorField(
        CLINIC_TARGET_IDENTITY,
        (
            "Disc 1 field-352 Ethos infirmary transplanted as a quiet examination "
            "office; retired actor e4 carries a repeatable alias-aware live patient "
            "record and perfect biological-compatibility readout; native exit leaf "
            "preserved; bloodwork refusal, authentic Solaris security battle, and "
            "physician escape"
        ),
        source_bundle,
        graphics,
        reparsed.header,
        tuple(components),
        bundle,
        ((CLINIC_ENTRY_PARAMETER, CLINIC_ENTRY_TRIANGLE),),
    )


def _prepare_clinic_exit_sequence(
    prepared: base.PreparedDonorField,
) -> base.PreparedDonorField:
    """Interpose the bloodwork gate after the donor seal wrapper exists."""

    if prepared.identity.scene != 550:
        raise SurfaceCampaignBuildError("Clinic exit gate applied to wrong field")
    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    if (
        editor.entity_count != CLINIC_EXIT_SEAL_ENTITY + 1
        or DONOR_DOOR_COLLISION_CONTRACTS[550][0].controller_entity
        != CLINIC_EXIT_ENTITY
    ):
        raise SurfaceCampaignBuildError("Clinic exit seal entity changed")
    native_action_pc = editor.get_script_pointer(CLINIC_EXIT_ENTITY, 2)
    expected_native_action = _clinic_native_field_change_action(
        destination_field=CLINIC_RETURN_FIELD,
        destination_parameter=CLINIC_RETURN_PARAMETER,
        seal_entity=CLINIC_EXIT_SEAL_ENTITY,
    )
    release_pc = editor.get_script_pointer(CLINIC_EXIT_SEAL_ENTITY, 4)
    if (
        editor.bytecode[
            native_action_pc : native_action_pc + len(expected_native_action)
        ]
        != expected_native_action
        or editor.bytecode[
            release_pc : release_pc + len(DONOR_SEAL_RELEASE_ACTION)
        ]
        != DONOR_SEAL_RELEASE_ACTION
    ):
        raise SurfaceCampaignBuildError(
            "Clinic post-clearance native exit foundation changed"
        )

    security_records = tuple(
        Console(
            CLINIC_SECURITY_STAGING_POSITION[0],
            CLINIC_SECURITY_STAGING_POSITION[1],
            34,
            0,
            "",
        )
        for _entity in CLINIC_SECURITY_ENTITIES
    )
    header = _insert_controller_records(
        prepared.header,
        old_entity_count=editor.entity_count,
        consoles=security_records,
    )
    editor = ScriptEditor(
        base.mass_driver._extend_atel_entity_table(
            editor.to_bytes(), editor.entity_count + len(CLINIC_SECURITY_ENTITIES)
        )
    )
    if tuple(range(CLINIC_EXIT_SEAL_ENTITY + 1, editor.entity_count)) != (
        CLINIC_SECURITY_ENTITIES
    ):
        raise SurfaceCampaignBuildError(
            "Clinic security actors left the post-seal entity boundary"
        )
    for entity in CLINIC_SECURITY_ENTITIES:
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, CLINIC_SHARED_STOP_PC)

    close_pc = editor.bytecode_size
    editor.append_and_repoint(
        CLINIC_EXIT_HELPER_ENTITY,
        CLINIC_EXIT_HELPER_CLOSE_SCRIPT,
        _clinic_exit_close_helper(routine_pc=close_pc),
    )
    for entity in CLINIC_SECURITY_ENTITIES:
        init_pc = editor.bytecode_size
        editor.append_and_repoint(
            entity,
            0,
            _clinic_security_actor_init(entity=entity, routine_pc=init_pc),
        )
        editor.append_and_repoint(
            entity,
            CLINIC_SECURITY_ENTRY_SCRIPT,
            _clinic_security_actor_entrance_body(entity=entity),
        )
        editor.append_and_repoint(
            entity,
            CLINIC_SECURITY_HIDE_SCRIPT,
            _clinic_security_actor_hide_body(),
        )

    already_open_action_pc = editor.append_raw_routine(
        _clinic_post_escape_field_change_action(
            seal_entity=CLINIC_EXIT_SEAL_ENTITY
        )
    )
    gate_pc = editor.bytecode_size
    editor.append_and_repoint(
        CLINIC_EXIT_ENTITY,
        2,
        _clinic_exit_gate_action(
            native_action_pc=native_action_pc,
            already_open_action_pc=already_open_action_pc,
            insistence_dialogue_id=CLINIC_EXIT_INSISTENCE_DIALOGUE_ID,
            escape_in_progress_dialogue_id=(
                CLINIC_ESCAPE_IN_PROGRESS_DIALOGUE_ID
            ),
            routine_pc=gate_pc,
        ),
    )
    return _rebuild_donor(
        prepared,
        editor=editor,
        header=header,
        role_suffix=(
            "exit denied until bloodwork refusal and security victory; "
            "exact Imperial escorts and Security Cubes enter through the leaf; "
            "physician crosses and closes it without blocking Fei"
        ),
    )


def _prepare_recovered_stabilization(
    prepared: base.PreparedDonorField,
) -> base.PreparedDonorField:
    """Turn the ward's retired procedure response into the production gate."""

    if prepared.identity.scene != stabilization590.SCENE:
        raise SurfaceCampaignBuildError(
            "Recovered stabilization transform requires logical field 590"
        )
    parsed = parse_dialogue(prepared.components[7])
    dialogue_id = stabilization590.PRODUCTION_DENIAL_DIALOGUE_ID
    if (
        dialogue_id >= len(parsed.blocks)
        or parsed.blocks[dialogue_id].text != donor567.SEALED_DIALOGUE_TEXT
    ):
        raise SurfaceCampaignBuildError(
            "Recovered stabilization production dialogue foundation changed"
        )
    dialogue = _replace_dialogue_texts(
        prepared.components[7],
        {dialogue_id: stabilization590.PRODUCTION_DENIAL_DIALOGUE},
    )
    return _rebuild_donor(
        prepared,
        editor=ScriptEditor(prepared.components[SCRIPT_INDEX]),
        dialogue=dialogue,
        role_suffix=(
            "recovered clinical bridge; retired procedure threshold reassigned "
            "to the four-clearance molecular-sorting bulkhead"
        ),
    )


def _prepare_service_manifold(
    prepared: base.PreparedDonorField,
) -> base.PreparedDonorField:
    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    # Restore the last authentic spoke.  The native e9 body remains at 0x0334,
    # but v173 deliberately parked s2 on the sealed response while field 588
    # was absent.  Build its checked wrapper first; e9 now enters the bright
    # scanner annex and that room returns through field-565 parameter 5.
    # The former e7 lab handoff is frozen below as provenance, then replaced
    # after collision separation by a non-opening authorization response.  It
    # remains physically sealed until that deeper section is deliberately
    # authored in a future release.
    e9_pc = editor.bytecode_size
    e9_action = base._field565_native_door_action(
        helper_entity=14,
        player_script=9,
        destination_field=588,
        destination_parameter=0,
        routine_pc=e9_pc,
    )
    editor.append_and_repoint(9, 2, e9_action)

    # Widen all seven exterior action shells without creating held-Cross
    # bounce.  Every replacement stays on the same uniquely audited triangle
    # while moving farther into the room than the 64-world-unit X envelope.
    if prepared.entry_triangles != (
        (0, 75),
        (1, 8),
        (2, 12),
        (3, 17),
        (4, 57),
        (6, 68),
    ):
        raise SurfaceCampaignBuildError("Field 565 entry-triangle foundation changed")
    script = editor.to_bytes()
    triangles = base._walkmesh_layer(prepared.components[1], 0)
    for parameter, (source, destination, triangle) in FIELD565_CLEAR_ARRIVALS.items():
        script = base._patch_bytecode(
            script,
            1 + 7 * parameter,
            struct.pack("<hhBBB", *source),
            struct.pack("<hhBBB", *destination),
        )
        hits = tuple(
            index
            for index, candidate in enumerate(triangles)
            if base._point_inside_triangle(destination[:2], candidate)
        )
        if hits != (triangle,):
            raise SurfaceCampaignBuildError(
                f"Field 565 parameter {parameter} left audited triangle "
                f"{triangle}: {hits}"
            )
    editor = ScriptEditor(script)

    dialogue, (
        production_denial_id,
        quarantine_denial_id,
        internal_keycard_denial_id,
        network_briefing_id,
        future_lab_handoff_id,
    ) = _append_dialogue(
        prepared.components[7],
        (
            "PRODUCTION BULKHEAD LOCKED\n"
            "Required: keycard, quarantine consensus,\n"
            "resonance authorization, and bio-interface cutoff.<Close>",
            "QUARANTINE AIRLOCK SEALED\n"
            "A quarantine keycard is required for entry.<Close>",
            SERVICE_INTERNAL_KEYCARD_DENIAL_DIALOGUE,
            SERVICE_NETWORK_BRIEFING_DIALOGUE,
            SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE,
        ),
    )
    if (
        production_denial_id,
        quarantine_denial_id,
        internal_keycard_denial_id,
        network_briefing_id,
        future_lab_handoff_id,
    ) != (
        SERVICE_PRODUCTION_DENIAL_DIALOGUE_ID,
        SERVICE_QUARANTINE_DENIAL_DIALOGUE_ID,
        SERVICE_INTERNAL_KEYCARD_DENIAL_DIALOGUE_ID,
        SERVICE_NETWORK_BRIEFING_DIALOGUE_ID,
        SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE_ID,
    ):
        raise SurfaceCampaignBuildError("Field 565 service dialogue IDs changed")
    old_quarantine = editor.get_script_pointer(10, 2)
    quarantine_gate_pc = editor.bytecode_size
    editor.append_and_repoint(
        10,
        2,
        _gate_existing_action(
            requirements=((QUARANTINE_KEYCARD_OPERAND, QUARANTINE_KEYCARD_MASK),),
            old_action_pc=old_quarantine,
            denial_dialogue_id=quarantine_denial_id,
            routine_pc=quarantine_gate_pc,
        ),
    )
    old_production = editor.get_script_pointer(5, 2)
    gate_pc = editor.bytecode_size
    editor.append_and_repoint(
        5,
        2,
        _gate_existing_action(
            requirements=(
                (SECURITY_KEYCARD_OPERAND, SECURITY_KEYCARD_MASK),
                (TONE_OPERAND, TONE_MASK),
                (STATE_OPERAND, QUARANTINE_MASK),
                (STATE_OPERAND, INTERFACE_BIT_MASK),
            ),
            old_action_pc=old_production,
            denial_dialogue_id=production_denial_id,
            routine_pc=gate_pc,
        ),
    )
    entries = tuple(
        (parameter, values[2])
        for parameter, values in sorted(FIELD565_CLEAR_ARRIVALS.items())
    )
    return _rebuild_donor(
        prepared,
        editor=editor,
        dialogue=dialogue,
        role_suffix=(
            "six active wide-target circulation thresholds plus one sealed "
            "future deep-service handoff, all with bounce-safe entries; "
            "Quarantine-keycard-controlled diagnostics entry, "
            "relay-controlled Quarantine exit, native five-tone internal "
            "service passage, and checked legacy "
            "production-interlock foundation"
        ),
        entry_triangles=entries,
    )


def _prepare_archive_checkin(
    prepared: base.PreparedDonorField,
) -> base.PreparedDonorField:
    """Install the alias check-in and repeatable vitals on field 549 e4."""

    if prepared.identity.scene != 549:
        raise SurfaceCampaignBuildError("Archive check-in requires field 549")
    dialogue, (alias_menu_id,) = _append_dialogue(
        prepared.components[7],
        (CHECKIN_ALIAS_MENU_DIALOGUE,),
        width=58,
        height=5,
    )
    dialogue, alias_result_ids = _append_dialogue(
        dialogue,
        CHECKIN_ALIAS_RESULT_DIALOGUES,
        width=58,
        height=5,
    )
    dialogue, (cancelled_id,) = _append_dialogue(
        dialogue,
        (CHECKIN_CANCELLED_DIALOGUE,),
        width=58,
        height=2,
    )
    dialogue, (repeat_menu_id,) = _append_dialogue(
        dialogue,
        (CHECKIN_REPEAT_MENU_DIALOGUE,),
        width=58,
        height=5,
    )
    dialogue, patient_ids = _append_dialogue(
        dialogue,
        tuple(
            PATIENT_VITALS_DIALOGUES[patient]
            for patient in ("Fei", "Elly", "Citan")
        ),
        width=58,
        height=4,
    )
    expected_ids = tuple(range(12, 21))
    actual_ids = (
        alias_menu_id,
        *alias_result_ids,
        cancelled_id,
        repeat_menu_id,
        *patient_ids,
    )
    if actual_ids != expected_ids:
        raise SurfaceCampaignBuildError(
            f"Field 549 check-in dialogue IDs changed: {actual_ids}"
        )

    parsed = parse_dialogue(dialogue)
    expected_texts = (
        CHECKIN_ALIAS_MENU_DIALOGUE,
        *CHECKIN_ALIAS_RESULT_DIALOGUES,
        CHECKIN_CANCELLED_DIALOGUE,
        CHECKIN_REPEAT_MENU_DIALOGUE,
        *(PATIENT_VITALS_DIALOGUES[name] for name in ("Fei", "Elly", "Citan")),
    )
    if tuple(parsed.blocks[index].text for index in expected_ids) != expected_texts:
        raise SurfaceCampaignBuildError("Field 549 check-in dialogue changed on encode")

    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    native_terminal_action = editor.bytecode[
        ARCHIVE_TERMINAL_RETAIL_ACTION_PC : ARCHIVE_TERMINAL_NATIVE_STOP_PC + 1
    ]
    if (
        editor.get_script_pointer(ARCHIVE_TERMINAL_ENTITY, 2)
        != ARCHIVE_TERMINAL_RETAIL_ACTION_PC
        or _sha256(native_terminal_action)
        != ARCHIVE_TERMINAL_NATIVE_ACTION_SHA256
        or editor.bytecode[
            ARCHIVE_TERMINAL_RETAIL_ACTION_PC : ARCHIVE_TERMINAL_NATIVE_MENU_PC
        ]
        != ARCHIVE_TERMINAL_NATIVE_SCREEN_OPEN_BODY
        or editor.bytecode[
            ARCHIVE_TERMINAL_NATIVE_CLOSE_PC : ARCHIVE_TERMINAL_NATIVE_STOP_PC - 3
        ]
        != ARCHIVE_TERMINAL_NATIVE_SCREEN_CLOSE_LAUNCH_BODY
        or editor.bytecode[
            ARCHIVE_TERMINAL_NATIVE_STOP_PC - 3 : ARCHIVE_TERMINAL_NATIVE_STOP_PC
        ]
        != _jump(ARCHIVE_TERMINAL_NATIVE_STOP_PC)
        or editor.bytecode[ARCHIVE_TERMINAL_NATIVE_STOP_PC] != 0
        or editor.bytecode[
            ARCHIVE_TERMINAL_NATIVE_MENU_PC : ARCHIVE_TERMINAL_NATIVE_MENU_PC + 4
        ]
        != base.mass_driver._choice_dialog(
            ARCHIVE_TERMINAL_NATIVE_MENU_DIALOGUE_ID
        )
        or tuple(
            editor.get_script_pointer(
                entity, ARCHIVE_TERMINAL_SCREEN_OPEN_SCRIPT
            )
            for entity in ARCHIVE_TERMINAL_SCREEN_ENTITIES
        )
        != ARCHIVE_TERMINAL_SCREEN_OPEN_PCS
        or tuple(
            editor.get_script_pointer(
                entity, ARCHIVE_TERMINAL_SCREEN_CLOSE_SCRIPT
            )
            for entity in ARCHIVE_TERMINAL_SCREEN_ENTITIES
        )
        != ARCHIVE_TERMINAL_SCREEN_CLOSE_PCS
    ):
        raise SurfaceCampaignBuildError("Field 549 retail archive terminal changed")
    action_pc = editor.bytecode_size
    if action_pc != ARCHIVE_CHECKIN_ACTION_PC:
        raise SurfaceCampaignBuildError("Field 549 check-in append point moved")
    action = _archive_checkin_action(
        alias_menu_dialogue_id=alias_menu_id,
        alias_result_dialogue_ids=alias_result_ids,
        cancelled_dialogue_id=cancelled_id,
        repeat_menu_dialogue_id=repeat_menu_id,
        patient_dialogue_ids=patient_ids,
        routine_pc=action_pc,
    )
    if len(action) != 469 or _sha256(action) != ARCHIVE_CHECKIN_ACTION_SHA256:
        raise SurfaceCampaignBuildError("Field 549 check-in terminal action changed")
    if editor.append_and_repoint(ARCHIVE_TERMINAL_ENTITY, 2, action) != action_pc:
        raise SurfaceCampaignBuildError("Field 549 check-in terminal action moved")
    rebuilt = _rebuild_donor(
        prepared,
        editor=editor,
        dialogue=dialogue,
        role_suffix=(
            "one-time intake alias registration, repeatable Fei/Elly/Citan "
            "vitals, and retained six-panel terminal opening/closing screens; "
            "retail binary archive codes retired"
        ),
    )
    return replace(
        rebuilt,
        role=(
            "classification intake terminal; one-time alias registration, "
            "repeatable Fei/Elly/Citan vitals, retained six-panel terminal "
            "opening/closing screens, and unreachable retail binary codes"
        ),
    )


def _prepare_interface_annex(
    prepared: base.PreparedDonorField,
) -> base.PreparedDonorField:
    triangles = base._walkmesh_layer(prepared.components[1], 0)
    if not base._point_inside_triangle(
        (INTERFACE_CONSOLE.x, INTERFACE_CONSOLE.z),
        triangles[INTERFACE_CONSOLE.triangle],
    ):
        raise SurfaceCampaignBuildError(
            "Field 588 interface scanner left its audited walkmesh"
        )
    dialogue, dialogue_ids = _append_dialogue(
        prepared.components[7],
        (
            INTERFACE_CONSOLE.text,
            QUARANTINE_KEYCARD_DIALOGUE,
        ),
    )
    # Retain the old receipt block as unreachable dialogue inventory so the
    # donor layout and every later checked ID stay frozen.  Only the first
    # block is referenced by the active interface-only action.
    dialogue_id, _legacy_keycard_dialogue_id = dialogue_ids
    if dialogue_ids != (
        INTERFACE_DIAGNOSTIC_DIALOGUE_ID,
        QUARANTINE_KEYCARD_DIALOGUE_ID,
    ):
        raise SurfaceCampaignBuildError(
            "Field 588 interface/keycard dialogue IDs changed"
        )
    retired_keycard_write = _set_bit(
        QUARANTINE_KEYCARD_OPERAND,
        QUARANTINE_KEYCARD_BIT_INDEX,
    )
    script = base._patch_bytecode(
        prepared.components[SCRIPT_INDEX],
        INTERFACE_RETIRED_KEYCARD_WRITE_PC,
        retired_keycard_write,
        b"\x00" * len(retired_keycard_write),
    )
    editor = ScriptEditor(script)
    entity = donor588.CONSOLE_ENTITY
    if entity >= editor.entity_count:
        raise SurfaceCampaignBuildError(
            "Field 588 interface-workstation carrier is absent"
        )
    editor.append_and_repoint(entity, 0, _console_init(INTERFACE_CONSOLE))
    action_pc = editor.bytecode_size
    editor.append_and_repoint(
        entity,
        2,
        _interface_cutoff_action(
            interface_dialogue_id=dialogue_id,
            routine_pc=action_pc,
        ),
    )
    return _rebuild_donor(
        prepared,
        editor=editor,
        dialogue=dialogue,
        role_suffix=(
            "bright native diagnostic scanner with a save-safe bio-interface "
            "cutoff; no credential award"
        ),
    )


def _prepare_resonance_annex(
    prepared: base.PreparedDonorField,
) -> base.PreparedDonorField:
    """Keep field 589 as the authentic clue for field 565's input puzzle."""

    if prepared.identity.scene != 589:
        raise SurfaceCampaignBuildError("Resonance annex requires field 589")
    dialogue, (dialogue_id,) = _append_dialogue(
        prepared.components[7],
        (RESONANCE_CLUE_RECEIPT_DIALOGUE,),
    )
    if dialogue_id != RESONANCE_CLUE_RECEIPT_DIALOGUE_ID:
        raise SurfaceCampaignBuildError("Field 589 clue receipt dialogue moved")

    editor = ScriptEditor(prepared.components[SCRIPT_INDEX])
    if (
        editor.get_script_pointer(RESONANCE_CLUE_ENTITY, 2)
        != RESONANCE_CLUE_ACTION_PC
        or editor.bytecode[
            RESONANCE_CLUE_TAIL_PC :
            RESONANCE_CLUE_TAIL_PC + len(RESONANCE_CLUE_TAIL)
        ]
        != RESONANCE_CLUE_TAIL
        or editor.bytecode_size != RESONANCE_CLUE_RECEIPT_ACTION_PC
    ):
        raise SurfaceCampaignBuildError("Field 589 five-tone clue foundation changed")

    routine = base.mass_driver._RoutineBuilder(
        RESONANCE_CLUE_RECEIPT_ACTION_PC
    )
    routine.emit(base.mass_driver._wait())
    routine.emit(PROGRESSION_CONFIRM_SOUND)
    routine.emit(b"\xF5" + _u16(dialogue_id) + b"\x01\x9C")
    routine.emit(RESONANCE_CLUE_TAIL)
    if (
        editor.append_raw_routine(routine.finish())
        != RESONANCE_CLUE_RECEIPT_ACTION_PC
    ):
        raise SurfaceCampaignBuildError("Field 589 clue receipt action moved")

    script = base._patch_bytecode(
        editor.to_bytes(),
        RESONANCE_CLUE_TAIL_PC,
        RESONANCE_CLUE_TAIL,
        _jump(RESONANCE_CLUE_RECEIPT_ACTION_PC)
        + b"\x00" * (len(RESONANCE_CLUE_TAIL) - 3),
    )
    return _rebuild_donor(
        prepared,
        editor=ScriptEditor(script),
        dialogue=dialogue,
        role_suffix=(
            "authentic five-tone clue and input-panel reminder; authorization "
            "is awarded only by the native field-565 password console"
        ),
    )


def prepare_campaign(
    source_disc: Path | str,
    donor_disc: Path | str,
    *,
    include_title: bool = True,
    clinic_resource_overrides: Mapping[int, bytes] | None = None,
) -> tuple[
    tuple[base.PreparedField, ...],
    tuple[base.PreparedDonorField, ...],
    tuple[base.PreparedTitleResource, ...],
]:
    """Prepare all rooms and, by default, the campaign title bootstrap.

    ``include_title=False`` is the content-only composition path used by the
    unified Disc 2 builder.  It lets that builder source the untouched Surface
    fields directly from Perfect Works while owning the one shared title/menu
    handoff itself.  ``clinic_resource_overrides`` validates normalized battle
    resources supplied by another module in that final composition.
    Standalone callers retain the historical defaults.
    """

    blueprint.validate_blueprint()
    _validate_campaign_dialogue_contracts()
    _validate_clinic_security_resources(
        source_disc,
        resource_overrides=clinic_resource_overrides,
    )
    _load_campaign_music_assets(source_disc)
    _validate_no_deathblow_level_requirements(source_disc)
    prepared_fields, prepared_donors = base.prepare_complete_route(
        source_disc, donor_disc
    )
    if sum(item.identity.scene == 550 for item in prepared_donors) != 1:
        raise SurfaceCampaignBuildError("Logical field 550 donor slot changed")
    clinic_office = _prepare_clinic_office(donor_disc)
    empty_medical_room = exam_rooms.prepare_empty_room_terminal(
        empty_clinic567.prepare_empty_clinic567_from_discs(
            source_disc,
            donor_disc,
        )
    )
    intake_exam_rooms = exam_rooms.prepare_exam_rooms_from_discs(
        source_disc,
        donor_disc,
    )
    recovered_stabilization = _prepare_donor_door_clearance(
        _prepare_recovered_stabilization(
            stabilization590.prepare_stabilization590_from_discs(
                source_disc,
                donor_disc,
            )
        )
    )
    donor588.verify_donor588_targets_are_dummy(source_disc)
    annex588 = _prepare_donor_door_clearance(
        _prepare_interface_annex(
            donor588.prepare_donor588_from_discs(source_disc, donor_disc)
        )
    )

    fields: list[base.PreparedField] = []
    for prepared in prepared_fields:
        scene = prepared.spec.identity.scene
        transform = {
            623: _prepare_transfer_shortcut,
            621: lambda item: _prepare_intake_lore(
                item, clinic_office=clinic_office
            ),
            620: _prepare_quarantine_lore,
            624: _prepare_sorting,
            626: _prepare_core,
            625: _prepare_meld,
            622: _prepare_generation,
        }.get(scene)
        transformed = prepared if transform is None else transform(prepared)
        cleared = _prepare_door_clearance(transformed)
        if scene == 620:
            cleared = _prepare_quarantine_completion(cleared)
        if scene == 621:
            cleared = _install_intake_exam_room_doors(cleared)
        fields.append(cleared)

    donors: list[base.PreparedDonorField] = []
    for prepared in prepared_donors:
        prepared = clinic_office if prepared.identity.scene == 550 else prepared
        transform = {
            549: _prepare_archive_checkin,
            565: _prepare_service_manifold,
            589: _prepare_resonance_annex,
        }.get(prepared.identity.scene)
        transformed = prepared if transform is None else transform(prepared)
        cleared = _prepare_donor_door_clearance(transformed)
        if cleared.identity.scene == 550:
            cleared = _prepare_clinic_exit_sequence(cleared)
        donors.append(cleared)
        if cleared.identity.scene == 565:
            donors.append(
                _prepare_donor_door_clearance(empty_medical_room)
            )
    donors.append(annex588)
    donors.append(recovered_stabilization)
    donors.extend(
        _prepare_donor_door_clearance(room)
        for room in intake_exam_rooms
    )

    # Reflow the complete 74-block authored inventory.  The later appointment
    # blocks are already authored within their explicit window grids.  Retained
    # retail dialogue, including
    # its timing and opaque controls, remains byte-identical.  Run music after
    # this content-only pass so no later bundle rebuild can invalidate either
    # the dialogue component or the final identity freeze.
    fields = [_prepare_campaign_dialogue_layout_field(item) for item in fields]
    donors = [_prepare_campaign_dialogue_layout_donor(item) for item in donors]

    from modules.soylent_system.tools import surface_soylent_completion as completion
    from modules.soylent_system.tools import surface_soylent_story_finish as story_finish
    from modules.soylent_system.tools import surface_soylent_checkpoint as checkpoint
    from modules.soylent_system.tools import surface_soylent_keycard_room as keycard_room
    from modules.soylent_system.tools import surface_soylent_quarantine_feedback as quarantine_feedback
    from modules.soylent_system.tools import surface_soylent_clinical_discoveries as clinical_discoveries
    from modules.soylent_system.tools import surface_soylent_clearance_report as clearance_report
    from modules.soylent_system.tools import surface_soylent_finale_closure as finale_closure
    from modules.soylent_system.tools import surface_soylent_final_guidance as final_guidance
    from modules.soylent_system.tools import surface_soylent_quarantine_committed_visuals as committed_visuals
    from modules.soylent_system.tools import surface_soylent_production_shutdown_visuals as production_visuals

    # Complete the reviewed foundation and retire only the two keycard-room
    # NPCs. Physical doors and retail assets remain unchanged. New dialogue is
    # checked against the same font grid before the output is frozen.
    previous_dialogue = {
        item.spec.identity.scene: parse_dialogue(item.components[7]).blocks
        for item in fields
    } | {
        item.identity.scene: parse_dialogue(item.components[7]).blocks
        for item in donors
    }
    fields = [story_finish.prepare_story_finish(completion.prepare_production_puzzle(item))
              for item in fields]
    donors = [checkpoint.prepare_checkpoint(item) if item.identity.scene == 590 else item
              for item in donors]
    donors = [keycard_room.prepare_keycard_room(item) for item in donors]
    fields = [quarantine_feedback.prepare_quarantine_feedback(item) for item in fields]
    donors = [clinical_discoveries.prepare_clinical_discoveries(item) for item in donors]
    donors = [clearance_report.prepare_clearance_report(item) if item.identity.scene == 590 else item
              for item in donors]
    fields = [finale_closure.prepare_finale_closure(item) for item in fields]
    fields = [committed_visuals.prepare_committed_visuals(item) for item in fields]
    fields = [production_visuals.prepare_shutdown_visuals(item) for item in fields]
    donors = [final_guidance.prepare_final_guidance(item) for item in donors]
    for scene, item in (
        [(item.spec.identity.scene, item) for item in fields]
        + [(item.identity.scene, item) for item in donors]
    ):
        old_blocks = previous_dialogue[scene]
        for block in parse_dialogue(item.components[7]).blocks:
            if block.block_id < len(old_blocks) and block.payload == old_blocks[block.block_id].payload:
                continue
            measurable = parse_dialogue(encode_dialogue((DialogueBlockSpec(
                0, block.width, block.height, block.text.replace("<Opcode:01:FF>", ""),
            ),))).blocks[0]
            issues = _campaign_dialogue_layout_issues(measurable)
            if issues:
                raise SurfaceCampaignBuildError(
                    f"Field {scene} completion dialogue {block.block_id} exceeds grid: {issues}"
                )

    # Run the music pass last.  Its frozen inputs therefore include every
    # content, door-animation, collision, and dialogue-layout transform above,
    # while its own compact rebuild cannot be invalidated by a later ATEL edit.
    fields = [_prepare_campaign_music_field(item) for item in fields]
    donors = [_prepare_campaign_music_donor(item) for item in donors]

    title_resources = (
        campaign_title.transform_title_resources(
            base.prepare_title_integration(
                source_disc,
                complete_dungeon=True,
                include_initial_gamestate=True,
            )
        )
        if include_title
        else ()
    )
    _validate_prepared_graph(tuple(fields), tuple(donors))
    _assert_final_identities(tuple(fields), tuple(donors))
    return tuple(fields), tuple(donors), title_resources


def _assert_final_identities(
    fields: Sequence[base.PreparedField],
    donors: Sequence[base.PreparedDonorField],
) -> None:
    prepared = {
        item.spec.identity.scene: item for item in fields
    } | {item.identity.scene: item for item in donors}
    if set(prepared) != set(CAMPAIGN_FINAL_IDENTITIES):
        raise SurfaceCampaignBuildError("Campaign identity table has the wrong room set")
    for scene, item in prepared.items():
        actual = (
            len(item.components[SCRIPT_INDEX]),
            _sha256(item.components[SCRIPT_INDEX]),
            len(item.components[7]),
            _sha256(item.components[7]),
            len(item.bundle),
            _sha256(item.bundle),
        )
        if actual != CAMPAIGN_FINAL_IDENTITIES[scene]:
            raise SurfaceCampaignBuildError(
                f"Field {scene} campaign output identity changed: {actual}"
            )


def _validate_prepared_graph(
    fields: Sequence[base.PreparedField],
    donors: Sequence[base.PreparedDonorField],
) -> None:
    scenes = {item.spec.identity.scene for item in fields} | {
        item.identity.scene for item in donors
    }
    expected = {room.field for room in blueprint.ROOMS}
    if scenes != expected:
        raise SurfaceCampaignBuildError(
            f"Prepared room set {sorted(scenes)} != blueprint {sorted(expected)}"
        )
    entries = {
        (item.spec.identity.scene, edit.parameter)
        for item in fields
        for edit in item.spec.entry_edits
    }
    entries.update(
        (item.identity.scene, parameter)
        for item in donors
        for parameter, _triangle in item.entry_triangles
    )
    missing = [
        endpoint.id
        for endpoint in blueprint.ENDPOINTS
        if (endpoint.destination_field, endpoint.destination_entry_parameter)
        not in entries
    ]
    if missing:
        raise SurfaceCampaignBuildError(
            "Campaign door destinations lack audited entries: " + ", ".join(missing)
        )


def _write_campaign_manifest(
    output_root: Path,
    *,
    source_disc: Path | str,
    donor_disc: Path | str,
    fields: Sequence[base.PreparedField],
    donors: Sequence[base.PreparedDonorField],
    title_resources: Sequence[base.PreparedTitleResource],
    replacements: Sequence[tuple[int, Path]],
    playtest: Mapping[str, object] | None = None,
) -> None:
    manifest_path = output_root / "manifest.json"
    base_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    from modules.soylent_system.tools import surface_soylent_completion as completion
    from modules.soylent_system.tools import surface_soylent_story_finish as story_finish
    from modules.soylent_system.tools import surface_soylent_checkpoint as checkpoint
    from modules.soylent_system.tools import surface_soylent_quarantine_feedback as quarantine_feedback
    from modules.soylent_system.tools import surface_soylent_clinical_discoveries as clinical_discoveries
    from modules.soylent_system.tools import surface_soylent_clearance_report as clearance_report

    campaign = blueprint.to_manifest()
    from modules.soylent_system.tools import surface_soylent_finale_closure as finale_closure
    from modules.soylent_system.tools import surface_soylent_final_guidance as final_guidance
    from modules.soylent_system.tools import surface_soylent_quarantine_committed_visuals as committed_visuals
    from modules.soylent_system.tools import surface_soylent_production_shutdown_visuals as production_visuals
    campaign.update(
        {
            "format": OUTPUT_FORMAT,
            "name": "Ignas Surface Soylent System — reconstructed Disc 2 dungeon",
            "source_disc": Path(source_disc).resolve().name,
            "donor_disc": Path(donor_disc).resolve().name,
            "technical_foundation": "v173 reciprocal-door conversion",
            "final_release": {"content_version": "1.1", "revision": 240,
                              "content_status": "final", "runtime_acceptance": "pending"},
            "production_shutdown_visuals": [production_visuals.shutdown_visuals_metadata(item)
                                            for item in fields if item.spec.identity.scene == 624],
            "finale_closure": [finale_closure.closure_metadata(item)
                               for item in fields if item.spec.identity.scene == 622],
            "final_guidance": final_guidance.final_guidance_metadata(),
            "quarantine_committed_visuals": [committed_visuals.committed_visuals_metadata(item)
                                            for item in fields if item.spec.identity.scene == 620],
            "playtest": dict(playtest or {"one_hit_kills": False}),
            "production_puzzles": [completion.puzzle_metadata(item)
                                   for item in fields if item.spec.identity.scene in (624, 626)],
            "checkpoint": {**checkpoint.checkpoint_metadata(),
                           **clearance_report.clearance_report_metadata(),
                           "menu": clearance_report.MENU_TEXT},
            "quarantine_feedback": [quarantine_feedback.feedback_metadata(item)
                                    for item in fields if item.spec.identity.scene == 620],
            "clinical_discoveries": [clinical_discoveries.discovery_metadata(item)
                                     for item in donors if item.identity.scene in (591, 592, 594)],
            "story_completion": [story_finish.story_metadata(item)
                                 for item in fields if item.spec.identity.scene in (625, 622)],
            "music": {
                "track": KRELIAN_LAB_MUSIC_TRACK,
                "music_id": KRELIAN_LAB_MUSIC_ID,
                "opcode": KRELIAN_LAB_MUSIC_OPCODE.hex(" ").upper(),
                "directory": MUSIC_DIRECTORY,
                "wave_local_file": KRELIAN_LAB_WAVE_LOCAL_FILE,
                "sequence_local_file": KRELIAN_LAB_SEQUENCE_LOCAL_FILE,
                "authentic_source_fields": sorted(
                    KRELIAN_LAB_MUSIC_SOURCE_EVIDENCE
                ),
                "excluded_nortune_music_id": NORTUNE_STEALTH_MUSIC_ID,
                "excluded_nortune_source_fields": sorted(
                    NORTUNE_STEALTH_MUSIC_SOURCE_EVIDENCE
                ),
                "provenance": (
                    "retains field 565's native 0x3D lab-corridor cue and "
                    "selects that cue through wrappers in every other room; "
                    "does not use the 0x3C Kislev/Nortune infiltration cue "
                    "also heard at field 555/560 thresholds"
                ),
                "initialized_rooms": sorted(
                    CAMPAIGN_PRE_MUSIC_SCRIPT_IDENTITIES
                ),
                "selector": "entity 0 script 0 in every campaign room",
                "transition_policy": (
                    "same requested ID preserves the loaded sequence; direct "
                    "entry into any room still selects the cue"
                ),
                "assets": [
                    {
                        "local_file": local_file,
                        "size": identity[0],
                        "sha256": identity[1],
                    }
                    for local_file, identity in sorted(
                        KRELIAN_LAB_MUSIC_ASSET_IDENTITIES.items()
                    )
                ],
            },
            "current_content_boundary": None,
            "quarantine_completion": {
                "field": 620,
                "entity": QUARANTINE_CURRENT_END_DOOR_ENTITY,
                "action_pc": QUARANTINE_CURRENT_END_DOOR_ACTION_PC,
                "required_local_value": 0x0070,
                "solution": "Genome, Limiter and Nanomachines on; Caste off",
                "award": "quarantine_complete",
                "award_operand": STATE_OPERAND,
                "award_bit": 8,
                "commit": "after acceptance dialogue closes, before native door animation",
                "destination": [565, 6],
                "preserved_return": {"entity": 23, "destination": [621, 2]},
                "repeat": "persistent clearance permits native door without another award",
            },
            "unassigned_medical_examination_room": {
                "field": empty_clinic567.SCENE,
                "name": "Unassigned Medical Examination Room",
                "source_disc_field": empty_clinic567.SOURCE_SCENE,
                "target_resources": list(
                    empty_clinic567.EMPTY_CLINIC567_TARGET_IDS
                ),
                "source_resources": list(
                    empty_clinic567.EMPTY_CLINIC567_SOURCE_IDS
                ),
                "bed": {
                    "source_model_index": empty_clinic567.BED_MODEL_INDEX,
                    "source_header_node": empty_clinic567.BED_HEADER_NODE,
                    "installed_header_node": (
                        empty_clinic567.BED_HEADER_NODE
                        + len(DONOR_DOOR_COLLISION_CONTRACTS[567])
                    ),
                    "model_identity": list(
                        empty_clinic567.BED_MODEL_IDENTITY
                    ),
                    "preserved": True,
                },
                "route": {
                    "controller_entity": empty_clinic567.RETURN_CONTROLLER,
                    "leaf_helper_entity": empty_clinic567.RETURN_HELPER,
                    "destination": [
                        empty_clinic567.RETURN_FIELD,
                        empty_clinic567.RETURN_PARAMETER,
                    ],
                },
                "terminal": {
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
                    "action_pc": exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC,
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
                "behavior": (
                    "exploration-only empty room with a repeatable no-patient "
                    "workstation readout; one reciprocal animated exit; all "
                    "retail NPC, automatic, battle, and progression routines "
                    "unreachable; all random encounter weights zero"
                ),
            },
            "intake_examination_rooms": {
                "source_disc_field": exam_rooms.SOURCE_SCENE,
                "source_resources": list(exam_rooms.SOURCE_IDS),
                "shared_style": (
                    "bright Solaris medical examination room with an intact "
                    "bed and illuminated clinical workstation"
                ),
                "population_policy": (
                    "fields 591, 592 and 594 each contain one solid, talkable physician "
                    "administering aid to a different native Soylent demihuman; "
                    "fields 567 and 593 have no patient or doctor"
                ),
                "intake_controller_entities": list(
                    INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES
                ),
                "intake_helper_entities": list(
                    INTAKE_EXAM_ROOM_HELPER_ENTITIES
                ),
                "intake_threshold_header_entities": list(
                    INTAKE_EXAM_ROOM_THRESHOLD_HEADER_ENTITIES
                ),
                "intake_threshold_model": {
                    "model_index": INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX,
                    "size": INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SIZE,
                    "sha256": INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SHA256,
                    "flags": f"0x{INTAKE_EXAM_ROOM_THRESHOLD_MODEL_FLAGS:04X}",
                    "placements": [
                        [yaw, origin_x, origin_y, origin_z]
                        for yaw, origin_x, origin_y, origin_z in (
                            INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS
                        )
                    ],
                    "rendering": (
                        "allocation-preserving clone of retail model 19's "
                        "single top-facing textured floor-apron FT4: 89 units "
                        "wide, 44 units beyond the leaf "
                        "on the far side, with no geometry on the accessible "
                        "hall side or above the leaf; the far-depth V endpoint "
                        "is capped at cyan-shadow row 0x8D before the source "
                        "texture's near-black tail; fourteen retained F3 slots "
                        "remain degenerate"
                    ),
                },
                "intake_camera_occluder_model": {
                    "model_index": INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX,
                    "size": INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SIZE,
                    "native_sha256": (
                        INTAKE_EXAM_ROOM_NATIVE_OCCLUDER_MODEL_SHA256
                    ),
                    "final_sha256": INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SHA256,
                    "disabled_mesh_groups": [0, 2],
                    "rendering": (
                        "only the native flat-black F3 corner-cap and F4 "
                        "ceiling-fascia index records are degenerate; textured "
                        "groups, packets, counts, offsets, pointers, and model "
                        "allocation remain unchanged"
                    ),
                },
                "intake_entry_parameters": list(
                    INTAKE_EXAM_ROOM_ENTRY_PARAMETERS
                ),
                "entrance_requirement": "security_keycard",
                "rooms": [
                    {
                        "field": spec.scene,
                        "target_resources": list(
                            exam_rooms.TARGET_IDS_BY_SCENE[spec.scene]
                        ),
                        "intake_controller_entity": controller,
                        "intake_return_parameter": spec.return_parameter,
                        "terminal_entity": exam_rooms.TERMINAL_ENTITY,
                        "terminal_entities": list(
                            exam_rooms.TERMINAL_ENTITIES
                        ),
                        "terminal_position": list(
                            exam_rooms.TERMINAL_POSITION
                        ),
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
                            "half_extents_script_units": [
                                exam_rooms.TERMINAL_INTERACTION_HALF_WIDTH,
                                exam_rooms.TERMINAL_INTERACTION_HALF_DEPTH,
                            ],
                            "effective_half_reach_world_units": list(
                                exam_rooms.TERMINAL_EFFECTIVE_HALF_REACH
                            ),
                            "requires_facing": (
                                exam_rooms.TERMINAL_REQUIRES_FACING
                            ),
                        },
                        "bed_model_index": exam_rooms.BED_MODEL_INDEX,
                        "patient_record": {
                            "dialogue_id": (
                                exam_rooms.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[
                                    spec.scene
                                ]
                            ),
                            "dialogue": (
                                exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE[
                                    spec.scene
                                ].removesuffix("<Close>")
                            ),
                            "repeatable": True,
                        },
                        "doctor": {
                            "present": spec.scene != 593,
                            "entity": exam_rooms.DOCTOR_ENTITY,
                            "graphic_bank": exam_rooms.DOCTOR_BANK,
                            "position": list(exam_rooms.DOCTOR_POSITION),
                            "triangle": exam_rooms.DOCTOR_TRIANGLE,
                            "dialogue_id": (
                                exam_rooms.DOCTOR_DIALOGUE_IDS_BY_SCENE[
                                    spec.scene
                                ]
                            ),
                            "dialogue": spec.doctor_dialogue.removesuffix(
                                "<Close>"
                            ),
                            "actor_sha256": (
                                exam_rooms.DOCTOR_ACTOR_IDENTITY[1]
                            ),
                            "sprite_sha256": (
                                exam_rooms.DOCTOR_SPRITE_IDENTITY[1]
                            ),
                        },
                        "patient": {
                            "present": spec.scene != 593,
                            "entity": exam_rooms.PATIENT_ENTITY,
                            "graphic_bank": (
                                exam_rooms.PATIENT_TARGET_BANK
                            ),
                            "position": list(exam_rooms.PATIENT_POSITION),
                            "triangle": exam_rooms.PATIENT_TRIANGLE,
                            "dialogue_id": (
                                exam_rooms.PATIENT_DIALOGUE_IDS_BY_SCENE[
                                    spec.scene
                                ]
                            ),
                            "dialogue": spec.patient_dialogue.removesuffix(
                                "<Close>"
                            ),
                            "appearance": (
                                exam_rooms.PATIENT_ASSET_SPECS[
                                    spec.scene
                                ].appearance
                            ),
                            "asset_source": {
                                "field": (
                                    exam_rooms.PATIENT_ASSET_SPECS[
                                        spec.scene
                                    ].source_scene
                                ),
                                "bank": (
                                    exam_rooms.PATIENT_ASSET_SPECS[
                                        spec.scene
                                    ].source_bank
                                ),
                                "actor_sha256": (
                                    exam_rooms.PATIENT_ASSET_SPECS[
                                        spec.scene
                                    ].actor_identity[1]
                                ),
                                "sprite_sha256": (
                                    exam_rooms.PATIENT_ASSET_SPECS[
                                        spec.scene
                                    ].sprite_identity[1]
                                ),
                            },
                        },
                        "awards_quarantine_keycard": (
                            spec.awards_quarantine_keycard
                        ),
                        "role": (
                            "Unoccupied examination room with the Quarantine keycard terminal"
                            if spec.scene == 593 else spec.role
                        ),
                    }
                    for spec, controller in zip(
                        (
                            spec
                            for spec in exam_rooms.EXAM_ROOM_SPECS
                            if (spec.scene, exam_rooms.ENTRY_PARAMETER)
                            in INTAKE_EXAM_ROOM_DESTINATIONS
                        ),
                        INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES,
                        strict=True,
                    )
                ],
                "quarantine_keycard_source_field": 593,
                "quarantine_keycard_operand": QUARANTINE_KEYCARD_OPERAND,
                "quarantine_keycard_bit_index": QUARANTINE_KEYCARD_BIT_INDEX,
                "quarantine_keycard_mask": QUARANTINE_KEYCARD_MASK,
                "pickup_sound_id": exam_rooms.ITEM_ACQUISITION_SOUND_ID,
                "policy": (
                    "all four terminals retain their distinct stored diagnostic "
                    "records; field 593 has no patient or doctor and first offers "
                    "the visibly inserted card, committing it once"
                ),
            },
            "intake_treatment_preparation": {
                "field": 594,
                "name": "Treatment Preparation Room",
                "source_disc_field": exam_rooms.SOURCE_SCENE,
                "source_resources": list(exam_rooms.SOURCE_IDS),
                "target_resources": list(
                    exam_rooms.TARGET_IDS_BY_SCENE[594]
                ),
                "intake_controller_entity": INTAKE_FREIGHT_DOOR_ENTITY,
                "intake_entry_parameter": 5,
                "entry_parameter": exam_rooms.ENTRY_PARAMETER,
                "return_controller_entity": exam_rooms.RETURN_CONTROLLER,
                "return_leaf_helper_entity": exam_rooms.RETURN_HELPER,
                "return_destination": [
                    exam_rooms.RETURN_FIELD,
                    exam_rooms.RETURN_PARAMETERS_BY_SCENE[594],
                ],
                "terminal_entity": exam_rooms.TERMINAL_ENTITY,
                "terminal_entities": list(exam_rooms.TERMINAL_ENTITIES),
                "terminal_position": list(exam_rooms.TERMINAL_POSITION),
                "terminal_positions": [
                    list(position)
                    for position in exam_rooms.TERMINAL_POSITIONS
                ],
                "terminal_triangles": list(exam_rooms.TERMINAL_TRIANGLES),
                "terminal_model_index": (
                    exam_rooms.MEDICAL_TERMINAL_MODEL_INDEX
                ),
                "terminal_interaction": {
                    "half_extents_script_units": [
                        exam_rooms.TERMINAL_INTERACTION_HALF_WIDTH,
                        exam_rooms.TERMINAL_INTERACTION_HALF_DEPTH,
                    ],
                    "effective_half_reach_world_units": list(
                        exam_rooms.TERMINAL_EFFECTIVE_HALF_REACH
                    ),
                    "requires_facing": exam_rooms.TERMINAL_REQUIRES_FACING,
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
                    "dialogue_id": exam_rooms.DOCTOR_DIALOGUE_IDS_BY_SCENE[594],
                    "dialogue": exam_rooms.DOCTOR_DIALOGUES_BY_SCENE[
                        594
                    ].removesuffix("<Close>"),
                    "actor_sha256": exam_rooms.DOCTOR_ACTOR_IDENTITY[1],
                    "sprite_sha256": exam_rooms.DOCTOR_SPRITE_IDENTITY[1],
                },
                "patient": {
                    "entity": exam_rooms.PATIENT_ENTITY,
                    "graphic_bank": exam_rooms.PATIENT_TARGET_BANK,
                    "position": list(exam_rooms.PATIENT_POSITION),
                    "triangle": exam_rooms.PATIENT_TRIANGLE,
                    "dialogue_id": exam_rooms.PATIENT_DIALOGUE_IDS_BY_SCENE[594],
                    "dialogue": exam_rooms.PATIENT_DIALOGUES_BY_SCENE[
                        594
                    ].removesuffix("<Close>"),
                    "appearance": exam_rooms.PATIENT_ASSET_SPECS[594].appearance,
                    "asset_source": {
                        "field": exam_rooms.PATIENT_ASSET_SPECS[594].source_scene,
                        "bank": exam_rooms.PATIENT_ASSET_SPECS[594].source_bank,
                        "actor_sha256": (
                            exam_rooms.PATIENT_ASSET_SPECS[594].actor_identity[1]
                        ),
                        "sprite_sha256": (
                            exam_rooms.PATIENT_ASSET_SPECS[594].sprite_identity[1]
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
            "recovered_room_donors": {
                "clinical_stabilization_ward": {
                    "status": "recovered into the active dungeon",
                    "registry": (
                        "modules/soylent_system/content/reserved_room_donors.json"
                    ),
                    "module": (
                        "tools/surface_soylent_campaign_stabilization590.py"
                    ),
                    "field": stabilization590.SCENE,
                    "source_disc_field": donor567.SCENE,
                    "source_resources": list(donor567.DONOR567_SOURCE_IDS),
                    "target_resources": list(stabilization590.TARGET_IDS),
                    "routes": [
                        {
                            "controller_entity": donor567.LOBBY_CONTROLLER,
                            "destination": list(
                                stabilization590.MANIFOLD_BULKHEAD_DESTINATION
                            ),
                        },
                        {
                            "controller_entity": donor567.SERVICE_CONTROLLER,
                            "destination": list(
                                stabilization590.MANIFOLD_STAFF_DESTINATION
                            ),
                        },
                        {
                            "controller_entity": donor567.RESTRICTED_CONTROLLER,
                            "destination": list(stabilization590.SORTING_DESTINATION),
                            "gate": "production_clearance",
                        },
                    ],
                },
            },
            "post_keycard_dungeon": {
                "entry_boundary": {
                    "award_field": 550,
                    "credential_operand": SECURITY_KEYCARD_OPERAND,
                    "credential_bit_index": SECURITY_KEYCARD_BIT_INDEX,
                    "credential_mask": SECURITY_KEYCARD_MASK,
                    "intake_door_entities": [
                        INTAKE_PATIENT_DOOR_ENTITY,
                        INTAKE_FREIGHT_DOOR_ENTITY,
                        *INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES,
                    ],
                    "unlocked_destinations": [
                        list(INTAKE_PATIENT_DESTINATION),
                        list(INTAKE_FREIGHT_DESTINATION),
                        *(
                            list(destination)
                            for destination in INTAKE_EXAM_ROOM_DESTINATIONS
                        ),
                    ],
                    "policy": (
                        "the clinic security victory is the true dungeon "
                        "threshold; the patient-service route, Treatment "
                        "Preparation Room, and all three Intake "
                        "examination rooms require that credential"
                    ),
                },
                "service_manifold": {
                    "field": 565,
                    "internal_passage": {
                        "entity": 12,
                        "native_action_pc": base.FIELD565_TONE_GATE_ACTION_PC,
                        "requirement": "five-tone directional puzzle",
                        "input_sequence": [
                            "Up",
                            "Down",
                            "Up",
                            "Left",
                            "Right",
                        ],
                        "award_operand": TONE_OPERAND,
                        "award_bit_index": TONE_BIT_INDEX,
                        "award_mask": TONE_MASK,
                        "leaf_helper_entity": 21,
                        "physical_seal_entity": 30,
                        "saved_state_1_door": True,
                    },
                    "future_lab_handoff": {
                        "entity": FIELD565_FUTURE_LAB_HANDOFF_ENTITY,
                        "arrival_parameter": 3,
                        "destination": None,
                        "dialogue_id": (
                            SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE_ID
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
                    "quarantine_entry": {
                        "entity": 10,
                        "requirement": "quarantine_keycard",
                        "credential_operand": QUARANTINE_KEYCARD_OPERAND,
                        "credential_bit_index": QUARANTINE_KEYCARD_BIT_INDEX,
                        "credential_mask": QUARANTINE_KEYCARD_MASK,
                        "destination": [620, 1],
                    },
                    "quarantine_exit": {
                        "field": 620,
                        "entity": QUARANTINE_CURRENT_END_DOOR_ENTITY,
                        "status": "active_diagnostic_gate",
                        "action_pc": QUARANTINE_CURRENT_END_DOOR_ACTION_PC,
                        "dialogue_id": QUARANTINE_CURRENT_END_DIALOGUE_ID,
                        "dialogue": QUARANTINE_COMPLETION_DIALOGUE.removesuffix("<Close>"),
                        "requirement": "Genome/Limiter/Nanomachines on; Caste off",
                        "required_local_value": 0x0070,
                        "awards": "quarantine_complete",
                        "destination": [565, 6],
                        "preserved_return_entity": 23,
                        "animates_leaf": True,
                        "transitions": True,
                        "writes_state": True,
                    },
                    "stabilization_routes": [
                        {
                            "entity": 5,
                            "destination": [590, 0],
                        },
                        {
                            "entity": 6,
                            "destination": [590, 1],
                            "saved_state_1_panel": True,
                        },
                    ],
                    "wide_outer_action_targets": {
                        "entities": list(range(4, 11)),
                        "half_extent_script_units": (
                            FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT
                        ),
                        "bounce_safe_arrivals": {
                            str(parameter): list(values[1][:2])
                            for parameter, values in FIELD565_CLEAR_ARRIVALS.items()
                        },
                    },
                },
                "quarantine_keycard_terminal": {
                    "field": 593,
                    "npc_entities": [],
                    "retired_npc_entities": [
                        exam_rooms.PATIENT_ENTITY, exam_rooms.DOCTOR_ENTITY,
                    ],
                    "independent_room": True,
                    "intake_origin": [621, 9],
                    "entry": [593, exam_rooms.ENTRY_PARAMETER],
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
                        "half_extents_script_units": [
                            exam_rooms.TERMINAL_INTERACTION_HALF_WIDTH,
                            exam_rooms.TERMINAL_INTERACTION_HALF_DEPTH,
                        ],
                        "effective_half_reach_world_units": list(
                            exam_rooms.TERMINAL_EFFECTIVE_HALF_REACH
                        ),
                        "requires_facing": (
                            exam_rooms.TERMINAL_REQUIRES_FACING
                        ),
                    },
                    "room_style": (
                        "bright Solaris examination room with a bed and an "
                        "illuminated clinical terminal"
                    ),
                    "entrance_requirements": ["security_keycard"],
                    "credential_operand": QUARANTINE_KEYCARD_OPERAND,
                    "credential_bit_index": QUARANTINE_KEYCARD_BIT_INDEX,
                    "credential_mask": QUARANTINE_KEYCARD_MASK,
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
                "interface_scanner_annex": {
                    "field": 588,
                    "independent_room": True,
                    "service_origin": [565, 5],
                    "entry": [588, 0],
                    "return": [565, 5],
                    "entity": donor588.CONSOLE_ENTITY,
                    "visible_static_nodes": list(
                        donor588.CAMPAIGN_VISIBLE_SCANNER_STATIC_NODES
                    ),
                    "donor_story_and_loot_retired": True,
                    "position": [INTERFACE_CONSOLE.x, INTERFACE_CONSOLE.z],
                    "room_style": "bright Soylent diagnostic scanner lab",
                    "entrance_requirements": [],
                    "awards": "interface_cutoff_armed",
                    "credential_award": None,
                    "policy": (
                        "the restored Service-Manifold annex arms only the "
                        "interface cutoff; it never issues a keycard"
                    ),
                },
                "clinical_stabilization_ward": {
                    "field": stabilization590.SCENE,
                    "production_bulkhead": {
                        "entity": donor567.RESTRICTED_CONTROLLER,
                        "requirements": [
                            "security_keycard",
                            "tone_authorized",
                            "quarantine_complete",
                            "interface_cutoff_armed",
                        ],
                        "destination": [624, 0],
                    },
                    "return_routes": [
                        list(stabilization590.MANIFOLD_BULKHEAD_DESTINATION),
                        list(stabilization590.MANIFOLD_STAFF_DESTINATION),
                    ],
                },
                "organic_resonance": {
                    "field": 589,
                    "entity": RESONANCE_CLUE_ENTITY,
                    "native_action_pc": RESONANCE_CLUE_ACTION_PC,
                    "native_tone_order": ["Up", "Down", "Up", "Left", "Right"],
                    "receipt_dialogue_id": (
                        RESONANCE_CLUE_RECEIPT_DIALOGUE_ID
                    ),
                    "receipt_sound_id": PROGRESSION_CONFIRM_SOUND_ID,
                    "clue_seen_operand": TONE_OPERAND,
                    "clue_seen_bit_index": RESONANCE_CLUE_BIT_INDEX,
                    "clue_seen_mask": RESONANCE_CLUE_BIT_MASK,
                    "policy": (
                        "plays the authentic five sounds and Fei/Citan clue; "
                        "only field 565's native input panel awards tone authorization"
                    ),
                },
                "ordered_back_half": [
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
                        "receipt_sound_id": PROGRESSION_CONFIRM_SOUND_ID,
                        "awards": "sorter_complete",
                    },
                    {
                        "field": 626,
                        "objective": (
                            "disable fusion and pattern while retaining containment"
                        ),
                        "receipt_dialogue_id": 5,
                        "receipt_sound_id": PROGRESSION_CONFIRM_SOUND_ID,
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
                "finale": {
                    "field": 622,
                    "battle_configuration": 9,
                    "progression_sound_id": PROGRESSION_CONFIRM_SOUND_ID,
                    "pending": {
                        "operand": STATE_OPERAND,
                        "bit_index": FINALE_EPILOGUE_PENDING_BIT_INDEX,
                        "mask": FINALE_EPILOGUE_PENDING_BIT_MASK,
                        "timing": "set immediately after FE7F battle synchronization",
                    },
                    "secured": {
                        "operand": STATE_OPERAND,
                        "bit_index": SECURED_BIT_INDEX,
                        "mask": SECURED_BIT_MASK,
                        "timing": "set only after the epilogue receipt closes",
                    },
                    "recovery": (
                        "pending without secured resumes the epilogue from the "
                        "boss console without replaying Sufal"
                    ),
                    "completion": (
                        "clear pending, unlock the reciprocal 622/623 emergency "
                        "return, keep the dungeon explorable, and do not force a "
                        "world-map or title transition"
                    ),
                },
            },
            "intake_checkin": {
                "receptionist": {
                    "field": 621,
                    "entity": INTAKE_RECEPTIONIST_ENTITY,
                    "retail_init_pc": INTAKE_RECEPTIONIST_RETAIL_INIT_PC,
                    "wide_init_pc": INTAKE_RECEPTIONIST_WIDE_INIT_PC,
                    "action_pc": INTAKE_RECEPTIONIST_ACTION_PC,
                    "saved_stance": [870.0675354, 1433.6101837],
                    "actor_position": [870, 1302],
                    "retail_circular_effective_reach": 64,
                    "interaction_operands": [
                        INTAKE_RECEPTIONIST_INTERACTION_HALF_WIDTH,
                        INTAKE_RECEPTIONIST_INTERACTION_HALF_DEPTH,
                    ],
                    "interaction_effective_half_extents": [
                        2 * INTAKE_RECEPTIONIST_INTERACTION_HALF_WIDTH
                        + PLAYER_COLLISION_RADIUS,
                        2 * INTAKE_RECEPTIONIST_INTERACTION_HALF_DEPTH
                        + PLAYER_COLLISION_RADIUS,
                    ],
                    "interaction_policy": (
                        "rectangular, no facing cone, collision ghosted; original "
                        "sprite and counter remain visible"
                    ),
                    "before_registration": RECEPTIONIST_PRECHECK_DIALOGUE.removesuffix(
                        "<Close>"
                    ),
                    "after_registration": RECEPTIONIST_POSTCHECK_DIALOGUE.removesuffix(
                        "<Close>"
                    ),
                },
                "door_behind_saved_stance": {
                    "field": 621,
                    "entity": INTAKE_ARCHIVE_DOOR_ENTITY,
                    "action_pc": INTAKE_ARCHIVE_DOOR_ACTION_PC,
                    "destination": [549, 0],
                },
                "quarantine_keycard_door": {
                    "field": 621,
                    "entity": INTAKE_QUARANTINE_DOOR_ENTITY,
                    "saved_stance": [69.98291015625, 840],
                    "saved_facing": 0,
                    "triangle": 18,
                    "locked_action_pc": INTAKE_QUARANTINE_LOCK_ACTION_PC,
                    "preserved_unlocked_action_pc": (
                        INTAKE_QUARANTINE_DOOR_ACTION_PC
                    ),
                    "destination": list(
                        INTAKE_QUARANTINE_DESTINATION
                    ),
                    "dialogue": INTAKE_QUARANTINE_LOCK_DIALOGUE.removesuffix(
                        "<Close>"
                    ),
                    "unlock_trigger": (
                        "accept the Quarantine keycard in Examination Room C"
                    ),
                    "credential_operand": QUARANTINE_KEYCARD_OPERAND,
                    "credential_bit_index": QUARANTINE_KEYCARD_BIT_INDEX,
                    "credential_mask": QUARANTINE_KEYCARD_MASK,
                    "policy": (
                        "bit-clear interactions drain Cross and report the "
                        "keycard requirement; bit-set interactions jump to the "
                        "retained native e22 open-and-enter action"
                    ),
                },
                "security_keycard_patient_door": {
                    "field": 621,
                    "entity": INTAKE_PATIENT_DOOR_ENTITY,
                    "gate_action_pc": INTAKE_PATIENT_KEYCARD_GATE_ACTION_PC,
                    "preserved_unlocked_action_pc": (
                        INTAKE_PATIENT_DOOR_ACTION_PC
                    ),
                    "destination": list(INTAKE_PATIENT_DESTINATION),
                    "credential_operand": SECURITY_KEYCARD_OPERAND,
                    "credential_bit_index": SECURITY_KEYCARD_BIT_INDEX,
                    "credential_mask": SECURITY_KEYCARD_MASK,
                    "locked_dialogue": (
                        INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE.removesuffix(
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
                "security_keycard_freight_door": {
                    "field": 621,
                    "entity": INTAKE_FREIGHT_DOOR_ENTITY,
                    "role": "Treatment Preparation Room entrance",
                    "saved_stance": [1665.015869140625, 396],
                    "saved_facing": 0x0800,
                    "triangle": 85,
                    "gate_action_pc": INTAKE_FREIGHT_KEYCARD_GATE_ACTION_PC,
                    "preserved_unlocked_action_pc": (
                        INTAKE_FREIGHT_DOOR_ACTION_PC
                    ),
                    "destination": list(INTAKE_FREIGHT_DESTINATION),
                    "credential_operand": SECURITY_KEYCARD_OPERAND,
                    "credential_bit_index": SECURITY_KEYCARD_BIT_INDEX,
                    "credential_mask": SECURITY_KEYCARD_MASK,
                    "locked_dialogue": (
                        INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE.removesuffix(
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
                "survivor_movement": {
                    "version": 198,
                    "field": 621,
                    "entities": sorted(INTAKE_WANDERING_SURVIVOR_SPECS),
                    "random_walk_opcode": "59 00",
                    "bounding_zone_opcode": "17 <four signed X/Z corners> FF",
                    "movement_zones": [
                        {
                            "entity": entity,
                            "start": list(
                                INTAKE_WANDERING_SURVIVOR_SPECS[entity][3]
                            ),
                            "corners": [list(point) for point in zone],
                            "opcode": (
                                _intake_survivor_movement_zone_body(zone)
                                .hex(" ")
                                .upper()
                            ),
                        }
                        for entity, zone in sorted(
                            INTAKE_SURVIVOR_MOVEMENT_ZONES.items()
                        )
                    ],
                    "collision_radius": INTAKE_SURVIVOR_COLLISION_RADIUS,
                    "walkmesh_halo": INTAKE_SURVIVOR_WALKMESH_HALO,
                    "minimum_zone_separation": (
                        INTAKE_SURVIVOR_MIN_ZONE_SEPARATION
                    ),
                    "center_aisle": list(INTAKE_SURVIVOR_CENTER_AISLE),
                    "minimum_doctor_clearance": (
                        INTAKE_SURVIVOR_MIN_DOCTOR_CLEARANCE
                    ),
                    "archive_door_position": list(INTAKE_ARCHIVE_DOOR_POSITION),
                    "archive_door_clearance": (
                        INTAKE_SURVIVOR_DOOR_CLEARANCE
                    ),
                    "archive_door_clearance_after_halo": (
                        INTAKE_SURVIVOR_DOOR_CLEARANCE
                        - INTAKE_SURVIVOR_WALKMESH_HALO
                    ),
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
                        ) in sorted(INTAKE_WANDERING_SURVIVOR_SPECS.items())
                        if retail_position != bounded_position
                    ],
                    "policy": (
                        "retain native random walking in nine disjoint clockwise "
                        "microzones whose 24-unit halos remain on the walkmesh; "
                        "keep every pair collision-separated and leave the "
                        "central player/physician aisle open"
                    ),
                },
                "terminal": {
                    "field": 549,
                    "entity": ARCHIVE_TERMINAL_ENTITY,
                    "action_pc": ARCHIVE_CHECKIN_ACTION_PC,
                    "retained_screen_source_action_pc": (
                        ARCHIVE_TERMINAL_RETAIL_ACTION_PC
                    ),
                    "binary_archive_menu_reachable": False,
                    "native_panel_entities": list(
                        ARCHIVE_TERMINAL_SCREEN_ENTITIES
                    ),
                    "native_screen_open_script": (
                        ARCHIVE_TERMINAL_SCREEN_OPEN_SCRIPT
                    ),
                    "native_screen_open_pcs": list(
                        ARCHIVE_TERMINAL_SCREEN_OPEN_PCS
                    ),
                    "native_screen_close_script": (
                        ARCHIVE_TERMINAL_SCREEN_CLOSE_SCRIPT
                    ),
                    "native_screen_close_pcs": list(
                        ARCHIVE_TERMINAL_SCREEN_CLOSE_PCS
                    ),
                    "screen_policy": (
                        "run the retained six-panel opening before every "
                        "check-in interaction and launch the retained native "
                        "close after every custom registration or vitals path; "
                        "the unrelated retail binary-code menu is unreachable"
                    ),
                },
                "registration": {
                    "aliases": list(CHECKIN_ALIASES),
                    "real_name_offered": False,
                    "completion_operand": STATE_OPERAND,
                    "completion_bit_index": CHECKIN_BIT_INDEX,
                    "completion_mask": CHECKIN_BIT_MASK,
                    "cancel_sets_completion": False,
                },
                "appointment": {
                    "packed_operand": APPOINTMENT_OPERAND,
                    "time_mask": APPOINTMENT_TIME_MASK,
                    "alias_mask": APPOINTMENT_ALIAS_MASK,
                    "alias_codes": {
                        alias: APPOINTMENT_ALIAS_CODES[index]
                        for index, alias in enumerate(CHECKIN_ALIASES)
                    },
                    "phase_operand": STATE_OPERAND,
                    "phase_mask": APPOINTMENT_PHASE_MASK,
                    "phases": {
                        "registered": APPOINTMENT_PHASE_REGISTERED,
                        "timer_armed": APPOINTMENT_PHASE_ARMED,
                        "called": APPOINTMENT_PHASE_CALLED,
                        "entered": APPOINTMENT_PHASE_ENTERED,
                        "legacy_v185_briefed": (
                            APPOINTMENT_PHASE_LEGACY_BRIEFED
                        ),
                        "office_active": APPOINTMENT_PHASE_OFFICE_ACTIVE,
                        "resolved": APPOINTMENT_PHASE_RESOLVED,
                    },
                    "office_stage_mask": APPOINTMENT_STAGE_MASK,
                    "office_stages": {
                        "await_refusal": APPOINTMENT_STAGE_AWAIT_REFUSAL,
                        "final_warning": APPOINTMENT_STAGE_FINAL_WARNING,
                        "security_pending": (
                            APPOINTMENT_STAGE_SECURITY_PENDING
                        ),
                        "flee_pending": APPOINTMENT_STAGE_FLEE_PENDING,
                        "complete": APPOINTMENT_STAGE_COMPLETE,
                        "security_entering": (
                            APPOINTMENT_STAGE_SECURITY_ENTERING
                        ),
                        "battle_pending": APPOINTMENT_STAGE_BATTLE_PENDING,
                    },
                    "delay_seconds": APPOINTMENT_DELAY_SECONDS,
                    "timer_starts": "field 549 return transition after registration",
                    "doctor": {
                        "lobby_field": 621,
                        "entity": INTAKE_DOCTOR_ENTITY,
                        "waiting_position": list(INTAKE_DOCTOR_WAITING_POSITION),
                        "office_door_entity": INTAKE_CLINIC_DOOR_ENTITY,
                        "collision": {
                            "version": 199,
                            "bounding_volume_opcode": (
                                DOCTOR_RECTANGULAR_BOUNDING_VOLUME.hex(" ").upper()
                            ),
                            "runtime_half_extents": [32, 32],
                            "retained_collision_radius": 16,
                            "transit_flags_opcode": (
                                DOCTOR_TRANSIT_COLLISION_FLAGS.hex(" ").upper()
                            ),
                            "stationary_flags_opcode": (
                                DOCTOR_STATIONARY_COLLISION_FLAGS.hex(" ").upper()
                            ),
                            "policy": (
                                "ghosted while hidden or following a scripted "
                                "doorway route; solid and immovable after reaching "
                                "reception and on a called-phase field reload"
                            ),
                        },
                        "instruction": "Follow me into the examination room.",
                        "follow_destination": list(INTAKE_CLINIC_DESTINATION),
                        "follow_door_open_variable": (
                            INTAKE_DOCTOR_DOOR_OPEN_VARIABLE
                        ),
                        "follow_door_policy": (
                            "the physician leaves the native lobby leaf at its "
                            "fully open endpoint and the live entered-phase "
                            "action transitions directly without closing or "
                            "replaying the opening animation; a true field "
                            "reload clears the local flag and safely falls "
                            "back to the native opening action"
                        ),
                        "graphic_bank": INTAKE_DOCTOR_GRAPHIC,
                        "asset_source": {
                            "field": CLINIC_SOURCE_SCENE,
                            "bank": INTAKE_DOCTOR_SOURCE_BANK,
                            "actor_sha256": (
                                INTAKE_SOURCE_PHYSICIAN_ACTOR_SHA256
                            ),
                            "sprite_sha256": (
                                INTAKE_SOURCE_PHYSICIAN_SPRITE_SHA256
                            ),
                        },
                        "reassigned_old_bank_user": {
                            "entity": INTAKE_REASSIGNED_CIVILIAN_ENTITY,
                            "graphic_bank": INTAKE_REASSIGNED_CIVILIAN_GRAPHIC,
                        },
                    },
                    "office": {
                        "field": 550,
                        "doctor_entity": CLINIC_DOCTOR_ENTITY,
                        "doctor_collision_policy": (
                            "solid and immovable in every visible unresolved "
                            "office phase; ghosted while hidden and before the "
                            "post-battle escape route"
                        ),
                        "source_field": CLINIC_SOURCE_SCENE,
                        "source_bundle_id": CLINIC_SOURCE_BUNDLE_ID,
                        "source_graphics_id": CLINIC_SOURCE_GRAPHICS_ID,
                        "briefing_dialogue_id": CLINIC_BRIEFING_DIALOGUE_ID,
                        "patient_record_terminal": {
                            "version": blueprint.CURRENT_RELEASE_VERSION,
                            "entity": CLINIC_RECORD_TERMINAL_ENTITY,
                            "entities": list(CLINIC_RECORD_TERMINAL_ENTITIES),
                            "static_node": CLINIC_RECORD_TERMINAL_STATIC_NODE,
                            "static_model": CLINIC_RECORD_TERMINAL_STATIC_MODEL,
                            "position": [
                                CLINIC_RECORD_TERMINAL.x,
                                CLINIC_RECORD_TERMINAL.z,
                            ],
                            "positions": [
                                [console.x, console.z]
                                for console in CLINIC_RECORD_TERMINALS
                            ],
                            "operator_triangle": (
                                CLINIC_RECORD_TERMINAL.triangle
                            ),
                            "operator_triangles": list(
                                CLINIC_RECORD_TERMINAL_OPERATOR_TRIANGLES
                            ),
                            "carriers": [
                                {
                                    "entity": entity,
                                    "position": [console.x, console.z],
                                    "operator_triangle": console.triangle,
                                    "runtime_carrier_triangle": 0,
                                }
                                for entity, console in zip(
                                    CLINIC_RECORD_TERMINAL_ENTITIES,
                                    CLINIC_RECORD_TERMINALS,
                                    strict=True,
                                )
                            ],
                            "runtime_carrier_triangle": 0,
                            "interaction_half_extents": [
                                CLINIC_RECORD_TERMINAL.interaction_half_width,
                                CLINIC_RECORD_TERMINAL.interaction_half_depth,
                            ],
                            "requires_facing": (
                                CLINIC_RECORD_TERMINAL.requires_facing
                            ),
                            "alias_operand": APPOINTMENT_OPERAND,
                            "alias_mask": APPOINTMENT_ALIAS_MASK,
                            "alias_dialogue_ids": list(
                                CLINIC_RECORD_ALIAS_DIALOGUE_IDS
                            ),
                            "missing_record_dialogue_id": (
                                CLINIC_RECORD_MISSING_DIALOGUE_ID
                            ),
                            "weight_character_id": PATIENT_CHARACTER_IDS["Fei"],
                            "weight_read_opcode": "FE 69",
                            "weight_write_opcode": None,
                            "vitals": {
                                "pulse_bpm": PATIENT_AUTHORED_VITALS["Fei"][0],
                                "blood_pressure": (
                                    PATIENT_AUTHORED_VITALS["Fei"][1]
                                ),
                                "temperature_c": (
                                    PATIENT_AUTHORED_VITALS["Fei"][2]
                                ),
                                "respiration_per_min": (
                                    PATIENT_AUTHORED_VITALS["Fei"][3]
                                ),
                                "observation": (
                                    PATIENT_AUTHORED_VITALS["Fei"][4]
                                ),
                            },
                            "biological_compatibility": {
                                "index_percent": 100,
                                "classification": "PERFECT FIT",
                                "lore_role": "Sufal Mass integration suitability",
                            },
                            "policy": (
                                "repeatable, read-only alias-aware patient record; "
                                "live Status weight, authored clinical vitals, and "
                                "perfect biological compatibility; hidden ghost "
                                "carrier cannot collide with Fei or steal the "
                                "physician's Cross interaction"
                            ),
                        },
                        "refusal_dialogue_ids": [
                            CLINIC_FIRST_REFUSAL_DIALOGUE_ID,
                            CLINIC_SECURITY_CALL_DIALOGUE_ID,
                        ],
                        "security_arrival_dialogue_id": (
                            CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID
                        ),
                        "escape_dialogue_id": (
                            CLINIC_DOCTOR_ESCAPE_DIALOGUE_ID
                        ),
                        "exit_insistence_dialogue_id": (
                            CLINIC_EXIT_INSISTENCE_DIALOGUE_ID
                        ),
                        "exit_gate_scheduler": {
                            "version": 212,
                            "opcodes_per_entity_slice": 8,
                            "doctor_scratch_operand": (
                                APPOINTMENT_SCRATCH_VARIABLE
                            ),
                            "exit_scratch_operand": (
                                CLINIC_EXIT_SCRATCH_VARIABLE
                            ),
                            "policy": (
                                "the exit retains its phase/stage snapshot in a "
                                "private field-local word across scheduler frames; "
                                "the lower-ID doctor update cannot clobber it"
                            ),
                        },
                        "doorway_traversal": {
                            "version": 200,
                            "walkmesh_size": CLINIC_SOURCE_WALKMESH_SIZE,
                            "walkmesh_sha256": (
                                CLINIC_SOURCE_WALKMESH_SHA256
                            ),
                            "exterior_triangles": list(
                                CLINIC_WALKMESH_EXTERIOR_TRIANGLES
                            ),
                            "exterior_material": (
                                CLINIC_WALKMESH_EXTERIOR_MATERIAL
                            ),
                            "exterior_material_flags": (
                                f"0x{CLINIC_WALKMESH_FORBIDDEN_MATERIAL_FLAG:08X}"
                            ),
                            "actor_local_override": (
                                f"0x{CLINIC_DOORWAY_WALKMESH_OVERRIDE_FLAGS:04X}"
                            ),
                            "override_set_opcode": (
                                CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET.hex(
                                    " "
                                ).upper()
                            ),
                            "override_clear_opcode": (
                                CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR.hex(
                                    " "
                                ).upper()
                            ),
                            "security_clear_position": list(
                                CLINIC_SECURITY_OVERRIDE_CLEAR_POSITION
                            ),
                            "security_waypoint_max_steps": (
                                CLINIC_SECURITY_WAYPOINT_MAX_STEPS
                            ),
                            "doctor_threshold_max_steps": (
                                CLINIC_DOCTOR_THRESHOLD_WAYPOINT_MAX_STEPS
                            ),
                            "policy": (
                                "the leaf opens completely before actor-local "
                                "movement permission is set; security clears it "
                                "only on deep interior floor, while the doctor "
                                "crosses outside, remains visible for the blocking "
                                "close, hides, and then clears it; Fei's "
                                "solid seal and the global walkmesh never change"
                            ),
                        },
                        "security_keycard": {
                            "operand": SECURITY_KEYCARD_OPERAND,
                            "bit_index": SECURITY_KEYCARD_BIT_INDEX,
                            "mask": SECURITY_KEYCARD_MASK,
                            "dialogue_id": CLINIC_SECURITY_KEYCARD_DIALOGUE_ID,
                            "dialogue": (
                                CLINIC_SECURITY_KEYCARD_DIALOGUE.removesuffix(
                                    "<Close>"
                                )
                            ),
                            "acquisition_sound_id": (
                                SECURITY_KEYCARD_ACQUIRED_SOUND_ID
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
                        "security_formation": {
                            "source_field": CLINIC_SECURITY_SOURCE_SCENE,
                            "source_configuration": (
                                CLINIC_SECURITY_SOURCE_CONFIGURATION
                            ),
                            "installed_configuration": (
                                CLINIC_SECURITY_CONFIGURATION
                            ),
                            "members": [
                                "Security Cube",
                                "Security Cube",
                                "Solaris Guard",
                                "Solaris Guard",
                            ],
                            "on_foot": True,
                            "escape_disabled": True,
                            "random_weight": 0,
                            "arena": f"0x{CLINIC_SECURITY_ARENA:02X}",
                            "arena_retail_proof_configuration": (
                                CLINIC_SECURITY_BRIGHT_ARENA_CONFIGURATION
                            ),
                            "record": CLINIC_SECURITY_FORMATION.hex(
                                " "
                            ).upper(),
                            "resource_transplant": False,
                            "resource_policy": (
                                "references the checked normalized Disc 2 "
                                "resources in place; no stats, model, or arena "
                                "resource is transplanted"
                            ),
                            "normalized_disc2_resources": [
                                {
                                    "canonical_id": canonical_id,
                                    "role": role,
                                    "size": size,
                                    "sha256": sha256,
                                }
                                for canonical_id, (
                                    role,
                                    size,
                                    sha256,
                                ) in sorted(
                                    CLINIC_SECURITY_NORMALIZED_CD2_RESOURCES.items()
                                )
                            ],
                        },
                        "security_overworld_entrance": {
                            "entities": list(CLINIC_SECURITY_ENTITIES),
                            "guard_entities": list(
                                CLINIC_SECURITY_GUARD_ENTITIES
                            ),
                            "cube_entities": list(
                                CLINIC_SECURITY_CUBE_ENTITIES
                            ),
                            "guard_asset": {
                                "source_field": (
                                    CLINIC_SECURITY_GUARD_SOURCE_SCENE
                                ),
                                "source_bundle_id": (
                                    CLINIC_SECURITY_GUARD_SOURCE_BUNDLE_ID
                                ),
                                "source_bundle_size": (
                                    CLINIC_SECURITY_GUARD_SOURCE_BUNDLE_SIZE
                                ),
                                "source_bundle_sha256": (
                                    CLINIC_SECURITY_GUARD_SOURCE_BUNDLE_SHA256
                                ),
                                "source_bank": CLINIC_SECURITY_GUARD_SOURCE_BANK,
                                "target_bank": CLINIC_SECURITY_GUARD_TARGET_BANK,
                                "actor_size": CLINIC_SECURITY_GUARD_ACTOR_SIZE,
                                "actor_sha256": CLINIC_SECURITY_GUARD_ACTOR_SHA256,
                                "sprite_size": CLINIC_SECURITY_GUARD_SPRITE_SIZE,
                                "sprite_sha256": (
                                    CLINIC_SECURITY_GUARD_SPRITE_SHA256
                                ),
                                "mapping": list(CLINIC_SECURITY_GUARD_MAPPING),
                                "palette": CLINIC_SECURITY_GUARD_PALETTE,
                                "palette_sha256": (
                                    CLINIC_SECURITY_GUARD_PALETTE_SHA256
                                ),
                            },
                            "cube_asset": {
                                "source_field": CLINIC_SECURITY_CUBE_SOURCE_SCENE,
                                "source_bundle_id": (
                                    CLINIC_SECURITY_CUBE_SOURCE_BUNDLE_ID
                                ),
                                "source_bundle_size": (
                                    CLINIC_SECURITY_CUBE_SOURCE_BUNDLE_SIZE
                                ),
                                "source_bundle_sha256": (
                                    CLINIC_SECURITY_CUBE_SOURCE_BUNDLE_SHA256
                                ),
                                "source_bank": CLINIC_SECURITY_CUBE_SOURCE_BANK,
                                "target_bank": CLINIC_SECURITY_CUBE_TARGET_BANK,
                                "actor_size": CLINIC_SECURITY_CUBE_ACTOR_SIZE,
                                "actor_sha256": CLINIC_SECURITY_CUBE_ACTOR_SHA256,
                                "sprite_size": CLINIC_SECURITY_CUBE_SPRITE_SIZE,
                                "sprite_sha256": (
                                    CLINIC_SECURITY_CUBE_SPRITE_SHA256
                                ),
                                "source_mapping": list(
                                    CLINIC_SECURITY_CUBE_SOURCE_MAPPING
                                ),
                                "mapping": list(CLINIC_SECURITY_CUBE_MAPPING),
                            },
                            "installed_components": {
                                "actor_size": (
                                    CLINIC_SECURITY_INSTALLED_ACTOR_COMPONENT_SIZE
                                ),
                                "actor_sha256": (
                                    CLINIC_SECURITY_INSTALLED_ACTOR_COMPONENT_SHA256
                                ),
                                "sprite_size": (
                                    CLINIC_SECURITY_INSTALLED_SPRITE_COMPONENT_SIZE
                                ),
                                "sprite_sha256": (
                                    CLINIC_SECURITY_INSTALLED_SPRITE_COMPONENT_SHA256
                                ),
                            },
                            "routes": {
                                str(entity): [list(point) for point in route]
                                for entity, route in CLINIC_SECURITY_ROUTES.items()
                            },
                            "hidden_staging_position": list(
                                CLINIC_SECURITY_STAGING_POSITION
                            ),
                            "exterior_reveal_position": list(
                                CLINIC_SECURITY_REVEAL_POSITION
                            ),
                            "entry_delays_frames": {
                                str(entity): delay
                                for entity, delay in (
                                    CLINIC_SECURITY_ENTRY_DELAYS.items()
                                )
                            },
                            "waypoint_max_steps": (
                                CLINIC_SECURITY_WAYPOINT_MAX_STEPS
                            ),
                            "final_facing": (
                                "FE17 actor-to-current-party-leader, then "
                                "four-frame settle"
                            ),
                            "door_sequence": (
                                "open, hidden snap to the exterior threshold, "
                                "scoped actor-local material override, four short "
                                "staggered crossings to deep interior floor, clear "
                                "the override, dynamic Fei facing, close, arrival "
                                "dialogue, fixed battle"
                            ),
                        },
                        "doctor_escape_waypoints": [
                            list(point)
                            for point in CLINIC_DOCTOR_ESCAPE_WAYPOINTS
                        ],
                        "exit_policy": (
                            "doctor insists on bloodwork until victory and remains "
                            "closed while fleeing; doctor approaches, opens, uses a "
                            "bounded actor-local material override to cross outside, "
                            "remains visible while the leaf reverse-closes behind "
                            "him, then hides before stage complete"
                        ),
                    },
                    "player_movement": (
                        "never scripted; control remains live during the one-minute "
                        "wait and every physician walk; dialogue, the short security "
                        "entrance cinematic, and battle lock input"
                    ),
                    "lobby_dialogue_serialization": {
                        "field_local_mutex": INTAKE_DIALOG_BUSY_VARIABLE,
                        "wrapped_native_entities": sorted(
                            INTAKE_NATIVE_DIALOGUE_ACTIONS
                        ),
                        "wrapped_authored_entities": [
                        INTAKE_RECEPTIONIST_ENTITY,
                        INTAKE_CLINIC_DOOR_ENTITY,
                        INTAKE_QUARANTINE_DOOR_ENTITY,
                        INTAKE_PATIENT_DOOR_ENTITY,
                        INTAKE_FREIGHT_DOOR_ENTITY,
                        ],
                        "policy": (
                            "the physician remains visible and Fei remains movable, "
                            "but the automatic alias call yields until any survivor, "
                            "receptionist, office-denial, keycard, or relay-gate "
                            "window closes; FE54 is committed before the actor-dialog "
                            "reset"
                        ),
                    },
                },
                "patient_records": {
                    patient: {
                        "display_name": PATIENT_PROFILE_MEASUREMENTS[patient][0],
                        "age": PATIENT_PROFILE_MEASUREMENTS[patient][1],
                        "sex": PATIENT_PROFILE_MEASUREMENTS[patient][2],
                        "height_cm": PATIENT_PROFILE_MEASUREMENTS[patient][3],
                        "clean_status_weight_hundredths_lb": (
                            PATIENT_RETAIL_INITIAL_WEIGHT_HUNDREDTHS_LB[patient]
                        ),
                        "weight_character_id": PATIENT_CHARACTER_IDS[patient],
                        "weight_dialogue_variables": list(
                            PATIENT_WEIGHT_DIALOG_VARIABLES
                        ),
                        "weight_read_and_convert_opcodes": _read_character_weight_lbs(
                            PATIENT_CHARACTER_IDS[patient],
                        ).hex(" ").upper(),
                        "pulse_bpm": PATIENT_AUTHORED_VITALS[patient][0],
                        "blood_pressure": PATIENT_AUTHORED_VITALS[patient][1],
                        "temperature_c": PATIENT_AUTHORED_VITALS[patient][2],
                        "respiration_per_min": PATIENT_AUTHORED_VITALS[patient][3],
                        "observation": PATIENT_AUTHORED_VITALS[patient][4],
                    }
                    for patient in ("Fei", "Elly", "Citan")
                },
                "weight_policy": (
                    "EX69 reads the selected mutable live Status weight; field "
                    "math converts it with the game's x2.20 convention into "
                    "whole and fractional pound dialogue parameters; the "
                    "campaign never writes weight with EX6B"
                ),
                "repeat_menu": [
                    "Fei",
                    "Elly",
                    "Citan",
                    "Exit",
                ],
            },
            "dialogue_layout": {
                "scope": "Surface-authored and reconstructed blocks only",
                "authored_blocks_audited": sum(
                    len(ids) for ids in CAMPAIGN_AUTHORED_DIALOGUE_IDS.values()
                ),
                "blocks_repaired": sum(
                    len(values)
                    for values in CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS.values()
                ),
                "v178_overwidth_lines_repaired": CAMPAIGN_V178_OVERFLOW_LINE_COUNT,
                "capacity_rule": "declared width OR 1, measured in font units",
                "ordinary_glyph_units": 2,
                "high_code_glyph_units": 3,
                "pagination": "explicit New control at the authored window height",
                "retail_dialogue_policy": "byte-identical outside the audited ID set",
                "intake_waiting_area": {
                    "field": 621,
                    "premise": (
                        "pre-revelation patients believe screening and treatment "
                        "will help them; no ambient adult knows the Soylent truth"
                    ),
                    "adult_dialogues": [
                        {
                            "entity": entity,
                            "dialogue_id": dialogue_id,
                            "text": INTAKE_WAITING_AREA_HOPEFUL_DIALOGUES[
                                dialogue_id
                            ].removesuffix("<Close>"),
                        }
                        for entity, (_action_pc, dialogue_id) in sorted(
                            INTAKE_NATIVE_DIALOGUE_ACTIONS.items()
                        )
                        if entity != INTAKE_BOY_ENTITY
                    ],
                },
                "intake_boy": {
                    "field": 621,
                    "entity": INTAKE_BOY_ENTITY,
                    "dialogue_id": INTAKE_BOY_DIALOGUE_ID,
                    "text": INTAKE_BOY_DIALOGUE.removesuffix("<Close>"),
                },
            },
            "rooms_prepared": [
                {
                    "field": item.spec.identity.scene,
                    "canonical_bundle_id": item.spec.identity.bundle_id,
                    "canonical_graphics_id": item.spec.identity.graphics_id,
                    "bundle_size": len(item.bundle),
                    "bundle_sha256": _sha256(item.bundle),
                    "script_size": len(item.components[SCRIPT_INDEX]),
                    "script_sha256": _sha256(item.components[SCRIPT_INDEX]),
                    "atel_entity_count": ScriptEditor(
                        item.components[SCRIPT_INDEX]
                    ).entity_count,
                    "header_actor_count": struct.unpack_from(
                        "<H", item.header, 0x18C
                    )[0],
                    "role": item.spec.role,
                }
                for item in fields
            ],
            "donors_prepared": [
                {
                    "field": item.identity.scene,
                    "target_ids": [item.identity.bundle_id, item.identity.graphics_id],
                    "bundle_size": len(item.bundle),
                    "bundle_sha256": _sha256(item.bundle),
                    "graphics_size": len(item.graphics),
                    "graphics_sha256": _sha256(item.graphics),
                    "atel_entity_count": ScriptEditor(
                        item.components[SCRIPT_INDEX]
                    ).entity_count,
                    "header_actor_count": struct.unpack_from(
                        "<H", item.header, 0x18C
                    )[0],
                    "role": item.role,
                }
                for item in donors
            ],
            "player_deathblows": {
                "gamestate_canonical_id": (
                    campaign_title.INITIAL_GAMESTATE_CANONICAL_ID
                ),
                "gamestate_size": campaign_title.CAMPAIGN_INITIAL_GAMESTATE_SIZE,
                "gamestate_sha256": (
                    campaign_title.CAMPAIGN_INITIAL_GAMESTATE_SHA256
                ),
                "scope": (
                    "every native on-foot deathblow for all eleven GameState "
                    "forms; Chu-Chu and Maria retain no invented commands"
                ),
                "profiles": [
                    {
                        "character_id": profile.character_id,
                        "character": profile.character,
                        "count": len(profile.command_names),
                        "full_mask": f"0x{profile.full_mask:04X}",
                        "commands": list(profile.command_names),
                    }
                    for profile in deathblows.DEATHBLOW_PROFILES
                ],
                "levels_changed": False,
                "stats_changed": False,
                "level_policy": (
                    "none required: canonical 2607 retains the checked Perfect "
                    "Works level-one deathblow learning tables"
                ),
                "level_resource": {
                    "canonical_id": DEATHBLOW_LEVEL_RESOURCE_CANONICAL_ID,
                    "size": DEATHBLOW_LEVEL_RESOURCE_SIZE,
                    "sha256": DEATHBLOW_LEVEL_RESOURCE_SHA256,
                    "decoded_file0_size": DEATHBLOW_LEVEL_FILE0_SIZE,
                    "decoded_file0_sha256": DEATHBLOW_LEVEL_FILE0_SHA256,
                },
                "fresh_start": (
                    "loaded by canonical 2595 when New Game initializes the route"
                ),
                "existing_save_policy": (
                    "old savestates retain their resident GameState and require "
                    "the separate fail-closed deathblow migration"
                ),
            },
            "title_resources": [
                {
                    "canonical_id": item.canonical_id,
                    "size": len(item.data),
                    "sha256": _sha256(item.data),
                }
                for item in title_resources
            ],
            "replacement_inventory": [
                {
                    "canonical_id": canonical_id,
                    "path": path.resolve().relative_to(output_root.resolve()).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": _sha256(path.read_bytes()),
                }
                for canonical_id, path in replacements
            ],
            "door_animations": [
                {
                    "id": "transfer_intake.transfer",
                    "field": 623,
                    "controller_entity": TRANSFER_NORTH_DOOR_CONTROLLER_ENTITY,
                    "physical_seal_entity": TRANSFER_NORTH_DOOR_SEAL_ENTITY,
                    "destination": [
                        TRANSFER_NORTH_DOOR_ANIMATION.destination_field,
                        TRANSFER_NORTH_DOOR_ANIMATION.destination_parameter,
                    ],
                    "asset": (
                        "byte-identical same-field paired blue leaves already used "
                        "by the reciprocal south threshold"
                    ),
                    "model_indices": list(TRANSFER_NORTH_DOOR_MODEL_INDICES),
                    "source_helper_entities": list(
                        TRANSFER_NORTH_DOOR_SOURCE_HELPER_ENTITIES
                    ),
                    "helper_entities": list(TRANSFER_NORTH_DOOR_HELPER_ENTITIES),
                    "closed_plane": [0, TRANSFER_NORTH_DOOR_CLOSED_PLANE_Z],
                    "header_translation": [
                        0,
                        0,
                        TRANSFER_NORTH_DOOR_ORIGIN_Z,
                    ],
                    "header_rotation": [0, TRANSFER_NORTH_DOOR_ROTATION_Y, 0],
                    "facing_correction": (
                        "half-turn reverses the source south-threshold winding "
                        "for the north-side approach"
                    ),
                    "closed_world_aabbs": [
                        [[-88, 0], [-132, 0], [1259, 1259]],
                        [[0, 88], [-132, 0], [1259, 1259]],
                    ],
                    "slide_per_frame": [[-2, 0], [2, 0]],
                    "frames": TRANSFER_NORTH_DOOR_ANIMATION.frames,
                    "sound_effect_id": TRANSFER_NORTH_DOOR_SOUND_ID,
                    "graphics_or_model_bytes_changed": False,
                },
                *(
                    {
                        "id": f"intake_exam_{index}",
                        "field": 621,
                        "controller_entity": controller,
                        "helper_entity": helper,
                        "physical_seal_entity": None,
                        "destination": [
                            animation.destination_field,
                            animation.destination_parameter,
                        ],
                        "return_parameter": return_parameter,
                        "asset": (
                            "existing field-621 Solaris single-leaf panel model"
                        ),
                        "model_index": placement[0],
                        "header_translation": list(placement[2:5]),
                        "header_rotation": [0, placement[1], 0],
                        "threshold_header_entity": threshold_entity,
                        "threshold_model_index": (
                            INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX
                        ),
                        "threshold_placement": list(threshold_placement),
                        "slide_per_frame": [placement[5], placement[6]],
                        "frames": animation.frames,
                        "sound_effect_id": INTAKE_EXAM_ROOM_SOUND_ID,
                        "closed_barrier": (
                            "the retained outer-wall walkmesh boundary; no "
                            "invisible collision-only seal is required"
                        ),
                        "graphics_or_model_bytes_changed": True,
                    }
                    for (
                        index,
                        controller,
                        helper,
                        threshold_entity,
                        threshold_placement,
                        animation,
                        placement,
                        return_parameter,
                    )
                    in zip(
                        ("a", "b", "c"),
                        INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES,
                        INTAKE_EXAM_ROOM_HELPER_ENTITIES,
                        INTAKE_EXAM_ROOM_THRESHOLD_HEADER_ENTITIES,
                        INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS,
                        INTAKE_EXAM_ROOM_ANIMATIONS,
                        INTAKE_EXAM_ROOM_MODEL_PLACEMENTS,
                        INTAKE_EXAM_ROOM_ENTRY_PARAMETERS,
                        strict=True,
                    )
                ),
            ],
            "door_collision": {
                "blueprint_endpoints_split": len(blueprint.ENDPOINTS),
                "native_surface_endpoints_split": sum(
                    len(items)
                    for items in SURFACE_DOOR_COLLISION_CONTRACTS.values()
                ),
                "donor_blueprint_endpoints_split": sum(
                    1
                    for items in DONOR_DOOR_COLLISION_CONTRACTS.values()
                    for item in items
                    if item.arrival_parameter is not None
                ),
                "field565_internal_gates_split": sum(
                    1
                    for item in DONOR_DOOR_COLLISION_CONTRACTS[565]
                    if item.endpoint_id.startswith("field565.internal_gate_")
                ),
                "field565_sealed_future_handoffs_split": sum(
                    1
                    for item in DONOR_DOOR_COLLISION_CONTRACTS[565]
                    if item.endpoint_id
                    == "field565.future_lab_handoff_sealed"
                ),
                "total_split_thresholds": (
                    len(blueprint.ENDPOINTS)
                    + sum(
                        1
                        for items in DONOR_DOOR_COLLISION_CONTRACTS.values()
                        for item in items
                        if item.arrival_parameter is None
                    )
                ),
                "interaction": (
                    "broad rectangular ghost carrier; no facing cone; remains "
                    "X-selectable at first physical contact"
                ),
                "intake_exam_outer_wall_barriers": {
                    "count": len(INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES),
                    "controller_entities": list(
                        INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES
                    ),
                    "policy": (
                        "the three new exterior panels sit directly on the "
                        "retained Intake walkmesh boundary; that wall blocks "
                        "Fei until the animated X action changes fields"
                    ),
                },
                "native_surface_physical_seal": {
                    "shape": "axis-aligned thin rectangle",
                    "normal_half_extent_script_units": (
                        DOOR_SEAL_NORMAL_HALF_EXTENT
                    ),
                    "normal_half_extent_world_units": (
                        2 * DOOR_SEAL_NORMAL_HALF_EXTENT
                    ),
                    "release": (
                        "remains solid through field unload; all 19 actions "
                        "have no scripted party walk across their panel"
                    ),
                },
                "donor_physical_seal": {
                    "shape": "rotation-invariant circle",
                    "action_disabled": True,
                    "immovable": True,
                    "external_radius_script_units": DONOR_DOOR_SEAL_RADIUS,
                    "external_radius_world_units": 2 * DONOR_DOOR_SEAL_RADIUS,
                    "external_effective_player_contact_radius": (
                        2 * DONOR_DOOR_SEAL_RADIUS + PLAYER_COLLISION_RADIUS
                    ),
                    "external_radius_scope": (
                        "default for donor thresholds except field 549's narrow "
                        "diagonal archive return and field-352 examination rooms "
                        "550, 567, and 591-594; recovered field 590 e4/e6 use the "
                        "wider audited override below"
                    ),
                    "archive_return_override": {
                        "field": 549,
                        "controller_entity": 6,
                        "physical_seal_entity": 16,
                        "shape": "rotation-invariant circle",
                        "center": list(ARCHIVE_RETURN_SEAL_CENTER),
                        "action_center": [
                            DONOR_DOOR_COLLISION_CONTRACTS[549][0].x,
                            DONOR_DOOR_COLLISION_CONTRACTS[549][0].z,
                        ],
                        "radius_script_units": ARCHIVE_RETURN_SEAL_RADIUS,
                        "radius_world_units": 2 * ARCHIVE_RETURN_SEAL_RADIUS,
                        "effective_player_contact_radius": (
                            2 * ARCHIVE_RETURN_SEAL_RADIUS
                            + PLAYER_COLLISION_RADIUS
                        ),
                        "saved_fixed_position": [
                            -12_702_524,
                            0,
                            16_007_409,
                        ],
                        "saved_world_position": [
                            -12_702_524 / 65_536,
                            0.0,
                            16_007_409 / 65_536,
                        ],
                        "saved_triangle": 10,
                        "round_trip_saved_fixed_position": [
                            -13_485_612,
                            0,
                            15_269_605,
                        ],
                        "round_trip_saved_world_position": [
                            -13_485_612 / 65_536,
                            0.0,
                            15_269_605 / 65_536,
                        ],
                        "round_trip_saved_triangle": 10,
                        "round_trip_saved_yaw": 0x0600,
                        "southwest_ray_clearance_world_units": (
                            5.639441995778888
                        ),
                        "closed_cut_triangles": list(
                            DONOR_DOOR_COLLISION_CONTRACTS[549][0].cut_triangles
                        ),
                        "diagonal_seam_intersection_margins_world_units": [
                            12.48625560742041,
                            15.741379398790173,
                        ],
                        "x_button": {
                            "required": True,
                            "automatic_proximity_action": False,
                            "carrier_entity": 6,
                            "script": 2,
                            "action_half_extents_script_units": list(
                                _donor_door_action_bounds(
                                    DONOR_DOOR_COLLISION_CONTRACTS[549][0]
                                )
                            ),
                            "effective_cross_half_extents_world_units": [
                                2 * value + PLAYER_COLLISION_RADIUS
                                for value in _donor_door_action_bounds(
                                    DONOR_DOOR_COLLISION_CONTRACTS[549][0]
                                )
                            ],
                        },
                        "policy": (
                            "the shifted physical circle stays inside the "
                            "unchanged deliberate-X shell, clears the exact "
                            "southwest corridor ray, and intersects both "
                            "diagonal aperture seams while closed; Forward "
                            "alone cannot open it"
                        ),
                    },
                    "exam_room_return_override": {
                        "scenes": list(FIELD352_X_ONLY_SCENES),
                        "shape": "axis-aligned z-normal thin rectangle",
                        "center": list(
                            EXAM_RETURN_RECTANGULAR_SEAL_POSITION
                        ),
                        "half_extents_script_units": list(
                            EXAM_RETURN_RECTANGULAR_SEAL_HALF_EXTENTS
                        ),
                        "physical_collision_extra_radius": 0,
                        "physical_collision_half_extents_world_units": [
                            2 * value
                            for value in (
                                EXAM_RETURN_RECTANGULAR_SEAL_HALF_EXTENTS
                            )
                        ],
                        "contact_planes_z": {
                            "inner": (
                                EXAM_RETURN_RECTANGULAR_SEAL_POSITION[1]
                                - 2
                                * EXAM_RETURN_RECTANGULAR_SEAL_HALF_EXTENTS[1]
                            ),
                            "outer": (
                                EXAM_RETURN_RECTANGULAR_SEAL_POSITION[1]
                                + 2
                                * EXAM_RETURN_RECTANGULAR_SEAL_HALF_EXTENTS[1]
                            ),
                        },
                        "x_button": {
                            "required": True,
                            "automatic_proximity_action": False,
                            "carrier_entity": exam_rooms.RETURN_CONTROLLER,
                            "script": 2,
                            "action_half_extents_script_units": list(
                                _donor_door_action_bounds(
                                    DONOR_DOOR_COLLISION_CONTRACTS[
                                        exam_rooms.SCENES[0]
                                    ][0]
                                )
                            ),
                            "start_scripts_extra_radius": (
                                PLAYER_COLLISION_RADIUS
                            ),
                            "effective_cross_half_extents_world_units": [
                                2 * value + PLAYER_COLLISION_RADIUS
                                for value in _donor_door_action_bounds(
                                    DONOR_DOOR_COLLISION_CONTRACTS[
                                        exam_rooms.SCENES[0]
                                    ][0]
                                )
                            ],
                        },
                        "retired_automatic_cavity": {
                            "owner_entity": EXAM_RETURN_RETIRED_CAVITY_ENTITY,
                            "former_script": EXAM_RETURN_RETIRED_CAVITY_SCRIPT,
                            "span": [
                                f"0x{EXAM_RETURN_RETIRED_CAVITY_PC:04X}",
                                f"0x{EXAM_RETURN_RETIRED_CAVITY_END_PC:04X}",
                            ],
                            "byte_identical_scenes": [550],
                            "side_terminal_carrier_scenes": list(
                                FIELD352_SIDE_TERMINAL_SCENES
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
                                "pc": (
                                    f"0x{empty_clinic567.SHARED_STOP_PC:04X}"
                                ),
                            },
                        },
                        "retail_walkmesh": {
                            "source_field": empty_clinic567.SOURCE_SCENE,
                            "component_index": 1,
                            "byte_identical": True,
                            "size": (
                                empty_clinic567.SOURCE_COMPONENT_IDENTITIES[1][0]
                            ),
                            "sha256": (
                                empty_clinic567.SOURCE_COMPONENT_IDENTITIES[1][1]
                            ),
                        },
                    },
                    "recovered_ward_wide_controller_entities": [
                        donor567.LOBBY_CONTROLLER,
                        donor567.RESTRICTED_CONTROLLER,
                    ],
                    "recovered_ward_wide_radius_script_units": 0x1C,
                    "recovered_ward_wide_radius_world_units": 2 * 0x1C,
                    "recovered_ward_wide_effective_player_contact_radius": (
                        2 * 0x1C + PLAYER_COLLISION_RADIUS
                    ),
                    "field565_outer_action_half_extent_script_units": (
                        FIELD565_OUTER_DOOR_ACTION_HALF_EXTENT
                    ),
                    "recovered_ward_action_half_extent_script_units": (
                        stabilization590.ACTION_HALF_EXTENT
                    ),
                    "internal_gate_radius_script_units": (
                        DONOR_INTERNAL_GATE_SEAL_RADIUS
                    ),
                    "internal_gate_radius_world_units": (
                        2 * DONOR_INTERNAL_GATE_SEAL_RADIUS
                    ),
                    "internal_gate_effective_player_contact_radius": (
                        2 * DONOR_INTERNAL_GATE_SEAL_RADIUS
                        + PLAYER_COLLISION_RADIUS
                    ),
                    "release": (
                        "success-only entity-script-4 ghost call after native "
                        "leaf animation and before scripted party motion; "
                        "field-565 e11/e12 failures retain their seals"
                    ),
                },
            },
            "preservation": {
                "graphics": (
                    "external graphics files remain byte-identical; logical field "
                    "550 uses the complete Disc 1 field-352 archive; logical "
                    "field 567 independently reuses that same intact field-352 "
                    "medical archive without the office encounter assets; logical "
                    "fields 591-594 independently reuse that same intact bright "
                    "clinical-room archive; logical "
                    "field 590 preserves the complete Disc 1 field-567 clinical "
                    "ward archive; logical field 588 preserves Disc 1 field 550's "
                    "bright Soylent diagnostic-scanner archive; field 621 "
                    "replaces only local actor/sprite bank 6 with that office's "
                    "exact physician bank"
                ),
                "walkmeshes": (
                    "byte-identical within each retained source; fields 550 and "
                    "567 and the four clinical rooms 591-594 use field "
                    "352's intact infirmary walkmesh, while field 590 uses field "
                    "567's intact Krelian Lab walkmesh and field 588 uses field "
                    "550's compact diagnostic-room walkmesh"
                ),
                "models": (
                    "byte-identical within each retained source; every retained "
                    "actor record remains byte-identical and in original order; "
                    "fields 567 and 591-594 preserve the complete static "
                    "examination bed, and each of 591-594 keeps the illuminated "
                    "medical workstation; "
                    "field 590 preserves all recovered ward models; field 588 "
                    "preserves the six-model baked diagnostic scanner shell"
                ),
                "encounters": (
                    "random encounters remain disabled; field 550 zeroes every "
                    "weight and replaces only unused slot 15 with a fixed, no-Escape "
                    "Solaris Guard/Security Cube formation from field 551; field "
                    "567 zeroes every weight without replacing any formation"
                    "; fields 591-594 independently retain that same zero-weight "
                    "clinic encounter table; recovered field 590 retains its "
                    "zero-weight encounter table"
                ),
                "new_actor_records": (
                    "field 623 adds two model-backed instances of its existing "
                    "models 10/11; field 621 adds three model-less door controls "
                    "and three helpers backed by its existing door models; fields "
                    "591-594 each add one model-less terminal carrier; remaining "
                    "additions are model-less consoles or separate collision-only "
                    "seals; field 588 reuses e7 over "
                    "its baked visible workstation and donor door X targets reuse "
                    "their authentic controller entities"
                ),
                "field_changes": (
                    f"{len(blueprint.ENDPOINTS)} reciprocal blueprint endpoints "
                    "remain deliberate physical X routes; field 620 e24 "
                    "commits diagnostic clearance before its native continuation, "
                    "and every examination-room return requires a deliberate "
                    "X press on e17:s2's native leaf/action path; no coordinate "
                    "or proximity worker opens those doors"
                ),
            },
            "materialization": {
                "foundation_format": base_manifest.get("format"),
                "native_field_jobs": len(base_manifest.get("jobs", ())),
                "donor_field_jobs": len(base_manifest.get("donor_jobs", ())),
                "title_resources": len(title_resources),
                "replacement_resources": len(replacements),
                "semantic_authority": (
                    "This campaign manifest supersedes the temporary v173 "
                    "materializer manifest. Rooms, doors, state, gates, and "
                    "the active Quarantine completion action above "
                    "describe the final build; reciprocal blueprint pairs "
                    "describe the active campaign topology."
                ),
            },
        }
    )
    manifest_path.write_text(
        json.dumps(campaign, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_campaign(
    source_disc: Path | str,
    donor_disc: Path | str,
    output_root: Path | str,
    *,
    force: bool = False,
    one_hit_kills: bool = False,
) -> tuple[
    tuple[base.PreparedField, ...],
    tuple[base.PreparedDonorField, ...],
    tuple[tuple[int, Path], ...],
]:
    if type(one_hit_kills) is not bool:
        raise SurfaceCampaignBuildError("one_hit_kills must be a boolean")
    fields, donors, title_resources = prepare_campaign(source_disc, donor_disc)
    playtest_resources = ()
    playtest = {"one_hit_kills": False}
    if one_hit_kills:
        from modules.soylent_system.tools.surface_soylent_playtest import prepare_one_hit_resources
        playtest_resources, playtest = prepare_one_hit_resources(source_disc)
    replacements = base.materialize(
        fields,
        output_root,
        source_disc,
        donor_fields=donors,
        donor_disc=donor_disc,
        title_resources=title_resources,
        complete_dungeon=True,
        force=force,
    )
    # Test combat is an explicit standalone build option. Keep it outside the
    # normal preparation/composition API and outside title/party resources.
    emitted = list(replacements)
    used_ids = {canonical_id for canonical_id, _ in emitted}
    for resource in playtest_resources:
        if resource.canonical_id in used_ids:
            raise SurfaceCampaignBuildError("Playtest resource overlaps campaign replacement")
        used_ids.add(resource.canonical_id)
        path = Path(output_root).resolve() / "replacements" / resource.filename
        path.write_bytes(resource.data)
        emitted.append((resource.canonical_id, path))
    replacements = tuple(emitted)
    _write_campaign_manifest(
        Path(output_root).resolve(),
        source_disc=source_disc,
        donor_disc=donor_disc,
        fields=fields,
        donors=donors,
        title_resources=title_resources,
        replacements=replacements,
        playtest=playtest,
    )
    return fields, donors, replacements


PLAYTEST_OPTIONS_PATH = Path(__file__).resolve().parent / "content" / "playtest.json"


def load_playtest_options(path: Path | str = PLAYTEST_OPTIONS_PATH) -> bool:
    """Read the source-tracked standalone test setting, rejecting typos."""
    options = json.loads(Path(path).read_text(encoding="utf-8"))
    if (not isinstance(options, dict)
            or set(options) != {"format", "one_hit_kills"}
            or options.get("format") != "soylent-playtest-options-v1"
            or type(options.get("one_hit_kills")) is not bool):
        raise SurfaceCampaignBuildError("Invalid Soylent playtest options")
    return options["one_hit_kills"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-disc", type=Path, required=True)
    parser.add_argument("--donor-disc", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--build-disc", action="store_true")
    parser.add_argument("--xenoiso", type=Path)
    parser.add_argument("--disc-output", type=Path)
    parser.add_argument(
        "--one-hit-kills", action=argparse.BooleanOptionalAction, default=None,
        help="Override content/playtest.json for standalone enemy-HP testing",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.build_disc and not all((args.xenoiso, args.disc_output)):
        parser.error("--build-disc requires --xenoiso and --disc-output")
    if not args.build_disc and any((args.xenoiso, args.disc_output)):
        parser.error("--xenoiso and --disc-output require --build-disc")
    try:
        one_hit_kills = (load_playtest_options() if args.one_hit_kills is None
                        else args.one_hit_kills)
        fields, donors, replacements = build_campaign(
            args.source_disc,
            args.donor_disc,
            args.output,
            force=args.force,
            one_hit_kills=one_hit_kills,
        )
        print(
            "Prepared cohesive Surface Soylent rooms: "
            + ", ".join(
                str(item.spec.identity.scene) for item in fields
            )
            + ", "
            + ", ".join(str(item.identity.scene) for item in donors)
        )
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
                raise SurfaceCampaignBuildError(
                    f"Xenoiso wrapper exited with code {completed.returncode}"
                )
            boot = verify_retail_title_boot(args.disc_output)
            print(
                f"Verified native publisher/title boot at raw LBA {boot.lba}: "
                f"{boot.sha256}"
            )
    except (
        OSError,
        ValueError,
        GrayboxBuildError,
        base.SurfaceSoylentBuildError,
    ) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
