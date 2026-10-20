# Mass Driver v92 Elly-only Central Control vision

V92 reframes the final Central Control vision as an experience visible only to
Elly. Emeralda sees the empty present-day room, notices Elly reacting to
something that is not there, and asks what happened. After the vision ends,
Elly explains that she saw the launch officers, heard their discussion, and
recognized the Prime Minister's adviser as Miang.

The historical speaker is now identified directly as `MIANG`, with
`PRIME MINISTER'S ADVISER` retained as her period title. The exchange makes her
role explicit without having her issue the launch order herself: she turns the
officers' doubts into reasons to fire until the director experiences the choice
as his own.

## In-game cutscene staging

The vision now uses native field-camera instructions instead of presenting the
entire exchange from the normal gameplay view. Central Control target 728 runs
the following sequence:

1. The camera moves to Elly as she notices the room changing. Emeralda says
   that she sees no one and that the room is empty.
2. Under a short fade, the current-party followers are hidden and the three
   historical actors appear.
3. A wide composition establishes the launch director and officer, a closer
   moving composition isolates Miang during her pressure campaign, and a final
   wide composition frames the order to execute Directive 0320.
4. Under a second fade, all three historical actors are hidden, the camera
   cuts back to the present-day Elly composition, and the followers are
   restored before the room is revealed.
5. Emeralda explains that she saw only Elly staring at nothing. Elly recounts
   the officers, their voices, and Miang, then connects the old weapon to the
   capsule's present healing purpose.
6. Only after that explanation does Citan enter for the final trajectory and
   capsule-launch exchange. A final fixed composition frames his arrival, then
   the native camera mode is released before the launch transition.

The follower visibility change is limited to the apparition itself. The ghost
actors begin hidden, are shown exactly once for the historical exchange, and
are hidden again before Emeralda's present-day response. Citan remains absent
from every earlier dungeon room and battle; this final launch assistance is
still his only appearance in the dungeon.

## Static coverage

The reconstruction tests check the authored dialogue for the Elly-only vision,
Emeralda's confusion, Elly's explanation, and the `MIANG` identification. The
target-728 script test also verifies the exact native camera target/eye
envelopes and their ordering around dialogue, both fades, follower hide/show,
single ghost reveal/removal, Citan's post-explanation staging, and final camera
release. The historical-asset test continues to verify the native actor art,
entity slots, palettes, and restored hidden state.

## Packaged delta from v91

Exactly one declared canonical resource differs from v91: 2062, the Central
Control target-728 field bundle. It grows from 52,912 to 53,380 bytes and has
SHA-256
`c7b7e5f91dae13ac7affabe1fb1c310f702425f42e14fc5a1072fa3f99dda9f2`.
Its 2,967-byte script has SHA-256
`aa93c971fe711dcad4487c98fc7675f4d182647dd67d76e15ac698607c4b4d0a`;
its 4,987-byte dialogue has SHA-256
`9cb0df9f124d169d85f1329860aaf84f769a0771d4289fcb2c7b40a8412bdd94`.
Canonical 2063 graphics and every other declared replacement are
byte-identical to v91.

## Packaged v92 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v92.bin`: 695,338,224 bytes / 295,637 raw sectors, SHA-256 `d5819da9fc76a4637b31b03a5c1baa154e3d3185d7165428ebbb753fcab8b4a3`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v92.cue`: 106 bytes, SHA-256 `05a876247789c1417274c8792d51bfbef6027958c6cd260559be8f4e6d3bbfc6`
- Manifest `work/mass_driver_v92_stage/manifest.json`: 190,187 bytes, SHA-256 `67e3daaccd778c302155853908213be436e732e81940e29296b4a6d3e30b185b`
- Replacement aggregate: 126 jobs, 158 declared replacements, 10,433,356 bytes, SHA-256 `6c4fc9f58b44ddfaf91690474554a519552e7ae15aa32b380887b5486dfba383`
- Complete automated suite: 204 tests and 2,382 subtests, with no failures, errors, or skips

## Runtime acceptance

Fully quit DuckStation, boot
`output/Xenogears_PW_CD2_mass_driver_standalone_v92.cue`, choose New Game, and
load no older F1 state or in-game save. An older full-machine state restores its
previous mounted disc and resident Central Control resources, so it cannot
validate the v92 scene.

Reach Central Control with the launch authorization complete and activate the
launch console. Confirm that the camera first moves to Elly and that Emeralda
says the room is empty. During the faded transition, confirm that Emeralda is
not present in the historical compositions, the director, officer, and Miang
appear cleanly, and the camera establishes the officers, moves in for Miang's
pressure, and returns wide for the launch order. Confirm that the adviser is
labeled `MIANG`.

When the vision ends, confirm that every historical actor disappears before
the room returns, Emeralda is visible again, and she says that she saw only
Elly staring at nothing. Confirm that Elly explains what she saw and identifies
Miang. Citan must not appear until this explanation is complete; he should then
enter for the capsule trajectory exchange. Finally, confirm that the scene
releases the fixed camera and completes the launch transition without leaving
the player in a frozen or incorrectly framed field view.
