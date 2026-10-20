# Standalone Mass Driver exploration dungeon

## Scope

This document describes the v13 structure-first, standalone, combat-free
reconstruction of the Zeboim Mass Driver Facility. Cold boot uses target field
728 as a hidden black gateway, then places Elly and Emeralda on the playable
world map immediately outside the native Mass Driver landmark. No save file,
retail story scene, field-617/618 hook, or late-game progression flag is
required.

The implemented completion boundary is the full standalone traversal: enter
the existing world-map Mass Driver, operate the moving inclined lift, cross
two underground approach tunnels and the employee subway/platform, pass
through a service vestibule and pressure-transfer airlock, explore every
connected facility branch, operate the two structural interlocks, reach
Central Control, backtrack through its visible door, or return outside from
its console.

Random battles, a boss battle, finished character writing, lore exposition,
and retail-story integration are intentionally out of scope for this version.
Every active authored dialogue block currently reads **TEMPORARY PLACEHOLDER**.
The stable block IDs and physical interaction points remain in
place so writing can be replaced later without redesigning the dungeon.

This is an original fan reconstruction using released Xenogears resources. It
is not recovered or official cut-content data.

## Playing

Double-click `output/PLAY_MASS_DRIVER_STANDALONE.cmd`. The launcher cold-boots
`output/Xenogears_PW_CD2_mass_driver_standalone_v13.cue` and requires no memory
card.

The rebuilt BIN is 690,288,480 bytes with SHA-256
`b9a50edc9e06636e2e9fbde6ea5c1a23d8c1a35348604bc9826e844248d41492`.
All 36 manifest-listed replacements were re-extracted from the final image
and matched the staged files exactly.

Approach the native Mass Driver complex until the **Mass Driver** label
appears and press **X** (Cross). The included portable DuckStation keyboard
profile maps X to `K`. The patched handlers accept X on the world map and in
fields; unchanged retail Circle paths remain accepted where the original
handlers support them.

## Active graph

The exact 16-target build order is:

```text
729, 364, 360, 720, 721, 363, 362, 727,
372, 361, 722, 723, 387, 725, 726, 728
```

The ordered approach is:

```text
world map -> 729 <-> 364 <-> 360 <-> 720 <-> 721
                                                |
                                                v
                                  363 <-> 362 <-> 727
```

- 729 is the native upper half of the moving inclined surface lift.
- 364 continues the same native lift to its actual lower landing.
- 360 and 720 are exactly two underground tunnel screens.
- 721 is the stationary subway/platform room.
- 721's far passage enters target 363 automatically and has no X prompt.
- 363 is an open subway-side vestibule with one mechanical facility door.
- 362 is source 376's two-door Zeboim personnel pressure-transfer airlock.
- 727 is a three-door operations junction with fixed destinations.

The facility is a connected, backtrackable graph:

```text
                                  361 control annex
                                   |
                                   |
362 <-> 727 <-> 372 <------------+------------> 722 storage annex
         |          |
         |          +<-> 723 <-> 726 <-> 728
         |                         ^
         +<-> 387 <-> 725 <--------+
```

Target 728's entity-13 console returns to world-map position 21. Its visible
entity-14 door instead returns to target 726 parameter 1.

Equivalent reciprocal edge list:

```text
729 <-> 364
364 <-> 360
360 <-> 720
720 <-> 721
721 <-> 363
363 <-> 362
362 <-> 727
727 <-> 372
372 <-> 361
372 <-> 722
372 <-> 723
723 <-> 726
727 <-> 387
387 <-> 725
725 <-> 726
726 <-> 728
```

These 16 reciprocal room links produce 32 directed route edges. The world-map
entry into target 729 and target 728's explicit outside-return console are
the two traversal operations outside that field-to-field graph.

## Audited room provenance

