# Mass Driver Dungeon 2.29 - v50 Central Control Authorization

Version 50 separates the Central Gate's mechanical power lock from the
launch-authorization puzzle. Auxiliary and accelerator-rail power now open
the gate, its first opening forces the solo El-Regulus boss, and the recovered
Directive and authority code are entered afterward at an adjacent console in
Central Control.

This remains an original, canon-conscious fan reconstruction. It is not
recovered or official cut-content data.

## Progression correction

Version 49 correctly moved the accelerator-rail bypass to Archive Annex 368,
but its Central Gate still required launch authorization. That made a
mechanical access door report a third condition whose code-entry terminal was
elsewhere in the dungeon, leaving the route unnecessarily difficult to read.

Version 50 gives each control one clear purpose:

- auxiliary power and accelerator-rail power operate the Central Gate;
- opening that gate starts the unavoidable launch-tube battle;
- Directive 0320 and the four-point authority code operate the launch system;
- the final console launches Taura's nanomachine capsule only after
  authorization is accepted.

## Persistent objective contract

The seven progression bits remain in persistent ATEL variable `0x03FE`.

| Bit | Objective | Field and entity | Use |
|---:|---|---|---|
| 0 | Auxiliary interlock | 361, entities 13 or 16 | First Central Gate power condition |
| 1 | Accelerator-rail interlock | 368, entity 13 | Second Central Gate power condition |
| 2 | Directive record recovered | 361, entity 12 | Enables the first authorization menu |
| 3 | Authority record recovered | 722, entity 15 | Enables the second authorization menu |
| 4 | Launch authorization accepted | 728, entity 16 | Unlocks the final launch console |
| 5 | Launch-tube boss defeated | 726, entity 14 | Prevents the fixed boss from repeating |
| 6 | Capsule launch completed | 728, entity 13 | Records standalone completion |

The gate no longer reads bit 4. The final launch console reads bit 4 after the
only playable route into Central Control has already forced or skipped the
completed boss through bit 5.

## Central Gate and boss

Target 726 entity 14 retains its native Zeboim door sound, helper-model
animation, bounded party movement, and reciprocal transition. Its action now
checks only:

1. auxiliary interlock bit 0;
2. accelerator-rail interlock bit 1.

If either bit is clear, the gate reports that specific power condition.
Missing rail power points to Archive Annex 368's existing console. Launch
authorization is not presented as a gate condition.

When both bits are set and boss bit 5 is clear, the same first-opening routine
brings in Citan and starts Elly's solo, no-escape El-Regulus battle against
the two Griffons. Victory sets bit 5, restores the on-foot party, and enters
target 728. Later uses of the gate see bit 5 and perform the ordinary animated
transition without replaying the battle.

## Central Control authorization

Target 722 still contains the maintenance authority record at entity 15. Its
entity-14 terminal is now route guidance: code entry is available in Central
Control.

After the boss, target 728 entity 16 becomes the two-stage authorization
console. It requires both recovered records before presenting the menus:

1. select Directive `0320`;
2. select `A-2 / B-5 / C-8 / D-4`.

Incorrect answers are rejected and remain retryable. The correct pair sets
launch-authorization bit 4. Reusing the console after acceptance displays its
active status rather than repeating the puzzle.

Target 728 entity 13 remains the separate payload-launch console. Before bit
4 is set, it directs the player to the adjacent authorization console. After
authorization, it launches Taura's nanomachine capsule, sets completion bit 6,
and returns the party to the world map.

## Backtracking and softlock audit

Central Control's visible entity-14 return door remains reciprocal:

```text
728:e14 -> 726:p1
```

If either record was missed, the player can leave Central Control and return
through the launch-support and service routes:

```text
728 -> 726 -> 375 -> 372 -> 361  Directive 0320
                             `-> 722  authority record
```

The two power bits remain persistent, and boss bit 5 suppresses the completed
fight. Returning to target 728 therefore does not close the gate, trap the
party, or repeat the boss. The return door itself has no authorization check.

## Route guidance

The active guidance now distinguishes access from launch authorization:

- the service hub identifies the Research Annex, Materials Storage, and
  Archive Annex 368;
- Materials Storage identifies Central Control as the code-entry location;
- the Central Gate reports only missing auxiliary or rail power;
- the final launch console points to the adjacent Central Control
  authorization console.

The v49 Annex 368 rail-console and Magnetic Conduit save-point corrections
remain unchanged and are documented in
[the v49 notes](mass-driver-dungeon-2.28.md).

## Expected v50 release artifacts

```text
stage:
work/mass_driver_v50_stage

image:
output/Xenogears_PW_CD2_mass_driver_standalone_v50.bin

cue:
output/Xenogears_PW_CD2_mass_driver_standalone_v50.cue

BIN size: 693,263,760 bytes
raw sectors: 294,755
BIN SHA-256: deb6fb8b45787363aec763d82f02bfc533c77fd5194421fe98eab13d11a1b5e3
CUE SHA-256: fa84d0b298db746c7dce5a7ab841dbcb71a5b9816576d79b193141e32d5781e5
staged replacement count: 140
staged replacement bytes: 8,153,246
packed-entry comparison: 140/140 exact
boot-record SHA-256: 79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 EDC/ECC validation: valid
automated tests: 152 passed
automated subtests: 1,892 passed
```

These values come from the completed v50 image and its independent
post-build extraction/validation run.

## Focused runtime acceptance

Cold boot the v50 CUE and choose New Game. Do not use an F1/F2 state made
with an older image.

1. Recover Directive 0320 in target 361 and operate either auxiliary control.
2. Enter Archive Annex 368 and use its native console to restore rail power.
3. Optionally recover the authority record in target 722 before approaching
   the Central Gate.
4. Confirm target 726 reports auxiliary or rail power when either is missing,
   but never requests launch authorization.
5. With both power bits set, open the gate and confirm the native door
   animation leads into the mandatory solo El-Regulus battle.
6. Win the battle and confirm the party reaches target 728 on foot with Citan
   and Emeralda restored.
7. If a record was skipped, use target 728's return door, recover it, and
   return through the same gate without repeating the boss.
8. At target 728 entity 16, confirm a wrong menu choice is rejected and
   `0320` plus `A-2 / B-5 / C-8 / D-4` is accepted.
9. Before authorization, confirm entity 13 refuses the launch and identifies
   the adjacent console. After authorization, confirm it launches Taura's
   capsule and returns the party outside.
