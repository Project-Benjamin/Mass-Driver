# Mass Driver Dungeon 2.17 - v38 Deterministic Passage Crossing

Version 38 repairs the field-372 hallway passage that opened both panels but
left Elly and Emeralda on the approach side with the compass hidden. Runtime
testing rejected v37 because its blocking `09 FF` party-leader dispatch could
stall before the crossing began. Since `FE53` followed that dispatch, player
control could never return.

## Control-safe crossing

The four internal passages still use their native paired Zeboim sliding
models, sound `0x77`, cameras, and local passage-state writes. They no longer
allocate a leader or follower execution slot while cinematic control is
disabled.

Field-local variable `0x0402`, unused by the donor field, now carries a
four-frame crossing request. Party entities 2 through 12 share one wrapper
on their normal script-1 update. An active actor that observes a request sets
itself to the audited far-side position, reapplies walkmesh layer 0, faces
forward, and stops normally:

| Door entity | Request | Far-side X/Z | Facing | Passage state |
| --- | ---: | ---: | ---: | ---: |
| 17 | 1 | -1155, -187 | 0 | 1 |
| 18 | 2 | -1130, -460 | 4 | 0 |
| 19 | 3 | -1171, 465 | 0 | 2 |
| 20 | 4 | -1159, 199 | 4 | 1 |

Each owner action now has this finite order:

```text
clear request
queue both native opening animations
FE54 cinematic control
door sound 0x77
wait 32 frames for the panels
stage camera
assert the crossing request for 4 frames
clear request and wait 8 settling frames
write the native passage state
restore camera
FE53 player-control restore
queue both native closing animations
STOP
```

There is no `09 FF`, `FE68`, or `FE24` party handoff in these owners. There
is also no script allocation between `FE54` and `FE53`. Panel-opening
allocation occurs before controls are disabled, and panel closing starts
only after controls are restored.

The stability candidate deliberately uses an exact same-field position
transfer rather than another collision-sensitive walk. A smoother traversal
animation can be layered on only after this reciprocal crossing is accepted
in the emulator.

## Verification

The builder now rejects:

- any pre-existing use of request variable `0x0402`;
- any deviation from the exact finite owner sequence;
- any party-script call or unbounded movement handoff in a local owner;
- opening helpers after `FE54` or closing helpers before `FE53`;
- different script-1 pointers among party entities 2 through 12;
- a malformed request dispatcher, endpoint, walkmesh, or facing value.

The complete visible-door verifier is now called directly by the automated
suite. The exact field-372 bytecode test also proves that party action slots
10 through 27 remain unused.

Only packed canonical file 1350 differs from v37:

```text
1350_field_372.bin: 36,324 -> 36,696 bytes
```

All other 137 packed replacements are byte-identical to v37.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v38.bin

BIN size: 692,852,160 bytes
raw sectors: 294,580
BIN SHA-256:
bb7c6a6cbf4f4b433ad1e36ffc263db516b1d41c385e9334cedd442fdb56db3b

packed staged replacement comparison:
138/138 exact, totaling 7,792,342 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 143 passed, 1,854 subtests passed
```

Runtime acceptance is not claimed until both directions pass manually.

## Manual acceptance

Do not load an older F2 state; DuckStation states retain the mounted image
and already-loaded field script.

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and cold-boot v38.
3. Restore auxiliary power through the research annex.
4. Return to the field-372 service hub.
5. Open the internal two-panel passage and confirm that both panels animate
   with sound, the party reaches the far side, the compass returns, and
   movement works.
6. Turn around and cross the same passage in the opposite direction.
7. Confirm the reciprocal traversal also restores the compass and movement.

If either side stalls, press F2 while the frozen field is still visible
before closing DuckStation. The state preserves the exact field VM state for
the next forensic pass.
