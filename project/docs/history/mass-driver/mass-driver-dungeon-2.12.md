# Mass Driver Dungeon 2.12 - v33 Internal Passage Repair

Version 33 repairs the field-script lock reported at the hallway-end door
after restoring auxiliary power. It also hardens all four same-field passages
in the service hub against the same follower-synchronization failure.

## Reported failure

The screenshot at `2026-07-25-16-13-34` is target field 372 entity 18. The
door correctly accepted X, hid the compass, played its sound, opened both
model halves, staged the side camera, and moved Elly through the threshold.
The field then remained rendered with Emeralda queued behind her.

Entity 18's action is:

```text
0x0594  start cinematic
0x0596  play native door sound 0x77
0x0599  open helper 26
0x059C  open helper 25
0x059F  stage camera
0x05A4  run current leader's movement script 7
0x05A7  wait for follower-coordinate synchronization
0x05A9  write local passage state
0x05AF  restore camera
0x05B4  close helper 26 asynchronously
0x05B7  close helper 25 asynchronously
0x05BA  restore controls
```

The leader movement is bounded and ends with an exact-position snap, so it
cannot account for a sustained lock. The unbounded `FE24` follower wait at
`0x05A7` is the persistent operation shown in the screenshot.

## Geometry repair

The retail movement-script-7 endpoint `(-1145, -411)` is only six world units
beyond the doorway edge. Elly can reach it while Emeralda remains queued in
the mechanism, leaving `FE24` unsatisfied.

All four local-passage endpoints now use safe connected outbound walkmesh
pockets:

```text
script 4: (-1145, -242) -> (-1155, -187)
script 5: (-1145,  418) -> (-1171,  465)
script 6: (-1145,  244) -> (-1159,  199)
script 7: (-1145, -411) -> (-1130, -460)
```

Xenogears duplicates these scripts for field entities 2 through 12, one for
every playable party actor. Version 33 patches both the bounded walk target
and final exact-position target in all 44 copies, so the repair does not
depend on Elly remaining the leader.

## Bounded synchronization

Each of entities 17 through 20 now uses a 24-frame `WAIT` in place of its
unbounded `FE24`. The longer outbound movement gives followers room to pass;
the finite grace period lets them settle without permitting one blocked
companion to lock cinematic control permanently.

The rewrites are size preserving. They retain each passage's exact local
state value, camera return, both asynchronous close-helper calls, control
restoration, action/collision pointers, and terminal `STOP`. Entity 19 still
terminates before the released-game party scene and story-state write.

No field destination changes because these are intentionally local passages
inside field 372. No dialogue, encounter, shop, world-map, El-Regulus, sound,
graphics, or external-door resource changes.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v33.bin

BIN size: 690,377,856 bytes
BIN SHA-256:
0be65aa49afe66992ca6179ce6f2812096f20cda14bb1406c84b018d44644c20

automated tests: 133 passed, 378 subtests passed
post-build replacement comparison: 122/122 exact

v32-to-v33 staged replacement comparison:
only canonical 1350 (target field 372) changed

boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid
```

## Manual acceptance

1. Close the old v32 session and cold-boot
   `output/PLAY_MASS_DRIVER_STANDALONE.cmd`; it targets the v33 CUE.
2. Restore auxiliary power and return through the adjacent door to the
   four-door service hub.
3. Cross the first internal passage, continue to the door at the end of the
   hallway, and press X.
4. Confirm both door halves open, Elly and Emeralda clear the threshold, the
   doors close, the compass returns, and movement control resumes.
5. Turn around and cross the same passage in reverse.
6. Backtrack through both sides of the first internal passage as well.