| Target | Canonical bundle/graphics | Area | Retail donor | Asset family |
| ---: | --- | --- | ---: | --- |
| 729 | 2064 / 2065 | Inclined-lift upper half | 361 | Disc 1 Ethos/Zeboim ruins |
| 364 | 1334 / 1335 | Inclined-lift continuation and lower landing | 362 | Disc 1 Ethos/Zeboim ruins |
| 360 | 1326 / 1327 | Curved employee-transit tunnel | 398 | Lighthouse underground, on foot |
| 720 | 2046 / 2047 | Coastal utility tunnel | 399 | Lighthouse underground, on foot |
| 721 | 2048 / 2049 | Abandoned subway terminus | 397 | Lighthouse underground, on foot |
| 363 | 1332 / 1333 | Open subway-side service vestibule | 363 | Disc 1 Ethos/Zeboim ruins |
| 362 | 1330 / 1331 | Personnel pressure-transfer airlock | 376 | Disc 1 Ethos/Zeboim ruins |
| 727 | 2060 / 2061 | Three-door operations junction | 377 | Disc 1 Ethos/Zeboim ruins |
| 372 | 1350 / 1351 | Four-boundary/eight-control service hub | 372 | Disc 1 Ethos/Zeboim ruins |
| 361 | 1328 / 1329 | Control/research annex | 373 | Disc 1 Ethos/Zeboim ruins |
| 722 | 2050 / 2051 | Materials-storage annex | 374 | Disc 1 Ethos/Zeboim ruins |
| 723 | 2052 / 2053 | Sealed stair connector | 375 | Disc 1 Ethos/Zeboim ruins |
| 387 | 1380 / 1381 | Stacked two-level connector | 387 | Disc 1 Ethos/Zeboim ruins |
| 725 | 2056 / 2057 | Magnetic conduit hall | 385 | Disc 1 Ethos/Zeboim ruins |
| 726 | 2058 / 2059 | Launch-support hall and interlocked door | 384 | Disc 1 Ethos/Zeboim ruins |
| 728 | 2062 / 2063 | Mass Driver Central Control | 369 | Disc 1 Ethos/Zeboim ruins |

Targets 360-364, 372, and 387 occupy canonical Disc 2 field slots whose
bundle/graphics pairs were verified as 24-byte `It's CDMAKE Dummy !`
placeholders. The remaining targets use allocated retail debug-room slots
720-729. Target 724 and source 382 are not part of v13.

Every facility donor is from the Disc 1 Ethos Dig Site/Zeboim ruins.
Lighthouse resources are limited to the two transit tunnels and the
stationary employee subway/platform. Moving-train field 197 is excluded, and
no rail ride occurs. The active route contains no Solaris, Krelian, or Anima
Relic donor room, character, or technology.

## Inclined lift and approach

Target 729 uses source field 361, not source field 386. Source 361 contains
the upper half of the native diagonal mechanism shown by the inclined-lift
reference. The build retains its control action, motor SFX, cinematic state,
original 30-step movement loop, and custom transition. That transition loads
target 364, a clone of source field 362, because the released lift is a
paired-field mechanism rather than one artificially extended field.

Target 364 continues the descent for source 362's native 15 movement steps.
Its released landing sequence stops the lift SFX and clears the platform's
motion velocity before control returns at the real bottom of the shaft. Only
after that landing does the far threshold enter target 360. The one-frame SFX
stop retained on target-360 entry is a defensive fail-safe after the completed
landing; it does not cancel the mechanism midway.

The reverse path retains the same paired mechanism. Target 360's lift-side
exit loads target 364 parameter 1. The lower control runs the source-362
ascent and transitions to target 729 parameter 1, where source 361 completes
the upper half. Source field 386's vertical/deep elevator is absent from the
active clone set.

Targets 360 and 720 are exactly two Lighthouse underground tunnel screens.
Target 721 supplies the static employee subway terminus. The existing
field-397 platform chest remains a repeatable physical interaction and awards
no item; its active text is currently a placeholder. The far threshold enters
target 363 parameter 0 automatically, without dialogue confirmation or an X
press.

## Vestibule and airlock

Target 363 clones source 363 and supplies the transition that was missing
between the open subway landing and the mechanical airlock:

