# Mass Driver Dungeon 2.19 - v40 Visible Walk and Panel Repair

Version 40 repairs two separate faults visible in the July 26 runtime
screenshots:

- external doors could complete their room transition before the party's
  walking task had actually started, making Elly and Emeralda appear to
  teleport through the next rooms;
- operating the archive door beyond target 726's golden save point could
  project the hidden baked door quads into large white-and-black striped
  polygons.

The screenshots were captured from a DuckStation process still running v38.
That explains why the already-repaired v39 field-722 initialization fault was
also still reproducible in that session. The walking race and unsafe hidden
panel geometry were shared by v38 and v39, so both receive independent v40
repairs.

## Deterministic visible walking

All 38 external mechanical door sides, forming 19 reciprocal room pairs, use
the same finite presentation contract. Earlier releases started the party
task after cinematic control was disabled:

```text
FE54 cinematic control
door sound
asynchronous model-helper opening
asynchronous party walk
fixed grace
field transition
```

The fixed-time owner could continue even if the VM had not allocated the
party task. The native panels opened, but the field transition then occurred
without a visible walk.

Version 40 uses this size-preserving order:

```text
asynchronous party task allocation
FE54 cinematic control
door sound
asynchronous model-helper opening
84-frame finite grace
field transition
```

The party routine itself remains finite:

```text
wait 32 frames for the native panels
bounded animated waypoint, maximum 48 updates
exact far-side position snap
STOP
```

The 32-frame delay is longer than every audited native panel interpolation.
The owner waits 84 frames, four frames longer than the combined panel and
movement bounds, before performing the unchanged field transition. No
unbounded `FE68` waypoint remains in an external door action.

The rewrite rotates bytes inside each existing branch without changing its
length, so checked conditional targets and field-transition PCs remain
unchanged. The builder separately verifies the two-branch actions at field
723 entity 13 and field 726 entity 14; each branch must allocate the same
bounded party routine immediately before its own cinematic-control opcode.

## PS1-safe field-726 panel suppression

Field 726 model 3 contains the original eight baked wall panels as the final
eight textured primitives of its final mesh block. Independent movable door
models replace those panels. Earlier builds attempted to hide each baked
quad by changing all four of its vertex indices to one vertex.

A degenerate textured PlayStation primitive is not a safe invisible object.
While the replacement panel moved near the save-point camera, the GTE could
project the degenerate quad across the near plane, producing the enormous
striped polygons in the second screenshot.

Version 40 suppresses the audited primitive tail structurally:

```text
model total primitive count: 268 -> 260
final mesh-block count:      248 -> 240
```

All model bytes, vertices, the original eight panel index records, and the
display-list offset remain in place. Only the two checked count bytes at
model offsets `0x0014` and `0x0A7E` change. This prevents the renderer from
submitting those eight primitives at all while leaving every subsequent
offset stable.

```text
patched field-726 model-3 SHA-256:
54414c5e15a5bc5c6846dec6736e3416b6af5dc3119b8aa33d1596ccd2bffe4b

patched field-726 model bundle SHA-256:
7756f762a208af076a1d331427f1fd33bf30f99d795c1008a72118a78fdf1e71
```

The reciprocal archive door beyond the save point remains target 726 entity
24 to target 371 parameter 0. Its native sliding animation, sound, receiving
position, camera direction, and return door are unchanged.

## Retained v39 destination repair

Field 722 entity 15 still begins script 0 at `0x019D`, executes
`INIT_ENTITY_NPC`, and branches to the original safe continuation at
`0x01AB`. The v40 global door rewrite does not reintroduce the v38
uninitialized record-actor crash.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v40.bin

BIN size: 692,852,160 bytes
raw sectors: 294,580
BIN SHA-256:
49b7ac85da2d217bc628c13d706f4171f9ee08d2f0b88d5e1db628dd844a0b02

packed staged replacement comparison:
138/138 exact, totaling 7,792,342 bytes

replacement files changed from v39:
19 field bundles
canonical IDs:
1328, 1330, 1332, 1336, 1338, 1340, 1342, 1344, 1346, 1348,
1350, 1380, 2050, 2052, 2054, 2056, 2058, 2060, 2062

field-726 canonical 2058 SHA-256:
1ddfbb4aa193048a9b768a051199923eded2a08b8f173f938d66ec5f3ff5731a

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 145 passed, 1,854 subtests passed
```

Every one of the 138 replacement files was re-extracted from the final
packed v40 BIN and compared with its staged size and SHA-256. Runtime
acceptance is not claimed until the repaired route passes manually.

## Manual acceptance

DuckStation PID 23816 was still mounted to the v38 CUE when the screenshots
were taken. Save states retain the mounted image and already-loaded field
program, so they cannot validate v40.

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`; confirm its window title says
   v40 and cold-boot with New Game.
3. Do not load an F2 state made with v38 or v39.
4. Cross the external doors in the two rooms that previously appeared to
   teleport the party. Confirm the panels open first, Elly and Emeralda
   visibly walk through, and only then does the next room load.
5. Cross field 372's east storage-annex door into field 722, wait several
   seconds, move normally, and return through the reciprocal door. This
   confirms that the retained v39 actor initialization is still sound.
6. Reach target 726's golden save point and press X at the door beyond it.
7. Confirm its native sound and sliding animation play, the party walks
   through, no striped polygons appear, and target 371 loads with movement
   enabled.
8. Return through target 371's reciprocal door. Confirm the party faces into
   target 726 with the used door behind them.
9. Continue through the next two connected rooms and backtrack once to verify
   that every transition remains animated and reversible.

If a door stalls or the geometry corrupts, leave the frame visible and press
F2 once before closing DuckStation.
