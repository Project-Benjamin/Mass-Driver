# Mass Driver v72: Two-character dungeon continuity

Version 72 makes Elly and Emeralda the complete active party from the dungeon
entrance through the Defense Archive, the below-grade Defense Bay, and the
Guardian battle. Citan no longer joins in target 376, gives no archive or bay
briefing, and never participates in a dungeon battle. The Guardian encounter
now boards only El-Regulus and Crescens; Fenrir is absent and party slot 2
remains empty.

Citan's first visible dungeon appearance is instead at the very end of
Central Control. After the historical afterimage and Elly's present-day
response, he arrives under the locked final fade as a temporary trajectory
assistant. He helps Elly hold the capsule's ascent course, takes part in no
combat, and is removed with `FE19` by the guarded field-617 return before
playable world-map control resumes. Elly and Emeralda therefore enter,
complete, and leave the dungeon as the same two-character party.

The revised continuity is:

```text
world-map entrance through target 376
    -> Elly and Emeralda only
target 376 authorization console and north-wall lift
    -> no Citan join or briefing
target 384 Custodian reveal
    -> Elly boards El-Regulus
    -> Emeralda boards Crescens
    -> party slot 2 remains empty
    -> two-Gear Guardian battle
target 384 victory and reciprocal return
    -> Elly and Emeralda restored on foot
five reserve magazines and target 728
    -> Elly and Emeralda reach the final launch
target 728 final launch sequence
    -> Citan appears for the first time
    -> temporary trajectory assistance; no battle
field 617 guarded world-map return
    -> FE19 removes Citan
    -> Elly and Emeralda return outside
```

## Defense Archive and Guardian contract

Target 376 preserves Elly and Emeralda's natural east-door arrival. It does
not execute a party-add operation for Citan, and the donor field's entity-3
party stub remains dormant. The wall console still requires Directive `0320`
followed by `A-2`, `B-5`, `C-8`, and `D-4`; acceptance sets authorization bit
4, returns control in the archive, and unlocks the distinct north-wall lift
without beginning combat upstairs.

On the first authorized target-384 entry, the short Custodian sequence now
addresses only Elly and Emeralda. Its fixed battle setup assigns and mounts:

- Elly in El-Regulus;

- Emeralda in Crescens.

No Citan or Fenrir assignment is made, no third pilot is enabled or mounted,
and party slot 2 stays empty. Formation 15 remains the isolated 36,000-HP
Guardian from enemy resource set `0x10` in Goliath Factory arena `0x0B`, with
Escape disabled and random weight zero.

Victory still returns to target 384 instead of forcing an upstairs field
change. The cleanup preserves the two Gear assignments, restores Elly and
Emeralda on foot, sets Guardian-defeated bit 5, and leaves the bay traversable.
Entity 18 remains the reciprocal X-operated route to target 376 parameter 2.

## Final Central Control handoff

Elly and Emeralda remain the only present-day party during Central Control's
technical prelude, historical afterimage, and Elly's response. Only after
that response does the room enter a locked black fade and stage Citan at the
guidance station at `(-30, 118)` on walkmesh 0.

Citan's role is deliberately narrow. He is a temporary launch assistant who
helps hold the capsule trajectory while Elly releases Taura's nanomachine
payload. Arrival bit 7 records that final appearance for the interrupted
launch path, but he has no dungeon exploration or battle role.

The released Mass Driver world-map cinematic still follows the authored
launch. Its standalone-only field-617 guard clears the retail return flag,
executes `FE19` for Citan, and restores the original Elly/Emeralda dungeon
party at playable world-map position 21. Ordinary retail field-617 parameters
and saves retain the original director path.

## Packed v72 resources

The final v72 manifest records these field and launch replacements:

| Component | Canonical ID | Size | SHA-256 |
| --- | ---: | ---: | --- |
| target-376 field bundle | 1358 | 134,924 | `08497bc822094c13b9abbb0a6eac580a0ed65233efa29fbcc7e71f6ab82fcc50` |
| target-376 graphics | 1359 | 239,616 | `969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd` |
| target-384 field bundle | 1374 | 133,660 | `968ff5955a933343cdec591a46b446d45f0d9f8072f40a84584b7f31e8dc28f3` |
| target-384 graphics | 1375 | 440,320 | `cb3cdcd7b61326e7d4aa3e54e7570abed2bcc3af295f4fd3cdbb288cb2896000` |
| target-728 field bundle | 2062 | 52,912 | `5e2a406e606cf154ee17ebd826367dc0b2f8d7c4d4d01452d0ee5af7154f9d4c` |
| target-728 graphics | 2063 | 204,800 | `129daa36749f9ac9ecc17ed318a9246bb5620b22c277e0e7063898023066be1d` |
| field-617 launch-cinematic return bundle | 1840 | 71,180 | `d35a13ab5be99c4ebb6e3934bd4ab0c00613839d810c2a4984dae70adbdefb26` |

