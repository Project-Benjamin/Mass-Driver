# Mass Driver v70: Defense Archive Citan staging

Version 70 repairs Citan's position when the party first enters the Defense
Archive, target field 376. Elly and Emeralda retain the source-394 room's
natural east-stair arrival. Citan is now already inside the archive beside
the wall console when the fade finishes, rather than appearing at the bottom
of the stairs on their follower trail.

The change is deliberately limited to first-entry actor staging. It does not
move Elly or Emeralda, start Citan's briefing automatically, alter the wall
terminal, or change the post-Guardian route.

## Root cause

Citan is party entity 3 and character 2 in target 376. His entity initializer
correctly establishes his checked interior position at
`(130, 50, walkmesh 0, direction 1)`, along with his temporary solid,
stationary talk state.

On first entry, however, the room owner subsequently runs `FE18 02` and
`FE1A` to load Citan into the active party. That asynchronous party creation
occurs after entity 3's initializer. It reconstructs the party actor on the
east-stair arrival trail and overwrites the position the initializer just
assigned. The result is the misplaced Citan shown at the bottom of the
stairs.

The problem was therefore ordering, not an incorrect walkmesh coordinate,
camera direction, or receiving entry.

## Post-load staging repair

Version 70 installs Citan's position routine in entity 3's previously unused
script slot 21. The first-entry owner update now contains this sequence while
the destination is still fading in:

```text
33 FE 54 FE 18 02 FE 1A 09 03 35
```

The final `09 03 35` invokes entity 3's script 21 after `FE18` / `FE1A` have
created the party actor. That script reapplies only Citan's checked interior
position, walkmesh, and facing.

The isolation is intentional:

- there is exactly one `09 03 35` call;
- there is no entity-2 staging call for Elly;
- there is no entity-7 staging call for Emeralda;
- Citan is staged before the joined-state bit is committed;
- the room waits 15 ticks and restores the fade/control handoff normally;
- no dialogue opens during the entry update.

Receiving parameter 0 remains
`(668, 192, walkmesh 0, actor direction 4, camera direction 4)`. Entity 2
(Elly) and entity 7 (Emeralda) retain their donor initializer and update
pointers, so both characters keep the natural inward-facing stair arrival.

## Interaction contract retained

After the fade, Citan waits on connected floor beside the console. Until
authorization is accepted, he remains a solid, immovable, stationary talk
actor with a separate X interaction radius. His briefing starts only when the
player walks to him, faces him, and presses X.

The genuine wall terminal remains entity 13 and can still be used before or
after speaking to Citan. Citan's conversation does not authorize the launch,
start the Guardian battle, or block the terminal. Once all five authorization
entries are accepted, his existing update restores ordinary non-solid party
following.

Version 69's other current room contracts remain unchanged, including:

- Archive Console D's separate main rail and rear mail terminals;
- the Materials Storage combined archive computer and Omegasol chest;
- the sole gold memory-cube Save point in Magnetic Conduit;
- the Directive `0320` and `A-2 / B-5 / C-8 / D-4` authorization sequence;
- the paired west bulkhead, Guardian battle, five reserve magazines, and
  Central Control launch handoff.

## Packed change

Only canonical replacement 1358, the target-376 field bundle, differs between
v69 and v70. The other 153 staged replacements are byte-identical.

| Component | v69 | v70 | v70 SHA-256 |
| --- | ---: | ---: | --- |
| canonical 1358 field bundle | 135,820 | 135,832 | `1fe471954ce92a641ee4ba58e2643f366a6c1478944b22c98e4627ced3e020c3` |
| field script | 2,970 | 2,984 | `9f21986aa00de2780e09761ae2802560ec4672a4499289857281cd88a1f145de` |
| dialogue | 3,013 | 3,013 | `5883f27923c6ca8718294cab8818fd559c731b0e833e0bb94a6389f622999ece` |

The v69 canonical-1358 SHA-256 was
`d6cb5e85cd0fda0b354f2a97e8fb8d2c99b5efd3816ae4452cda83f2982557de`.
Its field-script SHA-256 was
`66377de88f3f1db0b499d6d1d9574b346248e29556907955c0f501a2a8a01118`.

