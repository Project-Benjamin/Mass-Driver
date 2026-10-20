# Mass Driver Dungeon 2.26 - v47 Gray-Panel Door Repair

Version 47 makes the small gray launch-support panel shown in the July 26
screenshot reliably open its distinct Zeboim archive room. It retains every
accepted v46 route, renderer repair, door animation, and transition.

## Runtime identification

The v46 F2 state has SHA-256:

```text
57a220783964dd21cbb08c04acf1f39e557566af9c01dcdd74d10951e893f920
```

Its embedded media path names the v46 CUE, and its loaded ATEL matches target
726 exactly. The saved runtime values identify the pictured door:

```text
current field:             726
entry parameter:           5
previous field:            368

Elly/entity 2:             (-267.244, 0, -531.704)
player rotation:           0x0C00

door controller:           entity 22 at (-264, -540)
visible sliding helper:    entity 29 at (-302, -485)
helper model:              8
native slide routine:      PC 0x01BE
```

The room was not missing from the authored graph. The complete reciprocal
route already existed:

```text
726:e22 -> 369:p0
369:e22 -> 726:p6
```

Target 369 is a unique one-door Zeboim archive annex cloned from retail
Zeboim source field 378. Its return reaches target 726 at `(-345,-545)`,
facing west with the used door behind the party.

The installed entity-22 action at PC `0x0285` was also complete:

```text
party waypoint:     script 28
door sound:         74 77 80
native helper call: entity 29, script 4
field transition:   98 71 81 00 80  (target 369, parameter 0)
```

The runtime state nevertheless showed entity 22 running collision script 3
at STOP PC `0x01DC`; action script 2 had never started.

## Root cause

Entity 22's initializer set the controller's facing-required flag:

```text
script PC 0x0278: F8 03 04 00
```

`F8` is `SET_FLAGS_DYNAMIC`. Mode 3 ORs the 16-bit operand into the high
half of the entity's secondary flags, so this instruction sets
`0x00040000`. The field engine then requires the player to face the invisible
controller pivot before dispatching its X action.

At the captured position, the desired controller angle was approximately
`0x02D2`. Elly faced `0x0C00`, producing a circular difference of `0x092E`,
outside the engine's interaction tolerance. Elly was visually facing the
gray panel, but the panel model's extracted pivot and the invisible
controller pivot do not share that facing line. The engine therefore kept
selecting collision script 3 instead of action script 2.

Making helper entity 29 own the action is not a valid repair. Although its
angle is inside the facing tolerance, its retail model flags include
collision-only bit `0x04000000`, so the engine cannot dispatch its action
script.

## Scoped repair

Only entity 22 now explicitly clears the facing-required bit:

```text
v46: F8 03 04 00  (set secondary flag 0x00040000)
v47: F8 07 04 00  (clear secondary flag 0x00040000)
```

Mode 7 is the checked inverse operation for the same secondary flag half.
The replacement is exactly four bytes, so every ATEL pointer and routine PC
is unchanged. The controller retains its existing bounded interaction box
and remains X-only; it does not become an automatic transition.

The native door sound, entity-29 sliding animation, finite party walk,
target-369 transition, and reciprocal return are all unchanged.

## Exact decompressed change

Only one byte differs between the v46 and v47 target-726 script components:

```text
component size:        3,583 bytes
component offset:      0x0B3D
ATEL script mode byte: 03 -> 07

v46 script SHA-256:
fe81549eb4361a5342f3a13741d2cb61df50ba3d4de164dfd283978cea48369b

v47 script SHA-256:
85cd07f3418c768b16ab07104d4d3317a2e5e7a5d11b61cf3d161a4f532c096a
```

## Packed change from v46

Only one of the 140 staged canonical replacements differs:

```text
canonical 2058, target 726 bundle
size: 23,240 bytes

v46 SHA-256:
7457ac568f1173eb0b927e1661cda416bc13e026f6c7c57712c045bd30b16f45

v47 SHA-256:
574c4830a7bc8c8f0513b5fc3d89147f8495655f6cd543181d2beea8eda1d396
```

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v47.bin

BIN size: 693,263,760 bytes
raw sectors: 294,755
BIN SHA-256:
726c6a696e36eab691c1d981e3d592d05fb23364e1c2c166913d0aa86638c592

CUE SHA-256:
a09303a9bc00e338df1a44a2d40cf1b3eee60f9517980a89fef5d90385a068ca

packed staged replacement comparison:
140/140 exact, totaling 8,152,642 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 150 passed, 1,891 subtests passed
```

## Focused manual acceptance

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and confirm its title says
   v47.
3. Choose New Game. Do not load the v46 F1/F2 state; it restores the v46
   mounted disc and already-loaded v46 target-726 script.
4. Return to the small gray panel shown in the screenshot.
5. Stand directly in front of it as shown and press X once.
6. Confirm the native sound and sliding animation play, the party walks
   through, and target 369's archive room loads.
7. Use that room's visible return door. Confirm it returns to target 726 with
   the used gray panel behind the party.
8. If any step fails, press F2 immediately before X, press X once, then press
   F2 again while the failure is visible. Preserve both state generations and
   the screenshot.
