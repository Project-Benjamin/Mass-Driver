# Mass Driver Dungeon 2.98 - real-time Missile Command workers

V137 is the frozen package for the Defense Archive Missile Command timing
correction. It preserves v136's single-center-base rules, safe `(640,384)`
arcade-atlas placement, field-363 station, and complete 35-field route. Relative
to v136, exactly one declared payload changes: canonical 1358, target 376's
field bundle. Canonical 1359 field graphics and canonical 2476's arcade atlas
remain byte-identical.

## Smooth one-frame simulation

V136's monolithic terminal action split a frame across several explicit waits.
Firing therefore paused the rest of the simulation while the shot path and
dynamic display were updated. V137 keeps the terminal action responsible for
input, scoring, progression, pause, and exit, but reduces its active gameplay
loop to one wait per field frame. Firing no longer inserts a separate
shoot-triggered pause.

Finite automatic script-1 workers on entities 16-20 and 22-27 perform one whole
simulation-and-render pass concurrently with that terminal action:

- entity 16 owns the spawn/enemy-step clock and frame-start blast snapshots;
- entities 17-20 and 22-23 each own one enemy and one blast, with entities
  17-19 also advancing one center interceptor;
- entities 24 and 25 composite player and chain fireballs;
- entity 26 coalesces terrain and HUD refreshes; and
- entity 27 repairs enemy heads, draws the cursor, and detects wave completion.

Each worker is finite and stops without an internal wait. Request and
acknowledgement variables order setup, active play, pause, resume, wave clear,
and teardown. The frozen emitted routines were exhaustively checked below the
ATEL 1,024-opcode guard: the largest audited worker path is 820 operations,
within the 904-cycle soft budget, and maximum call depth is three. The input
path tops out at 53 operations within its 72-cycle budget. Only script 1 is
repointed on the resident worker entities; the terminal remains entity 21 and
its existing action, video, Nuke, and field-return responsibilities are
preserved.

The gameplay contract is otherwise unchanged from v136: a 2600-style single
center base, 10 loaded plus 20 underground ABMs, loaded-set-only base loss,
three concurrent player shots or fireballs, three chain fireballs, the custom
three-cell hot/bright/dim trail, Triangle pause, Cross resume, Circle exit from
pause, and the existing arcade quota, scoring, persistence, and bonus-city
systems. It remains a 2600-style adaptation, not an exact Atari 2600 clone.

## Frozen v137 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v137.bin
BIN size: 696,709,440 bytes
BIN raw sectors: 296,220
BIN SHA-256: 4900748c648dd61d6b966d403a3606fccc50d5ae1051cb3573ba4939a98f0ba1

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v137.cue
CUE size: 107 bytes
CUE SHA-256: 4d4e68176b3a5acc1acb5e33552866e81ed75d2af053343269c8a2b8e7a582b7

manifest: work/mass_driver_v137_stage/manifest.json
manifest size: 238,773 bytes
manifest SHA-256: a2487e9a452c397d22952096f9f343a62f70ca12cd360a4bf224d6b18988b42d
jobs: 138
unique replacements: 173
replacement bytes: 12,314,004
route fields: 35
directed edges: 70

field 376 canonical 1358 size: 189,948 bytes
field 376 canonical 1358 SHA-256: 1677755fa9440200b6179e621cfd302e3c3dd63a447e48187fb5f5fb8935e158
field 376 prepared header SHA-256: 2e85b169f0401db16d126d5e14d66efb34fda326a164b33664b8e0a33057724f
field 376 packed header SHA-256: fe657022b5fea258271e984038ea1824290613a049c4fcdda6df02499ffde777
field 376 script size: 48,494 bytes (46,570-byte bytecode)
field 376 script entities: 28
field 376 script SHA-256: d64bfbd2e84aa93f46c7b46af875912c72e5663db1fa636edee703cea1d3537b
arcade graphics canonical 1359 size: 239,616 bytes
arcade graphics canonical 1359 SHA-256: 969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd
arcade atlas canonical 2476 size: 8,212 bytes
arcade atlas canonical 2476 SHA-256: 3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d
```

All 173 declared replacements were extracted directly through the final BIN's
Xenogears FAT and matched the stage byte-for-byte, covering 12,314,004 bytes.
All 6,096 raw sectors occupied by those replacements passed MODE2/Form1
EDC/ECC regeneration. The standalone boot patch at raw LBA 172938 has SHA-256
`79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc`
and valid EDC/ECC. The complete suite passed 257 tests and 3,204 subtests with
no failures, errors, skips, or expected failures.

Fresh user-driven v137 emulator acceptance remains pending. Mount the v137 CUE,
completely leave target 376, and re-enter it from v137 media; a resident v136
field script cannot validate the worker scheduler. Ask the player to navigate
and press controls rather than automating emulator input. Confirm that firing
does not pause enemy motion, trails, explosions, or the cursor; then test three
simultaneous ABMs, chain reactions, base loss and reserve reload, pause/resume,
wave clear, scoring and persistence, clean exit, both Nuke and Video Disk, Elly
and Emeralda, compass, portraits, menus, dialogue teardown, and field return.
