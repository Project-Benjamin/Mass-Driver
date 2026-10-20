# Mass Driver v99 mounted El-Regulus field motion

V99 gives El-Regulus distinct movement and jump presentation while Elly is
mounted on a normal field map, including the Goliath Factory hall after the
Guardian battle. The six-phase walk, three-stage jump, and four-phase run
families now select appropriate El-Regulus art instead of showing the same
upright canvas throughout. This is a field-sprite correction only: the v98
battle-entry facing and native command-menu idle remain intact, and the
separate world-map sprite is unchanged.

The post-Guardian exchange now says that Elly and Emeralda will leave the
Gears in the lower bay until after Taura's capsule reaches the upper
atmosphere. The south personnel lift still performs the required safe dismount
before returning the party to the Defense Archive, but it does so silently.
The former player-facing instruction about needing to continue on foot has
been removed.

## Field-animation root cause

Canonical 453 is the global non-world-map field sprite for Gear 10. Its retail
336-byte controller already contains all sixteen animation programs needed by
the field engine. In particular, animation 3 contains the native Gear jump
sequence:

```text
C6 0B 15 A1 9D 05 86 33 87 C6 0C 21 C6 01 33 80
```

That program supplies the Gear-specific preparation hooks, physical launch,
apex wait, landing wait, and completion. The controller was not the missing
piece. V78's canonical-453 rebuild had mapped all 65 frame records onto five
flattened upright canvases. Timing and vertical movement continued to run, but
El-Regulus's art did not visibly change between idle, travel, launch, and
airborne states.

V99 preserves the controller byte-for-byte. Its SHA-256 remains
`beb29b73e796f48f7001e0470168708f0fc90f7cab8a17075a4261086a4431ea`.

## Distinct pose banks

The rebuilt frame section now contains three five-direction pose banks:

- **Idle:** the authentic Square-authored El-Regulus art extracted from
  Execution Site field 657.
- **Travel and airborne:** the established forward-driving derivatives of
  those same five authentic directions, retaining their checked crops and
  field draw origins.
- **Crouch and launch:** five new 86-percent-height derivatives compressed
  around each authentic direction's visible foot anchor. The feet therefore
  remain planted while the upper body lowers in preparation for launch.

No unrelated character or Gear pixels are introduced. The original three
palette banks are retained, and the patched 100-byte palette still has
SHA-256
`c3fd05839804be66115570da992e542f27a9517b163c7cc8caf0dde62e6e9aa4`.
The five combined crouch canvases have SHA-256
`b2b3a9e1622b46464f9dbe476914f2a65c5d34909e53ba98f28618fa97516c26`.

The 65 frame records use the existing cadence families:

| Animation family | Frame IDs | Per-direction presentation |
| --- | --- | --- |
| Walk | `1..30` | Six forward-driving frames with vertical phases `0, 1, 2, 3, 2, 1` |
| Jump | `31..45` | Upright -> feet-anchored crouch -> forward airborne |
| Run | `46..65` | Four forward-driving frames with vertical phases `0, 1, 2, 1` |

Walk and run convert each phase into the native two-pixel hover/bob offset.
Jump leaves its image origins stable because animation 3 already controls the
physical crouch, launch, apex, and landing sequence.

The converted frame section remains 45,052 bytes, with 26,912 meaningful
bytes followed by checked zero padding. Its SHA-256 is
`25a9e86a5da4aaf455741a003b13bbbb82d16532403eee292b30b24fd049132e`.
The complete 45,510-byte decoded canonical has SHA-256
`4a504751d5bcb94528b5e95936d6535ffc954b03c421c9fffe0c8fcfd1563014`.

| Canonical 453 result | Packed size | SHA-256 |
| --- | ---: | --- |
| v98 flattened field art | 8,848 | `41c2216b8169410295efbedd656297ddaf6d54dbbdbc96ded692c77df79d54c3` |
| v99 distinct field poses | 13,844 | `2035ee09d4c11e1497f4f25491c5cc0ce9dd80d06c06131fdc2bda4f46333f1b` |

## Post-Guardian handoff

Target 384's one-time post-battle block now reports the defeated Custodian and
unlocked west bulkhead, then has Elly say:

> We'll leave the Gears here until after we launch the capsule into the upper
> atmosphere.

Emeralda answers that they will return for them. This keeps the intended Gear
plan in character dialogue and places it before the party leaves the bay.

The south door's mechanical behavior is deliberately unchanged: its
human-scale transition dismounts both active slots, clears the two mounted
staging bits, opens the native leaves, and returns Elly and Emeralda to target
376 parameter 2 on foot. Only its old dialogue invocation is removed. There is
no `DISMOUNT REQUIRED` message and no instruction to proceed on foot.

