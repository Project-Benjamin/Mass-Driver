# Mass Driver Dungeon 2.16 - v37 Reciprocal Passage Repair

> Superseded: runtime testing on July 25, 2026 rejected v37. Both panels
> opened, but the blocking party-leader script never completed; the party
> stayed on the approach side with cinematic control locked. Version 38
> removes that runtime-dependent handoff. See
> [Mass Driver Dungeon 2.17](mass-driver-dungeon-2.17.md).

Version 37 repairs the cinematic lock reported at the hallway door beside
the auxiliary-power route. The screenshot is the reverse side of the same
field-372 passage previously tested from entity 18: entity 17, paired with
door-model helpers 25 and 26.

This is a same-field physical passage. It does not load another room and has
no destination parameter. The v35/v36 generalized door hardener unnecessarily
repointed entities 17-20 to new actions that started both model halves and the
party waypoint concurrently. On the reported reverse traversal, the party
could reach the far endpoint while the compass remained hidden and cinematic
control never returned.

## Restored native sequence

Version 37 removes only that unaccepted local rewrite. The four same-field
controllers retain their proven action pointers:

```text
entity 17  action 0x0551  helpers 25,26  leader script 4  endpoint (-1155,-187)
entity 18  action 0x0594  helpers 26,25  leader script 7  endpoint (-1130,-460)
entity 19  action 0x05D7  helpers 27,28  leader script 5  endpoint (-1171, 465)
entity 20  action 0x0674  helpers 28,27  leader script 6  endpoint (-1159, 199)
```

Each action now follows the accepted native order:

```text
cinematic lock
door sound 0x77
first native panel opening
second native panel opening
camera staging
bounded party-leader walk plus exact-position snap
fixed 24-frame follower-clear delay
local passage-state write
camera restore
both native closing animations
FE53 player-control restore
STOP
```

The deeper walkmesh-safe endpoints and the v33 replacement for the unbounded
`FE24` follower-coordinate wait remain unchanged. External doors keep the
v36 finite asynchronous field-transition hardening.

## Regression coverage

The build now rejects any reintroduction of the v35/v36 local asynchronous
scripts in party slots 24-27. It pins all four native controller pointers and
exact actions, requires serialized helper script 4 calls, bounded party
waypoint bodies for every possible leader, a fixed 24-frame delay, native
helper script 5 closing calls, and `FE53` before the checked STOP.

Only packed canonical file 1350 differs from v36:

```text
1350_field_372.bin: 36,604 -> 36,324 bytes
```

All other 137 packed replacements are byte-identical to v36.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v37.bin

BIN size: 692,852,160 bytes
raw sectors: 294,580
BIN SHA-256:
1cda6e164ca35d390b02e3af11481322211ceb8ed9f0e4141a4c7229fbd1bb87

packed staged replacement comparison:
138/138 exact, totaling 7,791,970 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 142 passed, 1,689 subtests passed
```

Runtime acceptance is not claimed until the manual reciprocal traversal
below passes.

## Manual acceptance

Do not load a v35/v36 F2 state; DuckStation states retain the old mounted
image and already-loaded field script.

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and cold-boot v37.
3. Restore auxiliary power through the research annex.
4. Return to the four-door service hub and open the first internal
   two-panel passage.
5. Walk to the hallway-end door shown in the 19:54 screenshot and press X.
6. Confirm both panels animate with sound, Elly walks completely through,
   the compass returns, and movement resumes.
7. Turn around and cross the same passage in the opposite direction.
8. Confirm the reciprocal traversal also restores the compass and movement.

If either side stalls, press F2 while the frozen field is still visible
before closing DuckStation. That state preserves the exact active field VM
slot and program counter for a deterministic follow-up.
