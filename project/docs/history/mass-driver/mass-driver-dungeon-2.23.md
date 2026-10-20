# Mass Driver Dungeon 2.23 - v44 Post-Auxiliary Stair Repair

Version 44 repairs the north external door immediately after the
auxiliary-power room. It restores the missing full staircase, keeps the
already accepted archive-F staircase independent, and removes the receiving
hall's wall-clipped camera.

## Runtime evidence

The fresh v43 F2 generations both identify the mounted image as
`Xenogears_PW_CD2_mass_driver_standalone_v43.cue`.

The pre-door generation is target 372. Elly is at `(8, 1195)`, immediately
south of entity 22 at `(4, 1230)`. Entity 22 is running its native door action,
and that action ends in `CHANGE_FIELD 726, parameter 2`.

The post-door generation is a completed target-726 load at parameter 2, not a
stalled VM or field transition:

```text
Elly:             (43, 602)
receiving door:   entity 15 at (43, 632)
controls:         enabled
compass:          enabled
camera eye:       (43, -491, 1258)
camera target:    (43, -32, 602)
```

The camera was 626 units beyond the closed north door and wall, looking
through both toward the party. That accounts for the white-and-black clipped
frame. The route was also semantically wrong because it bypassed the
staircase the door was supposed to enter.

## Independent stair routes

Disc 2 field 375's canonical entries `1356/1357` were allocated 24-byte
CDMAKE dummy files and had no transition references in the standalone route.
They can therefore safely host a second transformed copy of Disc 1 source
field 375 without displacing another room.

The post-auxiliary branch is now:

```text
372:e22 -> 375:p0
375:e12 -> 372:p2
375:e13 -> 726:p2
726:e15 -> 375:p1
```

The accepted archive-F branch remains:

```text
371:e22 -> 723:p0
723:e12 -> 371:p0
723:e13 -> 726:p8
726:e24 -> 723:p1
```

Both stairwells retain source 375's complete geometry, walkmesh, native
sliding doors, sound, helper animation, and bounded party movement. They use
separate target fields, entry parameters, and reciprocal door contracts.

## Wall-safe target-726 arrival

Target 726 parameter 2 remains thirty units inside entity 15's north door.
Its final seven-byte field entry is:

```python
FieldEntryAddition(
    43,
    602,
    0,
    camera_direction=0,
    actor_direction=4,
)
```

Actor octant 4 faces Elly south, away from the door and into the room.
Camera octant 0 places the eye near `(43, -491, -54)`, on the room-interior
side of the north wall. This is the one audited arrival where camera and
actor octants deliberately differ.

## Packed changes from v43

```text
canonical 1350, target 372 bundle
size: 36,720 bytes
SHA-256:
eaf16ee82731366a1fef80e8f97f2abc45b99a9a42dae9963186a4582e5609e0

canonical 1356, new target 375 bundle
size: 98,312 bytes
SHA-256:
02dec0f400cda157f278f8f1daa59ecdb2caf3ffebd06973b4f967e861cef9ed

canonical 1357, new target 375 graphics
size: 262,144 bytes
SHA-256:
75497ba4eca6ff580ba1259a5bdcb50e5a343ee474490d748a553c8f13e844a2

canonical 2058, target 726 bundle
size: 23,240 bytes
SHA-256:
421d7770c0e4c08417add9d7f48e173d1322bab74b778133b1b60df21a401ce2
```

Target 375's transformed script is 1,644 bytes with SHA-256
`d76bfb2916e1c9719d98478d759ed1bf1842645b3f4381d2238270f668f13074`.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v44.bin

BIN size: 693,263,760 bytes
raw sectors: 294,755
BIN SHA-256:
9ef2e79ed682483f46322ecd9541c6f3441ccc237e46b393683c64de8c937686

CUE SHA-256:
cc11622bc9c453d63a2f95d94799864fe8e61c5ddd84ac161de61ffcc55ff464

packed staged replacement comparison:
140/140 exact, totaling 8,152,642 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 149 passed, 1,891 subtests passed
```

These checks establish route, script, packing, and image integrity. The
following cold-boot traversal remains the runtime acceptance test.

## Focused manual acceptance

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and confirm the title says
   v44.
3. Choose New Game. Do not load an F1/F2 state created with v43; it restores
   the v43 image and already-loaded v43 field scripts.
4. Restore auxiliary power, return to target 372, and go through the north
   external door immediately after the auxiliary-power route.
5. Confirm the door plays its native slide and sound, carries the party
   through the threshold, and enters the complete inclined sealed stairwell.
6. Cross the stairwell and use its far door.
7. Confirm target 726 appears normally beside entity 15, Elly faces away
   from the door, the camera does not show striped or clipped geometry, and
   movement remains enabled.
8. Turn around and use entity 15. Confirm it returns through the same
   staircase and exits back into target 372.
9. If any step fails, press F2 immediately before X, press X once, then press
   F2 again while the fault is visible. Keep the screenshot and both state
   generations.