The dialogue and every field component other than the script remain
byte-identical. The complete v69 and v70 raw images differ at exactly eight
LBAs: `28`, `172923`, `196300`, and `196362` through `196366`.

## Validation

The final automated suite passes **186 tests and 2,074 subtests**.

The v70 stage contains 154 replacements totaling 9,833,455 bytes. Their
canonical-ID-order aggregate SHA-256 is:

```text
40a0be855adbcf8b7a575019c6f3c4ba7f1e28b58c2fb8f484094dd63d19a4fc
```

The final stage manifest is 172,327 bytes with SHA-256
`bea6e797f9741b2887cc181ad5c1232491649b911f33795f4f37fc2c25a60697`.

All 154 staged replacements re-extract byte-identically from the final image.
The 4,868 unique replacement sectors plus the standalone boot sector, 4,869
sectors in all, regenerate byte-exactly as MODE2/Form1. Including the FAT and
archive header expands the audited set to 4,886 sectors.

Comparing the retail source image with v70 finds 108,410 changed common
sectors plus 2,732 output-only sectors. All 111,142 regenerate with valid
EDC/ECC and zero invalid sectors or mismatches.

All 3,567 ordinary undeclared FAT files, totaling 624,830,582 bytes, remain
byte-identical. Their aggregate SHA-256 is:

```text
b25684ad3d74a5cef80900f415cf793babf96ee12e6c8a2090873d99968b8d29
```

Canonical 22 is the patched system executable. Canonical 17 is the overlapping
umbrella entry spanning that executable and the rebuilt archive region, so
neither is classified as untouched.

## v70 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v70.bin` | 694,881,936 | `d7bf2b659dbca7ce5815d7c5f907110bb3e64b4874aa6326d27c5a579f249464` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v70.cue` | 106 | `824aeef31b9f0d3943e30b593809380bddaa335417149de232019038ae7a3af5` |
| `work/mass_driver_v70_stage/manifest.json` | 172,327 | `bea6e797f9741b2887cc181ad5c1232491649b911f33795f4f37fc2c25a60697` |
| `output/MASS_DRIVER_V70_CONTINUE.sav` | 1,745,790 | `8a86fd92569983bbe96ed5f86a7884dc5b4b9354a607823231c95925c31f6490` |

The image contains 295,443 raw sectors. Its resident `0x8000`-byte archive
table has SHA-256
`86fac64c2bce5ec8e23dfa19c3e2130dec66f9d14a417af3848287b93ddfc87d`.

## Continuation and cold-boot acceptance

The supplied continuation was deterministically migrated from v69. Its state
header is `(2, 1647368, 3817114, 98422)`: frame format 2, a 1,647,368-byte
compressed frame, a 3,817,114-byte decompressed gameplay payload, and payload
offset 98,422. The resident archive table begins at decompressed payload offset
72,294. The migration changes one byte in that table and preserves the rest of
the gameplay payload.

The continuation begins after the Guardian with field 376 already resident.
It is useful for the unchanged west-bulkhead and reserve-magazine route, but
it cannot exercise the first-entry party load or validate this repair.
Runtime acceptance requires a cold boot:

1. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Choose New Game. Do not load an F1 state created in an older build.
3. Restore both power interlocks and enter target 376 normally through the
   Central Gate and east service stairs.
4. Confirm Elly and Emeralda remain together at the inward-facing stair
   threshold.
5. Confirm Citan is already waiting inside beside the wall console when the
   fade finishes. He must not appear at the bottom of the stairs.
6. Confirm no dialogue opens automatically and movement control returns.
7. Walk to Citan, face him, and press X. Confirm his briefing begins normally.
8. Use the wall terminal independently and confirm its five-stage
   authorization sequence is unchanged.

`output/CONTINUE_MASS_DRIVER_V70.cmd` cannot substitute for this test. An
older DuckStation state captured while field 376 is resident likewise
preserves the already-loaded script even after the v70 image is mounted.

