# Mass Driver Dungeon 3.02 - distinct interceptor heads

V141 is the frozen package for the Defense Archive Missile Command projectile
correction. It preserves V140's compact five-cell explosions, Missile-only
retail explosion sound `0x51`, Nuke crash sound `0x77`, bounded incoming tails,
real-time worker scheduler, safe `(640,384)` arcade atlas, single-center-base
rules, field-363 station, and complete 35-field route.

The V140-to-V141 staged/declared replacement delta is exactly canonical 1358.
Canonical 1359 field graphics and canonical 2476's 8,212-byte arcade atlas are
byte-identical to V140. This statement is deliberately scoped to declared
replacement payloads: the rebuilt media also changes generated overlapping FAT
entries 17 and 22.

## Projectile presentation

Each player interceptor now has a distinct grid-aligned head drawn from the
existing `interceptor` tile. The renderer copies only the tile's seven colored
foreground pixels in two narrow strips; it never copies the tile's baked CRT
background. Exactly three prior grid cells remain behind the head as hot,
bright, and dim exhaust. The `explosion` tile is reserved for the active blast
after detonation, so flight no longer presents an explosion as the missile.

No atlas bytes, graphics resource, palette, texture upload, or VRAM allocation
changed. The shared atlas remains canonical 2476 at `(640,384)`. Head movement,
detonation, cleanup, pause, wave reset, and exit restore the affected board cell
through the existing background-safe compositor.

The finite script-1 workers retain one simulation step per field frame and one
wait in the terminal action. Twenty-eight cycle boosters provide a 904-cycle
soft budget. Maximum audited executed operations are e16 87; e17-e19 441 each;
e20, e22, e23, and e26 406 each; e24 388 on reachable paths and 871 under the
unconstrained compositor contract; e25 332; and e27 311. Maximum call depth is
three.

## Frozen V141 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v141.bin
size: 696,709,440 bytes
raw sectors: 296,220
SHA-256: 65e10899e8bda43b423ad31c0266cb8839dd247c47cfe6498f699f3a6c387aba

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v141.cue
size: 107 bytes
SHA-256: 217a705a47d680ddeb147b744561330e21408be84c22c62c74edbae7aea7e6e3

manifest: work/mass_driver_v141_stage/manifest.json
size: 240,275 bytes
SHA-256: d4f755d3b594facda6bb240244db1e75d772db90d6b81f2b944e328ca7a44c0d
jobs: 138
unique replacements: 173
replacement bytes: 12,314,508
route fields: 35
directed edges: 70
```

Target 376 canonical 1358 is 190,452 bytes with SHA-256
`4e183eb7ccb93fb17708fa09fdc7b31934b14e0f4f71d5d1fea07308c2b62d0a`.
Its 1,104-byte packed header has SHA-256
`45ea04268fa4f554c24ca1693f1b8883cc479d27f865141f87ed1551c7cfed64`.
Its 48,943-byte script contains 47,019 bytes of bytecode and has SHA-256
`56b46a504df09c7dabbf007810ec37e0f80746ccdaf8be63046514f745d2ef49`.

Worker script-1 entry PCs are e16 `0x5EA0`, e17 `0x5FCC`, e18 `0x600A`,
e19 `0x6048`, e20 `0x6086`, e22 `0x60C1`, e23 `0x60FC`, e24 `0x6137`,
e25 `0x65BE`, e26 `0x6737`, and e27 `0x678E`. The interceptor foreground
helper begins at `0x08A9`; cell-to-VRAM begins at `0x082D`.

Canonical 1359 remains 239,616 bytes with SHA-256
`969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd`.
Canonical 2476 remains 8,212 bytes with SHA-256
`3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d`.

## Validation and reload

All 173 declared payloads were extracted directly from the final Xenogears FAT
and matched the stage byte-for-byte. All 6,096 occupied replacement sectors and
the separately audited patched boot sector regenerate byte-exact as
MODE2/Form1 with valid EDC/ECC.

The authoritative full suite passed 257 tests and 3,286 subtests in 43.20
seconds, with no failures, errors, skips, or expected failures.

Fresh user-driven V141 runtime acceptance remains pending. Fully mount the V141
CUE, completely leave target 376, and re-enter it so the new resident script is
loaded. Then verify a distinct interceptor head with exactly three exhaust
cells, explosion graphics only after detonation, smooth concurrent motion,
complete cleanup, pause/resume, wave clear, exit, overlays, party sprites, and
field return. Ask the user to navigate and press controls; do not automate the
emulator.