- entity 14 is an already open passage that returns to target 721 parameter
  1;
- entity 13 is a visible Zeboim mechanical door that enters target 362
  parameter 0.

Target 362 clones source 376's personnel pressure-transfer airlock:

- entity 14 is the north mechanical door and returns to target 363 parameter
  1;
- entity 15 is the south mechanical door and enters target 727 parameter 2;
- target 727 entity 14 supplies the reciprocal south-side door and returns to
  target 362 parameter 1.

This produces a coherent sequence:

```text
stationary subway -> open vestibule -> mechanical door
                  -> pressure-transfer airlock -> operations junction
```

The subway/vestibule boundary is visibly open and automatic on both sides.
Every boundary after it that is modeled as a closed Zeboim door requires X
and runs its door mechanism.

## Service hub, annexes, and launch loop

Target 727's three native mechanical doors have fixed destinations:

| Target 727 door | Destination |
| --- | --- |
| entity 12 | target 387 parameter 0 |
| entity 13 | target 372 parameter 0 |
| entity 14 | target 362 parameter 1 |

Target 372 is source 372's large service hub. It preserves four external
mechanical boundaries and four local door-action sides:

| Target 372 control | Function |
| --- | --- |
| entity 16 | return to target 727 parameter 1 |
| entity 17 | first local paired passage |
| entity 18 | reciprocal side of the first local passage |
| entity 19 | second local paired passage |
| entity 20 | reciprocal side of the second local passage |
| entity 21 | target 361 parameter 0 |
| entity 22 | target 723 parameter 0 |
| entity 23 | target 722 parameter 0 |

Helpers 24-31 remain assigned to those eight visible mechanisms. Entity 19
now stops immediately after operating its paired local doors, before the
donor's released-story party sequence.

The external return mapping uses a distinct physical arrival for every hub
door:

- target 361's return door enters target 372 parameter 1 beside entity 21;
- target 723's hub-side door enters target 372 parameter 2 beside entity 22;
- target 722's return door enters target 372 parameter 3 beside entity 23;
- target 372 entity 16 enters target 727 parameter 1 beside entity 13.

Target 387 preserves source 387's stacked connector. Its two doors share the
same horizontal coordinates but occupy separate walkmesh layers:

- entity 12 and parameter 0 use walkmesh 0 and connect to target 727;
- entity 13 and parameter 1 use walkmesh 1 and connect to target 725.

The launch-side loop is:

```text
727 <-> 387 <-> 725 <-> 726
 \                         /
  +<-> 372 <-> 723 <------+
```

Target 723's far door enters target 726 parameter 2. V13 retains that third
seven-byte entry record at `(43, 602)` on walkmesh 0, inside triangle 29 and
beside target 726 entity 15. Entity 15 animates the reciprocal door and
returns to target 723 parameter 1. This removes the old wrong-side spawn and
the visual door/hole mismatch.

## Arrival and camera continuity

The 32 directed room links and the world-map entrance use 33 unique receiving
field parameters. Every active seven-byte entry record contains an explicit
actor direction and camera direction; neither byte is allowed to inherit the
previous scene's saved heading. Xenogears places the camera eye behind the
party when both bytes use the same world-facing octant, so every receiving
record uses the same value for both.

Mechanical-door arrivals are validated geometrically. The builder reads the
forced outbound player waypoint from the reciprocal door action, compares it
with the receiving spawn, and requires the actor/camera octant to point from
that door into the room. The Lighthouse thresholds and paired inclined-lift
handoffs have explicit audited route-forward directions. The curved source-398
tunnel uses its southwest inward diagonal. The equal-coordinate entries in
targets 723 and 387 remain distinct through their separate walkmesh layers.

## Door and boundary semantics

The facility contains 22 external mechanical door sides forming 11 reciprocal
room pairs:

```text
363 <-> 362
362 <-> 727
727 <-> 372
372 <-> 361
372 <-> 722
372 <-> 723
723 <-> 726
727 <-> 387
387 <-> 725
725 <-> 726
726 <-> 728
```

