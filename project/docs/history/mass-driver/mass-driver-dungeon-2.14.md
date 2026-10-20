# Mass Driver Dungeon 2.14 - v35 Archive Annexes

Version 35 turns the Mass Driver's eight remaining decorative service panels
into accessible mechanical doors. One panel is in target field 363 and seven
are in target field 726. Every panel leads to a different one-room archive
annex, so no visible door is backed by a shared substitute room.

This is a release candidate pending in-game acceptance. The packed disc and
its field resources have been verified structurally; the new doors and rooms
still require the manual runtime checks below.

## New room graph

```text
363 <-> 365

726 <-> 366
726 <-> 367
726 <-> 368
726 <-> 369
726 <-> 370
726 <-> 371
726 <-> 724
```

Targets 365-371 and 724 each clone the source-378 Zeboim archive room. Each
annex has its own checked entry parameter, a placeholder record console, and
a reciprocal native animated return door. The placeholder messages reserve
independent record slots without treating draft exposition as final script.

The expanded standalone dungeon now contains 24 target fields:

```text
729, 364, 360, 720, 721, 363, 362, 727, 372, 361, 722, 723,
387, 725, 726, 365, 366, 367, 368, 369, 370, 371, 724, 728
```

## Door behavior

Each newly active panel is X-operated. Its controller:

1. enters the normal cinematic interaction state;
2. plays the door sound once;
3. runs a finite 32-step hinged model rotation;
4. moves the party through the audited walkmesh pocket; and
5. performs the checked field transition.

The finite animation cannot wait forever for an unbounded model state.
Collision callbacks remain STOP, so merely touching a closed panel does not
teleport the party.

The eight annex return doors retain the source room's native animation and
sound. Every directed arrival has an explicit player position, walkmesh
layer, actor direction, and camera direction. Returning from an annex places
the party in front of the panel it used, facing into the larger room with the
door behind it.

Across the complete dungeon, 38 external mechanical sides form 19 reciprocal
room pairs. Target 372 retains its four local action sides, producing 42
mechanical controls in total. The route has 48 directed field arrivals plus
the world-map entrance, all with explicit continuity.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v35.bin

BIN size: 692,854,512 bytes
raw sectors: 294,581
BIN SHA-256:
0d6263ea85b3277038e09bd4293f83875f3f98ed4070148fd2d9aaa761914b70

packed staged replacement comparison:
138/138 exact, totaling 7,793,266 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 141 passed, 1,641 subtests passed
```

All 138 staged replacement files were re-extracted from their packed
canonical entries and compared byte for byte. Runtime acceptance is not
claimed before the manual checks complete.

## Manual acceptance

Cold-boot v35 so the emulator cannot retain a previously loaded v34 field
script in RAM.

1. Close DuckStation and run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Enter the Mass Driver normally and reach target 363 after the employee
   subway platform.
3. Use its formerly decorative panel with X. Confirm one door sound, the
   complete hinged opening, transition into target 365, and normal player
   control.
4. Read the annex console. Confirm the placeholder record closes normally
   and does not award an item or alter the route.
5. Use the annex's animated return door. Confirm target 363 reloads with the
   party facing forward and the used panel behind it.
6. Reach target 726 and repeat the same check for all seven formerly
   decorative panels. Each must enter a different target among 366-371 and
   724, and every annex return door must restore the matching side of target
   726.
7. Confirm no panel opens into another panel's annex, no door transition
   freezes, no door sound loops, and the camera never leaves the party facing
   back into the door it just exited.
8. Recheck the pre-v35 objective route through targets 361, 722, 725, 726,
   and 728 to confirm the eight optional annexes do not disturb auxiliary
   power, authorization, the rail interlock, the boss, or Central Control.
