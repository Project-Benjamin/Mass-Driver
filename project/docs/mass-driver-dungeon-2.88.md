# Mass Driver v111 Krelian private-laboratory finale

V111 replaces the former target-507 visual presentation with retail field
595's later playable version of Krelian's private laboratory. The logical route
remains `728 -> 388 -> 507`, so no live Disc 2 story field is overwritten and
the red Zeboim pressure tunnel remains the final approach.

## Final-room transplant

The donor is retail Disc 1 field 595, canonical bundle 1796 and graphics 1797.
It supplies the white private laboratory with its staircase, circular
apparatus, native built-in desk terminal, walkmesh, models, actors, sprites,
and graphics. Retail rescue-scene control is removed. Playable Elly, Emeralda,
and final-only noncombat Citan use entities 1, 3, and 4; the donor's captive
Elly entity 2 is parked.

The red tunnel enters at `(434, -30)` on walkmesh 0, with camera octant 4 and
the party facing inward at direction 5. The tunnel performs the visible north
door sound and animation. In the destination room, static east-panel node 35,
model 18 is translated by `(-64, 0, +64)` into its open wall position. Entity
22 owns a quiet collision return at `(505, 75)` on triangle 61, avoiding an
invisible Cross/X hotspot and preserving reciprocal backtracking to target 388.

## Shifted finale

The final interaction is on the room's built-in desk console, static node 41,
model 26. Entity 5 is aligned directly in front of it at `(0, 450)` on
walkmesh triangle 106, requires the player to face the terminal, and uses bound
operand `0x30`. It owns the locked, launch, and already-completed states.

After authorization bit 4 and Citan-arrival bit 7 are present, the action shows
the Krelian/Miang/Ouroboros archive index and launch dialogue, then runs the
donor's complete mechanism order:

1. Entity 5 script 4 stages the circular assembly.
2. The scene waits 45 frames for that movement to settle.
3. Entity 11 script 4 runs the departure phase, retargeted from the donor's
   captive-Elly actor to playable Elly.
4. Completion bit 6 is set and the authentic Mass Driver world-map event runs
   at position `0x0FFF`, mode `17`.

The guarded field-617 return still removes Citan's temporary slot and restores
Elly and Emeralda outside. A repeat use of entity 5 reports active atmospheric
dispersal and cannot launch a second payload.

Central Control retains Elly's separate first-person Miang/Director memory and
Citan's natural final-route arrival. It still cannot set launch completion or
invoke the world-map event; the capsule-launch scene itself now occurs only in
the transplanted private laboratory after the red tunnel.

## Exact v110-to-v111 payload delta

Only target 507's canonical pair changes. The other 164 declared payloads are
byte-identical to v110.

| Canonical | Kind | v110 | v111 |
|---|---|---:|---:|
| 1620 | field bundle | 166,096 bytes, `ea78dfc08238254a14f13a85cae28b22bd0b29f5acb5faf339d13c6dbc7c1b84` | 107,736 bytes, `32d2719a3a92b91f66943f3151abeb3c8dc99f88c391510cbca99922ae7b1c19` |
| 1621 | graphics | 374,784 bytes, `f4b06ecad813330a5085afb4fa85d491c9b3e6ddd295e9ac6c410e891182f900` | 301,056 bytes, `1f742e0a6587ca88276174392bb8c9ce7c29ebdec2afe0990d18daf44c948a17` |

The transformed target-507 script is 2,811 bytes with SHA-256
`beb32f8305335c13ddfacac8f4679beeac3ed904959d5dd6dffb186a57a603ff`.

## Packaged v111 identities

- BIN: 696,408,384 bytes / 296,092 raw sectors; SHA-256
  `8fbf0a2dd5007b9d6553a6772ea5ad7bf268f5349c08955bda6ca61f875b17be`
- CUE: 107 bytes; SHA-256
  `e850a19e406cff8f096dbbbcbf6df688c1b67766fae2008245df4ae3277e9dcc`
- Manifest: 210,681 bytes; SHA-256
  `57abe00e63a7b07385ddd2d9fb59f8cf0876be0a167be3a154853f561bf5b2f4`
- Manifest inventory: 130 jobs, 166 replacements, 11,373,788 bytes
- Canonical-ID-order replacement aggregate: SHA-256
  `0a1c2a44ac301f3595bbd84f538ccb53470b769b62b74b93f17e8b9bbab32994`

## Validation contract

Structural validation checks donor hashes, the exact pre-opened header
transform, strict walkmesh containment for arrival/console/return points,
party reconstruction, retirement of the duplicate Elly actor, the reciprocal
route, console ownership, native apparatus call order, completion gating, and
the sole raw return transition to field 388. The packaged disc and every staged
replacement are audited against the manifest.

A resident pre-v111 target-507 field contains the old room art and script even
after selecting new media. Completely leave the room and re-enter it from the
v111 CUE, or cold-boot v111 and choose New Game. A fresh-media gameplay replay
of the new final room remains the runtime acceptance step.

A clean v110 in-game save made outside target 507 is valid for this narrow
retest because only canonical 1620/1621 changed. The current control-room save
may continue after launching the v111 CUE. Do not use an F1 state captured in
target 507, because that snapshot restores the old resident field resources.
