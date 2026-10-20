# Mass Driver Dungeon 2.13 - v34 Storage-Annex Door Repair

Version 34 repairs the second distinct field-script stall exposed after the
v33 internal-passage fix. It also separates that defect from the intentional
accelerator-rail objective gate.

## Exact F2-state identification

The two new screenshots are:

```text
2026-07-25-16-45-09
2026-07-25-16-48-29
```

Both show target field 372's east storage-annex doorway. The surviving F2
state, `SLUS-00669_1.sav` at 16:48:22, proves that v33 was running and places
Elly on walkmesh triangle 34 at approximately `(377, 1157)`, immediately in
front of visible door entity 23. Entity 23 leads to target field 722,
parameter 0.

F2 saves to the currently selected slot, so the second press replaced the
first state. There is one current state rather than a distinct before/after
pair. It was still sufficient to identify the exact trigger and loaded ATEL
script.

This is not field 372 entity 18, repaired in v33. Entities 17 and 18 are the
two action sides of one same-room internal passage; there is no separate room
containing its “other end.” Entity 23 is a different external mechanical door
to the materials-storage annex.

## Failure and repair

The retained v33 entity-23 action performed:

```text
start cinematic
play native door sound
run entity-31 native opening animation
run an unbounded FE68 leader walk to (412, 1154)
change to field 722 / parameter 0
```

`(412, 1154)` is the audited incenter of transition-pocket triangle 36, but
the retail FE68 operation can still remain pending at this small one-way
threshold. That leaves the door visibly open and prevents the checked field
change from executing.

Version 34 preserves the cinematic lock, door sound, entity-31 model
animation, safe destination point, and field-722 transition. It assigns
previously unused script 31 on all eleven possible party actors (entities
2-12) to the retail bounded movement form:

```text
bounded walk to (412, 1154), maximum 120 updates
exact-position snap to (412, 1154)
recompute the actor's walkmesh triangle
stop
```

Entity 23 invokes that shared party script through the current leader and
then performs the original field change. Even if pathing cannot finish the
short walk normally, the bounded routine reaches its safe snap and cannot
hold the doorway forever. The collision slot remains STOP, so the closed door
still responds to X rather than teleporting on contact.

The transformed target-372 bytecode grows only from 2,256 to 2,288 bytes:
15 bytes for the shared bounded waypoint and 17 bytes for the replacement
door action. All other dungeon resources are identical to v33.

## Railway warning is an objective

“The accelerator rail interlock is offline” comes from target field 726's
final Central Control gate, entity 14. It is expected when persistent
interlock bit `0x0002` has not been set.

The required visible control is target field 725 entity 16, in the
magnetic-conduit hall. From the locked gate room, use its other visible door
to enter that hall, activate the console with X, and return. The longer route
is field 372 entity 16 -> target 727 -> target 387 -> target 725.

The railway gate is unrelated to field 372 entities 17, 18, or 23. Entity 23
instead leads to field 722's address record and launch-authorization
terminal.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v34.bin

BIN size: 690,377,856 bytes
BIN SHA-256:
9883628d0927b79961583439df609f3112134bc4d20db8e04cf05f63d03197d1

automated tests: 133 passed, 388 subtests passed
post-build replacement comparison: 122/122 exact

v33-to-v34 staged replacement comparison:
only canonical 1350 (target field 372) changed

boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid
```

## Manual acceptance

The existing 16:48 F2 state embeds the v33 disc path and restores v33's
already-loaded field-372 script in PlayStation RAM. Loading it and immediately
pressing X cannot test this repair, even if v34 was launched first. Cold-boot
v34 and re-enter field 372 so the new resource is loaded.

1. Close DuckStation and run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Reach the service hub and approach the exact doorway shown in the 16:45
   and 16:48 screenshots.
3. Press X. Confirm the native door sound and opening animation play, Elly
   crosses the threshold, and the materials-storage annex loads.
4. Turn around and use the annex's reciprocal animated door. Confirm field
   372 reloads with the party facing forward, away from the door behind them.
5. Test the v33 internal passage in both directions; both halves must close,
   restore the compass, and return movement control.
6. At an accelerator-rail warning, use the room's other door, activate the
   visible magnetic-conduit-hall control with X, return, and confirm the final
   gate advances to its next unmet condition or opens when all three
   prerequisites are complete.
