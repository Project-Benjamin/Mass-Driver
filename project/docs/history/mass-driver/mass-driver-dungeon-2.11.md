# Mass Driver Dungeon 2.11 - v32 Door Transition Repair

Version 32 repairs the freeze reported at the service-hub door immediately
before the auxiliary-power annex. It also audits and hardens every external
mechanical door that uses the same blocking walk-through command.

## Reported failure

Target field 372 entity 21 completed its native opening sequence:

```text
0x06B7  start cinematic
0x06B9  play native door sound 0x77
0x06BC  run helper 29's door animation
0x06BF  walk Elly through the doorway
0x06C6  change field to target 361, parameter 0
```

The retail waypoint at `0x06BF` was `(-883, 888)`, only 9.59 world units
from a closed edge of its final walkmesh triangle. Elly could stop visibly in
the open threshold without the blocking movement reporting completion. The
field-change opcode at `0x06C6` was therefore never reached.

The destination was not corrupt. Canonical resources 1328 and 1329 parse
normally, target 361 entry 0 is on valid walkmesh 0, and its reciprocal door
still returns to target 372 parameter 1.

## Repair

The failing waypoint now targets the safe incenter `(-859, 866)` of the same
transition triangle:

```text
PC 0x06BF
retail: FE 68 8D FC 78 03 C0
v32:    FE 68 A5 FC 62 03 C0
```

This keeps the native X interaction, sound, helper-model animation, forward
walk, and `361/0` destination. It changes only the position that the blocking
walk must reach.

A route-wide geometry audit found the same edge-sensitive pattern elsewhere.
Version 32 repairs 20 `FE68` waypoint instances across targets 361, 362, 363,
372, 387, 722, 725, 726, 727, and 728. Each replacement remains inside its
original transition pocket or crosses only a connected internal triangle
edge while preserving the outbound direction. No door helper, sound,
transition target, arrival record, dialogue, combat resource, Gear resource,
or graphics resource changes.

## Isolation

Comparing the v31 and v32 staged replacements shows changes only in these ten
field bundles:

```text
1328  target 361
1330  target 362
1332  target 363
1350  target 372
1380  target 387
2050  target 722
2056  target 725
2058  target 726
2060  target 727
2062  target 728
```

Their paired graphics resources are byte-identical to v31. Every El-Regulus,
shop, world-map, normal-combat, and standalone-bootstrap replacement is also
byte-identical to v31.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v32.bin

BIN size: 690,377,856 bytes
BIN SHA-256:
01bd504ab2073d99014eb4db0828b1ac4c2ff817ea523727088685e9b47aa3d4

automated tests: 133 passed, 330 subtests passed
post-build replacement comparison: 122/122 exact
audited waypoint commands extracted from BIN: 20/20 exact

boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid
```

## Manual acceptance

1. Close the old v31 session and cold-boot
   `output/PLAY_MASS_DRIVER_STANDALONE.cmd`; it now targets the v32 CUE.
2. Return to the four-door service hub.
3. Press X at the door immediately before the auxiliary-power annex.
4. Confirm the native sound and opening animation play, Elly completes the
   walk through the doorway, and the auxiliary annex loads without a freeze.
5. Exit through the same door and confirm the animated return to the service
   hub also completes.
6. Check the service hub's other three external doors. They should retain
   their prior destinations and no longer stop the party at a threshold.
