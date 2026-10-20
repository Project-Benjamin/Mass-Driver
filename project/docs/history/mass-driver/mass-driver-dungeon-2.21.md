# Mass Driver Dungeon 2.21 - v42 Archive-Door Geometry Repair

Version 42 repairs the striped geometry reproduced while opening target 726
entity 24, the archive door beyond the golden save point. The v41 route
through target 723's complete staircase remains unchanged.

## Runtime identification

The new screenshot
`Xenogears (Disc 2) 2026-07-26-10-07-09.png` is the source-side target-726
door-opening frame, before target 723 loads. It is 99.995659 percent
pixel-identical to the earlier `08-46-41` failure frame. Target 723's retail
models and graphics are intact; changing the destination could not repair
this source-field rendering fault.

## Corrected model structure

Field 726 model 3 contains the eight obsolete baked wall panels replaced by
the independently animated archive doors. Version 40 lowered the primitive
counts but retained the panel data:

```text
declared primitives:        260
declared final mesh group:  240
mesh end:                   0x1200
display-list offset:        0x1240
display records retained:   268
instance buffer:            0x2940 (space for 268 primitives)
```

That left an invalid 64-byte gap between the mesh and display list, all eight
live panel display records, and their render-buffer allocation.

Version 42 removes the complete primitive tail:

```text
removed mesh indices:       8 * 8 bytes
removed display records:    8 * 12 bytes
declared primitives:        268 -> 260
declared final mesh group:  248 -> 240
display-list offset:        0x1240 -> 0x1200
instance buffer:            0x2940 -> 0x2800
model size:                 0x1EBC -> 0x1E1C
```

The retained mesh now ends exactly at the relocated display list. Its group
counts sum to 260, its display list contains exactly 20 type-0x25 and 240
type-0x2D primitive records, and its instance buffer matches those records.

```text
field-726 model-3 SHA-256:
9e6686ad10243acfb6274dd5b9a9a22399adaeb87f145c71ea67ffba8c33e745

field-726 nine-model archive SHA-256:
aa1c67b892f689fd98f5817b511c8262f5430a8edae31bf3f556a535e78e1b97
```

Only canonical field bundle 2058 differs from v41. Its packed size changes
from 23,420 to 23,240 bytes. Field 726's external graphics resource, the
target-723 staircase, every route destination, and every other replacement
remain byte-identical to v41.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v42.bin

BIN size: 692,852,160 bytes
BIN SHA-256:
1e6bf4218a6403dae16a7c10e595962dc6fbcc904be5ee6d82442ce7d711bcc1

CUE SHA-256:
5daff2b03627c48664d11910c2267f8515f19ec50b9b600e684c46d58fe61666

packed staged replacement comparison:
138/138 exact, totaling 7,792,162 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 146 passed, 1,859 subtests passed
```

These checks establish structural and packing integrity. Runtime acceptance
still requires a cold-boot traversal.

## Focused manual acceptance

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and confirm its title says
   v42.
3. Choose New Game and do not load an older F2 state.
4. Reach target 726's golden save point and press X at entity 24's door.
5. Confirm the native sound and sliding animation play without any white or
   black striped polygons.
6. Confirm the party walks through and target 723's staircase loads with
   movement enabled.
7. Cross the staircase into target 371, then return through both doors once.
8. If corruption remains, leave it visible, take a screenshot, and press F2
   once before closing DuckStation.
