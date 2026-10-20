# Mass Driver Dungeon 2.31 - v52 Archive-Control Chamber

Version 52 replaces the repeated post-gate checkpoint with a distinct
Zeboim-era archive/control room and puts launch authorization on a genuine
built-in console:

```text
                                      west sliding bulkhead
726 -- east service stairs --> 376 ------------------------> 377
                               archive console e13           gallery A
```

This is an original, canon-conscious fan reconstruction. It is not recovered
Square script or official cut-content data.

## Unique room source

Target 376 now clones retail Lighthouse underground field 394 rather than
field 385. Field 394 is not used by any other room in this dungeon. Its
archive/news control-room design is visually distinct from the earlier
facility halls and from the three source-385 missile galleries.

The room remains Zeboim-era technology. Version 52 does not introduce a
Solaris, Krelian, or Anima Relic control room.

Target 726's Central Gate still checks exactly two conditions:

- auxiliary power;
- accelerator-rail power.

When both are active, the gate enters target 376 parameter 0 through field
394's east open service-stair threshold. Launch authorization is not required
to cross that mechanical gate.

## Genuine accessible console

Authorization is attached to target 376 entity 13, field 394's native wall
terminal. The build preserves its exact retail initialization, update and
collision controller, layered console scenery, and walkable approach. Only
its X action is redirected to the Mass Driver authorization sequence.

It is deliberately not:

- the gold memory-cube save point;
- a treasure chest;
- an invisible plane dressed up as a terminal;
- a decorative door panel.

The native console is at field coordinates `(175, 123)` with a connected
walkable approach near `(175, 105)`. It uses no `FE55` save-menu opcode.
The original retail action on this same terminal referenced the Mass Driver
missile array, making it a coherent Zeboim control-room donor.

## Citan, battle, and forward route

On first entry, Elly, Emeralda, and Citan are visibly staged inside the room
before control returns. Entering Directive `0320` and
`A-2 / B-5 / C-8 / D-4` at the wall console starts the retained autonomous
Guardian sequence.

The fixed no-Escape encounter still contains:

- Elly in El-Regulus;
- Emeralda in Crescens;
- Citan in Fenrir;
- one 36,000-HP mechanical Guardian.

Victory returns the complete on-foot party to target 376 and sets the
Guardian-completion bit. The room's west wall now contains a real opening and
a separate animated bulkhead at entity 14. Pressing X plays a bounded
retail-form horizontal slide before entering missile gallery A. The reverse
door returns the party clear of the bulkhead and facing into the room.

## Automated and disc validation

Target 376's staged field bundle is canonical 1358:

- size: 128,604 bytes;
- SHA-256:
  `296befa91fafd000fa321a350f3560f79d81fa927e15b22d46f4d744af45166c`.

Its graphics bundle is canonical 1359:

- size: 239,616 bytes;
- SHA-256:
  `969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd`.

Release artifacts:

```text
work/mass_driver_v52_stage
output/Xenogears_PW_CD2_mass_driver_standalone_v52.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v52.cue
```

Final BIN:

- size: 694,794,912 bytes;
- raw sectors: 295,406;
- SHA-256:
  `6d95812eb38d809107fe305861278d800e4d3d24c07c94e5153bfd3a351279a4`.

Final CUE SHA-256:
`b6409270efb86d5e2a6e380cf3c5e2e1a526e84a7a938b34c272235a7575f560`.

All 149 staged replacements, totaling 9,680,343 bytes, were extracted from
the completed BIN and compared exactly: 149/149 matched. The standalone boot
sector retains valid MODE2/Form1 EDC/ECC and SHA-256
`79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc`.
The full suite passed 163 tests and 1,923 subtests.

## Focused runtime acceptance

Cold boot the v52 CUE and choose New Game. An F1 state from v51 or earlier
restores its older mounted disc and already-loaded field code, so it cannot
test this room. Make a fresh F2 state only after v52 has cold-booted.

1. Restore auxiliary power and activate the rail interlock at Archive Annex
   368's native console.
2. Open target 726's Central Gate. Confirm it transitions through east service
   stairs into a room that does not resemble the repeated v51 checkpoint.
3. Confirm the party faces inward and Citan is visibly present with Elly and
   Emeralda.
4. Walk inward to the built-in wall console and press X. Do not use a gold
   save point or chest.
5. Confirm the console opens the authorization choices, not the Save menu.
   Enter `0320`, then `A-2 / B-5 / C-8 / D-4`.
6. Confirm the code is accepted before the Guardian warning and that the
   three intended Gears appear in battle.
7. Win the battle and confirm the party returns to the same archive room with
   movement restored.
8. Open the west bulkhead. Confirm it visibly slides before entering gallery
   A and that immediately backtracking returns through the same doorway.

