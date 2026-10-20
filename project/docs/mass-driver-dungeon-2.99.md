# Mass Driver Dungeon 2.99 - background-safe Missile Command trails

V138 is the frozen package for the Defense Archive Missile Command rendering
correction. It preserves v137's real-time worker scheduler, single-center-base
rules, safe `(640,384)` arcade-atlas placement, field-363 station, and complete
35-field route. Relative to v137, exactly one declared payload changes:
canonical 1358, target 376's field bundle. Canonical 1359 field graphics and
canonical 2476's arcade atlas remain byte-identical.

## Background-safe moving objects

V137 moved enemy heads and interceptor heads at pixel resolution by copying
opaque 6-by-6 atlas tiles. Those tiles contain the board's 6-by-6 CRT-grain
background. At an off-grid destination the grain phase no longer matched the
board, so an otherwise correct moving object could stamp a visible square or
leave shifted background texture.

V138 removes those off-grid opaque copies:

- each player interceptor is exactly three grid-aligned 6-by-6 blocks: hot,
  bright, and dim;
- the hot block is the visible leading shot, so there is no separate moving
  player-head tile;
- enemy owners write one red 1-by-1 foreground point at the previous position;
  and
- the final cursor worker writes one white 1-by-1 foreground point at each
  current enemy position.

Only foreground pixels now move off grid. Grid-aligned trail blocks retain the
atlas' phase-matched CRT grain, so the renderer no longer copies a mismatched
background square around a moving head. The gray CRT board itself remains the
authored playfield; this correction removes displaced grain rather than
changing the board or the unchanged atlas.

The v137 lifecycle remains intact: finite automatic script-1 workers on
entities 16-20 and 22-27 simulate one complete frame while entity 21 handles
input with one outer wait. Firing adds no extra wait. The largest audited
worker path remains 820 operations within the 904-cycle soft budget and the
1,024-opcode hard guard; maximum call depth remains three. The input path is
54 operations within its 72-cycle budget.

## Frozen v138 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v138.bin
BIN size: 696,709,440 bytes
BIN raw sectors: 296,220
BIN SHA-256: de964249f26405c38b525e994b8a28a9e86da42bf447aa86409f0def43f3f7b9

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v138.cue
CUE size: 107 bytes
CUE SHA-256: ad5b5549bddf8b036803c796951d336bc5d7ccf4a1382016c0b8a9b3f7aeacca

manifest: work/mass_driver_v138_stage/manifest.json
manifest size: 238,768 bytes
manifest SHA-256: 214fef2edff8a684c504840289333b1f429c4120f3bd9843a2360c02a55b5803
jobs: 138
unique replacements: 173
replacement bytes: 12,313,680
route fields: 35
directed edges: 70

field 376 canonical 1358 size: 189,624 bytes
field 376 canonical 1358 SHA-256: 062ecc51338c7e7be7b023fd436bd85a859d354491adc728aedceb89485445c4
field 376 prepared header SHA-256: 2e85b169f0401db16d126d5e14d66efb34fda326a164b33664b8e0a33057724f
field 376 packed header SHA-256: 97b460b750fac0046f538da9ee7b15d2583a1b33918c36c21f9f6167b0747909
field 376 script size: 48,203 bytes (46,279-byte bytecode)
field 376 script entities: 28
field 376 script SHA-256: 83285c16b169c8858bc10d4e4eb1da7947e9c110e4441683d2dc90eb7e9b3648
arcade graphics canonical 1359 size: 239,616 bytes
arcade graphics canonical 1359 SHA-256: 969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd
arcade atlas canonical 2476 size: 8,212 bytes
arcade atlas canonical 2476 SHA-256: 3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d
```

All 173 declared replacements were extracted through the final BIN's
Xenogears FAT and matched the stage byte-for-byte, covering 12,313,680 bytes.
All 6,096 raw sectors occupied by those replacements passed MODE2/Form1
EDC/ECC regeneration. The standalone boot patch at raw LBA 172938 has SHA-256
`79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc`
and valid EDC/ECC. The final complete-suite result is 257 tests and
3,224 subtests with no failures, errors, skips, or expected failures.

Fresh user-driven v138 emulator acceptance remains pending. Mount the v138 CUE,
completely leave target 376, and re-enter it from v138 media. Ask the player to
navigate and press controls rather than automating emulator input. Capture an
empty-board baseline, exercise shallow and steep player shots plus diagonal
incoming missiles, and verify exactly three player blocks, one-pixel enemy
marks, smooth concurrent motion, and zero background residue after cleanup.
Then repeat pause/resume, wave clear, scoring and persistence, clean exit, both
Nuke and Video Disk, party sprites, compass, portraits, menus, dialogue
teardown, and field return.
