# Mass Driver Dungeon 3.01 - compact Missile Command blasts

V140 is the frozen package for the Defense Archive Missile Command blast and
sound correction. It preserves v139's bounded incoming-missile trails, v138's
background-safe pixel rendering and real-time worker scheduler, the
single-center-base rules, safe `(640,384)` arcade-atlas placement, field-363
station, and complete 35-field route. The v139-to-v140 staged/declared delta
contains exactly canonical 1358, target 376's field bundle. Canonical 1359
field graphics and canonical 2476's arcade atlas remain byte-identical.

## Compact five-cell blasts

Earlier Missile Command blasts expanded into a radius-two diamond. With
several simultaneous player and chain explosions, that footprint made the
ordered compositor's busiest path unnecessarily expensive and obscured too
much of the board.

V140 gives every player, chain-reaction, and incoming-impact blast one compact
five-beat lifecycle:

- phase one draws the center 6-by-6 cell;
- phases two through four draw a radius-one cross: the center plus its four
  orthogonal neighbors, for a maximum of five cells;
- phase five contracts visibly to the center cell; and
- expiry restores the final center cell and releases the blast slot without
  leaving explosion pixels behind.

Rendering, collision, chain reactions, and cleanup share that same
`1, 5, 5, 5, 1` phase footprint. Collision reads frame-start blast snapshots,
so a newly claimed player or chain blast receives its complete lifetime and
cannot age early because of worker order. Boundary clipping remains grid-safe,
and overlapping live objects redraw after cleanup restores their cells.

Missile Command now uses retail field sound effect `0x51` for ABM detonation,
destroyed-enemy chain blasts, incoming impacts, and game failure. This is the
retail field-363 Ether-blast cue. The separate Nuke minigame retains crash
sound `0x77`; door and machinery uses of `0x77` are also unchanged.

This is a narrow continuation of v139 rather than a board or rules rewrite.
The three-point incoming-missile tails, three-cell player interceptor trail,
cursor, scoring, wave progression, authored gray CRT board, arcade atlas,
input model, and surrounding field integration remain unchanged.

## Frozen v140 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v140.bin
BIN size: 696,709,440 bytes
BIN raw sectors: 296,220
BIN SHA-256: fdcdf41773183801c1d73fa9bab2f4e19bf713c280b1aabe7d052856cf73ef8c

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v140.cue
CUE size: 107 bytes
CUE SHA-256: ac0ae9f780974a5e8f71d21c44ba963928f9ce4424838e0b4ca0ecf62507d763

manifest: work/mass_driver_v140_stage/manifest.json
manifest size: 239,797 bytes
manifest SHA-256: 9868e6b95ee11c48808c15b30d73ac60768d2488176541b8856fb73fa13aa31d
jobs: 138
unique replacements: 173
replacement bytes: 12,314,212
route fields: 35
directed edges: 70

field 376 canonical 1358 size: 190,156 bytes
field 376 canonical 1358 SHA-256: 9a9ace17e9113d6a64000b71fcaed1c1d4207ec5f2e871f7f77a26927c9ca558
field 376 packed header size: 1,104 bytes
field 376 packed header SHA-256: eaa4229e1da964747c228532d883df39ef5ace214edb56fa62cbb84e49b0622e
field 376 script size: 48,679 bytes (46,755-byte bytecode)
field 376 script entities: 28
field 376 script SHA-256: 1f68fcad46f1619aec237f17fc1ec5d5cc126effd0a128e2cbc9b80c1c93dd22
field 376 worker script-1 PCs: e16 0x5E4A, e17 0x5F6E, e18 0x5FA4,
  e19 0x5FDA, e20 0x6010, e22 0x6043, e23 0x6076, e24 0x60A9,
  e25 0x64CE, e26 0x663F, e27 0x668E
arcade graphics canonical 1359 size: 239,616 bytes
arcade graphics canonical 1359 SHA-256: 969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd
arcade atlas canonical 2476 size: 8,212 bytes
arcade atlas canonical 2476 SHA-256: 3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d
```

Relative to v139, canonical 1358 changes from 193,384 bytes and SHA-256
`592b767c41e8dcc6b8b971936fd08654c1b4f6b05f031a452d34db9cd8baf173`
to the v140 identity above. Canonicals 1359 and 2476 retain their v139 sizes
and hashes.

All 173 declared replacements were extracted through the final BIN's
Xenogears FAT and matched the stage byte-for-byte, covering 12,314,212 bytes.
All 6,096 raw sectors occupied by those replacements passed MODE2/Form1
EDC/ECC regeneration. The standalone boot patch at raw LBA 172938 has SHA-256
`79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc`
and valid EDC/ECC. The current complete-suite result is 257 tests and 3,278
subtests with no failures, errors, skips, or expected failures.

Fresh user-driven v140 emulator acceptance remains pending; all earlier
runtime evidence is historical to its recorded package. Mount the v140 CUE,
completely leave target 376, and re-enter it from v140 media so the resident
field script is replaced rather than inherited from an earlier save state.
Ask the player to perform all navigation and control input; do not automate the
emulator. Exercise player detonations, chain reactions, incoming impacts, and
overlapping blasts while confirming the center/cross/cross/cross/center phase
sequence, five-cell maximum, phase-matched collision, smooth concurrent
motion, `0x51` blast sound, and zero residue after expiry or slot reuse.
Confirm bounded three-point incoming tails and the unchanged three-cell player
trail. Then repeat pause/resume, wave clear, scoring and persistence, clean
exit, Nuke with its retained `0x77` crash, Video Disk, party sprites, compass,
portraits, menus, dialogue teardown, and field return.
