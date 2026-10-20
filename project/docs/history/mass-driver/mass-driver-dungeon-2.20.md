# Mass Driver Dungeon 2.20 - v41 Archive Stair Route

Version 41 changes the archive route so the door beside Elly enters the
existing sealed stairwell before reaching the save-point hall. The route is
fully reciprocal and retains the native door presentation, walking contract,
arrival positions, and camera orientation established in v40.

## Screenshot identification

The three July 26 screenshots identify the requested endpoints:

- `Xenogears (Disc 2) 2026-07-26-08-46-49.png` is target 371, the archive
  annex. Elly is beside its only return door, entity 22.
- `Xenogears (Disc 2) 2026-07-26-08-47-00.png` is target 726, the save-point
  hall and the area that should follow the staircase.
- `Xenogears (Disc 2) 2026-07-26-08-46-41.png` is the target-726 entity-24
  door-opening/corruption frame, not a separate destination room.

The F2 states captured earlier represented a different crossing and were not
used to infer this route.

## Reciprocal route

The requested forward path is now:

```text
target 371 archive annex, entity 22
    -> target 723 sealed stairwell, parameter 0
target 723, entity 13
    -> target 726 save-point hall, parameter 8
```

The return path is:

```text
target 726 save-point hall, entity 24
    -> target 723 sealed stairwell, parameter 1
target 723, entity 12
    -> target 371 archive annex, parameter 0
```

This uses the complete existing staircase field instead of bypassing it with
a direct target-371/target-726 transition.

Target 723 was already an active connector and there was no unused safe field
slot. Its displaced connections therefore remain reachable as direct,
reciprocal door pairs:

```text
target 372 entity 22 <-> target 726 entity 15
target 727 entity 13 <-> target 372 entity 16
```

The corresponding transition parameters are:

```text
372:e22 -> 726:p2
726:e15 -> 372:p2
727:e13 -> 372:p0
372:e16 -> 727:p1
```

No visible door was removed or left without a destination. All arrival
coordinates, walk meshes, inward-facing directions, native sounds, sliding
animations, and finite party-walk routines are the previously audited
values; v41 only rotates the destinations among these existing door sides.

## Size-preserving patch

Only four canonical field bundles differ from v40:

```text
1348  target 371
1350  target 372
2052  target 723
2058  target 726
```

Every changed bundle is size-preserving. All 138 staged replacements were
re-extracted from the final packed image and matched exactly:

```text
packed staged replacement comparison:
138/138 exact, totaling 7,792,342 bytes
```

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v41.bin

BIN size: 692,852,160 bytes
BIN SHA-256:
F19ABAC3B4968113B8DE2BE11F66987D719D70C6D451B0DCF80AB7F7A4EE407A

CUE:
output/Xenogears_PW_CD2_mass_driver_standalone_v41.cue
CUE SHA-256:
2638DBBBAE04D35AC0E7AB968D19C7946F967F3A5C2C6C958E2EE90FEAEE3959

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 146 passed, 1,859 subtests passed
```

These checks establish build and packing integrity only. Runtime acceptance
is not claimed until the new route is tested manually from a cold boot.

## Manual acceptance

1. Close DuckStation completely so the currently mounted image and loaded
   field program are discarded.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and confirm its window title
   identifies v41.
3. Choose New Game. Do not load an F2 state made with an earlier image.
4. Reach target 371's archive annex and press X at the door beside Elly.
5. Confirm the native door sound and sliding animation play, the party walks
   through, and the complete target-723 staircase loads with movement
   enabled.
6. Traverse the staircase and use its far door. Confirm target 726's
   save-point hall loads on the intended side of entity 24, with the used
   door behind the party.
7. Return through entity 24 and traverse the staircase back to target 371.
   Confirm both transitions remain animated, reciprocal, and correctly
   oriented.
8. Cross the target-372/target-726 and target-727/target-372 door pairs once
   in each direction to confirm that the displaced routes remain accessible.
9. If any door stalls, corrupts the geometry, or loads the wrong room, leave
   the failure visible, take a screenshot, and press F2 once before closing
   DuckStation.
