# Mass Driver Dungeon 3.00 - bounded Missile Command enemy trails

V139 is the frozen package for the Defense Archive Missile Command enemy-trail
correction. It preserves v138's background-safe pixel rendering, real-time
worker scheduler, single-center-base rules, safe `(640,384)` arcade-atlas
placement, field-363 station, and complete 35-field route. Relative to v138,
exactly one declared payload changes: canonical 1358, target 376's field
bundle. Canonical 1359 field graphics and canonical 2476's arcade atlas remain
byte-identical.

## Bounded incoming-missile trails

V138 eliminated off-grid CRT-grain squares by drawing enemy motion with
foreground-only pixels. Its enemy owners, however, left every previous red
point in the framebuffer until the board was redrawn. A surviving incoming
missile could therefore accumulate a long permanent red line, and completed
trajectories could remain visible after their missile was gone.

V139 keeps the background-safe rendering while bounding each incoming
missile's visible history:

- each active incoming missile has one white 1-by-1 current head;
- exactly its three prior head positions are retained as red 1-by-1 points;
- advancing the missile restores the oldest point from the phase-correct
  6-by-6 CRT-board background before publishing the new three-point tail; and
- hit, ground-impact, slot-reuse, wave-reset, and game-reset paths clean up the
  retained points so inactive missiles leave no red history behind.

The player interceptor remains exactly three grid-aligned 6-by-6 blocks: hot,
bright, and dim. Its appearance, lifetime, and cleanup behavior are unchanged
from v138. Enemy owners still advance one simulation step per frame, and the
ordered redraw workers retain the red-tail, player/chain-effect, white-head,
and cursor layers without adding a firing pause or a second input wait.

This is a narrow continuation of v138 rather than a graphics replacement.
V138 supplied the foreground-only moving pixels and phase-safe board handling;
v139 adds a finite enemy-history lifecycle to those same pixels. The authored
gray CRT board, arcade atlas, input model, scoring, waves, and surrounding
field integration remain unchanged.

## Frozen v139 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v139.bin
BIN size: 696,714,144 bytes
BIN raw sectors: 296,222
BIN SHA-256: 4768860d0cfc0071e0bc613069482fd2cdca3c389a3b66a6aa1bc04119354336

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v139.cue
CUE size: 107 bytes
CUE SHA-256: e1834224b377014f4e32a44710604fc19733f9d2cd0ce08cba8e36a96c109171

manifest: work/mass_driver_v139_stage/manifest.json
manifest size: 239,182 bytes
manifest SHA-256: e0a163c31a5217154dede17048b989fac89ff93f27139cc566988eaec47f4324
jobs: 138
unique replacements: 173
replacement bytes: 12,317,440
route fields: 35
directed edges: 70

field 376 canonical 1358 size: 193,384 bytes
field 376 canonical 1358 SHA-256: 592b767c41e8dcc6b8b971936fd08654c1b4f6b05f031a452d34db9cd8baf173
field 376 prepared header SHA-256: 2e85b169f0401db16d126d5e14d66efb34fda326a164b33664b8e0a33057724f
field 376 packed header SHA-256: e9455a2fab674aa105c269cf7f56aafa202ad6e19f3a83b813be2d582745f741
field 376 script size: 51,551 bytes (49,627-byte bytecode)
field 376 script entities: 28
field 376 script SHA-256: d648ce976f1a4a870c3ae4d29fd33aef37a99ee7a8f5b9dcf42f1bd94f31cdf2
arcade graphics canonical 1359 size: 239,616 bytes
arcade graphics canonical 1359 SHA-256: 969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd
arcade atlas canonical 2476 size: 8,212 bytes
arcade atlas canonical 2476 SHA-256: 3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d
```

All 173 declared replacements were extracted through the final BIN's
Xenogears FAT and matched the stage byte-for-byte, covering 12,317,440 bytes.
All 6,098 raw sectors occupied by those replacements passed MODE2/Form1
EDC/ECC regeneration. The standalone boot patch at raw LBA 172938 has SHA-256
`79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc`
and valid EDC/ECC. The current complete-suite result is provisionally 257 tests
and 3,254 subtests with no failures, errors, skips, or expected failures.

Fresh user-driven v139 emulator acceptance remains pending. Mount the v139 CUE,
completely leave target 376, and re-enter it from v139 media so the resident
field script is replaced rather than inherited from an earlier save state.
Ask the player to perform all navigation and control input; do not automate the
emulator. Capture an empty-board baseline, then exercise shallow, steep, and
crossing incoming trajectories while confirming one white head, exactly three
red prior-head points, phase-correct disappearance of the fourth-oldest point,
smooth concurrent motion, and zero residue after hit, impact, reset, or slot
reuse. Confirm the unchanged three-block player trail as well. Then repeat
pause/resume, wave clear, scoring and persistence, clean exit, both Nuke and
Video Disk, party sprites, compass, portraits, menus, dialogue teardown, and
field return.