Target 372 contributes four additional local action sides, entities 17-20,
which operate two paired in-room passages. All 26 mechanical action sides use
the same checked behavior:

```text
X action -> cinematic lock -> door SFX -> field-model helper animation
         -> blocking movement and reciprocal transition, or local opening
```

Every corresponding collision callback remains STOP. Touching a closed door
therefore cannot skip the sound, animation, movement, lock check, or X input.
No visible mechanical door is parked to force a linear route, and no active
mechanical door is a bare X-to-field teleport.

Open passages do not pretend to be mechanical doors. The tunnel endpoints,
the subway threshold, and the target-721/363 open boundary remain automatic
on contact. The inclined lift uses its own complete native control and
movement sequence.

Target 726 has three distinct door-side arrivals:

| Parameter | Position/layer | Connected visible door |
| ---: | --- | --- |
| 0 | `(-595, -571)`, walkmesh 0 | entity 13, target 725 side |
| 1 | `(441, -590)`, walkmesh 0 | entity 14, target 728 side |
| 2 | `(43, 602)`, walkmesh 0 | entity 15, target 723 side |

Target 728's entity-14 door returns to target 726 parameter 1 with the same X,
sound, helper-animation, movement, and STOP-collision contract. Returning
outside is deliberately separate: entity 13 is the checked console action
that invokes world-map position 21.

## Placeholder text and structural interlocks

All active authored dialogue documents use clearly marked
`TEMPORARY PLACEHOLDER` text. This includes room-entry windows, the subway chest,
facility controls, optional physical props, locked-door feedback, and the
target-728 outside-return console. No current line should be treated as final
Elly dialogue, final Emeralda dialogue, research prose, lore exposition, or a
finished ending.

The stable structure retained for later writing is:

- target 721: one repeatable platform-chest interaction;
- target 361: physical optional controls and the auxiliary-interlock action;
- target 722: two optional physical interactions;
- target 725: the accelerator-rail interlock action;
- target 728: physical optional interactions and the entity-13 completion
  console.

The shared persistent operand is `0x03FE`, the final audited field-variable
word copied through GameState. Bit 0 records the target-361 auxiliary
interlock; bit 1 records the target-725 accelerator-rail interlock. The
physical controls set their bits independently of the placeholder prose.

Target 726 owns the actual structural gate. Its entity-14 door checks both
masks, remains closed if either is missing, and runs its full sound/helper
animation before entering target 728 when both are present. Target 727 never
reroutes its doors based on progression.

## Retail world-map provenance

Canonical world-map entry 4052 already contains the visible Mass Driver
exterior. It is composed of placement records 59-62 and native model blocks
48-51. Those assets are retained, as is English label 21, `Mass Driver`.

Dormant retail world-map bundles 4118, 4129, and 4140 preserve matching
missing-location metadata:

| Retail datum | Value |
| --- | --- |
| Initial position | index 21 at `(30163, 16396)` |
| Location rectangle | `(29880, 16287)`, width `202`, height `214` |
| Label | 21, `Mass Driver` |
| Dormant destination | unfinished field-0 placeholder |

The standalone build creates this reachable checked entry:

| Active datum | Value |
| --- | --- |
| Initial position | index 21 at `(30192, 16396)` |
| Interaction apron | `(29880, 16287)`, width `288`, height `214` |
| Outside approach | 24 world units east of the apron |
| Input | X (Cross), keyboard `K` in the portable profile |
| Destination | target field 729, parameter 0 |

Taura's house remains separate: placement record 51 still uses block 41, and
its on-foot and Gear rectangles still target field 614 with label 20,
`Torah's House`. No house model, label, trigger, or destination is
repurposed.

## Consistent X / Cross controls

Two checked executable overlays make X a consistent confirmation and
interaction button without removing retail Circle:

- Canonical field overlay 36 widens five MIPS masks from `0x20` to `0x60` at
  decoded offsets `0x106F8`, `0x108AC`, `0x13FC8`, `0x14184`, and `0x14458`.
