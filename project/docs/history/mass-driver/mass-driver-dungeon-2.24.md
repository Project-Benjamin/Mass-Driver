# Mass Driver Dungeon 2.24 - v45 Post-Save-Point Arrival Repair

> Superseded diagnosis: v45's arrival orientation is retained, but a later
> instruction-level and GPU-state reconstruction proved that the striped
> corruption was caused by a stale field-script branch enabling the
> 640-pixel renderer, not by the camera. The source repair and final evidence
> are in the v46 notes.

Version 45 repairs the west-side door after the save point and Magnetic
Conduit. It leaves the accepted v44 post-auxiliary staircase and every other
dungeon route unchanged.

## Runtime evidence

The fresh July 26 v44 state mounts
`Xenogears_PW_CD2_mass_driver_standalone_v44.cue` and has SHA-256
`913da37f61e6d58a9c10e76f75f0a0c03f1084a1f35cf1874db786314114e4e7`.
Its loaded field and entry are target 726, parameter 0, reached through the
route `725:e12 -> 726:p0`.

The transition is complete rather than frozen:

```text
Elly:             (-609.996, 0, -571)
receiving door:   entity 13 at (-617, 0, -572)
controls:         enabled
menu:             enabled
compass:          enabled
transition flag:  clear
camera eye:       (-1259.827, -491, -571)
camera target:    (-603.827, -32, -571)
```

Camera octant 2 placed the eye approximately 650 units west of Elly and
outside the hall's west wall. Looking east through the closed wall produced
the narrow white corridor strip against an otherwise black frame. The
nearby archive door and the v44 staircase are not involved in this fault.

## Scoped repair

The actor continues to face east, away from the door and into the room.
Only the camera octant changes to the unobstructed interior side:

```python
FieldEntryAddition(
    -595,
    -571,
    0,
    camera_direction=6,
    actor_direction=2,
)
```

This changes one decompressed target-726 script byte:

```text
script offset 0x08CA: 02 -> 06
entry before: AD FD C5 FD 00 02 02
entry after:  AD FD C5 FD 00 06 02
```

Target 726 parameter 2, used by the accepted v44 staircase, remains
`FieldEntryAddition(43, 602, 0, camera_direction=0, actor_direction=4)`.

## Packed change from v44

Only one of the 140 staged canonical replacements differs:

```text
canonical 2058, target 726 bundle
size: 23,240 bytes
v44 SHA-256:
421d7770c0e4c08417add9d7f48e173d1322bab74b778133b1b60df21a401ce2
v45 SHA-256:
97e2f48f6c38b30fced09e82fefafe963ba9bd5a3227f7d2ee223e24a92b484e
```

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v45.bin

BIN size: 693,263,760 bytes
raw sectors: 294,755
BIN SHA-256:
0dd192a073bc92bea080fce87f476ee73da63d82c46724a7571e4208668a1763

CUE SHA-256:
06dfcb63621cb6c083ca55ff8bb6893facfe6bb0e9041880d6881e9304fc25cd

packed staged replacement comparison:
140/140 exact, totaling 8,152,642 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 149 passed, 1,891 subtests passed
```

These checks establish script, packing, and image integrity. A fresh
cold-boot traversal remains the runtime acceptance test.

## Focused manual acceptance

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and confirm the title says
   v45.
3. Choose New Game. Do not load an F1/F2 state created with v44; it restores
   the v44 image and already-loaded v44 field script.
4. Reach the save point and Magnetic Conduit, then use the west door that
   leads into target 726.
5. Confirm the native door animation and sound complete.
6. Confirm the hall renders normally, Elly faces forward into it, and
   movement remains enabled. The previous black frame with a narrow white
   corridor strip must not appear.
7. Turn around and use entity 13. Confirm it returns through the same door
   into target 725.
8. Confirm the separate post-auxiliary staircase still enters its full
   stairwell and reaches target 726 normally.
9. If a step fails, press F2 immediately before X, press X once, then press
   F2 again while the fault is visible. Keep the screenshot and both state
   generations.
