#!/usr/bin/env python3
"""Build the two-disc ``Rico: Emotion and Resolve`` chapter anthology.

Disc 1 is rebuilt with Xenoiso's ``cd1`` mode, while Disc 2 uses ``cd2fix`` to
map canonical IDs onto its five-entry-shorter physical FAT.  Each output uses
its own audited empty field range, receives a native New Game route to an
in-field chapter hub, and contains all seven chapters so no live disc swap is
needed.  The generated M3U remains the single portable launch target for the
paired images.

This tool never edits either source BIN.  It accepts only the checked USA
retail images, prepares ordinary replacement files, and asks the guarded
Xenoiso wrapper to create new outputs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.tools.xgdeathblows import grant_all_on_foot_deathblows
from shared.tools import atel_primitives as atel
from shared.tools.xgdialog import (
    CHARACTER_IDS,
    PLAIN_ENCODE,
    DialogueBlockSpec,
    encode_dialogue,
    encode_text,
    parse_dialogue,
)
from shared.tools.xgdisc import Mode2Image
from shared.tools.xgencounter import (
    EMPTY_ENEMY_ID,
    ENCOUNTER_COMPONENT_SIZE,
    FORMATION_COUNT,
    FORMATION_SIZE,
    WEIGHTS_OFFSET,
    EncounterTable,
)
from shared.tools.xgfield import build_field_preserving, parse_field
from modules.rico.tools.xgrico_balance import (
    RICO_ID,
    YOUNG_RICO_ID,
    apply_initial_character_balance,
    apply_young_rico_anthology_profile,
    patch_battle_weight_resource,
    patch_memento_system_data,
    patch_young_rico_equipment_names,
    patch_weight_mutation_overlay,
)
from modules.rico.tools.xgrico_native_title import (
    TITLE_GRAPHICS_CANONICAL_ID,
    TITLE_MENU_CANONICAL_ID,
    build_rico_native_title_menu,
    patch_rico_native_title_graphics,
    patch_rico_native_title_overlay,
)
from shared.tools.xgscript import AtelScript
import modules.mass_driver.build as mass_driver
from modules.soylent_system.base import (
    _patch_donor_party,
    _point_inside_triangle,
    _walkmesh_layer,
)


CONTENT_ROOT = ROOT / "modules" / "rico" / "content"
STORY_MANIFEST = CONTENT_ROOT / "manifest.json"
YOUNG_RICO_PORTRAIT_TIM = CONTENT_ROOT / "assets" / "young_rico_menu_portrait.tim"
NORMALIZED_GAMESTATE = ROOT / "work" / "standalone_bootstrap" / "2595.bin"
XENOISO_WRAPPER = ROOT / "shared" / "tools" / "xenoiso_build.py"

DISC_IDENTITIES = {
    1: (
        718_738_272,
        "39c547a9afc6da15d847ef81a2c6cea1a6516bdfa562cf13b0999b04e8598bda",
    ),
    2: (
        688_700_880,
        "5eab85c683d4d7087d345b587472db9c44df29b35ce66553c2626d26018b947e",
    ),
}

TITLE_FIELD_ID = 490
TITLE_FIELD_CANONICAL_ID = 1586
TITLE_FIELD_SIZE = 4336
TITLE_FIELD_SHA256 = (
    "8086ef838b330ef7d8385a44d45352ba9017eeaab0db34ef6f9b23d39c085ba8"
)
TITLE_RESULT_BRANCH_PC = 0x00B0
TITLE_RESULT_BRANCH = bytes.fromhex("02 46 00 00 00 40 E7 00")
TITLE_ROUTE_FALLTHROUGH_PC = 0x00B8
TITLE_ROUTE_FALLTHROUGH = bytes.fromhex("02 02 04 00 00 40 CF 00")

TITLE_OVERLAY_CANONICAL_ID = 2599
MAIN_MENU_OVERLAY_CANONICAL_ID = 2597
WEIGHT_MUTATION_OVERLAY_CANONICAL_IDS = (2597, 2599, 2603)
TITLE_OVERLAY_SIZE = 153_864
TITLE_OVERLAY_SHA256 = (
    "82f84a24ac1fd1979754e1cc9c861405fb59ce95dd78db00a76f00c8f1bd177d"
)
TITLE_EXPECTED_DISC_OFFSET = 0x13B8
TITLE_EXPECT_DISC_1 = bytes.fromhex("21 20 00 00")
TITLE_EXPECT_DISC_2 = bytes.fromhex("01 00 04 34")

INITIAL_GAMESTATE_CANONICAL_ID = 2595
BATTLE_OVERLAY_CANONICAL_ID = 38
SYSTEM_DATA_CANONICAL_ID = 2594
SYSTEM_NAMES_CANONICAL_ID = 29
GAMESTATE_SIZE = 0x2358
NORMALIZED_GAMESTATE_SHA256 = (
    "c90f343a1cceccf9e9a8d3cb68079856ac8e63efad0d99a1f5655a4d45fa4375"
)
NAME_REGION_SIZE = 31 * 20
PARTY_RECORD_BASE = 0x26C
PARTY_RECORD_SIZE = 0xA4
PARTY_LEVEL_OFFSETS = (0x62, 0x63)

FIELD_BUNDLE_BASE = 606
SCRIPT_INDEX = 5
DIALOGUE_INDEX = 7
PAD_MASK_CROSS = 0x0020
PAD_MASK_CIRCLE = 0x0040
MENU_SELECTION_VARIABLE = 0x0014

# Field 229's young-Rico local sprite is an NPC animation bank.  Its animation
# 3 never raises the completion callback that the player jump state waits for,
# so an ordinary jump press can leave Rico grounded with flag 0x0800 set and
# movement speed permanently zero.  Run the normal player update first, then
# clear only that unsupported jump flag before the movement phase.  Animation
# 2 is separately aliased to the bank's walk program below, making Circle have
# no locomotion effect instead of dispatching the missing run program.
YOUNG_RICO_PARTY_UPDATE = b"\xA7\xF8\x04\x00\x08\x00"
YOUNG_RICO_ACTOR_COMPONENT_SHA256 = (
    "e6e3a8e4230e3aad533572d545eff80fffe78b9adb2247263d754f46fe2357e9"
)
YOUNG_RICO_PLAYER_ACTOR_COMPONENT_SHA256 = (
    "4364297ce0749c0e4173d4e899c7debcfc0ab4cc0023fe7ac5fb5746b700e5d2"
)
YOUNG_RICO_ACTOR_BANK_INDEX = 1
YOUNG_RICO_ACTOR_BANK_SHA256 = (
    "041ba5fb6be84e6e80dd30c51f0a57566b93fd34b84c8fb2e6ea578b0ff92caa"
)
YOUNG_RICO_PLAYER_ACTOR_BANK_SHA256 = (
    "a7707314eb769cdfa357a2c1af7f26a149439b7cd34f9f40f55595f65c22ff83"
)
YOUNG_RICO_SPRITE_COMPONENT_SIZE = 23_716
YOUNG_RICO_SPRITE_COMPONENT_SHA256 = (
    "933cd7bd1ad9c6e8034a5b57a204d010d50314ad3a2c8c02ec55ae96204e7177"
)
YOUNG_RICO_SPRITE_BANK_SIZE = 9_612
YOUNG_RICO_SPRITE_BANK_SHA256 = (
    "f7bbcd75bfbb203febc55de313b19f8d72fda32508e12bdce33e9fea83e9633c"
)
YOUNG_RICO_ANIMATION_HEADER_OFFSET = 0x0AB4
YOUNG_RICO_NPC_ANIMATION_HEADER = bytes.fromhex(
    "02 00 08 00 1C 00 00 00"
)
YOUNG_RICO_PLAYER_ANIMATION_HEADER = bytes.fromhex(
    "03 00 08 00 1C 00 1C 00"
)

# Retail field 229 is a cutscene room: its closed front door is visual only,
# and the retail director never yields control while Rico could approach it.
# Layer-0 triangles 78/79 therefore extend roughly 104 units behind model 17's
# closed leaf.  The authored threshold between interior triangle 59 and that
# pocket is about 28 units inside the leaf, leaving suitable clearance for
# Rico's 16-unit actor radius.  Treat that reciprocal neighbor seam as a wall;
# this preserves every vertex, triangle, material, objective, and visible prop.
CHAPTER_ONE_WALKMESH_SIZE = 2_824
CHAPTER_ONE_WALKMESH_SHA256 = (
    "17f74d55935c4ebd8d9690bd9ee17395a0d50b9f65b9c5b5e4516ae919851c58"
)
CHAPTER_ONE_SEALED_WALKMESH_SHA256 = (
    "ebe47fde109410278b91bdc600bac099658f3ec5697e94fe461e1fc8ab1c1cc1"
)
CHAPTER_ONE_WALKMESH_TRIANGLE_OFFSET = 0x28
CHAPTER_ONE_WALKMESH_VERTEX_OFFSET = 0x4EC
CHAPTER_ONE_DOOR_THRESHOLD_EDGE = ((51, 95), (90, 57))
CHAPTER_ONE_DOOR_NEIGHBOR_LINKS = ((59, 1, 79), (79, 1, 59))
CHAPTER_ONE_DOOR_EXTERIOR_TRIANGLES = frozenset((78, 79))
CHAPTER_ONE_DOOR_REPRO_POSITION = (
    149.7455291748047,
    139.11358642578125,
)
CHAPTER_ONE_ANNA_ENTITY = 4
CHAPTER_ONE_ANNA_INIT_PC = 0x0182
CHAPTER_ONE_ANNA_UPDATE_PC = 0x018F
CHAPTER_ONE_ANNA_HEADER_RECORD = bytes.fromhex(
    "E0 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
)
CHAPTER_ONE_ANNA_SOURCE_INIT = bytes.fromhex(
    "0B 00 80 19 84 FF CB 00 C0 5F 04 2A 00"
)
CHAPTER_ONE_ANNA_SOURCE_UPDATE = b"\x00"
CHAPTER_ONE_ANNA_ACTOR_BANK_SIZE = 2_708
CHAPTER_ONE_ANNA_ACTOR_BANK_SHA256 = (
    "0da7d9832202b636c29358955c19c5e0a63746240d428fe84c814a4c742467d8"
)
CHAPTER_ONE_ANNA_SPRITE_BANK_SIZE = 14_092
CHAPTER_ONE_ANNA_SPRITE_BANK_SHA256 = (
    "074fbae2905b92a019df8046f389fd93bbbcd8d143b9def90d84f8af4dc654e0"
)
# Field 229's retail cutscene stages Anne standing at the bright wall window.
# For the playable reconstruction, keep her untouched native standing artwork
# on the flat floor just beyond the bed's foot.  Keep the visible actor solid so
# Rico cannot overlap her; a model-less controller at the same point owns dialogue.
CHAPTER_ONE_ANNA_VISUAL_POSITION = (35, -140, 75)
CHAPTER_ONE_ANNA_INTERACTION_POSITION = CHAPTER_ONE_ANNA_VISUAL_POSITION
# Node 13/model 6's audited, yaw-transformed conservative world footprint.
CHAPTER_ONE_BED_WORLD_FOOTPRINT = (31, 187, -312, -155)
# Model 0 primitive 43 is the bright pane above the bed that the player reads
# as this scene's window.  Its checked node-7 transform puts the pane here.
CHAPTER_ONE_WINDOW_PANE_WORLD_CENTER = (218, -218)
# The same model's two broad, unobstructed windows are primitive pairs 38/39
# and 40/41.  Their node-7 yaw puts both glass planes behind the diagonal floor
# boundary.  Aim each carrier at the pane while validating through a strict,
# reachable interior anchor.  The second carrier sits at the clear end of its
# pane: a centered target would overlap Anne's forgiving bedside action box.
CHAPTER_ONE_SETTLEMENT_WINDOW_POSITION = (-225, 35, 66)
CHAPTER_ONE_SETTLEMENT_WINDOW_INTERACTION_HALF_WIDTH = 0x04
CHAPTER_ONE_SETTLEMENT_WINDOW_INTERACTION_HALF_DEPTH = 0x04
CHAPTER_ONE_SETTLEMENT_WINDOW_WALKMESH_ANCHOR = (-201, 59)
CHAPTER_ONE_GATE_WINDOW_POSITION = (-39, -151, 74)
CHAPTER_ONE_GATE_WINDOW_INTERACTION_HALF_WIDTH = 0x04
CHAPTER_ONE_GATE_WINDOW_INTERACTION_HALF_DEPTH = 0x04
CHAPTER_ONE_GATE_WINDOW_WALKMESH_ANCHOR = (-15, -127)
CHAPTER_ONE_ANNA_PLAYABLE_INIT = bytes.fromhex(
    "0B 00 80 19 23 00 74 FF C0 5F 03 2A 00"
)
# Retail Anne scripts 9 and 12 pair animation 2 with her cough dialogue.  That
# animation's native sprite program loops, so PLAY_ANIMATION_EX plus
# WAIT_ANIMATION_END is required to play exactly one cough and restore idle.
CHAPTER_ONE_ANNA_COUGH_ANIMATION = 2
CHAPTER_ONE_ANNA_COUGH_INTERVAL_FRAMES = 900
CHAPTER_ONE_ANNA_COUGH_ONCE = bytes(
    (0x5D, CHAPTER_ONE_ANNA_COUGH_ANIMATION, 0x5E)
)
CHAPTER_ONE_ANNA_INTERACTION_COUGH_SCRIPT = 31
CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL = bytes(
    (
        0x09,
        CHAPTER_ONE_ANNA_ENTITY,
        CHAPTER_ONE_ANNA_INTERACTION_COUGH_SCRIPT | 0x20,
    )
)
CHAPTER_ONE_ANNA_INTERACTION_HALF_WIDTH = 0x10
CHAPTER_ONE_ANNA_INTERACTION_HALF_DEPTH = 0x0C
# RAC12 Slot 1 proves this exact stance is at model 6's bed.  It was inside the
# mislabelled window carrier, which is why Cross displayed window dialogue.
CHAPTER_ONE_SLOT_ONE_BED_REPRO_POSITION = (
    165.65040588378906,
    -180.13084411621094,
)
# RAC21 proved that the historical (-124,+203) carrier belonged to model 0's
# opposite pane.  RAC27 Slot 1 then pinned a subtler failure at the intended
# pane: Rico was touching its right-hand frontage and inside the action box,
# but aiming at the floor-side carrier produced a native facing gap of 0x032E,
# beyond Noah's 700-unit cone.  Aim this model-less carrier through the wall at
# primitive 43 instead.  Its small rectangle collects presses across the
# reachable frontage; script 2 then trims every axis-aligned corner away from
# the diagonal frame with Rico's live normal/tangent coordinates.
# The third value is the associated contact-floor triangle; the invisible aim
# point itself is intentionally behind that triangle's wall edge.
CHAPTER_ONE_WINDOW_POSITION = (198, -208, 25)
CHAPTER_ONE_WINDOW_INTERACTION_HALF_WIDTH = 0x04
CHAPTER_ONE_WINDOW_INTERACTION_HALF_DEPTH = 0x02
CHAPTER_ONE_WINDOW_LIVE_REPRO_POSITION = (
    191.968,
    -189.894,
)
# RAC27 Slot 1 (size 1,674,463; SHA-256 B529F366...AC72A9B74) is the
# right-side frame stance reported by the player.  The fixed-point position is
# preserved as evidence; the engine floors it before its integer ratan2 test.
CHAPTER_ONE_WINDOW_SLOT_ONE_EDGE_REPRO_POSITION = (
    186.17092895507812,
    -196.13218688964844,
)
CHAPTER_ONE_WINDOW_SLOT_ONE_EDGE_ENGINE_POSITION = (186, -197)
CHAPTER_ONE_WINDOW_SLOT_ONE_EDGE_YAW = 0x0200
# The 2026-08-30 Slot 1 report captures Rico at the other reachable portion of
# the same frame.  Cross reaches this controller, but the fixed-point position
# floors to normal 377, one unit below the former scripted cutoff.  Preserve
# this exact stance as a regression without enlarging the native action box.
CHAPTER_ONE_WINDOW_SLOT_ONE_LEFT_EDGE_REPRO_POSITION = (
    181.175537109375,
    -195.9246826171875,
)
CHAPTER_ONE_WINDOW_SLOT_ONE_LEFT_EDGE_ENGINE_POSITION = (181, -196)
# The next clean-build Slot 1 (1,667,958 bytes, SHA-256 12DDF718...5526700)
# captured another collision-limited stance farther along the same glass.  Its
# fixed-point normal is 375.802, but per-axis flooring produces normal 376.
# Leave one unit of subpixel headroom so every equivalent frame contact works.
CHAPTER_ONE_WINDOW_SLOT_ONE_LOWER_EDGE_REPRO_POSITION = (
    179.509765625,
    -196.2923583984375,
)
CHAPTER_ONE_WINDOW_SLOT_ONE_LOWER_EDGE_ENGINE_POSITION = (179, -197)
CHAPTER_ONE_WINDOW_CONTACT_TRIANGLES = (17, 25, 83, 84)
CHAPTER_ONE_WINDOW_CONTACT_NORMAL_MIN = 375
CHAPTER_ONE_WINDOW_CONTACT_TANGENT_RANGE = (-30, 3)
# Three otherwise-unused top-of-bank field words hold the leader coordinates
# and one derived normal/tangent value during the window's script-2 check.
CHAPTER_ONE_WINDOW_POSITION_X_VARIABLE = 0x07F8
CHAPTER_ONE_WINDOW_POSITION_Z_VARIABLE = 0x07FA
CHAPTER_ONE_WINDOW_POSITION_SCRATCH_VARIABLE = 0x07FC
# These read-only live captures are visibly away from the glass.  RAC22's
# 0x18 operands wrongly accepted both; the tight pane-front volume must not.
CHAPTER_ONE_WINDOW_TOO_FAR_REPRO_POSITIONS = (
    (132, -148),
    (151.290390, -164.898102),
)
CHAPTER_ONE_MISLABELLED_BED_REPRO_POSITION = (
    182.83290100097656,
    -201.90713500976562,
)
# Field 229's node 15/model 8 is the low desk beneath node 8/model 1's two
# books.  RAC33 Slot 1 captures Rico at (201.49,-59.05), triangle 51, facing
# the desk's diagonal room-side edge.  The visible books themselves are above
# non-walkable furniture, so aim this model-less carrier at that edge and pin
# its reachable floor point separately.  OP18 doubles the 6/6 operands and
# Rico contributes a 16-unit radius, yielding a precise 28-unit frontage.
# The 2026-09-03 Slot 1 report independently captures the neighboring floor
# triangle at (200.71,-56.87), still facing the books and exactly on the
# effective Z edge.  Preserve both stances as regression evidence.
CHAPTER_ONE_READING_DESK_POSITION = (226, -85, 51)
CHAPTER_ONE_READING_DESK_INTERACTION_HALF_WIDTH = 0x06
CHAPTER_ONE_READING_DESK_INTERACTION_HALF_DEPTH = 0x06
CHAPTER_ONE_READING_DESK_SLOT_ONE_REPRO_POSITION = (
    201.48570251464844,
    -59.0458984375,
)
CHAPTER_ONE_READING_DESK_SLOT_ONE_ENGINE_POSITION = (201, -60)
CHAPTER_ONE_READING_DESK_SLOT_ONE_YAW = 0x0200
CHAPTER_ONE_READING_DESK_CURRENT_SLOT_ONE_REPRO_POSITION = (
    200.7132110595703,
    -56.86717224121094,
)
CHAPTER_ONE_READING_DESK_CURRENT_SLOT_ONE_ENGINE_POSITION = (200, -57)
CHAPTER_ONE_READING_DESK_CURRENT_SLOT_ONE_TRIANGLE = 54
CHAPTER_ONE_READING_DESK_CURRENT_SLOT_ONE_YAW = 0x0200
# The Emerald Traveler replaces a six-window exchange with one narration.
# Retain the removed five show/wait pairs as unreachable tail allocation so
# every later controller keeps its bytecode address.  This makes the player's
# already-resident Slot 1 safely migratable without rewriting live actor PCs.
CHAPTER_ONE_READING_DESK_ACTION_LAYOUT_PADDING = 40
# Field 229's node 23/model 16 is the long green cooking counter beneath the
# window.  Its complete reachable frontage is triangle 27's unlinked diagonal
# edge from (-160,173) to (-93,240).  RAC34 Slot 1 captures Rico at the
# northeast end, (-95.83,232.98), while the player's requested move to the
# left follows that same edge.  Center a no-facing carrier on walkable t27:
# Noah's doubled 10/10 operands plus Rico's 16-unit radius make a 36-by-36
# coarse box, covering the entire frontage.  Script 2 then trims its broad
# room-side corners to the actual diagonal contact strip.  The water-bucket
# box ends at Z=164; this one begins at Z=169, leaving a deliberate five-unit
# dead gap so the two objects cannot steal Cross.
CHAPTER_ONE_COOKING_COUNTER_POSITION = (-124, 205, 27)
CHAPTER_ONE_COOKING_COUNTER_INTERACTION_HALF_WIDTH = 0x0A
CHAPTER_ONE_COOKING_COUNTER_INTERACTION_HALF_DEPTH = 0x0A
CHAPTER_ONE_COOKING_COUNTER_FRONTAGE_EDGE = ((-160, 173), (-93, 240))
CHAPTER_ONE_COOKING_COUNTER_SLOT_ONE_REPRO_POSITION = (
    -95.83183288574219,
    232.98023986816406,
)
CHAPTER_ONE_COOKING_COUNTER_SLOT_ONE_ENGINE_POSITION = (-96, 232)
CHAPTER_ONE_COOKING_COUNTER_SLOT_ONE_YAW = 0x0A00
# The 2026-09-02 Slot 1 report (1,673,608 bytes, SHA-256 D8B1A6EF...A8)
# captures Rico at the central cooktop, where the counter collision holds his
# center at (-114.705,202.006).  Per-axis flooring gives (-115,202), whose
# diagonal normal Z-X is 317.  That is a legitimate 16-unit-radius contact,
# not one of the coarse box's remote corners.  Keep one additional unit of
# headroom for either signed flooring or truncation while the actor settles.
CHAPTER_ONE_COOKING_STOVE_SLOT_ONE_REPRO_POSITION = (
    -114.70513916015625,
    202.0063934326172,
)
CHAPTER_ONE_COOKING_STOVE_SLOT_ONE_ENGINE_POSITION = (-115, 202)
CHAPTER_ONE_COOKING_STOVE_SLOT_ONE_YAW = 0x0A00
CHAPTER_ONE_COOKING_COUNTER_CONTACT_NORMAL_RANGE = (316, 333)
CHAPTER_ONE_COOKING_COUNTER_CONTACT_TANGENT_RANGE = (13, 147)
CHAPTER_ONE_COOKING_COUNTER_POSITION_X_VARIABLE = (
    CHAPTER_ONE_WINDOW_POSITION_X_VARIABLE
)
CHAPTER_ONE_COOKING_COUNTER_POSITION_Z_VARIABLE = (
    CHAPTER_ONE_WINDOW_POSITION_Z_VARIABLE
)
CHAPTER_ONE_COOKING_COUNTER_POSITION_SCRATCH_VARIABLE = (
    CHAPTER_ONE_WINDOW_POSITION_SCRATCH_VARIABLE
)
# Field 229's two visible gray water buckets are model 13 at static nodes 20
# and 24, with world footprints X[-223,-196]/Z[181,208] and
# X[-252,-225]/Z[151,178].  Their meshes lie beyond triangle 64's diagonal
# floor boundary.  RAC31 Slot 1 captures the natural right-bucket contact at
# (-168.17,157.55); the old carrier at (-196,132) missed it on both axes.
# Center this no-facing frontage on reachable t64 and span the two adjacent
# bucket faces.  Its effective X/Z half-box is 34/24 after Noah doubles OP18
# and adds Rico's 16-unit radius.  The resulting box remains six units clear
# of the stonebell-vase action along Z instead of stealing that interaction.
CHAPTER_ONE_WATER_BUCKET_POSITION = (-190, 140, 64)
CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_WIDTH = 0x09
CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_DEPTH = 0x04
CHAPTER_ONE_WATER_BUCKET_SLOT_ONE_REPRO_POSITION = (
    -168.16722106933594,
    157.54751586914062,
)
CHAPTER_ONE_WATER_BUCKET_SLOT_ONE_ENGINE_POSITION = (-169, 157)
# The central cylindrical heater is model 12 at static node 19, footprint
# X[-40,18]/Z[-18,40].  Its mesh is not walkable, so aim the invisible carrier
# at the visible front-center (-11,-18) and validate it through a reachable
# floor anchor, just as the recessed window is validated.  RAC30 Slot 1 caught
# Rico at the right-front contact point (5.21,-40.34), triangle 45, yaw 0xC00.
# A 30-by-24 effective half-box follows the heater's visible width and reaches
# that exact contact point without spilling farther into the room.  Facing plus
# the safe-default choice prevents a passing Cross press from completing it.
CHAPTER_ONE_HEATER_POSITION = (-11, -18, 45)
CHAPTER_ONE_HEATER_INTERACTION_HALF_WIDTH = 0x07
CHAPTER_ONE_HEATER_INTERACTION_HALF_DEPTH = 0x04
CHAPTER_ONE_HEATER_SLOT_ONE_REPRO_POSITION = (
    5.2100067138671875,
    -40.34001159667969,
)
CHAPTER_ONE_HEATER_SLOT_ONE_ENGINE_POSITION = (5, -41)
CHAPTER_ONE_HEATER_SLOT_ONE_YAW = 0x0C00
CHAPTER_ONE_HEATER_INTERACTION_STANCE = (
    *CHAPTER_ONE_HEATER_SLOT_ONE_ENGINE_POSITION,
    45,
)
# The rusty orange vase is field-229 node 11/model 4 and its flowers are node 18/
# model 11.  RAC25 Slot 1 captures Rico at (-234.58,91.65) facing the visible
# arrangement.  Its own tiny no-facing target is strictly inside t66 and has a
# six-unit effective Z gap from the corrected bucket frontage.
CHAPTER_ONE_FLOWER_VASE_POSITION = (-235, 90, 66)
CHAPTER_ONE_FLOWER_VASE_INTERACTION_HALF_WIDTH = 0x02
CHAPTER_ONE_FLOWER_VASE_INTERACTION_HALF_DEPTH = 0x02
CHAPTER_ONE_FLOWER_VASE_SLOT_ONE_REPRO_POSITION = (-234.580, 91.650)
# Model 17's visible diagonal leaf spans approximately (120,66)..(66,120),
# while the reachable interior threshold is the t59/t79 edge (51,95)..(90,57).
# Center the no-facing carrier on that complete frontage.  OP18 doubles these
# operands and action selection adds Rico's 16-unit radius, so 6/6 supplies an
# effective 28-unit half-box that contains both threshold endpoints.
CHAPTER_ONE_EXIT_POSITION = (70, 76, 59)
CHAPTER_ONE_EXIT_INTERACTION_HALF_WIDTH = 0x06
CHAPTER_ONE_EXIT_INTERACTION_HALF_DEPTH = 0x06

# Field 229 already owns the exact wooden leaf used by retail young Rico.  Its
# script-4 helper plays sound 0x08 and performs the finite hinge animation.  The
# playable sanitizer retires scripts 2..31, so pin and explicitly restore only
# this helper; the unused close helper remains retired when Rico changes field.
CHAPTER_ONE_DOOR_ENTITY = 6
CHAPTER_ONE_DOOR_INIT_PC = 0x0340
CHAPTER_ONE_DOOR_INIT_BODY = bytes.fromhex("BC 2A 00")
CHAPTER_ONE_DOOR_OPEN_SCRIPT = 4
CHAPTER_ONE_DOOR_OPEN_PC = 0x0345
CHAPTER_ONE_DOOR_OPEN_BODY = bytes.fromhex(
    "74 08 80 02 04 04 0E 00 41 5A 03 BF 40 80 3C 04 04 5A 01 48 03 00"
)

# Rico's visible departure is deliberately confined to the connected interior
# side of the opened leaf.  RAC31 Slot 1 proved that both old cross-seam OP4B
# legs exhausted their 64-update budgets without moving, after which an OP1A
# incorrectly treated exterior triangle 78 as walkmesh *layer* 78 and froze
# the field.  Walk only to the reachable t59 threshold, start that bounded
# script asynchronously, and let the fade communicate the actual crossing.
# The parent transition therefore remains finite even if this cosmetic walk
# is obstructed.
CHAPTER_ONE_DOOR_DEPARTURE_SCRIPT = 8
CHAPTER_ONE_DOOR_DEPARTURE_MAX_STEPS = 16
CHAPTER_ONE_DOOR_DEPARTURE_VISIBLE_FRAMES = 8
CHAPTER_ONE_DOOR_REPOSITION = (70, 76, 59)
CHAPTER_ONE_DOOR_TURN_TO_ANNA_FRAMES = 4

DIALOGUE_WINDOW_WIDTH = 58
DIALOGUE_WINDOW_HEIGHT = 7
DIALOGUE_WINDOW_MIN_WIDTH = 8
DIALOGUE_CHOICE_START = "<Opcode:01:FF>"
DIALOGUE_ZERO_WIDTH_TOKENS = frozenset(("Wait", "Opcode:01:FF"))
DIALOGUE_PLAIN_SPEAKERS = frozenset(
    ("Anne", "ETHOS PRIEST", "Hammer", "Sigmund", "Rue", "Suzarn", "Guard",
     "Infirmary Attendant", "Worker", "Leonardo", "Prisoner", "Battler",
     "Arena Official", "Gramps", "Clerk", "Latina")
)
DIALOGUE_DELAY_TOKEN = re.compile(r"Delay:\d{1,3}\Z", re.ASCII)
DIALOGUE_TOKEN = re.compile(r"<([^<>]+)>", re.ASCII)
DIALOGUE_SENTENCE_CLOSERS = frozenset(("]", '"', "'", ")"))

HUB_FIELDS = {1: 720, 2: 229}
HUB_DONOR_FIELD = 719
HUB_DONOR_BUNDLE_SIZE = 45_076
HUB_DONOR_BUNDLE_SHA256 = (
    "f00ebb22804b968fe956d7cf633967a193448373a28a21a2f95c40da44d2df3e"
)
HUB_DONOR_GRAPHICS_SIZE = 112_640
HUB_DONOR_GRAPHICS_SHA256 = (
    "d0d6c0f6eddb4c6e4f63020cda740b3975f9108870c5e84a0606c27bd395c9aa"
)
HUB_MUSIC = 0x41
HUB_ENTRY_POSITION = (0, -1000, 1)
HUB_MARKER_ACTOR_BANK = 1
HUB_MARKER_ACTOR_BANK_SHA256 = (
    "078c67c1e05379bd5733b18d29f924277f5507b1e37e0f148e3d2bef3bdbd23f"
)
HUB_MARKER_SPRITE_BANK_SHA256 = (
    "d5d60d1f41c730e12acca80678865badcba0cb4a44d8e81511dd7a01ab964509"
)
HUB_SOURCE_SCRIPT_ENTITY_COUNT = 11
HUB_SOURCE_HEADER_RECORD_COUNT = 12
HUB_MARKER_FIRST_ENTITY = 10
HUB_MARKER_HALF_WIDTH = 0x10
HUB_MARKER_HALF_DEPTH = 0x10
HUB_PATH_ENTITY = 6
HUB_SAVE_DONOR_FIELD = 385
HUB_SAVE_SOURCE_ENTITY = 16
HUB_SAVE_SOURCE_POINTERS = (0x0172, 0x01B1, 0x01B8, 0x01C0)
HUB_SAVE_ACTOR_BANK = 2
HUB_SAVE_ACTOR_SIZE = 2_408
HUB_SAVE_ACTOR_SHA256 = (
    "42d88ff3385229ef53fdcf468b13ab61b6413a9ee47d756ece61756c246b8c52"
)
HUB_SAVE_SPRITE_SIZE = 7_308
HUB_SAVE_SPRITE_SHA256 = (
    "69060c5d8f1f25c3a3a4c438baaaabb18551f250abf66364b60cbbc28ac468d0"
)
HUB_SAVE_VRAM_MAPPING = (960, 0, 0, 0)
HUB_SAVE_VRAM_SIZE = (64, 256)
HUB_SAVE_ENTITY = HUB_MARKER_FIRST_ENTITY + 7
HUB_SAVE_POSITION = (300, -925, 1)
HUB_SAVE_HALF_WIDTH = 0x0F
HUB_SAVE_HALF_DEPTH = 0x0F
HUB_SAVE_LOCAL_FLAG = 0x040E
HUB_SAVE_UPDATE = bytes.fromhex("37 0E 04 FE 99 01 00")
HUB_SAVE_NATIVE_ACTION = bytes.fromhex("FE 99 00 FE 55 FE 87 00")
HUB_SAVE_NATIVE_COLLISION_PREFIX = bytes.fromhex(
    "FE 99 00 02 0E 04 00 00 40 D1 01 74 50 80 36 0E 04 00"
)
HUB_SAVE_MENU_CHOICE = (
    "<Opcode:01:FF>MEMORY CUBE\n"
    "     Open Save Menu\n"
    "     Return to Main Menu\n"
    "     Cancel<Close>"
)
CHAPTER_FIELDS = {
    1: {chapter_id: 720 + chapter_id for chapter_id in range(1, 8)},
    2: {chapter_id: 229 + chapter_id for chapter_id in range(1, 8)},
}

# Rico leaves through Anne's real bedroom door and enters a dedicated,
# automatic daylight exterior.  Retail field 199 supplies an authentic Nortune
# residential facade and a discarded wooden packing crate beside it.  Young
# Rico's exact field-229 actor/sprite bank replaces its compatible bank 1, and
# every retail battle/story actor is retired.  The route visibly takes him from
# the patched-metal home to the crate and back while narration names the action.
CHAPTER_ONE_FIREWOOD_FIELD = 377
CHAPTER_ONE_FIREWOOD_DONOR_FIELD = 199
CHAPTER_ONE_FIREWOOD_RICO_SOURCE_FIELD = 229
CHAPTER_ONE_FIREWOOD_DONOR_BUNDLE_SIZE = 160_504
CHAPTER_ONE_FIREWOOD_DONOR_BUNDLE_SHA256 = (
    "bc3a0700a6eaca262d8350bd3bad3b7943bc475ed46d10fbc066aca6d6e12ba9"
)
CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SIZE = 311_296
CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SHA256 = (
    "09b85a270a107d425c532ec5d9206f541e4cdb13b2cab503926e0a026f064865"
)
CHAPTER_ONE_FIREWOOD_DONOR_HEADER_SIZE = 2_400
CHAPTER_ONE_FIREWOOD_DONOR_HEADER_SHA256 = (
    "3c0a2e8d7f6a94cb880013f681007410e77961e3a901ea5042ed828c327239d4"
)
CHAPTER_ONE_FIREWOOD_DONOR_WALKMESH_SIZE = 36_456
CHAPTER_ONE_FIREWOOD_DONOR_WALKMESH_SHA256 = (
    "0a848ad6775cecd4cfdd02958c55a0e5b9d2d14e8518632486b0f0e12ed2e7b3"
)
CHAPTER_ONE_FIREWOOD_DONOR_MODELS_SIZE = 148_156
CHAPTER_ONE_FIREWOOD_DONOR_MODELS_SHA256 = (
    "766d811d44f28f00eb7aade5039f51d1c0174dfba7aeb4725051b80e11d397cb"
)
CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_COMPONENT_SIZE = 8_948
CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_COMPONENT_SHA256 = (
    "6e53eebd45021f526ff7f09fa2eb78d481030a4d27dfdf40da2ed0df60f362b0"
)
CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_COMPONENT_SIZE = 43_956
CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_COMPONENT_SHA256 = (
    "00043fa8710bb55999c232d6bdae55fad4f791d6bcd6378827006fb21f0f1556"
)
CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_BANK_SIZE = 2_408
CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_BANK_SHA256 = (
    "42d88ff3385229ef53fdcf468b13ab61b6413a9ee47d756ece61756c246b8c52"
)
CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_BANK_SIZE = 7_308
CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_BANK_SHA256 = (
    "69060c5d8f1f25c3a3a4c438baaaabb18551f250abf66364b60cbbc28ac468d0"
)
CHAPTER_ONE_FIREWOOD_DONOR_ENTITY_COUNT = 50
CHAPTER_ONE_FIREWOOD_DONOR_DIRECTOR_INIT_PC = 0x0016
CHAPTER_ONE_FIREWOOD_DONOR_DIRECTOR_INIT_BODY = bytes.fromhex(
    "BC 35 3A 04 53 F8 40 35 3C 04 84 FE 40 35 3E 04 00 00 40 "
    "35 38 04 01 00 40 35 54 00 02 00 40 FE 3B 05 80 A0 01 80 "
    "16 80 9C 82 9D C0 8F 00 75 2F 80 00"
)
CHAPTER_ONE_FIREWOOD_BANK_INDEX = 1
CHAPTER_ONE_FIREWOOD_BANK_VRAM_MAPPING = (896, 0, 0, 0)
CHAPTER_ONE_FIREWOOD_RICO_ENTITY = 1
CHAPTER_ONE_FIREWOOD_APPROACH_SCRIPT = 4
CHAPTER_ONE_FIREWOOD_RETURN_SCRIPT = 5
CHAPTER_ONE_FIREWOOD_WAYPOINT_MAX_STEPS = 120
CHAPTER_ONE_FIREWOOD_DOOR_POSITION = (430, 215, 202)
CHAPTER_ONE_FIREWOOD_MID_ROUTE = (
    (535, 190, 221),
    (535, 13, 216),
)
CHAPTER_ONE_FIREWOOD_WORK_POSITION = (514, 13, 216)
CHAPTER_ONE_FIREWOOD_RICO_TIMESCALE = 0x140
CHAPTER_ONE_FIREWOOD_CRATE_NODE = 72
CHAPTER_ONE_FIREWOOD_CRATE_HEADER_RECORD = bytes.fromhex(
    "10 00 00 00 00 00 00 00 00 00 00 00 00 00 11 00"
)
CHAPTER_ONE_FIREWOOD_CRATE_MODEL_INDEX = 17
CHAPTER_ONE_FIREWOOD_CRATE_MODEL_SIZE = 1_460
CHAPTER_ONE_FIREWOOD_CRATE_MODEL_SHA256 = (
    "d757e960bcc474c195632c63a555ee6b05f6d7ecfe9fb7c2cda0de4c004d87a3"
)
CHAPTER_ONE_FIREWOOD_DOOR_NODE = 52
CHAPTER_ONE_FIREWOOD_DOOR_HEADER_RECORD = bytes.fromhex(
    "90 02 00 00 00 0C 00 00 8E 01 E5 FF AD 00 02 00"
)
CHAPTER_ONE_FIREWOOD_DOOR_MODEL_INDEX = 2
CHAPTER_ONE_FIREWOOD_DOOR_MODEL_SIZE = 156
CHAPTER_ONE_FIREWOOD_DOOR_MODEL_SHA256 = (
    "26c37d9718f2880a01e6e5067b789d4ab73236eba9a2cf603897e6da114133de"
)
# Camera vectors use ATEL's (x, z, y) order.  The work shot keeps the wooden
# crate and the low Nortune facade in frame; a brief cut masks the unsupported
# pickup/carry pose while the on-screen narration names what Rico is doing.
CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_TARGET = (470, 120, -55)
CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_EYE = (926, 696, -457)
CHAPTER_ONE_FIREWOOD_WORK_CAMERA_TARGET = (480, 13, -70)
CHAPTER_ONE_FIREWOOD_WORK_CAMERA_EYE = (750, -302, -286)
CHAPTER_ONE_FIREWOOD_FIELD_FADE_FRAMES = 36
CHAPTER_ONE_FIREWOOD_ESTABLISH_HOLD_FRAMES = 40
CHAPTER_ONE_FIREWOOD_CAMERA_MOVE_FRAMES = 30
CHAPTER_ONE_FIREWOOD_WORK_SETTLE_FRAMES = 24
CHAPTER_ONE_FIREWOOD_GATHER_PAUSE_FRAMES = 30
CHAPTER_ONE_FIREWOOD_PICKUP_FADE_FRAMES = 20
CHAPTER_ONE_FIREWOOD_PICKUP_BLACK_HOLD_FRAMES = 12
CHAPTER_ONE_FIREWOOD_RETURN_SETTLE_FRAMES = 30

# The post-firewood story remains entirely inside the field engine.  Target
# 376 reuses Rico's authentic childhood room (retail field 229) for his return,
# Anne's final illness, and the empty-bed aftermath.  Target 378 then owns a
# live funeral on a broad upland burial ground outside the capital.  Completion
# bit 5 is deliberately committed only in that final field.
CHAPTER_ONE_AFTERMATH_FIELD = 376
CHAPTER_ONE_AFTERMATH_DONOR_FIELD = 229
CHAPTER_ONE_AFTERMATH_DONOR_BUNDLE_SIZE = 30_484
CHAPTER_ONE_AFTERMATH_DONOR_BUNDLE_SHA256 = (
    "4fbe78dc6292c1d7a22d47606db739cf46cfb8f4359c23193049a46266a85cfe"
)
CHAPTER_ONE_AFTERMATH_DONOR_GRAPHICS_SIZE = 137_216
CHAPTER_ONE_AFTERMATH_DONOR_GRAPHICS_SHA256 = (
    "3f521dfec1e8ddaf3f39af0f3446e4de7e0841a47a2482efb00a1b9fb9315a75"
)
CHAPTER_ONE_AFTERMATH_HEADER_SIZE = 848
CHAPTER_ONE_AFTERMATH_HEADER_SHA256 = (
    "ff81ef5782d5fab847da345598dad168b7318ef2d894957dd051b24e13f781aa"
)
CHAPTER_ONE_AFTERMATH_ENTITY_COUNT = 7
CHAPTER_ONE_AFTERMATH_CAMERA_ENTITY = 1
CHAPTER_ONE_AFTERMATH_RICO_ENTITY = 5
CHAPTER_ONE_AFTERMATH_RICO_INIT_PC = 0x0227
CHAPTER_ONE_AFTERMATH_RICO_INIT_BODY = bytes.fromhex(
    "0B 01 80 19 90 00 90 00 C0 5F 04 2A 00"
)
CHAPTER_ONE_AFTERMATH_DOOR_ENTITY = 6
CHAPTER_ONE_AFTERMATH_ENTRY_SCRIPT = 4
CHAPTER_ONE_AFTERMATH_COUGH_SCRIPT = 9
CHAPTER_ONE_AFTERMATH_DOOR_START_POSITION = (144, 144, 78)
CHAPTER_ONE_AFTERMATH_ENTRY_POSITION = (47, 41, 58)
CHAPTER_ONE_AFTERMATH_ENTRY_MAX_STEPS = 64
CHAPTER_ONE_AFTERMATH_FADE_FRAMES = 24
# Retail field 229 keeps its room grade in RGB-fader slot 1 while its cinematic
# B3/B4 fades run independently in slot 0.  Keep that layering, but use a
# channel-corrected blue grade for the post-firewood night.  F1 stores its
# three color operands as R,G,B despite the older Noah debugger's B,G,R labels.
CHAPTER_ONE_AFTERMATH_NIGHT_GRADE_MODE = 2
CHAPTER_ONE_AFTERMATH_NIGHT_GRADE_RGB = (100, 40, 30)
CHAPTER_ONE_AFTERMATH_NIGHT_GRADE_FRAMES = 1
CHAPTER_ONE_AFTERMATH_DAYLIGHT_GRADE_RGB = (0, 0, 0)
CHAPTER_ONE_AFTERMATH_BLACKOUT_RGB = (0xFF, 0xFF, 0xFF)
# Retail field 229 initializes Anne beside the kitchen counter at (-124,203),
# then its sickroom helper snaps her to (13,-84).  That source choreography is
# hidden in retail, but the playable return-home shot reveals the first
# position while Rico enters and makes the later cut look like a teleport.
# Anne can naturally move while Rico is outside gathering wood.  Initialize
# the clone at the helper's final, audited stance before the room is revealed.
CHAPTER_ONE_AFTERMATH_ANNA_SICKROOM_POSITION = (13, -84, 73)

# Exact retail field-229 staging helpers.  The B5 camera is tracked through
# invisible entity 1, so each camera preset is paired with its authored anchor
# move instead of guessing a new view of the room.
CHAPTER_ONE_AFTERMATH_NATIVE_HELPERS = {
    (1, 4): (0x00F2, bytes.fromhex("19 CC 00 C6 FF C0 00")),
    (1, 6): (0x0100, bytes.fromhex("19 BA FF B6 FF C0 00")),
    (1, 7): (0x0107, bytes.fromhex("19 5E 00 91 FF C0 00")),
    (4, 5): (0x0199, bytes.fromhex("19 0D 00 AC FF C0 5F 03 00")),
    (4, 8): (0x01B6, bytes.fromhex("19 73 00 FD FE C0 25 04 00")),
    (5, 6): (0x025E, bytes.fromhex("19 82 00 E0 FF C0 5F 02 00")),
    (5, 9): (
        0x0277,
        bytes.fromhex("20 0D 80 19 A3 00 4E FF C0 5F 06 00"),
    ),
    (6, 0): (0x0340, bytes.fromhex("BC 2A 00")),
    (6, 4): (0x0345, CHAPTER_ONE_DOOR_OPEN_BODY),
}
CHAPTER_ONE_AFTERMATH_DOOR_CLOSE_PC = 0x035B

CHAPTER_ONE_FUNERAL_FIELD = 378
CHAPTER_ONE_LIVE_FUNERAL_DONOR_FIELD = 15
CHAPTER_ONE_LIVE_FUNERAL_DONOR_BUNDLE_SIZE = 114_012
CHAPTER_ONE_LIVE_FUNERAL_DONOR_BUNDLE_SHA256 = (
    "9461e0ce6855c404c02badacf7c1b913a356b1685957bf129a79df30bf6382c5"
)
CHAPTER_ONE_LIVE_FUNERAL_DONOR_GRAPHICS_SIZE = 380_928
CHAPTER_ONE_LIVE_FUNERAL_DONOR_GRAPHICS_SHA256 = (
    "a5f3fdce2d67135721a987f5ddc97ec9beb90bfbc475432c921232663c7f6f43"
)
CHAPTER_ONE_LIVE_FUNERAL_DONOR_HEADER_SIZE = 2_144
CHAPTER_ONE_LIVE_FUNERAL_DONOR_HEADER_SHA256 = (
    "88d6eb4da5c8842147c4cd9312075163dde287b8183cb4487d886b2eb9c2d4de"
)
CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_HEADER_SHA256 = (
    "bdb406fdcdfb47b539b58c4ab8e1f805f386df68dc2232caab0c04e49025832a"
)
CHAPTER_ONE_LIVE_FUNERAL_ENTITY_COUNT = 63
CHAPTER_ONE_LIVE_FUNERAL_RICO_ENTITY = 1
CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ENTITY = 2
CHAPTER_ONE_LIVE_FUNERAL_PRIEST_APPROACH_SCRIPT = 4
CHAPTER_ONE_LIVE_FUNERAL_COMPLETION_SCRIPT = 5
CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX = 1
CHAPTER_ONE_LIVE_FUNERAL_RICO_SPRITE_BANK_INDEX = 1
CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX = 0
CHAPTER_ONE_LIVE_FUNERAL_PRIEST_SPRITE_BANK_INDEX = 0
CHAPTER_ONE_LIVE_FUNERAL_DONOR_RICO_SPRITE_BANK_INDEX = 0
CHAPTER_ONE_LIVE_FUNERAL_PRESERVED_ACTOR_BANK_INDEX = 5
CHAPTER_ONE_LIVE_FUNERAL_PRESERVED_SPRITE_BANK_INDEX = 1
CHAPTER_ONE_LIVE_FUNERAL_RICO_POSITION = (500, -2400, 1882)
CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START = (950, -2350, 1885)
CHAPTER_ONE_LIVE_FUNERAL_PRIEST_BLESSING_POSITION = (720, -2520, 1885)
CHAPTER_ONE_LIVE_FUNERAL_MARKER_POSITION = (600, -2700, 1885)
CHAPTER_ONE_LIVE_FUNERAL_BACKGROUND_MARKER_POSITION = (900, -2750, 1885)
CHAPTER_ONE_LIVE_FUNERAL_RICO_DIRECTION = 7
CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START_DIRECTION = 6
CHAPTER_ONE_LIVE_FUNERAL_PRIEST_BLESSING_DIRECTION = 4
CHAPTER_ONE_LIVE_FUNERAL_WAYPOINT_MAX_STEPS = 160
CHAPTER_ONE_LIVE_FUNERAL_CAMERA_TARGET = (700, -2525, -20)
CHAPTER_ONE_LIVE_FUNERAL_CAMERA_EYE = (1400, -3400, -650)
CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_TARGET = (700, -2600, -20)
CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_EYE = (1120, -3160, -430)
CHAPTER_ONE_LIVE_FUNERAL_CAMERA_MOVE_FRAMES = 36
CHAPTER_ONE_LIVE_FUNERAL_RETURN_CAMERA_MOVE_FRAMES = 48
CHAPTER_ONE_LIVE_FUNERAL_FADE_FRAMES = 36
CHAPTER_ONE_LIVE_FUNERAL_ESTABLISH_HOLD_FRAMES = 60
CHAPTER_ONE_LIVE_FUNERAL_BLESSING_SETTLE_FRAMES = 42
CHAPTER_ONE_LIVE_FUNERAL_REFLECTION_HOLD_FRAMES = 60
CHAPTER_ONE_LIVE_FUNERAL_WIDE_HOLD_FRAMES = 60
CHAPTER_ONE_LIVE_FUNERAL_EPILOGUE_SETTLE_FRAMES = 30
# The funeral story belongs to invisible director entity 0.  F5 bit 0 keeps
# native WAIT_DIALOG alive when its owning actor is hidden; without it, the
# first graveside textbox takes OP_STOP and aborts the entire conclusion.
CHAPTER_ONE_LIVE_FUNERAL_HIDDEN_DIALOGUE_FLAGS = 0x01

# Field 15's component-04 entries correspond only to actor banks whose header
# upload flag is clear. Retail therefore maps sprite 0 to actor bank 1 and
# sprite 1 to bank 5. The funeral keeps that compact ordering while adding the
# hooded Ethos priest as bank 0. Field 15's later MIM upload owns x832 and
# contains Rico's exact 64-by-75 sheet, so Rico stays there while the taller
# priest occupies the unobstructed x896 page. The bank-5 upload remains as a
# third entry so the header and component counts agree.
CHAPTER_ONE_LIVE_FUNERAL_DONOR_RICO_ACTOR_BANK_SHA256 = (
    "fed1648acf4758bdffb60ebd04b762f4a69255aabe04e64d72c69dc3b893826c"
)
CHAPTER_ONE_LIVE_FUNERAL_DONOR_RICO_SPRITE_BANK_SHA256 = (
    "8e3be5c4a63d06e76f6afd4d132169e40c846a4e4a3f8b7307bf23345f9088d1"
)
CHAPTER_ONE_LIVE_FUNERAL_DONOR_PRIEST_ACTOR_BANK_SHA256 = (
    "041ba5fb6be84e6e80dd30c51f0a57566b93fd34b84c8fb2e6ea578b0ff92caa"
)
CHAPTER_ONE_LIVE_FUNERAL_DONOR_PRESERVED_SPRITE_BANK_SHA256 = (
    "69060c5d8f1f25c3a3a4c438baaaabb18551f250abf66364b60cbbc28ac468d0"
)
CHAPTER_ONE_ETON_SOURCE_FIELD = 348
CHAPTER_ONE_ETON_SOURCE_BUNDLE_SIZE = 48_552
CHAPTER_ONE_ETON_SOURCE_BUNDLE_SHA256 = (
    "e55d30e34a22462480d6fb08a6d4a826d1b00348aa0eb544e5cb001dd47466be"
)
CHAPTER_ONE_ETON_ACTOR_COMPONENT_SIZE = 8_992
CHAPTER_ONE_ETON_ACTOR_COMPONENT_SHA256 = (
    "9840e89817bf8c3be57e274de8073b1b061f7ab8baa924577c1b6908cf82400a"
)
CHAPTER_ONE_ETON_SPRITE_COMPONENT_SIZE = 62_516
CHAPTER_ONE_ETON_SPRITE_COMPONENT_SHA256 = (
    "6641415ccd433383d200715f550f595dbe7cbf6bb3ff6b51ec424ee16ab210be"
)
CHAPTER_ONE_ETON_ACTOR_BANK_SIZE = 2_448
CHAPTER_ONE_ETON_ACTOR_BANK_SHA256 = (
    "a11b63437f3775caa9dd4618c9732441cf92b8c0fd35cceb6648738778fa93ac"
)
CHAPTER_ONE_ETON_SPRITE_BANK_SIZE = 26_124
CHAPTER_ONE_ETON_SPRITE_BANK_SHA256 = (
    "b1d95b5bc1be875f0fd1eaf1e4425f4603238e2c983cbcfb5b6f0d59db19b1ed"
)
CHAPTER_ONE_ETON_SOURCE_BANK_INDEX = 0
CHAPTER_ONE_ETON_SOURCE_BANK_VRAM_MAPPING = (832, 0, 0, 0)
CHAPTER_ONE_LIVE_FUNERAL_PRIEST_VRAM_MAPPING = (896, 0, 0, 0)
CHAPTER_ONE_LIVE_FUNERAL_RICO_VRAM_MAPPING = (832, 0, 0, 0)
CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_ACTOR_SIZE = 11_648
CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_ACTOR_SHA256 = (
    "8d95e98c2713446542c7dcabb527d0248703101b0a7ae84c999354822271dabf"
)
CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_SPRITE_SIZE = 43_060
CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_SPRITE_SHA256 = (
    "131f9d2cca2b53896eabe206d70e8470d59df681593bba66241f2a9e3b64b028"
)

# Field 15 owns two pale wooden cross/sign models.  Relocate both from the
# narrow ravine to its broad northern upland: one marks Anne's fresh grave and
# the second, weathered marker establishes that this is a burial ground rather
# than a random trail.  Both retain native models and textures.
CHAPTER_ONE_GRAVE_MARKER_TARGET_MODEL_INDEX = 2
CHAPTER_ONE_GRAVE_MARKER_TARGET_MODEL_SHA256 = (
    "76a5f2f30a34f6e929e296cd61b335a6089328de7aa16ad5d7c5ca400195852f"
)
CHAPTER_ONE_GRAVE_MARKER_TARGET_NODE = 63
CHAPTER_ONE_GRAVE_MARKER_SOURCE_NODE_RECORD = bytes.fromhex(
    "10 00 00 00 00 00 00 00 00 00 00 00 00 00 02 00"
)
CHAPTER_ONE_GRAVE_MARKER_TARGET_NODE_RECORD = bytes.fromhex(
    "10 00 00 00 00 00 00 00 B0 03 48 02 34 F0 02 00"
)
CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_MODEL_INDEX = 3
CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_MODEL_SHA256 = (
    "5726c4f0a7e085b1571ee5d44c5c4d875d55a0c7c4edbba17fd1ac106c9ccb8d"
)
CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_NODE = 64
CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_SOURCE_NODE_RECORD = bytes.fromhex(
    "10 00 00 00 00 00 00 00 00 00 00 00 00 00 03 00"
)
CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_NODE_RECORD = bytes.fromhex(
    "10 00 00 00 00 00 00 00 2C 02 1A 00 D2 F8 03 00"
)

PLAYABLE_BATTLE_RESOURCE_IDS = (47, 2614, 2622, 2623)
PLAYABLE_BATTLE_RESOURCE_IDENTITIES = {
    47: (
        4_544,
        "c12ac12cc0926364f534f930575bafe7213067385e0a24277e0789a8b00f6b41",
    ),
    2614: (
        56_260,
        "52805ab340a772ad978266fb56cd747baae3549cee9260194e91605653cad369",
    ),
    2622: (
        5_808,
        "adf14b0fe34410e076adfe7d19eb6a2d58d8589031e47de37c98a3072baeb26c",
    ),
    2623: (
        163_848,
        "f17e757120023be7079d98544e5e56a46e940448504cf610b9b0ba4bf74a2347",
    ),
}
NORTUNE_ENCOUNTER_SHA256 = (
    "54325752ea0b7e2c679501792acf113e86495454e3a238acdaf63eaa7db06e16"
)
NORTUNE_CONFIGURATION_6 = bytes.fromhex(
    "02 00 1E 00 00 00 00 00 82 82 FF FF FF FF FF FF "
    "00 00 00 00 00 00 00 00 01 00 02 00 01 01 01 01"
)

# Retail field 218 is the Champion's sitting room above Latina's bar.  Its
# purple east leaf opens into field 219, the Champion's actual bedroom.  Keep
# that real two-room arrangement instead of treating the leaf as an arena
# entrance.  Standalone builds place the extra room immediately after Chapter
# 1's 376..378 presentation fields; the unified Disc 2 composition supplies a
# checked dummy-field override because Mass Driver owns logical field 379.
CHAPTER_TWO_BEDROOM_FIELD = 379
UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD = 67
CHAPTER_TWO_BEDROOM_DONOR_FIELD = 219
CHAPTER_TWO_PERSISTENT_STATE_VARIABLE = 0x03EC
CHAPTER_TWO_HAMMER_STATE_VARIABLE = 0x03EE
CHAPTER_TWO_HAMMER_ARRIVED_BIT = 0
CHAPTER_TWO_MAIN_FIELD_DONOR = 218
CHAPTER_TWO_MAIN_ENTRY = mass_driver.FieldEntryAddition(92, -29, 0, 7, 0xFF)
CHAPTER_TWO_MAIN_PLAYABLE_ENTRY = mass_driver.FieldEntryAddition(
    -125,
    134,
    0,
    7,
    0xFF,
)
CHAPTER_TWO_MAIN_RETURN_ENTRY = mass_driver.FieldEntryAddition(
    70,
    -318,
    0,
    0xFF,
    0xFF,
)
CHAPTER_TWO_MAIN_PLAYABLE_ENTRY_TRIANGLE = 38
CHAPTER_TWO_MAIN_RETURN_TRIANGLE = 71
CHAPTER_TWO_MAIN_DOOR_FRONTAGE = (94, -291, 70)
CHAPTER_TWO_MAIN_DOOR_ENTITY = 2
CHAPTER_TWO_MAIN_DOOR_MODEL_INDEX = 24
CHAPTER_TWO_MAIN_DOOR_HEADER_RECORD = bytes.fromhex(
    "90 02 00 00 00 0E 00 00 3E 00 00 00 8A FE 18 00"
)
CHAPTER_TWO_MAIN_DOOR_INIT_PC = 0x027A
CHAPTER_TWO_MAIN_DOOR_INIT_BODY = bytes.fromhex("46 00")
CHAPTER_TWO_MAIN_DOOR_ACTION_PC = 0x027D
CHAPTER_TWO_MAIN_DOOR_ACTION_BODY = bytes.fromhex(
    "02 44 02 02 00 46 94 02 15 C4 00 1F 11 47 00 "
    "DB 80 00 80 5B"
)

# e19 is retail Hammer.  Its local bank-4 actor/sprite pair is byte-identical
# to Hammer's field-269 appearance; e4 is Suzarn, the actor the older anthology
# accidentally placed at Hammer's hotspot.  Stage Hammer downstairs and run a
# finite two-leg climb through the donor's own stair waypoints.
CHAPTER_TWO_HAMMER_ENTITY = 19
CHAPTER_TWO_HAMMER_ACTOR_BANK = 4
CHAPTER_TWO_HAMMER_VRAM_MAPPING = (384, 256, 0, 0)
CHAPTER_TWO_HAMMER_ACTOR_BANK_SIZE = 5_788
CHAPTER_TWO_HAMMER_ACTOR_BANK_SHA256 = (
    "8efce6f4757622e7b060bffc5f5d1a241f457ab527f580f51c8e7f6b19fee910"
)
CHAPTER_TWO_HAMMER_SPRITE_BANK_SIZE = 29_196
CHAPTER_TWO_HAMMER_SPRITE_BANK_SHA256 = (
    "c50aa038b697ba4f34567991b49eaf05afd1d17162a144fc200b9da20c663e3e"
)
CHAPTER_TWO_HAMMER_NATIVE_INIT_PC = 0x079B
CHAPTER_TWO_HAMMER_NATIVE_INIT_PREFIX = bytes.fromhex("0B 04 80")
CHAPTER_TWO_HAMMER_STAGE_POSITION = (-97, -68, 64)
CHAPTER_TWO_HAMMER_ROUTE = ((-27, -151, 89), (69, -52, 14))
CHAPTER_TWO_HAMMER_ROUTE_MAX_STEPS = 120

CHAPTER_TWO_BEDROOM_BUNDLE_SIZE = 34_200
CHAPTER_TWO_BEDROOM_BUNDLE_SHA256 = (
    "6cc5d621c6acd9b0e7b66629a8fba28f55eb5136c8803f9905490267d6ef03e3"
)
CHAPTER_TWO_BEDROOM_GRAPHICS_SIZE = 94_208
CHAPTER_TWO_BEDROOM_GRAPHICS_SHA256 = (
    "9e941ecf8cb6737b248f708e74c7e357d607057b8bb846fe8880b05ac4452584"
)
CHAPTER_TWO_BEDROOM_HEADER_SIZE = 832
CHAPTER_TWO_BEDROOM_HEADER_SHA256 = (
    "c6e49e0f85fdb62f5cd23e052abd321f51af50c4880f54ba1c784a45f7add308"
)
CHAPTER_TWO_BEDROOM_COMPONENT_IDENTITIES = {
    1: (
        1_812,
        "0330571c5f384186a5c4e3245a520f9e9ff5caa7c0d2d43e11788ce5b0ab06dd",
    ),
    2: (
        6_796,
        "8ee67707fe2cb1fa1d221b4d4b73d6cc7981576408167f234c29f2b74601fc04",
    ),
    5: (
        7_128,
        "7316d32a9d8ef9e1a3a48e3692755256ab357ee5a1646e61df1752aeefc6c7d9",
    ),
    7: (
        469,
        "ac4f561122e5b8cad4e9fd2711c92a9f37d929e28ba9f6a5bcc095b436e72d70",
    ),
}
CHAPTER_TWO_BEDROOM_ENTITY_COUNT = 16
CHAPTER_TWO_BEDROOM_ENTRY = mass_driver.FieldEntryAddition(
    -131,
    10,
    0,
    0xFF,
    0xFF,
)
CHAPTER_TWO_BEDROOM_ENTRY_TRIANGLE = 8
CHAPTER_TWO_BEDROOM_RICO_ENTITY = 1
CHAPTER_TWO_BEDROOM_DOOR_ENTITY = 2
CHAPTER_TWO_BEDROOM_DOOR_HEADER_RECORD = bytes.fromhex(
    "90 02 00 00 00 06 00 00 84 FF 00 00 3E 00 01 00"
)
CHAPTER_TWO_BEDROOM_DOOR_MODEL_INDEX = 1
CHAPTER_TWO_BEDROOM_DOOR_MODEL_SIZE = 164
CHAPTER_TWO_BEDROOM_DOOR_MODEL_SHA256 = (
    "9a10fbeb7ab8d9915b1b36a3d2fe71c9d2f7d7781f0e3918dfa50b12f6867291"
)
CHAPTER_TWO_BEDROOM_DOOR_INIT_PC = 0x007D
CHAPTER_TWO_BEDROOM_DOOR_INIT_BODY = bytes.fromhex("46 00")
CHAPTER_TWO_BEDROOM_DOOR_ACTION_PC = 0x0080
CHAPTER_TWO_BEDROOM_DOOR_ACTION_BODY = bytes.fromhex(
    "15 C4 00 1F 11 47 00 DA 80 02 80 5B"
)
CHAPTER_TWO_BED_CONTROLLER_ENTITY = 3
CHAPTER_TWO_BED_POSITION = (-70, -110, 17)
CHAPTER_TWO_BED_REFLECTION = (
    "<Rico>\nA private room, better food, a door that locks.<New>"
    "The title of Champ never opened the gates of D Block.<Close>"
)
VARIABLE_PARTY_DONORS = {
    232: ((0x0161, 0x0175, 0x0180), (0x003E, 0x0040, 0x0042)),
    235: ((0x0165, 0x0179, 0x0184), (0x003E, 0x0040, 0x0042)),
}
PLAYABLE_ENTRY_POSITIONS = {
    # Keep chapter entries clear of the model-less interaction carriers.
    # OP18 doubles each encoded X/Z bound at runtime and selection adds the
    # player's fixed 16-unit extent.  The old Chapter 1 point (163,-178)
    # therefore started inside the cold-window carrier and could immediately
    # recapture Cross input, making young Rico appear unable to move.
    1: (115, -121, 86),
    2: (-125, 134, 38),
    3: (0, 0, 25),
    4: (91, 74, 15),
    5: (3, 51, 195),
    6: (0, 0, 164),
    7: (-11, 121, 32),
}
STAGED_PARTY_ACTORS = {
    # Fei remains a visible, stationary conversation partner while Rico is
    # the controlled leader.  The hub restores ordinary party following.
    2: {0: (-70, 181)},
    7: {0: (47, 116)},
}
CHAPTER_PARTIES = {
    1: (YOUNG_RICO_ID,),
    2: (RICO_ID, 0),
    3: (RICO_ID, 0, 2),
    4: (RICO_ID, 0, 3),
    5: (RICO_ID, 0, 3),
    6: (RICO_ID, 0, 3),
    7: (RICO_ID, 0),
}
HUB_PARTY = (RICO_ID,)
INTERACTION_ACTOR_BINDINGS = {
    1: {"Anne's bedside": (4,)},
    2: {"Hammer": (CHAPTER_TWO_HAMMER_ENTITY,), "Fei": (1,)},
    3: {"Sigmund": (25,)},
    4: {"Sigmund": (14,)},
    7: {"Fei": (1,)},
}

# Field 237 contains the real sliding leaf used by Rico's retail palace
# entrance.  Chapter 4 reuses that exact model and its finite native FE1B
# helpers for Fei and Bart's visible departure after Sigmund asks to speak in
# private.  Keep every source address and body pinned: the ordinary playable
# sanitizer retires donor scripts 2..31, so an unnoticed donor drift would
# otherwise turn the requested open/close calls into the shared STOP.
CHAPTER_FOUR_RICO_ENTITY = 2
CHAPTER_FOUR_FEI_ENTITY = 1
CHAPTER_FOUR_BART_ENTITY = 4
CHAPTER_FOUR_SIGMUND_ENTITY = 14
CHAPTER_FOUR_DOOR_ENTITY = 18
CHAPTER_FOUR_DOOR_MODEL_INDEX = 6
CHAPTER_FOUR_DOOR_MODEL_SIZE = 136
CHAPTER_FOUR_DOOR_MODEL_SHA256 = (
    "7f9805ef42cb862195fed5cac071e7c71108fb15af8244350f28559b6f032fbc"
)
CHAPTER_FOUR_DOOR_HEADER_RECORD = bytes.fromhex(
    "90 02 00 00 00 04 00 00 00 00 00 00 00 00 06 00"
)
CHAPTER_FOUR_DOOR_OPEN_SCRIPT = 6
CHAPTER_FOUR_DOOR_CLOSE_SCRIPT = 7
CHAPTER_FOUR_DOOR_OPEN_PC = 0x058B
CHAPTER_FOUR_DOOR_CLOSE_PC = 0x058F
CHAPTER_FOUR_DOOR_OPEN_BODY = bytes.fromhex("05 99 0D 00")
CHAPTER_FOUR_DOOR_CLOSE_BODY = bytes.fromhex("05 B8 0D 00")
CHAPTER_FOUR_DOOR_OPEN_SUBROUTINE_PC = 0x0D99
CHAPTER_FOUR_DOOR_CLOSE_SUBROUTINE_PC = 0x0DB8
CHAPTER_FOUR_DOOR_OPEN_SUBROUTINE = bytes.fromhex(
    "74 77 80 37 24 04 02 24 04 0E 00 43 B7 0D C6 FE 1B "
    "02 00 00 00 26 00 80 3C 24 04 01 9F 0D 0D"
)
CHAPTER_FOUR_DOOR_CLOSE_SUBROUTINE = bytes.fromhex(
    "74 77 80 37 26 04 02 26 04 0E 00 43 D6 0D C6 FE 1B "
    "FE FF 00 00 26 00 80 3C 26 04 01 BE 0D 0D"
)
CHAPTER_FOUR_WALKMESH_SIZE = 2_756
CHAPTER_FOUR_WALKMESH_SHA256 = (
    "a0a7c1c05273b635309a2997129aec0f2b90ec0d7d26593d87676ea26caef2f3"
)
CHAPTER_FOUR_SEALED_WALKMESH_SHA256 = (
    "6d1126d017e160af164fcb110849fa0e2a8636114550208f0fec6cf4566bbeb8"
)
CHAPTER_FOUR_WALKMESH_TRIANGLE_OFFSET = 0x28
CHAPTER_FOUR_WALKMESH_VERTEX_OFFSET = 0x450
CHAPTER_FOUR_DOOR_NEIGHBOR_LINKS = ((35, 1, 36), (36, 1, 35))
CHAPTER_FOUR_DOOR_TRIANGLE_RECORDS = {
    35: bytes.fromhex("04 00 02 00 03 00 FF FF 24 00 22 00 86 00"),
    36: bytes.fromhex("00 00 03 00 02 00 25 00 23 00 FF FF 86 00"),
}
CHAPTER_FOUR_DOOR_VERTEX_RECORDS = {
    2: bytes.fromhex("15 01 00 00 24 FF 00 00"),
    3: bytes.fromhex("FC 00 00 00 24 FF 00 00"),
}
CHAPTER_FOUR_DOOR_EXTERIOR_TRIANGLES = frozenset((36, 37))
CHAPTER_FOUR_PRIVATE_STAGE_SCRIPT = 4
CHAPTER_FOUR_PRIVATE_APPROACH_SCRIPT = 5
CHAPTER_FOUR_PRIVATE_CROSS_SCRIPT = 6
CHAPTER_FOUR_PRIVATE_WAYPOINT_MAX_STEPS = 120
CHAPTER_FOUR_PRIVATE_LOOK_PAUSE = 20
CHAPTER_FOUR_PRIVATE_ASSENT_PAUSE = 30
CHAPTER_FOUR_PRIVATE_SETTLE_PAUSE = 45

# Fields 235 and 232 each retain one visible native exit leaf on e5.  Their
# walkmesh triangles themselves straddle the closed leaf, so severing graph
# neighbors cannot block the player.  Chapters 5 and 6 instead make the
# anthology exit carrier an invisible, immovable contact actor and restore
# only these pinned finite native door helpers for the completion choice.
CHAPTER_FIVE_DOOR_ENTITY = 5
CHAPTER_FIVE_DOOR_MODEL_INDEX = 4
CHAPTER_FIVE_DOOR_MODEL_SIZE = 136
CHAPTER_FIVE_DOOR_MODEL_SHA256 = (
    "3a017dbd2020876e29cd19bfe8ec2120a37c6c692cbd08bfc63384a71593a49a"
)
CHAPTER_FIVE_DOOR_HEADER_RECORD = bytes.fromhex(
    "90 02 00 00 00 00 00 00 00 00 00 00 00 00 04 00"
)
CHAPTER_FIVE_DOOR_OPEN_SCRIPT = 4
CHAPTER_FIVE_DOOR_CLOSE_SCRIPT = 5
CHAPTER_FIVE_DOOR_INIT_PC = 0x01B4
CHAPTER_FIVE_DOOR_INIT_BODY = bytes.fromhex("BC 2A 00")
CHAPTER_FIVE_DOOR_OPEN_PC = 0x01B9
CHAPTER_FIVE_DOOR_OPEN_BODY = bytes.fromhex("05 08 00 00")
CHAPTER_FIVE_DOOR_CLOSE_BODY = bytes.fromhex("05 27 00 00")
CHAPTER_FIVE_DOOR_OPEN_SUBROUTINE_PC = 0x0008
CHAPTER_FIVE_DOOR_CLOSE_SUBROUTINE_PC = 0x0027
CHAPTER_FIVE_DOOR_OPEN_SUBROUTINE = bytes.fromhex(
    "74 77 80 37 02 04 02 02 04 0E 00 43 26 00 C6 FE 1B "
    "02 00 00 00 26 00 80 3C 02 04 01 0E 00 0D"
)
CHAPTER_FIVE_DOOR_CLOSE_SUBROUTINE = bytes.fromhex(
    "74 77 80 37 04 04 02 04 04 0E 00 43 45 00 C6 FE 1B "
    "FE FF 00 00 26 00 80 3C 04 04 01 2D 00 0D"
)

CHAPTER_SIX_DOOR_ENTITY = 5
CHAPTER_SIX_DOOR_MODEL_INDEX = 3
CHAPTER_SIX_DOOR_MODEL_SIZE = 172
CHAPTER_SIX_DOOR_MODEL_SHA256 = (
    "da6f22d67e6ef389e6ea7625bf90e086cdbc5367e074cc1eaedda71666d47eab"
)
CHAPTER_SIX_DOOR_HEADER_RECORD = bytes.fromhex(
    "90 02 00 00 00 00 00 00 00 00 00 00 00 00 03 00"
)
CHAPTER_SIX_DOOR_OPEN_SCRIPT = 4
CHAPTER_SIX_DOOR_CLOSE_SCRIPT = 5
CHAPTER_SIX_DOOR_INIT_PC = 0x01B4
CHAPTER_SIX_DOOR_INIT_BODY = bytes.fromhex("BC 2A 00")
CHAPTER_SIX_DOOR_OPEN_PC = 0x01B9
CHAPTER_SIX_DOOR_OPEN_BODY = bytes.fromhex("05 08 00 00")
CHAPTER_SIX_DOOR_CLOSE_BODY = bytes.fromhex("05 27 00 00")
CHAPTER_SIX_DOOR_OPEN_SUBROUTINE_PC = 0x0008
CHAPTER_SIX_DOOR_CLOSE_SUBROUTINE_PC = 0x0027
CHAPTER_SIX_DOOR_OPEN_SUBROUTINE = bytes.fromhex(
    "74 77 80 37 00 04 02 00 04 0E 00 43 26 00 C6 FE 1B "
    "02 00 00 00 26 00 80 3C 00 04 01 0E 00 0D"
)
CHAPTER_SIX_DOOR_CLOSE_SUBROUTINE = bytes.fromhex(
    "74 77 80 37 02 04 02 02 04 0E 00 43 45 00 C6 FE 1B "
    "FE FF 00 00 26 00 80 3C 02 04 01 2D 00 0D"
)

# Field 298 is visibly Rico and Hammer's Yggdrasil bedroom.  Its east wall
# carries one real sliding leaf (e15/model17); the retail model-less e16
# action carrier is deliberately retired with the donor story logic.  Chapter
# 7 restores only e15's finite open/close helpers and completes at the exact
# retail inside-door stance.
CHAPTER_SEVEN_DOOR_ENTITY = 15
CHAPTER_SEVEN_DOOR_MODEL_INDEX = 17
CHAPTER_SEVEN_DOOR_MODEL_SIZE = 136
CHAPTER_SEVEN_DOOR_MODEL_SHA256 = (
    "4cc0e226a7e6d439b5c9c2547085051721a66ab0be01701f455e65300e58a415"
)
CHAPTER_SEVEN_DOOR_HEADER_RECORD = bytes.fromhex(
    "90 02 00 00 00 0C 00 00 00 00 00 00 00 00 11 00"
)
CHAPTER_SEVEN_DOOR_OPEN_SCRIPT = 4
CHAPTER_SEVEN_DOOR_CLOSE_SCRIPT = 5
CHAPTER_SEVEN_DOOR_OPEN_PC = 0x02D3
CHAPTER_SEVEN_DOOR_CLOSE_PC = 0x02D7
CHAPTER_SEVEN_DOOR_OPEN_BODY = bytes.fromhex("05 8E 03 00")
CHAPTER_SEVEN_DOOR_CLOSE_BODY = bytes.fromhex("05 AD 03 00")
CHAPTER_SEVEN_DOOR_OPEN_SUBROUTINE_PC = 0x038E
CHAPTER_SEVEN_DOOR_CLOSE_SUBROUTINE_PC = 0x03AD
CHAPTER_SEVEN_DOOR_OPEN_SUBROUTINE = bytes.fromhex(
    "74 77 80 37 0A 04 02 0A 04 10 00 43 AC 03 C6 FE 1B "
    "FE FF 00 00 26 00 80 3C 0A 04 01 94 03 0D"
)
CHAPTER_SEVEN_DOOR_CLOSE_SUBROUTINE = bytes.fromhex(
    "74 77 80 37 0C 04 02 0C 04 10 00 43 CB 03 C6 FE 1B "
    "02 00 00 00 26 00 80 3C 0C 04 01 B3 03 0D"
)
CHAPTER_SEVEN_WALKMESH_SIZE = 2_492
CHAPTER_SEVEN_WALKMESH_SHA256 = (
    "e26b64fa0429d72edbde32587af5baca5d9a9c9447f1dd88c5b7d26e1e592ae6"
)
CHAPTER_SEVEN_SEALED_WALKMESH_SHA256 = (
    "18ac3ff55670b188b67526bdeb815b9869491d76a5f06c7e9f499c6dd55723a3"
)
CHAPTER_SEVEN_WALKMESH_TRIANGLE_OFFSET = 0x30
CHAPTER_SEVEN_WALKMESH_VERTEX_OFFSET = 0x254
CHAPTER_SEVEN_DOOR_NEIGHBOR_LINKS = ((22, 0, 23), (23, 2, 22))
CHAPTER_SEVEN_DOOR_TRIANGLE_RECORDS = {
    22: bytes.fromhex("18 00 17 00 1B 00 17 00 FF FF 15 00 86 00"),
    23: bytes.fromhex("18 00 19 00 17 00 FF FF 19 00 16 00 01 00"),
}
CHAPTER_SEVEN_DOOR_VERTEX_RECORDS = {
    24: bytes.fromhex("AC 00 00 00 B1 FF 00 00"),
    23: bytes.fromhex("AC 00 00 00 F1 FF 00 00"),
}
CHAPTER_SEVEN_DOOR_EXTERIOR_TRIANGLES = frozenset((21, 22))
CHAPTER_SEVEN_EXIT_POSITION = (164, -45, 23)
PLAYABLE_NATIVE_EXIT_DOORS = {
    4: (
        CHAPTER_FOUR_DOOR_ENTITY,
        CHAPTER_FOUR_DOOR_OPEN_SCRIPT,
        CHAPTER_FOUR_DOOR_CLOSE_SCRIPT,
    ),
    5: (
        CHAPTER_FIVE_DOOR_ENTITY,
        CHAPTER_FIVE_DOOR_OPEN_SCRIPT,
        CHAPTER_FIVE_DOOR_CLOSE_SCRIPT,
    ),
    6: (
        CHAPTER_SIX_DOOR_ENTITY,
        CHAPTER_SIX_DOOR_OPEN_SCRIPT,
        CHAPTER_SIX_DOOR_CLOSE_SCRIPT,
    ),
    7: (
        CHAPTER_SEVEN_DOOR_ENTITY,
        CHAPTER_SEVEN_DOOR_OPEN_SCRIPT,
        CHAPTER_SEVEN_DOOR_CLOSE_SCRIPT,
    ),
}

# The two companions are placed beside Rico only while the screen is fully
# black.  Their separate, four-unit-clearance routes converge on distinct
# lanes at the retail door, then cross the X252..277 aperture one at a time.
# Every tuple is (X, Z, audited layer-0 triangle).
CHAPTER_FOUR_PRIVATE_STAGE_POSITIONS = {
    CHAPTER_FOUR_FEI_ENTITY: (-180, 8, 70),
    CHAPTER_FOUR_BART_ENTITY: (-180, -8, 70),
}
CHAPTER_FOUR_PRIVATE_APPROACH_ROUTES = {
    CHAPTER_FOUR_FEI_ENTITY: (
        (-138, 62, 50),
        (-132, 60, 47),
        (-8, 0, 40),
        (46, 0, 19),
        (86, -18, 22),
        (258, -166, 30),
    ),
    CHAPTER_FOUR_BART_ENTITY: (
        (-138, -62, 57),
        (-92, -62, 59),
        (-42, -12, 41),
        (6, 0, 39),
        (46, 0, 19),
        (86, -18, 22),
        (274, -166, 29),
    ),
}
CHAPTER_FOUR_PRIVATE_CROSS_ROUTES = {
    CHAPTER_FOUR_FEI_ENTITY: ((258, -216, 35), (258, -274, 37)),
    CHAPTER_FOUR_BART_ENTITY: ((271, -216, 35), (271, -274, 37)),
}
HAZARDOUS_DONOR_INIT_ENTITIES = {
    # Field 218 contains several mutually exclusive Hammer/cast variants.
    # Its retail manager e27 hides them according to story progress, but that
    # manager is deliberately retired in the anthology.  e4 is Suzarn, not
    # Hammer; retire her with every alternate and stage authentic Hammer e19
    # deterministically below.
    218: (4, 5, 6, 7, 20, 21, 22, 23, 24, 25, 27),
    # Model-less retail Cross controllers overlap anthology objectives/exits.
    # Retire them along with each field's story manager so the lower retail
    # entity ID cannot steal the player's interaction from the new hotspot.
    236: (13, 15, 16, 18, 19, 26, 28),
    # e23 clears persistent operand 0x020A; e26 deletes story cast members.
    237: (13, 16, 19, 20, 22, 23, 24, 26, 32),
    235: (4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
    232: (4, 6, 7, 8, 9, 10, 11, 12, 15, 16),
    # Field 298's retail Rico/Hammer memory actors are story-variable driven.
    # The anthology stages its own Rico and Fei, so none may leak into the
    # post-Hammer chapter from an imported save.
    298: (12, 13, 14, 16),
}

# Every required prop remapped during the full-room audit is backed by a
# visible donor node, not a bare-floor carrier.  Each tuple is
# (description, source node, model index, exact 16-byte node record,
# model byte size, model SHA-256).  The source validator pins these before
# any actor records are inserted into the header.
PLAYABLE_VISIBLE_PROP_SOURCE_PINS = {
    1: (
        (
            "bright window panes",
            7,
            0,
            bytes.fromhex("10 80 00 00 00 0A 00 00 00 00 00 00 00 00 00 00"),
            1_808,
            "ceb77528eb4dc4e1463ad0acb06a38f0f50b2a3106a49e164334bdc09c30f103",
        ),
        (
            "windowed house walls",
            27,
            20,
            bytes.fromhex("10 00 00 00 00 0A 00 00 00 00 00 00 00 00 14 00"),
            2_024,
            "4da8fa05a397ebc853242c4a5dc18879665218282de1de04878ac66f84cc824e",
        ),
        (
            "Anne's bed",
            13,
            6,
            bytes.fromhex("10 00 00 00 00 0A 00 00 00 00 00 00 00 00 06 00"),
            512,
            "cfb6aded3a452658ad4bc667b8edaac64e6ecc0ac38de6f43c1b5fe153bb6544",
        ),
        (
            "Anne's reading books",
            8,
            1,
            bytes.fromhex("10 00 00 00 00 0A 00 00 00 00 00 00 00 00 01 00"),
            420,
            "477b1271d6e07d862b8eacd6c8c1e9454f822c5794e76225674a32146cecc407",
        ),
        (
            "reading desk",
            15,
            8,
            bytes.fromhex("10 00 00 00 00 0A 00 00 00 00 00 00 00 00 08 00"),
            256,
            "11224ba088082a9ae6f540dba9f590c86c8c303fae86116eab6fb7c5d0ec2c30",
        ),
        (
            "cooking pots",
            9,
            2,
            bytes.fromhex("10 00 00 00 00 0A 00 00 00 00 00 00 00 00 02 00"),
            1_280,
            "0b805c97c72be9e4c14dda11dd0d791a429cf1baa259375ff9c81a8d42430c90",
        ),
        (
            "cooking canister",
            12,
            5,
            bytes.fromhex("10 00 00 00 00 0A 00 00 00 00 00 00 00 00 05 00"),
            684,
            "10b3b03e952059ca81367391ae99bf752b23644df915389f489ac16df52754e4",
        ),
        (
            "cooking counter",
            23,
            16,
            bytes.fromhex("10 00 00 00 00 0A 00 00 00 00 00 00 00 00 10 00"),
            972,
            "21d73fba477339c8e4c64062acfb243d72d82f2e30c4651cf62e1bdcaa115c3c",
        ),
        (
            "stonebell vase",
            11,
            4,
            bytes.fromhex("10 00 00 00 00 0A 00 00 00 00 00 00 00 00 04 00"),
            676,
            "727de36b7183880765d16e0421325929b65f7ffa090d7875f2c49f628c98bfdc",
        ),
        (
            "stonebell flowers",
            18,
            11,
            bytes.fromhex("00 00 00 00 00 0A 00 00 00 00 00 00 00 00 0B 00"),
            556,
            "49a93712d3558750cdc278c74b1454f11959aeb2b3b762aa9d446e0c3bfd7f2f",
        ),
        (
            "room heater",
            19,
            12,
            bytes.fromhex("10 00 00 00 00 0A 00 00 00 00 00 00 00 00 0C 00"),
            784,
            "f3f14d1fdd15d2918f5af5fc1aa6969703629b8856eea43c4c354dd74d2027fd",
        ),
        (
            "near water bucket",
            20,
            13,
            bytes.fromhex("10 00 00 00 00 0A 00 00 27 00 00 00 27 00 0D 00"),
            364,
            "c57f3f230eb183ae7ddd4f8233bf2e483fe0517ee876f9027c5fa730bcb128e6",
        ),
        (
            "far water bucket",
            24,
            13,
            bytes.fromhex("10 00 00 00 00 0A 00 00 0A 00 00 00 09 00 0D 00"),
            364,
            "c57f3f230eb183ae7ddd4f8233bf2e483fe0517ee876f9027c5fa730bcb128e6",
        ),
        (
            "closed house door",
            6,
            17,
            bytes.fromhex("80 02 00 00 00 0A 00 00 78 00 C6 FF 42 00 11 00"),
            136,
            "6be99f0f9132e627ec92d3119db511eb0082ca81046bd3de74eb07d37083da3b",
        ),
    ),
    2: (
        (
            "mantel clock",
            41,
            13,
            bytes.fromhex("10 00 00 00 00 0E 00 00 00 00 00 00 00 00 0D 00"),
            828,
            "a2eb442966237e8865400847e484bc41c54e82555b5d9b9decba788c213a1da0",
        ),
        (
            "Champion bedroom door",
            2,
            24,
            bytes.fromhex("90 02 00 00 00 0E 00 00 3E 00 00 00 8A FE 18 00"),
            172,
            "688a7e41612bb3c2ec19bb371f2a1e1b43073b2558697d5548bc1eb3fa62f1b9",
        ),
    ),
    3: (
        (
            "portrait wall",
            46,
            18,
            bytes.fromhex("10 80 00 00 00 08 00 00 00 00 00 00 00 00 12 00"),
            4_460,
            "325692eaa6dcfe7b97866fe1743f419758b2dc233bb703bf0ce663157e11c7f2",
        ),
        (
            "medical cabinet",
            41,
            13,
            bytes.fromhex("10 00 00 00 00 08 00 00 00 00 00 00 00 00 0D 00"),
            1_128,
            "e8cd7e2690d81b21f6b94e52d02c31648368bbb1cad402846072d5d775f767f7",
        ),
    ),
    4: (
        (
            "office archive cabinet",
            87,
            24,
            bytes.fromhex("10 02 00 00 00 04 00 00 00 00 00 00 00 00 18 00"),
            1_400,
            "a1b7cb57997a90c27416d9cc620bdece59927efcb2aaf5e8bf362f88473c4e1f",
        ),
        (
            "north vessel archive conduit",
            79,
            15,
            bytes.fromhex("10 02 00 00 00 04 00 00 00 00 00 00 00 00 0F 00"),
            14_480,
            "8f524712a6ffe9a31de56682d5f175928cc5b5942bd5046622934ba4f9734486",
        ),
        (
            "south vessel archive conduit",
            78,
            14,
            bytes.fromhex("10 02 00 00 00 04 00 00 00 00 00 00 00 00 0E 00"),
            14_480,
            "37072279d820a30357c5d22a6ee1b5baa8cf42c2f2e10ddbce22fe4dd8bfa8e4",
        ),
        (
            "Anne's file desk",
            94,
            31,
            bytes.fromhex("10 02 00 00 00 04 00 00 00 00 00 00 00 00 1F 00"),
            1_368,
            "7bbb304db6090c691f188c4f5a1c7ea80a3c81789238e895ae40550cabbc5d65",
        ),
        (
            "wall communication display",
            89,
            26,
            bytes.fromhex("10 02 00 00 00 04 00 00 00 00 00 00 00 00 1A 00"),
            1_912,
            "87e5426d56b5bfb80bd10d91c3a3e55e96cc31f239221b9d1f62e744d33b2492",
        ),
    ),
    6: (
        (
            "central control tower",
            18,
            0,
            bytes(16),
            4_584,
            "126a48db2c4c0e86165ab4a69913f44da2a0a657c2a7024307b0464f0921a5f0",
        ),
        (
            "northeast cabinet bank",
            19,
            1,
            bytes.fromhex("00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00"),
            2_336,
            "0881996d3bd055a439111aeddb93a8ac638dcae9e5342e1ff199ffdce74d71ad",
        ),
        (
            "southwest cabinet bank",
            20,
            2,
            bytes.fromhex("00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 00"),
            2_336,
            "5bd0ad48c113cce03c7d38a652b32fac2b271e14ba9f7e022ee26cbeea8dbe75",
        ),
    ),
    7: (
        *tuple(
            (
                f"hanging garment layer {model}",
                18 + model,
                model,
                bytes.fromhex(
                    f"10 00 00 00 00 0C 00 00 00 00 00 00 00 00 {model:02X} 00"
                ),
                188,
                digest,
            )
            for model, digest in (
                (2, "d3ff78f7bfe712e32f65b176dde5bf0e7fad75f01fae35ad24aefec84d84c431"),
                (3, "d8d6a19a6b4369c91e2afe9ebe8859cdcfa90700fb84bc3067dd2162cc90fcd5"),
                (4, "2977803ee063a38e3334681f28ee19308a496512e99148a0dfcbbf23c35552c3"),
                (5, "192557667cfe687305a16f5a59814b1b248b037ca82dbb8a7a7de7e5c1545ebf"),
                (6, "d36d4599f949e16a875f73cbc0970bc1fff8033f4583c85fc3cebceca4e0145f"),
                (7, "d00664cc0cda949a7e6236aefc14ca7f907a4d2460107f27c2d50cf477374c52"),
            )
        ),
        (
            "clothes rack",
            26,
            8,
            bytes.fromhex("00 00 00 00 00 0C 00 00 00 00 00 00 00 00 08 00"),
            1_540,
            "c0654627bd2ad8948cd517faf1deb0ba0706506cda559211e3304bd760f2debd",
        ),
        (
            "desktop effects",
            27,
            9,
            bytes.fromhex("10 00 00 00 00 0C 00 00 00 00 00 00 00 00 09 00"),
            4_216,
            "6d9d3fb3c2b8af00aec8926f3536275c559fce18ec79fb97fe690ee08078ae37",
        ),
        (
            "writing desk and bed rails",
            28,
            10,
            bytes.fromhex("10 00 00 00 00 0C 00 00 00 00 00 00 00 00 0A 00"),
            3_200,
            "7dfc7313c0e927c20684cc14951fcf42c0df8dcf270d9ed00486d3704e72fb68",
        ),
        (
            "bunks and chair",
            29,
            11,
            bytes.fromhex("10 00 00 00 00 0C 00 00 00 00 00 00 00 00 0B 00"),
            2_076,
            "87cd16ca37ebe7cdb1b255ef93c167b005f75b8e5c20a49146cb21bcdc6a54c3",
        ),
        (
            "tall locker",
            31,
            13,
            bytes.fromhex("10 00 00 00 00 0C 00 00 00 00 00 00 00 00 0D 00"),
            1_104,
            "84017268b143beda5d0156d5f1dbc98ca97a67c7b130c5c60596f22428943553",
        ),
    ),
}
INERT_HIDDEN_INIT = b"\xBC\x23\x2A\x00"
DISABLE_DIALOGUE_UPDATE = b"\x2A\x00"

OUTPUT_BIN_NAMES = {
    1: "Xenogears_Rico_Arc_Disc_1.bin",
    2: "Xenogears_Rico_Arc_Disc_2.bin",
}
OUTPUT_CUE_NAMES = {
    1: "Xenogears_Rico_Arc_Disc_1.cue",
    2: "Xenogears_Rico_Arc_Disc_2.cue",
}
OUTPUT_M3U_NAME = "Xenogears_Rico_Arc.m3u"


class RicoArcBuildError(RuntimeError):
    """Raised when a source, script, story document, or output is unsafe."""


@dataclass(frozen=True)
class Chapter:
    chapter_id: int
    title: str
    disc: int
    target_field: int
    donor_field: int
    music: int
    selection_exposition: str
    blocks: tuple[str, ...]
    source_path: Path


@dataclass(frozen=True)
class Replacement:
    canonical_id: int
    role: str
    data: bytes


@dataclass(frozen=True)
class ChapterOneAncillaryFields:
    """Logical destinations for Chapter 1's three automatic story fields.

    The standalone anthology retains its historical 376/377/378 allocation.
    A Disc 2 composition can supply a different mapping without mutating the
    module-level constants or accidentally applying Disc 2 dummy slots to the
    populated fields at the same logical numbers on Disc 1.
    """

    firewood: int = CHAPTER_ONE_FIREWOOD_FIELD
    aftermath: int = CHAPTER_ONE_AFTERMATH_FIELD
    funeral: int = CHAPTER_ONE_FUNERAL_FIELD

    def __post_init__(self) -> None:
        fields = {
            "firewood": self.firewood,
            "aftermath": self.aftermath,
            "funeral": self.funeral,
        }
        for role, field in fields.items():
            if type(field) is not int or not 0 <= field <= 0x7FFF:
                raise RicoArcBuildError(
                    f"Chapter 1 {role} field is outside 0..32767: {field!r}"
                )
        if len(set(fields.values())) != len(fields):
            raise RicoArcBuildError(
                f"Chapter 1 ancillary fields must be distinct: {fields}"
            )


DEFAULT_CHAPTER_ONE_ANCILLARY_FIELDS = ChapterOneAncillaryFields()
UNIFIED_DISC2_CHAPTER_ONE_ANCILLARY_FIELDS = ChapterOneAncillaryFields(
    firewood=64,
    aftermath=65,
    funeral=66,
)


def _chapter_one_ancillary_fields(
    value: ChapterOneAncillaryFields | Mapping[str, int] | None,
) -> ChapterOneAncillaryFields:
    """Normalize one public ancillary-field mapping with exact role names."""

    if value is None:
        return DEFAULT_CHAPTER_ONE_ANCILLARY_FIELDS
    if isinstance(value, ChapterOneAncillaryFields):
        return value
    if not isinstance(value, Mapping):
        raise RicoArcBuildError(
            "Chapter 1 ancillary fields must be a mapping or "
            "ChapterOneAncillaryFields"
        )
    expected = {"firewood", "aftermath", "funeral"}
    actual = set(value)
    if actual != expected:
        raise RicoArcBuildError(
            "Chapter 1 ancillary mapping keys must be exactly "
            f"{sorted(expected)}; got {sorted(actual)}"
        )
    return ChapterOneAncillaryFields(
        firewood=value["firewood"],
        aftermath=value["aftermath"],
        funeral=value["funeral"],
    )


@dataclass(frozen=True)
class HubMarker:
    """One luminous chapter memory placed on the Path of Sephirot."""

    chapter_id: int
    x: int
    z: int
    triangle: int


# Seven translucent memory lights form a navigable ring around the Path's
# central monolith.  The south entry remains clear so Rico always begins with
# control and deliberately approaches a chapter rather than landing inside an
# action carrier.
HUB_MARKERS = (
    HubMarker(1, 0, -650, 1),
    HubMarker(2, -469, -405, 0),
    HubMarker(3, -585, 145, 0),
    HubMarker(4, -260, 585, 0),
    HubMarker(5, 260, 585, 0),
    HubMarker(6, 585, 145, 1),
    HubMarker(7, 469, -405, 1),
)


DialogueRef = int | str
LockedDialogueState = tuple[tuple[int, ...], tuple[DialogueRef, ...]]
LockedDialogueStep = tuple[int, tuple[DialogueRef, ...]]


@dataclass(frozen=True)
class PlayableStage:
    """One idempotent, player-triggered beat of a chapter interaction."""

    bit: int
    dialogue: tuple[DialogueRef, ...]
    after_dialogue: tuple[DialogueRef, ...] = ()
    required_bits: tuple[int, ...] = ()
    locked_dialogue: tuple[DialogueRef, ...] = ()
    # Ordered reminders route to the first prerequisite bit still incomplete.
    locked_dialogue_steps: tuple[LockedDialogueStep, ...] = ()
    # Some interactions need to acknowledge every partial order explicitly.
    # Each entry maps the prerequisite bits already complete to its dialogue.
    locked_dialogue_states: tuple[LockedDialogueState, ...] = ()
    battle_configuration: int | None = None
    gear_battle: bool = False
    solo_rico: bool = False
    hide_entities_after: tuple[int, ...] = ()
    time_cut_after: bool = False
    private_departure_after: bool = False
    completes_chapter: bool = False
    choice_text: str | None = None
    accepted_selection: int = 1
    accepted_sound_id: int | None = None
    rejection_dialogue: tuple[DialogueRef, ...] = ()


@dataclass(frozen=True)
class PlayableInteraction:
    """A bounded Cross interaction anchored to audited walkmesh geometry."""

    name: str
    x: int
    z: int
    triangle: int
    stages: tuple[PlayableStage, ...]
    interaction_half_width: int = 0x04
    interaction_half_depth: int = 0x04
    requires_facing: bool = True
    activation_required_bits: tuple[int, ...] = ()
    hide_bound_actors_until_active: bool = False
    repeat_dialogue: tuple[DialogueRef, ...] = ()
    # A model-less controller may need to aim behind recessed wall geometry.
    # In that case this reachable point, rather than the invisible pivot, is
    # what ``triangle`` validates.  It must remain inside the action box.
    walkmesh_anchor: tuple[int, int] | None = None


@dataclass(frozen=True)
class PlayableExitTransition:
    """One multi-field story beat produced by a chapter's exit controller."""

    bit: int
    required_bits: tuple[int, ...]
    doorway_dialogue: tuple[DialogueRef, ...]
    firewood_dialogue: tuple[DialogueRef, ...]
    sickness_dialogue: tuple[DialogueRef, ...]
    loss_dialogue: tuple[DialogueRef, ...]
    funeral_dialogue: tuple[DialogueRef, ...]


@dataclass(frozen=True)
class PlayableTimedBit:
    """One non-objective state bit completed after a background delay."""

    bit: int
    trigger_bit: int
    frames: int


@dataclass(frozen=True)
class PlayableChapter:
    chapter_id: int
    interactions: tuple[PlayableInteraction, ...]
    exit_x: int
    exit_z: int
    exit_triangle: int
    required_bits: tuple[int, ...]
    exit_dialogue: tuple[DialogueRef, ...]
    exit_locked_steps: tuple[tuple[int, str], ...]
    exit_interaction_half_width: int = 0x04
    exit_interaction_half_depth: int = 0x04
    exit_requires_facing: bool = True
    completion_at_exit: bool = False
    optional_bits: tuple[int, ...] = ()
    timed_bits: tuple[PlayableTimedBit, ...] = ()
    exit_transition: PlayableExitTransition | None = None


PLAYABLE_STATE_VARIABLE = 0x07D0
PLAYABLE_INTRO_BIT = 0
PLAYABLE_BATTLE_MUSIC = 0x14
CHAPTER_ONE_MUSIC_ID = 0x08
PLAYABLE_ACTOR_GHOST_FLAGS = b"\x20\x01\x80"
PLAYABLE_ACTOR_SOLID_FLAGS = b"\x20\x0C\x80"
PLAYABLE_CONTROLLER_PARK_POSITION = (0x7000, 0x7000)
CHAPTER_ONE_STOVE_ON_BIT = 6
# Retail Zeboim computer controls use sound 0xF9 for their short mechanical
# power/key click. One isolated dispatch gives the stove a tactile ignition
# cue without copying any of the donor computer's later boot sequence.
CHAPTER_ONE_STOVE_IGNITION_SOUND_ID = 0xF9
# Retail's Blackmoon Forest campfire uses field SFX 0x111.  It loops until
# field SFX 0 is dispatched, so the stove helper gives it a short, deliberate
# ignition crackle and then releases the shared field-sound channel.
CHAPTER_ONE_STOVE_FIRE_SOUND_ID = 0x111
CHAPTER_ONE_FIELD_SOUND_STOP_ID = 0
CHAPTER_ONE_STOVE_CLICK_HOLD_FRAMES = 24
CHAPTER_ONE_STOVE_FIRE_HOLD_FRAMES = 60
CHAPTER_ONE_STOVE_AUDIO_HELPER_PC = 0x035F
CHAPTER_ONE_STOVE_AUDIO_HELPER_SOURCE = bytes.fromhex(
    "00 41 6D 03 C0 40 80 3C 06 04 5A 01 5B"
)
CHAPTER_ONE_STOVE_AUDIO_HELPER_CALL = bytes(
    (
        0x05,
        CHAPTER_ONE_STOVE_AUDIO_HELPER_PC & 0xFF,
        CHAPTER_ONE_STOVE_AUDIO_HELPER_PC >> 8,
    )
)
CHAPTER_ONE_HEATER_VALVE_BIT = 11
# These Chapter 1 bits track appliance state rather than player objectives.
# They deliberately remain outside ``required_bits`` / ``optional_bits``.
CHAPTER_ONE_KETTLE_BOILED_BIT = 12
CHAPTER_ONE_KETTLE_FILLED_BIT = 13
CHAPTER_ONE_KETTLE_BOIL_FRAMES = 15 * 60
# Inventory stacks in the checked standalone GameState.  Child Rico keeps only
# the two foods that fit this memory and the three keepsakes already equipped
# on his carrier record; every unrelated stack is hidden for the duration of
# Chapter 1 and restored when the player actually leaves it.
# ATEL opcodes 8B/8C/8D use the high byte of their object operand as the
# inventory family: 0 for ordinary items, 1 for weapons/armor, and 2 for
# accessories.  Keep the source IDs below unencoded so the baseline contract
# remains readable, then build the exact VM operands in one place.
CHAPTER_ONE_RETAINED_ITEM_STACKS = (
    (0x39, 10),  # Hob-Jerky
    (0x3F, 12),  # Bizfruit
)
CHAPTER_ONE_HIDDEN_ITEM_STACKS = (
    (0x52, 1),
    (0x32, 2),
    (0x31, 12),
    (0x02, 1),
    (0x51, 1),
    (0x53, 1),
    (0x01, 1),
    (0x06, 2),
    (0x09, 2),
    (0x35, 3),
    (0x1C, 3),
    (0x38, 2),
    (0x34, 2),
    (0x6B, 1),
    (0x5E, 1),
    (0x6A, 1),
)
CHAPTER_ONE_HIDDEN_WEAPON_STACKS = (
    (0x32, 1),
    (0x10, 1),
    (0x39, 1),
    (0x33, 1),
    (0x01, 1),
    (0x3A, 1),
    (0x1F, 1),
)
CHAPTER_ONE_HIDDEN_ACCESSORY_STACKS = (
    (0x6A, 1),  # Economether
    (0x62, 3),  # EtherStone
)
ATEL_WEAPON_INVENTORY_PREFIX = 0x0100
ATEL_ACCESSORY_INVENTORY_PREFIX = 0x0200
CHAPTER_ONE_HIDDEN_INVENTORY_OBJECT_STACKS = (
    *CHAPTER_ONE_HIDDEN_ITEM_STACKS,
    *(
        (ATEL_WEAPON_INVENTORY_PREFIX | item_id, quantity)
        for item_id, quantity in CHAPTER_ONE_HIDDEN_WEAPON_STACKS
    ),
    *(
        (ATEL_ACCESSORY_INVENTORY_PREFIX | item_id, quantity)
        for item_id, quantity in CHAPTER_ONE_HIDDEN_ACCESSORY_STACKS
    ),
)
if (
    {item_id for item_id, _quantity in CHAPTER_ONE_RETAINED_ITEM_STACKS}
    & {item_id for item_id, _quantity in CHAPTER_ONE_HIDDEN_ITEM_STACKS}
    or sum(quantity for _item_id, quantity in CHAPTER_ONE_HIDDEN_ITEM_STACKS)
    != 36
    or sum(quantity for _item_id, quantity in CHAPTER_ONE_HIDDEN_WEAPON_STACKS)
    != 7
    or sum(
        quantity
        for _item_id, quantity in CHAPTER_ONE_HIDDEN_ACCESSORY_STACKS
    )
    != 4
    or any(
        not 1 <= item_id <= 0xFF or not 1 <= quantity <= 99
        for item_id, quantity in (
            *CHAPTER_ONE_RETAINED_ITEM_STACKS,
            *CHAPTER_ONE_HIDDEN_ITEM_STACKS,
            *CHAPTER_ONE_HIDDEN_WEAPON_STACKS,
            *CHAPTER_ONE_HIDDEN_ACCESSORY_STACKS,
        )
    )
):
    raise RuntimeError("Chapter 1 inventory contract is invalid")
PLAYABLE_NEXT_OR_HUB_CHOICE = (
    "<Opcode:01:FF>Where will Rico go?\n"
    "     Continue to Next Chapter\n"
    "     Return to Chapter Select<Close>"
)
PLAYABLE_FINAL_HUB_CHOICE = (
    "Rico's Arc is complete.<New><Opcode:01:FF>Where will Rico go?\n"
    "     Return to Chapter Select\n"
    "     Remain Here<Close>"
)


def _locked_state(
    completed_bits: Sequence[int],
    *dialogue: DialogueRef,
) -> LockedDialogueState:
    return tuple(completed_bits), tuple(dialogue)


def _locked_step(bit: int, *dialogue: DialogueRef) -> LockedDialogueStep:
    return bit, tuple(dialogue)


def _stage(
    bit: int,
    *dialogue: DialogueRef,
    choice: str | None = None,
    accepted: int = 1,
    accepted_sound: int | None = None,
    rejected: Sequence[DialogueRef] = (),
    after: Sequence[DialogueRef] = (),
    required: Sequence[int] = (),
    locked: Sequence[DialogueRef] = (),
    locked_steps: Sequence[LockedDialogueStep] = (),
    locked_states: Sequence[LockedDialogueState] = (),
    battle: int | None = None,
    gear: bool = False,
    solo_rico: bool = False,
    hide_after: Sequence[int] = (),
    time_cut: bool = False,
    private_departure: bool = False,
    completes: bool = False,
) -> PlayableStage:
    return PlayableStage(
        bit=bit,
        dialogue=tuple(dialogue),
        choice_text=choice,
        accepted_selection=accepted,
        accepted_sound_id=accepted_sound,
        rejection_dialogue=tuple(rejected),
        after_dialogue=tuple(after),
        required_bits=tuple(required),
        locked_dialogue=tuple(locked),
        locked_dialogue_steps=tuple(locked_steps),
        locked_dialogue_states=tuple(locked_states),
        battle_configuration=battle,
        gear_battle=gear,
        solo_rico=solo_rico,
        hide_entities_after=tuple(hide_after),
        time_cut_after=time_cut,
        private_departure_after=private_departure,
        completes_chapter=completes,
    )


def _playable_chapter_contract(chapter_id: int) -> PlayableChapter:
    """Return the first playable reconstruction contract for one chapter.

    These are intentionally field interactions rather than a linear list of
    text boxes.  Integer dialogue references address the authored chapter;
    strings are short diegetic action or examination lines appended at build time.
    Bracketed prose from the screenplay draft is never routed to the player.
    """

    if chapter_id == 1:
        return PlayableChapter(
            chapter_id=1,
            interactions=(
                PlayableInteraction(
                    "settlement window",
                    CHAPTER_ONE_SETTLEMENT_WINDOW_POSITION[0],
                    CHAPTER_ONE_SETTLEMENT_WINDOW_POSITION[1],
                    CHAPTER_ONE_SETTLEMENT_WINDOW_POSITION[2],
                    (),
                    interaction_half_width=(
                        CHAPTER_ONE_SETTLEMENT_WINDOW_INTERACTION_HALF_WIDTH
                    ),
                    interaction_half_depth=(
                        CHAPTER_ONE_SETTLEMENT_WINDOW_INTERACTION_HALF_DEPTH
                    ),
                    requires_facing=True,
                    repeat_dialogue=(2,),
                    walkmesh_anchor=(
                        CHAPTER_ONE_SETTLEMENT_WINDOW_WALKMESH_ANCHOR
                    ),
                ),
                PlayableInteraction(
                    "gate window",
                    CHAPTER_ONE_GATE_WINDOW_POSITION[0],
                    CHAPTER_ONE_GATE_WINDOW_POSITION[1],
                    CHAPTER_ONE_GATE_WINDOW_POSITION[2],
                    (),
                    interaction_half_width=(
                        CHAPTER_ONE_GATE_WINDOW_INTERACTION_HALF_WIDTH
                    ),
                    interaction_half_depth=(
                        CHAPTER_ONE_GATE_WINDOW_INTERACTION_HALF_DEPTH
                    ),
                    requires_facing=True,
                    repeat_dialogue=(3,),
                    walkmesh_anchor=CHAPTER_ONE_GATE_WINDOW_WALKMESH_ANCHOR,
                ),
                PlayableInteraction(
                    "cold window",
                    CHAPTER_ONE_WINDOW_POSITION[0],
                    CHAPTER_ONE_WINDOW_POSITION[1],
                    CHAPTER_ONE_WINDOW_POSITION[2],
                    (),
                    interaction_half_width=CHAPTER_ONE_WINDOW_INTERACTION_HALF_WIDTH,
                    interaction_half_depth=CHAPTER_ONE_WINDOW_INTERACTION_HALF_DEPTH,
                    requires_facing=True,
                    repeat_dialogue=(
                        "Rico looks through the glass at the weathered houses "
                        "of the poor settlement on Kislev's outskirts. Beyond "
                        "them, the Imperial Capital fades into the cold haze."
                        "<Close>",
                    ),
                    walkmesh_anchor=(
                        CHAPTER_ONE_WINDOW_SLOT_ONE_EDGE_ENGINE_POSITION
                    ),
                ),
                PlayableInteraction(
                    "room heater",
                    CHAPTER_ONE_HEATER_POSITION[0],
                    CHAPTER_ONE_HEATER_POSITION[1],
                    CHAPTER_ONE_HEATER_POSITION[2],
                    (
                        _stage(
                            CHAPTER_ONE_HEATER_VALVE_BIT,
                            "A low fire glows inside the round iron woodstove. "
                            "Its valve is nearly closed, holding back the heat."
                            "<Close>",
                            choice=(
                                "<Opcode:01:FF>Open the valve?\n"
                                "     Open Valve\n"
                                "     Leave It Closed<Close>"
                            ),
                            accepted=1,
                            rejected=(
                                "Rico leaves the valve closed for now.<Close>",
                            ),
                            after=(
                                "Rico opens the valve. The fire takes a deeper "
                                "breath, and more heat spreads through the house."
                                "<Close>",
                            ),
                            required=(2,),
                            locked=(
                                "A low fire glows inside the round iron woodstove. "
                                "Its valve is nearly closed, holding back the heat."
                                "<Close>",
                            ),
                        ),
                    ),
                    interaction_half_width=CHAPTER_ONE_HEATER_INTERACTION_HALF_WIDTH,
                    interaction_half_depth=CHAPTER_ONE_HEATER_INTERACTION_HALF_DEPTH,
                    requires_facing=True,
                    walkmesh_anchor=(
                        CHAPTER_ONE_HEATER_SLOT_ONE_ENGINE_POSITION
                    ),
                    repeat_dialogue=(
                        "The open valve feeds the round iron woodstove, and "
                        "steady warmth spreads through the house.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "stonebell vase",
                    CHAPTER_ONE_FLOWER_VASE_POSITION[0],
                    CHAPTER_ONE_FLOWER_VASE_POSITION[1],
                    CHAPTER_ONE_FLOWER_VASE_POSITION[2],
                    (
                        _stage(
                            7,
                            "Rico tips the ladle slowly, giving the stonebell "
                            "a drink. Its pale blue bells lift above the damp "
                            "soil.<Close>",
                            after=(
                                24,
                                25,
                            ),
                            required=(1,),
                            locked=(
                                "A small blue flower rises from a rusty orange "
                                "clay vase. Its pale blue bells hang over dry "
                                "soil."
                                "<Close>",
                            ),
                        ),
                    ),
                    interaction_half_width=(
                        CHAPTER_ONE_FLOWER_VASE_INTERACTION_HALF_WIDTH
                    ),
                    interaction_half_depth=(
                        CHAPTER_ONE_FLOWER_VASE_INTERACTION_HALF_DEPTH
                    ),
                    requires_facing=False,
                    repeat_dialogue=(
                        "The stonebell's pale blue bells lift above the damp "
                        "soil.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "water buckets",
                    CHAPTER_ONE_WATER_BUCKET_POSITION[0],
                    CHAPTER_ONE_WATER_BUCKET_POSITION[1],
                    CHAPTER_ONE_WATER_BUCKET_POSITION[2],
                    (
                        _stage(
                            3,
                            "Rico dips the ladle into the nearer bucket and "
                            "gathers a ladleful of clear water.<Close>",
                            required=(2,),
                            locked=(
                                "Two dented water buckets stand underneath the "
                                "window. Both hold clear water. A ladle rests "
                                "across the nearer rim.<Close>",
                            ),
                        ),
                        _stage(
                            1,
                            "Rico dips the ladle into the same bucket again and "
                            "lifts a careful scoop for the stonebell.<Close>",
                            required=(6,),
                            locked=(
                                "<Rico>\nI need to turn on the stove before I "
                                "take water for the flower.<Close>",
                            ),
                        ),
                    ),
                    interaction_half_width=(
                        CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_WIDTH
                    ),
                    interaction_half_depth=(
                        CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_DEPTH
                    ),
                    requires_facing=False,
                    repeat_dialogue=(
                        "The ladle rests across the bucket. Rico has taken all "
                        "the water Anne asked for.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "Anne's bedside",
                    CHAPTER_ONE_ANNA_INTERACTION_POSITION[0],
                    CHAPTER_ONE_ANNA_INTERACTION_POSITION[1],
                    CHAPTER_ONE_ANNA_INTERACTION_POSITION[2],
                    (
                        _stage(
                            2,
                            4,
                            5,
                            6,
                            7,
                            8,
                            9,
                            10,
                            after=(21,),
                        ),
                        _stage(
                            4,
                            "<Rico>\nI brought your cup, Mom.<New>Anne\nThank "
                            "you, Rico.<Close>",
                            "Rico brings Anne the cup and steadies it "
                            "while she takes a small drink.<New>She presses the "
                            "cloth to her mouth. When she lowers the cloth, "
                            "Rico sees blood.<Close>",
                            12,
                            13,
                            14,
                            15,
                            16,
                            17,
                            18,
                            26,
                            27,
                            28,
                            required=(
                                3,
                                CHAPTER_ONE_STOVE_ON_BIT,
                                1,
                                7,
                                CHAPTER_ONE_HEATER_VALVE_BIT,
                                CHAPTER_ONE_KETTLE_BOILED_BIT,
                                10,
                            ),
                            locked_steps=(
                                _locked_step(
                                    3,
                                    "Anne\nThe bucket and ladle are in the "
                                    "corner, my sweet boy.<New>Bring water for "
                                    "the kettle first.<Close>",
                                ),
                                _locked_step(
                                    CHAPTER_ONE_STOVE_ON_BIT,
                                    "Anne\nThe stove is still cold, Rico.<New>Turn "
                                    "it on beneath the kettle so the water can "
                                    "heat.<Close>",
                                ),
                                _locked_step(
                                    1,
                                    "Anne\nThe kettle can heat while you take "
                                    "another scoop from the bucket.<New>The "
                                    "stonebell needs a drink.<Close>",
                                ),
                                _locked_step(
                                    7,
                                    "Anne\nYou have the water, Rico.<New>The "
                                    "stonebell's soil is still dry.<Close>",
                                ),
                                _locked_step(
                                    CHAPTER_ONE_HEATER_VALVE_BIT,
                                    "Anne\nThe woodstove valve is still nearly "
                                    "closed, Rico.<New>Open it so more heat can "
                                    "spread through the house.<Close>",
                                ),
                                _locked_step(
                                    CHAPTER_ONE_KETTLE_BOILED_BIT,
                                    "Anne\nThe flower has its water now.<New>Give "
                                    "the kettle a little more time to boil, my "
                                    "sweet boy.<Close>",
                                ),
                                _locked_step(
                                    10,
                                    "Anne\nThe water should be ready now, Rico."
                                    "<New>Please finish the tea and bring it "
                                    "to me.<Close>",
                                ),
                            ),
                        ),
                    ),
                    interaction_half_width=CHAPTER_ONE_ANNA_INTERACTION_HALF_WIDTH,
                    interaction_half_depth=CHAPTER_ONE_ANNA_INTERACTION_HALF_DEPTH,
                    requires_facing=False,
                    repeat_dialogue=(29,),
                ),
                PlayableInteraction(
                    "reading desk",
                    CHAPTER_ONE_READING_DESK_POSITION[0],
                    CHAPTER_ONE_READING_DESK_POSITION[1],
                    CHAPTER_ONE_READING_DESK_POSITION[2],
                    (
                        _stage(
                            8,
                            "Rico inspects The Emerald Traveler, a book his "
                            "mother has been reading with him.<New>It tells of "
                            "a heroine whose journey will be key to saving the "
                            "world.<Close>",
                        ),
                    ),
                    interaction_half_width=(
                        CHAPTER_ONE_READING_DESK_INTERACTION_HALF_WIDTH
                    ),
                    interaction_half_depth=(
                        CHAPTER_ONE_READING_DESK_INTERACTION_HALF_DEPTH
                    ),
                    requires_facing=True,
                    repeat_dialogue=(
                        "The Emerald Traveler lies open where Rico and his "
                        "mother stopped reading.<New>Its heroine's journey "
                        "will be key to saving the world.<Close>",
                    ),
                    walkmesh_anchor=(
                        CHAPTER_ONE_READING_DESK_SLOT_ONE_ENGINE_POSITION
                    ),
                ),
                PlayableInteraction(
                    "cooking counter",
                    CHAPTER_ONE_COOKING_COUNTER_POSITION[0],
                    CHAPTER_ONE_COOKING_COUNTER_POSITION[1],
                    CHAPTER_ONE_COOKING_COUNTER_POSITION[2],
                    (
                        _stage(
                            CHAPTER_ONE_STOVE_ON_BIT,
                            "Rico fills the kettle with water from the ladle."
                            "<Close>",
                            choice=(
                                "<Opcode:01:FF>Turn on the stove?\n"
                                "     Turn It On\n"
                                "     Leave It Off<Close>"
                            ),
                            accepted=1,
                            accepted_sound=CHAPTER_ONE_STOVE_IGNITION_SOUND_ID,
                            rejected=(
                                "Rico leaves the stove off for now.<Close>",
                            ),
                            after=(
                                "Rico turns on the cooking stove. Heat begins "
                                "to build beneath the kettle.<Close>",
                                22,
                                23,
                            ),
                            required=(3,),
                            locked=(
                                "A worn-down iron cooking stove stands beside "
                                "the counter. The empty kettle rests on its "
                                "cold cooktop.<New>A small chipped cup sits "
                                "beside the jar of dried medicinal herbs."
                                "<Close>",
                            ),
                        ),
                        _stage(
                            10,
                            "The kettle begins to whistle. The water has boiled."
                            "<New>Rico takes a pinch of dried medicinal herbs "
                            "from the jar on the counter and places it into the "
                            "cup.<New>He pours in the steaming "
                            "water, then sets the kettle back on the cooktop."
                            "<New>The herbal tea is ready for Anne.<Close>",
                            required=(7, CHAPTER_ONE_KETTLE_BOILED_BIT),
                            locked_states=(
                                _locked_state(
                                    (),
                                    "The cooking stove is on. The water is "
                                    "heating. Rico still has the flower to "
                                    "water.<Close>",
                                ),
                                _locked_state(
                                    (7,),
                                    "The cooking stove is on. The water is "
                                    "heating, but it has not boiled yet.<Close>",
                                ),
                                _locked_state(
                                    (CHAPTER_ONE_KETTLE_BOILED_BIT,),
                                    "The kettle has boiled, but Rico still has "
                                    "the flower to water.<Close>",
                                ),
                            ),
                        ),
                        _stage(
                            9,
                            "A dented pot and two chipped bowls sit on the "
                            "narrow counter. Anne taught Rico how to make a "
                            "handful of grain feed them both.<Close>",
                            "<Rico>\nYou always give me the fuller bowl."
                            "<Close>",
                            "Anne\nAnd you always put some back when you "
                            "think I am not looking.<Close>",
                            "<Rico>\nThen give me the smaller bowl.<Close>",
                            "Anne\nAnd miss this argument?<Close>",
                        ),
                    ),
                    interaction_half_width=(
                        CHAPTER_ONE_COOKING_COUNTER_INTERACTION_HALF_WIDTH
                    ),
                    interaction_half_depth=(
                        CHAPTER_ONE_COOKING_COUNTER_INTERACTION_HALF_DEPTH
                    ),
                    requires_facing=False,
                    repeat_dialogue=(
                        "Two chipped bowls sit beside the dented pot. Neither "
                        "bowl stays fuller for long.<Close>",
                    ),
                ),
            ),
            exit_x=CHAPTER_ONE_EXIT_POSITION[0],
            exit_z=CHAPTER_ONE_EXIT_POSITION[1],
            exit_triangle=CHAPTER_ONE_EXIT_POSITION[2],
            required_bits=(1, 2, 3, 4, 5, 6, 7, 10, CHAPTER_ONE_HEATER_VALVE_BIT),
            optional_bits=(8, 9),
            timed_bits=(
                PlayableTimedBit(
                    bit=CHAPTER_ONE_KETTLE_BOILED_BIT,
                    trigger_bit=CHAPTER_ONE_STOVE_ON_BIT,
                    frames=CHAPTER_ONE_KETTLE_BOIL_FRAMES,
                ),
            ),
            exit_dialogue=(20,),
            exit_locked_steps=(
                (
                    2,
                    "<Rico>\nI can't leave Mom right now.<Close>",
                ),
                (
                    3,
                    "<Rico>\nMom asked me to fill the kettle.<New>The bucket "
                    "and ladle are in the corner.<Close>",
                ),
                (
                    6,
                    "<Rico>\nI need to turn on the stove so Mom's water can "
                    "boil.<Close>",
                ),
                (
                    1,
                    "<Rico>\nMom asked for another scoop from the same bucket."
                    "<New>It is for the stonebell.<Close>",
                ),
                (
                    7,
                    "<Rico>\nI have water in the ladle.<New>The stonebell's "
                    "soil is still dry.<Close>",
                ),
                (
                    CHAPTER_ONE_HEATER_VALVE_BIT,
                    "<Rico>\nThe woodstove valve is still nearly closed."
                    "<New>I need to open it so the room stays warm for "
                    "Mom.<Close>",
                ),
                (
                    10,
                    "<Rico>\nI still need to finish Mom's tea at the stove."
                    "<New>I need to put a pinch of medicinal herbs in the cup."
                    "<New>Then I can pour in the hot water and bring it to "
                    "Mom.<Close>",
                ),
                (
                    4,
                    "<Rico>\nI have Mom's cup of hot tea.<New>I should take "
                    "it to her now.<Close>",
                ),
            ),
            exit_interaction_half_width=CHAPTER_ONE_EXIT_INTERACTION_HALF_WIDTH,
            exit_interaction_half_depth=CHAPTER_ONE_EXIT_INTERACTION_HALF_DEPTH,
            exit_requires_facing=False,
            completion_at_exit=True,
            exit_transition=PlayableExitTransition(
                bit=5,
                required_bits=(
                    2,
                    3,
                    6,
                    1,
                    7,
                    CHAPTER_ONE_HEATER_VALVE_BIT,
                    10,
                    4,
                ),
                doorway_dialogue=(
                    "<Rico>\nMom... how come I don't have a dad?<Close>",
                    "Anne\nRico, you do have a father.<New><Rico>\nThen where "
                    "is he?<New>Anne\nHe's... away.<New>Fighting in the war."
                    "<New><Rico>\nIs he ever coming back?<New>Anne\nW-Well... "
                    "that is...<New>I don't know.<New>Anne\nBut your father "
                    "is a great man, Rico.<New>And someday...<New>I know "
                    "you'll follow in his footsteps.<Close>",
                ),
                # Block 30 is narrated over the live exterior gathering beat.
                firewood_dialogue=(30,),
                sickness_dialogue=(31, 32, 33, 34, 35, 36),
                loss_dialogue=(37, 38, 39, 40),
                funeral_dialogue=(41, 42, 43, 44),
            ),
        )

    if chapter_id == 2:
        return PlayableChapter(
            chapter_id=2,
            interactions=(
                PlayableInteraction(
                    "mantel clock",
                    115,
                    -187,
                    62,
                    (
                        _stage(
                            7,
                            "<Rico>\nThe mantel clock came with the "
                            "Champion's room.<New>Three years up here, and it "
                            "still keeps the arena's schedule better than any "
                            "guard.<Close>",
                        ),
                    ),
                    repeat_dialogue=(
                        "<Rico>\nThe clock marks time by the arena's "
                        "bells.<New>In D Block, even the hours belong to "
                        "Battling.<Close>",
                    ),
                    interaction_half_width=0x06,
                    interaction_half_depth=0x08,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "Hammer",
                    60,
                    -49,
                    133,
                    (
                        _stage(
                            1,
                            2,
                            3,
                            4,
                            5,
                        ),
                        _stage(
                            4,
                            13,
                            14,
                            15,
                            16,
                            required=(3,),
                            locked=(
                                "Hammer\nMaster Rico, your Group League "
                                "bout is waiting.<New>I'll have the sewer "
                                "report ready when you return.<Close>",
                            ),
                            after=(
                                "<Rico>\nRedrum is dead. It killed the five "
                                "Battlers.<New>This wound can wait. The Finals "
                                "won't.<Close>",
                            ),
                            time_cut=True,
                        ),
                    ),
                    repeat_dialogue=(
                        "Hammer\nMaster Rico, the Finals will start "
                        "soon.<New>Fei is waiting for you across the "
                        "room.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "Fei",
                    -70,
                    181,
                    39,
                    (
                        _stage(
                            2,
                            6,
                            7,
                            8,
                            9,
                            10,
                            11,
                            after=(
                                "Hammer\nBro made rank A after that "
                                "Baptism.<New>Now he's entered Battling--"
                                "says the special pardon is his way out of "
                                "D Block.<Close>",
                            ),
                            required=(1,),
                            locked=(
                                "<Rico>\nHammer is still coming upstairs "
                                "with news from the infirmary.<Close>",
                            ),
                        ),
                        _stage(
                            5,
                            18,
                            19,
                            20,
                            21,
                            22,
                            required=(4,),
                            locked=(
                                "<Rico>\nThe title defense and Hammer's "
                                "sewer report come first.<Close>",
                            ),
                        ),
                    ),
                    activation_required_bits=(1,),
                    hide_bound_actors_until_active=True,
                    repeat_dialogue=(
                        "<Fei>\nI'll meet you in the Finals, "
                        "Rico.<New>I won't hold back.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "arena passage",
                    -213,
                    -73,
                    82,
                    (
                        _stage(
                            3,
                            "<Rico>\nAnother Group League title "
                            "defense.<New>Stier is waiting beyond the arena "
                            "passage.<Close>",
                            choice=(
                                "<Opcode:01:FF>Enter the Battling arena?\n"
                                "     Enter\n"
                                "     Not yet<Close>"
                            ),
                            accepted=1,
                            rejected=(
                                "<Rico>\nStier can wait until I'm "
                                "ready.<Close>",
                            ),
                            after=(
                                "<Rico>\nAnother challenger down.<New>The "
                                "title stays with me.<Close>",
                            ),
                            required=(2,),
                            locked=(
                                "<Rico>\nThere's business in the Champion's "
                                "room before my next title defense.<Close>",
                            ),
                            battle=6,
                            gear=True,
                            solo_rico=True,
                        ),
                        _stage(
                            6,
                            "<Rico>\nFei made it to the Finals.<New>Now he "
                            "gets the fight he asked for.<Close>",
                            choice=(
                                "<Opcode:01:FF>Enter the Finals League?\n"
                                "     Enter\n"
                                "     Not yet<Close>"
                            ),
                            accepted=1,
                            rejected=(
                                "<Rico>\nThe Finals begin when both of us "
                                "are ready.<Close>",
                            ),
                            after=(
                                "ANNOUNCER\nFIFTH ROUND COMPLETE\nWINNER: FEI "
                                "FONG WONG<Close>",
                                24,
                                25,
                            ),
                            required=(5,),
                            locked=(
                                "<Rico>\nFei and I have unfinished business "
                                "before the Finals begin.<Close>",
                            ),
                            time_cut=True,
                        ),
                    ),
                    repeat_dialogue=(
                        "<Rico>\nFei won the Finals. The title is "
                        "his.<New>Stier and I still have a Group League "
                        "bout to finish.<Close>",
                    ),
                    interaction_half_width=0x0A,
                    interaction_half_depth=0x04,
                    requires_facing=False,
                ),
            ),
            exit_x=-304,
            exit_z=9,
            exit_triangle=84,
            required_bits=(1, 2, 3, 4, 5, 6),
            exit_dialogue=(
                27,
                28,
                "<Rico>\nStier hit the Kaiser's box.<New>I got out before "
                "the guards reached the wreck.<Close>",
                30,
                31,
                32,
                33,
                34,
                35,
                37,
            ),
            exit_locked_steps=(
                (
                    1,
                    "<Rico>\nHammer was calling from downstairs.<New>I "
                    "should hear his news before I leave.<Close>",
                ),
                (
                    2,
                    "<Rico>\nSuzarn is bringing the new prisoner "
                    "upstairs.<New>I need to deal with his Baptism.<Close>",
                ),
                (
                    3,
                    "<Rico>\nMy Group League title defense is "
                    "next.<New>Stier is waiting at the arena passage.<Close>",
                ),
                (
                    4,
                    "<Rico>\nHammer promised the full report on the "
                    "sewer murders after my bout.<Close>",
                ),
                (
                    5,
                    "<Rico>\nFei is waiting across the room.<New>We need "
                    "to settle the sewer case and the Finals.<Close>",
                ),
                (
                    6,
                    "<Rico>\nFei is ready for the Finals.<New>I should meet "
                    "him at the arena passage.<Close>",
                ),
            ),
            completion_at_exit=True,
            optional_bits=(7,),
        )

    if chapter_id == 3:
        return PlayableChapter(
            chapter_id=3,
            interactions=(
                PlayableInteraction(
                    "family seal",
                    275,
                    2,
                    104,
                    (
                        _stage(
                            1,
                            2,
                            after=(
                                "SYSTEM\nHOUSEHOLD PORTRAIT INDEX: "
                                "AVAILABLE\nMEDICAL LEDGER: AVAILABLE<Close>",
                            ),
                        ),
                        _stage(
                            4,
                            "SYSTEM\nTWO SEALED RECORDS ARE READY FOR "
                            "COMPARISON.<Close>",
                            choice=(
                                "<Opcode:01:FF>Cross-check which records?\n"
                                "     Portrait index\n"
                                "     Medical ledger\n"
                                "     Both records<Close>"
                            ),
                            accepted=3,
                            rejected=(
                                "<Citan>\nOne record alone could be dismissed "
                                "as an error.<New>We must compare both while "
                                "the family seal is active.<Close>",
                            ),
                            after=(
                                "SYSTEM\nANNE BANDERAS: HOUSEHOLD IDENTITY "
                                "CONFIRMED\nRICARDO BANDERAS: DIRECT FAMILY "
                                "MATCH<Close>",
                                "<Rico>\nThere it is. No rumor. No broken "
                                "scanner.<New>This room knows exactly who I "
                                "am.<Close>",
                                "The family door opens. Sigmund enters. The "
                                "palace guard waits outside.<Close>",
                            ),
                            required=(2, 3),
                            locked_states=(
                                _locked_state(
                                    (),
                                    "<Citan>\nWe need both the portrait index "
                                    "and medical ledger before the family seal "
                                    "can prove the match.<Close>",
                                ),
                                _locked_state(
                                    (2,),
                                    "<Citan>\nThe portrait index is authentic. "
                                    "We still need Anne's medical ledger "
                                    "before the seal can prove the match.<Close>",
                                ),
                                _locked_state(
                                    (3,),
                                    "<Citan>\nThe medical ledger is authentic. "
                                    "We still need Anne's portrait index "
                                    "before the seal can prove the match.<Close>",
                                ),
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "SYSTEM\nDIRECT FAMILY MATCH PRESERVED IN "
                        "HOUSEHOLD ARCHIVE<Close>",
                    ),
                ),
                PlayableInteraction(
                    "Anne's portrait",
                    -169,
                    -254,
                    11,
                    (
                        _stage(
                            2,
                            3,
                            4,
                            5,
                            required=(1,),
                            locked=(
                                "<Rico>\nThe family seal must open the "
                                "archive before I can search Mother's "
                                "portrait index.<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "<Rico>\nMother was here before Committee B erased "
                        "her from the palace record.<Close>",
                    ),
                    interaction_half_width=0x0A,
                    interaction_half_depth=0x04,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "medical cabinet",
                    -170,
                    96,
                    34,
                    (
                        _stage(
                            3,
                            "The cabinet bears Anne Banderas's name. Its "
                            "treatment ledger was sealed under an Ethos "
                            "medical index.<Close>",
                            "<Citan>\nThe patient number matches the prenatal "
                            "record.<New>Whoever removed the paper ledger "
                            "left its index behind.<Close>",
                            required=(1,),
                            locked=(
                                "<Citan>\nThe family seal must authorize "
                                "the archive before we examine Anne's "
                                "medical index.<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "MEDICAL INDEX\nANNE BANDERAS\nPRENATAL TREATMENT "
                        "RECORD: SEALED<Close>",
                    ),
                    interaction_half_width=0x06,
                    interaction_half_depth=0x08,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "Sigmund",
                    0,
                    223,
                    38,
                    (
                        _stage(
                            5,
                            7,
                            8,
                            9,
                            10,
                            11,
                            12,
                            13,
                            15,
                            required=(4,),
                            locked=(
                                "<Rico>\nI need the archive's proof before "
                                "I confront the Kaiser.<Close>",
                            ),
                        ),
                    ),
                    activation_required_bits=(4,),
                    hide_bound_actors_until_active=True,
                    repeat_dialogue=(
                        "Sigmund\nThe guard is waiting outside.<New>This room "
                        "will be sealed pending an Imperial review.<Close>",
                    ),
                ),
            ),
            exit_x=0,
            exit_z=-289,
            exit_triangle=42,
            required_bits=(1, 2, 3, 4, 5),
            exit_dialogue=(
                "Palace guards return Rico to D Block. Citan's copy of "
                "the family index survives the seal.<Close>",
                17,
                "CHAPTER 3 COMPLETE<Close>",
            ),
            exit_locked_steps=(
                (
                    1,
                    "The family seal waits beside the closed archive door. "
                    "Its reader is dark.<Close>",
                ),
                (
                    2,
                    "<Rico>\nMother's portrait index may confirm who lived "
                    "in this room.<Close>",
                ),
                (
                    3,
                    "<Citan>\nThe medical index is the second independent "
                    "record we need.<Close>",
                ),
                (
                    4,
                    "<Rico>\nBoth records are ready.<New>I should cross-check "
                    "them at the family seal.<Close>",
                ),
                (
                    5,
                    "<Rico>\nSigmund is here.<New>He will answer for what "
                    "this room recognized.<Close>",
                ),
            ),
            completion_at_exit=True,
        )

    if chapter_id == 4:
        sigmund_stages = (
            _stage(
                4,
                11,
                after=(
                    *range(14, 49),
                ),
                required=(1, 2, 3),
                locked=(
                    "Sigmund\nFinish tracing the three archive records. "
                    "Then I will answer you without guards or office.<Close>",
                ),
                hide_after=(1, 4),
                time_cut=True,
                private_departure=True,
            ),
            _stage(
                5,
                "Sigmund sets a worn file on the desk but does not offer "
                "it to Rico.<Close>",
                *range(50, 58),
                "Beside Anne's file, the Memento Pendant remains on "
                "Sigmund's desk. Rico looks at it, then turns away.<Close>",
                *range(59, 78),
                required=(4,),
                locked=(
                    "The file remains sealed beside the family archive.<Close>",
                ),
            ),
            _stage(
                6,
                "Rico steps closer. Sigmund does not look away.<Close>",
                *range(79, 90),
                "Rico's fist rises, then comes down against the desk. The "
                "wood groans beneath it.<Close>",
                *range(91, 115),
                required=(5,),
                locked=(
                    "Sigmund\nRead the medical file first.<New>You asked for "
                    "the rest of the truth.<Close>",
                ),
            ),
            _stage(
                7,
                "For a long moment, only the machinery inside the wall can "
                "be heard.<Close>",
                *range(116, 138),
                required=(6,),
                locked=(
                    "<Rico>\nHe admitted what he chose.<New>Now he is going "
                    "to hear what that choice did to Kislev.<Close>",
                ),
            ),
            _stage(
                8,
                *range(138, 143),
                "Sigmund crosses to the communication panel and stops with "
                "his hand above the switch.<Close>",
                *range(144, 150),
                "Rico searches Sigmund's face for hesitation.<Close>",
                *range(151, 156),
                required=(7,),
                locked=(
                    "Sigmund\nYou told me what Kislev must change.<New>There "
                    "is one answer left to give you.<Close>",
                ),
            ),
        )
        return PlayableChapter(
            chapter_id=4,
            interactions=(
                PlayableInteraction(
                    "office archive cabinet",
                    121,
                    -110,
                    20,
                    (
                        _stage(
                            1,
                            "SYSTEM\nFATIMA VESSEL RELEASE: BLOCKED\n"
                            "COMMITTEE B SOURCE ARCHIVE: REQUIRED<Close>",
                            2,
                            3,
                        ),
                    ),
                    repeat_dialogue=(
                        "ARCHIVE RECORD 1\nETHOS PRENATAL PROCEDURES\nSUBJECT: "
                        "ANNE BANDERAS<Close>",
                    ),
                    interaction_half_width=0x06,
                    interaction_half_depth=0x04,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "north vessel archive conduit",
                    -154,
                    146,
                    49,
                    (
                        _stage(
                            2,
                            "ARCHIVE SEARCH\nTHE REMOVAL ORDER CITES THREE "
                            "INDEPENDENT RECORDS.<Close>",
                            choice=(
                                "<Opcode:01:FF>Verify which record?\n"
                                "     Physician registry\n"
                                "     Palace expenses\n"
                                "     Tomb inventory<Close>"
                            ),
                            accepted=1,
                            rejected=(
                                "<Fei>\nThat record could show where the lie "
                                "went.<New>It will not show who made the "
                                "death report possible.<Close>",
                            ),
                            after=(
                                "PHYSICIAN REGISTRY\nATTENDING PHYSICIAN: "
                                "DECEASED BEFORE ANNE BANDERAS DEATH REPORT "
                                "WAS FILED<Close>",
                                4,
                                5,
                                6,
                            ),
                            required=(1,),
                            locked=(
                                "<Rico>\nThe medical record came first.<New>"
                                "I need its subject number before I can trace "
                                "the removal order.<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "ARCHIVE RECORD 2\nDEATH REPORTS: FABRICATED\n"
                        "DESTINATION: OUTER DISTRICT<Close>",
                    ),
                    interaction_half_width=0x08,
                    interaction_half_depth=0x04,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "south vessel archive conduit",
                    -157,
                    -137,
                    56,
                    (
                        _stage(
                            3,
                            "ARCHIVE SEARCH\nTHE FALSE DEATH REPORT WAS USED "
                            "AGAIN AFTER RICO ENTERED THE PALACE.<Close>",
                            choice=(
                                "<Opcode:01:FF>Trace the later order:\n"
                                "     D Block census\n"
                                "     Family seal response\n"
                                "     Committee payroll<Close>"
                            ),
                            accepted=2,
                            rejected=(
                                "<Bart>\nThat trail ends with the Committee's "
                                "clerks.<New>The family seal should lead back "
                                "to the Kaiser's office.<Close>",
                            ),
                            after=(7, 8, 9),
                            required=(2,),
                            locked=(
                                "<Rico>\nFirst I find out how they buried "
                                "Mother on paper.<New>Then I find out who kept "
                                "the lie alive.<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "ARCHIVE RECORD 3\nFAMILY SEAL RESPONSE CONFIRMED\n"
                        "COMMITTEE B SUPPRESSION APPROVED<Close>",
                    ),
                    interaction_half_width=0x08,
                    interaction_half_depth=0x04,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "Sigmund",
                    -190,
                    0,
                    69,
                    sigmund_stages,
                    activation_required_bits=(1, 2, 3),
                    hide_bound_actors_until_active=True,
                    repeat_dialogue=(
                        "Sigmund\nNo more sealed rooms.<New>Kislev will hear "
                        "the whole truth.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "wall communication display",
                    388,
                    0,
                    24,
                    (
                        _stage(
                            11,
                            157,
                            158,
                            159,
                            161,
                            162,
                            required=(8,),
                            locked=(
                                "Sigmund\nI have not given the order yet.<New>"
                                "Make me finish the answer I owe you.<Close>",
                            ),
                        ),
                        _stage(
                            13,
                            "SYSTEM\nANNE BANDERAS FILE AND COMMITTEE B "
                            "ORDERS READY FOR RELEASE.<Close>",
                            choice=(
                                "<Opcode:01:FF>Release copies to:\n"
                                "     Civil archive\n"
                                "     Committee B\n"
                                "     Keep them sealed<Close>"
                            ),
                            accepted=1,
                            rejected=(
                                "<Rico>\nNo. Another sealed room is how they "
                                "kept this buried.<Close>",
                            ),
                            after=(
                                "SYSTEM\nOFFSITE COPIES: SECURE\nSOURCE ARCHIVE: "
                                "COMMITTEE CONTROL RETAINED\nREMOTE PURGE: "
                                "BLOCKED<Close>",
                                "<Rico>\nNow it does not depend on one file, "
                                "one room, or one man's courage.<Close>",
                            ),
                            required=(12,),
                            locked=(
                                "SYSTEM\nA VERIFIED SOURCE FILE IS REQUIRED "
                                "BEFORE PUBLIC RELEASE.<Close>",
                            ),
                        ),
                    ),
                    interaction_half_width=0x03,
                    interaction_half_depth=0x03,
                    requires_facing=False,
                    repeat_dialogue=(
                        "SYSTEM\nOFFSITE COPIES: SECURE\nSOURCE ARCHIVE: "
                        "COMMITTEE CONTROL RETAINED<Close>",
                    ),
                ),
                PlayableInteraction(
                    "Anne's file on the desk",
                    281,
                    92,
                    10,
                    (
                        _stage(
                            12,
                            "The channel closes. Sigmund removes the Imperial "
                            "signet and sets it beside Anne's file.<Close>",
                            *range(164, 174),
                            "Sigmund offers Anne's file. Rico accepts it only "
                            "after ordering public copies.<Close>",
                            *range(175, 178),
                            "Rico turns toward the door, then stops.<Close>",
                            *range(179, 181),
                            required=(11,),
                            locked=(
                                "<Rico>\nThe public order comes first.<New>"
                                "The file means nothing if one closed room can "
                                "erase it again.<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "<Rico>\nThe original stays with me until every copy "
                        "is safe.<Close>",
                    ),
                    interaction_half_width=0x06,
                    interaction_half_depth=0x06,
                    requires_facing=False,
                ),
            ),
            # The private scene closes the authentic sliding leaf after Fei
            # and Bart depart.  Rico completes the chapter from its inside
            # approach; the exit action reopens that same native leaf before
            # transferring to the next chapter or hub.
            exit_x=258,
            exit_z=-166,
            exit_triangle=30,
            required_bits=(1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13),
            exit_dialogue=(
                "An alarm cuts through the room. Committee B has begun B "
                "Protocol.<Close>",
                183,
            ),
            exit_locked_steps=(
                (1, "The office archive cabinet is still sealed.<Close>"),
                (2, "<Rico>\nI need to trace who fabricated her death.<Close>"),
                (3, "<Rico>\nThe third record will show who kept the lie alive.<Close>"),
                (4, "<Rico>\nThe records are complete. Sigmund will answer me now.<Close>"),
                (5, "Sigmund\nAnne's medical file contains the rest of the truth.<Close>"),
                (6, "<Rico>\nHe has told me what happened. He has not answered for his choice.<Close>"),
                (7, "<Rico>\nKislev's laws put Mother's suffering into every street and cell.<Close>"),
                (8, "<Rico>\nSigmund still has to decide whether he will act in public.<Close>"),
                (11, "<Rico>\nThe communication panel is ready for his order.<Close>"),
                (12, "<Rico>\nAnne's original file is still on the desk.<Close>"),
                (13, "<Rico>\nThe evidence needs offsite copies before I leave.<Close>"),
            ),
            completion_at_exit=True,
        )

    if chapter_id == 5:
        return PlayableChapter(
            chapter_id=5,
            interactions=(
                PlayableInteraction(
                    "central control",
                    13,
                    -8,
                    192,
                    (
                        _stage(
                            1,
                            1,
                            2,
                            "MONITOR\nPROTECTED CHANNEL OPEN\nSENDER: RUE "
                            "COHEN, COMMITTEE B<Close>",
                            *range(4, 23),
                            "FACILITY MAP\nTHREE LOCAL RELAYS HAVE "
                            "LOCKED AGAINST CENTRAL CONTROL.<Close>",
                            24,
                            25,
                            after=(
                                "SYSTEM\nTHREE LOCAL RELAYS HAVE REJECTED "
                                "CENTRAL CONTROL.<New>ARCHIVE INTEGRITY MUST "
                                "BE RESTORED FIRST.<Close>",
                            ),
                        ),
                        _stage(
                            6,
                            "MONITOR\nCOMMITTEE CONTROL CHANNEL OPEN\n"
                            "PALACE GUARD CHANNEL OPEN<Close>",
                            *range(85, 98),
                            after=(
                                "ARCHIVIST\nCommittee Control is secure.<New>"
                                "The final lift transponder still requires a "
                                "local check.<Close>",
                            ),
                            required=(5,),
                            locked=(
                                "ARCHIVIST\nCommittee Control is still "
                                "sealed.<New>The defense Gear must be stopped "
                                "before we can reach Rue.<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "ARCHIVIST\nAll surviving records are secure.<New>"
                        "Verify the final lift at the upper station.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "archive integrity relay",
                    206,
                    121,
                    165,
                    (
                        _stage(
                            2,
                            *range(26, 31),
                            choice=(
                                "<Opcode:01:FF>Choose the archive priority:\n"
                                "     Save one listed file\n"
                                "     Copy registered citizens\n"
                                "     Save every sealed record<Close>"
                            ),
                            accepted=3,
                            rejected=(
                                "<Rico>\nNo. They hid workers, prisoners and "
                                "Battlers beside Mother.<New>We save every "
                                "record we can reach.<Close>",
                            ),
                            after=(*range(32, 43),),
                            required=(1,),
                            locked=(
                                "ARCHIVE RELAY\nCENTRAL AUTHORIZATION REQUIRED<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "ARCHIVE RELAY\nPURGE: STOPPED\nCIVIL COPIES: "
                        "TRANSMITTING<Close>",
                    ),
                ),
                PlayableInteraction(
                    "emergency distribution relay",
                    -163,
                    127,
                    183,
                    (
                        _stage(
                            3,
                            *range(43, 52),
                            choice=(
                                "<Opcode:01:FF>Route emergency reserve to:\n"
                                "     Battling arena\n"
                                "     Committee security\n"
                                "     Worker lifts<Close>"
                            ),
                            accepted=3,
                            rejected=(
                                "<Rico>\nPeople below us are running out of "
                                "air.<New>The arena can go dark.<Close>",
                            ),
                            after=(
                                52,
                                53,
                                54,
                                55,
                                "The Battling broadcast goes dark. The worker "
                                "lifts begin to move.<Close>",
                                57,
                                58,
                                59,
                            ),
                            required=(2,),
                            locked=(
                                "EMERGENCY RELAY\nARCHIVE PURGE IS DRAWING "
                                "MAINTENANCE POWER<New>RESTORE ARCHIVE "
                                "INTEGRITY FIRST<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "EMERGENCY RELAY\nBROADCAST: OFFLINE\nWORKER LIFTS: "
                        "MOVING<Close>",
                    ),
                ),
                PlayableInteraction(
                    "combat telemetry relay",
                    -163,
                    -123,
                    185,
                    (
                        _stage(
                            4,
                            *range(60, 69),
                            choice=(
                                "<Opcode:01:FF>One command remains:\n"
                                "     Corrupt combat library\n"
                                "     Release lower bulkheads<Close>"
                            ),
                            accepted=2,
                            rejected=(
                                "<Rico>\nThe workers do not get another "
                                "chance if those doors stay shut.<New>We "
                                "do.<Close>",
                            ),
                            after=(
                                *range(69, 75),
                                "The lower bulkheads turn green. Committee "
                                "B's defense Gear begins to launch.<Close>",
                                *range(76, 81),
                            ),
                            required=(3,),
                            locked=(
                                "COMBAT RELAY\nEVACUATION POWER ROUTE "
                                "INCOMPLETE<Close>",
                            ),
                        ),
                        _stage(
                            5,
                            "COMBAT RELAY\nDEFENSE GEAR: ACTIVE\nSTIER "
                            "PREDICTION MODEL: LOCKED<Close>",
                            choice=(
                                "<Opcode:01:FF>Intercept the defense Gear?\n"
                                "     Deploy\n"
                                "     Review systems<Close>"
                            ),
                            accepted=1,
                            rejected=(
                                "<Bart>\nTake the time you need.<New>Once we "
                                "deploy, that machine will come straight for "
                                "Stier.<Close>",
                            ),
                            after=(
                                82,
                                83,
                                "The defense Gear falls. Committee Control "
                                "opens.<Close>",
                            ),
                            required=(4,),
                            locked=(
                                "COMBAT RELAY\nOPEN THE LOWER BULKHEADS "
                                "BEFORE DEPLOYING STIER<Close>",
                            ),
                            battle=15,
                            gear=True,
                        ),
                    ),
                    repeat_dialogue=(
                        "COMBAT RELAY\nDEFENSE GEAR: DESTROYED\nLOWER "
                        "BULKHEADS: OPEN<Close>",
                    ),
                ),
            ),
            exit_x=6,
            exit_z=883,
            exit_triangle=276,
            required_bits=(1, 2, 3, 4, 5, 6),
            exit_dialogue=(*range(98, 104),),
            exit_locked_steps=(
                (
                    1,
                    "<Rico>\nCentral control will show what B Protocol "
                    "locked down.<Close>",
                ),
                (
                    2,
                    "<Rico>\nThe source archive is being purged.<New>We "
                    "save every sealed record first.<Close>",
                ),
                (
                    3,
                    "<Rico>\nWorkers are trapped below.<New>The emergency "
                    "distribution relay can restore their lifts.<Close>",
                ),
                (
                    4,
                    "<Rico>\nThe combat relay still controls the lower "
                    "bulkheads.<Close>",
                ),
                (
                    5,
                    "<Rico>\nCommittee B's defense Gear is still active.<New>"
                    "Stier will face it with Fei and Bart.<Close>",
                ),
                (
                    6,
                    "<Rico>\nCommittee Control is open.<New>Rue and the final "
                    "lift still need to be accounted for.<Close>",
                ),
            ),
            completion_at_exit=True,
        )

    if chapter_id == 6:
        return PlayableChapter(
            chapter_id=6,
            interactions=(
                PlayableInteraction(
                    "Fatima command station",
                    111,
                    31,
                    165,
                    (
                        _stage(
                            1,
                            1,
                            2,
                            3,
                            4,
                            after=(
                                "FATIMA COMMAND\nBLOODLINE AUTHORITY: "
                                "ACCEPTED\nCORE REGULATOR: AVAILABLE<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "FATIMA COMMAND\nVESSEL AUTHORITY: BART FATIMA\n"
                        "STATUS: ACTIVE<Close>",
                    ),
                    interaction_half_width=0x06,
                    interaction_half_depth=0x06,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "core regulator",
                    31,
                    111,
                    167,
                    (
                        _stage(
                            2,
                            5,
                            after=(
                                "CORE REGULATOR\nPRIMARY POWER: STABLE\n"
                                "EVACUATION GRID: AVAILABLE<Close>",
                            ),
                            required=(1,),
                            locked=(
                                "<Rico>\nThe regulator is dormant. Bart's "
                                "command station must answer first.<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "CORE REGULATOR\nPRIMARY POWER: STABLE<Close>",
                    ),
                    interaction_half_width=0x06,
                    interaction_half_depth=0x06,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "Nortune evacuation station",
                    -111,
                    31,
                    169,
                    (
                        _stage(
                            3,
                            "CITYWIDE EVACUATION GRID\nRESERVE POWER IS "
                            "READY FOR ALL DISTRICTS.<Close>",
                            choice=(
                                "<Opcode:01:FF>Protect which route?\n"
                                "     Battling arena\n"
                                "     Committee offices\n"
                                "     Civil evacuation<Close>"
                            ),
                            accepted=3,
                            rejected=(
                                "<Rico>\nNo. The people leaving D Block and "
                                "the lower levels come first.<Close>",
                            ),
                            after=(
                                "Sigmund\nEvacuation routes are clear. "
                                "Central District is under civil "
                                "control.<Close>",
                                "<Rico>\nKeep them clear.<New>Bart, wake the "
                                "ship. I'll make sure Nortune does not chain "
                                "it down again.<Close>",
                                "EVACUATION GRID\nCIVIL ROUTES: PROTECTED\n"
                                "VESSEL CLAMPS: RELEASED<Close>",
                            ),
                            required=(2,),
                            locked=(
                                "EVACUATION GRID\nCORE POWER IS NOT STABLE<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "EVACUATION GRID\nCIVIL ROUTES: PROTECTED<Close>",
                    ),
                    interaction_half_width=0x06,
                    interaction_half_depth=0x06,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "Stier launch control",
                    -31,
                    -111,
                    171,
                    (
                        _stage(
                            4,
                            "STIER LAUNCH CONTROL\nALL CLAMPS: GREEN\n"
                            "COMMITTEE DEFENSE GEARS: APPROACHING<Close>",
                            choice=(
                                "<Opcode:01:FF>Launch Stier?\n"
                                "     Launch\n"
                                "     Hold position<Close>"
                            ),
                            accepted=1,
                            rejected=(
                                "<Rico>\nHold the clamps where they are.<New>"
                                "I will launch when the others are ready.<Close>",
                            ),
                            after=(
                                "The defense Gears fall away. The Fatima "
                                "vessel continues its ascent beneath "
                                "Nortune.<Close>",
                                8,
                            ),
                            required=(3,),
                            locked=(
                                "<Rico>\nThe citywide evacuation routes must "
                                "be protected before Stier launches.<Close>",
                            ),
                            battle=6,
                            gear=True,
                        ),
                    ),
                    repeat_dialogue=(
                        "STIER LAUNCH CONTROL\nDEFENSE FORMATION: "
                        "CLEARED<Close>",
                    ),
                    interaction_half_width=0x06,
                    interaction_half_depth=0x06,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "collar shutdown console",
                    300,
                    200,
                    6,
                    (
                        _stage(
                            5,
                            "COLLAR CONTROL\nTHE DETONATION NETWORK IS STILL "
                            "ACTIVE.<Close>",
                            choice=(
                                "<Opcode:01:FF>Authorize shutdown for:\n"
                                "     Arena contracts\n"
                                "     D Block only\n"
                                "     Every collar<Close>"
                            ),
                            accepted=3,
                            rejected=(
                                "<Rico>\nNot one floor. Not one kind of "
                                "prisoner.<New>Turn off every collar.<Close>",
                            ),
                            after=(
                                "Rico authorizes the full shutdown. Across "
                                "Nortune, the collar control lights go "
                                "dark.<Close>",
                                21,
                                22,
                                23,
                            ),
                            required=(4,),
                            locked=(
                                "COLLAR CONTROL\nSTIER HAS NOT CLEARED THE "
                                "VESSEL'S DEFENSE ROUTE<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "COLLAR CONTROL\nDETONATION NETWORK: OFFLINE\n"
                        "DETENTION GATES: RELEASED<Close>",
                    ),
                    interaction_half_width=0x0A,
                    interaction_half_depth=0x08,
                    requires_facing=False,
                ),
                PlayableInteraction(
                    "Kislev communications receiver",
                    -300,
                    -200,
                    1,
                    (
                        _stage(
                            6,
                            "The receiver opens a secure channel to the "
                            "Kaiser's office.<Close>",
                            *range(10, 20),
                            *range(25, 31),
                            required=(5,),
                            locked=(
                                "<Rico>\nThe collar network must be dark "
                                "before Sigmund addresses D Block.<Close>",
                            ),
                        ),
                    ),
                    repeat_dialogue=(
                        "KISLEV RECEIVER\nPUBLIC ADDRESS: STORED\n"
                        "COMMITTEE B: DISSOLVED<Close>",
                    ),
                    interaction_half_width=0x0A,
                    interaction_half_depth=0x08,
                    requires_facing=False,
                ),
            ),
            exit_x=661,
            exit_z=6,
            exit_triangle=195,
            required_bits=(1, 2, 3, 4, 5, 6),
            exit_dialogue=(
                31,
                "<Rico>\nNortune is clear. Solaris is next.<Close>",
                32,
            ),
            exit_locked_steps=(
                (
                    1,
                    "<Rico>\nBart's Fatima command station must wake the "
                    "buried vessel.<Close>",
                ),
                (
                    2,
                    "<Bart>\nThe core regulator needs power before the ship "
                    "can protect anyone.<Close>",
                ),
                (
                    3,
                    "<Rico>\nNortune's citywide evacuation routes come "
                    "before launch.<Close>",
                ),
                (
                    4,
                    "<Rico>\nStier must clear the defense formation so the "
                    "vessel can reach Ft. Hurricane.<Close>",
                ),
                (
                    5,
                    "<Rico>\nThe collar network is still active across "
                    "Nortune.<Close>",
                ),
                (
                    6,
                    "<Rico>\nSigmund still owes Kislev the truth over the "
                    "public receiver.<Close>",
                ),
            ),
            completion_at_exit=True,
        )

    if chapter_id == 7:
        return PlayableChapter(
            chapter_id=7,
            interactions=(
                PlayableInteraction(
                    "Fei",
                    47,
                    116,
                    35,
                    (
                        _stage(
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7,
                            "<Fei>\nI'll give you some time.<New>You do not "
                            "have to pack his memory away with the rest of "
                            "this room.<Close>",
                            hide_after=(1,),
                            time_cut=True,
                        ),
                    ),
                    repeat_dialogue=(
                        "The room is quiet. Fei has returned to the "
                        "corridor.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "Hammer's empty bunk",
                    -50,
                    85,
                    30,
                    (
                        _stage(
                            2,
                            8,
                            "Rico stands beside Hammer's empty bunk. The "
                            "blanket is still twisted where Hammer left it.<Close>",
                            "<Rico>\nHammer's last words asked me to return "
                            "to Nortune.<New>I will not return as the heir he "
                            "named, but I will keep the part of that promise "
                            "that belongs to D Block.<Close>",
                            required=(1,),
                            locked=(
                                "<Rico>\nFei and I have not finished saying "
                                "goodbye to Hammer.<Close>",
                            ),
                        ),
                    ),
                    interaction_half_width=0x08,
                    interaction_half_depth=0x06,
                    requires_facing=False,
                    repeat_dialogue=(
                        "Hammer's bunk is empty. Rico leaves the blanket as "
                        "Hammer left it.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "Rico's bunk",
                    100,
                    55,
                    28,
                    (
                        _stage(
                            3,
                            "Rico folds the blanket on his own bunk. D Block "
                            "once taught him that a private room meant he had "
                            "won something.<Close>",
                            "<Rico>\nA larger cell was still a cell.<New>This "
                            "room was different because I chose the people on "
                            "the other side of its door.<Close>",
                            required=(2,),
                            locked=(
                                "<Rico>\nHammer's bunk comes first.<New>I am "
                                "not leaving his place unacknowledged.<Close>",
                            ),
                        ),
                    ),
                    interaction_half_width=0x08,
                    interaction_half_depth=0x06,
                    requires_facing=False,
                    repeat_dialogue=(
                        "Rico's bunk is made. Only the clothes and papers "
                        "remain.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "hanging work clothes",
                    -120,
                    -100,
                    27,
                    (
                        _stage(
                            4,
                            "Rico takes his old work clothes from the rack, "
                            "folds them, and leaves the Champion's coat "
                            "hanging.<Close>",
                            "<Rico>\nThe Champ was a name the arena needed. "
                            "I do not need to carry it home.<Close>",
                            required=(3,),
                            locked=(
                                "<Rico>\nI should put my own bunk in order "
                                "before I pack the rest.<Close>",
                            ),
                        ),
                    ),
                    interaction_half_width=0x08,
                    interaction_half_depth=0x04,
                    requires_facing=False,
                    repeat_dialogue=(
                        "The work clothes are packed. The Champion's coat "
                        "remains on the rack.<Close>",
                    ),
                ),
                PlayableInteraction(
                    "Kislev dispatch in the locker",
                    -10,
                    165,
                    38,
                    (
                        _stage(
                            5,
                            "A folded Kislev dispatch is tucked inside the "
                            "tall locker. The last weak carrier delivered it "
                            "before ordinary contact failed.<Close>",
                            9,
                            10,
                            required=(4,),
                            locked=(
                                "The tall locker door sticks in its frame. Rico "
                                "leaves it closed while the room is still in "
                                "disarray.<Close>",
                            ),
                        ),
                    ),
                    requires_facing=False,
                    repeat_dialogue=(
                        "KISLEV DISPATCH\nCOLLARS DISMANTLED\nARENA CLOSED\n"
                        "ARCHIVE COPIES DELIVERED<Close>",
                    ),
                ),
                PlayableInteraction(
                    "Rico's reply",
                    65,
                    -96,
                    27,
                    (
                        _stage(
                            6,
                            11,
                            choice=(
                                "<Opcode:01:FF>Address Rico's reply to:\n"
                                "     D Block\n"
                                "     Imperial Palace\n"
                                "     No one<Close>"
                            ),
                            accepted=1,
                            rejected=(
                                "<Rico>\nNo. This is for the people who lived "
                                "behind those gates with us.<Close>",
                            ),
                            after=(*range(12, 22),),
                            required=(5,),
                            locked=(
                                "<Rico>\nI need to read Kislev's dispatch "
                                "before I answer it.<Close>",
                            ),
                        ),
                    ),
                    requires_facing=False,
                    repeat_dialogue=(
                        "RICO'S LETTER\nADDRESSEE: D BLOCK\nRETURN: "
                        "NORTUNE<Close>",
                    ),
                ),
                PlayableInteraction(
                    "Rico's folded letter on the chair",
                    120,
                    -100,
                    26,
                    (
                        _stage(
                            9,
                            22,
                            "<Rico>\nI carried my promise to Mom out of "
                            "Nortune.<New>Going back does not mean forgetting "
                            "what happened there.<New>It means choosing what "
                            "happens next.<Close>",
                            required=(6,),
                            locked=(
                                "<Rico>\nMy letter to D Block is not "
                                "finished yet.<Close>",
                            ),
                        ),
                    ),
                    interaction_half_width=0x03,
                    interaction_half_depth=0x03,
                    requires_facing=False,
                    repeat_dialogue=(
                        "<Rico>\nThe letter is ready.<New>This time, I know "
                        "which door I am walking toward.<Close>",
                    ),
                ),
            ),
            exit_x=CHAPTER_SEVEN_EXIT_POSITION[0],
            exit_z=CHAPTER_SEVEN_EXIT_POSITION[1],
            exit_triangle=CHAPTER_SEVEN_EXIT_POSITION[2],
            required_bits=(1, 2, 3, 4, 5, 6, 9),
            exit_dialogue=(23, 24),
            exit_locked_steps=(
                (
                    1,
                    "<Rico>\nFei is still here.<New>We should speak about "
                    "Hammer before I leave.<Close>",
                ),
                (
                    2,
                    "<Rico>\nHammer's bunk is still exactly as he left "
                    "it.<Close>",
                ),
                (
                    3,
                    "<Rico>\nMy own bunk should be put in order.<Close>",
                ),
                (
                    4,
                    "<Rico>\nMy work clothes are still hanging on the "
                    "rack.<Close>",
                ),
                (
                    5,
                    "The tall locker is still closed. Rust stains its stiff "
                    "hinge.<Close>",
                ),
                (
                    6,
                    "<Rico>\nD Block deserves an answer before ordinary "
                    "contact disappears.<Close>",
                ),
                (
                    9,
                    "<Rico>\nMy folded letter is on the chair.<New>I should "
                    "take it before I leave.<Close>",
                ),
            ),
            completion_at_exit=True,
        )

    raise RicoArcBuildError(f"No playable contract for chapter {chapter_id}")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _alias_young_rico_run_to_walk(actor_component: bytes) -> bytes:
    """Make field 229's unsupported run ID reuse young Rico's walk program."""

    if (
        len(actor_component) != 4_184
        or _sha256_bytes(actor_component)
        != YOUNG_RICO_ACTOR_COMPONENT_SHA256
    ):
        raise RicoArcBuildError("Young Rico actor component changed")
    banks = mass_driver._indexed_bundle_entries(actor_component)
    if (
        len(banks) != 2
        or _sha256_bytes(banks[YOUNG_RICO_ACTOR_BANK_INDEX])
        != YOUNG_RICO_ACTOR_BANK_SHA256
    ):
        raise RicoArcBuildError("Young Rico actor bank changed")
    start = YOUNG_RICO_ANIMATION_HEADER_OFFSET
    end = start + len(YOUNG_RICO_NPC_ANIMATION_HEADER)
    if actor_component[start:end] != YOUNG_RICO_NPC_ANIMATION_HEADER:
        raise RicoArcBuildError("Young Rico animation header changed")

    result = bytearray(actor_component)
    result[start:end] = YOUNG_RICO_PLAYER_ANIMATION_HEADER
    changed_offsets = {
        index
        for index, (before, after) in enumerate(zip(actor_component, result))
        if before != after
    }
    rebuilt_banks = mass_driver._indexed_bundle_entries(bytes(result))
    if (
        changed_offsets != {start, start + 6}
        or _sha256_bytes(result)
        != YOUNG_RICO_PLAYER_ACTOR_COMPONENT_SHA256
        or _sha256_bytes(rebuilt_banks[YOUNG_RICO_ACTOR_BANK_INDEX])
        != YOUNG_RICO_PLAYER_ACTOR_BANK_SHA256
    ):
        raise RicoArcBuildError("Young Rico run-to-walk alias drifted")
    return bytes(result)


def _validate_chapter_one_anna_source(
    header: bytes,
    components: Sequence[bytes],
) -> None:
    """Pin Anne's complete retail actor identity before relocating her."""

    editor = AtelScript(components[SCRIPT_INDEX])
    if CHAPTER_ONE_ANNA_ENTITY >= editor.entity_count:
        raise RicoArcBuildError("Chapter 1 lost Anne's native actor")
    record = 0x190 + CHAPTER_ONE_ANNA_ENTITY * 16
    init_pc = editor.get_script_pointer(CHAPTER_ONE_ANNA_ENTITY, 0)
    init = mass_driver._pointed_script_body(editor, init_pc)
    update_pc = editor.get_script_pointer(CHAPTER_ONE_ANNA_ENTITY, 1)
    update = mass_driver._pointed_script_body(editor, update_pc)
    actor_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.ACTOR_INDEX]
    )
    sprite_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.SPRITE_INDEX]
    )
    if (
        record + 16 > len(header)
        or header[record : record + 16] != CHAPTER_ONE_ANNA_HEADER_RECORD
        or init_pc != CHAPTER_ONE_ANNA_INIT_PC
        or init != CHAPTER_ONE_ANNA_SOURCE_INIT
        or update_pc != CHAPTER_ONE_ANNA_UPDATE_PC
        or update != CHAPTER_ONE_ANNA_SOURCE_UPDATE
    ):
        raise RicoArcBuildError("Chapter 1 Anne source actor changed")
    if (
        not actor_banks
        or len(actor_banks[0]) != CHAPTER_ONE_ANNA_ACTOR_BANK_SIZE
        or _sha256_bytes(actor_banks[0]) != CHAPTER_ONE_ANNA_ACTOR_BANK_SHA256
        or not sprite_banks
        or len(sprite_banks[0]) != CHAPTER_ONE_ANNA_SPRITE_BANK_SIZE
        or _sha256_bytes(sprite_banks[0]) != CHAPTER_ONE_ANNA_SPRITE_BANK_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 Anne visual assets changed")


def _validate_chapter_one_door_source(components: Sequence[bytes]) -> None:
    """Pin field 229's native wooden-leaf initializer and opening helper."""

    editor = AtelScript(components[SCRIPT_INDEX])
    if CHAPTER_ONE_DOOR_ENTITY >= editor.entity_count:
        raise RicoArcBuildError("Chapter 1 lost its native house door")
    init_pc = editor.get_script_pointer(CHAPTER_ONE_DOOR_ENTITY, 0)
    open_pc = editor.get_script_pointer(
        CHAPTER_ONE_DOOR_ENTITY,
        CHAPTER_ONE_DOOR_OPEN_SCRIPT,
    )
    close_pc = editor.get_script_pointer(CHAPTER_ONE_DOOR_ENTITY, 5)
    if (
        init_pc != CHAPTER_ONE_DOOR_INIT_PC
        or editor.bytecode[
            init_pc : init_pc + len(CHAPTER_ONE_DOOR_INIT_BODY)
        ]
        != CHAPTER_ONE_DOOR_INIT_BODY
        or open_pc != CHAPTER_ONE_DOOR_OPEN_PC
        or open_pc + len(CHAPTER_ONE_DOOR_OPEN_BODY) != close_pc
        or editor.bytecode[
            open_pc : open_pc + len(CHAPTER_ONE_DOOR_OPEN_BODY)
        ]
        != CHAPTER_ONE_DOOR_OPEN_BODY
        or not CHAPTER_ONE_DOOR_OPEN_BODY.startswith(b"\x74\x08\x80")
    ):
        raise RicoArcBuildError("Chapter 1 native house-door helper changed")


def _validate_chapter_one_anna_output(
    editor: AtelScript,
    bedside_action_pc: int,
) -> None:
    """Require standing Anne's ambient cough and independent bedside action."""

    init_pc = editor.get_script_pointer(CHAPTER_ONE_ANNA_ENTITY, 0)
    update_pc = editor.get_script_pointer(CHAPTER_ONE_ANNA_ENTITY, 1)
    cough_pc = editor.get_script_pointer(
        CHAPTER_ONE_ANNA_ENTITY,
        CHAPTER_ONE_ANNA_INTERACTION_COUGH_SCRIPT,
    )
    expected_update = _chapter_one_anna_ambient_update(update_pc)
    if (
        editor.bytecode[
            init_pc : init_pc + len(CHAPTER_ONE_ANNA_PLAYABLE_INIT)
        ]
        != CHAPTER_ONE_ANNA_PLAYABLE_INIT
        or editor.bytecode[
            update_pc : update_pc + len(expected_update)
        ]
        != expected_update
        or editor.bytecode[
            cough_pc : cough_pc + len(CHAPTER_ONE_ANNA_COUGH_ONCE) + 1
        ]
        != CHAPTER_ONE_ANNA_COUGH_ONCE + b"\x00"
        or editor.get_script_pointer(CHAPTER_ONE_ANNA_ENTITY, 2)
        != bedside_action_pc
    ):
        raise RicoArcBuildError("Chapter 1 Anne playable relocation drifted")


def _seal_chapter_one_house_door(walkmesh: bytes) -> bytes:
    """Make field 229's authored inner door threshold a collision boundary."""

    if (
        len(walkmesh) != CHAPTER_ONE_WALKMESH_SIZE
        or _sha256_bytes(walkmesh) != CHAPTER_ONE_WALKMESH_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 house walkmesh changed")
    layer_count, triangle_bytes = struct.unpack_from("<II", walkmesh, 0)
    triangle_offset, vertex_offset = struct.unpack_from("<II", walkmesh, 0x18)
    if (
        layer_count != 2
        or triangle_bytes != 87 * 14
        or triangle_offset != CHAPTER_ONE_WALKMESH_TRIANGLE_OFFSET
        or vertex_offset != CHAPTER_ONE_WALKMESH_VERTEX_OFFSET
    ):
        raise RicoArcBuildError("Chapter 1 house walkmesh layout changed")

    def triangle_record(
        data: bytes | bytearray,
        triangle: int,
    ) -> tuple[tuple[int, int, int], tuple[int, int, int], int]:
        record = triangle_offset + triangle * 14
        indices = struct.unpack_from("<3H", data, record)
        neighbors = struct.unpack_from("<3h", data, record + 6)
        material = struct.unpack_from("<H", data, record + 12)[0]
        return indices, neighbors, material

    # The two records must still describe the exact reciprocal v4-v5 seam.
    # Neighbor slot 1 owns the edge made by vertex indices 1 and 2 in each
    # triangle, in opposite winding order.
    seam_edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for triangle, slot, neighbor in CHAPTER_ONE_DOOR_NEIGHBOR_LINKS:
        indices, neighbors, material = triangle_record(walkmesh, triangle)
        if neighbors[slot] != neighbor or material != 1:
            raise RicoArcBuildError("Chapter 1 door neighbor seam changed")
        edge_indices = (indices[slot], indices[(slot + 1) % 3])
        edge = tuple(
            struct.unpack_from("<hhhh", walkmesh, vertex_offset + index * 8)[
                ::2
            ]
            for index in edge_indices
        )
        seam_edges.append(edge)
    expected_edge = set(CHAPTER_ONE_DOOR_THRESHOLD_EDGE)
    if any(set(edge) != expected_edge for edge in seam_edges):
        raise RicoArcBuildError("Chapter 1 door threshold vertices changed")

    result = bytearray(walkmesh)
    changed_words: list[int] = []
    for triangle, slot, _neighbor in CHAPTER_ONE_DOOR_NEIGHBOR_LINKS:
        neighbor_offset = triangle_offset + triangle * 14 + 6 + slot * 2
        struct.pack_into("<h", result, neighbor_offset, -1)
        changed_words.append(neighbor_offset)

    changed_offsets = {
        index
        for index, (before, after) in enumerate(zip(walkmesh, result))
        if before != after
    }
    expected_changed_offsets = {
        offset + byte
        for offset in changed_words
        for byte in range(2)
    }
    if (
        changed_offsets != expected_changed_offsets
        or _sha256_bytes(result) != CHAPTER_ONE_SEALED_WALKMESH_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 door collision patch drifted")

    # Follow the engine's encoded triangle neighbors, not shared geometry.
    # The patch must remove exactly the two behind-door triangles while every
    # authored Chapter 1 point remains reachable from young Rico's entry.
    reachable = {PLAYABLE_ENTRY_POSITIONS[1][2]}
    pending = list(reachable)
    while pending:
        current = pending.pop()
        _indices, neighbors, _material = triangle_record(result, current)
        for neighbor in neighbors:
            if neighbor >= 0 and neighbor not in reachable:
                reachable.add(neighbor)
                pending.append(neighbor)
    if set(range(87)) - reachable != CHAPTER_ONE_DOOR_EXTERIOR_TRIANGLES:
        raise RicoArcBuildError("Chapter 1 door patch changed room connectivity")
    contract = _playable_chapter_contract(1)
    required_triangles = {
        PLAYABLE_ENTRY_POSITIONS[1][2],
        contract.exit_triangle,
        *(interaction.triangle for interaction in contract.interactions),
    }
    if not required_triangles <= reachable:
        raise RicoArcBuildError("Chapter 1 door patch blocks an authored objective")
    return bytes(result)


def _validate_chapter_one_door_departure_route(walkmesh: bytes) -> None:
    """Prove Rico's cosmetic exit walk never attempts the sealed seam."""

    if (
        len(walkmesh) != CHAPTER_ONE_WALKMESH_SIZE
        or _sha256_bytes(walkmesh) != CHAPTER_ONE_SEALED_WALKMESH_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 departure lost its sealed walkmesh")
    triangles = _walkmesh_layer(walkmesh, 0)
    x, z, triangle = CHAPTER_ONE_DOOR_REPOSITION
    if (
        CHAPTER_ONE_DOOR_REPOSITION != CHAPTER_ONE_EXIT_POSITION
        or triangle in CHAPTER_ONE_DOOR_EXTERIOR_TRIANGLES
        or triangle >= len(triangles)
        or not _point_inside_triangle((x, z), triangles[triangle])
        or CHAPTER_ONE_DOOR_DEPARTURE_MAX_STEPS != 16
        or CHAPTER_ONE_DOOR_DEPARTURE_VISIBLE_FRAMES != 8
    ):
        raise RicoArcBuildError(
            "Chapter 1 cosmetic door walk left its bounded t59 threshold"
        )


def _seal_chapter_four_office_door(walkmesh: bytes) -> bytes:
    """Seal field 237's offstage corridor behind its visible south leaf."""

    if (
        len(walkmesh) != CHAPTER_FOUR_WALKMESH_SIZE
        or _sha256_bytes(walkmesh) != CHAPTER_FOUR_WALKMESH_SHA256
    ):
        raise RicoArcBuildError("Chapter 4 office walkmesh changed")
    layer_count, triangle_bytes = struct.unpack_from("<II", walkmesh, 0)
    triangle_offset, vertex_offset = struct.unpack_from("<II", walkmesh, 0x18)
    if (
        layer_count != 2
        or triangle_bytes != 76 * 14
        or triangle_offset != CHAPTER_FOUR_WALKMESH_TRIANGLE_OFFSET
        or vertex_offset != CHAPTER_FOUR_WALKMESH_VERTEX_OFFSET
    ):
        raise RicoArcBuildError("Chapter 4 office walkmesh layout changed")

    for triangle, record_bytes in CHAPTER_FOUR_DOOR_TRIANGLE_RECORDS.items():
        record = triangle_offset + triangle * 14
        if walkmesh[record : record + 14] != record_bytes:
            raise RicoArcBuildError("Chapter 4 door triangle record changed")
    for vertex, record_bytes in CHAPTER_FOUR_DOOR_VERTEX_RECORDS.items():
        record = vertex_offset + vertex * 8
        if walkmesh[record : record + 8] != record_bytes:
            raise RicoArcBuildError("Chapter 4 door threshold vertices changed")

    result = bytearray(walkmesh)
    changed_words: list[int] = []
    for triangle, slot, neighbor in CHAPTER_FOUR_DOOR_NEIGHBOR_LINKS:
        record = triangle_offset + triangle * 14
        neighbors = struct.unpack_from("<3h", walkmesh, record + 6)
        if neighbors[slot] != neighbor:
            raise RicoArcBuildError("Chapter 4 door neighbor seam changed")
        neighbor_offset = record + 6 + slot * 2
        struct.pack_into("<h", result, neighbor_offset, -1)
        changed_words.append(neighbor_offset)

    changed_offsets = {
        index
        for index, (before, after) in enumerate(zip(walkmesh, result))
        if before != after
    }
    expected_changed_offsets = {
        offset + byte for offset in changed_words for byte in range(2)
    }
    if (
        changed_offsets != expected_changed_offsets
        or _sha256_bytes(result) != CHAPTER_FOUR_SEALED_WALKMESH_SHA256
    ):
        raise RicoArcBuildError("Chapter 4 door collision patch drifted")

    # The scripted companions use bounded movement followed by exact snaps,
    # so their private-scene departure can cross this deliberately closed
    # player seam after the native leaf opens.  Ordinary player movement
    # cannot enter the otherwise unused t36/t37 offstage corridor.
    reachable = {PLAYABLE_ENTRY_POSITIONS[4][2]}
    pending = list(reachable)
    while pending:
        current = pending.pop()
        record = triangle_offset + current * 14
        neighbors = struct.unpack_from("<3h", result, record + 6)
        for neighbor in neighbors:
            if neighbor >= 0 and neighbor not in reachable:
                reachable.add(neighbor)
                pending.append(neighbor)
    if set(range(76)) - reachable != CHAPTER_FOUR_DOOR_EXTERIOR_TRIANGLES:
        raise RicoArcBuildError("Chapter 4 door patch changed room connectivity")
    contract = _playable_chapter_contract(4)
    required_triangles = {
        PLAYABLE_ENTRY_POSITIONS[4][2],
        contract.exit_triangle,
        *(interaction.triangle for interaction in contract.interactions),
    }
    if not required_triangles <= reachable:
        raise RicoArcBuildError("Chapter 4 door patch blocks an authored objective")
    return bytes(result)


def _seal_chapter_seven_bedroom_door(walkmesh: bytes) -> bytes:
    """Seal field 298's inside/outside seam behind its visible east leaf."""

    if (
        len(walkmesh) != CHAPTER_SEVEN_WALKMESH_SIZE
        or _sha256_bytes(walkmesh) != CHAPTER_SEVEN_WALKMESH_SHA256
    ):
        raise RicoArcBuildError("Chapter 7 bedroom walkmesh changed")
    layer_count, triangle_bytes = struct.unpack_from("<II", walkmesh, 0)
    triangle_offset, vertex_offset = struct.unpack_from("<II", walkmesh, 0x18)
    if (
        layer_count != 3
        or triangle_bytes != 39 * 14
        or triangle_offset != CHAPTER_SEVEN_WALKMESH_TRIANGLE_OFFSET
        or vertex_offset != CHAPTER_SEVEN_WALKMESH_VERTEX_OFFSET
    ):
        raise RicoArcBuildError("Chapter 7 bedroom walkmesh layout changed")

    for triangle, record_bytes in CHAPTER_SEVEN_DOOR_TRIANGLE_RECORDS.items():
        record = triangle_offset + triangle * 14
        if walkmesh[record : record + 14] != record_bytes:
            raise RicoArcBuildError("Chapter 7 door triangle record changed")
    for vertex, record_bytes in CHAPTER_SEVEN_DOOR_VERTEX_RECORDS.items():
        record = vertex_offset + vertex * 8
        if walkmesh[record : record + 8] != record_bytes:
            raise RicoArcBuildError("Chapter 7 door threshold vertices changed")

    result = bytearray(walkmesh)
    changed_words: list[int] = []
    for triangle, slot, neighbor in CHAPTER_SEVEN_DOOR_NEIGHBOR_LINKS:
        record = triangle_offset + triangle * 14
        neighbors = struct.unpack_from("<3h", walkmesh, record + 6)
        if neighbors[slot] != neighbor:
            raise RicoArcBuildError("Chapter 7 door neighbor seam changed")
        neighbor_offset = record + 6 + slot * 2
        struct.pack_into("<h", result, neighbor_offset, -1)
        changed_words.append(neighbor_offset)

    changed_offsets = {
        index
        for index, (before, after) in enumerate(zip(walkmesh, result))
        if before != after
    }
    expected_changed_offsets = {
        offset + byte for offset in changed_words for byte in range(2)
    }
    if (
        changed_offsets != expected_changed_offsets
        or _sha256_bytes(result) != CHAPTER_SEVEN_SEALED_WALKMESH_SHA256
    ):
        raise RicoArcBuildError("Chapter 7 door collision patch drifted")

    reachable = {PLAYABLE_ENTRY_POSITIONS[7][2]}
    pending = list(reachable)
    while pending:
        current = pending.pop()
        record = triangle_offset + current * 14
        neighbors = struct.unpack_from("<3h", result, record + 6)
        for neighbor in neighbors:
            if neighbor >= 0 and neighbor not in reachable:
                reachable.add(neighbor)
                pending.append(neighbor)
    if set(range(39)) - reachable != CHAPTER_SEVEN_DOOR_EXTERIOR_TRIANGLES:
        raise RicoArcBuildError("Chapter 7 door patch changed room connectivity")
    contract = _playable_chapter_contract(7)
    required_triangles = {
        PLAYABLE_ENTRY_POSITIONS[7][2],
        contract.exit_triangle,
        *(interaction.triangle for interaction in contract.interactions),
    }
    if not required_triangles <= reachable:
        raise RicoArcBuildError("Chapter 7 door patch blocks an authored objective")
    return bytes(result)


def _u16(value: int) -> bytes:
    if not isinstance(value, int) or not 0 <= value <= 0xFFFF:
        raise RicoArcBuildError(f"u16 value outside 0..65535: {value}")
    return struct.pack("<H", value)


def _s16(value: int) -> bytes:
    if not isinstance(value, int) or not -0x8000 <= value <= 0x7FFF:
        raise RicoArcBuildError(f"s16 value outside -32768..32767: {value}")
    return struct.pack("<h", value)


def _immediate(value: int) -> bytes:
    if not isinstance(value, int) or not 0 <= value <= 0x7FFF:
        raise RicoArcBuildError(f"ATEL immediate outside 0..32767: {value}")
    return _u16(value | 0x8000)


def _dialog(block_id: int, *, flags: int = 0) -> bytes:
    return b"\xF5" + _u16(block_id) + bytes((flags,))


def _choice_dialog(block_id: int, *, flags: int = 0) -> bytes:
    return b"\xD2" + _u16(block_id) + bytes((flags,))


def _wait(frames: int = 1) -> bytes:
    if not 1 <= frames <= 0x7FFF:
        raise RicoArcBuildError(f"ATEL wait outside 1..32767: {frames}")
    return b"\x26" + _immediate(frames)


def _chapter_one_anna_ambient_update(routine_pc: int) -> bytes:
    """Cough on scene entry, restore idle, then repeat after a quiet interval."""

    return (
        CHAPTER_ONE_ANNA_COUGH_ONCE
        + _wait(CHAPTER_ONE_ANNA_COUGH_INTERVAL_FRAMES)
        + _jump(routine_pc)
    )


def _jump(pc: int) -> bytes:
    return b"\x01" + _u16(pc)


def _chapter_one_kettle_timer_update(base_pc: int) -> bytes:
    """Boil the kettle in the background without taking control from Rico."""

    routine = mass_driver._RoutineBuilder(base_pc)
    routine.jump_if_bit_clear(
        PLAYABLE_STATE_VARIABLE,
        1 << CHAPTER_ONE_STOVE_ON_BIT,
        "poll",
    )
    routine.emit(
        _wait(CHAPTER_ONE_KETTLE_BOIL_FRAMES)
        + atel.set_var_bit(
            PLAYABLE_STATE_VARIABLE,
            CHAPTER_ONE_KETTLE_BOILED_BIT,
        )
        + b"\x00"
    )
    routine.label("poll")
    routine.emit(_wait() + _jump(base_pc))
    return routine.finish()


def _wait_for_pad_release(mask: int, pc: int) -> bytes:
    released_pc = pc + 11
    return b"\x31" + _u16(mask) + _u16(released_pc) + _wait() + _jump(pc)


def _dialogue_sequence(
    block_ids: Iterable[int],
    *,
    flags: int = 0,
) -> bytes:
    ids = tuple(block_ids)
    output = bytearray()
    for index, block_id in enumerate(ids):
        output.extend(_dialog(block_id, flags=flags))
        output.append(0x9C)
        if index + 1 < len(ids):
            output.extend(_wait())
    return bytes(output)


def _actor_dialog_reset() -> bytes:
    return b"\xF4\x01\xFE\x0D\xFC\x80"


def _automatic_dialogue(block_ids: Iterable[int], *, routine_pc: int) -> bytes:
    prefix = _actor_dialog_reset() + b"\x33\xFE\x54"
    release_pc = routine_pc + len(prefix)
    body = (
        prefix
        + _wait_for_pad_release(PAD_MASK_CROSS, release_pc)
        + _wait()
        + _dialogue_sequence(block_ids)
        + _actor_dialog_reset()
    )
    close_release_pc = routine_pc + len(body)
    return (
        body
        + _wait_for_pad_release(PAD_MASK_CROSS, close_release_pc)
        + b"\xFE\x53"
    )


def _prelaunch_exposition(
    block_ids: Iterable[int],
    *,
    routine_pc: int,
    flags: int = 0,
) -> bytes:
    """Present confirmed chapter framing without restoring field control.

    The caller already owns FE54's movement lock.  Cross is drained on both
    sides of the pages so the confirmation press cannot dismiss the first
    page and the closing press cannot leak into the destination field.
    """

    ids = tuple(block_ids)
    if not ids:
        raise RicoArcBuildError("A chapter launch needs exposition dialogue")
    body = (
        _wait_for_pad_release(PAD_MASK_CROSS, routine_pc)
        + _wait()
        + _dialogue_sequence(ids, flags=flags)
        + _actor_dialog_reset()
    )
    close_release_pc = routine_pc + len(body)
    return (
        body
        + _wait_for_pad_release(PAD_MASK_CROSS, close_release_pc)
        + _wait()
    )


def _change_field(field: int, parameter: int = 0) -> bytes:
    return b"\x98" + _immediate(field) + _immediate(parameter)


def _play_music(music_id: int) -> bytes:
    return b"\x75" + _immediate(music_id)


def _play_sound_effect(sound_id: int) -> bytes:
    """Dispatch one field sound effect without starting a music sequence."""

    return b"\x74" + _immediate(sound_id)


def _chapter_one_stove_audio_helper() -> bytes:
    """Play a finite burner crackle from a size-neutral local subroutine."""

    return (
        _wait(CHAPTER_ONE_STOVE_CLICK_HOLD_FRAMES)
        + _play_sound_effect(CHAPTER_ONE_STOVE_FIRE_SOUND_ID)
        + _wait(CHAPTER_ONE_STOVE_FIRE_HOLD_FRAMES)
        + _play_sound_effect(CHAPTER_ONE_FIELD_SOUND_STOP_ID)
        + b"\x0D"
    )


def _install_chapter_one_stove_audio_helper(script: bytes) -> bytes:
    """Replace one retired field-229 routine with the burner subroutine."""

    editor = AtelScript(script)
    start = CHAPTER_ONE_STOVE_AUDIO_HELPER_PC
    end = start + len(CHAPTER_ONE_STOVE_AUDIO_HELPER_SOURCE)
    if editor.bytecode[start:end] != CHAPTER_ONE_STOVE_AUDIO_HELPER_SOURCE:
        raise RicoArcBuildError("Chapter 1 retired stove-audio cave changed")
    result = bytearray(editor.to_bytes())
    file_start = editor.bytecode_offset + start
    result[file_start : file_start + len(CHAPTER_ONE_STOVE_AUDIO_HELPER_SOURCE)] = (
        _chapter_one_stove_audio_helper()
    )
    return bytes(result)


class RoutineBuilder:
    """Absolute-PC ATEL label patcher for the anthology's menu routine."""

    def __init__(self, base: int):
        self.base = base
        self.data = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    @property
    def pc(self) -> int:
        return self.base + len(self.data)

    def emit(self, encoded: bytes) -> None:
        self.data.extend(encoded)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise RicoArcBuildError(f"Duplicate routine label: {name}")
        self.labels[name] = len(self.data)

    def jump(self, label: str) -> None:
        self.data.append(0x01)
        self.fixups.append((len(self.data), label))
        self.data.extend(b"\x00\x00")

    def jump_if_not_equal(self, variable: int, value: int, label: str) -> None:
        self.data.extend(b"\x02" + _u16(variable) + _s16(value) + b"\x40")
        self.fixups.append((len(self.data), label))
        self.data.extend(b"\x00\x00")

    def finish(self) -> bytes:
        result = bytearray(self.data)
        for offset, label in self.fixups:
            if label not in self.labels:
                raise RicoArcBuildError(f"Undefined routine label: {label}")
            result[offset : offset + 2] = _u16(self.base + self.labels[label])
        return bytes(result)


def _mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RicoArcBuildError(f"{context} must be a JSON object")
    return value


def _integer(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RicoArcBuildError(f"{context} must be an integer")
    return value


def load_chapters(manifest_path: Path = STORY_MANIFEST) -> tuple[Chapter, ...]:
    try:
        manifest = _mapping(
            json.loads(manifest_path.read_text(encoding="utf-8")),
            "Story manifest",
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RicoArcBuildError(f"Cannot read story manifest {manifest_path}: {exc}") from exc
    if manifest.get("format") != "xenogears-rico-anthology-v1":
        raise RicoArcBuildError("Story manifest format is not supported")
    filenames = manifest.get("chapters")
    if not isinstance(filenames, list) or len(filenames) != 7:
        raise RicoArcBuildError("Story manifest must name exactly seven chapters")

    chapters: list[Chapter] = []
    for expected_id, filename in enumerate(filenames, start=1):
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise RicoArcBuildError(f"Unsafe chapter filename: {filename!r}")
        path = manifest_path.parent / filename
        try:
            document = _mapping(
                json.loads(path.read_text(encoding="utf-8")),
                f"Chapter {expected_id}",
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RicoArcBuildError(f"Cannot read chapter {path}: {exc}") from exc
        if document.get("format") != "xenogears-rico-chapter-v1":
            raise RicoArcBuildError(f"Chapter {path.name} format is not supported")
        chapter_id = _integer(document.get("id"), f"{path.name} id")
        if chapter_id != expected_id:
            raise RicoArcBuildError(
                f"Chapter order mismatch: expected {expected_id}, got {chapter_id}"
            )
        blocks = document.get("blocks")
        if not isinstance(blocks, list) or not blocks or not all(
            isinstance(block, str) for block in blocks
        ):
            raise RicoArcBuildError(f"Chapter {chapter_id} has no valid dialogue blocks")
        chapter = Chapter(
            chapter_id=chapter_id,
            title=str(document.get("title", "")),
            disc=_integer(document.get("disc"), f"Chapter {chapter_id} disc"),
            target_field=_integer(
                document.get("target_field"), f"Chapter {chapter_id} target field"
            ),
            donor_field=_integer(
                document.get("donor_field"), f"Chapter {chapter_id} donor field"
            ),
            music=_integer(document.get("music"), f"Chapter {chapter_id} music"),
            selection_exposition=str(document.get("selection_exposition", "")),
            blocks=tuple(blocks),
            source_path=path,
        )
        if chapter.disc not in (1, 2):
            raise RicoArcBuildError(f"Chapter {chapter_id} disc must be 1 or 2")
        expected_disc = 1 if chapter_id <= 3 else 2
        if chapter.disc != expected_disc:
            raise RicoArcBuildError(
                f"Chapter {chapter_id} must be on Disc {expected_disc}"
            )
        if not chapter.title:
            raise RicoArcBuildError(f"Chapter {chapter_id} has no title")
        if not chapter.selection_exposition:
            raise RicoArcBuildError(
                f"Chapter {chapter_id} has no selection exposition"
            )
        chapters.append(chapter)

    targets = [chapter.target_field for chapter in chapters]
    if len(targets) != len(set(targets)):
        raise RicoArcBuildError("Chapter target fields must be unique")
    expected_targets = [721, 722, 723, 230, 231, 232, 233]
    if targets != expected_targets:
        raise RicoArcBuildError(
            f"Chapter target allocation changed: {targets}, expected {expected_targets}"
        )
    if chapters[0].music != CHAPTER_ONE_MUSIC_ID:
        raise RicoArcBuildError(
            "Chapter 1 must retain retail Rico-memory music "
            f"{CHAPTER_ONE_MUSIC_ID:#04x}"
        )
    return tuple(chapters)


def _dialogue_visible_text(fragment: str) -> str:
    """Return only glyphs rendered by one dialogue-line fragment."""

    output: list[str] = []
    position = 0
    while position < len(fragment):
        character = fragment[position]
        if character != "<":
            if character not in PLAIN_ENCODE and character != "\n":
                raise RicoArcBuildError(
                    f"Unsupported dialogue-layout glyph {character!r}"
                )
            output.append(character)
            position += 1
            continue
        end = fragment.find(">", position + 1)
        if end < 0:
            raise RicoArcBuildError("Unterminated dialogue-layout token")
        token = fragment[position + 1 : end]
        if token in CHARACTER_IDS:
            output.append(token)
        elif token in DIALOGUE_ZERO_WIDTH_TOKENS or DIALOGUE_DELAY_TOKEN.fullmatch(
            token
        ):
            pass
        else:
            raise RicoArcBuildError(f"Opaque dialogue-layout token <{token}>")
        position = end + 1
    return "".join(output)


def _dialogue_units(fragment: str) -> int:
    """Measure the native renderer's four-pixel horizontal units."""

    return sum(
        2 if PLAIN_ENCODE[character] <= 0x63 else 3
        for character in _dialogue_visible_text(fragment)
        if character != "\n"
    )


def _wrap_dialogue_words(text: str, capacity: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    rows: list[str] = []
    line = ""
    for word in words:
        if _dialogue_units(word) > capacity:
            raise RicoArcBuildError(
                f"Dialogue word exceeds the native window width: {word!r}"
            )
        candidate = word if not line else f"{line} {word}"
        if _dialogue_units(candidate) <= capacity:
            line = candidate
        else:
            rows.append(line)
            line = word
    rows.append(line)
    return rows


def _is_dialogue_all_upper(fragment: str) -> bool:
    visible = _dialogue_visible_text(fragment)
    return any(character.isalpha() for character in visible) and not any(
        character.islower() for character in visible
    )


def _is_dialogue_label_row(row: str) -> bool:
    if row in DIALOGUE_PLAIN_SPEAKERS:
        return True
    match = DIALOGUE_TOKEN.fullmatch(row)
    if match and match.group(1) in CHARACTER_IDS:
        return True
    return _is_dialogue_all_upper(row)


def _layout_dialogue_page(page: str, capacity: int) -> tuple[list[str], bool]:
    original = page.split("\n")
    if page.startswith(DIALOGUE_CHOICE_START):
        if any(_dialogue_units(row) > capacity for row in original):
            raise RicoArcBuildError("Choice row exceeds the native dialogue width")
        return original, True

    if _is_dialogue_all_upper(page):
        # Authored all-caps rows are chapter cards or terminal records.  Their
        # row boundaries carry meaning, so wrap each row independently.
        rows: list[str] = []
        for row in original:
            rows.extend(_wrap_dialogue_words(row, capacity))
        return rows, False

    if original and _is_dialogue_label_row(original[0]):
        return original[:1] + _wrap_dialogue_words(
            " ".join(original[1:]), capacity
        ), False

    # Prose and stage directions used hand-inserted visual wraps.  Rebalance
    # them at word boundaries for the actual USA renderer width.
    return _wrap_dialogue_words(" ".join(original), capacity), False


def _dialogue_layout_issues(
    text: str,
    width: int = DIALOGUE_WINDOW_WIDTH,
    height: int = DIALOGUE_WINDOW_HEIGHT,
) -> tuple[str, ...]:
    if not text.endswith("<Close>") or text.count("<Close>") != 1:
        raise RicoArcBuildError(
            "Dialogue layout requires exactly one terminal <Close>"
        )
    capacity = width | 1
    issues: list[str] = []
    for page_number, page in enumerate(text[: -len("<Close>")].split("<New>"), 1):
        rows = page.split("\n")
        if len(rows) > height:
            issues.append(
                f"page {page_number} has {len(rows)} rows; maximum is {height}"
            )
        for row_number, row in enumerate(rows, 1):
            units = _dialogue_units(row)
            if units > capacity:
                issues.append(
                    f"page {page_number} row {row_number} uses {units} units; "
                    f"maximum is {capacity}"
                )
    return tuple(issues)


def _dialogue_sentence_page_issues(text: str) -> tuple[str, ...]:
    """Report page turns that interrupt a sentence in laid-out dialogue."""

    if not text.endswith("<Close>") or text.count("<Close>") != 1:
        raise RicoArcBuildError(
            "Dialogue pagination requires exactly one terminal <Close>"
        )
    pages = text[: -len("<Close>")].split("<New>")
    issues: list[str] = []
    for page_number, page in enumerate(pages[:-1], 1):
        visible = _dialogue_visible_text(page).strip()
        sentence_tail = visible
        while sentence_tail and sentence_tail[-1] in DIALOGUE_SENTENCE_CLOSERS:
            sentence_tail = sentence_tail[:-1].rstrip()
        if not sentence_tail or sentence_tail[-1] not in ".!?":
            tail = visible.splitlines()[-1] if visible else "<empty>"
            issues.append(
                f"page {page_number} turns before its sentence ends: {tail!r}"
            )
    return tuple(issues)


def _dialogue_window_dimensions(text: str) -> tuple[int, int]:
    """Fit one native window to the widest and tallest page in a block."""

    issues = _dialogue_layout_issues(text)
    if issues:
        raise RicoArcBuildError(
            "Dialogue dimensions require laid-out text: " + "; ".join(issues)
        )
    pages = text[: -len("<Close>")].split("<New>")
    rows = [page.split("\n") or [""] for page in pages]
    widest = max(
        (_dialogue_units(row) for page_rows in rows for row in page_rows),
        default=0,
    )
    # Native window widths are even.  An even value N provides N|1 units of
    # usable space, so rounding an odd measured row down remains exact.
    width = max(DIALOGUE_WINDOW_MIN_WIDTH, widest & ~1)
    height = max(len(page_rows) for page_rows in rows)
    if width > DIALOGUE_WINDOW_WIDTH or height > DIALOGUE_WINDOW_HEIGHT:
        raise RicoArcBuildError(
            f"Fitted dialogue window {width}x{height} exceeds the native "
            f"{DIALOGUE_WINDOW_WIDTH}x{DIALOGUE_WINDOW_HEIGHT} maximum"
        )
    return width, height


def _semantic_dialogue_atoms(text: str) -> tuple[str, ...]:
    return tuple(
        text.replace("<New>", " ")
        .replace("\n", " ")
        .replace("<Close>", "")
        .split()
    )


def _reflow_dialogue_text_once(
    text: str,
    width: int,
    height: int,
) -> str:
    if not text.endswith("<Close>") or text.count("<Close>") != 1:
        raise RicoArcBuildError(
            "Dialogue layout requires exactly one terminal <Close>"
        )
    capacity = width | 1
    output_pages: list[str] = []
    for source_page in text[: -len("<Close>")].split("<New>"):
        rows, is_choice = _layout_dialogue_page(source_page, capacity)
        if is_choice and len(rows) > height:
            raise RicoArcBuildError("Choice menu exceeds the native dialogue height")
        rows = rows or [""]
        for start in range(0, len(rows), height):
            output_pages.append("\n".join(rows[start : start + height]))
    return "<New>".join(output_pages) + "<Close>"


def _reflow_dialogue_text(
    text: str,
    width: int = DIALOGUE_WINDOW_WIDTH,
    height: int = DIALOGUE_WINDOW_HEIGHT,
    *,
    sentence_safe_pages: bool = False,
) -> str:
    result = _reflow_dialogue_text_once(text, width, height)
    if _semantic_dialogue_atoms(result) != _semantic_dialogue_atoms(text):
        raise RicoArcBuildError("Dialogue reflow changed semantic text or controls")
    issues = _dialogue_layout_issues(result, width, height)
    if issues:
        raise RicoArcBuildError("Dialogue does not fit: " + "; ".join(issues))
    if sentence_safe_pages:
        sentence_issues = _dialogue_sentence_page_issues(result)
        if sentence_issues:
            raise RicoArcBuildError(
                "Dialogue sentence crosses a page turn: "
                + "; ".join(sentence_issues)
            )
    if _reflow_dialogue_text_once(result, width, height) != result:
        raise RicoArcBuildError("Dialogue reflow is not deterministic")
    return result


def _playable_choice_count(text: str) -> int:
    """Validate one stage-local menu and return its selectable row count."""

    if not isinstance(text, str):
        raise RicoArcBuildError("Playable stage choice text must be a string")
    laid_out = _reflow_dialogue_text(text)
    body = laid_out[: -len("<Close>")]
    if "<New>" in body or not body.startswith(DIALOGUE_CHOICE_START):
        raise RicoArcBuildError(
            "Playable stage choice must be one page beginning with the "
            "choice control"
        )
    rows = body.split("\n")
    title = rows[0][len(DIALOGUE_CHOICE_START) :]
    if not _dialogue_visible_text(title).strip():
        raise RicoArcBuildError("Playable stage choice must have a title row")
    choices = rows[1:]
    if not 2 <= len(choices) <= 0x0F or any(
        not _dialogue_visible_text(row).strip() for row in choices
    ):
        raise RicoArcBuildError(
            "Playable stage choice must have between 2 and 15 nonempty rows"
        )
    return len(choices)


def _dialogue_data(
    blocks: Sequence[str],
    *,
    fit_windows: bool = False,
    sentence_safe_pages: bool = False,
) -> bytes:
    laid_out = tuple(
        _reflow_dialogue_text(
            text,
            sentence_safe_pages=sentence_safe_pages,
        )
        for text in blocks
    )
    dimensions = tuple(
        _dialogue_window_dimensions(text)
        if fit_windows
        else (DIALOGUE_WINDOW_WIDTH, DIALOGUE_WINDOW_HEIGHT)
        for text in laid_out
    )
    specs = tuple(
        DialogueBlockSpec(
            block_id=index,
            width=width,
            height=height,
            text=text,
        )
        for index, (text, (width, height)) in enumerate(
            zip(laid_out, dimensions, strict=True)
        )
    )
    encoded = encode_dialogue(specs)
    parsed = parse_dialogue(encoded)
    if tuple(block.text for block in parsed.blocks) != laid_out:
        raise RicoArcBuildError("Laid-out dialogue failed round-trip")
    return encoded


def validate_story(chapters: Sequence[Chapter]) -> dict[str, Any]:
    details = []
    for chapter in chapters:
        chapter_one = chapter.chapter_id == 1
        dialogue = _dialogue_data(
            chapter.blocks,
            fit_windows=chapter_one,
            sentence_safe_pages=chapter_one,
        )
        selection_dialogue = _dialogue_data(
            (chapter.selection_exposition,),
            fit_windows=chapter_one,
            sentence_safe_pages=chapter_one,
        )
        details.append(
            {
                "id": chapter.chapter_id,
                "title": chapter.title,
                "disc": chapter.disc,
                "target_field": chapter.target_field,
                "donor_field": chapter.donor_field,
                "block_count": len(chapter.blocks),
                "dialogue_size": len(dialogue),
                "dialogue_sha256": _sha256_bytes(dialogue),
                "selection_exposition_sha256": _sha256_bytes(
                    selection_dialogue
                ),
                "authored_sha256": _sha256_file(chapter.source_path),
            }
        )
    return {
        "chapter_count": len(chapters),
        "installed_fields": {
            f"disc{disc}": {
                str(chapter_id): field
                for chapter_id, field in CHAPTER_FIELDS[disc].items()
            }
            for disc in (1, 2)
        },
        "chapters": details,
    }


def _field_bundle_id(field: int) -> int:
    if not 0 <= field <= 0x7FFF:
        raise RicoArcBuildError(f"Field outside canonical range: {field}")
    return FIELD_BUNDLE_BASE + field * 2


class DiscReader:
    def __init__(self, path: Path, disc: int):
        self.path = path.resolve()
        self.disc = disc
        self.image = Mode2Image(self.path)
        self.entries = self.image.read_index()
        self.cache: dict[int, bytes] = {}

    def canonical(self, canonical_id: int) -> bytes:
        if canonical_id not in self.cache:
            physical = canonical_id if self.disc == 1 else canonical_id - 5
            if physical < 0 or physical >= len(self.entries):
                raise RicoArcBuildError(
                    f"Disc {self.disc} canonical {canonical_id} is outside its FAT"
                )
            entry = self.entries[physical]
            if entry.kind != "file":
                raise RicoArcBuildError(
                    f"Disc {self.disc} canonical {canonical_id} is {entry.kind}"
                )
            self.cache[canonical_id] = self.image.extract_entry(entry)
        return self.cache[canonical_id]


def validate_disc(path: Path, disc: int) -> tuple[int, str]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise RicoArcBuildError(f"Disc {disc} source does not exist: {resolved}")
    size = resolved.stat().st_size
    digest = _sha256_file(resolved)
    expected = DISC_IDENTITIES[disc]
    if (size, digest) != expected:
        raise RicoArcBuildError(
            f"Disc {disc} source mismatch: size {size}, SHA-256 {digest}; "
            f"expected {expected[0]}, {expected[1]}"
        )
    Mode2Image(resolved).read_index()
    return size, digest


def _sanitized_director(music: int) -> bytes:
    # BC is the shared first director opcode in the Nortune donor rooms.  It
    # performs the native field actor setup.  Keep the director invisible and
    # ineligible for Cross activation, then select the donor's music and STOP
    # before any retail story branch can execute.
    return INERT_HIDDEN_INIT[:-1] + _play_music(music) + b"\x00"


def _copy_chapter_two_state_to_persistent() -> bytes:
    """Preserve Chapter 2 progress across its optional bedroom field load."""

    return atel.copy_variable(
        CHAPTER_TWO_PERSISTENT_STATE_VARIABLE,
        PLAYABLE_STATE_VARIABLE,
    )


def _restore_chapter_two_state() -> bytes:
    """Restore the sitting-room objective mask after either room initializes."""

    return atel.copy_variable(
        PLAYABLE_STATE_VARIABLE,
        CHAPTER_TWO_PERSISTENT_STATE_VARIABLE,
    )


def _chapter_two_director(music: int) -> bytes:
    """Sanitize a Chapter 2 room while restoring its cross-field state."""

    return (
        INERT_HIDDEN_INIT[:-1]
        + _restore_chapter_two_state()
        + _play_music(music)
        + b"\x00"
    )


def _chapter_two_main_bedroom_action(target_field: int) -> bytes:
    """Save progress, then reuse field 218's authentic bedroom-door action."""

    if not 0 <= target_field <= 0x7FFF:
        raise RicoArcBuildError("Chapter 2 bedroom target is outside field range")
    # Retail prepends a story-variable JUMP_IF that leads to its old
    # "No good. It's locked." response.  The anthology bedroom is always
    # optional and available, so retain the exact native open/walk traversal
    # beginning at OP15 while deliberately dropping only that lock branch.
    native = CHAPTER_TWO_MAIN_DOOR_ACTION_BODY[8:]
    expected_tail = _immediate(CHAPTER_TWO_BEDROOM_DONOR_FIELD) + _immediate(0) + b"\x5B"
    if not native.endswith(expected_tail):
        raise RicoArcBuildError("Chapter 2 native bedroom-door target changed")
    return (
        _copy_chapter_two_state_to_persistent()
        + native[: -len(expected_tail)]
        + _immediate(target_field)
        + _immediate(0)
        + b"\x5B"
    )


def _chapter_two_bedroom_return_action(main_field: int) -> bytes:
    """Save progress, then reuse field 219's authentic return-door action."""

    if not 0 <= main_field <= 0x7FFF:
        raise RicoArcBuildError("Chapter 2 sitting-room target is outside field range")
    native = CHAPTER_TWO_BEDROOM_DOOR_ACTION_BODY
    expected_tail = _immediate(CHAPTER_TWO_MAIN_FIELD_DONOR) + _immediate(2) + b"\x5B"
    if not native.endswith(expected_tail):
        raise RicoArcBuildError("Chapter 2 native return-door target changed")
    return (
        _copy_chapter_two_state_to_persistent()
        + native[: -len(expected_tail)]
        + _immediate(main_field)
        + _immediate(2)
        + b"\x5B"
    )


def _chapter_two_hammer_init() -> bytes:
    """Initialize authentic bank-4 Hammer at the foot of the stairs."""

    x, z, _triangle = CHAPTER_TWO_HAMMER_STAGE_POSITION
    return (
        b"\x0B"
        + _immediate(CHAPTER_TWO_HAMMER_ACTOR_BANK)
        + b"\x19"
        + _s16(x)
        + _s16(z)
        + b"\xC0\x1A\x00"
        + PLAYABLE_ACTOR_GHOST_FLAGS
        + b"\x00"
    )


def _chapter_two_hammer_stair_route(base_pc: int) -> bytes:
    """Stage Hammer once, or snap him upstairs after a bedroom reload."""

    routine = mass_driver._RoutineBuilder(base_pc)
    routine.jump_if_bit_clear(
        CHAPTER_TWO_HAMMER_STATE_VARIABLE,
        1 << CHAPTER_TWO_HAMMER_ARRIVED_BIT,
        "climb",
    )
    end_x, end_z, _end_triangle = CHAPTER_TWO_HAMMER_ROUTE[-1]
    routine.emit(
        b"\x19"
        + _s16(end_x)
        + _s16(end_z)
        + b"\xC0"
        + PLAYABLE_ACTOR_SOLID_FLAGS
        + b"\x5F\x04\x5B"
    )
    routine.label("climb")
    body = bytearray()
    for x, z, _triangle in CHAPTER_TWO_HAMMER_ROUTE:
        position = _s16(x) + _s16(z)
        body.extend(
            b"\x4B"
            + position
            + b"\xC0"
            + _immediate(CHAPTER_TWO_HAMMER_ROUTE_MAX_STEPS)
            + b"\x19"
            + position
            + b"\xC0"
        )
    body.extend(
        atel.set_var_bit(
            CHAPTER_TWO_HAMMER_STATE_VARIABLE,
            CHAPTER_TWO_HAMMER_ARRIVED_BIT,
        )
        + PLAYABLE_ACTOR_SOLID_FLAGS
        + b"\x5F\x04\x5B"
    )
    routine.emit(bytes(body))
    return routine.finish()


def _chapter_two_hammer_controller_gate(
    base_pc: int,
    x: int,
    z: int,
) -> bytes:
    """Keep Hammer's upstairs hotspot parked until his climb completes."""

    routine = mass_driver._RoutineBuilder(base_pc)
    routine.label("poll")
    routine.jump_if_bit_clear(
        CHAPTER_TWO_HAMMER_STATE_VARIABLE,
        1 << CHAPTER_TWO_HAMMER_ARRIVED_BIT,
        "wait",
    )
    routine.emit(b"\x19" + _s16(x) + _s16(z) + b"\xC0")
    routine.label("enabled")
    routine.emit(_wait())
    routine.jump("enabled")
    routine.label("wait")
    routine.emit(_wait())
    routine.jump("poll")
    return routine.finish()


def _chapter_two_hammer_actor_action_gate(
    base_pc: int,
    action_pc: int,
) -> bytes:
    """Ignore Cross on moving Hammer, then forward after he reaches Rico."""

    routine = mass_driver._RoutineBuilder(base_pc)
    routine.jump_if_bit_clear(
        CHAPTER_TWO_HAMMER_STATE_VARIABLE,
        1 << CHAPTER_TWO_HAMMER_ARRIVED_BIT,
        "inactive",
    )
    routine.emit(_jump(action_pc))
    routine.label("inactive")
    routine.emit(_playable_action_prefix(routine.pc))
    routine.emit(_playable_action_finish(routine.pc))
    return routine.finish()


def _playable_silent_update() -> bytes:
    """Keep the destination field silent after its prelaunch exposition."""

    # RESET_FIELD_SCRIPT_ACTOR_FOREVER is the proven inert update terminator.
    # STOP would restart this update every frame.
    return b"\x5B"


def _append_dialogue_blocks(
    source: bytes,
    texts: Sequence[str],
    *,
    fit_windows: bool = False,
    sentence_safe_pages: bool = False,
) -> tuple[bytes, int]:
    """Append dialogue without re-encoding potentially irregular retail blocks.

    A few released fields contain harmless bytes after a Close token, so the
    strict dialogue parser quite correctly refuses to normalize them.  Moving
    the existing offset/dimension tables and preserving their payload verbatim
    keeps every native script ID stable while giving the playable controllers
    a collision-free authored ID range.
    """

    if len(source) < 8:
        raise RicoArcBuildError("Donor dialogue component is truncated")
    old_count = struct.unpack_from("<I", source, 0)[0] + 1
    old_header_size = 4 + old_count * 4
    if old_header_size > len(source):
        raise RicoArcBuildError("Donor dialogue header exceeds its component")
    old_offsets = tuple(
        struct.unpack_from("<H", source, 4 + index * 2)[0]
        for index in range(old_count)
    )
    if (
        not old_offsets
        or old_offsets[0] != old_header_size
        or tuple(sorted(old_offsets)) != old_offsets
        or len(set(old_offsets)) != old_count
        or old_offsets[-1] >= len(source)
    ):
        raise RicoArcBuildError("Donor dialogue offset table is invalid")
    old_dimensions_start = 4 + old_count * 2
    old_dimensions = source[
        old_dimensions_start : old_dimensions_start + old_count * 2
    ]
    old_payload = source[old_header_size:]

    laid_out = tuple(
        _reflow_dialogue_text(
            text,
            sentence_safe_pages=sentence_safe_pages,
        )
        for text in texts
    )
    payloads = tuple(encode_text(text) for text in laid_out)
    new_count = old_count + len(payloads)
    new_header_size = 4 + new_count * 4
    shift = new_header_size - old_header_size
    shifted_offsets = tuple(offset + shift for offset in old_offsets)
    cursor = new_header_size + len(old_payload)
    appended_offsets: list[int] = []
    for payload in payloads:
        if cursor > 0xFFFF:
            raise RicoArcBuildError("Playable dialogue offset exceeds u16")
        appended_offsets.append(cursor)
        cursor += len(payload)
    if cursor > 0xFFFF:
        raise RicoArcBuildError("Playable dialogue component exceeds 64 KiB")

    output = bytearray(struct.pack("<I", new_count - 1))
    for offset in (*shifted_offsets, *appended_offsets):
        output.extend(_u16(offset))
    output.extend(old_dimensions)
    for text in laid_out:
        dimensions = (
            _dialogue_window_dimensions(text)
            if fit_windows
            else (DIALOGUE_WINDOW_WIDTH, DIALOGUE_WINDOW_HEIGHT)
        )
        output.extend(bytes(dimensions))
    output.extend(old_payload)
    for payload in payloads:
        output.extend(payload)
    if len(output) != cursor:
        raise RicoArcBuildError("Playable dialogue append size drifted")
    return bytes(output), old_count


def _chapter_selection_exposition(chapter: Chapter) -> tuple[str, ...]:
    """Return timeline framing, never gameplay instructions, before launch."""

    if (
        not 1 <= chapter.chapter_id <= 7
        or not chapter.blocks
        or not chapter.selection_exposition
    ):
        raise RicoArcBuildError("Chapter selection exposition is incomplete")
    if "objective" in chapter.selection_exposition.casefold():
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} selection exposition contains "
            "gameplay instructions"
        )
    return (chapter.blocks[0], chapter.selection_exposition)


def _playable_custom_texts(
    contract: PlayableChapter,
    *,
    additional_texts: Sequence[str] = (),
) -> tuple[str, ...]:
    ordered: list[str] = [
        *(text for _bit, text in contract.exit_locked_steps),
        (
            PLAYABLE_FINAL_HUB_CHOICE
            if contract.chapter_id == 7
            else PLAYABLE_NEXT_OR_HUB_CHOICE
        ),
    ]
    for interaction in contract.interactions:
        ordered.extend(
            ref for ref in interaction.repeat_dialogue if isinstance(ref, str)
        )
        for stage in interaction.stages:
            ordered.extend(ref for ref in stage.dialogue if isinstance(ref, str))
            if stage.choice_text is not None:
                ordered.append(stage.choice_text)
            ordered.extend(
                ref
                for ref in stage.rejection_dialogue
                if isinstance(ref, str)
            )
            ordered.extend(
                ref for ref in stage.after_dialogue if isinstance(ref, str)
            )
            ordered.extend(
                ref for ref in stage.locked_dialogue if isinstance(ref, str)
            )
            for _missing_bit, step_dialogue in stage.locked_dialogue_steps:
                ordered.extend(
                    ref for ref in step_dialogue if isinstance(ref, str)
                )
            for _completed_bits, state_dialogue in stage.locked_dialogue_states:
                ordered.extend(
                    ref for ref in state_dialogue if isinstance(ref, str)
                )
    if contract.exit_transition is not None:
        transition = contract.exit_transition
        for refs in (
            transition.doorway_dialogue,
            transition.firewood_dialogue,
            transition.sickness_dialogue,
            transition.loss_dialogue,
            transition.funeral_dialogue,
        ):
            ordered.extend(ref for ref in refs if isinstance(ref, str))
    ordered.extend(ref for ref in contract.exit_dialogue if isinstance(ref, str))
    if not all(isinstance(text, str) and text for text in additional_texts):
        raise RicoArcBuildError("Additional playable dialogue must be nonempty text")
    ordered.extend(additional_texts)
    unique: list[str] = []
    seen: set[str] = set()
    for text in ordered:
        if text not in seen:
            seen.add(text)
            unique.append(text)
    return tuple(unique)


def _resolve_playable_dialogue(
    refs: Iterable[DialogueRef],
    *,
    authored_base: int,
    authored_count: int,
    custom_ids: dict[str, int],
) -> tuple[int, ...]:
    result: list[int] = []
    for ref in refs:
        if isinstance(ref, int):
            if not 0 <= ref < authored_count:
                raise RicoArcBuildError(
                    f"Playable dialogue reference {ref} exceeds {authored_count} blocks"
                )
            result.append(authored_base + ref)
        else:
            try:
                result.append(custom_ids[ref])
            except KeyError as exc:
                raise RicoArcBuildError(
                    f"Playable custom dialogue was not allocated: {ref!r}"
                ) from exc
    return tuple(result)


def _insert_dynamic_actor_records(
    header: bytes,
    *,
    old_entity_count: int,
    records_to_insert: Sequence[bytes],
) -> bytes:
    if len(header) < 0x190:
        raise RicoArcBuildError("Playable donor actor header is truncated")
    actor_count = struct.unpack_from("<H", header, 0x18C)[0]
    if len(header) != 0x190 + actor_count * 16 or old_entity_count > actor_count:
        raise RicoArcBuildError("Playable donor actor table boundary changed")
    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(actor_count)
    ]
    if any(len(record) != 16 for record in records_to_insert):
        raise RicoArcBuildError("Playable dynamic actor record is not 16 bytes")
    records[old_entity_count:old_entity_count] = records_to_insert
    result = bytearray(header[:0x190] + b"".join(records))
    struct.pack_into("<H", result, 0x18C, len(records))
    return bytes(result)


def _place_actor_record(header: bytes, entity: int, x: int, z: int) -> bytes:
    actor_count = struct.unpack_from("<H", header, 0x18C)[0]
    if not 0 <= entity < actor_count:
        raise RicoArcBuildError(
            f"Playable entry actor {entity} exceeds {actor_count} records"
        )
    if not all(-0x8000 <= value <= 0x7FFF for value in (x, z)):
        raise RicoArcBuildError("Playable entry position is outside s16")
    result = bytearray(header)
    record = 0x190 + entity * 16
    struct.pack_into("<h", result, record + 8, x)
    struct.pack_into("<h", result, record + 12, z)
    return bytes(result)


def _registered_character_entities(editor: AtelScript) -> dict[int, int]:
    result: dict[int, int] = {}
    for entity in range(editor.entity_count):
        pc = editor.get_script_pointer(entity, 0)
        body = editor.bytecode[pc : pc + 7]
        if len(body) != 7 or body[0] != 0x16 or body[3:5] != b"\xFE\x0D":
            continue
        first = struct.unpack_from("<H", body, 1)[0]
        second = struct.unpack_from("<H", body, 5)[0]
        if first & 0x8000 and second == first:
            character = first & 0x7FFF
            if 0 <= character <= 10 and character not in result:
                result[character] = entity
    return result


def _normalize_playable_party_script(chapter: Chapter, script: bytes) -> bytes:
    """Turn variable donor party actors into the three live party selectors.

    Nortune fields 232 and 235 register their actors from story variables
    rather than fixed character IDs.  Treating those entities as absent and
    adding eleven more carriers registers the same party twice.  Keep the
    authentic three donor actors and replace only their checked operands.
    """

    contract = VARIABLE_PARTY_DONORS.get(chapter.donor_field)
    if contract is None:
        return script
    pcs, source_operands = contract
    return _patch_donor_party(script, pcs, source_operands)


def _playable_native_party_entities(
    chapter: Chapter,
    editor: AtelScript,
) -> set[int]:
    if chapter.donor_field in VARIABLE_PARTY_DONORS:
        return {1, 2, 3}
    return set(_registered_character_entities(editor).values())


def _missing_playable_characters(
    chapter: Chapter,
    editor: AtelScript,
) -> tuple[int, ...]:
    # Variable-party donors already expose selectors FD/FE/FF through e1-e3;
    # those selectors follow the current party and must not be duplicated by
    # fixed-character carriers.
    if chapter.donor_field in VARIABLE_PARTY_DONORS:
        return ()
    registered = _registered_character_entities(editor)
    return tuple(character for character in range(11) if character not in registered)


def _normalized_party_init(
    selector: int,
    position: tuple[int, int] | None = None,
) -> bytes:
    result = bytearray(
        b"\x16"
        + _immediate(selector)
        + b"\xFE\x0D"
        + _immediate(selector)
    )
    if position is not None:
        x, z = position
        result.extend(b"\x19" + _s16(x) + _s16(z) + b"\xC0\x1A\x00")
    result.append(0)
    return bytes(result)


def _young_rico_party_init(x: int, z: int) -> bytes:
    """Use field 229's native young-Rico bank as the controlled Rico actor.

    INIT_ENTITY_PC must run first: it registers Rico in party slot zero, sets
    the controlled-actor flag, and attaches the normal player update path.
    INIT_ENTITY_NPC then replaces only that actor's visual with field 229's
    local young-Rico bank.  The engine's implementations leave the party
    mapping and controlled-actor flag intact during that second graphic reset.
    This avoids both the donor's transparent adult staging and an inert child
    NPC masquerading as the player.
    """

    return (
        b"\x16"
        + _immediate(YOUNG_RICO_ID)
        + b"\x0B"
        + _immediate(1)
        + b"\xFE\x0D"
        # Keep Rico's normal dialogue portrait mapping while the menu uses the
        # dedicated character-10 portrait sheet slot.
        + _immediate(RICO_ID)
        + b"\x19"
        + _s16(x)
        + _s16(z)
        + b"\xC0\x1A\x00\x00"
    )


def _battle_configurations(contract: PlayableChapter) -> dict[int, bool]:
    """Map each used formation to its required character/Gear scale."""

    configurations: dict[int, bool] = {}
    for interaction in contract.interactions:
        for stage in interaction.stages:
            configuration = stage.battle_configuration
            if configuration is None:
                continue
            previous = configurations.setdefault(configuration, stage.gear_battle)
            if previous != stage.gear_battle:
                raise RicoArcBuildError(
                    f"Formation {configuration} is requested at two battle scales"
                )
    return configurations


def _install_playable_encounters(
    source: bytes,
    contract: PlayableChapter,
) -> bytes:
    """Install deterministic, no-Escape fixed fights and disable random ones."""

    configurations = _battle_configurations(contract)
    if not source:
        if configurations:
            raise RicoArcBuildError("Playable battle donor has no encounter table")
        return source
    if (
        len(source) != ENCOUNTER_COMPONENT_SIZE
        or _sha256_bytes(source) != NORTUNE_ENCOUNTER_SHA256
    ):
        raise RicoArcBuildError("Playable donor encounter table changed")
    if not set(configurations) <= {6, 15}:
        raise RicoArcBuildError(
            f"Unaudited playable battle formations: {sorted(configurations)}"
        )

    result = bytearray(source)
    result[WEIGHTS_OFFSET : WEIGHTS_OFFSET + FORMATION_COUNT] = bytes(
        FORMATION_COUNT
    )

    source_six = bytes(result[6 * FORMATION_SIZE : 7 * FORMATION_SIZE])
    if source_six != NORTUNE_CONFIGURATION_6:
        raise RicoArcBuildError("Nortune Gear formation 6 changed")

    if 6 in configurations:
        result[6 * FORMATION_SIZE + 1] |= 0x80

    if 15 in configurations:
        destination = 15 * FORMATION_SIZE
        result[destination : destination + FORMATION_SIZE] = source_six
        result[destination + 1] |= 0x80
        # Protocol B uses one defense Gear rather than the donor formation's
        # two anonymous arena opponents.
        for slot in range(1, 8):
            result[destination + 0x08 + slot] = 0xFF
            result[destination + 0x18 + slot] = 0xFF

    return bytes(result)


def _playable_controller_init(
    x: int,
    z: int,
    *,
    half_width: int,
    half_depth: int,
    requires_facing: bool = True,
    initially_disabled: bool = False,
) -> bytes:
    if not all(1 <= value <= 0x7F for value in (half_width, half_depth)):
        raise RicoArcBuildError("Playable interaction bounds are outside 1..127")
    # Use the proven model-less Mass Driver carrier.  Unlike INIT_ENTITY_NPC,
    # this never attempts to load a local actor/sprite bank (field 298 has no
    # sprite payload at all), and it remains a facing-gated, non-colliding X
    # region over the authentic room prop.
    init_x, init_z = (
        PLAYABLE_CONTROLLER_PARK_POSITION if initially_disabled else (x, z)
    )
    return mass_driver._static_door_controller_init(
        init_x,
        init_z,
        requires_facing=requires_facing,
        interaction_half_width=half_width,
        interaction_half_depth=half_depth,
        invisible=True,
    )


def _chapter_one_door_departure_body() -> bytes:
    """Walk young Rico to the safe interior edge of the opened leaf."""

    x, z, _triangle = CHAPTER_ONE_DOOR_REPOSITION
    return (
        b"\x4B"
        + _s16(x)
        + _s16(z)
        + b"\xC0"
        + _immediate(CHAPTER_ONE_DOOR_DEPARTURE_MAX_STEPS)
        + b"\x00"
    )


def _chapter_one_door_turn_to_anna_body(leader_entity: int) -> bytes:
    """Turn young Rico back toward Anne before his doorstep question."""

    if not 0 <= leader_entity <= 0xFA:
        raise RicoArcBuildError("Chapter 1 Rico entity is outside 0..250")
    return (
        b"\xFE\x17"
        + bytes((leader_entity, CHAPTER_ONE_ANNA_ENTITY))
        + _wait(CHAPTER_ONE_DOOR_TURN_TO_ANNA_FRAMES)
    )


def _chapter_one_doorway_exchange_body(
    leader_entity: int,
    doorway_dialogue_ids: Sequence[int],
) -> bytes:
    """Turn Rico toward Anne for their final conversation in the house."""

    dialogue_ids = tuple(doorway_dialogue_ids)
    if len(dialogue_ids) != 2:
        raise RicoArcBuildError(
            "Chapter 1 doorway conversation requires two dialogue blocks"
        )
    rico_question = dialogue_ids[0]

    return (
        # This transition runs on an invisible controller, so turn Rico's
        # visible party actor toward Anne by their live field positions.
        _chapter_one_door_turn_to_anna_body(leader_entity)
        + _dialogue_sequence((rico_question,))
        # Anne visibly coughs after Rico's first question, then the complete
        # alternating conversation plays before the door is allowed to open.
        + CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL
        + _dialogue_sequence(dialogue_ids[1:])
    )


def _chapter_one_door_transition_body(
    firewood_field: int = CHAPTER_ONE_FIREWOOD_FIELD,
) -> bytes:
    """Open the native leaf and fade into the daylight firewood scene."""

    return (
        # The native wooden leaf must finish its sound/hinge helper first.
        # Rico's cosmetic approach is asynchronous so it can never hold the
        # field transition hostage; after eight visible frames the fade owns
        # the crossing and the destination initializes under black.
        b"\x09"
        + bytes(
            (
                CHAPTER_ONE_DOOR_ENTITY,
                CHAPTER_ONE_DOOR_OPEN_SCRIPT | 0x20,
            )
        )
        + b"\x07\xFF"
        + bytes((CHAPTER_ONE_DOOR_DEPARTURE_SCRIPT | 0x20,))
        + _wait(CHAPTER_ONE_DOOR_DEPARTURE_VISIBLE_FRAMES)
        + mass_driver._facility_video_screen_fade_body(0xFF, 32)
        + _change_field(firewood_field, 0)
        + b"\x5B"
    )


def _validate_chapter_one_door_output(
    editor: AtelScript,
    *,
    leader_entity: int,
    departure_pc: int,
    exit_entity: int,
    exit_action_pc: int,
    stop_pc: int,
    doorway_dialogue_ids: Sequence[int],
    firewood_field: int = CHAPTER_ONE_FIREWOOD_FIELD,
) -> None:
    """Pin the complete sanitized Chapter 1 departure transaction."""

    bytecode = editor.bytecode
    open_pc = editor.get_script_pointer(
        CHAPTER_ONE_DOOR_ENTITY,
        CHAPTER_ONE_DOOR_OPEN_SCRIPT,
    )
    if (
        editor.get_script_pointer(CHAPTER_ONE_DOOR_ENTITY, 0)
        != CHAPTER_ONE_DOOR_INIT_PC
        or bytecode[
            CHAPTER_ONE_DOOR_INIT_PC :
            CHAPTER_ONE_DOOR_INIT_PC + len(CHAPTER_ONE_DOOR_INIT_BODY)
        ]
        != CHAPTER_ONE_DOOR_INIT_BODY
        or open_pc != CHAPTER_ONE_DOOR_OPEN_PC
        or bytecode[
            open_pc : open_pc + len(CHAPTER_ONE_DOOR_OPEN_BODY)
        ]
        != CHAPTER_ONE_DOOR_OPEN_BODY
    ):
        raise RicoArcBuildError("Chapter 1 native door output drifted")

    # Sanitization must leave no second retail door/story action reachable.
    if (
        not 0 <= stop_pc < editor.bytecode_size
        or bytecode[stop_pc : stop_pc + 1] != b"\x00"
        or any(
            editor.get_script_pointer(CHAPTER_ONE_DOOR_ENTITY, script_index)
            != stop_pc
            for script_index in range(2, 32)
            if script_index != CHAPTER_ONE_DOOR_OPEN_SCRIPT
        )
    ):
        raise RicoArcBuildError("Chapter 1 door sanitizer output drifted")

    departure = _chapter_one_door_departure_body()
    if (
        editor.get_script_pointer(
            leader_entity,
            CHAPTER_ONE_DOOR_DEPARTURE_SCRIPT,
        )
        != departure_pc
        or bytecode[departure_pc : departure_pc + len(departure)] != departure
        or editor.get_script_pointer(exit_entity, 2) != exit_action_pc
        or departure.count(b"\x4B") != 1
        or any(opcode in departure for opcode in (b"\x19", b"\x1A", b"\xF8"))
    ):
        raise RicoArcBuildError("Chapter 1 Rico departure route drifted")

    transition = (
        _chapter_one_doorway_exchange_body(
            leader_entity,
            doorway_dialogue_ids,
        )
        + _chapter_one_door_transition_body(firewood_field)
    )
    action = bytecode[exit_action_pc:]
    if (
        action.count(transition) != 1
        or b"\x09\xFF"
        + bytes((CHAPTER_ONE_DOOR_DEPARTURE_SCRIPT | 0x20,))
        in action
    ):
        raise RicoArcBuildError(
            "Chapter 1 exit lost its ordered door, Rico, fade, and field calls"
        )


def _playable_exit_controller_init(contract: PlayableChapter) -> bytes:
    """Build an exit carrier, including solid blockers for cut-through leaves."""

    if contract.chapter_id in (5, 6):
        # These two donor walkmesh triangles physically cross their closed
        # door planes.  A four-unit invisible contact actor covers each narrow
        # aperture while retaining the same facing-gated Cross footprint.
        return mass_driver._solid_station_controller_init(
            contract.exit_x,
            contract.exit_z,
            requires_facing=True,
            collision_operand=0x04,
        )
    return _playable_controller_init(
        contract.exit_x,
        contract.exit_z,
        half_width=contract.exit_interaction_half_width,
        half_depth=contract.exit_interaction_half_depth,
        requires_facing=contract.exit_requires_facing,
    )


def _playable_controller_activation_gate(
    base_pc: int,
    required_bits: Sequence[int],
    x: int,
    z: int,
) -> bytes:
    """Move one initially parked controller into place after actor arrival."""

    if not required_bits:
        raise RicoArcBuildError("Controller activation gate has no prerequisites")
    routine = mass_driver._RoutineBuilder(base_pc)
    routine.label("poll")
    for bit in required_bits:
        routine.jump_if_bit_clear(
            PLAYABLE_STATE_VARIABLE,
            1 << bit,
            "wait",
        )
    # OP2A is a one-way DISABLE_DIALOG_ACTIVATION opcode, not a toggle. Keep
    # this always-active ghost carrier outside the field until prerequisites
    # are met, then move it once to its audited interaction coordinate.
    routine.emit(b"\x19" + _s16(x) + _s16(z) + b"\xC0")
    routine.label("enabled")
    routine.emit(_wait())
    routine.jump("enabled")
    routine.label("wait")
    routine.emit(_wait())
    routine.jump("poll")
    return routine.finish()


def _playable_actor_arrival_gate(
    base_pc: int,
    required_bits: Sequence[int],
) -> bytes:
    """Hide a stationary story actor until all arrival bits are complete."""

    if not required_bits:
        raise RicoArcBuildError("Actor arrival gate has no prerequisites")
    routine = mass_driver._RoutineBuilder(base_pc)
    # OP23 changes rendering only.  OP20/0x01 also removes actor-to-actor
    # contact so the unseen story actor cannot form an invisible wall.
    routine.emit(b"\x23" + PLAYABLE_ACTOR_GHOST_FLAGS)
    routine.label("poll")
    for bit in required_bits:
        routine.jump_if_bit_clear(
            PLAYABLE_STATE_VARIABLE,
            1 << bit,
            "wait",
        )
    # These actors are stationary conversation partners.  OP20/0x0C restores
    # the retail-proven solid, immovable NPC class before revealing them.
    routine.emit(PLAYABLE_ACTOR_SOLID_FLAGS + b"\x22")
    routine.label("visible")
    routine.emit(_wait())
    routine.jump("visible")
    routine.label("wait")
    routine.emit(_wait())
    routine.jump("poll")
    return routine.finish()


def _chapter_four_private_stage_body(entity: int) -> bytes:
    """Ghost and place one companion while the private-scene fade is black."""

    try:
        x, z, _triangle = CHAPTER_FOUR_PRIVATE_STAGE_POSITIONS[entity]
    except KeyError as exc:
        raise RicoArcBuildError(
            f"Chapter 4 has no private-scene stage point for entity {entity}"
        ) from exc
    return (
        PLAYABLE_ACTOR_GHOST_FLAGS
        + b"\x19"
        + _s16(x)
        + _s16(z)
        + b"\xC0\x1A\x00\x00"
    )


def _chapter_four_private_route_body(
    route: Sequence[tuple[int, int, int]],
    *,
    hide_offstage: bool,
) -> bytes:
    """Walk a finite audited route and exact-snap after every bounded leg."""

    if not route:
        raise RicoArcBuildError("Chapter 4 private-scene route is empty")
    body = bytearray()
    for x, z, _triangle in route:
        position = _s16(x) + _s16(z)
        # OP4B is the finite counterpart to retail's unbounded OP4A.  Even if
        # an unexpected actor touches the route, each leg advances after 120
        # updates and OP19 restores its exact audited endpoint, so the
        # cinematic can never wait forever on a walking actor.
        body.extend(
            b"\x4B"
            + position
            + b"\xC0"
            + _immediate(CHAPTER_FOUR_PRIVATE_WAYPOINT_MAX_STEPS)
            + b"\x19"
            + position
            + b"\xC0"
        )
    if hide_offstage:
        # The last route point is beyond the closed-side door plane on t37.
        # Hide only there; the companion remains visible while crossing.
        body.extend(b"\x23" + PLAYABLE_ACTOR_GHOST_FLAGS)
    body.append(0x00)
    return bytes(body)


def _chapter_four_private_departure_action() -> bytes:
    """Stage the visible Fei/Bart departure through field 237's real door."""

    def run(entity: int, script: int) -> bytes:
        if not 0 <= entity <= 0xFF or not 0 <= script < 32:
            raise RicoArcBuildError("Chapter 4 private-scene call is invalid")
        return b"\x09" + bytes((entity, script | 0x20))

    return (
        # The field has no audited generic Rico head-nod animation.  Two
        # deliberate looks and a held second pause communicate his assent
        # without dispatching an unsupported player animation.
        b"\xFE\x17"
        + bytes((CHAPTER_FOUR_RICO_ENTITY, CHAPTER_FOUR_FEI_ENTITY))
        + _wait(CHAPTER_FOUR_PRIVATE_LOOK_PAUSE)
        + b"\xFE\x17"
        + bytes((CHAPTER_FOUR_RICO_ENTITY, CHAPTER_FOUR_BART_ENTITY))
        + _wait(CHAPTER_FOUR_PRIVATE_ASSENT_PAUSE)
        # Reposition only behind a completed fade.  OP20/0x01 makes both
        # actors non-pushing before either visible walk begins.
        + mass_driver._facility_video_screen_fade_body(0xFF, 20)
        + run(CHAPTER_FOUR_FEI_ENTITY, CHAPTER_FOUR_PRIVATE_STAGE_SCRIPT)
        + run(CHAPTER_FOUR_BART_ENTITY, CHAPTER_FOUR_PRIVATE_STAGE_SCRIPT)
        + mass_driver._facility_video_screen_fade_body(0, 20)
        # Walk to two separate inside-door lanes before moving the leaf.
        + run(CHAPTER_FOUR_FEI_ENTITY, CHAPTER_FOUR_PRIVATE_APPROACH_SCRIPT)
        + run(CHAPTER_FOUR_BART_ENTITY, CHAPTER_FOUR_PRIVATE_APPROACH_SCRIPT)
        # Native e18:s6 opens and stops.  Each companion then crosses in a
        # finite blocking script and hides only at the offstage t37 endpoint.
        + run(CHAPTER_FOUR_DOOR_ENTITY, CHAPTER_FOUR_DOOR_OPEN_SCRIPT)
        + run(CHAPTER_FOUR_FEI_ENTITY, CHAPTER_FOUR_PRIVATE_CROSS_SCRIPT)
        + _wait(5)
        + run(CHAPTER_FOUR_BART_ENTITY, CHAPTER_FOUR_PRIVATE_CROSS_SCRIPT)
        + run(CHAPTER_FOUR_DOOR_ENTITY, CHAPTER_FOUR_DOOR_CLOSE_SCRIPT)
        + b"\xFE\x17"
        + bytes((CHAPTER_FOUR_RICO_ENTITY, CHAPTER_FOUR_SIGMUND_ENTITY))
        + _wait(CHAPTER_FOUR_PRIVATE_SETTLE_PAUSE)
    )


def _chapter_four_segment_on_walkmesh(
    start: tuple[int, int],
    end: tuple[int, int],
    triangles: Sequence[Sequence[tuple[int, int, int]]],
) -> bool:
    """Sample every world-unit step of one flat, audited cinematic leg."""

    dx = end[0] - start[0]
    dz = end[1] - start[1]
    steps = max(abs(dx), abs(dz), 1)
    for step in range(steps + 1):
        x = round(start[0] + dx * step / steps)
        z = round(start[1] + dz * step / steps)
        if not any(_point_inside_triangle((x, z), triangle) for triangle in triangles):
            return False
    return True


def _validate_chapter_four_private_scene_source(
    header: bytes,
    components: Sequence[bytes],
) -> None:
    """Pin field 237's leaf, helpers, and every finite departure waypoint."""

    editor = AtelScript(components[SCRIPT_INDEX])
    required_entities = (
        CHAPTER_FOUR_RICO_ENTITY,
        CHAPTER_FOUR_FEI_ENTITY,
        CHAPTER_FOUR_BART_ENTITY,
        CHAPTER_FOUR_SIGMUND_ENTITY,
        CHAPTER_FOUR_DOOR_ENTITY,
    )
    if editor.entity_count <= max(required_entities):
        raise RicoArcBuildError("Chapter 4 donor lost a private-scene entity")
    record = 0x190 + CHAPTER_FOUR_DOOR_ENTITY * 16
    if (
        record + 16 > len(header)
        or header[record : record + 16] != CHAPTER_FOUR_DOOR_HEADER_RECORD
    ):
        raise RicoArcBuildError("Chapter 4 native door header/model node changed")
    models = mass_driver._indexed_bundle_entries(components[2])
    if CHAPTER_FOUR_DOOR_MODEL_INDEX >= len(models):
        raise RicoArcBuildError("Chapter 4 native door model is absent")
    door_model = models[CHAPTER_FOUR_DOOR_MODEL_INDEX]
    if (
        len(door_model) != CHAPTER_FOUR_DOOR_MODEL_SIZE
        or _sha256_bytes(door_model) != CHAPTER_FOUR_DOOR_MODEL_SHA256
    ):
        raise RicoArcBuildError("Chapter 4 native door model changed")

    for script, pointer, body in (
        (
            CHAPTER_FOUR_DOOR_OPEN_SCRIPT,
            CHAPTER_FOUR_DOOR_OPEN_PC,
            CHAPTER_FOUR_DOOR_OPEN_BODY,
        ),
        (
            CHAPTER_FOUR_DOOR_CLOSE_SCRIPT,
            CHAPTER_FOUR_DOOR_CLOSE_PC,
            CHAPTER_FOUR_DOOR_CLOSE_BODY,
        ),
    ):
        if (
            editor.get_script_pointer(CHAPTER_FOUR_DOOR_ENTITY, script)
            != pointer
            or editor.bytecode[pointer : pointer + len(body)] != body
        ):
            raise RicoArcBuildError(
                f"Chapter 4 native door script {script} changed"
            )
    for pointer, body, label in (
        (
            CHAPTER_FOUR_DOOR_OPEN_SUBROUTINE_PC,
            CHAPTER_FOUR_DOOR_OPEN_SUBROUTINE,
            "open",
        ),
        (
            CHAPTER_FOUR_DOOR_CLOSE_SUBROUTINE_PC,
            CHAPTER_FOUR_DOOR_CLOSE_SUBROUTINE,
            "close",
        ),
    ):
        if editor.bytecode[pointer : pointer + len(body)] != body:
            raise RicoArcBuildError(
                f"Chapter 4 native door {label} subroutine changed"
            )

    triangles = _walkmesh_layer(components[1], 0)
    for entity in (CHAPTER_FOUR_FEI_ENTITY, CHAPTER_FOUR_BART_ENTITY):
        stage = CHAPTER_FOUR_PRIVATE_STAGE_POSITIONS[entity]
        approach = CHAPTER_FOUR_PRIVATE_APPROACH_ROUTES[entity]
        crossing = CHAPTER_FOUR_PRIVATE_CROSS_ROUTES[entity]
        route = (stage, *approach, *crossing)
        for x, z, triangle in route:
            if (
                not 0 <= triangle < len(triangles)
                or not _point_inside_triangle((x, z), triangles[triangle])
            ):
                raise RicoArcBuildError(
                    f"Chapter 4 entity {entity} waypoint {(x, z)} left "
                    f"walkmesh triangle {triangle}"
                )
        for left, right in zip(route, route[1:]):
            if not _chapter_four_segment_on_walkmesh(
                left[:2], right[:2], triangles
            ):
                raise RicoArcBuildError(
                    f"Chapter 4 entity {entity} route leaves the walkmesh "
                    f"between {left[:2]} and {right[:2]}"
                )


def _validate_chapter_five_six_exit_door_source(
    chapter_id: int,
    header: bytes,
    components: Sequence[bytes],
) -> None:
    """Pin Chapters 5/6's visible exit leaves and finite native helpers."""

    specs = {
        5: (
            CHAPTER_FIVE_DOOR_ENTITY,
            CHAPTER_FIVE_DOOR_MODEL_INDEX,
            CHAPTER_FIVE_DOOR_MODEL_SIZE,
            CHAPTER_FIVE_DOOR_MODEL_SHA256,
            CHAPTER_FIVE_DOOR_HEADER_RECORD,
            CHAPTER_FIVE_DOOR_INIT_PC,
            CHAPTER_FIVE_DOOR_INIT_BODY,
            CHAPTER_FIVE_DOOR_OPEN_SCRIPT,
            CHAPTER_FIVE_DOOR_OPEN_PC,
            CHAPTER_FIVE_DOOR_OPEN_BODY,
            CHAPTER_FIVE_DOOR_OPEN_SUBROUTINE_PC,
            CHAPTER_FIVE_DOOR_OPEN_SUBROUTINE,
            CHAPTER_FIVE_DOOR_CLOSE_SUBROUTINE_PC,
            CHAPTER_FIVE_DOOR_CLOSE_SUBROUTINE,
        ),
        6: (
            CHAPTER_SIX_DOOR_ENTITY,
            CHAPTER_SIX_DOOR_MODEL_INDEX,
            CHAPTER_SIX_DOOR_MODEL_SIZE,
            CHAPTER_SIX_DOOR_MODEL_SHA256,
            CHAPTER_SIX_DOOR_HEADER_RECORD,
            CHAPTER_SIX_DOOR_INIT_PC,
            CHAPTER_SIX_DOOR_INIT_BODY,
            CHAPTER_SIX_DOOR_OPEN_SCRIPT,
            CHAPTER_SIX_DOOR_OPEN_PC,
            CHAPTER_SIX_DOOR_OPEN_BODY,
            CHAPTER_SIX_DOOR_OPEN_SUBROUTINE_PC,
            CHAPTER_SIX_DOOR_OPEN_SUBROUTINE,
            CHAPTER_SIX_DOOR_CLOSE_SUBROUTINE_PC,
            CHAPTER_SIX_DOOR_CLOSE_SUBROUTINE,
        ),
    }
    try:
        (
            door_entity,
            model_index,
            model_size,
            model_sha256,
            header_record,
            init_pc,
            init_body,
            open_script,
            open_pc,
            open_body,
            open_subroutine_pc,
            open_subroutine,
            close_subroutine_pc,
            close_subroutine,
        ) = specs[chapter_id]
    except KeyError as exc:
        raise RicoArcBuildError(
            f"Chapter {chapter_id} has no pinned solid exit door"
        ) from exc

    editor = AtelScript(components[SCRIPT_INDEX])
    if editor.entity_count <= door_entity:
        raise RicoArcBuildError(f"Chapter {chapter_id} donor lost its exit door")
    record = 0x190 + door_entity * 16
    if record + 16 > len(header) or header[record : record + 16] != header_record:
        raise RicoArcBuildError(
            f"Chapter {chapter_id} native exit door header/model node changed"
        )
    models = mass_driver._indexed_bundle_entries(components[2])
    if model_index >= len(models):
        raise RicoArcBuildError(
            f"Chapter {chapter_id} native exit door model is absent"
        )
    door_model = models[model_index]
    if len(door_model) != model_size or _sha256_bytes(door_model) != model_sha256:
        raise RicoArcBuildError(
            f"Chapter {chapter_id} native exit door model changed"
        )
    if (
        editor.get_script_pointer(door_entity, 0) != init_pc
        or editor.bytecode[init_pc : init_pc + len(init_body)] != init_body
    ):
        raise RicoArcBuildError(
            f"Chapter {chapter_id} native exit door initializer changed"
        )
    if (
        editor.get_script_pointer(door_entity, open_script) != open_pc
        or editor.bytecode[open_pc : open_pc + len(open_body)] != open_body
    ):
        raise RicoArcBuildError(
            f"Chapter {chapter_id} native exit door open wrapper changed"
        )
    for pointer, body, label in (
        (open_subroutine_pc, open_subroutine, "open"),
        (close_subroutine_pc, close_subroutine, "close"),
    ):
        if editor.bytecode[pointer : pointer + len(body)] != body:
            raise RicoArcBuildError(
                f"Chapter {chapter_id} native exit door {label} subroutine changed"
            )


def _validate_chapter_seven_room_source(
    header: bytes,
    components: Sequence[bytes],
) -> None:
    """Pin field 298's visible east door and its finite native helpers."""

    editor = AtelScript(components[SCRIPT_INDEX])
    if editor.entity_count <= CHAPTER_SEVEN_DOOR_ENTITY:
        raise RicoArcBuildError("Chapter 7 donor lost its native bedroom door")
    record = 0x190 + CHAPTER_SEVEN_DOOR_ENTITY * 16
    if (
        record + 16 > len(header)
        or header[record : record + 16] != CHAPTER_SEVEN_DOOR_HEADER_RECORD
    ):
        raise RicoArcBuildError("Chapter 7 native door header/model node changed")
    models = mass_driver._indexed_bundle_entries(components[2])
    if CHAPTER_SEVEN_DOOR_MODEL_INDEX >= len(models):
        raise RicoArcBuildError("Chapter 7 native door model is absent")
    door_model = models[CHAPTER_SEVEN_DOOR_MODEL_INDEX]
    if (
        len(door_model) != CHAPTER_SEVEN_DOOR_MODEL_SIZE
        or _sha256_bytes(door_model) != CHAPTER_SEVEN_DOOR_MODEL_SHA256
    ):
        raise RicoArcBuildError("Chapter 7 native door model changed")

    for script, pointer, body in (
        (
            CHAPTER_SEVEN_DOOR_OPEN_SCRIPT,
            CHAPTER_SEVEN_DOOR_OPEN_PC,
            CHAPTER_SEVEN_DOOR_OPEN_BODY,
        ),
        (
            CHAPTER_SEVEN_DOOR_CLOSE_SCRIPT,
            CHAPTER_SEVEN_DOOR_CLOSE_PC,
            CHAPTER_SEVEN_DOOR_CLOSE_BODY,
        ),
    ):
        if (
            editor.get_script_pointer(CHAPTER_SEVEN_DOOR_ENTITY, script)
            != pointer
            or editor.bytecode[pointer : pointer + len(body)] != body
        ):
            raise RicoArcBuildError(
                f"Chapter 7 native door script {script} changed"
            )
    for pointer, body, label in (
        (
            CHAPTER_SEVEN_DOOR_OPEN_SUBROUTINE_PC,
            CHAPTER_SEVEN_DOOR_OPEN_SUBROUTINE,
            "open",
        ),
        (
            CHAPTER_SEVEN_DOOR_CLOSE_SUBROUTINE_PC,
            CHAPTER_SEVEN_DOOR_CLOSE_SUBROUTINE,
            "close",
        ),
    ):
        if editor.bytecode[pointer : pointer + len(body)] != body:
            raise RicoArcBuildError(
                f"Chapter 7 native door {label} subroutine changed"
            )


def _validate_chapter_two_room_source(
    header: bytes,
    components: Sequence[bytes],
) -> None:
    """Pin field 218's real bedroom leaf and authentic Hammer assets."""

    editor = AtelScript(components[SCRIPT_INDEX])
    if editor.entity_count <= CHAPTER_TWO_HAMMER_ENTITY:
        raise RicoArcBuildError("Chapter 2 donor lost authentic Hammer")
    if (
        mass_driver._read_field_entry(components[SCRIPT_INDEX], 0)
        != CHAPTER_TWO_MAIN_ENTRY
        or mass_driver._read_field_entry(components[SCRIPT_INDEX], 2)
        != CHAPTER_TWO_MAIN_RETURN_ENTRY
    ):
        raise RicoArcBuildError("Chapter 2 sitting-room entry records changed")

    door_record = 0x190 + CHAPTER_TWO_MAIN_DOOR_ENTITY * 16
    if (
        door_record + 16 > len(header)
        or header[door_record : door_record + 16]
        != CHAPTER_TWO_MAIN_DOOR_HEADER_RECORD
        or editor.get_script_pointer(CHAPTER_TWO_MAIN_DOOR_ENTITY, 0)
        != CHAPTER_TWO_MAIN_DOOR_INIT_PC
        or editor.bytecode[
            CHAPTER_TWO_MAIN_DOOR_INIT_PC :
            CHAPTER_TWO_MAIN_DOOR_INIT_PC
            + len(CHAPTER_TWO_MAIN_DOOR_INIT_BODY)
        ]
        != CHAPTER_TWO_MAIN_DOOR_INIT_BODY
        or editor.get_script_pointer(CHAPTER_TWO_MAIN_DOOR_ENTITY, 2)
        != CHAPTER_TWO_MAIN_DOOR_ACTION_PC
        or editor.bytecode[
            CHAPTER_TWO_MAIN_DOOR_ACTION_PC :
            CHAPTER_TWO_MAIN_DOOR_ACTION_PC
            + len(CHAPTER_TWO_MAIN_DOOR_ACTION_BODY)
        ]
        != CHAPTER_TWO_MAIN_DOOR_ACTION_BODY
    ):
        raise RicoArcBuildError("Chapter 2 native bedroom door changed")

    hammer_init = editor.get_script_pointer(CHAPTER_TWO_HAMMER_ENTITY, 0)
    if (
        hammer_init != CHAPTER_TWO_HAMMER_NATIVE_INIT_PC
        or editor.bytecode[
            hammer_init : hammer_init + len(CHAPTER_TWO_HAMMER_NATIVE_INIT_PREFIX)
        ]
        != CHAPTER_TWO_HAMMER_NATIVE_INIT_PREFIX
    ):
        raise RicoArcBuildError("Chapter 2 Hammer initializer changed")
    actor_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.ACTOR_INDEX]
    )
    sprite_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.SPRITE_INDEX]
    )
    if (
        CHAPTER_TWO_HAMMER_ACTOR_BANK >= len(actor_banks)
        or CHAPTER_TWO_HAMMER_ACTOR_BANK >= len(sprite_banks)
        or struct.unpack_from(
            "<4H",
            header,
            CHAPTER_TWO_HAMMER_ACTOR_BANK * 8,
        )
        != CHAPTER_TWO_HAMMER_VRAM_MAPPING
        or len(actor_banks[CHAPTER_TWO_HAMMER_ACTOR_BANK])
        != CHAPTER_TWO_HAMMER_ACTOR_BANK_SIZE
        or _sha256_bytes(actor_banks[CHAPTER_TWO_HAMMER_ACTOR_BANK])
        != CHAPTER_TWO_HAMMER_ACTOR_BANK_SHA256
        or len(sprite_banks[CHAPTER_TWO_HAMMER_ACTOR_BANK])
        != CHAPTER_TWO_HAMMER_SPRITE_BANK_SIZE
        or _sha256_bytes(sprite_banks[CHAPTER_TWO_HAMMER_ACTOR_BANK])
        != CHAPTER_TWO_HAMMER_SPRITE_BANK_SHA256
    ):
        raise RicoArcBuildError("Chapter 2 authentic Hammer bank changed")

    triangles = _walkmesh_layer(components[1], 0)
    for role, (x, z, triangle) in (
        (
            "playable entry",
            (
                CHAPTER_TWO_MAIN_PLAYABLE_ENTRY.x,
                CHAPTER_TWO_MAIN_PLAYABLE_ENTRY.z,
                CHAPTER_TWO_MAIN_PLAYABLE_ENTRY_TRIANGLE,
            ),
        ),
        (
            "bedroom return",
            (
                CHAPTER_TWO_MAIN_RETURN_ENTRY.x,
                CHAPTER_TWO_MAIN_RETURN_ENTRY.z,
                CHAPTER_TWO_MAIN_RETURN_TRIANGLE,
            ),
        ),
        ("bedroom-door frontage", CHAPTER_TWO_MAIN_DOOR_FRONTAGE),
    ):
        if (
            not 0 <= triangle < len(triangles)
            or not _point_inside_triangle((x, z), triangles[triangle])
        ):
            raise RicoArcBuildError(
                f"Chapter 2 {role} left audited triangle {triangle}"
            )
    for role, (x, z, triangle) in (
        ("Hammer staging point", CHAPTER_TWO_HAMMER_STAGE_POSITION),
        *(
            (f"Hammer stair waypoint {index}", point)
            for index, point in enumerate(
                CHAPTER_TWO_HAMMER_ROUTE,
                start=1,
            )
        ),
    ):
        if (
            not 0 <= triangle < len(triangles)
            or not _point_inside_triangle((x, z), triangles[triangle])
        ):
            raise RicoArcBuildError(
                f"Chapter 2 {role} left audited triangle {triangle}"
            )
    hammer_route = (
        CHAPTER_TWO_HAMMER_STAGE_POSITION,
        *CHAPTER_TWO_HAMMER_ROUTE,
    )
    for left, right in zip(hammer_route, hammer_route[1:]):
        if not _chapter_four_segment_on_walkmesh(
            left[:2],
            right[:2],
            triangles,
        ):
            raise RicoArcBuildError(
                "Chapter 2 Hammer stair route leaves the walkmesh between "
                f"{left[:2]} and {right[:2]}"
            )
    edge_owners: dict[
        tuple[tuple[int, int, int], tuple[int, int, int]],
        list[int],
    ] = {}
    for triangle_index, vertices in enumerate(triangles):
        for vertex_index in range(3):
            edge = tuple(
                sorted(
                    (
                        vertices[vertex_index],
                        vertices[(vertex_index + 1) % 3],
                    )
                )
            )
            edge_owners.setdefault(edge, []).append(triangle_index)
    adjacency = [set() for _triangle in triangles]
    for owners in edge_owners.values():
        for owner in owners:
            adjacency[owner].update(other for other in owners if other != owner)
    for left, right in zip(hammer_route, hammer_route[1:]):
        source_triangle = left[2]
        target_triangle = right[2]
        reachable = {source_triangle}
        pending = [source_triangle]
        while pending:
            owner = pending.pop()
            for neighbor in adjacency[owner] - reachable:
                reachable.add(neighbor)
                pending.append(neighbor)
        if target_triangle not in reachable:
            raise RicoArcBuildError(
                "Chapter 2 Hammer stair waypoints are not edge-connected: "
                f"{source_triangle} to {target_triangle}"
            )
    start_heights = {
        vertex[1]
        for vertex in triangles[CHAPTER_TWO_HAMMER_STAGE_POSITION[2]]
    }
    end_heights = {
        vertex[1]
        for vertex in triangles[CHAPTER_TWO_HAMMER_ROUTE[-1][2]]
    }
    if start_heights != {0} or end_heights != {62}:
        raise RicoArcBuildError(
            "Chapter 2 Hammer route no longer climbs from floor 0 to floor 62"
        )


def _validate_chapter_two_bedroom_source(donor_bundle: bytes) -> tuple[
    list[bytes],
    bytes,
]:
    """Return checked field-219 components and header for sanitization."""

    if (
        len(donor_bundle) != CHAPTER_TWO_BEDROOM_BUNDLE_SIZE
        or _sha256_bytes(donor_bundle) != CHAPTER_TWO_BEDROOM_BUNDLE_SHA256
    ):
        raise RicoArcBuildError("Chapter 2 Champion-bedroom donor changed")
    parsed = parse_field(donor_bundle)
    components = [part.data for part in parsed.parts]
    if (
        len(parsed.header) != CHAPTER_TWO_BEDROOM_HEADER_SIZE
        or _sha256_bytes(parsed.header) != CHAPTER_TWO_BEDROOM_HEADER_SHA256
    ):
        raise RicoArcBuildError("Chapter 2 Champion-bedroom header changed")
    for index, (size, digest) in CHAPTER_TWO_BEDROOM_COMPONENT_IDENTITIES.items():
        if (
            index >= len(components)
            or len(components[index]) != size
            or _sha256_bytes(components[index]) != digest
        ):
            raise RicoArcBuildError(
                f"Chapter 2 Champion-bedroom component {index} changed"
            )

    editor = AtelScript(components[SCRIPT_INDEX])
    if (
        editor.entity_count != CHAPTER_TWO_BEDROOM_ENTITY_COUNT
        or mass_driver._read_field_entry(components[SCRIPT_INDEX], 0)
        != CHAPTER_TWO_BEDROOM_ENTRY
    ):
        raise RicoArcBuildError("Chapter 2 Champion-bedroom script layout changed")
    door_record = 0x190 + CHAPTER_TWO_BEDROOM_DOOR_ENTITY * 16
    if (
        parsed.header[door_record : door_record + 16]
        != CHAPTER_TWO_BEDROOM_DOOR_HEADER_RECORD
        or editor.get_script_pointer(CHAPTER_TWO_BEDROOM_DOOR_ENTITY, 0)
        != CHAPTER_TWO_BEDROOM_DOOR_INIT_PC
        or editor.bytecode[
            CHAPTER_TWO_BEDROOM_DOOR_INIT_PC :
            CHAPTER_TWO_BEDROOM_DOOR_INIT_PC
            + len(CHAPTER_TWO_BEDROOM_DOOR_INIT_BODY)
        ]
        != CHAPTER_TWO_BEDROOM_DOOR_INIT_BODY
        or editor.get_script_pointer(CHAPTER_TWO_BEDROOM_DOOR_ENTITY, 2)
        != CHAPTER_TWO_BEDROOM_DOOR_ACTION_PC
        or editor.bytecode[
            CHAPTER_TWO_BEDROOM_DOOR_ACTION_PC :
            CHAPTER_TWO_BEDROOM_DOOR_ACTION_PC
            + len(CHAPTER_TWO_BEDROOM_DOOR_ACTION_BODY)
        ]
        != CHAPTER_TWO_BEDROOM_DOOR_ACTION_BODY
    ):
        raise RicoArcBuildError("Chapter 2 Champion-bedroom return door changed")
    models = mass_driver._indexed_bundle_entries(components[2])
    if (
        CHAPTER_TWO_BEDROOM_DOOR_MODEL_INDEX >= len(models)
        or len(models[CHAPTER_TWO_BEDROOM_DOOR_MODEL_INDEX])
        != CHAPTER_TWO_BEDROOM_DOOR_MODEL_SIZE
        or _sha256_bytes(models[CHAPTER_TWO_BEDROOM_DOOR_MODEL_INDEX])
        != CHAPTER_TWO_BEDROOM_DOOR_MODEL_SHA256
    ):
        raise RicoArcBuildError("Chapter 2 Champion-bedroom door model changed")
    triangles = _walkmesh_layer(components[1], 0)
    for role, (x, z, triangle) in (
        (
            "entry",
            (
                CHAPTER_TWO_BEDROOM_ENTRY.x,
                CHAPTER_TWO_BEDROOM_ENTRY.z,
                CHAPTER_TWO_BEDROOM_ENTRY_TRIANGLE,
            ),
        ),
        ("bed", CHAPTER_TWO_BED_POSITION),
    ):
        if (
            not 0 <= triangle < len(triangles)
            or not _point_inside_triangle((x, z), triangles[triangle])
        ):
            raise RicoArcBuildError(
                f"Chapter 2 Champion-bedroom {role} left triangle {triangle}"
            )
    return components, parsed.header


def _validate_playable_visible_prop_sources(
    chapter_id: int,
    header: bytes,
    components: Sequence[bytes],
) -> None:
    """Fail closed if a required visible donor prop changes or disappears."""

    pins = PLAYABLE_VISIBLE_PROP_SOURCE_PINS.get(chapter_id, ())
    if not pins:
        return
    models = mass_driver._indexed_bundle_entries(components[2])
    for description, node, model, record_bytes, size, digest in pins:
        record = 0x190 + node * 16
        if (
            record + 16 > len(header)
            or header[record : record + 16] != record_bytes
        ):
            raise RicoArcBuildError(
                f"Chapter {chapter_id} visible {description} node changed"
            )
        if model >= len(models):
            raise RicoArcBuildError(
                f"Chapter {chapter_id} visible {description} model is absent"
            )
        payload = models[model]
        if len(payload) != size or _sha256_bytes(payload) != digest:
            raise RicoArcBuildError(
                f"Chapter {chapter_id} visible {description} model changed"
            )


def _playable_action_prefix(routine_pc: int) -> bytes:
    prefix = _actor_dialog_reset() + b"\x33\xFE\x54"
    release_pc = routine_pc + len(prefix)
    return prefix + _wait_for_pad_release(PAD_MASK_CROSS, release_pc) + _wait()


def _playable_action_finish(routine_pc: int) -> bytes:
    prefix = _actor_dialog_reset()
    release_pc = routine_pc + len(prefix)
    return (
        prefix
        + _wait_for_pad_release(PAD_MASK_CROSS, release_pc)
        + b"\xFE\x53\x00"
    )


def _emit_chapter_one_window_contact_gate(
    routine: mass_driver._RoutineBuilder,
    outside_label: str,
) -> None:
    """Reject coarse AABB hits outside primitive 43's diagonal frontage."""

    x_variable = CHAPTER_ONE_WINDOW_POSITION_X_VARIABLE
    z_variable = CHAPTER_ONE_WINDOW_POSITION_Z_VARIABLE
    scratch = CHAPTER_ONE_WINDOW_POSITION_SCRATCH_VARIABLE
    minimum_tangent, maximum_tangent = (
        CHAPTER_ONE_WINDOW_CONTACT_TANGENT_RANGE
    )
    # OP2D samples the controlled leader.  Its disposable Y destination is
    # immediately overwritten, letting this exact gate use only three words.
    routine.emit(
        b"\x2D\xFF"
        + _u16(x_variable)
        + _u16(z_variable)
        + _u16(scratch)
        + atel.copy_variable(scratch, x_variable)
        + atel.variable_math(
            0x39,
            scratch,
            z_variable,
            operand_is_variable=True,
        )
    )
    routine.jump_if_signed_less_than(
        scratch,
        CHAPTER_ONE_WINDOW_CONTACT_NORMAL_MIN,
        outside_label,
    )
    routine.emit(
        atel.copy_variable(scratch, x_variable)
        + atel.variable_math(
            0x38,
            scratch,
            z_variable,
            operand_is_variable=True,
        )
    )
    routine.jump_if_signed_less_than(
        scratch,
        minimum_tangent,
        outside_label,
    )
    routine.jump_if_signed_greater_or_equal(
        scratch,
        maximum_tangent + 1,
        outside_label,
    )


def _emit_chapter_one_cooking_counter_contact_gate(
    routine: mass_driver._RoutineBuilder,
    outside_label: str,
) -> None:
    """Reject the coarse counter AABB away from its diagonal frontage."""

    x_variable = CHAPTER_ONE_COOKING_COUNTER_POSITION_X_VARIABLE
    z_variable = CHAPTER_ONE_COOKING_COUNTER_POSITION_Z_VARIABLE
    scratch = CHAPTER_ONE_COOKING_COUNTER_POSITION_SCRATCH_VARIABLE
    minimum_normal, maximum_normal = (
        CHAPTER_ONE_COOKING_COUNTER_CONTACT_NORMAL_RANGE
    )
    minimum_tangent, maximum_tangent = (
        CHAPTER_ONE_COOKING_COUNTER_CONTACT_TANGENT_RANGE
    )
    routine.emit(
        b"\x2D\xFF"
        + _u16(x_variable)
        + _u16(z_variable)
        + _u16(scratch)
        + atel.copy_variable(scratch, z_variable)
        + atel.variable_math(
            0x39,
            scratch,
            x_variable,
            operand_is_variable=True,
        )
    )
    routine.jump_if_signed_less_than(
        scratch,
        minimum_normal,
        outside_label,
    )
    routine.jump_if_signed_greater_or_equal(
        scratch,
        maximum_normal + 1,
        outside_label,
    )
    routine.emit(
        atel.copy_variable(scratch, x_variable)
        + atel.variable_math(
            0x38,
            scratch,
            z_variable,
            operand_is_variable=True,
        )
    )
    routine.jump_if_signed_less_than(
        scratch,
        minimum_tangent,
        outside_label,
    )
    routine.jump_if_signed_greater_or_equal(
        scratch,
        maximum_tangent + 1,
        outside_label,
    )


def _playable_actor_action_gate(
    base_pc: int,
    required_bits: Sequence[int],
    action_pc: int,
) -> bytes:
    """Silently ignore a hidden actor, then forward Cross after arrival."""

    if not required_bits:
        raise RicoArcBuildError("Actor action gate has no prerequisites")
    routine = mass_driver._RoutineBuilder(base_pc)
    for bit in required_bits:
        routine.jump_if_bit_clear(
            PLAYABLE_STATE_VARIABLE,
            1 << bit,
            "inactive",
        )
    # The lower-ID visible actor may win action selection over its co-located
    # model-less carrier.  Forward to the one shared, idempotent action so
    # either selection owner behaves identically after the actor arrives.
    routine.emit(_jump(action_pc))
    routine.label("inactive")
    routine.emit(_playable_action_prefix(routine.pc))
    routine.emit(_playable_action_finish(routine.pc))
    return routine.finish()


def _gear_battle_stage(
    *,
    solo_rico: bool,
    chapter_party: Sequence[int],
) -> tuple[bytes, bytes]:
    before = bytearray()
    after = bytearray()
    if solo_rico:
        # FE3A/FE3B alter the battle/menu participation frame mask; they do
        # not add or remove field-party actors.  Keep Rico's field companion
        # present for the post-fight conversation while excluding everyone
        # except Rico from this formation, then restore this chapter's exact
        # mask afterward.
        for character in range(11):
            before.extend(b"\xFE\x3B" + _immediate(character))
        before.extend(b"\xFE\x3A" + _immediate(5))
        # Runtime Gear numbers differ from dialogue-name token numbers.
        # Retail field 225 assigns Rico -> Gear 6 (Stier).
        before.extend(b"\xFE\xA1" + _immediate(5) + _immediate(6))
        before.extend(b"\xFE\x41" + _immediate(0))
        after.extend(b"\xFE\x42" + _immediate(0))
        for character in range(11):
            after.extend(b"\xFE\x3B" + _immediate(character))
        for character in chapter_party:
            after.extend(b"\xFE\x3A" + _immediate(character))
    else:
        for character, gear in ((5, 6), (0, 0), (3, 4)):
            before.extend(b"\xFE\xA1" + _immediate(character) + _immediate(gear))
        for slot in range(3):
            before.extend(b"\xFE\x41" + _immediate(slot))
        for slot in range(3):
            after.extend(b"\xFE\x42" + _immediate(slot))
    return bytes(before), bytes(after)


def _chapter_fields_for_hub(return_hub: int) -> Mapping[int, int]:
    matches = [
        CHAPTER_FIELDS[disc]
        for disc, hub_field in HUB_FIELDS.items()
        if hub_field == return_hub
    ]
    if len(matches) != 1:
        raise RicoArcBuildError(
            f"Unknown or ambiguous Rico chapter hub field: {return_hub}"
        )
    return matches[0]


def _emit_playable_completion(
    routine: Any,
    contract: PlayableChapter,
    *,
    label_prefix: str,
    return_hub: int,
    authored_base: int,
    authored_count: int,
    custom_ids: dict[str, int],
    next_chapter_exposition_ids: Sequence[int],
) -> None:
    """Emit one replayable next-chapter/chapter-select completion prompt."""

    exit_dialogue = _resolve_playable_dialogue(
        contract.exit_dialogue,
        authored_base=authored_base,
        authored_count=authored_count,
        custom_ids=custom_ids,
    )
    if exit_dialogue:
        routine.emit(_dialogue_sequence(exit_dialogue) + _wait())

    choice = (
        PLAYABLE_FINAL_HUB_CHOICE
        if contract.chapter_id == 7
        else PLAYABLE_NEXT_OR_HUB_CHOICE
    )
    routine.emit(_choice_dialog(custom_ids[choice]) + b"\xA9\x12\x9C")
    stay_label = f"{label_prefix}_stay"
    if contract.chapter_id == 7:
        if next_chapter_exposition_ids:
            raise RicoArcBuildError("The final chapter cannot launch a successor")
        routine.jump_if_not_equal(
            MENU_SELECTION_VARIABLE,
            1,
            stay_label,
        )
        routine.emit(_hub_launch_body(return_hub))
        routine.label(stay_label)
        return

    if not next_chapter_exposition_ids:
        raise RicoArcBuildError(
            f"Chapter {contract.chapter_id} has no next-chapter exposition"
        )
    hub_label = f"{label_prefix}_hub"
    routine.jump_if_not_equal(MENU_SELECTION_VARIABLE, 1, hub_label)
    next_field = _chapter_fields_for_hub(return_hub)[contract.chapter_id + 1]
    routine.emit(
        _prelaunch_exposition(
            next_chapter_exposition_ids,
            routine_pc=routine.pc,
        )
    )
    routine.emit(
        _chapter_launch_body(contract.chapter_id + 1, next_field)
    )
    routine.label(hub_label)
    routine.jump_if_not_equal(MENU_SELECTION_VARIABLE, 2, stay_label)
    routine.emit(_hub_launch_body(return_hub))
    routine.label(stay_label)


def _build_playable_interaction_action(
    interaction: PlayableInteraction,
    *,
    base_pc: int,
    authored_base: int,
    authored_count: int,
    custom_ids: dict[str, int],
    field_music: int,
    chapter_party: Sequence[int],
    contract: PlayableChapter,
    return_hub: int,
    next_chapter_exposition_ids: Sequence[int],
) -> bytes:
    routine = mass_driver._RoutineBuilder(base_pc)
    routine.emit(_playable_action_prefix(base_pc))
    contact_gate_label: str | None = None
    if contract.chapter_id == 1 and interaction.name == "cold window":
        contact_gate_label = "outside_window_contact"
        _emit_chapter_one_window_contact_gate(
            routine,
            contact_gate_label,
        )
    elif contract.chapter_id == 1 and interaction.name == "cooking counter":
        contact_gate_label = "outside_cooking_counter_contact"
        _emit_chapter_one_cooking_counter_contact_gate(
            routine,
            contact_gate_label,
        )
    chapter_one_anna_bedside = (
        contract.chapter_id == 1 and interaction.name == "Anne's bedside"
    )

    for index, stage in enumerate(interaction.stages):
        routine.jump_if_bit_clear(
            PLAYABLE_STATE_VARIABLE,
            1 << stage.bit,
            f"stage_{index}",
        )
    completion_stage = next(
        (stage for stage in interaction.stages if stage.completes_chapter),
        None,
    )
    if completion_stage is None:
        if not interaction.repeat_dialogue:
            raise RicoArcBuildError(
                f"Playable interaction {interaction.name!r} needs contextual "
                "repeat dialogue"
            )
        repeat_dialogue = _resolve_playable_dialogue(
            interaction.repeat_dialogue,
            authored_base=authored_base,
            authored_count=authored_count,
            custom_ids=custom_ids,
        )
        if chapter_one_anna_bedside:
            routine.emit(CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL)
        routine.emit(_dialogue_sequence(repeat_dialogue))
    else:
        _emit_playable_completion(
            routine,
            contract,
            label_prefix="repeat_completion",
            return_hub=return_hub,
            authored_base=authored_base,
            authored_count=authored_count,
            custom_ids=custom_ids,
            next_chapter_exposition_ids=next_chapter_exposition_ids,
        )
    routine.emit(_playable_action_finish(routine.pc))

    for index, stage in enumerate(interaction.stages):
        routine.label(f"stage_{index}")
        if stage.locked_dialogue_steps:
            for missing_bit, _dialogue in stage.locked_dialogue_steps:
                routine.jump_if_bit_clear(
                    PLAYABLE_STATE_VARIABLE,
                    1 << missing_bit,
                    f"locked_{index}_step_{missing_bit}",
                )
        elif stage.locked_dialogue_states:
            required = tuple(stage.required_bits)
            required_set = frozenset(required)
            ready_label = f"stage_{index}_requirements_met"
            state_labels = {
                frozenset(completed_bits): (
                    f"locked_{index}_state_"
                    f"{sum(1 << bit for bit in completed_bits):04x}"
                )
                for completed_bits, _dialogue in stage.locked_dialogue_states
            }

            def emit_state_tree(
                required_index: int,
                completed_bits: frozenset[int],
            ) -> None:
                if required_index == len(required):
                    target = (
                        ready_label
                        if completed_bits == required_set
                        else state_labels.get(completed_bits)
                    )
                    if target is None:
                        raise RicoArcBuildError(
                            f"Playable interaction {interaction.name!r} stage "
                            f"{stage.bit} has no dialogue for completed bits "
                            f"{sorted(completed_bits)}"
                        )
                    routine.jump(target)
                    return
                required_bit = required[required_index]
                completed_mask = sum(1 << bit for bit in completed_bits)
                clear_label = (
                    f"stage_{index}_required_{required_index}_"
                    f"{completed_mask:04x}_clear"
                )
                routine.jump_if_bit_clear(
                    PLAYABLE_STATE_VARIABLE,
                    1 << required_bit,
                    clear_label,
                )
                emit_state_tree(
                    required_index + 1,
                    completed_bits | {required_bit},
                )
                routine.label(clear_label)
                emit_state_tree(required_index + 1, completed_bits)

            emit_state_tree(0, frozenset())
            routine.label(ready_label)
        else:
            for required_bit in stage.required_bits:
                routine.jump_if_bit_clear(
                    PLAYABLE_STATE_VARIABLE,
                    1 << required_bit,
                    f"locked_{index}",
                )
        chapter_one_stove_choice = (
            contract.chapter_id == 1
            and interaction.name == "cooking counter"
            and stage.bit == CHAPTER_ONE_STOVE_ON_BIT
        )
        dialogue = _resolve_playable_dialogue(
            stage.dialogue,
            authored_base=authored_base,
            authored_count=authored_count,
            custom_ids=custom_ids,
        )
        anna_cough_before_dialogue = chapter_one_anna_bedside or (
            contract.chapter_id == 1
            and (
                (interaction.name == "reading desk" and stage.bit == 8)
                or (interaction.name == "cooking counter" and stage.bit == 9)
            )
        )
        if anna_cough_before_dialogue:
            routine.emit(CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL)
        if chapter_one_stove_choice:
            # The kettle is a fixed prop already sitting on the cooktop.  Fill
            # it once, then preserve that setup if the player leaves the stove
            # off and returns to the choice later.
            routine.jump_if_bit_clear(
                PLAYABLE_STATE_VARIABLE,
                1 << CHAPTER_ONE_KETTLE_FILLED_BIT,
                f"stage_{index}_fill_kettle",
            )
            routine.jump(f"stage_{index}_stove_choice")
            routine.label(f"stage_{index}_fill_kettle")
            routine.emit(
                _dialogue_sequence(dialogue)
                + atel.set_var_bit(
                    PLAYABLE_STATE_VARIABLE,
                    CHAPTER_ONE_KETTLE_FILLED_BIT,
                )
            )
            routine.label(f"stage_{index}_stove_choice")
        else:
            routine.emit(_dialogue_sequence(dialogue))
        if stage.choice_text is not None:
            choice_count = _playable_choice_count(stage.choice_text)
            if dialogue:
                routine.emit(_wait())
            routine.emit(
                _choice_dialog(custom_ids[stage.choice_text])
                + bytes((0xA9, 0x10 | choice_count, 0x9C))
            )
            routine.jump_if_not_equal(
                MENU_SELECTION_VARIABLE,
                stage.accepted_selection,
                f"rejected_{index}",
            )
            if stage.accepted_sound_id is not None:
                routine.emit(_play_sound_effect(stage.accepted_sound_id))
        progress_committed = False
        if stage.battle_configuration is not None:
            before_battle = after_battle = b""
            if stage.gear_battle:
                before_battle, after_battle = _gear_battle_stage(
                    solo_rico=stage.solo_rico,
                    chapter_party=chapter_party,
                )
            routine.emit(
                before_battle
                + _wait(15)
                + _play_music(PLAYABLE_BATTLE_MUSIC)
                + mass_driver._fixed_battle(stage.battle_configuration)
                + b"\xFE\x7F"
                + atel.set_var_bit(
                    PLAYABLE_STATE_VARIABLE,
                    stage.bit,
                )
                + after_battle
                + _play_music(field_music)
            )
            progress_committed = True
        if stage.private_departure_after:
            routine.emit(_chapter_four_private_departure_action())
        else:
            if stage.time_cut_after:
                routine.emit(
                    mass_driver._facility_video_screen_fade_body(0xFF, 20)
                )
            for entity in stage.hide_entities_after:
                if not 0 <= entity <= 0xFF:
                    raise RicoArcBuildError(
                        f"Playable hide entity is outside u8: {entity}"
                    )
                routine.emit(b"\x09" + bytes((entity, 4 | 0x20)))
            if stage.time_cut_after:
                routine.emit(
                    _wait(20)
                    + mass_driver._facility_video_screen_fade_body(0, 20)
                )
        # A battle commits its victory immediately after FE7F, before Gear
        # teardown, music, or post-event dialogue.  Non-battle objectives
        # commit at the equivalent point after their interaction text.
        # The stove bit triggers the background boil timer. Commit it only
        # after the post-action conversation so the full delay is available
        # while the player can move Rico and water the flower.
        if not progress_committed and not chapter_one_stove_choice:
            routine.emit(
                atel.set_var_bit(PLAYABLE_STATE_VARIABLE, stage.bit)
            )
        after_dialogue = _resolve_playable_dialogue(
            stage.after_dialogue,
            authored_base=authored_base,
            authored_count=authored_count,
            custom_ids=custom_ids,
        )
        if after_dialogue:
            routine.emit(
                CHAPTER_ONE_STOVE_AUDIO_HELPER_CALL
                if chapter_one_stove_choice
                else _wait()
            )
            if contract.chapter_id == 1 and (
                (
                    interaction.name == "cooking counter"
                    and stage.bit == CHAPTER_ONE_STOVE_ON_BIT
                )
                or (interaction.name == "stonebell vase" and stage.bit == 7)
            ):
                routine.emit(CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL)
            routine.emit(_dialogue_sequence(after_dialogue))
        if not progress_committed and chapter_one_stove_choice:
            routine.emit(
                atel.set_var_bit(PLAYABLE_STATE_VARIABLE, stage.bit)
            )
        if stage.completes_chapter:
            _emit_playable_completion(
                routine,
                contract,
                label_prefix=f"stage_{index}_completion",
                return_hub=return_hub,
                authored_base=authored_base,
                authored_count=authored_count,
                custom_ids=custom_ids,
                next_chapter_exposition_ids=next_chapter_exposition_ids,
            )
        routine.emit(_playable_action_finish(routine.pc))

    for index, stage in enumerate(interaction.stages):
        if stage.choice_text is None:
            continue
        routine.label(f"rejected_{index}")
        rejection_dialogue = _resolve_playable_dialogue(
            stage.rejection_dialogue,
            authored_base=authored_base,
            authored_count=authored_count,
            custom_ids=custom_ids,
        )
        if rejection_dialogue:
            routine.emit(_wait() + _dialogue_sequence(rejection_dialogue))
        routine.emit(_playable_action_finish(routine.pc))

    for index, stage in enumerate(interaction.stages):
        if stage.locked_dialogue_steps:
            for missing_bit, step_dialogue_refs in stage.locked_dialogue_steps:
                routine.label(f"locked_{index}_step_{missing_bit}")
                step_dialogue = _resolve_playable_dialogue(
                    step_dialogue_refs,
                    authored_base=authored_base,
                    authored_count=authored_count,
                    custom_ids=custom_ids,
                )
                if chapter_one_anna_bedside:
                    routine.emit(CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL)
                routine.emit(_dialogue_sequence(step_dialogue))
                routine.emit(_playable_action_finish(routine.pc))
            continue
        if stage.locked_dialogue_states:
            for completed_bits, state_dialogue_refs in (
                stage.locked_dialogue_states
            ):
                completed_mask = sum(1 << bit for bit in completed_bits)
                routine.label(
                    f"locked_{index}_state_{completed_mask:04x}"
                )
                state_dialogue = _resolve_playable_dialogue(
                    state_dialogue_refs,
                    authored_base=authored_base,
                    authored_count=authored_count,
                    custom_ids=custom_ids,
                )
                if chapter_one_anna_bedside:
                    routine.emit(CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL)
                routine.emit(_dialogue_sequence(state_dialogue))
                routine.emit(_playable_action_finish(routine.pc))
            continue
        if not stage.locked_dialogue:
            continue
        routine.label(f"locked_{index}")
        locked_dialogue = _resolve_playable_dialogue(
            stage.locked_dialogue,
            authored_base=authored_base,
            authored_count=authored_count,
            custom_ids=custom_ids,
        )
        if chapter_one_anna_bedside:
            routine.emit(CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL)
        routine.emit(_dialogue_sequence(locked_dialogue))
        routine.emit(_playable_action_finish(routine.pc))

    if contact_gate_label is not None:
        routine.label(contact_gate_label)
        # A coarse rectangle hit away from the visible diagonal prop is not
        # an interaction. Return silently after the normal Cross-release path.
        routine.emit(_playable_action_finish(routine.pc))

    result = routine.finish()
    if contract.chapter_id == 1 and interaction.name == "reading desk":
        result += bytes(CHAPTER_ONE_READING_DESK_ACTION_LAYOUT_PADDING)
    return result


def _build_playable_exit_action(
    contract: PlayableChapter,
    *,
    leader_entity: int,
    base_pc: int,
    return_hub: int,
    authored_base: int,
    authored_count: int,
    custom_ids: dict[str, int],
    next_chapter_exposition_ids: Sequence[int],
    chapter_one_firewood_field: int = CHAPTER_ONE_FIREWOOD_FIELD,
) -> bytes:
    routine = mass_driver._RoutineBuilder(base_pc)
    routine.emit(_playable_action_prefix(base_pc))
    for required_bit, _text in contract.exit_locked_steps:
        routine.jump_if_bit_clear(
            PLAYABLE_STATE_VARIABLE,
            1 << required_bit,
            f"locked_{required_bit}",
        )
    if contract.exit_transition is not None:
        if contract.chapter_id != 1:
            raise RicoArcBuildError(
                "Only Chapter 1 owns the dedicated funeral exit transition"
            )
        doorway_dialogue_ids = _resolve_playable_dialogue(
            contract.exit_transition.doorway_dialogue,
            authored_base=authored_base,
            authored_count=authored_count,
            custom_ids=custom_ids,
        )
        routine.emit(
            _chapter_one_doorway_exchange_body(
                leader_entity,
                doorway_dialogue_ids,
            )
            + _chapter_one_door_transition_body(chapter_one_firewood_field)
        )
        for required_bit, text in contract.exit_locked_steps:
            routine.label(f"locked_{required_bit}")
            routine.emit(_dialogue_sequence((custom_ids[text],)))
            routine.emit(_playable_action_finish(routine.pc))
        return routine.finish()

    exit_door = PLAYABLE_NATIVE_EXIT_DOORS.get(contract.chapter_id)
    if exit_door is not None:
        door_entity, open_script, _close_script = exit_door
        # Every mapped chapter moves its authentic visible leaf before the
        # completion choice appears.
        routine.emit(
            b"\x09"
            + bytes((door_entity, open_script | 0x20))
        )
    _emit_playable_completion(
        routine,
        contract,
        label_prefix="exit_completion",
        return_hub=return_hub,
        authored_base=authored_base,
        authored_count=authored_count,
        custom_ids=custom_ids,
        next_chapter_exposition_ids=next_chapter_exposition_ids,
    )
    if exit_door is not None:
        # Only a canceled completion prompt falls through this far.  Accepted
        # rows change field, so close the native leaf solely for the player
        # who chose to remain.
        door_entity, _open_script, close_script = exit_door
        routine.emit(
            b"\x09"
            + bytes((door_entity, close_script | 0x20))
        )
    routine.emit(_playable_action_finish(routine.pc))
    for required_bit, text in contract.exit_locked_steps:
        routine.label(f"locked_{required_bit}")
        routine.emit(_dialogue_sequence((custom_ids[text],)))
        routine.emit(_playable_action_finish(routine.pc))
    return routine.finish()


def _validate_playable_contract(
    components: Sequence[bytes],
    chapter: Chapter,
    contract: PlayableChapter,
) -> None:
    if contract.chapter_id != chapter.chapter_id:
        raise RicoArcBuildError(
            f"Chapter contract ID {contract.chapter_id} does not match "
            f"chapter {chapter.chapter_id}"
        )
    reminder_bits = tuple(bit for bit, _text in contract.exit_locked_steps)
    if len(reminder_bits) != len(set(reminder_bits)):
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} exit reminder bits must be unique: "
            f"{reminder_bits}"
        )
    transition = contract.exit_transition
    transition_bits = {transition.bit} if transition is not None else set()
    expected_reminder_bits = set(contract.required_bits) - transition_bits
    if set(reminder_bits) != expected_reminder_bits:
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} exit reminder bits must match its "
            f"player-completed requirements: reminders {reminder_bits}, "
            f"required {contract.required_bits}, transition {transition_bits}"
        )
    if transition is not None and (
        contract.chapter_id != 1
        or transition.bit not in contract.required_bits
        or tuple(transition.required_bits) != reminder_bits
        or len(transition.doorway_dialogue) != 2
        or not transition.sickness_dialogue
        or not transition.loss_dialogue
        or not transition.funeral_dialogue
    ):
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} has an invalid exit transition"
        )
    if contract.chapter_id == 1:
        if (
            (contract.exit_x, contract.exit_z, contract.exit_triangle)
            != CHAPTER_ONE_EXIT_POSITION
            or contract.exit_interaction_half_width
            != CHAPTER_ONE_EXIT_INTERACTION_HALF_WIDTH
            or contract.exit_interaction_half_depth
            != CHAPTER_ONE_EXIT_INTERACTION_HALF_DEPTH
            or contract.exit_requires_facing
        ):
            raise RicoArcBuildError(
                "Chapter 1 door hotspot drifted from its audited frontage"
            )
        # OP18 doubles each encoded half-extent and action selection adds the
        # player's fixed 16-unit horizontal extent.  Both ends of the native
        # t59/t79 threshold must therefore remain selectable from inside the
        # visible doorway without a facing gate.
        effective_x = contract.exit_interaction_half_width * 2 + 0x10
        effective_z = contract.exit_interaction_half_depth * 2 + 0x10
        if any(
            abs(x - contract.exit_x) > effective_x
            or abs(z - contract.exit_z) > effective_z
            for x, z in CHAPTER_ONE_DOOR_THRESHOLD_EDGE
        ):
            raise RicoArcBuildError(
                "Chapter 1 door hotspot no longer covers its native threshold"
            )
    private_departures = [
        stage
        for interaction in contract.interactions
        for stage in interaction.stages
        if stage.private_departure_after
    ]
    if chapter.chapter_id == 4:
        if chapter.donor_field != 237 or len(private_departures) != 1:
            raise RicoArcBuildError(
                "Chapter 4 requires exactly one field-237 private departure"
            )
        private_stage = private_departures[0]
        if (
            private_stage.bit != 4
            or private_stage.dialogue != (11,)
            or private_stage.hide_entities_after
            != (CHAPTER_FOUR_FEI_ENTITY, CHAPTER_FOUR_BART_ENTITY)
            or not private_stage.time_cut_after
        ):
            raise RicoArcBuildError(
                "Chapter 4 private departure contract drifted from its "
                "audited staging"
            )
    elif private_departures:
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} cannot use Chapter 4 private staging"
        )
    triangles = _walkmesh_layer(components[1], 0)
    entry_x, entry_z, entry_triangle = PLAYABLE_ENTRY_POSITIONS[chapter.chapter_id]

    # The controller helper's OP18 operands are shifted left once by the
    # engine, then the player's fixed 16-unit horizontal extent is added when
    # selecting an action target.  Reject entries inside that effective box:
    # even a correctly controlled actor can otherwise have its opening Cross
    # press consumed by the nearby interaction and look frozen in dialogue.
    for interaction in contract.interactions:
        effective_x = interaction.interaction_half_width * 2 + 0x10
        effective_z = interaction.interaction_half_depth * 2 + 0x10
        if (
            abs(entry_x - interaction.x) <= effective_x
            and abs(entry_z - interaction.z) <= effective_z
        ):
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} entry overlaps the effective "
                f"interaction box for {interaction.name}"
            )
    exit_effective_x = contract.exit_interaction_half_width * 2 + 0x10
    exit_effective_z = contract.exit_interaction_half_depth * 2 + 0x10
    if (
        abs(entry_x - contract.exit_x) <= exit_effective_x
        and abs(entry_z - contract.exit_z) <= exit_effective_z
    ):
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} entry overlaps the effective exit box"
        )

    # Competing action volumes make Cross dispatch depend on actor-table order
    # rather than the prop Rico is facing.  The bed/window bug demonstrated
    # why every authored target (including the chapter exit) must have its own
    # non-overlapping effective box.
    action_boxes = [
        (
            interaction.name,
            interaction.x,
            interaction.z,
            interaction.interaction_half_width * 2 + 0x10,
            interaction.interaction_half_depth * 2 + 0x10,
        )
        for interaction in contract.interactions
    ]
    action_boxes.append(
        (
            "chapter exit",
            contract.exit_x,
            contract.exit_z,
            exit_effective_x,
            exit_effective_z,
        )
    )
    for index, left in enumerate(action_boxes):
        for right in action_boxes[index + 1 :]:
            if (
                abs(left[1] - right[1]) <= left[3] + right[3]
                and abs(left[2] - right[2]) <= left[4] + right[4]
            ):
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} action boxes overlap: "
                    f"{left[0]} and {right[0]}"
                )
    points = [("chapter entry", entry_x, entry_z, entry_triangle)]
    for interaction in contract.interactions:
        approved_recessed_anchor = chapter.chapter_id == 1 and (
            (
                interaction.name == "settlement window"
                and (interaction.x, interaction.z, interaction.triangle)
                == CHAPTER_ONE_SETTLEMENT_WINDOW_POSITION
                and interaction.interaction_half_width
                == CHAPTER_ONE_SETTLEMENT_WINDOW_INTERACTION_HALF_WIDTH
                and interaction.interaction_half_depth
                == CHAPTER_ONE_SETTLEMENT_WINDOW_INTERACTION_HALF_DEPTH
                and interaction.requires_facing
                and interaction.walkmesh_anchor
                == CHAPTER_ONE_SETTLEMENT_WINDOW_WALKMESH_ANCHOR
            )
            or (
                interaction.name == "gate window"
                and (interaction.x, interaction.z, interaction.triangle)
                == CHAPTER_ONE_GATE_WINDOW_POSITION
                and interaction.interaction_half_width
                == CHAPTER_ONE_GATE_WINDOW_INTERACTION_HALF_WIDTH
                and interaction.interaction_half_depth
                == CHAPTER_ONE_GATE_WINDOW_INTERACTION_HALF_DEPTH
                and interaction.requires_facing
                and interaction.walkmesh_anchor
                == CHAPTER_ONE_GATE_WINDOW_WALKMESH_ANCHOR
            )
            or (
                interaction.name == "cold window"
                and (interaction.x, interaction.z, interaction.triangle)
                == CHAPTER_ONE_WINDOW_POSITION
                and interaction.interaction_half_width
                == CHAPTER_ONE_WINDOW_INTERACTION_HALF_WIDTH
                and interaction.interaction_half_depth
                == CHAPTER_ONE_WINDOW_INTERACTION_HALF_DEPTH
                and interaction.requires_facing
                and interaction.walkmesh_anchor
                == CHAPTER_ONE_WINDOW_SLOT_ONE_EDGE_ENGINE_POSITION
            )
            or (
                interaction.name == "room heater"
                and (interaction.x, interaction.z, interaction.triangle)
                == CHAPTER_ONE_HEATER_POSITION
                and interaction.interaction_half_width
                == CHAPTER_ONE_HEATER_INTERACTION_HALF_WIDTH
                and interaction.interaction_half_depth
                == CHAPTER_ONE_HEATER_INTERACTION_HALF_DEPTH
                and interaction.requires_facing
                and interaction.walkmesh_anchor
                == CHAPTER_ONE_HEATER_SLOT_ONE_ENGINE_POSITION
            )
            or (
                interaction.name == "reading desk"
                and (interaction.x, interaction.z, interaction.triangle)
                == CHAPTER_ONE_READING_DESK_POSITION
                and interaction.interaction_half_width
                == CHAPTER_ONE_READING_DESK_INTERACTION_HALF_WIDTH
                and interaction.interaction_half_depth
                == CHAPTER_ONE_READING_DESK_INTERACTION_HALF_DEPTH
                and interaction.requires_facing
                and interaction.walkmesh_anchor
                == CHAPTER_ONE_READING_DESK_SLOT_ONE_ENGINE_POSITION
            )
        )
        point_x, point_z = (
            interaction.walkmesh_anchor
            if interaction.walkmesh_anchor is not None
            else (interaction.x, interaction.z)
        )
        if interaction.walkmesh_anchor is not None:
            effective_x = interaction.interaction_half_width * 2 + 0x10
            effective_z = interaction.interaction_half_depth * 2 + 0x10
            if (
                abs(point_x - interaction.x) > effective_x
                or abs(point_z - interaction.z) > effective_z
            ):
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} {interaction.name} "
                    "walkmesh anchor left its effective interaction box"
                )
            if not approved_recessed_anchor:
                raise RicoArcBuildError(
                    "Only Chapter 1's exact audited recessed carriers may use "
                    "a walkmesh anchor"
                )
        points.append(
            (
                (
                    f"{interaction.name} walkmesh anchor"
                    if interaction.walkmesh_anchor is not None
                    else interaction.name
                ),
                point_x,
                point_z,
                interaction.triangle,
            )
        )
    points.append(
        ("chapter exit", contract.exit_x, contract.exit_z, contract.exit_triangle)
    )
    for name, x, z, triangle in points:
        if triangle >= len(triangles) or not _point_inside_triangle(
            (x, z), triangles[triangle]
        ):
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} {name} ({x},{z}) left "
                f"walkmesh triangle {triangle}"
            )
        if chapter.chapter_id == 1:
            vertices = triangles[triangle]
            crosses = tuple(
                (end[0] - start[0]) * (z - start[2])
                - (end[2] - start[2]) * (x - start[0])
                for start, end in zip(
                    vertices,
                    (*vertices[1:], vertices[0]),
                    strict=True,
                )
            )
            if not (
                all(value > 0 for value in crosses)
                or all(value < 0 for value in crosses)
            ):
                raise RicoArcBuildError(
                    f"Chapter 1 {name} ({x},{z}) is not strictly inside "
                    f"walkmesh triangle {triangle}"
                )

    if chapter.chapter_id == 1:
        anna_x, anna_z, anna_triangle = CHAPTER_ONE_ANNA_VISUAL_POSITION
        if (
            anna_triangle >= len(triangles)
            or not _point_inside_triangle(
                (anna_x, anna_z), triangles[anna_triangle]
            )
            or {vertex[1] for vertex in triangles[anna_triangle]} != {0}
        ):
            raise RicoArcBuildError(
                "Chapter 1 standing Anne left the flat floor at the bed's foot"
            )
        vertices = triangles[anna_triangle]
        crosses = tuple(
            (end[0] - start[0]) * (anna_z - start[2])
            - (end[2] - start[2]) * (anna_x - start[0])
            for start, end in zip(
                vertices,
                (*vertices[1:], vertices[0]),
                strict=True,
            )
        )
        if not (
            all(value > 0 for value in crosses)
            or all(value < 0 for value in crosses)
        ):
            raise RicoArcBuildError(
                "Chapter 1 standing Anne is not strictly inside the foot-side floor"
            )

    # A coordinate can be inside a valid triangle yet remain stranded on a
    # disconnected island.  Require every objective and the return point to
    # share an edge-connected walkmesh component with Rico's entry.
    edge_owners: dict[tuple[tuple[int, ...], tuple[int, ...]], list[int]] = {}
    for triangle_index, vertices in enumerate(triangles):
        for vertex_index in range(3):
            edge = tuple(
                sorted(
                    (
                        vertices[vertex_index],
                        vertices[(vertex_index + 1) % 3],
                    )
                )
            )
            edge_owners.setdefault(edge, []).append(triangle_index)
    adjacency = [set() for _triangle in triangles]
    for owners in edge_owners.values():
        for owner in owners:
            adjacency[owner].update(other for other in owners if other != owner)
    reachable = {entry_triangle}
    pending = [entry_triangle]
    while pending:
        owner = pending.pop()
        for neighbor in adjacency[owner] - reachable:
            reachable.add(neighbor)
            pending.append(neighbor)
    for name, _x, _z, triangle in points[1:]:
        if triangle not in reachable:
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} {name} is disconnected from "
                "the playable entry"
            )

    interaction_bits = [
        stage.bit
        for interaction in contract.interactions
        for stage in interaction.stages
    ]
    bits = interaction_bits + (
        [transition.bit] if transition is not None else []
    )
    if (
        not bits
        or any(bit <= PLAYABLE_INTRO_BIT or bit > 15 for bit in bits)
        or len(bits) != len(set(bits))
    ):
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} playable progress bits are invalid: {bits}"
        )
    timed_bits = [timed.bit for timed in contract.timed_bits]
    if (
        any(bit <= PLAYABLE_INTRO_BIT or bit > 15 for bit in timed_bits)
        or len(timed_bits) != len(set(timed_bits))
        or set(timed_bits) & set(bits)
        or any(
            timed.trigger_bit not in set(bits)
            or not 1 <= timed.frames <= 0x7FFF
            for timed in contract.timed_bits
        )
    ):
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} timed progress bits are invalid: "
            f"{contract.timed_bits}"
        )
    expected_timed_bits = (
        (
            PlayableTimedBit(
                bit=CHAPTER_ONE_KETTLE_BOILED_BIT,
                trigger_bit=CHAPTER_ONE_STOVE_ON_BIT,
                frames=CHAPTER_ONE_KETTLE_BOIL_FRAMES,
            ),
        )
        if contract.chapter_id == 1
        else ()
    )
    if contract.timed_bits != expected_timed_bits:
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} has unsupported timed progress"
        )
    if contract.chapter_id == 1 and set(bits) & {
        CHAPTER_ONE_KETTLE_BOILED_BIT,
        CHAPTER_ONE_KETTLE_FILLED_BIT,
    }:
        raise RicoArcBuildError(
            "Chapter 1 objective bits collide with internal kettle state"
        )
    known_bits = set(bits) | set(timed_bits)
    stages_by_bit = {
        stage.bit: stage
        for interaction in contract.interactions
        for stage in interaction.stages
    }
    # Runtime dispatch always selects the first unfinished stage on a given
    # carrier, and a disabled carrier cannot be used until its activation bits
    # are present.  Model both constraints as real prerequisites so static
    # reachability cannot approve a chapter that deadlocks in the field.
    effective_requirements: dict[int, set[int]] = {}
    for interaction in contract.interactions:
        if (
            not any(stage.completes_chapter for stage in interaction.stages)
            and not interaction.repeat_dialogue
        ):
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} interaction "
                f"{interaction.name!r} needs contextual repeat dialogue"
            )
        if not set(interaction.activation_required_bits) <= known_bits:
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} {interaction.name} has unknown "
                "activation prerequisites"
            )
        if (
            interaction.hide_bound_actors_until_active
            and (
                not interaction.activation_required_bits
                or not INTERACTION_ACTOR_BINDINGS.get(
                    chapter.chapter_id,
                    {},
                ).get(interaction.name)
            )
        ):
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} {interaction.name} has an "
                "incomplete actor-arrival gate"
            )
        if (
            interaction.activation_required_bits
            and not set(interaction.activation_required_bits)
            <= set(interaction.stages[0].required_bits)
        ):
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} {interaction.name} can be "
                "selected through its actor before the activation gate is "
                "safe"
            )
        prior_stage_bits: set[int] = set()
        for stage in interaction.stages:
            if stage.choice_text is None:
                if (
                    isinstance(stage.accepted_selection, bool)
                    or stage.accepted_selection != 1
                    or stage.rejection_dialogue
                ):
                    raise RicoArcBuildError(
                        f"Chapter {chapter.chapter_id} {interaction.name} "
                        "configures a choice result without choice text"
                    )
            else:
                choice_count = _playable_choice_count(stage.choice_text)
                if (
                    isinstance(stage.accepted_selection, bool)
                    or not isinstance(stage.accepted_selection, int)
                    or not 1 <= stage.accepted_selection <= choice_count
                ):
                    raise RicoArcBuildError(
                        f"Chapter {chapter.chapter_id} {interaction.name} "
                        f"accepts choice row {stage.accepted_selection!r}; "
                        f"valid rows are 1..{choice_count}"
                    )
            if stage.accepted_sound_id is not None and (
                stage.choice_text is None
                or isinstance(stage.accepted_sound_id, bool)
                or not isinstance(stage.accepted_sound_id, int)
                or not 0 <= stage.accepted_sound_id <= 0x7FFF
            ):
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} {interaction.name} stage "
                    f"{stage.bit} has an invalid accepted-choice sound"
                )
            if not set(stage.required_bits) <= known_bits:
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} {interaction.name} has an "
                    "unknown prerequisite bit"
                )
            if stage.locked_dialogue and stage.locked_dialogue_states:
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} {interaction.name} stage "
                    f"{stage.bit} mixes fallback and state-specific locked dialogue"
                )
            if stage.locked_dialogue_steps and (
                stage.locked_dialogue or stage.locked_dialogue_states
            ):
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} {interaction.name} stage "
                    f"{stage.bit} mixes ordered and other locked dialogue"
                )
            if stage.required_bits and not (
                stage.locked_dialogue
                or stage.locked_dialogue_steps
                or stage.locked_dialogue_states
            ):
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} {interaction.name} stage "
                    f"{stage.bit} needs contextual prerequisite dialogue"
                )
            if stage.locked_dialogue_steps:
                step_bits = tuple(
                    missing_bit
                    for missing_bit, _dialogue in stage.locked_dialogue_steps
                )
                if (
                    step_bits != tuple(stage.required_bits)
                    or len(step_bits) != len(set(step_bits))
                    or any(
                        not step_dialogue
                        for _missing_bit, step_dialogue in (
                            stage.locked_dialogue_steps
                        )
                    )
                ):
                    raise RicoArcBuildError(
                        f"Chapter {chapter.chapter_id} {interaction.name} stage "
                        f"{stage.bit} has invalid ordered locked dialogue"
                    )
            if stage.locked_dialogue_states:
                if not stage.required_bits:
                    raise RicoArcBuildError(
                        f"Chapter {chapter.chapter_id} {interaction.name} stage "
                        f"{stage.bit} has state dialogue without prerequisites"
                    )
                required = tuple(stage.required_bits)
                required_set = frozenset(required)
                if len(required) != len(required_set):
                    raise RicoArcBuildError(
                        f"Chapter {chapter.chapter_id} {interaction.name} stage "
                        f"{stage.bit} repeats a state-dialogue prerequisite"
                    )
                actual_states: list[frozenset[int]] = []
                for completed_bits, state_dialogue in (
                    stage.locked_dialogue_states
                ):
                    completed = frozenset(completed_bits)
                    if (
                        len(completed) != len(completed_bits)
                        or not completed <= required_set
                        or completed == required_set
                        or not state_dialogue
                    ):
                        raise RicoArcBuildError(
                            f"Chapter {chapter.chapter_id} {interaction.name} "
                            f"stage {stage.bit} has an invalid locked state"
                        )
                    actual_states.append(completed)
                expected_states = {
                    frozenset(
                        bit
                        for offset, bit in enumerate(required)
                        if state & (1 << offset)
                    )
                    for state in range((1 << len(required)) - 1)
                }
                if (
                    len(actual_states) != len(set(actual_states))
                    or set(actual_states) != expected_states
                ):
                    raise RicoArcBuildError(
                        f"Chapter {chapter.chapter_id} {interaction.name} stage "
                        f"{stage.bit} does not cover every incomplete state"
                    )
            effective_requirements[stage.bit] = (
                set(stage.required_bits)
                | set(interaction.activation_required_bits)
                | prior_stage_bits
            )
            prior_stage_bits = prior_stage_bits | {stage.bit}
    if transition is not None:
        stages_by_bit[transition.bit] = transition
        if not set(transition.required_bits) <= known_bits:
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} exit transition has an "
                "unknown prerequisite bit"
            )
        effective_requirements[transition.bit] = set(
            transition.required_bits
        )
    for timed in contract.timed_bits:
        effective_requirements[timed.bit] = {timed.trigger_bit}
    if not set(contract.required_bits) <= known_bits:
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} exit has an unknown prerequisite bit"
        )

    reachable_bits: set[int] = set()
    while True:
        newly_reachable = {
            bit
            for bit, requirements in effective_requirements.items()
            if requirements <= reachable_bits
        } - reachable_bits
        if not newly_reachable:
            break
        reachable_bits.update(newly_reachable)
    if known_bits - reachable_bits:
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} has unreachable progress bits: "
            f"{sorted(known_bits - reachable_bits)}"
        )

    terminal_stages = [
        (interaction, index, stage)
        for interaction in contract.interactions
        for index, stage in enumerate(interaction.stages)
        if stage.completes_chapter
    ]
    expected_terminal_count = 0 if contract.completion_at_exit else 1
    if len(terminal_stages) != expected_terminal_count:
        location = "the exit" if contract.completion_at_exit else "one stage"
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} must complete at {location}; "
            f"found {len(terminal_stages)} completion stages"
        )
    if contract.completion_at_exit:
        optional_bits = set(contract.optional_bits)
        required_bits = set(contract.required_bits)
        if (
            len(optional_bits) != len(contract.optional_bits)
            or optional_bits & required_bits
            or required_bits | optional_bits != set(bits)
        ):
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} exit completion can bypass "
                "playable objective bits"
            )
        completion_closure = set(contract.required_bits)
        pending_bits = list(contract.required_bits)
    else:
        terminal_interaction, terminal_index, terminal_stage = terminal_stages[0]
        if terminal_index != len(terminal_interaction.stages) - 1:
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} completion stage is not terminal"
            )
        completion_closure = {terminal_stage.bit}
        pending_bits = list(effective_requirements[terminal_stage.bit])
    while pending_bits:
        bit = pending_bits.pop()
        if bit in completion_closure:
            if contract.completion_at_exit and bit in effective_requirements:
                pending_bits.extend(effective_requirements[bit])
            continue
        completion_closure.add(bit)
        pending_bits.extend(effective_requirements[bit])
    if not set(contract.required_bits) <= completion_closure:
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} completion can bypass required bits"
        )

    routed_refs: list[DialogueRef] = list(contract.exit_dialogue)
    for interaction in contract.interactions:
        routed_refs.extend(interaction.repeat_dialogue)
        for stage in interaction.stages:
            routed_refs.extend(stage.dialogue)
            routed_refs.extend(stage.rejection_dialogue)
            routed_refs.extend(stage.after_dialogue)
            routed_refs.extend(stage.locked_dialogue)
            for _missing_bit, step_dialogue in stage.locked_dialogue_steps:
                routed_refs.extend(step_dialogue)
            for _completed_bits, state_dialogue in stage.locked_dialogue_states:
                routed_refs.extend(state_dialogue)
    if transition is not None:
        routed_refs.extend(transition.doorway_dialogue)
        routed_refs.extend(transition.firewood_dialogue)
        routed_refs.extend(transition.sickness_dialogue)
        routed_refs.extend(transition.loss_dialogue)
        routed_refs.extend(transition.funeral_dialogue)
    bracketed_refs = [
        ref
        for ref in routed_refs
        if isinstance(ref, int) and chapter.blocks[ref].lstrip().startswith("[")
    ]
    if bracketed_refs:
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} routes screenplay prose blocks: "
            f"{sorted(set(bracketed_refs))}"
        )

    battle_configurations = _battle_configurations(contract)
    if battle_configurations:
        encounters = EncounterTable(components[6])
        if any(encounters.weights):
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} retains random encounters"
            )
        for configuration, gear_battle in battle_configurations.items():
            if not components[6][configuration * FORMATION_SIZE + 1] & 0x80:
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} formation {configuration} "
                    "still permits Escape"
                )
            active = tuple(
                encounters.get_enemy(configuration, slot)
                for slot in range(8)
                if encounters.get_enemy(configuration, slot).enemy_id
                != EMPTY_ENEMY_ID
            )
            if not active:
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} battle configuration "
                    f"{configuration} is empty"
                )
            if any(enemy.is_gear != gear_battle for enemy in active):
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} formation {configuration} "
                    "has the wrong battle scale"
                )
            if configuration == 15 and len(active) != 1:
                raise RicoArcBuildError(
                    "Protocol B defense formation must contain exactly one Gear"
                )


def _build_playable_chapter_bundle(
    donor_bundle: bytes,
    chapter: Chapter,
    return_hub: int,
    next_chapter: Chapter | None,
    *,
    ancillary_fields: ChapterOneAncillaryFields | Mapping[str, int] | None = None,
    chapter_two_bedroom_field: int = CHAPTER_TWO_BEDROOM_FIELD,
) -> bytes:
    if not 0 <= chapter_two_bedroom_field <= 0x7FFF:
        raise RicoArcBuildError("Chapter 2 bedroom field is outside 0..32767")
    chapter_one_fields = _chapter_one_ancillary_fields(ancillary_fields)
    parsed = parse_field(donor_bundle)
    components = [part.data for part in parsed.parts]
    contract = _playable_chapter_contract(chapter.chapter_id)
    needs_direct_successor = 2 <= chapter.chapter_id <= 6
    if needs_direct_successor and (
        next_chapter is None
        or next_chapter.chapter_id != chapter.chapter_id + 1
    ):
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} needs its exact successor exposition"
        )
    if chapter.chapter_id == 7 and next_chapter is not None:
        raise RicoArcBuildError("Chapter 7 cannot have a successor")
    next_chapter_exposition = (
        _chapter_selection_exposition(next_chapter)
        if needs_direct_successor and next_chapter is not None
        else ()
    )
    _validate_playable_visible_prop_sources(
        chapter.chapter_id,
        parsed.header,
        components,
    )
    if chapter.chapter_id == 2:
        if chapter.donor_field != CHAPTER_TWO_MAIN_FIELD_DONOR:
            raise RicoArcBuildError(
                "Chapter 2 sitting-room reconstruction requires donor field 218"
            )
        _validate_chapter_two_room_source(parsed.header, components)
    if chapter.chapter_id == 4:
        _validate_chapter_four_private_scene_source(parsed.header, components)
    if chapter.chapter_id in (5, 6):
        expected_donor = {5: 235, 6: 232}[chapter.chapter_id]
        if chapter.donor_field != expected_donor:
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} solid exit requires donor field "
                f"{expected_donor}"
            )
        _validate_chapter_five_six_exit_door_source(
            chapter.chapter_id,
            parsed.header,
            components,
        )
    if chapter.chapter_id == 7:
        if chapter.donor_field != 298:
            raise RicoArcBuildError(
                "Chapter 7 bedroom reconstruction requires donor field 298"
            )
        _validate_chapter_seven_room_source(parsed.header, components)
    source_walkmesh_component = components[1]
    source_actor_component = components[mass_driver.ACTOR_INDEX]
    if chapter.chapter_id == 1:
        if chapter.donor_field != 229:
            raise RicoArcBuildError(
                "Chapter 1 young-Rico animation fix requires donor field 229"
            )
        _validate_chapter_one_anna_source(parsed.header, components)
        _validate_chapter_one_door_source(components)
        components[1] = _seal_chapter_one_house_door(
            source_walkmesh_component
        )
        _validate_chapter_one_door_departure_route(components[1])
        components[mass_driver.ACTOR_INDEX] = _alias_young_rico_run_to_walk(
            source_actor_component
        )
    if chapter.chapter_id == 4:
        components[1] = _seal_chapter_four_office_door(
            source_walkmesh_component
        )
    if chapter.chapter_id == 7:
        components[1] = _seal_chapter_seven_bedroom_door(
            source_walkmesh_component
        )
    if chapter.chapter_id == 2:
        components[SCRIPT_INDEX] = mass_driver._replace_field_entry(
            components[SCRIPT_INDEX],
            0,
            CHAPTER_TWO_MAIN_ENTRY,
            CHAPTER_TWO_MAIN_PLAYABLE_ENTRY,
        )
    components[SCRIPT_INDEX] = _normalize_playable_party_script(
        chapter,
        components[SCRIPT_INDEX],
    )
    if chapter.chapter_id == 1:
        components[SCRIPT_INDEX] = _install_chapter_one_stove_audio_helper(
            components[SCRIPT_INDEX]
        )
    source_encounters = components[6]
    components[6] = _install_playable_encounters(source_encounters, contract)
    _validate_playable_contract(components, chapter, contract)

    custom_texts = _playable_custom_texts(
        contract,
        additional_texts=next_chapter_exposition,
    )
    appended_texts = tuple(chapter.blocks) + custom_texts
    components[DIALOGUE_INDEX], authored_base = _append_dialogue_blocks(
        components[DIALOGUE_INDEX],
        appended_texts,
        fit_windows=chapter.chapter_id == 1,
        sentence_safe_pages=chapter.chapter_id == 1,
    )
    custom_ids = {
        text: authored_base + len(chapter.blocks) + index
        for index, text in enumerate(custom_texts)
    }
    next_chapter_exposition_ids = tuple(
        custom_ids[text] for text in next_chapter_exposition
    )

    editor = AtelScript(components[SCRIPT_INDEX])
    old_entity_count = editor.entity_count
    if old_entity_count < 2:
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} donor has too few actors: {old_entity_count}"
        )
    registered_characters = _registered_character_entities(editor)
    native_party_entities = _playable_native_party_entities(chapter, editor)
    missing_characters = _missing_playable_characters(chapter, editor)
    leader_character = CHAPTER_PARTIES[chapter.chapter_id][0]
    if chapter.donor_field in VARIABLE_PARTY_DONORS:
        leader_entity = 1
    else:
        leader_entity = registered_characters.get(leader_character)
        if leader_entity is None:
            try:
                leader_entity = old_entity_count + missing_characters.index(
                    leader_character
                )
            except ValueError as exc:
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} has no leader party carrier"
                ) from exc
    staged_party_entities: dict[int, tuple[int, int, int]] = {}
    for character, (x, z) in STAGED_PARTY_ACTORS.get(
        chapter.chapter_id,
        {},
    ).items():
        entity = registered_characters.get(character)
        if entity is None:
            try:
                entity = old_entity_count + missing_characters.index(character)
            except ValueError as exc:
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} cannot stage character {character}"
                ) from exc
        staged_party_entities[entity] = (character, x, z)
    controller_count = len(contract.interactions) + 1
    inserted_records = [
        mass_driver._field_actor_record(0x01E0, 0, 0, 0)
        for _character in missing_characters
    ] + [
        mass_driver._field_actor_record(0x01E0, interaction.x, interaction.z, 0)
        for interaction in contract.interactions
    ] + [
        mass_driver._field_actor_record(
            0x01E0,
            contract.exit_x,
            contract.exit_z,
            0,
        )
    ]
    header = _insert_dynamic_actor_records(
        parsed.header,
        old_entity_count=old_entity_count,
        records_to_insert=inserted_records,
    )
    entry_x, entry_z, _entry_triangle = PLAYABLE_ENTRY_POSITIONS[
        chapter.chapter_id
    ]
    header = _place_actor_record(
        header,
        leader_entity,
        entry_x,
        entry_z,
    )
    for entity, (_character, x, z) in staged_party_entities.items():
        header = _place_actor_record(header, entity, x, z)
    if chapter.chapter_id == 2:
        hammer_x, hammer_z, _hammer_triangle = (
            CHAPTER_TWO_HAMMER_STAGE_POSITION
        )
        header = _place_actor_record(
            header,
            CHAPTER_TWO_HAMMER_ENTITY,
            hammer_x,
            hammer_z,
        )
    editor = AtelScript(
        mass_driver._extend_atel_entity_table(
            editor.to_bytes(),
            old_entity_count + len(inserted_records),
        )
    )
    stop_pc = editor.append_raw_routine(b"\x00")
    disable_dialogue_pc = editor.append_raw_routine(DISABLE_DIALOGUE_UPDATE)
    bound_actor_entities = {
        entity
        for entities in INTERACTION_ACTOR_BINDINGS.get(
            chapter.chapter_id,
            {},
        ).values()
        for entity in entities
    }

    # Keep native actor initialization so the authentic room and visible cast
    # still render, but run no donor story logic.  Only party actors retain
    # their native update loop.  This explicit allowlist prevents an old
    # helper/action slot from jumping into retail dialogue or transitions.
    # Retained ambient actors also run one self-local OP2A update so their
    # now-retired script 2 cannot silently steal Cross from a nearby authored
    # interaction.  Bound conversation actors are deliberately excluded;
    # OP2A is one-way for the lifetime of the field.
    for entity in range(old_entity_count):
        for script_index in range(2, 32):
            editor.set_script_pointer(entity, script_index, stop_pc)
        if entity != 0 and entity not in native_party_entities:
            editor.set_script_pointer(
                entity,
                1,
                (
                    stop_pc
                    if entity in bound_actor_entities
                    else disable_dialogue_pc
                ),
            )

    # The sanitizer above deliberately retires every retail action helper.
    # Re-enable only the exact native exit-leaf helpers pinned by the source
    # validators.  Their bytecode-relative addresses survive the entity-table
    # extension unchanged.
    if chapter.chapter_id == 1:
        editor.set_script_pointer(
            CHAPTER_ONE_DOOR_ENTITY,
            CHAPTER_ONE_DOOR_OPEN_SCRIPT,
            CHAPTER_ONE_DOOR_OPEN_PC,
        )
    if chapter.chapter_id == 2:
        editor.append_and_repoint(
            CHAPTER_TWO_MAIN_DOOR_ENTITY,
            2,
            _chapter_two_main_bedroom_action(chapter_two_bedroom_field),
        )
    if chapter.chapter_id == 4:
        editor.set_script_pointer(
            CHAPTER_FOUR_DOOR_ENTITY,
            CHAPTER_FOUR_DOOR_OPEN_SCRIPT,
            CHAPTER_FOUR_DOOR_OPEN_PC,
        )
        editor.set_script_pointer(
            CHAPTER_FOUR_DOOR_ENTITY,
            CHAPTER_FOUR_DOOR_CLOSE_SCRIPT,
            CHAPTER_FOUR_DOOR_CLOSE_PC,
        )
    if chapter.chapter_id == 5:
        editor.set_script_pointer(
            CHAPTER_FIVE_DOOR_ENTITY,
            CHAPTER_FIVE_DOOR_OPEN_SCRIPT,
            CHAPTER_FIVE_DOOR_OPEN_PC,
        )
        editor.append_and_repoint(
            CHAPTER_FIVE_DOOR_ENTITY,
            CHAPTER_FIVE_DOOR_CLOSE_SCRIPT,
            CHAPTER_FIVE_DOOR_CLOSE_BODY,
        )
    if chapter.chapter_id == 6:
        editor.set_script_pointer(
            CHAPTER_SIX_DOOR_ENTITY,
            CHAPTER_SIX_DOOR_OPEN_SCRIPT,
            CHAPTER_SIX_DOOR_OPEN_PC,
        )
        editor.append_and_repoint(
            CHAPTER_SIX_DOOR_ENTITY,
            CHAPTER_SIX_DOOR_CLOSE_SCRIPT,
            CHAPTER_SIX_DOOR_CLOSE_BODY,
        )
    if chapter.chapter_id == 7:
        editor.set_script_pointer(
            CHAPTER_SEVEN_DOOR_ENTITY,
            CHAPTER_SEVEN_DOOR_OPEN_SCRIPT,
            CHAPTER_SEVEN_DOOR_OPEN_PC,
        )
        editor.set_script_pointer(
            CHAPTER_SEVEN_DOOR_ENTITY,
            CHAPTER_SEVEN_DOOR_CLOSE_SCRIPT,
            CHAPTER_SEVEN_DOOR_CLOSE_PC,
        )

    # Some donor rooms also carry one-shot retail cast/story managers in
    # script 0.  Those routines are not harmless decoration: depending on the
    # player's imported story variables, they can hide actors, rewrite party
    # state, or advance GameProgress before our chapter director even runs.
    # Retire only the audited managers below so ordinary prop/NPC initializers
    # still build the authentic room.
    for entity in HAZARDOUS_DONOR_INIT_ENTITIES.get(chapter.donor_field, ()):
        if not 0 < entity < old_entity_count or entity in native_party_entities:
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} cannot retire donor manager "
                f"entity {entity}"
            )
        editor.append_and_repoint(entity, 0, INERT_HIDDEN_INIT)
    if chapter.chapter_id == 2:
        editor.append_and_repoint(
            CHAPTER_TWO_HAMMER_ENTITY,
            0,
            _chapter_two_hammer_init(),
        )
        hammer_route_pc = editor.bytecode_size
        editor.append_and_repoint(
            CHAPTER_TWO_HAMMER_ENTITY,
            1,
            _chapter_two_hammer_stair_route(hammer_route_pc),
        )
    hide_entities = {
        entity
        for interaction in contract.interactions
        for stage in interaction.stages
        for entity in stage.hide_entities_after
    }
    private_departure_entities = (
        {CHAPTER_FOUR_FEI_ENTITY, CHAPTER_FOUR_BART_ENTITY}
        if chapter.chapter_id == 4
        else set()
    )
    for entity in hide_entities:
        if not 0 < entity < old_entity_count or entity == leader_entity:
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} cannot hide donor entity {entity}"
            )
        if entity in private_departure_entities:
            editor.append_and_repoint(
                entity,
                CHAPTER_FOUR_PRIVATE_STAGE_SCRIPT,
                _chapter_four_private_stage_body(entity),
            )
            editor.append_and_repoint(
                entity,
                CHAPTER_FOUR_PRIVATE_APPROACH_SCRIPT,
                _chapter_four_private_route_body(
                    CHAPTER_FOUR_PRIVATE_APPROACH_ROUTES[entity],
                    hide_offstage=False,
                ),
            )
            editor.append_and_repoint(
                entity,
                CHAPTER_FOUR_PRIVATE_CROSS_SCRIPT,
                _chapter_four_private_route_body(
                    CHAPTER_FOUR_PRIVATE_CROSS_ROUTES[entity],
                    hide_offstage=True,
                ),
            )
            continue
        editor.append_and_repoint(
            entity,
            4,
            b"\x23" + PLAYABLE_ACTOR_GHOST_FLAGS + b"\x00",
        )

    director_pc = editor.bytecode_size
    director = (
        _chapter_two_director(chapter.music)
        if chapter.chapter_id == 2
        else _sanitized_director(chapter.music)
    )
    if editor.append_raw_routine(director) != director_pc:
        raise RicoArcBuildError("Playable director append position drifted")
    editor.set_script_pointer(0, 0, director_pc)

    # Timeline framing belongs exclusively to the selection that launches the
    # field.  Once the destination renders, entity 0 remains silent so the
    # player discovers the room through dialogue and object interactions.
    silent_update_pc = editor.bytecode_size
    silent_update = _playable_silent_update()
    if editor.append_raw_routine(silent_update) != silent_update_pc:
        raise RicoArcBuildError("Playable silent update append position drifted")
    editor.set_script_pointer(0, 1, silent_update_pc)
    if chapter.chapter_id == 2:
        # e2 itself owns the real bedroom-door action.  The ordinary ambient
        # sanitizer's OP2A update would permanently disable Cross activation,
        # so give this one audited leaf the same inert, non-disabling update as
        # the director.
        editor.set_script_pointer(
            CHAPTER_TWO_MAIN_DOOR_ENTITY,
            1,
            silent_update_pc,
        )

    next_entity = old_entity_count
    party_update_pc = editor.append_raw_routine(b"\xA7\x00")
    young_rico_update_pc = (
        editor.append_raw_routine(YOUNG_RICO_PARTY_UPDATE)
        if chapter.chapter_id == 1
        else None
    )
    party_entities = set(native_party_entities)
    if chapter.donor_field in VARIABLE_PARTY_DONORS:
        party_selectors = {1: 0xFD, 2: 0xFE, 3: 0xFF}
    else:
        party_selectors = {
            entity: character
            for character, entity in registered_characters.items()
        }
    for character in missing_characters:
        entity = next_entity
        next_entity += 1
        party_entities.add(entity)
        party_selectors[entity] = character
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)
        init_pc = editor.append_raw_routine(_normalized_party_init(character))
        editor.set_script_pointer(entity, 0, init_pc)
        editor.set_script_pointer(entity, 1, party_update_pc)

    # Retail donor update scripts often contain story-specific movement and
    # conditional branches.  The proven playable-field carrier is the plain
    # A7 follow/update loop.  Young Rico alone adds the post-A7 jump guard
    # required by field 229's finite NPC animation bank.
    for entity in party_entities:
        update_pc = party_update_pc
        if chapter.chapter_id == 1 and entity == leader_entity:
            if young_rico_update_pc is None:
                raise RicoArcBuildError("Young Rico update routine was not installed")
            update_pc = young_rico_update_pc
        editor.set_script_pointer(
            entity,
            1,
            stop_pc if entity in staged_party_entities else update_pc,
        )
    for entity, selector in party_selectors.items():
        # Field 229 carries a native local young-Rico sprite bank.  Register
        # Rico through INIT_ENTITY_PC first, then replace only his graphics
        # with that local bank and retire the donor's separate cutscene double
        # below.  Every other party actor receives ordinary PC registration.
        if chapter.chapter_id == 1 and entity == leader_entity:
            editor.append_and_repoint(
                entity,
                0,
                _young_rico_party_init(entry_x, entry_z),
            )
            continue
        position = (
            (entry_x, entry_z)
            if entity == leader_entity and chapter.chapter_id != 2
            else None
        )
        editor.append_and_repoint(
            entity,
            0,
            _normalized_party_init(selector, position),
        )
    chapter_one_departure_pc: int | None = None
    if chapter.chapter_id == 1:
        young_rico_cutscene_entity = 5
        if young_rico_cutscene_entity >= old_entity_count:
            raise RicoArcBuildError("Field 229 lost its native young-Rico actor")
        editor.append_and_repoint(
            young_rico_cutscene_entity,
            0,
            INERT_HIDDEN_INIT,
        )
        # Keep Anne's native stable standing pose on the floor at the bed's
        # foot with her normal actor collision.  The model-less controller at
        # the same point owns interaction without adding another obstacle.
        editor.append_and_repoint(
            CHAPTER_ONE_ANNA_ENTITY,
            0,
            CHAPTER_ONE_ANNA_PLAYABLE_INIT,
        )
        anna_update_pc = editor.bytecode_size
        installed_anna_update_pc = editor.append_and_repoint(
            CHAPTER_ONE_ANNA_ENTITY,
            1,
            _chapter_one_anna_ambient_update(anna_update_pc),
        )
        if installed_anna_update_pc != anna_update_pc:
            raise RicoArcBuildError("Chapter 1 Anne cough append position drifted")
        editor.append_and_repoint(
            CHAPTER_ONE_ANNA_ENTITY,
            CHAPTER_ONE_ANNA_INTERACTION_COUGH_SCRIPT,
            CHAPTER_ONE_ANNA_COUGH_ONCE + b"\x00",
        )
        chapter_one_departure_pc = editor.append_and_repoint(
            leader_entity,
            CHAPTER_ONE_DOOR_DEPARTURE_SCRIPT,
            _chapter_one_door_departure_body(),
        )

    chapter_one_bedside_action_pc: int | None = None
    for interaction in contract.interactions:
        hammer_arrival_gate = (
            chapter.chapter_id == 2 and interaction.name == "Hammer"
        )
        entity = next_entity
        next_entity += 1
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)
        editor.append_and_repoint(
            entity,
            0,
            _playable_controller_init(
                interaction.x,
                interaction.z,
                half_width=interaction.interaction_half_width,
                half_depth=interaction.interaction_half_depth,
                requires_facing=interaction.requires_facing,
                initially_disabled=(
                    bool(interaction.activation_required_bits)
                    or hammer_arrival_gate
                ),
            ),
        )
        if hammer_arrival_gate:
            activation_pc = editor.bytecode_size
            editor.append_and_repoint(
                entity,
                1,
                _chapter_two_hammer_controller_gate(
                    activation_pc,
                    interaction.x,
                    interaction.z,
                ),
            )
        elif interaction.activation_required_bits:
            activation_pc = editor.bytecode_size
            editor.append_and_repoint(
                entity,
                1,
                _playable_controller_activation_gate(
                    activation_pc,
                    interaction.activation_required_bits,
                    interaction.x,
                    interaction.z,
                ),
            )
        if chapter.chapter_id == 1 and interaction.name == "cooking counter":
            timer_pc = editor.bytecode_size
            installed_timer_pc = editor.append_and_repoint(
                entity,
                1,
                _chapter_one_kettle_timer_update(timer_pc),
            )
            if installed_timer_pc != timer_pc:
                raise RicoArcBuildError(
                    "Chapter 1 kettle timer append position drifted"
                )
        action_pc = editor.bytecode_size
        action = _build_playable_interaction_action(
            interaction,
            base_pc=action_pc,
            authored_base=authored_base,
            authored_count=len(chapter.blocks),
            custom_ids=custom_ids,
            field_music=chapter.music,
            chapter_party=CHAPTER_PARTIES[chapter.chapter_id],
            contract=contract,
            return_hub=return_hub,
            next_chapter_exposition_ids=next_chapter_exposition_ids,
        )
        installed_action_pc = editor.append_and_repoint(entity, 2, action)
        if installed_action_pc != action_pc:
            raise RicoArcBuildError("Playable action append position drifted")
        if chapter.chapter_id == 1 and interaction.name == "Anne's bedside":
            chapter_one_bedside_action_pc = installed_action_pc
        for actor_entity in INTERACTION_ACTOR_BINDINGS.get(
            chapter.chapter_id,
            {},
        ).get(interaction.name, ()):
            if not 0 < actor_entity < old_entity_count:
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} interaction "
                    f"{interaction.name!r} lost actor {actor_entity}"
                )
            # A pre-arrival actor remains fully inert; its co-located model-less
            # controller stays parked until the activation gate opens.  Once
            # visible, either the lower-ID actor or the controller may win
            # action selection, so both forward to the same action routine.
            if (
                hammer_arrival_gate
                and actor_entity == CHAPTER_TWO_HAMMER_ENTITY
            ):
                gate_pc = editor.bytecode_size
                gate_body = _chapter_two_hammer_actor_action_gate(
                    gate_pc,
                    installed_action_pc,
                )
                installed_gate_pc = editor.append_and_repoint(
                    actor_entity,
                    2,
                    gate_body,
                )
                if installed_gate_pc != gate_pc:
                    raise RicoArcBuildError(
                        "Chapter 2 Hammer action gate append position drifted"
                    )
            elif interaction.hide_bound_actors_until_active:
                gate_pc = editor.bytecode_size
                gate_body = _playable_actor_action_gate(
                    gate_pc,
                    interaction.activation_required_bits,
                    installed_action_pc,
                )
                installed_gate_pc = editor.append_and_repoint(
                    actor_entity,
                    2,
                    gate_body,
                )
                if installed_gate_pc != gate_pc:
                    raise RicoArcBuildError(
                        "Playable actor action gate append position drifted"
                    )
            else:
                editor.set_script_pointer(actor_entity, 2, installed_action_pc)
            if interaction.hide_bound_actors_until_active:
                if actor_entity == leader_entity:
                    raise RicoArcBuildError(
                        f"Chapter {chapter.chapter_id} cannot gate Rico's arrival"
                    )
                arrival_pc = editor.bytecode_size
                editor.append_and_repoint(
                    actor_entity,
                    1,
                    _playable_actor_arrival_gate(
                        arrival_pc,
                        interaction.activation_required_bits,
                    ),
                )

    if chapter.chapter_id == 1:
        if chapter_one_bedside_action_pc is None:
            raise RicoArcBuildError("Chapter 1 lost Anne's bedside action")
        _validate_chapter_one_anna_output(
            editor,
            chapter_one_bedside_action_pc,
        )

    exit_entity = next_entity
    next_entity += 1
    if next_entity != editor.entity_count:
        raise RicoArcBuildError("Playable controller entity allocation drifted")
    for script_index in range(32):
        editor.set_script_pointer(exit_entity, script_index, stop_pc)
    editor.append_and_repoint(
        exit_entity,
        0,
        _playable_exit_controller_init(contract),
    )
    exit_pc = editor.bytecode_size
    installed_exit_pc = editor.append_and_repoint(
        exit_entity,
        2,
        _build_playable_exit_action(
            contract,
            leader_entity=leader_entity,
            base_pc=exit_pc,
            return_hub=return_hub,
            authored_base=authored_base,
            authored_count=len(chapter.blocks),
            custom_ids=custom_ids,
            next_chapter_exposition_ids=next_chapter_exposition_ids,
            chapter_one_firewood_field=chapter_one_fields.firewood,
        ),
    )
    if installed_exit_pc != exit_pc:
        raise RicoArcBuildError("Playable exit append position drifted")
    if chapter.chapter_id == 1:
        if chapter_one_departure_pc is None:
            raise RicoArcBuildError("Chapter 1 lost Rico's door staging")
        if contract.exit_transition is None:
            raise RicoArcBuildError("Chapter 1 lost its doorway conversation")
        doorway_dialogue_ids = _resolve_playable_dialogue(
            contract.exit_transition.doorway_dialogue,
            authored_base=authored_base,
            authored_count=len(chapter.blocks),
            custom_ids=custom_ids,
        )
        _validate_chapter_one_door_output(
            editor,
            leader_entity=leader_entity,
            departure_pc=chapter_one_departure_pc,
            exit_entity=exit_entity,
            exit_action_pc=installed_exit_pc,
            stop_pc=stop_pc,
            doorway_dialogue_ids=doorway_dialogue_ids,
            firewood_field=chapter_one_fields.firewood,
        )

    components[SCRIPT_INDEX] = editor.to_bytes()
    changed_components = [SCRIPT_INDEX, DIALOGUE_INDEX]
    if components[1] != source_walkmesh_component:
        changed_components.append(1)
    if components[mass_driver.ACTOR_INDEX] != source_actor_component:
        changed_components.append(mass_driver.ACTOR_INDEX)
    if components[6] != source_encounters:
        changed_components.append(6)
    bundle = build_field_preserving(
        donor_bundle,
        components,
        tuple(sorted(changed_components)),
        compact_changed=True,
        replacement_header=header,
    )
    reparsed = parse_field(bundle)
    if (
        tuple(part.data for part in reparsed.parts) != tuple(components)
        or len(reparsed.header) != len(header)
        or reparsed.header[0x18C:] != header[0x18C:]
    ):
        raise RicoArcBuildError(
            f"Chapter {chapter.chapter_id} playable field failed packed round-trip"
        )
    return bundle


def _build_scene_bundle(
    donor_bundle: bytes,
    chapter: Chapter,
    return_hub: int,
    next_chapter: Chapter | None,
    *,
    ancillary_fields: ChapterOneAncillaryFields | Mapping[str, int] | None = None,
    chapter_two_bedroom_field: int = CHAPTER_TWO_BEDROOM_FIELD,
) -> bytes:
    """Compatibility entry point; every chapter is now a playable field."""

    return _build_playable_chapter_bundle(
        donor_bundle,
        chapter,
        return_hub,
        next_chapter,
        ancillary_fields=ancillary_fields,
        chapter_two_bedroom_field=chapter_two_bedroom_field,
    )


def _build_chapter_two_bed_reflection_action(base_pc: int) -> bytes:
    """Give the sanitized Champion bed one optional, story-safe reflection."""

    routine = mass_driver._RoutineBuilder(base_pc)
    routine.emit(_playable_action_prefix(base_pc))
    routine.emit(_dialogue_sequence((0,)))
    routine.emit(_playable_action_finish(routine.pc))
    return routine.finish()


def _build_chapter_two_bedroom_bundle(
    donor_bundle: bytes,
    chapter: Chapter,
    main_field: int,
) -> bytes:
    """Sanitize retail field 219 as Chapter 2's optional Champion bedroom."""

    if chapter.chapter_id != 2:
        raise RicoArcBuildError("The Champion bedroom requires Chapter 2")
    if not 0 <= main_field <= 0x7FFF:
        raise RicoArcBuildError("Chapter 2 sitting-room field is outside range")
    components, header = _validate_chapter_two_bedroom_source(donor_bundle)
    source_encounters = components[mass_driver.ENCOUNTER_INDEX]
    if (
        len(source_encounters) != ENCOUNTER_COMPONENT_SIZE
        or _sha256_bytes(source_encounters) != NORTUNE_ENCOUNTER_SHA256
    ):
        raise RicoArcBuildError("Champion-bedroom encounter table changed")
    encounters = bytearray(source_encounters)
    encounters[WEIGHTS_OFFSET : WEIGHTS_OFFSET + FORMATION_COUNT] = bytes(
        FORMATION_COUNT
    )
    components[mass_driver.ENCOUNTER_INDEX] = bytes(encounters)
    components[DIALOGUE_INDEX] = _dialogue_data(
        (CHAPTER_TWO_BED_REFLECTION,)
    )

    editor = AtelScript(components[SCRIPT_INDEX])
    stop_pc = editor.append_raw_routine(b"\x00")
    for entity in range(editor.entity_count):
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)

    editor.append_and_repoint(0, 0, _chapter_two_director(chapter.music))
    silent_update_pc = editor.append_and_repoint(
        0,
        1,
        _playable_silent_update(),
    )
    editor.append_and_repoint(
        CHAPTER_TWO_BEDROOM_RICO_ENTITY,
        0,
        _normalized_party_init(RICO_ID),
    )
    editor.append_and_repoint(
        CHAPTER_TWO_BEDROOM_RICO_ENTITY,
        1,
        b"\xA7\x00",
    )

    # Preserve only the real purple leaf's model initializer.  Its retail
    # action is rebuilt below with the current anthology field and state-copy
    # target; every other retail helper remains unreachable.
    editor.set_script_pointer(
        CHAPTER_TWO_BEDROOM_DOOR_ENTITY,
        0,
        CHAPTER_TWO_BEDROOM_DOOR_INIT_PC,
    )
    editor.set_script_pointer(
        CHAPTER_TWO_BEDROOM_DOOR_ENTITY,
        1,
        silent_update_pc,
    )
    editor.append_and_repoint(
        CHAPTER_TWO_BEDROOM_DOOR_ENTITY,
        2,
        _chapter_two_bedroom_return_action(main_field),
    )

    bed_x, bed_z, _bed_triangle = CHAPTER_TWO_BED_POSITION
    editor.append_and_repoint(
        CHAPTER_TWO_BED_CONTROLLER_ENTITY,
        0,
        _playable_controller_init(
            bed_x,
            bed_z,
            half_width=0x08,
            half_depth=0x08,
            requires_facing=False,
        ),
    )
    bed_action_pc = editor.bytecode_size
    editor.append_and_repoint(
        CHAPTER_TWO_BED_CONTROLLER_ENTITY,
        2,
        _build_chapter_two_bed_reflection_action(bed_action_pc),
    )
    for entity in range(4, editor.entity_count):
        editor.append_and_repoint(entity, 0, INERT_HIDDEN_INIT)

    components[SCRIPT_INDEX] = editor.to_bytes()
    changed = (
        SCRIPT_INDEX,
        mass_driver.ENCOUNTER_INDEX,
        DIALOGUE_INDEX,
    )
    bundle = build_field_preserving(
        donor_bundle,
        components,
        changed,
        compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if (
        tuple(part.data for part in reparsed.parts) != tuple(components)
        or len(reparsed.header) != len(header)
        or reparsed.header[0x18C:] != header[0x18C:]
    ):
        raise RicoArcBuildError(
            "Chapter 2 Champion bedroom failed packed round-trip"
        )
    return bundle


def _chapter_dialogue_texts(
    chapter: Chapter,
    refs: Iterable[DialogueRef],
) -> tuple[str, ...]:
    """Resolve authored/custom references into text for a second field."""

    resolved: list[str] = []
    for ref in refs:
        if isinstance(ref, int):
            if not 0 <= ref < len(chapter.blocks):
                raise RicoArcBuildError(
                    f"Chapter {chapter.chapter_id} dialogue reference {ref} "
                    "is outside its authored blocks"
                )
            text = chapter.blocks[ref]
        elif isinstance(ref, str):
            text = ref
        else:
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} has an invalid dialogue reference"
            )
        if text.lstrip().startswith("["):
            raise RicoArcBuildError(
                f"Chapter {chapter.chapter_id} live sequence routes screenplay prose"
            )
        resolved.append(text)
    return tuple(resolved)


def _chapter_one_firewood_rico_init() -> bytes:
    """Initialize only young Rico at the daylight Nortune threshold."""

    x, z, _triangle = CHAPTER_ONE_FIREWOOD_DOOR_POSITION
    return (
        b"\x0B"
        + _immediate(CHAPTER_ONE_FIREWOOD_BANK_INDEX)
        + b"\xFE\x0D"
        + _immediate(RICO_ID)
        + b"\x19"
        + _s16(x)
        + _s16(z)
        + b"\xC0\x1A\x00\x21"
        + _immediate(CHAPTER_ONE_FIREWOOD_RICO_TIMESCALE)
        + b"\x00"
    )


def _chapter_one_firewood_route_body(
    route: Sequence[tuple[int, int, int]],
) -> bytes:
    """Walk and exact-snap each finite exterior cinematic waypoint."""

    if not route:
        raise RicoArcBuildError("Chapter 1 firewood route is empty")
    body = bytearray()
    for x, z, _triangle in route:
        position = _s16(x) + _s16(z)
        body.extend(
            b"\x4B"
            + position
            + b"\xC0"
            + _immediate(CHAPTER_ONE_FIREWOOD_WAYPOINT_MAX_STEPS)
            + b"\x19"
            + position
            + b"\xC0"
        )
    body.append(0x00)
    return bytes(body)


def _chapter_one_firewood_camera(
    target: tuple[int, int, int],
    eye: tuple[int, int, int],
    *,
    transition_frames: int,
    enter_camera_mode: bool,
) -> bytes:
    """Compose one silent, fixed-camera exterior shot."""

    return mass_driver._historical_camera_shot_body(
        mass_driver.HistoricalCameraShot(
            target=target,
            eye=eye,
            transition_frames=transition_frames,
            dialogues=(),
        ),
        enter_camera_mode=enter_camera_mode,
        allow_silent=True,
    )


def _build_chapter_one_firewood_story(
    *,
    base_pc: int,
    firewood_dialogue_ids: Sequence[int] = (0,),
    aftermath_field: int = CHAPTER_ONE_AFTERMATH_FIELD,
) -> bytes:
    """Stage and narrate Rico gathering firewood in live Nortune geometry."""

    dialogue_ids = tuple(firewood_dialogue_ids)
    if not dialogue_ids:
        raise RicoArcBuildError("The live firewood scene needs narration")

    def run(script_index: int) -> bytes:
        if not 0 <= script_index < 32:
            raise RicoArcBuildError("Chapter 1 firewood script index is invalid")
        return b"\x09" + bytes(
            (
                CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
                script_index | 0x20,
            )
        )

    fade = mass_driver._facility_video_screen_fade_body
    routine = mass_driver._RoutineBuilder(base_pc)
    routine.emit(
        _actor_dialog_reset()
        + b"\x33\xFE\x54"
        + _chapter_one_firewood_camera(
            CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_TARGET,
            CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_EYE,
            transition_frames=0,
            enter_camera_mode=True,
        )
        + fade(0, CHAPTER_ONE_FIREWOOD_FIELD_FADE_FRAMES)
        + _wait(CHAPTER_ONE_FIREWOOD_ESTABLISH_HOLD_FRAMES)
        + run(CHAPTER_ONE_FIREWOOD_APPROACH_SCRIPT)
        + _chapter_one_firewood_camera(
            CHAPTER_ONE_FIREWOOD_WORK_CAMERA_TARGET,
            CHAPTER_ONE_FIREWOOD_WORK_CAMERA_EYE,
            transition_frames=CHAPTER_ONE_FIREWOOD_CAMERA_MOVE_FRAMES,
            enter_camera_mode=False,
        )
        + _wait(CHAPTER_ONE_FIREWOOD_WORK_SETTLE_FRAMES)
    )
    release_pc = routine.pc
    routine.emit(
        _wait_for_pad_release(PAD_MASK_CROSS, release_pc)
        + _wait()
        + _dialogue_sequence(dialogue_ids)
        + _actor_dialog_reset()
        + _wait(CHAPTER_ONE_FIREWOOD_GATHER_PAUSE_FRAMES)
        # Young Rico has only native idle and walk programs.  Hide the actual
        # pickup through a short cinematic cut instead of calling a missing
        # crouch/carry animation that could leave him running in place.
        + fade(0xFF, CHAPTER_ONE_FIREWOOD_PICKUP_FADE_FRAMES)
        + _chapter_one_firewood_camera(
            CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_TARGET,
            CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_EYE,
            transition_frames=0,
            enter_camera_mode=False,
        )
        + _wait(CHAPTER_ONE_FIREWOOD_PICKUP_BLACK_HOLD_FRAMES)
        + fade(0, CHAPTER_ONE_FIREWOOD_PICKUP_FADE_FRAMES)
        + run(CHAPTER_ONE_FIREWOOD_RETURN_SCRIPT)
        + _wait(CHAPTER_ONE_FIREWOOD_RETURN_SETTLE_FRAMES)
        + fade(0xFF, CHAPTER_ONE_FIREWOOD_FIELD_FADE_FRAMES)
        + _change_field(aftermath_field, 0)
        + b"\x5B"
    )
    return routine.finish()


def _validate_chapter_one_firewood_source(
    donor_bundle: bytes,
    young_rico_source_bundle: bytes,
) -> tuple[list[bytes], bytes]:
    """Pin the daylight donor, visible props, path, and young-Rico assets."""

    if (
        len(donor_bundle) != CHAPTER_ONE_FIREWOOD_DONOR_BUNDLE_SIZE
        or _sha256_bytes(donor_bundle)
        != CHAPTER_ONE_FIREWOOD_DONOR_BUNDLE_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 firewood field donor changed")
    donor = parse_field(donor_bundle)
    components = [part.data for part in donor.parts]
    if (
        len(donor.header) != CHAPTER_ONE_FIREWOOD_DONOR_HEADER_SIZE
        or _sha256_bytes(donor.header)
        != CHAPTER_ONE_FIREWOOD_DONOR_HEADER_SHA256
        or len(components[1]) != CHAPTER_ONE_FIREWOOD_DONOR_WALKMESH_SIZE
        or _sha256_bytes(components[1])
        != CHAPTER_ONE_FIREWOOD_DONOR_WALKMESH_SHA256
        or len(components[mass_driver.MODEL_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_MODELS_SIZE
        or _sha256_bytes(components[mass_driver.MODEL_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_MODELS_SHA256
        or len(components[mass_driver.ACTOR_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_COMPONENT_SIZE
        or _sha256_bytes(components[mass_driver.ACTOR_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_COMPONENT_SHA256
        or len(components[mass_driver.SPRITE_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_COMPONENT_SIZE
        or _sha256_bytes(components[mass_driver.SPRITE_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_COMPONENT_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 firewood donor components changed")

    editor = AtelScript(components[SCRIPT_INDEX])
    init_pc = editor.get_script_pointer(0, 0)
    if (
        editor.entity_count != CHAPTER_ONE_FIREWOOD_DONOR_ENTITY_COUNT
        or init_pc != CHAPTER_ONE_FIREWOOD_DONOR_DIRECTOR_INIT_PC
        or editor.bytecode[
            init_pc : init_pc + len(CHAPTER_ONE_FIREWOOD_DONOR_DIRECTOR_INIT_BODY)
        ]
        != CHAPTER_ONE_FIREWOOD_DONOR_DIRECTOR_INIT_BODY
    ):
        raise RicoArcBuildError("Chapter 1 firewood donor director changed")

    crate_record_at = 0x190 + CHAPTER_ONE_FIREWOOD_CRATE_NODE * 16
    if (
        donor.header[
            crate_record_at : crate_record_at + 16
        ]
        != CHAPTER_ONE_FIREWOOD_CRATE_HEADER_RECORD
    ):
        raise RicoArcBuildError("Chapter 1 wooden-crate node changed")
    door_record_at = 0x190 + CHAPTER_ONE_FIREWOOD_DOOR_NODE * 16
    if (
        donor.header[door_record_at : door_record_at + 16]
        != CHAPTER_ONE_FIREWOOD_DOOR_HEADER_RECORD
    ):
        raise RicoArcBuildError("Chapter 1 Nortune facade node changed")
    models = mass_driver._indexed_bundle_entries(
        components[mass_driver.MODEL_INDEX]
    )
    for role, index, expected_size, expected_hash in (
        (
            "wooden packing crate",
            CHAPTER_ONE_FIREWOOD_CRATE_MODEL_INDEX,
            CHAPTER_ONE_FIREWOOD_CRATE_MODEL_SIZE,
            CHAPTER_ONE_FIREWOOD_CRATE_MODEL_SHA256,
        ),
        (
            "Nortune house door",
            CHAPTER_ONE_FIREWOOD_DOOR_MODEL_INDEX,
            CHAPTER_ONE_FIREWOOD_DOOR_MODEL_SIZE,
            CHAPTER_ONE_FIREWOOD_DOOR_MODEL_SHA256,
        ),
    ):
        if (
            index >= len(models)
            or len(models[index]) != expected_size
            or _sha256_bytes(models[index]) != expected_hash
        ):
            raise RicoArcBuildError(f"Chapter 1 firewood {role} changed")

    triangles = _walkmesh_layer(components[1], 0)
    points = (
        ("Nortune doorway", CHAPTER_ONE_FIREWOOD_DOOR_POSITION),
        *(
            (f"route waypoint {index}", point)
            for index, point in enumerate(
                CHAPTER_ONE_FIREWOOD_MID_ROUTE,
                start=1,
            )
        ),
        ("wood-gathering stance", CHAPTER_ONE_FIREWOOD_WORK_POSITION),
    )
    for role, (x, z, triangle) in points:
        if (
            not 0 <= triangle < len(triangles)
            or not _point_inside_triangle((x, z), triangles[triangle])
        ):
            raise RicoArcBuildError(
                f"Chapter 1 firewood {role} left its audited walkmesh triangle"
            )
    route = (
        CHAPTER_ONE_FIREWOOD_DOOR_POSITION,
        *CHAPTER_ONE_FIREWOOD_MID_ROUTE,
        CHAPTER_ONE_FIREWOOD_WORK_POSITION,
    )
    for left, right in zip(route, route[1:]):
        if (
            not _chapter_four_segment_on_walkmesh(
                left[:2], right[:2], triangles
            )
            or not _chapter_four_segment_on_walkmesh(
                right[:2], left[:2], triangles
            )
        ):
            raise RicoArcBuildError(
                "Chapter 1 firewood route leaves the walkmesh"
            )

    donor_actor_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.ACTOR_INDEX]
    )
    donor_sprite_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.SPRITE_INDEX]
    )
    if (
        len(donor_actor_banks) != 3
        or len(donor_sprite_banks) != 3
        or len(donor_actor_banks[CHAPTER_ONE_FIREWOOD_BANK_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_BANK_SIZE
        or _sha256_bytes(donor_actor_banks[CHAPTER_ONE_FIREWOOD_BANK_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_BANK_SHA256
        or len(donor_sprite_banks[CHAPTER_ONE_FIREWOOD_BANK_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_BANK_SIZE
        or _sha256_bytes(donor_sprite_banks[CHAPTER_ONE_FIREWOOD_BANK_INDEX])
        != CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_BANK_SHA256
        or struct.unpack_from(
            "<4H",
            donor.header,
            CHAPTER_ONE_FIREWOOD_BANK_INDEX * 8,
        )
        != CHAPTER_ONE_FIREWOOD_BANK_VRAM_MAPPING
    ):
        raise RicoArcBuildError("Chapter 1 firewood donor bank layout changed")

    young_rico_source = parse_field(young_rico_source_bundle)
    source_components = [part.data for part in young_rico_source.parts]
    if (
        len(source_components[mass_driver.ACTOR_INDEX]) != 4_184
        or _sha256_bytes(source_components[mass_driver.ACTOR_INDEX])
        != YOUNG_RICO_ACTOR_COMPONENT_SHA256
        or len(source_components[mass_driver.SPRITE_INDEX])
        != YOUNG_RICO_SPRITE_COMPONENT_SIZE
        or _sha256_bytes(source_components[mass_driver.SPRITE_INDEX])
        != YOUNG_RICO_SPRITE_COMPONENT_SHA256
        or struct.unpack_from(
            "<4H",
            young_rico_source.header,
            CHAPTER_ONE_FIREWOOD_BANK_INDEX * 8,
        )
        != CHAPTER_ONE_FIREWOOD_BANK_VRAM_MAPPING
    ):
        raise RicoArcBuildError("Chapter 1 young-Rico source assets changed")
    source_actor_banks = mass_driver._indexed_bundle_entries(
        source_components[mass_driver.ACTOR_INDEX]
    )
    source_sprite_banks = mass_driver._indexed_bundle_entries(
        source_components[mass_driver.SPRITE_INDEX]
    )
    if (
        len(source_actor_banks) != 2
        or len(source_sprite_banks) != 2
        or len(source_actor_banks[CHAPTER_ONE_FIREWOOD_BANK_INDEX])
        != 1_464
        or _sha256_bytes(source_actor_banks[CHAPTER_ONE_FIREWOOD_BANK_INDEX])
        != YOUNG_RICO_ACTOR_BANK_SHA256
        or len(source_sprite_banks[CHAPTER_ONE_FIREWOOD_BANK_INDEX])
        != YOUNG_RICO_SPRITE_BANK_SIZE
        or _sha256_bytes(source_sprite_banks[CHAPTER_ONE_FIREWOOD_BANK_INDEX])
        != YOUNG_RICO_SPRITE_BANK_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 young-Rico bank identity changed")
    return components, donor.header


def _build_chapter_one_firewood_bundle(
    donor_bundle: bytes,
    young_rico_source_bundle: bytes,
    chapter: Chapter,
    *,
    aftermath_field: int = CHAPTER_ONE_AFTERMATH_FIELD,
) -> bytes:
    """Clone field 199 as a sanitized automatic Nortune firewood scene."""

    if chapter.chapter_id != 1:
        raise RicoArcBuildError("The firewood presentation requires Chapter 1")
    contract = _playable_chapter_contract(1)
    transition = contract.exit_transition
    if transition is None or not transition.firewood_dialogue:
        raise RicoArcBuildError("Chapter 1 lost its live firewood narration")
    firewood_dialogue = _chapter_dialogue_texts(
        chapter,
        transition.firewood_dialogue,
    )
    components, header = _validate_chapter_one_firewood_source(
        donor_bundle,
        young_rico_source_bundle,
    )
    source_components = [
        part.data for part in parse_field(young_rico_source_bundle).parts
    ]
    source_actor = mass_driver._indexed_bundle_entries(
        source_components[mass_driver.ACTOR_INDEX]
    )[CHAPTER_ONE_FIREWOOD_BANK_INDEX]
    source_sprite = mass_driver._indexed_bundle_entries(
        source_components[mass_driver.SPRITE_INDEX]
    )[CHAPTER_ONE_FIREWOOD_BANK_INDEX]
    components[mass_driver.ACTOR_INDEX] = (
        mass_driver._replace_indexed_bundle_entry(
            components[mass_driver.ACTOR_INDEX],
            CHAPTER_ONE_FIREWOOD_BANK_INDEX,
            source_actor,
            CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_BANK_SHA256,
        )
    )
    components[mass_driver.SPRITE_INDEX] = (
        mass_driver._replace_indexed_bundle_entry(
            components[mass_driver.SPRITE_INDEX],
            CHAPTER_ONE_FIREWOOD_BANK_INDEX,
            source_sprite,
            CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_BANK_SHA256,
        )
    )

    # The donor's standard encounter table carries three nonzero weights even
    # though retail reaches this version only as a cutscene.  Zero them so
    # Rico's scripted steps can never dispatch a battle.
    encounter = bytearray(components[mass_driver.ENCOUNTER_INDEX])
    if len(encounter) != ENCOUNTER_COMPONENT_SIZE:
        raise RicoArcBuildError("Chapter 1 firewood encounter table changed")
    encounter[WEIGHTS_OFFSET : WEIGHTS_OFFSET + FORMATION_COUNT] = bytes(
        FORMATION_COUNT
    )
    components[mass_driver.ENCOUNTER_INDEX] = bytes(encounter)

    editor = AtelScript(components[SCRIPT_INDEX])
    stop_pc = editor.append_raw_routine(b"\x00")
    for entity in range(editor.entity_count):
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)
    for entity in range(2, editor.entity_count):
        editor.append_and_repoint(entity, 0, INERT_HIDDEN_INIT)

    editor.append_and_repoint(
        CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
        0,
        _chapter_one_firewood_rico_init(),
    )
    editor.append_and_repoint(
        CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
        CHAPTER_ONE_FIREWOOD_APPROACH_SCRIPT,
        _chapter_one_firewood_route_body(
            (
                *CHAPTER_ONE_FIREWOOD_MID_ROUTE,
                CHAPTER_ONE_FIREWOOD_WORK_POSITION,
            )
        ),
    )
    editor.append_and_repoint(
        CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
        CHAPTER_ONE_FIREWOOD_RETURN_SCRIPT,
        _chapter_one_firewood_route_body(
            (
                *reversed(CHAPTER_ONE_FIREWOOD_MID_ROUTE),
                CHAPTER_ONE_FIREWOOD_DOOR_POSITION,
            )
        ),
    )

    director = (
        INERT_HIDDEN_INIT[:-1]
        + _play_music(chapter.music)
        + mass_driver._facility_video_screen_fade_body(0xFF, 1)
        + b"\x00"
    )
    editor.append_and_repoint(0, 0, director)
    story_pc = editor.bytecode_size
    editor.append_and_repoint(
        0,
        1,
        _build_chapter_one_firewood_story(
            base_pc=story_pc,
            firewood_dialogue_ids=range(len(firewood_dialogue)),
            aftermath_field=aftermath_field,
        ),
    )
    components[SCRIPT_INDEX] = editor.to_bytes()
    components[DIALOGUE_INDEX] = _dialogue_data(
        firewood_dialogue,
        fit_windows=True,
        sentence_safe_pages=True,
    )

    changed = (
        mass_driver.ACTOR_INDEX,
        mass_driver.SPRITE_INDEX,
        mass_driver.ENCOUNTER_INDEX,
        SCRIPT_INDEX,
        DIALOGUE_INDEX,
    )
    bundle = build_field_preserving(
        donor_bundle,
        components,
        changed,
        compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if (
        tuple(part.data for part in reparsed.parts) != tuple(components)
        or len(reparsed.header) != len(header)
        or reparsed.header[0x18C:] != header[0x18C:]
        or struct.unpack_from(
            "<4H",
            reparsed.header,
            CHAPTER_ONE_FIREWOOD_BANK_INDEX * 8,
        )
        != CHAPTER_ONE_FIREWOOD_BANK_VRAM_MAPPING
    ):
        raise RicoArcBuildError(
            "Chapter 1 firewood field failed packed round-trip"
        )
    return bundle


def _chapter_one_aftermath_call(
    entity: int,
    script_index: int,
    *,
    asynchronous: bool = False,
) -> bytes:
    """Call one sanitized aftermath helper in blocking or parallel form."""

    if not 0 <= entity <= 0xFF or not 0 <= script_index < 32:
        raise RicoArcBuildError("Chapter 1 aftermath helper call is invalid")
    return bytes(
        (
            0x07 if asynchronous else 0x09,
            entity,
            script_index | 0x20,
        )
    )


def _chapter_one_aftermath_camera(preset: int) -> bytes:
    """Select one authored field-229 camera rotation."""

    if preset not in (2, 4, 5):
        raise RicoArcBuildError("Chapter 1 aftermath camera preset is invalid")
    return b"\xB5" + _immediate(preset) + _immediate(1)


def _chapter_one_aftermath_anchor_init() -> bytes:
    """Create the invisible young-Rico camera anchor without requiring Fei."""

    return (
        b"\x16"
        + _immediate(YOUNG_RICO_ID)
        + b"\xFE\x0D"
        + _immediate(YOUNG_RICO_ID)
        + b"\x20\x0D\x80\x23\x00"
    )


def _chapter_one_aftermath_anna_init() -> bytes:
    """Stage Anne at the stove before the return-home shot becomes visible."""

    x, z, _triangle = CHAPTER_ONE_AFTERMATH_ANNA_SICKROOM_POSITION
    return (
        b"\x0B"
        + _immediate(0)
        + b"\x19"
        + _s16(x)
        + _s16(z)
        + b"\xC0\x5F\x03\x2A\x00"
    )
def _chapter_one_aftermath_entry_body() -> bytes:
    """Walk Rico finitely through the real bedroom door and exact-snap."""

    x, z, _triangle = CHAPTER_ONE_AFTERMATH_ENTRY_POSITION
    position = _s16(x) + _s16(z)
    return (
        b"\x4B"
        + position
        + b"\xC0"
        + _immediate(CHAPTER_ONE_AFTERMATH_ENTRY_MAX_STEPS)
        + b"\x19"
        + position
        + b"\xC0\x00"
    )


def _chapter_one_aftermath_grade_body(
    rgb: tuple[int, int, int],
    *,
    frames: int,
) -> bytes:
    """Transition persistent RGB-fader slot 1 to one checked grade."""

    if len(rgb) != 3 or any(not 0 <= channel <= 0xFF for channel in rgb):
        raise RicoArcBuildError("Chapter 1 aftermath RGB grade is invalid")
    if not 1 <= frames <= 0x7FFF:
        raise RicoArcBuildError("Chapter 1 aftermath grade duration is invalid")
    red, green, blue = rgb
    return (
        b"\xF1"
        + _immediate(CHAPTER_ONE_AFTERMATH_NIGHT_GRADE_MODE)
        + _immediate(red)
        + _immediate(green)
        + _immediate(blue)
        + _immediate(frames)
    )


def _chapter_one_aftermath_night_grade_body(
    *,
    frames: int = CHAPTER_ONE_AFTERMATH_NIGHT_GRADE_FRAMES,
) -> bytes:
    """Apply the cool moonlight grade in persistent RGB-fader slot 1."""

    return _chapter_one_aftermath_grade_body(
        CHAPTER_ONE_AFTERMATH_NIGHT_GRADE_RGB,
        frames=frames,
    )


def _chapter_one_aftermath_daylight_grade_body(
    *,
    frames: int = 1,
) -> bytes:
    """Restore the room's neutral daylight colors in persistent slot 1."""

    return _chapter_one_aftermath_grade_body(
        CHAPTER_ONE_AFTERMATH_DAYLIGHT_GRADE_RGB,
        frames=frames,
    )


def _chapter_one_aftermath_blackout_handoff_body() -> bytes:
    """Move death-scene black behind dialogue, then clear front fader slot 0."""

    return (
        _chapter_one_aftermath_grade_body(
            CHAPTER_ONE_AFTERMATH_BLACKOUT_RGB,
            frames=1,
        )
        + _wait()
        + _chapter_one_aftermath_scene_fade_body(reveal=True)
    )


def _chapter_one_aftermath_daylight_restore_body() -> bytes:
    """Reveal the morning empty-bed shot in neutral daylight behind UI."""

    return (
        _chapter_one_aftermath_daylight_grade_body(
            frames=CHAPTER_ONE_AFTERMATH_FADE_FRAMES,
        )
        + _wait(CHAPTER_ONE_AFTERMATH_FADE_FRAMES)
    )


def _chapter_one_aftermath_scene_fade_body(*, reveal: bool) -> bytes:
    """Fade slot 0 without overwriting the persistent slot-1 night grade."""

    opcode = b"\xB3" if reveal else b"\xB4"
    return (
        opcode
        + _immediate(CHAPTER_ONE_AFTERMATH_FADE_FRAMES)
        + _wait(CHAPTER_ONE_AFTERMATH_FADE_FRAMES)
    )


def _build_chapter_one_aftermath_story(
    *,
    base_pc: int,
    sickness_ids: Sequence[int],
    loss_ids: Sequence[int],
    funeral_field: int = CHAPTER_ONE_FUNERAL_FIELD,
) -> bytes:
    """Return home, stage Anne's death, and reveal the live empty room."""

    sickness = tuple(sickness_ids)
    loss = tuple(loss_ids)
    if len(sickness) != 6 or len(loss) != 4:
        raise RicoArcBuildError("Chapter 1 aftermath dialogue layout changed")

    fade_in = _chapter_one_aftermath_scene_fade_body(reveal=True)
    fade_out = _chapter_one_aftermath_scene_fade_body(reveal=False)
    death_blackout_handoff = _chapter_one_aftermath_blackout_handoff_body()
    daylight_restore = _chapter_one_aftermath_daylight_restore_body()
    call = _chapter_one_aftermath_call
    routine = mass_driver._RoutineBuilder(base_pc)
    routine.emit(
        _actor_dialog_reset()
        + b"\x33\xFE\x54"
        # Retail field-229 screen geometry. Rico's entry and Anne's first cough
        # remain in daylight; the nighttime grade begins only under the first
        # scene-ending blackout below.
        + bytes.fromhex("A0 00 80 1E 80 00 82")
        + _chapter_one_aftermath_daylight_grade_body()
        + fade_in
        + _wait(12)
        + call(
            CHAPTER_ONE_AFTERMATH_DOOR_ENTITY,
            CHAPTER_ONE_DOOR_OPEN_SCRIPT,
        )
        + call(
            CHAPTER_ONE_AFTERMATH_RICO_ENTITY,
            CHAPTER_ONE_AFTERMATH_ENTRY_SCRIPT,
        )
        # The visual close runs in parallel and receives a fixed hold; it can
        # never strand the story on a cosmetic completion callback.
        + call(
            CHAPTER_ONE_AFTERMATH_DOOR_ENTITY,
            5,
            asynchronous=True,
        )
        + _wait(20)
        # Hold the return-home shot long enough for Anne's complete native
        # cough cycle before cutting to the closer sickbed composition.
        + call(
            CHAPTER_ONE_ANNA_ENTITY,
            CHAPTER_ONE_AFTERMATH_COUGH_SCRIPT,
        )
        + _wait(8)
        + fade_out
        + _chapter_one_aftermath_night_grade_body()
        # Sickroom: exact retail camera-anchor and actor staging.
        + _chapter_one_aftermath_camera(2)
        + call(1, 4, asynchronous=True)
        + call(CHAPTER_ONE_ANNA_ENTITY, 5, asynchronous=True)
        + call(CHAPTER_ONE_AFTERMATH_RICO_ENTITY, 6)
        + fade_in
    )
    release_pc = routine.pc
    routine.emit(
        _wait_for_pad_release(PAD_MASK_CROSS, release_pc)
        + _wait()
        + _dialogue_sequence(sickness[:2])
        + call(
            CHAPTER_ONE_ANNA_ENTITY,
            CHAPTER_ONE_AFTERMATH_COUGH_SCRIPT,
        )
        + _wait(8)
        + _dialogue_sequence(sickness[2:])
        + _actor_dialog_reset()
    )
    release_pc = routine.pc
    routine.emit(
        # Anne's death is a time cut under black, not an unsupported sprite
        # pose.  The next reveal uses the retail empty-bed composition.
        # Drain the closing Cross press while the sickroom is still visible;
        # no input-dependent loop should ever begin behind a black screen.
        _wait_for_pad_release(PAD_MASK_CROSS, release_pc)
        + _wait()
        + _wait(20)
        + fade_out
        # Slot 0 renders in front of field dialogue.  Hand its blackout to
        # slot 1 and clear slot 0 before opening the death narration, matching
        # retail field 591's text-over-black layering.
        + death_blackout_handoff
        + b"\x33"
        + _dialogue_sequence(loss[:1])
        + _actor_dialog_reset()
        + _chapter_one_aftermath_camera(4)
        + call(1, 7, asynchronous=True)
        + call(CHAPTER_ONE_ANNA_ENTITY, 8, asynchronous=True)
        + call(CHAPTER_ONE_AFTERMATH_RICO_ENTITY, 9)
        # Morning has arrived. Restore the neutral daylight grade for both the
        # empty-bed vigil and the following Stonebell composition.
        + daylight_restore
    )
    release_pc = routine.pc
    routine.emit(
        _wait_for_pad_release(PAD_MASK_CROSS, release_pc)
        + _wait()
        + _dialogue_sequence(loss[1:3])
        + _actor_dialog_reset()
        + _wait(20)
        + fade_out
        # The final live shot turns from the empty bed toward the watered
        # stonebell, using the room's native west-side camera anchor.
        + _chapter_one_aftermath_camera(5)
        + call(1, 6, asynchronous=True)
        + b"\x25"
        + bytes((CHAPTER_ONE_AFTERMATH_RICO_ENTITY,))
        + fade_in
    )
    release_pc = routine.pc
    routine.emit(
        _wait_for_pad_release(PAD_MASK_CROSS, release_pc)
        + _wait()
        + _dialogue_sequence(loss[3:])
        + _actor_dialog_reset()
        + _wait(20)
        + fade_out
        + _change_field(funeral_field, 0)
        + b"\x5B"
    )
    return routine.finish()


def _build_chapter_one_aftermath_bundle(
    donor_bundle: bytes,
    chapter: Chapter,
    *,
    funeral_field: int = CHAPTER_ONE_FUNERAL_FIELD,
) -> bytes:
    """Clone field 229 into a fully live sickness and mourning sequence."""

    if (
        len(donor_bundle) != CHAPTER_ONE_AFTERMATH_DONOR_BUNDLE_SIZE
        or _sha256_bytes(donor_bundle)
        != CHAPTER_ONE_AFTERMATH_DONOR_BUNDLE_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 aftermath donor changed")
    if chapter.chapter_id != 1:
        raise RicoArcBuildError("The live aftermath requires Chapter 1")
    contract = _playable_chapter_contract(1)
    transition = contract.exit_transition
    if transition is None:
        raise RicoArcBuildError("Chapter 1 lost its aftermath transition")

    sickness = _chapter_dialogue_texts(
        chapter,
        transition.sickness_dialogue,
    )
    loss = _chapter_dialogue_texts(chapter, transition.loss_dialogue)
    if len(sickness) != 6 or len(loss) != 4:
        raise RicoArcBuildError("Chapter 1 aftermath text changed")
    dialogue_blocks = (*sickness, *loss)
    sickness_ids = tuple(range(len(sickness)))
    loss_ids = tuple(range(len(sickness), len(dialogue_blocks)))

    parsed = parse_field(donor_bundle)
    components = [part.data for part in parsed.parts]
    editor = AtelScript(components[SCRIPT_INDEX])
    if (
        len(parsed.header) != CHAPTER_ONE_AFTERMATH_HEADER_SIZE
        or _sha256_bytes(parsed.header)
        != CHAPTER_ONE_AFTERMATH_HEADER_SHA256
        or editor.entity_count != CHAPTER_ONE_AFTERMATH_ENTITY_COUNT
    ):
        raise RicoArcBuildError("Chapter 1 aftermath field layout changed")
    _validate_chapter_one_anna_source(parsed.header, components)
    _validate_chapter_one_door_source(components)
    triangles = _walkmesh_layer(components[1], 0)
    for role, (x, z, triangle) in (
        ("door start", CHAPTER_ONE_AFTERMATH_DOOR_START_POSITION),
        ("interior endpoint", CHAPTER_ONE_AFTERMATH_ENTRY_POSITION),
        (
            "Anne sickroom staging",
            CHAPTER_ONE_AFTERMATH_ANNA_SICKROOM_POSITION,
        ),
    ):
        if (
            not 0 <= triangle < len(triangles)
            or not _point_inside_triangle((x, z), triangles[triangle])
        ):
            raise RicoArcBuildError(
                f"Chapter 1 aftermath {role} left its walkmesh triangle"
            )
    anna_triangle = CHAPTER_ONE_AFTERMATH_ANNA_SICKROOM_POSITION[2]
    if {vertex[1] for vertex in triangles[anna_triangle]} != {0}:
        raise RicoArcBuildError(
            "Chapter 1 Anne sickroom staging left its flat floor"
        )
    if not _chapter_four_segment_on_walkmesh(
        CHAPTER_ONE_AFTERMATH_DOOR_START_POSITION[:2],
        CHAPTER_ONE_AFTERMATH_ENTRY_POSITION[:2],
        triangles,
    ):
        raise RicoArcBuildError("Chapter 1 aftermath entry route is obstructed")
    for (entity, script_index), (pc, body) in (
        CHAPTER_ONE_AFTERMATH_NATIVE_HELPERS.items()
    ):
        if (
            editor.get_script_pointer(entity, script_index) != pc
            or editor.bytecode[pc : pc + len(body)] != body
        ):
            raise RicoArcBuildError(
                "Chapter 1 native aftermath staging helper changed"
            )
    anna_x, anna_z, _anna_triangle = (
        CHAPTER_ONE_AFTERMATH_ANNA_SICKROOM_POSITION
    )
    anna_position = b"\x19" + _s16(anna_x) + _s16(anna_z) + b"\xC0"
    if not CHAPTER_ONE_AFTERMATH_NATIVE_HELPERS[
        (CHAPTER_ONE_ANNA_ENTITY, 5)
    ][1].startswith(anna_position):
        raise RicoArcBuildError(
            "Chapter 1 Anne sickroom initializer left its native staging helper"
        )
    if editor.get_script_pointer(6, 5) != CHAPTER_ONE_AFTERMATH_DOOR_CLOSE_PC:
        raise RicoArcBuildError("Chapter 1 native door-close helper changed")
    if (
        editor.get_script_pointer(CHAPTER_ONE_AFTERMATH_RICO_ENTITY, 0)
        != CHAPTER_ONE_AFTERMATH_RICO_INIT_PC
        or editor.bytecode[
            CHAPTER_ONE_AFTERMATH_RICO_INIT_PC :
            CHAPTER_ONE_AFTERMATH_RICO_INIT_PC
            + len(CHAPTER_ONE_AFTERMATH_RICO_INIT_BODY)
        ]
        != CHAPTER_ONE_AFTERMATH_RICO_INIT_BODY
    ):
        raise RicoArcBuildError("Chapter 1 young-Rico aftermath actor changed")

    encounter = bytearray(components[mass_driver.ENCOUNTER_INDEX])
    if len(encounter) != ENCOUNTER_COMPONENT_SIZE:
        raise RicoArcBuildError("Chapter 1 aftermath encounter table changed")
    encounter[WEIGHTS_OFFSET : WEIGHTS_OFFSET + FORMATION_COUNT] = bytes(
        FORMATION_COUNT
    )
    components[mass_driver.ENCOUNTER_INDEX] = bytes(encounter)

    stop_pc = editor.append_raw_routine(b"\x00")
    for entity in range(editor.entity_count):
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)
    for entity in (2, 3):
        editor.append_and_repoint(entity, 0, INERT_HIDDEN_INIT)

    # Restore only the exact native staging pieces named above.
    for (entity, script_index), (pc, _body) in (
        CHAPTER_ONE_AFTERMATH_NATIVE_HELPERS.items()
    ):
        editor.set_script_pointer(entity, script_index, pc)
    # The source counter pose is visible in our live door-entry shot.  Begin
    # Anne at the same stove-side point used by the subsequent sickroom helper
    # so that helper becomes an invisible, idempotent endpoint lock.
    editor.append_and_repoint(
        CHAPTER_ONE_ANNA_ENTITY,
        0,
        _chapter_one_aftermath_anna_init(),
    )
    editor.set_script_pointer(
        CHAPTER_ONE_AFTERMATH_RICO_ENTITY,
        0,
        CHAPTER_ONE_AFTERMATH_RICO_INIT_PC,
    )
    editor.set_script_pointer(
        CHAPTER_ONE_AFTERMATH_DOOR_ENTITY,
        5,
        CHAPTER_ONE_AFTERMATH_DOOR_CLOSE_PC,
    )
    editor.append_and_repoint(
        CHAPTER_ONE_AFTERMATH_CAMERA_ENTITY,
        0,
        _chapter_one_aftermath_anchor_init(),
    )
    editor.append_and_repoint(
        CHAPTER_ONE_AFTERMATH_CAMERA_ENTITY,
        1,
        b"\xA7\x00",
    )
    editor.append_and_repoint(
        CHAPTER_ONE_AFTERMATH_RICO_ENTITY,
        CHAPTER_ONE_AFTERMATH_ENTRY_SCRIPT,
        _chapter_one_aftermath_entry_body(),
    )
    editor.append_and_repoint(
        CHAPTER_ONE_ANNA_ENTITY,
        CHAPTER_ONE_AFTERMATH_COUGH_SCRIPT,
        CHAPTER_ONE_ANNA_COUGH_ONCE + b"\x00",
    )
    editor.append_and_repoint(
        0,
        0,
        INERT_HIDDEN_INIT[:-1]
        + _play_music(chapter.music)
        + mass_driver._facility_video_screen_fade_body(0xFF, 1)
        + b"\x00",
    )
    story_pc = editor.bytecode_size
    editor.append_and_repoint(
        0,
        1,
        _build_chapter_one_aftermath_story(
            base_pc=story_pc,
            sickness_ids=sickness_ids,
            loss_ids=loss_ids,
            funeral_field=funeral_field,
        ),
    )
    components[SCRIPT_INDEX] = editor.to_bytes()
    components[DIALOGUE_INDEX] = _dialogue_data(
        dialogue_blocks,
        fit_windows=True,
        sentence_safe_pages=True,
    )

    changed = (
        mass_driver.ENCOUNTER_INDEX,
        SCRIPT_INDEX,
        DIALOGUE_INDEX,
    )
    bundle = build_field_preserving(
        donor_bundle,
        components,
        changed,
        compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if (
        tuple(part.data for part in reparsed.parts) != tuple(components)
        or len(reparsed.header) != len(parsed.header)
        or reparsed.header[0x18C:] != parsed.header[0x18C:]
    ):
        raise RicoArcBuildError(
            "Chapter 1 aftermath field failed packed round-trip"
        )
    return bundle


def _chapter_one_live_funeral_actor_init(
    bank: int,
    position: tuple[int, int, int],
    direction: int,
) -> bytes:
    """Initialize one visible, stationary participant at Anne's grave."""

    x, z, _triangle = position
    body = bytearray(b"\x0B" + _immediate(bank))
    body.extend(
        b"\x19"
        + _s16(x)
        + _s16(z)
        + b"\xC0\x1A\x00\x5F"
        + bytes((direction,))
        + b"\x00"
    )
    return bytes(body)


def _chapter_one_live_funeral_priest_approach() -> bytes:
    """Walk the priest finitely close enough to give Rico a final blessing."""

    x, z, _triangle = CHAPTER_ONE_LIVE_FUNERAL_PRIEST_BLESSING_POSITION
    position = _s16(x) + _s16(z)
    return (
        b"\x4B"
        + position
        + b"\xC0"
        + _immediate(CHAPTER_ONE_LIVE_FUNERAL_WAYPOINT_MAX_STEPS)
        + b"\x19"
        + position
        + b"\xC0\x5F"
        + bytes((CHAPTER_ONE_LIVE_FUNERAL_PRIEST_BLESSING_DIRECTION,))
        + b"\x00"
    )


def _chapter_one_live_funeral_camera(
    target: tuple[int, int, int],
    eye: tuple[int, int, int],
    *,
    transition_frames: int,
    enter_camera_mode: bool,
) -> bytes:
    """Compose one occlusion-checked fixed shot of the live funeral."""

    return mass_driver._historical_camera_shot_body(
        mass_driver.HistoricalCameraShot(
            target=target,
            eye=eye,
            transition_frames=transition_frames,
            dialogues=(),
        ),
        enter_camera_mode=enter_camera_mode,
        allow_silent=True,
    )


def _build_chapter_one_live_funeral_story(
    *,
    base_pc: int,
    transition: PlayableExitTransition,
    funeral_ids: Sequence[int],
    epilogue_ids: Sequence[int],
) -> bytes:
    """Stage Anne's burial once, regardless of stale completion state."""

    funeral = tuple(funeral_ids)
    epilogue = tuple(epilogue_ids)
    if len(funeral) != 4 or len(epilogue) != 1:
        raise RicoArcBuildError("Chapter 1 live funeral dialogue layout changed")

    fade = mass_driver._facility_video_screen_fade_body
    routine = mass_driver._RoutineBuilder(base_pc)
    routine.emit(
        _actor_dialog_reset()
        + b"\x33\xFE\x54"
        + _chapter_one_live_funeral_camera(
            CHAPTER_ONE_LIVE_FUNERAL_CAMERA_TARGET,
            CHAPTER_ONE_LIVE_FUNERAL_CAMERA_EYE,
            transition_frames=0,
            enter_camera_mode=True,
        )
        + fade(0, CHAPTER_ONE_LIVE_FUNERAL_FADE_FRAMES)
        + _wait(CHAPTER_ONE_LIVE_FUNERAL_ESTABLISH_HOLD_FRAMES)
    )
    release_pc = routine.pc
    routine.emit(
        _wait_for_pad_release(PAD_MASK_CROSS, release_pc)
        + _wait()
        # The first page establishes the grave; the hooded Eton then gives
        # Anne's eulogy while both actors and the marker remain plainly visible.
        + _dialogue_sequence(
            funeral[:2],
            flags=CHAPTER_ONE_LIVE_FUNERAL_HIDDEN_DIALOGUE_FLAGS,
        )
        + _actor_dialog_reset()
        + _chapter_one_aftermath_call(
            CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ENTITY,
            CHAPTER_ONE_LIVE_FUNERAL_PRIEST_APPROACH_SCRIPT,
        )
        + _chapter_one_live_funeral_camera(
            CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_TARGET,
            CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_EYE,
            transition_frames=CHAPTER_ONE_LIVE_FUNERAL_CAMERA_MOVE_FRAMES,
            enter_camera_mode=False,
        )
        + _wait(CHAPTER_ONE_LIVE_FUNERAL_BLESSING_SETTLE_FRAMES)
    )
    release_pc = routine.pc
    routine.emit(
        _wait_for_pad_release(PAD_MASK_CROSS, release_pc)
        + _wait()
        + _dialogue_sequence(
            funeral[2:],
            flags=CHAPTER_ONE_LIVE_FUNERAL_HIDDEN_DIALOGUE_FLAGS,
        )
        + _actor_dialog_reset()
        + _wait(CHAPTER_ONE_LIVE_FUNERAL_REFLECTION_HOLD_FRAMES)
        # Ease back to the complete graveside tableau.  The old version
        # faded to black here and then opened the epilogue and final choice
        # without ever restoring the picture, leaving both interfaces
        # running invisibly.  Keep every remaining beat on the live field.
        + _chapter_one_live_funeral_camera(
            CHAPTER_ONE_LIVE_FUNERAL_CAMERA_TARGET,
            CHAPTER_ONE_LIVE_FUNERAL_CAMERA_EYE,
            transition_frames=CHAPTER_ONE_LIVE_FUNERAL_RETURN_CAMERA_MOVE_FRAMES,
            enter_camera_mode=False,
        )
        + _wait(CHAPTER_ONE_LIVE_FUNERAL_WIDE_HOLD_FRAMES)
        + _dialogue_sequence(
            epilogue,
            flags=CHAPTER_ONE_LIVE_FUNERAL_HIDDEN_DIALOGUE_FLAGS,
        )
        + _actor_dialog_reset()
        # Commit only after the explicit END OF CHAPTER 1 page closes.
        + atel.set_var_bit(
            PLAYABLE_STATE_VARIABLE,
            transition.bit,
        )
        + _wait(CHAPTER_ONE_LIVE_FUNERAL_EPILOGUE_SETTLE_FRAMES)
        # A stale Slot 1 completion bit used to skip every page and dump the
        # player into the orb room.  The funeral is now deliberately linear;
        # the visible Rico actor owns the reliable two-row completion menu.
        + _chapter_one_aftermath_call(
            CHAPTER_ONE_LIVE_FUNERAL_RICO_ENTITY,
            CHAPTER_ONE_LIVE_FUNERAL_COMPLETION_SCRIPT,
        )
    )
    return routine.finish()


def _build_chapter_one_live_funeral_completion(
    *,
    base_pc: int,
    choice_id: int,
    next_field: int,
    return_hub: int,
) -> bytes:
    """Show the graveside destination choice from Rico's visible actor."""

    routine = mass_driver._RoutineBuilder(base_pc)
    routine.label("completion_prompt")
    prefix = _actor_dialog_reset() + b"\x33\xFE\x54"
    release_pc = routine.pc + len(prefix)
    routine.emit(
        prefix
        + _wait_for_pad_release(
            PAD_MASK_CROSS | PAD_MASK_CIRCLE,
            release_pc,
        )
        + _wait()
        + _choice_dialog(choice_id)
        + b"\xA9\x12\x9C"
    )
    routine.jump_if_not_equal(
        MENU_SELECTION_VARIABLE,
        1,
        "check_hub",
    )
    routine.emit(
        _chapter_one_next_chapter_departure(
            next_field=next_field,
        )
    )
    routine.label("check_hub")
    routine.jump_if_not_equal(
        MENU_SELECTION_VARIABLE,
        2,
        "completion_prompt",
    )
    routine.emit(_chapter_one_hub_departure(return_hub))
    return routine.finish()


def _build_chapter_one_live_funeral_bundle(
    donor_bundle: bytes,
    young_rico_source_bundle: bytes,
    eton_source_bundle: bytes,
    chapter: Chapter,
    next_chapter: Chapter,
    return_hub: int,
) -> bytes:
    """Build Anne's funeral on an open burial ground beyond Nortune."""

    if (
        len(donor_bundle) != CHAPTER_ONE_LIVE_FUNERAL_DONOR_BUNDLE_SIZE
        or _sha256_bytes(donor_bundle)
        != CHAPTER_ONE_LIVE_FUNERAL_DONOR_BUNDLE_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 live-funeral donor changed")
    if chapter.chapter_id != 1 or next_chapter.chapter_id != 2:
        raise RicoArcBuildError("Chapter 1 live funeral lost its chapter route")
    if (
        len(eton_source_bundle) != CHAPTER_ONE_ETON_SOURCE_BUNDLE_SIZE
        or _sha256_bytes(eton_source_bundle)
        != CHAPTER_ONE_ETON_SOURCE_BUNDLE_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 Eton source changed")

    contract = _playable_chapter_contract(1)
    transition = contract.exit_transition
    if transition is None:
        raise RicoArcBuildError("Chapter 1 lost its funeral transition")
    funeral = _chapter_dialogue_texts(chapter, transition.funeral_dialogue)
    epilogue = _chapter_dialogue_texts(chapter, contract.exit_dialogue)
    dialogue_blocks = (
        *funeral,
        *epilogue,
        PLAYABLE_NEXT_OR_HUB_CHOICE,
    )
    funeral_ids = tuple(range(len(funeral)))
    epilogue_start = len(funeral)
    epilogue_ids = tuple(
        range(epilogue_start, epilogue_start + len(epilogue))
    )
    choice_id = epilogue_start + len(epilogue)
    next_field = _chapter_fields_for_hub(return_hub)[2]

    parsed = parse_field(donor_bundle)
    components = [part.data for part in parsed.parts]
    editor = AtelScript(components[SCRIPT_INDEX])
    if (
        len(parsed.header) != CHAPTER_ONE_LIVE_FUNERAL_DONOR_HEADER_SIZE
        or _sha256_bytes(parsed.header)
        != CHAPTER_ONE_LIVE_FUNERAL_DONOR_HEADER_SHA256
        or editor.entity_count != CHAPTER_ONE_LIVE_FUNERAL_ENTITY_COUNT
    ):
        raise RicoArcBuildError("Chapter 1 live-funeral layout changed")

    target_actor_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.ACTOR_INDEX]
    )
    target_sprite_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.SPRITE_INDEX]
    )
    if (
        len(target_actor_banks) != 6
        or len(target_sprite_banks) != 2
        or _sha256_bytes(
            target_actor_banks[CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX]
        )
        != CHAPTER_ONE_LIVE_FUNERAL_DONOR_RICO_ACTOR_BANK_SHA256
        or _sha256_bytes(
            target_sprite_banks[
                CHAPTER_ONE_LIVE_FUNERAL_DONOR_RICO_SPRITE_BANK_INDEX
            ]
        )
        != CHAPTER_ONE_LIVE_FUNERAL_DONOR_RICO_SPRITE_BANK_SHA256
        or _sha256_bytes(
            target_actor_banks[
                CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX
            ]
        )
        != CHAPTER_ONE_LIVE_FUNERAL_DONOR_PRIEST_ACTOR_BANK_SHA256
        or _sha256_bytes(
            target_sprite_banks[
                CHAPTER_ONE_LIVE_FUNERAL_PRESERVED_SPRITE_BANK_INDEX
            ]
        )
        != CHAPTER_ONE_LIVE_FUNERAL_DONOR_PRESERVED_SPRITE_BANK_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 live-funeral bank layout changed")
    if struct.unpack_from(
        "<4H",
        parsed.header,
        CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX * 8,
    ) != (832, 0, 0, 1) or struct.unpack_from(
        "<4H",
        parsed.header,
        CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX * 8,
    ) != (896, 0, 0, 0) or struct.unpack_from(
        "<4H",
        parsed.header,
        CHAPTER_ONE_LIVE_FUNERAL_PRESERVED_ACTOR_BANK_INDEX * 8,
    ) != (512, 256, 0, 0):
        raise RicoArcBuildError("Chapter 1 live-funeral VRAM map changed")

    young = parse_field(young_rico_source_bundle)
    young_components = [part.data for part in young.parts]
    young_actor_banks = mass_driver._indexed_bundle_entries(
        young_components[mass_driver.ACTOR_INDEX]
    )
    young_sprite_banks = mass_driver._indexed_bundle_entries(
        young_components[mass_driver.SPRITE_INDEX]
    )
    if (
        _sha256_bytes(young_components[mass_driver.ACTOR_INDEX])
        != YOUNG_RICO_ACTOR_COMPONENT_SHA256
        or _sha256_bytes(young_components[mass_driver.SPRITE_INDEX])
        != YOUNG_RICO_SPRITE_COMPONENT_SHA256
        or _sha256_bytes(young_actor_banks[YOUNG_RICO_ACTOR_BANK_INDEX])
        != YOUNG_RICO_ACTOR_BANK_SHA256
        or _sha256_bytes(young_sprite_banks[YOUNG_RICO_ACTOR_BANK_INDEX])
        != YOUNG_RICO_SPRITE_BANK_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 live-funeral Rico source changed")

    eton = parse_field(eton_source_bundle)
    eton_components = [part.data for part in eton.parts]
    if (
        len(eton_components[mass_driver.ACTOR_INDEX])
        != CHAPTER_ONE_ETON_ACTOR_COMPONENT_SIZE
        or _sha256_bytes(eton_components[mass_driver.ACTOR_INDEX])
        != CHAPTER_ONE_ETON_ACTOR_COMPONENT_SHA256
        or len(eton_components[mass_driver.SPRITE_INDEX])
        != CHAPTER_ONE_ETON_SPRITE_COMPONENT_SIZE
        or _sha256_bytes(eton_components[mass_driver.SPRITE_INDEX])
        != CHAPTER_ONE_ETON_SPRITE_COMPONENT_SHA256
        or struct.unpack_from(
            "<4H",
            eton.header,
            CHAPTER_ONE_ETON_SOURCE_BANK_INDEX * 8,
        )
        != CHAPTER_ONE_ETON_SOURCE_BANK_VRAM_MAPPING
    ):
        raise RicoArcBuildError("Chapter 1 Eton components changed")
    eton_actor_banks = mass_driver._indexed_bundle_entries(
        eton_components[mass_driver.ACTOR_INDEX]
    )
    eton_sprite_banks = mass_driver._indexed_bundle_entries(
        eton_components[mass_driver.SPRITE_INDEX]
    )
    eton_actor = eton_actor_banks[CHAPTER_ONE_ETON_SOURCE_BANK_INDEX]
    eton_sprite = eton_sprite_banks[CHAPTER_ONE_ETON_SOURCE_BANK_INDEX]
    if (
        len(eton_actor) != CHAPTER_ONE_ETON_ACTOR_BANK_SIZE
        or _sha256_bytes(eton_actor) != CHAPTER_ONE_ETON_ACTOR_BANK_SHA256
        or len(eton_sprite) != CHAPTER_ONE_ETON_SPRITE_BANK_SIZE
        or _sha256_bytes(eton_sprite) != CHAPTER_ONE_ETON_SPRITE_BANK_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 hooded Eton bank changed")

    components[mass_driver.ACTOR_INDEX] = (
        mass_driver._replace_indexed_bundle_entry(
            components[mass_driver.ACTOR_INDEX],
            CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX,
            eton_actor,
            CHAPTER_ONE_LIVE_FUNERAL_DONOR_PRIEST_ACTOR_BANK_SHA256,
        )
    )
    components[mass_driver.ACTOR_INDEX] = (
        mass_driver._replace_indexed_bundle_entry(
            components[mass_driver.ACTOR_INDEX],
            CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX,
            young_actor_banks[YOUNG_RICO_ACTOR_BANK_INDEX],
            CHAPTER_ONE_LIVE_FUNERAL_DONOR_RICO_ACTOR_BANK_SHA256,
        )
    )
    components[mass_driver.SPRITE_INDEX] = mass_driver._rebuild_indexed_bundle(
        components[mass_driver.SPRITE_INDEX],
        (
            eton_sprite,
            young_sprite_banks[YOUNG_RICO_ACTOR_BANK_INDEX],
            target_sprite_banks[
                CHAPTER_ONE_LIVE_FUNERAL_PRESERVED_SPRITE_BANK_INDEX
            ],
        ),
    )
    if (
        len(components[mass_driver.ACTOR_INDEX])
        != CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_ACTOR_SIZE
        or _sha256_bytes(components[mass_driver.ACTOR_INDEX])
        != CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_ACTOR_SHA256
        or len(components[mass_driver.SPRITE_INDEX])
        != CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_SPRITE_SIZE
        or _sha256_bytes(components[mass_driver.SPRITE_INDEX])
        != CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_SPRITE_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 live-funeral bank install drifted")

    model_entries = mass_driver._indexed_bundle_entries(
        components[mass_driver.MODEL_INDEX]
    )
    marker_at = 0x190 + CHAPTER_ONE_GRAVE_MARKER_TARGET_NODE * 16
    background_marker_at = (
        0x190 + CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_NODE * 16
    )
    if (
        len(model_entries) <= CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_MODEL_INDEX
        or _sha256_bytes(
            model_entries[CHAPTER_ONE_GRAVE_MARKER_TARGET_MODEL_INDEX]
        )
        != CHAPTER_ONE_GRAVE_MARKER_TARGET_MODEL_SHA256
        or _sha256_bytes(
            model_entries[CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_MODEL_INDEX]
        )
        != CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_MODEL_SHA256
        or parsed.header[marker_at : marker_at + 16]
        != CHAPTER_ONE_GRAVE_MARKER_SOURCE_NODE_RECORD
        or parsed.header[background_marker_at : background_marker_at + 16]
        != CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_SOURCE_NODE_RECORD
    ):
        raise RicoArcBuildError("Chapter 1 native grave markers changed")

    header = bytearray(parsed.header)
    struct.pack_into(
        "<4H",
        header,
        CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX * 8,
        *CHAPTER_ONE_LIVE_FUNERAL_PRIEST_VRAM_MAPPING,
    )
    struct.pack_into(
        "<4H",
        header,
        CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX * 8,
        *CHAPTER_ONE_LIVE_FUNERAL_RICO_VRAM_MAPPING,
    )
    header[marker_at : marker_at + 16] = (
        CHAPTER_ONE_GRAVE_MARKER_TARGET_NODE_RECORD
    )
    header[background_marker_at : background_marker_at + 16] = (
        CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_NODE_RECORD
    )
    if (
        len(header) != CHAPTER_ONE_LIVE_FUNERAL_DONOR_HEADER_SIZE
        or _sha256_bytes(header)
        != CHAPTER_ONE_LIVE_FUNERAL_INSTALLED_HEADER_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 funeral VRAM remap drifted")
    header = bytes(header)

    triangles = _walkmesh_layer(components[1], 0)
    for role, (x, z, triangle) in (
        ("grave marker", CHAPTER_ONE_LIVE_FUNERAL_MARKER_POSITION),
        (
            "background grave marker",
            CHAPTER_ONE_LIVE_FUNERAL_BACKGROUND_MARKER_POSITION,
        ),
        ("Rico", CHAPTER_ONE_LIVE_FUNERAL_RICO_POSITION),
        ("Eton start", CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START),
        ("Eton blessing", CHAPTER_ONE_LIVE_FUNERAL_PRIEST_BLESSING_POSITION),
    ):
        if (
            not 0 <= triangle < len(triangles)
            or not _point_inside_triangle((x, z), triangles[triangle])
        ):
            raise RicoArcBuildError(
                f"Chapter 1 live-funeral {role} left its walkmesh triangle"
            )
    if not _chapter_four_segment_on_walkmesh(
        CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START[:2],
        CHAPTER_ONE_LIVE_FUNERAL_PRIEST_BLESSING_POSITION[:2],
        triangles,
    ):
        raise RicoArcBuildError("Chapter 1 Eton blessing route is obstructed")

    encounter = bytearray(components[mass_driver.ENCOUNTER_INDEX])
    if len(encounter) != ENCOUNTER_COMPONENT_SIZE:
        raise RicoArcBuildError("Chapter 1 funeral encounter table changed")
    encounter[WEIGHTS_OFFSET : WEIGHTS_OFFSET + FORMATION_COUNT] = bytes(
        FORMATION_COUNT
    )
    components[mass_driver.ENCOUNTER_INDEX] = bytes(encounter)

    editor = AtelScript(components[SCRIPT_INDEX])
    stop_pc = editor.append_raw_routine(b"\x00")
    for entity in range(editor.entity_count):
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)
    for entity in range(3, editor.entity_count):
        editor.append_and_repoint(entity, 0, INERT_HIDDEN_INIT)
    editor.append_and_repoint(
        CHAPTER_ONE_LIVE_FUNERAL_RICO_ENTITY,
        0,
        _chapter_one_live_funeral_actor_init(
            CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX,
            CHAPTER_ONE_LIVE_FUNERAL_RICO_POSITION,
            CHAPTER_ONE_LIVE_FUNERAL_RICO_DIRECTION,
        ),
    )
    completion_pc = editor.bytecode_size
    editor.append_and_repoint(
        CHAPTER_ONE_LIVE_FUNERAL_RICO_ENTITY,
        CHAPTER_ONE_LIVE_FUNERAL_COMPLETION_SCRIPT,
        _build_chapter_one_live_funeral_completion(
            base_pc=completion_pc,
            choice_id=choice_id,
            next_field=next_field,
            return_hub=return_hub,
        ),
    )
    editor.append_and_repoint(
        CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ENTITY,
        0,
        _chapter_one_live_funeral_actor_init(
            CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX,
            CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START,
            CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START_DIRECTION,
        ),
    )
    editor.append_and_repoint(
        CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ENTITY,
        CHAPTER_ONE_LIVE_FUNERAL_PRIEST_APPROACH_SCRIPT,
        _chapter_one_live_funeral_priest_approach(),
    )
    editor.append_and_repoint(
        0,
        0,
        INERT_HIDDEN_INIT[:-1]
        + _play_music(chapter.music)
        + mass_driver._facility_video_screen_fade_body(0xFF, 1)
        + b"\x00",
    )
    story_pc = editor.bytecode_size
    editor.append_and_repoint(
        0,
        1,
        _build_chapter_one_live_funeral_story(
            base_pc=story_pc,
            transition=transition,
            funeral_ids=funeral_ids,
            epilogue_ids=epilogue_ids,
        ),
    )
    components[SCRIPT_INDEX] = editor.to_bytes()
    components[DIALOGUE_INDEX] = _dialogue_data(
        dialogue_blocks,
        fit_windows=True,
        sentence_safe_pages=True,
    )

    changed = (
        mass_driver.ACTOR_INDEX,
        mass_driver.SPRITE_INDEX,
        mass_driver.ENCOUNTER_INDEX,
        SCRIPT_INDEX,
        DIALOGUE_INDEX,
    )
    bundle = build_field_preserving(
        donor_bundle,
        components,
        changed,
        compact_changed=True,
        replacement_header=header,
    )
    reparsed = parse_field(bundle)
    if (
        tuple(part.data for part in reparsed.parts) != tuple(components)
        or len(reparsed.header) != len(header)
        or struct.unpack_from(
            "<4H",
            reparsed.header,
            CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX * 8,
        )
        != CHAPTER_ONE_LIVE_FUNERAL_PRIEST_VRAM_MAPPING
        or struct.unpack_from(
            "<4H",
            reparsed.header,
            CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX * 8,
        )
        != CHAPTER_ONE_LIVE_FUNERAL_RICO_VRAM_MAPPING
        or reparsed.header[0x18C:] != header[0x18C:]
    ):
        raise RicoArcBuildError(
            "Chapter 1 live funeral failed packed round-trip"
        )
    return bundle


def _chapter_one_still_screen_model(donor_bundle: bytes) -> bytes:
    """Extract field 617's isolated 36-quad still-image plane."""

    parsed = parse_field(donor_bundle)
    models = parsed.parts[mass_driver.MODEL_INDEX].data
    if (
        len(models) != CHAPTER_ONE_STILL_SCREEN_DONOR_ARCHIVE_SIZE
        or _sha256_bytes(models)
        != CHAPTER_ONE_STILL_SCREEN_DONOR_ARCHIVE_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 still-screen donor archive changed")
    entries = mass_driver._indexed_bundle_entries(models)
    if CHAPTER_ONE_STILL_SCREEN_DONOR_MODEL_INDEX >= len(entries):
        raise RicoArcBuildError("Chapter 1 still-screen donor model is absent")
    screen = entries[CHAPTER_ONE_STILL_SCREEN_DONOR_MODEL_INDEX]
    if (
        len(screen) != CHAPTER_ONE_STILL_SCREEN_MODEL_SIZE
        or _sha256_bytes(screen) != CHAPTER_ONE_STILL_SCREEN_MODEL_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 still-screen model changed")
    return screen


def _install_chapter_one_still_screen(
    header: bytes,
    models: bytes,
    screen_model: bytes,
) -> tuple[bytes, bytes]:
    """Insert the hidden image plane before field 394's static nodes."""

    if (
        len(header) != 848
        or struct.unpack_from("<H", header, 0x18C)[0] != 28
        or len(screen_model) != CHAPTER_ONE_STILL_SCREEN_MODEL_SIZE
        or _sha256_bytes(screen_model) != CHAPTER_ONE_STILL_SCREEN_MODEL_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 still-screen staging changed")
    entries = mass_driver._indexed_bundle_entries(models)
    if len(entries) != CHAPTER_ONE_STILL_SCREEN_MODEL_INDEX:
        raise RicoArcBuildError("Chapter 1 still-screen model index drifted")
    rebuilt_models = mass_driver._rebuild_indexed_bundle(
        models,
        (*entries, screen_model),
    )

    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(28)
    ]
    screen_x, screen_y, screen_z = CHAPTER_ONE_STILL_SCREEN_POSITION
    records.insert(
        CHAPTER_ONE_STILL_SCREEN_ENTITY,
        mass_driver._field_actor_record(
            0x02B0,
            screen_x,
            screen_z,
            CHAPTER_ONE_STILL_SCREEN_MODEL_INDEX,
            y=screen_y,
        ),
    )
    rebuilt_header = bytearray(header[:0x190] + b"".join(records))
    struct.pack_into("<H", rebuilt_header, 0x18C, len(records))
    if (
        len(rebuilt_header) != 864
        or len(records) != 29
        or len(mass_driver._indexed_bundle_entries(rebuilt_models)) != 15
    ):
        raise RicoArcBuildError("Chapter 1 still-screen insertion drifted")
    return bytes(rebuilt_header), rebuilt_models


def _chapter_one_still_plane_load(field_file_id: int) -> bytes:
    """Load one TIM into the caption-safe retail model-plane texture pages."""

    if field_file_id not in CHAPTER_ONE_STILL_FIELD_FILE_IDS:
        raise RicoArcBuildError("Unknown Chapter 1 still selector")
    return (
        b"\xFE\x77\x00"
        + b"\xFE\x77\x01"
        + _u16(field_file_id)
        # Retail fields 617/618's caption-safe 16-bpp pages at (320,256).
        + b"\x40\x01\x00\x01\x00\x00\xF0"
        + b"\xFE\x77\x02"
        + _wait(15)
    )


def _chapter_one_still_caption_sequence(block_ids: Iterable[int]) -> bytes:
    """Keep the image plane visible beneath fixed-top borderless captions."""

    ids = tuple(block_ids)
    if not ids:
        raise RicoArcBuildError("Chapter 1 still has no captions")
    output = bytearray()
    for index, block_id in enumerate(ids):
        output.extend(_dialog(block_id, flags=0x53) + b"\x9C")
        if index + 1 < len(ids):
            output.extend(_wait())
    return bytes(output)


def _chapter_one_still_story_segment(
    field_file_id: int,
    block_ids: Iterable[int],
) -> bytes:
    """Load, reveal, caption, and fade one held Chapter 1 story image."""

    return (
        _chapter_one_still_plane_load(field_file_id)
        + mass_driver._facility_video_screen_fade_body(
            0,
            CHAPTER_ONE_STILL_FADE_FRAMES,
        )
        + _chapter_one_still_caption_sequence(block_ids)
        + mass_driver._facility_video_screen_fade_body(
            0xFF,
            CHAPTER_ONE_STILL_FADE_FRAMES,
        )
    )


def _build_chapter_one_funeral_story(
    *,
    base_pc: int,
    transition: PlayableExitTransition,
    sickness_ids: Sequence[int],
    loss_ids: Sequence[int],
    funeral_ids: Sequence[int],
    epilogue_ids: Sequence[int],
    choice_id: int,
    return_hub: int,
) -> bytes:
    """Build the one-shot funeral and its replayable destination choice."""

    routine = mass_driver._RoutineBuilder(base_pc)
    routine.emit(_actor_dialog_reset() + b"\x33\xFE\x54")
    release_pc = routine.pc
    routine.emit(_wait_for_pad_release(PAD_MASK_CROSS, release_pc) + _wait())
    routine.jump_if_bit_clear(
        PLAYABLE_STATE_VARIABLE,
        1 << transition.bit,
        "first_run",
    )
    routine.jump("completion_prompt")

    routine.label("first_run")
    # Field 617's isolated plane keeps the three supplied 16-bpp aftermath
    # pictures away from the ordinary glyph pages. Each image therefore
    # remains on screen until the player finishes its relevant captions.
    routine.emit(
        b"\xFE\x65\x46\x80\x01\x80"
        + mass_driver._facility_video_screen_camera_body()
        + b"\x24"
        + bytes((CHAPTER_ONE_STILL_SCREEN_ENTITY,))
        + _chapter_one_still_story_segment(
            CHAPTER_ONE_ANNA_SICKBED_FIELD_FILE_ID,
            sickness_ids,
        )
    )
    release_pc = routine.pc
    routine.emit(_wait_for_pad_release(PAD_MASK_CROSS, release_pc) + _wait())
    routine.emit(
        _chapter_one_still_story_segment(
            CHAPTER_ONE_RICO_MOURNING_FIELD_FILE_ID,
            loss_ids,
        )
    )
    release_pc = routine.pc
    routine.emit(_wait_for_pad_release(PAD_MASK_CROSS, release_pc) + _wait())
    routine.emit(
        _chapter_one_still_story_segment(
            CHAPTER_ONE_FUNERAL_FIELD_FILE_ID,
            funeral_ids,
        )
        + b"\x25"
        + bytes((CHAPTER_ONE_STILL_SCREEN_ENTITY,))
        + _actor_dialog_reset()
    )
    # Commit only after all three images and Chapter 1's closing page complete.
    # A canceled destination prompt can therefore never replay the sequence.
    routine.emit(
        atel.set_var_bit(
            PLAYABLE_STATE_VARIABLE,
            transition.bit,
        )
        + _dialogue_sequence(epilogue_ids)
        + _wait()
    )

    routine.label("completion_prompt")
    routine.emit(_actor_dialog_reset())
    release_pc = routine.pc
    routine.emit(
        _wait_for_pad_release(
            PAD_MASK_CROSS | PAD_MASK_CIRCLE,
            release_pc,
        )
        + _wait()
        + _choice_dialog(choice_id)
        + b"\xA9\x12\x9C"
    )
    routine.jump_if_not_equal(
        MENU_SELECTION_VARIABLE,
        1,
        "check_hub",
    )
    next_field = _chapter_fields_for_hub(return_hub)[2]
    routine.emit(
        _chapter_one_next_chapter_departure(
            next_field=next_field,
        )
    )
    routine.label("check_hub")
    routine.jump_if_not_equal(
        MENU_SELECTION_VARIABLE,
        2,
        "completion_retry",
    )
    routine.emit(_chapter_one_hub_departure(return_hub))
    routine.label("completion_retry")
    routine.jump("completion_prompt")
    return routine.finish()


def _build_chapter_one_funeral_bundle(
    donor_bundle: bytes,
    screen_model: bytes,
    chapter: Chapter,
    next_chapter: Chapter,
    return_hub: int,
) -> bytes:
    """Clone retail field 394 into field 376 as an automatic funeral scene."""

    if (
        len(donor_bundle) != CHAPTER_ONE_FUNERAL_DONOR_BUNDLE_SIZE
        or _sha256_bytes(donor_bundle)
        != CHAPTER_ONE_FUNERAL_DONOR_BUNDLE_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 funeral field donor changed")
    if chapter.chapter_id != 1:
        raise RicoArcBuildError("The funeral presentation requires Chapter 1")
    if next_chapter.chapter_id != 2:
        raise RicoArcBuildError("The funeral must lead into Chapter 2")
    contract = _playable_chapter_contract(1)
    transition = contract.exit_transition
    if transition is None:
        raise RicoArcBuildError("Chapter 1 lost its funeral exit transition")

    sickness = _chapter_dialogue_texts(
        chapter,
        transition.sickness_dialogue,
    )
    loss = _chapter_dialogue_texts(
        chapter,
        transition.loss_dialogue,
    )
    funeral = _chapter_dialogue_texts(
        chapter,
        transition.funeral_dialogue,
    )
    epilogue = _chapter_dialogue_texts(chapter, contract.exit_dialogue)
    dialogue_blocks = (
        *sickness,
        *loss,
        *funeral,
        *epilogue,
        PLAYABLE_NEXT_OR_HUB_CHOICE,
    )
    sickness_ids = tuple(range(len(sickness)))
    loss_start = len(sickness)
    loss_ids = tuple(range(loss_start, loss_start + len(loss)))
    funeral_start = loss_start + len(loss)
    funeral_ids = tuple(
        range(funeral_start, funeral_start + len(funeral))
    )
    epilogue_start = funeral_start + len(funeral)
    epilogue_ids = tuple(
        range(epilogue_start, epilogue_start + len(epilogue))
    )
    choice_id = epilogue_start + len(epilogue)

    parsed = parse_field(donor_bundle)
    components = [part.data for part in parsed.parts]
    editor = AtelScript(components[SCRIPT_INDEX])
    if (
        editor.entity_count != 14
        or len(parsed.header) != 848
        or parsed.header[0x18C:0x18E] != _u16(28)
        or editor.bytecode[
            editor.get_script_pointer(0, 0) :
            editor.get_script_pointer(0, 0)
            + 1
            + len(CHAPTER_ONE_FUNERAL_SCREEN_GEOMETRY)
            + 1
        ]
        != b"\xBC" + CHAPTER_ONE_FUNERAL_SCREEN_GEOMETRY + b"\x2A"
    ):
        raise RicoArcBuildError("Chapter 1 funeral donor staging changed")

    header, components[mass_driver.MODEL_INDEX] = (
        _install_chapter_one_still_screen(
            parsed.header,
            components[mass_driver.MODEL_INDEX],
            screen_model,
        )
    )
    editor = AtelScript(
        mass_driver._extend_atel_entity_table(
            components[SCRIPT_INDEX],
            CHAPTER_ONE_STILL_SCREEN_ENTITY + 1,
        )
    )

    stop_pc = editor.append_raw_routine(b"\x00")
    for entity in range(editor.entity_count):
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)

    # Preserve field 394's exact full-screen projection geometry, hide its
    # director, and black the 3-D room before the automatic sequence begins.
    director_init = (
        b"\xBC"
        + CHAPTER_ONE_FUNERAL_SCREEN_GEOMETRY
        + b"\x2A"
        + _play_music(chapter.music)
        + mass_driver._facility_video_screen_fade_body(0xFF, 1)
        + b"\x00"
    )
    editor.append_and_repoint(0, 0, director_init)
    editor.append_and_repoint(
        CHAPTER_ONE_STILL_SCREEN_ENTITY,
        0,
        mass_driver._facility_video_screen_init_body(),
    )
    story_pc = editor.bytecode_size
    editor.append_and_repoint(
        0,
        1,
        _build_chapter_one_funeral_story(
            base_pc=story_pc,
            transition=transition,
            sickness_ids=sickness_ids,
            loss_ids=loss_ids,
            funeral_ids=funeral_ids,
            epilogue_ids=epilogue_ids,
            choice_id=choice_id,
            return_hub=return_hub,
        ),
    )
    components[SCRIPT_INDEX] = editor.to_bytes()
    components[DIALOGUE_INDEX] = _dialogue_data(
        dialogue_blocks,
        fit_windows=True,
        sentence_safe_pages=True,
    )
    bundle = build_field_preserving(
        donor_bundle,
        components,
        (SCRIPT_INDEX, mass_driver.MODEL_INDEX, DIALOGUE_INDEX),
        compact_changed=True,
        replacement_header=header,
    )
    reparsed = parse_field(bundle)
    if (
        tuple(part.data for part in reparsed.parts) != tuple(components)
        or len(reparsed.header) != len(header)
        or reparsed.header[0x18C:] != header[0x18C:]
    ):
        raise RicoArcBuildError("Chapter 1 funeral field failed packed round-trip")
    return bundle


def _ordered_hub_chapters(chapters: Sequence[Chapter]) -> tuple[Chapter, ...]:
    ordered = tuple(chapters)
    if tuple(chapter.chapter_id for chapter in ordered) != tuple(range(1, 8)):
        raise RicoArcBuildError("Chapter hub content must contain chapters 1..7")
    return ordered


def _hub_dialogue_blocks() -> tuple[str, ...]:
    titles = (
        "MOTHER'S PROMISE",
        "THE CHAMP",
        "THE LOCKED ROOM",
        "THE BURIED SHIP",
        "PROTOCOL B",
        "THINGS LEFT TO DO",
        "RESOLVE",
    )
    return tuple(
        f"<Opcode:01:FF>CHAPTER {chapter_id}: {title}?\n"
        "     Enter\n     Not yet<Close>"
        for chapter_id, title in enumerate(titles, start=1)
    )


def _hub_dialogue_layout(chapters: Sequence[Chapter]) -> tuple[str, ...]:
    ordered = _ordered_hub_chapters(chapters)
    return (
        *_hub_dialogue_blocks(),
        *(
            text
            for chapter in ordered
            for text in _chapter_selection_exposition(chapter)
        ),
    )


def _hub_selection_exposition_ids(
    chapters: Sequence[Chapter],
) -> dict[int, tuple[int, ...]]:
    ordered = _ordered_hub_chapters(chapters)
    cursor = len(_hub_dialogue_blocks())
    result: dict[int, tuple[int, ...]] = {}
    for chapter in ordered:
        count = len(_chapter_selection_exposition(chapter))
        result[chapter.chapter_id] = tuple(range(cursor, cursor + count))
        cursor += count
    return result


def _chapter_party_setup(chapter_id: int) -> bytes:
    """Normalize the live party and battle frame for one selectable chapter."""

    party = CHAPTER_PARTIES[chapter_id]
    expected_leader = YOUNG_RICO_ID if chapter_id == 1 else RICO_ID
    if (
        not party
        or party[0] != expected_leader
        or len(party) != len(set(party))
    ):
        raise RicoArcBuildError(
            f"Chapter {chapter_id} party has an invalid unique leader"
        )
    return _party_setup(party)


def _party_setup(party: Sequence[int]) -> bytes:
    """Remove every live member, then install one exact ordered party."""

    if not party or len(party) != len(set(party)) or any(
        not 0 <= character <= 10 for character in party
    ):
        raise RicoArcBuildError("Party setup contains invalid character IDs")
    setup = bytearray()
    # FE19/FE18 are the actual current-party operations. FE1A completes each
    # asynchronous load before the next add or field transition. Remove every
    # possible member—including Rico—then add the exact requested party. This
    # remains deterministic even when entered from a noncanonical live state.
    for character in range(11):
        setup.extend(b"\xFE\x19" + bytes((character,)))
    for character in party:
        setup.extend(b"\xFE\x18" + bytes((character,)) + b"\xFE\x1A")

    # The battle frame is independent of the current-party operations.
    for character in range(11):
        setup.extend(b"\xFE\x3B" + _immediate(character))
    for character in party:
        setup.extend(b"\xFE\x3A" + _immediate(character))
    return bytes(setup)


def _chapter_one_inventory_restriction() -> bytes:
    """Remove non-child item and equipment stacks from the checked baseline."""

    return b"".join(
        b"\x8D" + _immediate(object_id)
        for object_id, quantity in CHAPTER_ONE_HIDDEN_INVENTORY_OBJECT_STACKS
        for _copy in range(quantity)
    )


def _chapter_one_inventory_restore() -> bytes:
    """Restore all inventory stacks hidden while Chapter 1 was active."""

    return b"".join(
        b"\x8C" + _immediate(object_id)
        for object_id, quantity in CHAPTER_ONE_HIDDEN_INVENTORY_OBJECT_STACKS
        for _copy in range(quantity)
    )


def _chapter_one_next_chapter_departure(
    *,
    next_field: int,
) -> bytes:
    """Restore adult Rico's items, then launch Chapter 2 without a teaser."""

    return _chapter_one_inventory_restore() + _chapter_launch_body(2, next_field)


def _chapter_one_hub_departure(return_hub: int) -> bytes:
    """Restore adult Rico's items, then leave Chapter 1 for its hub."""

    return _chapter_one_inventory_restore() + _hub_launch_body(return_hub)


def _chapter_two_transition_out() -> bytes:
    """Conceal live party removal and re-registration before a field load."""

    return b"\x33\xFE\x54\xB4" + _immediate(12) + _wait(12)


def _chapter_launch_body(chapter_id: int, target_field: int) -> bytes:
    prefix = b""
    party_setup = _chapter_party_setup(chapter_id)
    if chapter_id == 2:
        # Missing-story interludes begin with Rico. Fei's arrival and every
        # original campaign event remain outside this anthology's scenes.
        prefix = _chapter_two_transition_out()
        party_setup = _party_setup((5,))
    return (
        prefix
        + party_setup
        + (
            _chapter_one_inventory_restriction()
            if chapter_id == 1
            else b""
        )
        + atel.set_variable_s16(PLAYABLE_STATE_VARIABLE, 0)
        + (
            (
                atel.set_variable_s16(
                    CHAPTER_TWO_PERSISTENT_STATE_VARIABLE,
                    0,
                )
                + atel.set_variable_s16(
                    CHAPTER_TWO_HAMMER_STATE_VARIABLE,
                    0,
                )
            )
            if chapter_id == 2
            else b""
        )
        + _change_field(target_field, 0)
        + b"\x5B"
    )


def _hub_launch_body(target_field: int) -> bytes:
    """Return to a clean Rico-only chapter-select state."""

    return (
        _party_setup(HUB_PARTY)
        + atel.set_variable_s16(PLAYABLE_STATE_VARIABLE, 0)
        + atel.set_variable_s16(
            CHAPTER_TWO_PERSISTENT_STATE_VARIABLE,
            0,
        )
        + atel.set_variable_s16(
            CHAPTER_TWO_HAMMER_STATE_VARIABLE,
            0,
        )
        + _change_field(target_field, 0)
        + b"\x5B"
    )


def _hub_marker_init(marker: HubMarker) -> bytes:
    """Create one visible, non-colliding native Sephirot memory light."""

    if marker not in HUB_MARKERS:
        raise RicoArcBuildError("Unknown Sephirot chapter marker")
    return (
        b"\x0B"
        + _immediate(HUB_MARKER_ACTOR_BANK)
        + b"\x19"
        + _s16(marker.x)
        + _s16(marker.z)
        + b"\xC0\x1A\x00"
        # These are the retail light's own translucent render mode and scale.
        + b"\xFE\x5E"
        + _immediate(2)
        + b"\xFE\x03"
        + _immediate(0x1555)
        # Rectangular, facing-gated action target; OP20/0x80 removes physical
        # actor contact so the seven lights never obstruct Rico's path.
        + b"\xF8\x00\x00\x20\xF8\x03\x04\x00\x18"
        + bytes((HUB_MARKER_HALF_WIDTH, HUB_MARKER_HALF_DEPTH, 0x64, 0))
        + b"\x20\x01\x80\x00"
    )


def _hub_save_point_assets(donor_bundle: bytes) -> tuple[bytes, bytes]:
    """Extract the checked retail memory-cube actor and sprite banks."""

    parsed = parse_field(donor_bundle)
    components = [part.data for part in parsed.parts]
    if len(parsed.header) != 848:
        raise RicoArcBuildError("Memory-cube donor actor header changed")
    actor_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.ACTOR_INDEX]
    )
    sprite_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.SPRITE_INDEX]
    )
    source_bank = 1
    source_editor = AtelScript(components[SCRIPT_INDEX])
    if source_editor.entity_count != 17:
        raise RicoArcBuildError("Retail memory-cube donor entity count changed")
    source_pointers = tuple(
        source_editor.get_script_pointer(HUB_SAVE_SOURCE_ENTITY, script_index)
        for script_index in range(4)
    )
    source_record = 0x190 + HUB_SAVE_SOURCE_ENTITY * 16
    expected_record = mass_driver._field_actor_record(0x01E0, 0, 0, 0)
    if (
        len(actor_banks) != 2
        or len(sprite_banks) != 2
        or len(actor_banks[source_bank]) != HUB_SAVE_ACTOR_SIZE
        or _sha256_bytes(actor_banks[source_bank]) != HUB_SAVE_ACTOR_SHA256
        or len(sprite_banks[source_bank]) != HUB_SAVE_SPRITE_SIZE
        or _sha256_bytes(sprite_banks[source_bank]) != HUB_SAVE_SPRITE_SHA256
        or struct.unpack_from("<4H", parsed.header, source_bank * 8)
        != (896, 0, 0, 0)
        or parsed.header[source_record : source_record + 16] != expected_record
        or source_pointers != HUB_SAVE_SOURCE_POINTERS
        or source_editor.bytecode[
            source_pointers[1] : source_pointers[1] + len(HUB_SAVE_UPDATE)
        ]
        != HUB_SAVE_UPDATE
        or source_editor.bytecode[
            source_pointers[2] :
            source_pointers[2] + len(HUB_SAVE_NATIVE_ACTION)
        ]
        != HUB_SAVE_NATIVE_ACTION
        or source_editor.bytecode[
            source_pointers[3] :
            source_pointers[3] + len(HUB_SAVE_NATIVE_COLLISION_PREFIX)
        ]
        != HUB_SAVE_NATIVE_COLLISION_PREFIX
    ):
        raise RicoArcBuildError("Retail memory-cube donor changed")
    return actor_banks[source_bank], sprite_banks[source_bank]


def _hub_save_point_init() -> bytes:
    """Place the authentic memory cube on the clear south-east hub approach."""

    x, z, triangle = HUB_SAVE_POSITION
    return (
        b"\x0B"
        + _immediate(HUB_SAVE_ACTOR_BANK)
        + b"\x19"
        + _s16(x)
        + _s16(z)
        + b"\xC0\x1A"
        + bytes((triangle,))
        + b"\x20\x0D\x80\xF8\x00\x00\x20\x18"
        + bytes((HUB_SAVE_HALF_WIDTH, HUB_SAVE_HALF_DEPTH, 0x64, 0))
        + b"\x1F\x70\x00"
    )


def _hub_save_point_collision(base_pc: int) -> bytes:
    """Relocate the retail one-shot proximity chime without absolute PCs."""

    routine = RoutineBuilder(base_pc)
    routine.emit(b"\xFE\x99\x00")
    routine.jump_if_not_equal(HUB_SAVE_LOCAL_FLAG, 0, "stop")
    routine.emit(
        b"\x74"
        + _immediate(0x50)
        + b"\x36"
        + _u16(HUB_SAVE_LOCAL_FLAG)
    )
    routine.label("stop")
    routine.emit(b"\x00")
    return routine.finish()


def _build_hub_save_point_action(
    base_pc: int,
    dialogue_id: int,
    content_menu_field: int,
) -> bytes:
    """Offer native Save, an in-session content-menu return, or Cancel."""

    if isinstance(content_menu_field, bool) or not isinstance(
        content_menu_field, int
    ):
        raise RicoArcBuildError("Content-menu field must be an integer")
    content_menu_route = (
        atel.set_variable_s16(PLAYABLE_STATE_VARIABLE, 0)
        + _change_field(content_menu_field, 0)
        + b"\x5B"
    )
    if _playable_choice_count(HUB_SAVE_MENU_CHOICE) != 3:
        raise RicoArcBuildError("Hub memory-cube menu must have three choices")

    routine = RoutineBuilder(base_pc)
    routine.emit(_playable_action_prefix(base_pc))
    routine.emit(_choice_dialog(dialogue_id) + b"\xA9\x12\x9C")
    routine.jump_if_not_equal(MENU_SELECTION_VARIABLE, 1, "check_return")
    # FE87 only reports that the native menu closed; it cannot distinguish a
    # completed save from Cancel. Return to the hub after Save so a canceled
    # memory-card operation never ejects the player into another module.
    routine.emit(HUB_SAVE_NATIVE_ACTION[:-1])
    routine.jump("finish")

    routine.label("check_return")
    routine.jump_if_not_equal(MENU_SELECTION_VARIABLE, 2, "finish")
    routine.emit(content_menu_route)

    routine.label("finish")
    routine.emit(_playable_action_finish(routine.pc))
    return routine.finish()


def _build_hub_marker_action(
    base_pc: int,
    marker: HubMarker,
    target_field: int,
    exposition_ids: Sequence[int],
) -> bytes:
    """Build one explicit-Cross, cancel-safe chapter-memory entrance."""

    if marker not in HUB_MARKERS or not 1 <= marker.chapter_id <= 7:
        raise RicoArcBuildError("Chapter marker ID is outside 1..7")
    if not exposition_ids:
        raise RicoArcBuildError("Chapter marker has no selection exposition")

    routine = RoutineBuilder(base_pc)
    routine.emit(_playable_action_prefix(base_pc))
    routine.emit(_choice_dialog(marker.chapter_id - 1) + b"\xA9\x12\x9C")
    routine.jump_if_not_equal(MENU_SELECTION_VARIABLE, 1, "cancel")
    routine.emit(
        _prelaunch_exposition(
            exposition_ids,
            routine_pc=routine.pc,
        )
    )
    routine.emit(_chapter_launch_body(marker.chapter_id, target_field))

    routine.label("cancel")
    routine.emit(_playable_action_finish(routine.pc))
    return routine.finish()


def _build_hub_bundle(
    donor_bundle: bytes,
    chapter_fields: Mapping[int, int],
    chapters: Sequence[Chapter],
    *,
    content_menu_field: int | None = None,
    save_point_donor_bundle: bytes | None = None,
) -> bytes:
    if set(chapter_fields) != set(range(1, 8)):
        raise RicoArcBuildError("Chapter hub route table must contain chapters 1..7")
    if (content_menu_field is None) != (save_point_donor_bundle is None):
        raise RicoArcBuildError(
            "Content-menu field and memory-cube donor must be supplied together"
        )
    install_save_point = content_menu_field is not None
    save_assets = (
        _hub_save_point_assets(save_point_donor_bundle)
        if save_point_donor_bundle is not None
        else None
    )
    ordered_chapters = _ordered_hub_chapters(chapters)
    exposition_ids = _hub_selection_exposition_ids(ordered_chapters)
    if (
        len(donor_bundle) != HUB_DONOR_BUNDLE_SIZE
        or _sha256_bytes(donor_bundle) != HUB_DONOR_BUNDLE_SHA256
    ):
        raise RicoArcBuildError("Path of Sephirot hub donor changed")
    parsed = parse_field(donor_bundle)
    components = [part.data for part in parsed.parts]
    if len(parsed.header) != 592:
        raise RicoArcBuildError("Path of Sephirot actor header changed")
    actor_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.ACTOR_INDEX]
    )
    sprite_banks = mass_driver._indexed_bundle_entries(
        components[mass_driver.SPRITE_INDEX]
    )
    if (
        len(actor_banks) != 2
        or _sha256_bytes(actor_banks[HUB_MARKER_ACTOR_BANK])
        != HUB_MARKER_ACTOR_BANK_SHA256
        or len(sprite_banks) != 2
        or _sha256_bytes(sprite_banks[HUB_MARKER_ACTOR_BANK])
        != HUB_MARKER_SPRITE_BANK_SHA256
    ):
        raise RicoArcBuildError("Path of Sephirot light assets changed")
    if install_save_point:
        if save_assets is None:
            raise RicoArcBuildError("Memory-cube assets were not prepared")
        if struct.unpack_from(
            "<4H", parsed.header, HUB_SAVE_ACTOR_BANK * 8
        ) != (0, 0, 0, 0):
            raise RicoArcBuildError("Path of Sephirot save-point VRAM cell changed")
        save_actor, save_sprite = save_assets
        components[mass_driver.ACTOR_INDEX] = mass_driver._rebuild_indexed_bundle(
            components[mass_driver.ACTOR_INDEX],
            (*actor_banks, save_actor),
        )
        components[mass_driver.SPRITE_INDEX] = mass_driver._rebuild_indexed_bundle(
            components[mass_driver.SPRITE_INDEX],
            (*sprite_banks, save_sprite),
        )

    source_editor = AtelScript(components[SCRIPT_INDEX])
    header_record_count = struct.unpack_from("<H", parsed.header, 0x18C)[0]
    native_marker_record = mass_driver._field_actor_record(0x01E0, 0, 0, 0)
    native_marker_init = bytes.fromhex(
        "0B 01 80 2A FE 5E 02 80 FE 03 55 95 00"
    )
    if (
        source_editor.entity_count != HUB_SOURCE_SCRIPT_ENTITY_COUNT
        or header_record_count != HUB_SOURCE_HEADER_RECORD_COUNT
        or parsed.header[0x190 + 10 * 16 : 0x190 + 11 * 16]
        != native_marker_record
        or source_editor.get_script_pointer(10, 0) != 0x0CEA
        or source_editor.bytecode[0x0CEA : 0x0CEA + len(native_marker_init)]
        != native_marker_init
    ):
        raise RicoArcBuildError("Path of Sephirot source entity layout changed")

    triangles = _walkmesh_layer(components[1], 0)
    points = [("hub entry", *HUB_ENTRY_POSITION)] + [
        (f"chapter {marker.chapter_id} marker", marker.x, marker.z, marker.triangle)
        for marker in HUB_MARKERS
    ]
    if install_save_point:
        points.append(("memory-cube save point", *HUB_SAVE_POSITION))
    for name, x, z, triangle in points:
        if triangle >= len(triangles) or not _point_inside_triangle(
            (x, z), triangles[triangle]
        ):
            raise RicoArcBuildError(f"{name} left the Path of Sephirot walkmesh")
    effective_half_x = HUB_MARKER_HALF_WIDTH * 2 + 0x10
    effective_half_z = HUB_MARKER_HALF_DEPTH * 2 + 0x10
    entry_x, entry_z, _entry_triangle = HUB_ENTRY_POSITION
    for marker in HUB_MARKERS:
        if (
            abs(entry_x - marker.x) <= effective_half_x
            and abs(entry_z - marker.z) <= effective_half_z
        ):
            raise RicoArcBuildError("Hub entry overlaps a chapter marker")
    for index, left in enumerate(HUB_MARKERS):
        for right in HUB_MARKERS[index + 1 :]:
            if (
                abs(left.x - right.x) <= effective_half_x * 2
                and abs(left.z - right.z) <= effective_half_z * 2
            ):
                raise RicoArcBuildError(
                    f"Sephirot markers {left.chapter_id} and "
                    f"{right.chapter_id} overlap"
                )
    if install_save_point:
        save_x, save_z, _save_triangle = HUB_SAVE_POSITION
        save_effective_x = HUB_SAVE_HALF_WIDTH * 2 + 0x10
        save_effective_z = HUB_SAVE_HALF_DEPTH * 2 + 0x10
        if (
            abs(entry_x - save_x) <= save_effective_x
            and abs(entry_z - save_z) <= save_effective_z
        ):
            raise RicoArcBuildError("Hub entry overlaps the memory-cube save point")
        for marker in HUB_MARKERS:
            if (
                abs(marker.x - save_x) <= effective_half_x + save_effective_x
                and abs(marker.z - save_z) <= effective_half_z + save_effective_z
            ):
                raise RicoArcBuildError(
                    f"Chapter {marker.chapter_id} marker overlaps the memory cube"
                )

    dialogue_layout = _hub_dialogue_layout(ordered_chapters)
    save_dialogue_id: int | None = None
    if install_save_point:
        save_dialogue_id = len(dialogue_layout)
        dialogue_layout = (*dialogue_layout, HUB_SAVE_MENU_CHOICE)
    components[DIALOGUE_INDEX] = _dialogue_data(
        dialogue_layout,
        fit_windows=True,
    )
    records_to_insert = tuple(
        native_marker_record for _marker in HUB_MARKERS[1:]
    )
    if install_save_point:
        records_to_insert = (*records_to_insert, native_marker_record)
    header = _insert_dynamic_actor_records(
        parsed.header,
        old_entity_count=HUB_SOURCE_SCRIPT_ENTITY_COUNT,
        records_to_insert=records_to_insert,
    )
    if install_save_point:
        mutable_header = bytearray(header)
        struct.pack_into(
            "<4H",
            mutable_header,
            HUB_SAVE_ACTOR_BANK * 8,
            *HUB_SAVE_VRAM_MAPPING,
        )
        header = bytes(mutable_header)
    for marker in HUB_MARKERS:
        entity = HUB_MARKER_FIRST_ENTITY + marker.chapter_id - 1
        header = _place_actor_record(header, entity, marker.x, marker.z)
    if install_save_point:
        save_x, save_z, _save_triangle = HUB_SAVE_POSITION
        header = _place_actor_record(header, HUB_SAVE_ENTITY, save_x, save_z)
    header = _place_actor_record(header, 1, entry_x, entry_z)
    editor = AtelScript(
        mass_driver._extend_atel_entity_table(
            components[SCRIPT_INDEX],
            HUB_SOURCE_SCRIPT_ENTITY_COUNT + len(records_to_insert),
        )
    )
    stop_pc = editor.append_raw_routine(b"\x00")
    # Retire the ending cutscene, camera director, cast, and particle tracker.
    # Preserve only the native blue Path plane's initializer/deformation loop.
    for entity in range(editor.entity_count):
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)
    editor.set_script_pointer(
        HUB_PATH_ENTITY,
        0,
        source_editor.get_script_pointer(HUB_PATH_ENTITY, 0),
    )
    editor.set_script_pointer(
        HUB_PATH_ENTITY,
        1,
        source_editor.get_script_pointer(HUB_PATH_ENTITY, 1),
    )

    party_update_pc = editor.append_raw_routine(b"\xA7\x00")
    editor.append_and_repoint(
        1,
        0,
        _normalized_party_init(5, (entry_x, entry_z)),
    )
    editor.set_script_pointer(1, 1, party_update_pc)
    for entity in (2, 3, 4, 5, 7, 8, 9):
        editor.append_and_repoint(entity, 0, INERT_HIDDEN_INIT)
    director_pc = editor.append_raw_routine(_sanitized_director(HUB_MUSIC))
    editor.set_script_pointer(0, 0, director_pc)

    for marker in HUB_MARKERS:
        entity = HUB_MARKER_FIRST_ENTITY + marker.chapter_id - 1
        editor.append_and_repoint(entity, 0, _hub_marker_init(marker))
        action_pc = editor.bytecode_size
        editor.append_and_repoint(
            entity,
            2,
            _build_hub_marker_action(
                action_pc,
                marker,
                chapter_fields[marker.chapter_id],
                exposition_ids[marker.chapter_id],
            ),
        )

    if install_save_point:
        if save_dialogue_id is None or content_menu_field is None:
            raise RicoArcBuildError("Memory-cube menu route was not prepared")
        editor.append_and_repoint(HUB_SAVE_ENTITY, 0, _hub_save_point_init())
        editor.append_and_repoint(HUB_SAVE_ENTITY, 1, HUB_SAVE_UPDATE)
        save_action_pc = editor.bytecode_size
        editor.append_and_repoint(
            HUB_SAVE_ENTITY,
            2,
            _build_hub_save_point_action(
                save_action_pc,
                save_dialogue_id,
                content_menu_field,
            ),
        )
        save_collision_pc = editor.bytecode_size
        editor.append_and_repoint(
            HUB_SAVE_ENTITY,
            3,
            _hub_save_point_collision(save_collision_pc),
        )

    components[SCRIPT_INDEX] = editor.to_bytes()
    changed_components = (SCRIPT_INDEX, DIALOGUE_INDEX)
    if install_save_point:
        changed_components = (
            mass_driver.ACTOR_INDEX,
            mass_driver.SPRITE_INDEX,
            SCRIPT_INDEX,
            DIALOGUE_INDEX,
        )
    bundle = build_field_preserving(
        donor_bundle,
        components,
        changed_components,
        compact_changed=True,
        replacement_header=header,
    )
    reparsed = parse_field(bundle)
    if (
        tuple(part.data for part in reparsed.parts) != tuple(components)
        or len(reparsed.header) != len(header)
        or reparsed.header[0x18C:] != header[0x18C:]
    ):
        raise RicoArcBuildError("Chapter hub failed packed round-trip")
    return bundle


def _build_title_bundle(source: bytes, hub_field: int) -> bytes:
    if len(source) != TITLE_FIELD_SIZE or _sha256_bytes(source) != TITLE_FIELD_SHA256:
        raise RicoArcBuildError("Title field does not match checked USA retail data")
    parsed = parse_field(source)
    components = [part.data for part in parsed.parts]
    editor = AtelScript(components[SCRIPT_INDEX])
    if editor.bytecode[TITLE_RESULT_BRANCH_PC : TITLE_RESULT_BRANCH_PC + 8] != TITLE_RESULT_BRANCH:
        raise RicoArcBuildError("Title menu result branch changed")
    if (
        editor.bytecode[
            TITLE_ROUTE_FALLTHROUGH_PC : TITLE_ROUTE_FALLTHROUGH_PC + 8
        ]
        != TITLE_ROUTE_FALLTHROUGH
    ):
        raise RicoArcBuildError("Title New Game fallthrough changed")
    route_pc = editor.append_raw_routine(_hub_launch_body(hub_field))
    script = bytearray(editor.to_bytes())
    offset = editor.bytecode_offset + TITLE_ROUTE_FALLTHROUGH_PC
    script[offset : offset + 8] = b"\x01" + _u16(route_pc) + bytes(5)
    components[SCRIPT_INDEX] = bytes(script)
    result = build_field_preserving(
        source,
        components,
        (SCRIPT_INDEX,),
        compact_changed=True,
    )
    if tuple(part.data for part in parse_field(result).parts) != tuple(components):
        raise RicoArcBuildError("Title field failed packed round-trip")
    return result


def _build_disc2_title_overlay(source: bytes) -> bytes:
    if (
        len(source) != TITLE_OVERLAY_SIZE
        or _sha256_bytes(source) != TITLE_OVERLAY_SHA256
    ):
        raise RicoArcBuildError("Title overlay does not match checked USA retail data")
    result = bytearray(source)
    start = TITLE_EXPECTED_DISC_OFFSET
    if result[start : start + 4] != TITLE_EXPECT_DISC_1:
        raise RicoArcBuildError("Title overlay expected-disc instruction changed")
    result[start : start + 4] = TITLE_EXPECT_DISC_2
    return bytes(result)


def _build_initial_gamestate(retail_state: bytes) -> bytes:
    from modules.rico.recruitment import apply_rico_recruitment_profile
    if len(retail_state) != GAMESTATE_SIZE:
        raise RicoArcBuildError("Retail initial GameState has an unexpected size")
    if not NORMALIZED_GAMESTATE.is_file():
        raise RicoArcBuildError(
            f"Checked high-level GameState is missing: {NORMALIZED_GAMESTATE}"
        )
    staged = NORMALIZED_GAMESTATE.read_bytes()
    if (
        len(staged) != GAMESTATE_SIZE
        or _sha256_bytes(staged) != NORMALIZED_GAMESTATE_SHA256
    ):
        raise RicoArcBuildError("Checked high-level GameState identity changed")

    state = bytearray(staged)
    # The save-derived state uses runtime name strings.  loadInitialGameState
    # expects the on-disc fixed-cell catalog, so retain the exact retail region.
    state[:NAME_REGION_SIZE] = retail_state[:NAME_REGION_SIZE]
    for character in range(11):
        record = PARTY_RECORD_BASE + character * PARTY_RECORD_SIZE
        for relative in PARTY_LEVEL_OFFSETS:
            state[record + relative] = 70
        current_hp = record + 0x4C
        max_hp = record + 0x4E
        state[current_hp : current_hp + 2] = state[max_hp : max_hp + 2]
        current_mp = record + 0x50
        max_mp = record + 0x52
        state[current_mp : current_mp + 2] = state[max_mp : max_mp + 2]

    # Rico leads. Fei and Bart remain visible party members for the later arc.
    state[0x1D34:0x1D37] = bytes((5, 0, 3))
    membership = struct.unpack_from("<H", state, 0x1D30)[0]
    membership |= (
        (1 << RICO_ID)
        | (1 << YOUNG_RICO_ID)
        | (1 << 0)
        | (1 << 2)
        | (1 << 3)
    )
    struct.pack_into("<H", state, 0x1D30, membership)
    struct.pack_into(
        "<H",
        state,
        0x1D32,
        (1 << 5) | (1 << 0) | (1 << 3),
    )
    state[0x22B1:0x22B4] = bytes(3)
    struct.pack_into("<H", state, 0x1834, 0)
    struct.pack_into("<H", state, 0x1836, 0)
    struct.pack_into("<H", state, 0x1934, 0)
    struct.pack_into("<H", state, 0x1D1C, 0)  # persistent operand 0x03EC
    struct.pack_into("<H", state, 0x1D1E, 0)  # persistent operand 0x03EE
    struct.pack_into("<H", state, 0x2318, 0)
    struct.pack_into("<H", state, 0x231A, TITLE_FIELD_ID)
    struct.pack_into("<H", state, 0x2320, 0)
    state_with_deathblows = grant_all_on_foot_deathblows(bytes(state))
    balanced = apply_initial_character_balance(state_with_deathblows)
    return apply_rico_recruitment_profile(apply_young_rico_anthology_profile(balanced))


def prepare_replacements(
    disc1: DiscReader,
    chapters: Sequence[Chapter],
    *,
    content_menu_field: int | None = None,
    disc2_ancillary_fields: (
        ChapterOneAncillaryFields | Mapping[str, int] | None
    ) = None,
    disc2_chapter_two_bedroom_field: int | None = None,
) -> dict[int, list[Replacement]]:
    chapters = _ordered_hub_chapters(chapters)
    chapters_by_id = {chapter.chapter_id: chapter for chapter in chapters}
    replacements: dict[int, list[Replacement]] = {1: [], 2: []}
    ancillary_fields_by_disc = {
        1: DEFAULT_CHAPTER_ONE_ANCILLARY_FIELDS,
        2: _chapter_one_ancillary_fields(disc2_ancillary_fields),
    }
    if disc2_chapter_two_bedroom_field is not None and (
        type(disc2_chapter_two_bedroom_field) is not int
        or not 0 <= disc2_chapter_two_bedroom_field <= 0x7FFF
    ):
        raise RicoArcBuildError(
            "Disc 2 Chapter 2 bedroom field is outside 0..32767"
        )
    chapter_two_bedroom_fields = {
        1: CHAPTER_TWO_BEDROOM_FIELD,
        2: (
            CHAPTER_TWO_BEDROOM_FIELD
            if disc2_chapter_two_bedroom_field is None
            else disc2_chapter_two_bedroom_field
        ),
    }
    for disc, fields in ancillary_fields_by_disc.items():
        occupied_fields = {
            TITLE_FIELD_ID,
            HUB_FIELDS[disc],
            *CHAPTER_FIELDS[disc].values(),
        }
        ancillary_targets = {fields.firewood, fields.aftermath, fields.funeral}
        bedroom_field = chapter_two_bedroom_fields[disc]
        overlap = ancillary_targets & occupied_fields
        if overlap:
            raise RicoArcBuildError(
                f"Disc {disc} Chapter 1 ancillary fields overlap Rico's "
                f"title, hub, or chapter fields: {sorted(overlap)}"
            )
        if bedroom_field in occupied_fields or bedroom_field in ancillary_targets:
            raise RicoArcBuildError(
                f"Disc {disc} Chapter 2 bedroom field {bedroom_field} overlaps "
                "Rico's title, hub, chapter, or Chapter 1 ancillary fields"
            )
        if content_menu_field is not None and content_menu_field in ancillary_targets:
            raise RicoArcBuildError(
                f"Disc {disc} Chapter 1 ancillary fields overlap content menu "
                f"field {content_menu_field}"
            )
        if content_menu_field is not None and content_menu_field == bedroom_field:
            raise RicoArcBuildError(
                f"Disc {disc} Chapter 2 bedroom overlaps content menu field "
                f"{content_menu_field}"
            )
    if not YOUNG_RICO_PORTRAIT_TIM.is_file():
        raise RicoArcBuildError(
            f"Young-Rico menu portrait is missing: {YOUNG_RICO_PORTRAIT_TIM}"
        )
    young_rico_portrait = YOUNG_RICO_PORTRAIT_TIM.read_bytes()
    title_source = disc1.canonical(TITLE_FIELD_CANONICAL_ID)
    retail_state = disc1.canonical(INITIAL_GAMESTATE_CANONICAL_ID)
    title_atlas, title_menu = build_rico_native_title_menu(
        disc1.canonical(TITLE_MENU_CANONICAL_ID),
        young_rico_portrait,
    )
    title_graphics = patch_rico_native_title_graphics(
        disc1.canonical(TITLE_GRAPHICS_CANONICAL_ID),
        title_atlas,
    )
    initial_state = _build_initial_gamestate(retail_state)
    battle_weight = patch_battle_weight_resource(
        disc1.canonical(BATTLE_OVERLAY_CANONICAL_ID)
    )
    memento_system_data = patch_memento_system_data(
        disc1.canonical(SYSTEM_DATA_CANONICAL_ID)
    )
    young_rico_names = patch_young_rico_equipment_names(
        disc1.canonical(SYSTEM_NAMES_CANONICAL_ID)
    )
    weight_overlays = {
        canonical_id: patch_weight_mutation_overlay(disc1.canonical(canonical_id))
        for canonical_id in WEIGHT_MUTATION_OVERLAY_CANONICAL_IDS
    }
    disc2_weight_title = patch_weight_mutation_overlay(
        _build_disc2_title_overlay(
            disc1.canonical(TITLE_OVERLAY_CANONICAL_ID)
        )
    )
    native_title_overlays = {
        1: patch_rico_native_title_overlay(
            weight_overlays[TITLE_OVERLAY_CANONICAL_ID],
            expected_disc=1,
        ),
        2: patch_rico_native_title_overlay(
            disc2_weight_title,
            expected_disc=2,
        ),
    }

    donor_cache: dict[int, tuple[bytes, bytes]] = {}

    def donor(field: int) -> tuple[bytes, bytes]:
        if field not in donor_cache:
            bundle_id = _field_bundle_id(field)
            donor_cache[field] = (
                disc1.canonical(bundle_id),
                disc1.canonical(bundle_id + 1),
            )
        return donor_cache[field]

    hub_bundle_source, hub_graphics = donor(HUB_DONOR_FIELD)
    if (
        len(hub_graphics) != HUB_DONOR_GRAPHICS_SIZE
        or _sha256_bytes(hub_graphics) != HUB_DONOR_GRAPHICS_SHA256
    ):
        raise RicoArcBuildError("Path of Sephirot hub graphics changed")
    hub_save_source = (
        donor(HUB_SAVE_DONOR_FIELD)[0]
        if content_menu_field is not None
        else None
    )
    firewood_bundle_source, firewood_graphics = donor(
        CHAPTER_ONE_FIREWOOD_DONOR_FIELD
    )
    if (
        len(firewood_graphics) != CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SIZE
        or _sha256_bytes(firewood_graphics)
        != CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 firewood donor graphics changed")
    funeral_bundle_source, funeral_graphics = donor(
        CHAPTER_ONE_LIVE_FUNERAL_DONOR_FIELD
    )
    if (
        len(funeral_graphics)
        != CHAPTER_ONE_LIVE_FUNERAL_DONOR_GRAPHICS_SIZE
        or _sha256_bytes(funeral_graphics)
        != CHAPTER_ONE_LIVE_FUNERAL_DONOR_GRAPHICS_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 hillside funeral graphics changed")
    young_rico_source_bundle, young_rico_source_graphics = donor(
        CHAPTER_ONE_FIREWOOD_RICO_SOURCE_FIELD
    )
    if (
        len(young_rico_source_graphics)
        != CHAPTER_ONE_AFTERMATH_DONOR_GRAPHICS_SIZE
        or _sha256_bytes(young_rico_source_graphics)
        != CHAPTER_ONE_AFTERMATH_DONOR_GRAPHICS_SHA256
    ):
        raise RicoArcBuildError("Chapter 1 aftermath graphics changed")
    eton_source_bundle, _eton_source_graphics = donor(
        CHAPTER_ONE_ETON_SOURCE_FIELD
    )
    bedroom_source_bundle, bedroom_graphics = donor(
        CHAPTER_TWO_BEDROOM_DONOR_FIELD
    )
    if (
        len(bedroom_graphics) != CHAPTER_TWO_BEDROOM_GRAPHICS_SIZE
        or _sha256_bytes(bedroom_graphics)
        != CHAPTER_TWO_BEDROOM_GRAPHICS_SHA256
    ):
        raise RicoArcBuildError("Chapter 2 Champion-bedroom graphics changed")
    chapter_one = next(
        (chapter for chapter in chapters if chapter.chapter_id == 1),
        None,
    )
    if chapter_one is None:
        raise RicoArcBuildError("Chapter 1 is missing from the funeral build")
    chapter_two = next(
        (chapter for chapter in chapters if chapter.chapter_id == 2),
        None,
    )
    if chapter_two is None:
        raise RicoArcBuildError("Chapter 2 is missing from the bedroom build")
    battle_resources: dict[int, bytes] = {}
    for canonical_id in PLAYABLE_BATTLE_RESOURCE_IDS:
        data = disc1.canonical(canonical_id)
        if (len(data), _sha256_bytes(data)) != PLAYABLE_BATTLE_RESOURCE_IDENTITIES[
            canonical_id
        ]:
            raise RicoArcBuildError(
                f"Playable battle dependency {canonical_id} changed"
            )
        battle_resources[canonical_id] = data

    for disc in (1, 2):
        chapter_one_fields = ancillary_fields_by_disc[disc]
        chapter_two_bedroom_field = chapter_two_bedroom_fields[disc]
        if content_menu_field is None:
            hub_bundle = _build_hub_bundle(
                hub_bundle_source,
                CHAPTER_FIELDS[disc],
                chapters,
            )
        else:
            hub_bundle = _build_hub_bundle(
                hub_bundle_source,
                CHAPTER_FIELDS[disc],
                chapters,
                content_menu_field=content_menu_field,
                save_point_donor_bundle=hub_save_source,
            )
        if chapter_one_fields == DEFAULT_CHAPTER_ONE_ANCILLARY_FIELDS:
            firewood_bundle = _build_chapter_one_firewood_bundle(
                firewood_bundle_source,
                young_rico_source_bundle,
                chapter_one,
            )
            aftermath_bundle = _build_chapter_one_aftermath_bundle(
                young_rico_source_bundle,
                chapter_one,
            )
        else:
            firewood_bundle = _build_chapter_one_firewood_bundle(
                firewood_bundle_source,
                young_rico_source_bundle,
                chapter_one,
                aftermath_field=chapter_one_fields.aftermath,
            )
            aftermath_bundle = _build_chapter_one_aftermath_bundle(
                young_rico_source_bundle,
                chapter_one,
                funeral_field=chapter_one_fields.funeral,
            )
        replacements[disc].extend(
            (
                Replacement(
                    TITLE_FIELD_CANONICAL_ID,
                    "native title route to Rico chapter hub",
                    _build_title_bundle(title_source, HUB_FIELDS[disc]),
                ),
                Replacement(
                    TITLE_MENU_CANONICAL_ID,
                    "native Rico's Arc title menu and young-Rico portrait",
                    title_menu,
                ),
                Replacement(
                    TITLE_GRAPHICS_CANONICAL_ID,
                    "native Rico's Arc title-menu glyph atlas",
                    title_graphics,
                ),
                Replacement(
                    INITIAL_GAMESTATE_CANONICAL_ID,
                    "adult Rico balance and isolated young-Rico child loadout",
                    initial_state,
                ),
                Replacement(
                    BATTLE_OVERLAY_CANONICAL_ID,
                    "body-weight physical-damage and ATB mechanics",
                    battle_weight,
                ),
                Replacement(
                    SYSTEM_DATA_CANONICAL_ID,
                    "equipment data and young-Rico keepsake descriptions",
                    memento_system_data,
                ),
                Replacement(
                    SYSTEM_NAMES_CANONICAL_ID,
                    "young-Rico keepsake equipment names",
                    young_rico_names,
                ),
                Replacement(
                    _field_bundle_id(HUB_FIELDS[disc]),
                    (
                        f"Disc {disc} Path of Sephirot chapter-select field; "
                        "Chapter 1 childhood inventory gate"
                    ),
                    hub_bundle,
                ),
                Replacement(
                    _field_bundle_id(HUB_FIELDS[disc]) + 1,
                    "shared Path of Sephirot chapter-select graphics",
                    hub_graphics,
                ),
                Replacement(
                    _field_bundle_id(chapter_one_fields.firewood),
                    "Chapter 1 automatic daylight firewood scene",
                    firewood_bundle,
                ),
                Replacement(
                    _field_bundle_id(chapter_one_fields.firewood) + 1,
                    "Chapter 1 authentic Nortune exterior graphics",
                    firewood_graphics,
                ),
                Replacement(
                    _field_bundle_id(chapter_one_fields.aftermath),
                    "Chapter 1 live Anne sickness and empty-bedroom aftermath",
                    aftermath_bundle,
                ),
                Replacement(
                    _field_bundle_id(chapter_one_fields.aftermath) + 1,
                    "Chapter 1 authentic Rico childhood-room graphics",
                    young_rico_source_graphics,
                ),
                Replacement(
                    _field_bundle_id(chapter_one_fields.funeral),
                    "Chapter 1 live outskirts funeral and final blessing",
                    _build_chapter_one_live_funeral_bundle(
                        funeral_bundle_source,
                        young_rico_source_bundle,
                        eton_source_bundle,
                        chapter_one,
                        chapters_by_id[2],
                        HUB_FIELDS[disc],
                    ),
                ),
                Replacement(
                    _field_bundle_id(chapter_one_fields.funeral) + 1,
                    "Chapter 1 open hillside funeral graphics",
                    funeral_graphics,
                ),
                Replacement(
                    _field_bundle_id(chapter_two_bedroom_field),
                    "Chapter 2 optional Champion bedroom",
                    _build_chapter_two_bedroom_bundle(
                        bedroom_source_bundle,
                        chapter_two,
                        CHAPTER_FIELDS[disc][2],
                    ),
                ),
                Replacement(
                    _field_bundle_id(chapter_two_bedroom_field) + 1,
                    "Chapter 2 authentic Champion-bedroom graphics",
                    bedroom_graphics,
                ),
            )
        )
        replacements[disc].extend(
            Replacement(
                canonical_id,
                "checked Nortune Gear battle arena/stat/model dependency",
                data,
            )
            for canonical_id, data in battle_resources.items()
        )
        for canonical_id in WEIGHT_MUTATION_OVERLAY_CANONICAL_IDS:
            data = (
                native_title_overlays[disc]
                if canonical_id == TITLE_OVERLAY_CANONICAL_ID
                else weight_overlays[canonical_id]
            )
            role = "per-character weight minimum/maximum enforcement"
            if canonical_id == MAIN_MENU_OVERLAY_CANONICAL_ID:
                role += "; disabled Gear-row rendering when no party Gear exists"
            if canonical_id == TITLE_OVERLAY_CANONICAL_ID:
                role += "; one reachable native Rico's Arc title row"
                if disc == 2:
                    role += "; Disc 2 New Game expected-disc gate"
            replacements[disc].append(Replacement(canonical_id, role, data))

    # Every chapter is self-contained, so install all seven on both outputs.
    # This avoids live CD swaps: Xenogears keeps its FAT resident in memory,
    # and reading a newly inserted disc through the old table can red-screen.
    for disc in (1, 2):
        chapter_one_fields = ancillary_fields_by_disc[disc]
        chapter_two_bedroom_field = chapter_two_bedroom_fields[disc]
        for chapter in chapters:
            donor_bundle, donor_graphics = donor(chapter.donor_field)
            target_field = CHAPTER_FIELDS[disc][chapter.chapter_id]
            bundle_id = _field_bundle_id(target_field)
            if chapter_one_fields == DEFAULT_CHAPTER_ONE_ANCILLARY_FIELDS:
                scene_bundle = _build_scene_bundle(
                    donor_bundle,
                    chapter,
                    HUB_FIELDS[disc],
                    chapters_by_id.get(chapter.chapter_id + 1),
                    chapter_two_bedroom_field=chapter_two_bedroom_field,
                )
            else:
                scene_bundle = _build_scene_bundle(
                    donor_bundle,
                    chapter,
                    HUB_FIELDS[disc],
                    chapters_by_id.get(chapter.chapter_id + 1),
                    ancillary_fields=chapter_one_fields,
                    chapter_two_bedroom_field=chapter_two_bedroom_field,
                )
            replacements[disc].extend(
                (
                    Replacement(
                        bundle_id,
                        f"Chapter {chapter.chapter_id}: {chapter.title} field "
                        f"at Disc {disc} safe target {target_field}",
                        scene_bundle,
                    ),
                    Replacement(
                        bundle_id + 1,
                        f"Chapter {chapter.chapter_id}: {chapter.title} graphics",
                        donor_graphics,
                    ),
                )
            )

    from modules.rico.chapter_two import expand_replacements
    replacements = expand_replacements(
        disc1, replacements, chapters_by_id, chapter_two_bedroom_fields
    )
    for disc, items in replacements.items():
        ids = [item.canonical_id for item in items]
        if len(ids) != len(set(ids)):
            raise RicoArcBuildError(f"Disc {disc} replacement IDs overlap: {ids}")
    return replacements


def _write_replacements(
    root: Path,
    replacements: dict[int, list[Replacement]],
) -> dict[int, list[tuple[int, Path]]]:
    paths: dict[int, list[tuple[int, Path]]] = {1: [], 2: []}
    for disc, items in replacements.items():
        directory = root / f"disc{disc}"
        directory.mkdir(parents=True, exist_ok=True)
        for item in sorted(items, key=lambda value: value.canonical_id):
            path = directory / f"{item.canonical_id:04d}.bin"
            path.write_bytes(item.data)
            paths[disc].append((item.canonical_id, path))
    return paths


def _safe_link(source: Path, destination: Path) -> None:
    try:
        os.link(source, destination)
    except OSError:
        shutil.copyfile(source, destination)


def _run_xenoiso(
    *,
    disc: int,
    source: Path,
    output: Path,
    replacements: Sequence[tuple[int, Path]],
    xenoiso: Path,
    force: bool,
) -> None:
    command = [
        sys.executable,
        str(XENOISO_WRAPPER),
        "--xenoiso",
        str(xenoiso),
        "--disc",
        str(disc),
        "--source",
        str(source),
        "--output",
        str(output),
    ]
    for canonical_id, path in replacements:
        command.extend(("--replacement", f"{canonical_id}={path}"))
    if force:
        command.append("--force")
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode:
        raise RicoArcBuildError(
            f"Disc {disc} Xenoiso build failed with exit code {result.returncode}"
        )


def verify_image_replacements(
    image_path: Path,
    disc: int,
    replacements: Sequence[Replacement],
) -> None:
    """Re-extract every changed FAT entry and compare it byte-for-byte."""

    image = Mode2Image(image_path)
    entries = image.read_index()
    for replacement in replacements:
        if replacement.canonical_id == 22:
            from modules.rico.dialogue_name_color import verify_executable_image
            verify_executable_image(image_path, disc, replacement.data)
            continue
        physical = (
            replacement.canonical_id
            if disc == 1
            else replacement.canonical_id - 5
        )
        if not 0 <= physical < len(entries):
            raise RicoArcBuildError(
                f"Disc {disc} output lost canonical {replacement.canonical_id}"
            )
        actual = image.extract_entry(entries[physical])
        if actual != replacement.data:
            raise RicoArcBuildError(
                f"Disc {disc} output canonical {replacement.canonical_id} "
                "does not match its prepared replacement"
            )


def _output_identity(path: Path) -> dict[str, Any]:
    return {
        "name": path.name,
        "size": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    chapters = load_chapters(args.story_manifest.resolve())
    story = validate_story(chapters)
    from modules.rico.chapter_two_interludes import validate_graph
    story["chapter_two_expansion"] = validate_graph()
    if args.validate_only:
        return {"format": "xenogears-rico-build-v1", "story": story}

    disc_paths = {1: args.disc1.resolve(), 2: args.disc2.resolve()}
    sources = {
        disc: {
            "path": str(path),
            "size": identity[0],
            "sha256": identity[1],
        }
        for disc, path in disc_paths.items()
        if (identity := validate_disc(path, disc))
    }
    if disc_paths[1] == disc_paths[2]:
        raise RicoArcBuildError("Disc 1 and Disc 2 must be different source files")

    disc1 = DiscReader(disc_paths[1], 1)
    from modules.rico.chapter_two_resources import validate_disc_two_allocations
    validate_disc_two_allocations(DiscReader(disc_paths[2], 2).canonical)
    replacements = prepare_replacements(disc1, chapters)
    from modules.rico.release_presentation import apply_release_presentation
    replacements, presentation = apply_release_presentation(
        disc1, replacements,
        executable_sources={1: disc1.canonical(22),
                            2: DiscReader(disc_paths[2], 2).canonical(22)},
    )
    output_root = args.output.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    stage_directory = getattr(args, "stage_directory", "prepared")
    if stage_directory not in ("prepared", "stage"):
        raise RicoArcBuildError("Stage directory must be 'prepared' or 'stage'")
    prepared_root = (output_root / stage_directory).resolve()
    if prepared_root.parent != output_root:
        raise RicoArcBuildError("Stage directory resolves outside the output root")
    if prepared_root.exists() and not args.force:
        raise RicoArcBuildError(
            f"Prepared output already exists: {prepared_root}; pass --force"
        )
    if prepared_root.exists():
        # Exact generated directory only.  Source images never live below it.
        shutil.rmtree(prepared_root)
    replacement_paths = _write_replacements(prepared_root, replacements)

    manifest: dict[str, Any] = {
        "format": "xenogears-rico-build-v1",
        "story": story,
        "dialogue_presentation": presentation,
        "sources": {f"disc{disc}": value for disc, value in sources.items()},
        "replacements": {
            f"disc{disc}": [
                {
                    "canonical_id": item.canonical_id,
                    "role": item.role,
                    "size": len(item.data),
                    "sha256": _sha256_bytes(item.data),
                }
                for item in sorted(items, key=lambda value: value.canonical_id)
            ]
            for disc, items in replacements.items()
        },
    }

    if not args.prepare_only:
        if args.xenoiso is None:
            raise RicoArcBuildError("--xenoiso is required unless --prepare-only is used")
        xenoiso = args.xenoiso.resolve()
        if not xenoiso.is_file():
            raise RicoArcBuildError(f"Xenoiso executable does not exist: {xenoiso}")
        if any(character.isspace() for character in str(xenoiso)):
            raise RicoArcBuildError(f"Xenoiso path contains whitespace: {xenoiso}")

        outputs: dict[str, Any] = {}
        with tempfile.TemporaryDirectory(prefix="ricoarc_", dir=output_root) as temporary:
            link_root = Path(temporary)
            linked_sources = {
                1: link_root / "disc1_source.bin",
                2: link_root / "disc2_source.bin",
            }
            for disc in (1, 2):
                _safe_link(disc_paths[disc], linked_sources[disc])
                output = output_root / OUTPUT_BIN_NAMES[disc]
                _run_xenoiso(
                    disc=disc,
                    source=linked_sources[disc],
                    output=output,
                    replacements=replacement_paths[disc],
                    xenoiso=xenoiso,
                    force=args.force,
                )
                verify_image_replacements(output, disc, replacements[disc])
                cue = output.with_suffix(".cue")
                expected_cue = output_root / OUTPUT_CUE_NAMES[disc]
                if cue != expected_cue:
                    raise RicoArcBuildError(
                        f"Unexpected Disc {disc} CUE path: {cue}, expected {expected_cue}"
                    )
                outputs[f"disc{disc}_bin"] = _output_identity(output)
                outputs[f"disc{disc}_cue"] = _output_identity(cue)

        playlist = output_root / OUTPUT_M3U_NAME
        playlist.write_text(
            f"{OUTPUT_CUE_NAMES[1]}\n{OUTPUT_CUE_NAMES[2]}\n",
            encoding="utf-8",
            newline="\n",
        )
        outputs["playlist"] = _output_identity(playlist)
        manifest["outputs"] = outputs

    manifest_path = output_root / "rico_arc_build_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disc1", type=Path)
    parser.add_argument("--disc2", type=Path)
    parser.add_argument("--xenoiso", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "rico_arc")
    parser.add_argument(
        "--stage-directory",
        choices=("prepared", "stage"),
        default="prepared",
        help="Replacement subdirectory; legacy calls retain 'prepared'",
    )
    parser.add_argument("--story-manifest", type=Path, default=STORY_MANIFEST)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.validate_only and (args.disc1 is None or args.disc2 is None):
        parser.error("--disc1 and --disc2 are required unless --validate-only is used")
    try:
        manifest = build(args)
        if args.validate_only:
            print(
                f"Validated {manifest['story']['chapter_count']} Rico chapters "
                "and every dialogue block"
            )
        else:
            destination = args.output.resolve()
            print(f"Prepared Rico anthology at {destination}")
            if "outputs" in manifest:
                print(f"Playlist: {destination / OUTPUT_M3U_NAME}")
        return 0
    except (RicoArcBuildError, OSError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