- Canonical world-map overlay 37 widens the checked on-foot landmark mask from
  `0x20` to `0x60` at decoded offset `0x210A4`.
- X activates the native Mass Driver landmark and physical controls/doors.
- Traversal through open tunnel, subway, and vestibule boundaries remains
  automatic on contact; these boundaries do not add an X prompt.

## Standalone architecture

- The executable's checked New Game dispatch changes from retail boot mode 6
  to field mode 1.
- Canonical GameState entry 2595 stages Elly and Emeralda and cold-boots
  target 728 with entry parameter 0.
- Target 728 is both Central Control and the cold-bootstrap gateway. The
  prepared GameState clears retail previous-field operand 4. On cold boot,
  the field director blacks the display before the first rendered frame,
  holds through the 32-frame loader reveal window, then calls
  `WORLD_MAP(21, 1)`.
- A normal room transition into target 728 comes from target 726.
  `SaveFieldAndDirections` writes previous-field value `726`; target 728
  distinguishes that arrival from cold boot and runs only its normal
  placeholder entry scene.
- Target 728 entity 14 is a reciprocal animated door to target 726 parameter
  1. Entity 13 is a separate X-activated console that returns outside.
- Canonical world-map entry 4052 retains the native Mass Driver and Taura
  models, adds a reachable position-21 spawn and interaction apron, and sends
  the landmark directly to target 729.
- Target 729 is a pure landmark destination using the source-361 upper lift.
  The lift remains a physical native control and keeps its released 30-step
  motion before entering target 364 through its cinematic field transition.
- Target 364 clones source 362 as the paired 15-step continuation and actual
  lower landing. Its native sequence stops the lift SFX and clears platform
  velocity before control returns. Its far threshold reaches target 360.
- Target 360 returns to target 364 parameter 1. The native reverse sequence
  then reaches target 729 parameter 1. Target 360's entry SFX stop remains
  only as a post-landing fail-safe.
- Targets 360 and 720 are the only two tunnel screens. Target 721 is the
  stationary platform, and its far collider enters target 363 automatically.
- Target 363 supplies the open vestibule before target 362's two-door
  personnel pressure-transfer airlock.
- Target 727 has three fixed doors to targets 362, 372, and 387. No dynamic
  hub-gate action is installed.
- Target 372 supplies four external route doors and four local action sides.
- Target 387 supplies the stacked target-727/725 connector.
- Target 726 supplies three distinct arrivals, including parameter 2 for the
  target-723 door.
- The current donor list is `361, 362, 398, 399, 397, 363, 376, 377, 372,
  373, 374, 375, 387, 385, 384, 369`.
- The implementation uses no legacy interaction-prompt route exit.

## Building

