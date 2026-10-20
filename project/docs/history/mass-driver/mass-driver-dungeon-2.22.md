# Mass Driver Dungeon 2.22 - v43 Post-Auxiliary Passage Repair

Version 43 repairs both paired same-room passages encountered after returning
from the auxiliary-power annex to target 372. The retail field models,
textures, walkmesh, door-helper actors, and external destinations remain
unchanged.

## Failure surface

The v38-v42 stability implementation deliberately avoided allocating another
party-leader VM slot. It used field-local request variable `0x0402`, observed
by the already-running script-1 update on party entities 2 through 12.
However, each matching branch used opcode `0x19` to move every loaded party
actor to one far-side coordinate in a single frame. Both door-panel helpers
also started concurrently. The resulting party stack, camera jump, and
competing panel motion could present as a graphical glitch even though the
retail model data was intact.

The post-auxiliary forward order is:

| Controller | Request | Far-side X/Z | Facing | Passage state |
| --- | ---: | ---: | ---: | ---: |
| entity 20 | 4 | -1159, 199 | 4 | 1 |
| entity 18 | 2 | -1130, -460 | 4 | 0 |

Their reciprocal sides are:

| Controller | Request | Far-side X/Z | Facing | Passage state |
| --- | ---: | ---: | ---: | ---: |
| entity 19 | 3 | -1171, 465 | 0 | 2 |
| entity 17 | 1 | -1155, -187 | 0 | 1 |

## Bounded animated crossing

The allocation-safe script-1 request dispatcher remains at `0x0918`. Each of
its four branches now performs:

```text
bounded actor walk (opcode 0x4B, maximum 48 steps)
exact far-side position (opcode 0x19)
walkmesh-layer refresh
forward facing
STOP
```

The exact landing remains a collision-independent fallback, but it occurs
after a visible movement attempt instead of being the entire crossing.

Each local owner now follows this finite sequence:

```text
clear stale request
FE54 cinematic control and native sound 0x77
run the first checked retail panel-opening helper to completion
run the second checked retail panel-opening helper to completion
stage the native passage camera
assert the crossing request for 4 frames
clear the request
wait 52 frames for the bounded movement and landing
write the native local-passage state
restore the camera
FE53 player-control restoration
queue both checked closing helpers
STOP
```

The opening helpers are serialized in their donor order. The v37 runtime
failure occurred later, in its blocking party-leader dispatch; the retail
panel helpers themselves completed. Version 43 retains v38's allocation-safe
party mechanism and does not reintroduce that rejected handoff.

The installed action pointers are:

```text
entity 17: 0x0986
entity 18: 0x09C2
entity 19: 0x09FE
entity 20: 0x0A3A
```

Automated verification requires all four exact animated branches, the
48-step bound, a settle window no shorter than the 52-frame movement grace,
serialized opening-helper order, no `07 FF`, `09 FF`, `FE68`, or `FE24`
party handoff in any local owner, exact far-side positions, exact local-state
writes, and control restoration before the closing helpers begin. The helper
validator also proves each blocking FE1B opener has its checked counter
variable, finite limit, incrementing back-edge, terminal target, and STOP.
Negative tests reject both an undersized owner wait and a helper whose exit
was redirected into a nonterminating reset loop.

## Isolated packed change

Only canonical field bundle 1350 differs from v42:

```text
v42 packed size: 36,696 bytes
v43 packed size: 36,720 bytes
v43 packed SHA-256:
ab6b15346e37ea6dc521518654488a50c0a8c5a502a430fd643b5a4bd4dcb0f4

v43 script component: 5,434 bytes
v43 script SHA-256:
b8596ebbc0079ce2ac9890012dc13ef40228cfb3f78d96c9f73cd2b3b950205e
```

Canonical graphics 1351 remains byte-identical to retail and v42:

```text
ac2add532e180e4c925bbdeab752f77643617e5c27cfcb57606e417a368f39f1
```

Every other staged replacement is byte-identical to v42.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v43.bin

BIN size: 692,852,160 bytes
raw sectors: 294,580
BIN SHA-256:
5276877ee466d30273d39139068af3d56ca33bbcd20767a45c2453483aa58f25

CUE SHA-256:
873eec04ce94262d2e556a0a04da97cb9a51f054da19541c6ae5fcfd69d6c336

packed staged replacement comparison:
138/138 exact, totaling 7,792,186 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 148 passed, 1,863 subtests passed
```

These checks establish script, route, packing, and image integrity. Emulator
acceptance still requires the reciprocal traversal below.

## Focused manual acceptance

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and confirm the title says
   v43.
3. Choose New Game. Do not load an older F1/F2 state.
4. Restore auxiliary power in the control/research annex and return through
   its animated door to the target-372 service hub.
5. Continue toward the lower corridor and activate the first paired passage.
   Confirm its two panels open serially with sound, Elly and Emeralda visibly
   cross, the compass returns, and movement works.
6. Continue to the hallway-end paired passage and repeat the same checks.
7. Turn around and cross both passages in reverse. Confirm each reciprocal
   side closes normally and returns control.
8. If a fault remains, press F2 immediately before activating the affected
   door, press X, then press F2 again while the fault is visible. Keep the
   screenshot and both resulting state generations for VM-phase analysis.
