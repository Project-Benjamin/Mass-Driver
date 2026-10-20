# Mass Driver v71: Below-grade Defense Bay

Version 71 separates the Defense Archive authorization from its Guardian
battle. Entering Directive `0320` and the four authority points no longer
makes the battle begin beside the archive terminal. The accepted code instead
unlocks a distinct north-wall lift. That lift carries the party into new
target field 384, a below-grade industrial Defense Bay, where a short
Custodian-robot scene leads into the existing three-Gear Guardian battle.

Victory returns the party to the bay on foot. Its entrance remains available
as a reciprocal X-operated route upstairs to target 376, where the defeated
Guardian has unlocked the west bulkhead and the dungeon continues normally.

The resulting progression is:

```text
target 376 wall console, entity 13
    -> correct 0320 / A-2 / B-5 / C-8 / D-4 entry
    -> authorization bit 4; no battle
target 376 north-wall lift, entity 17
    -> target 384 parameter 0
target 384 one-time Custodian reveal
    -> Guardian battle in arena 0x0B
    -> same-field return; defeated bit 5
target 384 entrance, entity 18
    -> target 376 parameter 2
target 376 west bulkhead, entity 14
    -> five reserve magazines and Central Control
```

## Authorization and lift contract

The genuine source-394 wall console remains target-376 entity 13. Its manual
sequence still checks the directive first and then asks for A, B, C, and D
separately. A wrong or incomplete sequence is rejected without changing
progression. A correct sequence sets only launch-authorization bit 4 and
reports that the Defense Bay lift is available.

The boss routine is no longer attached to that console. Citan now directs the
party to the north wall because their Gears and the active Custodian are below.
The west bulkhead remains independently sealed by Guardian-defeated bit 5, so
authorization cannot bypass the new bay.

The new lift has the following checked contract:

- controller entity 17 at `(0, 270)` on walkmesh 0;
- helper entities 18 and 19;
- native-textured paired leaves 14 and 15 with stationary frame 16;
- model anchor `(-44, 301)` and quarter-turn yaw `0x0400`;
- 48-unit X interaction half-width without a narrow facing requirement;
- locked dialogue until authorization bit 4 is set;
- destination target 384 parameter 0.

The presentation reuses the Defense Archive bulkhead's weathered native
leaves and frame as a narrower, recessed north-wall freight lift. The leaves
remain closed during the short ordinary field-change fade. This preserves a
solid lift silhouette and prevents field 394's baked north wall from being
exposed during travel.

## Defense Bay provenance and geometry

Target 384 occupies retail Disc 2 canonical slots 1374 and 1375. Both were
allocated 24-byte `It's CDMAKE Dummy !` placeholders before v71, so the new
room does not overwrite a live Disc 2 field.

The donor is retail field 403, the Lighthouse elevator-bottom / Goliath
Factory industrial floor that already supplies the Guardian battle's enclosed
Gear-scale arena `0x0B`.

| Donor resource | Canonical ID | Size | SHA-256 |
| --- | ---: | ---: | --- |
| source-403 field bundle | 1412 | 133,200 | `bdf72c325201d6931539ca26ab693fcd63535f8e425a064306f4c3e8adf414a8` |
| source-403 graphics | 1413 | 440,320 | `cb3cdcd7b61326e7d4aa3e54e7570abed2bcc3af295f4fd3cdbb288cb2896000` |

Its main floor is one connected component containing all 520 triangles and
344 vertices. The checked bounds are `x=-2926..3054`,
`y=-192..49`, and `z=-1179..1563`. Target-384 parameter 0 places
the party at `(350, -600, walkmesh 0)`, inside triangle 413. Actor direction
0 faces north into the bay. Camera direction 4 keeps the eye on the open
interior side instead of behind the party across the south wall.

The donor's Lighthouse story paths are absent:

- its automatic Gear-map switch and unconditional party mounts are removed;
- its random encounter initializer is removed;
- the source story selector and five-destination dispatcher are parked;
- all old transitions to fields 391, 393, 395, 398, and 404 are neutralized;
- its far Lighthouse endpoint is retired.