The corresponding embedded field payloads are:

| Payload | Size | SHA-256 |
| --- | ---: | --- |
| target-376 script | 2,916 | `4411e60b7b78a520ea84c1060e74be6c073a38233a11aa76e14dddef53530116` |
| target-376 dialogue | 2,209 | `c357dfe6ad636f5e1d0f80f8b8e598ce17c5623ceccad6979c83c36ab51d892c` |
| target-384 script | 19,819 | `1f5d1010e72effcc7905fdbc7930de62e31f54c2fe77225061cf82bce807b575` |
| target-384 dialogue | 820 | `499d5722dceeb5e67da358b7917ed575e26a632a166e5498df0652b58f472996` |
| target-728 script | 2,771 | `1e5f2084366d029f47c8d58a5458a055a38979be61d5589dad3cbff136704070` |
| target-728 dialogue | 4,762 | `81dfcada3204f406e1390bda06714d60237ac0afa9cd57c18206228c12d91215` |
| field-617 launch-return script | 15,547 | `08b5c0a7cdf0b4aa31eca2942b831c481b0f3961475e6f93f93615ab515d33ef` |
| field-617 dialogue | 13,328 | `6bde74052340accfa0d370c688435fbf3294396768599e1bfd9d7ced4d52f9fa` |

## v72 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v72.bin` | 695,535,792 | `6834a04e3f1da62e211931a25fc7a3a2ac2d3947da04b9792ae290a41f2e4cff` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v72.cue` | 106 | `b407f03b6de89300cee90796474e18b4170f6868b1d152f046339fd691a14912` |
| `work/mass_driver_v72_stage/manifest.json` | 176,283 | `918b3776c68a0399d0aa82e5aa01da8b084d0023daf49e9d35a9accf7570d9de` |

The image contains 295,721 raw sectors.

## Validation and cold-boot requirement

The final automated suite passes **188 tests and 2,151 subtests**. All 156
manifest replacements, totaling 10,406,787 bytes, re-extract byte-exact from
the v72 image. Their canonical-ID-order aggregate SHA-256 is
`225c1cd8747ba041635f14e6c10888d9fbd212c47f9cb756d43c8c3af7c46f03`.

The replacements occupy 5,148 unique sectors; together with the standalone
boot sector, all 5,149 regenerate byte-exactly as MODE2/Form1. Comparing the
retail source with v72 finds 108,796 changed common sectors and 3,010
output-only sectors. All 111,806 changed or output-only sectors regenerate
with valid EDC/ECC, with zero invalid sectors and zero mismatches.

All 3,565 ordinary undeclared FAT files, totaling 624,830,534 bytes, remain
byte-identical. Their aggregate SHA-256 is
`ab116c665120d6699bee74ddce86f2d76532f41636c531636050c091c23dae43`.
Canonical 22 is the patched system executable; canonical 17 is its overlapping
umbrella entry, so neither is classified as untouched.

Focused cold-boot runtime acceptance remains pending for v72.

The v71 continuation is not compatible with v72. It embeds gameplay RAM from
the earlier continuity in which Citan joined in the Defense Archive and
remained in the active party. It also begins after the Guardian with target
376 already resident, so mounting the v72 image cannot replace that resident
party and room state.

Do not use `output/MASS_DRIVER_V71_CONTINUE.sav` or an older F1 state for v72
acceptance. Cold boot
`output/Xenogears_PW_CD2_mass_driver_standalone_v72.cue`, choose New Game, and
exercise the route from its standalone bootstrap.

Focused runtime acceptance must confirm:

1. Citan is absent from every dungeon room before the final Central Control
   launch sequence.
2. Target 376 contains only Elly and Emeralda, and accepted authorization
   unlocks the lift without adding Citan or starting combat.
3. The target-384 Custodian sequence boards only El-Regulus and Crescens.
   The Guardian battle has two playable pilots, no Fenrir, and an empty third
   party slot.
4. Victory restores Elly and Emeralda on foot in target 384, and the
   reciprocal lift returns safely to target 376.
5. Elly and Emeralda traverse the remainder of the dungeon without Citan.
6. Citan first appears only after Elly's final Central Control response,
   assists with the capsule trajectory, and enters no battle.
7. The authentic Mass Driver cinematic completes, field 617 executes the
   guarded `FE19` removal, and playable control resumes outside with only Elly
   and Emeralda.
