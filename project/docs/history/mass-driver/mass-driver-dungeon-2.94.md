# Mass Driver Dungeon 2.94 - Missile Command arcade-authenticity pass

This pass replaces Missile Command's short ten-wave approximation with a
bounded translation of the original Atari arcade economy. The Defense Archive
game now has independently controlled and stocked batteries, overlapping ABMs,
chain-reaction fireballs, attackable bases, the arcade ordinary-missile quotas
and score multiplier, bonus cities, and an endurance loop that ends only when
the city reserve is exhausted.

The implementation remains a native Xenogears field-script game on the shared
28x16 archive CRT. It adopts the original's consequential decisions rather than
claiming cycle-, pixel-, or ROM-perfect emulation.

## Reference baseline

The gameplay contract was checked against these preserved sources:

- Atari's 1980 operation, maintenance, and service manual, especially printed
  pages 8-9 for the manufacturer settings, three bases, ten ABMs per base,
  rearming, attack types, and play-until-the-last-city rule:
  <https://www.arcade-museum.com/manuals-videogames/M/MissileCommand.pdf>
- The revision-3 ROM disassembly and gameplay notes for battery speeds, object
  limits, chain explosions, target rules, scoring, city reserves, and end-wave
  ordering: <https://6502disassembly.com/va-missile-command/>
- The ROM-derived wave guide for ordinary-missile quotas, speed progression,
  fliers, colors, and the two-wave score-multiplier ladder:
  <https://6502disassembly.com/va-missile-command/wave-guide.html>
- The annotated revision-3 listing and preserved Atari revision-1 source used
  to resolve implementation details and revision differences:
  <https://6502disassembly.com/va-missile-command/MissileCommand.html> and
  <https://github.com/historicalsource/missile-command>

The selected baseline is revision 3 with the cabinet's recommended six cities
and one bonus city every 10,000 points. Revision-2 marathon bugs are not part of
the target behavior.

## Implemented arcade contract

| System | Defense Archive implementation |
| --- | --- |
| Batteries | Left, center, and right batteries each begin a wave with 10 ABMs. Square fires left, Cross fires center, and Circle fires right; the HUD reports `L`, `C`, and `R` separately. |
| Concurrent defense | Each battery owns one ABM/fireball lifecycle, allowing three ABMs in flight together. The center ABM advances faster than either side ABM. A held button is latched and a busy or empty battery cannot spend another missile. |
| Chain reactions | Each player fireball uses a phase-matched radius-two diamond. A destroyed attacker can seed one of three bounded secondary fireballs, and those blasts can destroy and score further attackers before all affected cells are erased. |
| Ground targets | Incoming missiles select among six cities and all three batteries. A battery hit loses its remaining stock and shows empty for the rest of the wave; every battery is rebuilt and rearmed at the next wave. City losses remain limited to three per wave. |
| Wave pressure | Ordinary-missile quotas for waves 1-19 are `12, 15, 18, 12, 16, 14, 17, 10, 13, 16, 19, 12, 14, 16, 18, 14, 17, 19, 22`; later waves retain 22. Up to six attackers may be active, and their step delay tightens to a bounded maximum-pressure rate. |
| Scoring | An intercepted ordinary missile is worth 25 points, each surviving city 100, and each unused ABM 5. All three values use the arcade multiplier: x1 on waves 1-2, x2 on 3-4, through x5 on 9-10, then x6. The exact score range is 0-99,995 in five-point units. |
| Bonus cities | Every crossed 10,000-point threshold banks a reserve city. End-wave city and ammo bonuses are added first, then reserves rebuild open craters. A bonus earned while all six cities stand remains banked for a later loss. |
| Endurance | Clearing a wave with at least one restored city continues the game. There is no wave-10 victory. Quota and pressure remain at their maximum while the displayed and persisted best wave caps at 31; zero cities after bonus-city deployment produces `THE END`. |

Triangle pauses during play, Cross resumes, and Circle exits from the pause
screen. Retry, teardown, the shared four-letter pilot profile, and the rule that
the minigame writes no story-progression state are retained.

## Score-record migration

The released v129/v130 record used signature `0x4E4B` and stored Missile
Command's high score in ten-point units in bits 5-14 of the fourth profile
word. That range could not represent the new five-point bonuses or endurance
scores.