The user supplies legally obtained US Disc 1 and Disc 2 images. Original disc
images are never modified in place.

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_standalone_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v13.bin
```

Run the automated suite with:

```powershell
python -m pytest -q
```

The Disc 1 image supplies only extracted Zeboim donor resources; the playable
image is built from Disc 2.

## Graph release validation

### Automated contract

The v13 builder and tests must verify:

- world-map position 21 enters target 729 parameter 0;
- the exact 16-target order is `729, 364, 360, 720, 721, 363, 362, 727,
  372, 361, 722, 723, 387, 725, 726, 728`;
- the graph contains the 32 directed edges represented by the 16 reciprocal
  pairs in this document;
- all 32 directed edges plus the world-map entry have unique receiving
  parameters with explicit, matched actor/camera octants;
- every mechanical arrival faces from its reciprocal door waypoint into the
  receiving room, leaving the door behind the party;
- target 729 uses source 361, retains its native 30-step upper motion, and
  preserves its cinematic transition into target 364;
- target 364 uses source 362, retains the 15-step descent continuation and
  native landing SFX/velocity cleanup, and reaches target 360 only from its
  far threshold;
- target 360 returns to target 364 parameter 1, whose native ascent reaches
  target 729 parameter 1;
- source 386 is absent from the active clone set;
- 360 and 720 are exactly two tunnel screens;
- target 721's far threshold is collision-driven, has no prompt, and enters
  target 363 parameter 0;
- target 363's open entity-14 side returns to target 721 parameter 1;
- target 363's entity-13 mechanical door enters target 362 parameter 0;
- target 362 uses source 376, not source 362;
- target 362's entity-14 and entity-15 doors reach targets 363 parameter 1
  and 727 parameter 2;
- all three target-727 doors retain fixed destinations to targets 387, 372,
  and 362;
- target 372 retains external entities 16 and 21-23 plus local entities
  17-20 and helpers 24-31;
- targets 361, 722, and 723 clone sources 373, 374, and 375;
- target 387 uses source 387 and preserves its separate mesh-0 and mesh-1
  door arrivals;
- target 726 parameter 2 is `(43, 602)` on walkmesh 0 and is used by target
  723's far door;
- the target-361 and target-725 controls set persistent interlock bits 0 and
  1 independently of their placeholder dialogue;
- target 726 entity 14 remains locked until both bits are set, then animates
  into target 728 parameter 0;
- target 728 entity 14 animates back to target 726 parameter 1;
- target 728 entity 13 returns to world-map position 21;
- all 22 external mechanical sides and all four local sides use X, door SFX,
  a non-STOP model helper, and STOP collision behavior;
- no transition leaves the allowed graph;
- every active authored dialogue document contains clearly marked temporary
  placeholder text;
- source 382, train field 197, Solaris, Krelian, and Anima Relic content are
  excluded.

### Runtime acceptance

Start from a fresh cold boot and verify:

1. No Central Control frame appears before the world map.
2. The party begins outside the native Mass Driver; its label appears and X
   enters target 729.
3. Target 729 is the inclined lift, not the vertical/deep elevator.
4. Activating the lift plays its motor and completes target 729's native
   30-step upper descent before target 364 loads.
5. Target 364 continues the same descent for 15 native movement steps, reaches
   the visible lower landing, stops the motor, and clears platform velocity
   before returning control.
6. Crossing target 364's far threshold enters target 360. Returning through
   target 360 loads target 364 parameter 1, and the native ascent reaches
   target 729 parameter 1.
7. Exactly targets 360 and 720 serve as tunnel screens before the stationary
   subway/platform in target 721.
8. The existing platform chest is repeatable, displays placeholder text, and
   awards no item.
9. Crossing the far platform threshold loads target 363 parameter 0 without
   an X prompt.
10. Target 363's open side returns automatically to target 721 parameter 1,
    while its visible mechanical door animates into target 362 parameter 0.
11. Target 362's north door animates into target 363 parameter 1; its south
    door animates into target 727 parameter 2.
12. All three target-727 doors are usable and always lead to targets 387,
    372, and 362. Its entity-14 door returns to target 362 parameter 1.
13. All four target-372 external doors are usable and reciprocal. Entities
    17-20 each operate their paired local passage with sound and animation.
14. The source-373 and source-374 annex return doors animate to target 372
    parameters 1 and 3 respectively.
15. Target 723 returns to target 372 parameter 2 and reaches target 726
    parameter 2 through its other animated door.
16. Target 387 can be crossed between its separate lower and upper walkmesh
    layers; both doors animate and backtrack correctly.
17. Both target-361 and target-725 physical controls set their interlock bits
    even though their text is temporary.
18. Both routes into target 726 can be traversed and backtracked. Parameter 2
    places the party inside entity 15's north door rather than at another
    entrance.
19. Target 726's Central Control door remains closed when an interlock is
    missing, then plays sound and animation into target 728 after both are
    active.
20. Target 728's visible door animates back to target 726 parameter 1.
21. Target 728's entity-13 console, not the room door, returns the party to
    world-map position 21.
22. Every active authored window is visibly marked as temporary placeholder
    text; no prose is evaluated as final narrative in this release.

If scripted emulator movement cannot reliably operate a door or reach a
specific branch, use a human playthrough for that acceptance step and record
the exact field, entrance, door, and observed result rather than guessing from
automated input.