The canonical-1374 delta is:

| Target-384 component | v98 | v99 |
| --- | --- | --- |
| Complete bundle | 162,424 bytes, `059a4a881c5428a21dbc37dc4f0fac2cb6c6b5d26c70c966a2524cdca330dd5e` | 162,324 bytes, `75fad1781aa359ddba478e09da09b6f5bc3e91934fd7242f457a1f68c467c532` |
| Script | 21,207 bytes, `ca016611e19974493f7b8e32d8451ed64bde18ba0953476864e216664f259b3a` | 21,202 bytes, `e03a314c117cf576f1477967fad830fb0b83cdaa489db05ed39afcf29ab3c588` |
| Dialogue | 1,112 bytes, `bc981e1f36278ffc9757afb4c8fc638640d8b20562f19e2a28d1a64861a808c9` | 1,017 bytes, `168bf7a52807850f7a471df89f244a562cba03e96c5468bb2a7403daaca82791` |

The field-617 launch return is byte-identical to v98. Citan is still removed
there before Elly and Emeralda return outside, and no second Gear-planning
exchange is injected after the retail cinematic.

## Isolation

Relative to v98, only declared canonicals 453 and 1374 differ. Target 384's
canonical-1375 Goliath Factory graphics, canonical 2960 battle programs,
canonical battle overlay 38, Crescens, Guardian, world-map El-Regulus sprite,
Central Control, and field-617 launch return remain byte-identical.

The v98 native battle entry is therefore preserved in full: animation 0 still
uses native `60 00 43 00` slot-center facing and hands off to the repeating
keyframe-1 idle after the delayed `21 00 6D 00` completion handshake. V99 does
not alter attacks, Attack-Level progression, deathblows, battle damage, or
Infinity mode.

## Packaged v99 identities

The completed v99 package is:

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v99.bin`: 695,839,200
  bytes, 295,850 raw sectors, SHA-256
  `87e2567a13f3cbb3a09f71b8f55db45190ba89bf8823a6ad8128454781414c42`.
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v99.cue`: 106 bytes,
  SHA-256
  `c2128564ac07ce01cf35af9b9c341bb76154ef8b58d99c2fde4dc13f84f4aa41`.
- Manifest `work/mass_driver_v99_stage/manifest.json`: 197,542 bytes,
  SHA-256
  `d506954981bec569616a7c47c754ddb4de9232e9ea90966561e915fd46039dc6`.
- The manifest has 128 jobs and 162 declared replacements totaling 10,875,784
  replacement bytes. Its canonical-ID-order aggregate SHA-256 is
  `78cdb68c8bf3cd6d56c726e637ca4942cc11cdfce287a6f758535c3cc3e95e3e`.
- The complete automated suite passes 207 tests and 2,585 subtests with no
  failures, errors, or skips.

The preserved v98 package identities and its canonical-2960 native-idle delta
remain in [the v98 release notes](history/mass-driver/mass-driver-dungeon-2.75.md).

## Cold-boot runtime acceptance

1. Fully quit DuckStation and launch
   `output/PLAY_MASS_DRIVER_STANDALONE.cmd`. Verify that it selects the v99
   CUE, choose New Game, and load no older F1 state or in-game save.
2. Complete the code terminal and Guardian encounter normally. Confirm that
   the post-battle exchange says the Gears will remain until after the capsule
   reaches the upper atmosphere. It must not tell the player to dismount or
   proceed on foot.
3. After control returns in target 384 with both pilots mounted, move
   El-Regulus in every available direction. Confirm its forward-driving art
   and visible six-phase hover cadence replace the former static upright glide.
4. Trigger the normal field jump. Confirm a readable upright -> crouch ->
   airborne -> landing progression, with the physical launch, apex, and landing
   behavior still completing normally. El-Regulus must remain controllable.
5. Run through the hall and confirm the four-phase field cadence. Crescens and
   unrelated field actors must remain unchanged.
6. Check the offline north door, then backtrack through the south personnel
   lift. It must dismount both pilots and return the party upstairs safely
   without displaying the removed on-foot instruction.
7. Continue through the dungeon and launch the capsule. Confirm Central
   Control, Citan's final-only assistance, the retail launch cinematic, and the
   Elly/Emeralda world-map return behave exactly as in v98.
8. Enter a completely new Gear battle from v99 media and confirm El-Regulus
   still faces its slot-center target and visibly idles at the initial command
   menu before the first attack.

Runtime acceptance requires both the new mounted-field animation and the quiet
south-lift handoff. A resumed v98 field or F1 state keeps its resident
canonical 453 and target-384 script and cannot validate either change.