Signature `0x4E4C` stores the score in exact five-point units across bits 5-14
of the fourth profile word and bits 10-14 of the shared best-level word. Bits
5-9 of the latter still hold Missile Command's best wave. On first use, a valid
`0x4E4B` record is decoded, converted losslessly to five-point units, repacked,
and signed as `0x4E4C`. Nuke's high score and best level and all four pilot
letters retain their existing bits. Invalid or unsigned legacy words still use
the established safe reset path.

## Intentionally deferred

This pass does not add smart bombs/cruise missiles, bombers, killer satellites,
or MIRV splitting. It also does not emulate the trackball, alternating
two-player mode, operator-selectable city and bonus thresholds, random crater
selection, attract-mode AI, per-wave palettes, or revision-specific scoring
bugs.

The original ROM can keep eight ABMs airborne and twenty explosions active;
the field-script version deliberately caps defense at one lifecycle per
battery plus three chain fireballs. Its D-pad cursor, grid trajectories,
five-beat diamond blasts, six-attacker scheduler, wave-31 record cap, and
99,995-point score cap are native-engine constraints rather than arcade-ROM
claims. Those differences are suitable follow-up work only if their script,
call-depth, persistence, and runtime costs can be bounded.

## Focused and manual validation checklist

Run the focused structural test before packaging:

```text
python -m pytest -q tests/test_build_mass_driver_dungeon.py -k missile_command
```

The focused audit should confirm the three button masks and ammo words, three
player slots, three chain slots, nine ground targets, rearm path, revision-3
quota table, multiplier and score constants, 10,000-point reserve logic,
wave-31 endurance branch, both persistence signatures, and absence of story
progression writes.

For emulator acceptance, fully leave and re-enter target 376 after mounting the
candidate media; a state captured with the old room resident cannot validate
new field code.

1. Open the southeast computer, choose `Arcade Games` and then
   `Missile Command`, and verify the new Square/Cross/Circle battery legend and
   Triangle pause legend. Confirm all three HUD ammo values begin at 10.
2. Aim once and press Square, Cross, and Circle in quick succession. Confirm
   three simultaneous trails launch from the matching bases and that the center
   ABM reaches an equivalent-height target sooner. Holding or re-pressing a
   busy battery button must not consume extra ammo.
3. Intercept a close group. Confirm each destroyed missile scores once, creates
   a secondary blast when a chain slot is available, and can trigger another
   hit. Let every blast collapse and check that no explosion cells remain.
4. Let an attacker hit each battery in separate trials. Its individual ammo
   must fall to zero, its empty art must appear, and the other two buttons must
   continue to work. Clear the wave and confirm all three batteries return to
   10.
5. Confirm wave 1 launches 12 ordinary missiles and wave 2 launches 15. Spot
   check that one interception is worth 25 on wave 1, 50 on wave 3, and 150 on
   wave 11, and that city and unused-ammo bonuses use the same multiplier.
6. Test a score just below 10,000. Cross the threshold during the end-wave
   tally, confirm `BONUS CITY EARNED`, then verify that a crater is restored or,
   with all six cities intact, that the reserve survives until a later loss.
7. Continue beyond the former wave-10 ending. Confirm maximum-pressure waves
   repeat, wave 31 continues without wrapping the displayed record, and only a
   zero-city state with no deployable reserve reaches `THE END`.
8. Load a valid v130 arcade record with known Missile Command score, best wave,
   Nuke score/level, and four-letter tag. Enter once to migrate it, verify every
   displayed value, earn a five-point increment, leave, and re-enter to confirm
   exact persistence.
9. Verify Triangle pause, Cross resume, Circle exit, Cross retry, terminal
   teardown, and normal field control. Recheck `Back`, Nuke launch/exit, and the
   Video Disk prompt/Cancel path on the shared computer.

## Built v131 candidate

The frozen v131 generator produced a 50,560-byte field-376 script containing
48,636 bytes of ATEL bytecode, inside a 192,268-byte field bundle. Focused
gameplay tests, the complete automated suite, script call-depth and opcode-slice
review, and JSON/diff checks pass. The standalone BIN was built and all 175
declared replacements were extracted back out and matched to the stage
manifest by size and SHA-256.

The current candidate is
`output/Xenogears_PW_CD2_mass_driver_standalone_v131.cue`. Its exact BIN, CUE,
manifest, field, and script identities are recorded in `README.md`. No live
v131 emulator acceptance result is claimed; use the checklist above after a
fresh target-376 load.