The room remains navigable on foot before and after the fixed battle.
Source-403 environmental animation and its native party actor banks remain
available. The near industrial doorway becomes the sole return controller,
entity 18 at `(372, -676)`, with a wide X action and a STOP collision slot.
It plays the facility-door sound, waits a bounded 12 ticks, and returns to
target 376 parameter 2 rather than activating on contact.

That receiving parameter is `(0, 245, walkmesh 0, actor direction 4,
camera direction 2)`, one checked step inside the Defense Archive lift.

## One-time Custodian sequence

On the first authorized entry, target 384 reports that launch authority was
verified but the defense inhibit was rejected under the surviving emergency
law. Citan identifies the Custodian Core as having transferred into the
defense robot guarding the party's Gears. The exchange is short and occurs in
the bay rather than upstairs at the authorization console.

Only then does the director assign and board:

- Elly in El-Regulus;
- Emeralda in Crescens;
- Citan in Fenrir.

The fixed configuration is still formation 15: one isolated 36,000-HP
Guardian from enemy resource set `0x10`, with Escape disabled, random weight
zero, and the retail Goliath Factory interior arena `0x0B`.

The battle uses a same-field return. After victory, the director restores the
three persistent Gear assignments, dismounts the visible party, sets
Guardian-defeated bit 5, presents the Custodian-offline exchange, and returns
control in target 384. A later visit sees a quiet, traversable bay: neither
the reveal nor the battle repeats.

An unauthorized direct/debug entry cannot start the battle. It reports that
launch authority is missing and directs the player back to the archive
console.

## Packed changes

Canonical contents 1358, 1374, and 1375 are the only v70-to-v71 replacement
changes. The other 153 previously staged replacements are byte-identical.
Canonical 1374 and 1375 are new replacements for the two former target-384
dummy files.

| Component | v70 size | v71 size | v71 SHA-256 |
| --- | ---: | ---: | --- |
| canonical 1358, target-376 bundle | 135,832 | 135,460 | `9d1950f6486df612919aae53671ab7c94464468ab22ca670c7d7a7648d18a5e8` |
| target-376 field script | 2,984 | 3,152 | `31b6a6733f744c5a30686c713ce32d9634108917429bc3a6c201eb47b3053000` |
| target-376 dialogue | 3,013 | 2,463 | `ed341bdf5dd2959434f6738feb52807a0927b755a8602e1ecc665ccb159fe9ea` |
| canonical 1374, target-384 bundle | 24 | 133,640 | `d00829ca635d0f4cc33b1d14272a21057cee7427d0217b16a9a55412d87d8416` |
| target-384 field script | — | 19,839 | `d27aed0a413711250689c4d791ba48c3f77d01a6439bb16d9779f838630f0e3a` |
| target-384 dialogue | — | 775 | `43a5d5e9384b81342a57a14905c00aedcf057a3ac9244fca5ad23a86b34d3d01` |
| canonical 1375, target-384 graphics | 24 | 440,320 | `cb3cdcd7b61326e7d4aa3e54e7570abed2bcc3af295f4fd3cdbb288cb2896000` |

The target-376 graphics remain byte-identical. Comparing the complete v70 and
v71 raw images finds 84,628 changed common sectors and 279 v71-only sectors,
84,907 sectors in all.

## Validation

The final automated suite passes **187 tests and 2,095 subtests**.

The v71 stage contains 156 replacements totaling 10,407,043 bytes. Their
canonical-ID-order aggregate SHA-256 is:

```text
448c45c5df4c83a4511fe87481c27425732fa8a80a797fec7bb8f56fa948e314
```

The final stage manifest is 175,490 bytes with SHA-256
`ff593f5249b71a759b9dfbf0f89be5484e99ac22f7d3ac5541e6facb6c5d9fb7`.

All 156 staged replacements re-extract byte-identically from the final image.
The 5,149 unique replacement sectors plus the standalone boot sector, 5,150
sectors in all, regenerate byte-exactly as MODE2/Form1. Including the FAT and
archive header expands the audited set to 5,167 sectors.

The retail-to-v71 comparison contains 111,812 changed or output-only sectors.
Every one regenerates with valid EDC/ECC and zero invalid sectors or
mismatches.

All 3,565 ordinary undeclared FAT files, totaling 624,830,534 bytes, remain
byte-identical. Their aggregate SHA-256 is:

```text
ab116c665120d6699bee74ddce86f2d76532f41636c531636050c091c23dae43
```

Canonical 22 is the patched system executable. Canonical 17 is the overlapping
umbrella entry spanning that executable and the rebuilt archive region, so
neither is classified as untouched.

## v71 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v71.bin` | 695,538,144 | `09a91f50211a8f1106a6a341e69dd225a64e31c89a3939f10997a93baceef90b` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v71.cue` | 106 | `d672bea94a499da2fc8696e86d3fc950a721da9778466faf19ce41ff804dfcc5` |
| `work/mass_driver_v71_stage/manifest.json` | 175,490 | `ff593f5249b71a759b9dfbf0f89be5484e99ac22f7d3ac5541e6facb6c5d9fb7` |
| `output/MASS_DRIVER_V71_CONTINUE.sav` | 1,745,813 | `cc8d4582df72ceaf2e7dd6d07177f62ab731f8dff19c0da058bed0ab7346545a` |

The image contains 295,722 raw sectors. Its resident `0x8000`-byte archive
table has SHA-256
`b6e4bbf5c843942691e8fcd9fcb94643c399af0cec33e5ecdfb5dc8cd047d85c`.

## Continuation and cold-boot acceptance

The supplied continuation was deterministically migrated from v70. Its state
header is `(2, 1647391, 3817114, 98422)`: frame format 2, a
1,647,391-byte compressed frame, a 3,817,114-byte decompressed gameplay
payload, and payload offset 98,422. The resident archive table begins at
decompressed payload offset 72,294.

Migration replaces the exact v70 resident table with the exact v71 table and
updates the same-length CUE name. The two tables differ in 5,231 bytes, all
inside that sole table; no decompressed gameplay-state byte outside it
changes.

The continuation begins after the Guardian with target 376 already resident
and defeated bit 5 set. Its resident room code is from the earlier checkpoint.
It can test the unchanged west-bulkhead, reserve-magazine, and Central Control
route, but it cannot validate any of v71's new progression:

- authorization ending without an immediate battle;
- the locked and unlocked north-wall lift;
- first entry into target 384;
- the Custodian reveal and same-field battle return;
- the reciprocal bay-to-archive trip.

Runtime acceptance therefore requires a cold boot:

1. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Choose New Game. Do not load an F1 state created in an older build.
3. Restore both power interlocks and enter target 376 normally through the
   Central Gate and east service stairs.
4. Before authorization, confirm the west bulkhead is sealed and the distinct
   recessed north-wall lift is visible. Press X at the lift and confirm that
   it requests completion of the archive wall-console sequence.
5. Use entity 13 and enter `0320`, then `A-2`, `B-5`, `C-8`, and `D-4`.
   Confirm acceptance returns control in the Defense Archive without starting
   a battle.
6. Return to the north-wall lift and press X. Confirm its facility sound and
   fade lead to the separate industrial target-384 bay, with the party facing
   inward on connected floor.
7. Confirm the short Custodian-frame scene begins there, identifies the
   defense robot, boards El-Regulus, Crescens, and Fenrir, and starts the
   no-Escape Guardian battle.
8. Win the battle. Confirm the party returns to target 384 on foot, receives
   the Custodian-offline exchange, remains controllable, and does not
   immediately repeat the encounter.
9. Use the bay entrance behind the party. Confirm its X action returns safely
   to target 376 parameter 2 beside the north lift without a contact bounce or
   camera-through-wall frame.
10. Confirm the west bulkhead is now available. Optionally revisit target 384
    and verify that the one-time scene and battle remain complete while the
    upstairs return still works.
11. Continue through all five reserve magazines to Central Control and finish
    the launch objective normally.

`output/CONTINUE_MASS_DRIVER_V71.cmd` cannot substitute for these checks. An
older DuckStation state captured while target 376 is resident likewise keeps
its already-loaded field script even after the v71 image is mounted.
