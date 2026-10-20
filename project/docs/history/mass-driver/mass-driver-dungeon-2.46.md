# Mass Driver v69: separate rail control and rear archive mail

Version 69 gives Archive Console D's two visible computers distinct jobs.
The main terminal remains the accelerator-rail control that satisfies the rail
half of the Central Gate interlock. The computer in the back is now a separate
archive-mail terminal containing Aron's saved 6081 message to Lena.

The rear mail terminal does not restore the accelerator, unlock a progression
condition, or repeat the main terminal's feedback. Version 68's Materials
Storage computer, native Omegasol chest, and sole-Save contract are unchanged.

This is original, canon-conscious fan-authored exposition. It is not recovered
Square dialogue or evidence of official deleted content.

## Two visible terminals, two roles

Target field 368 uses the following interaction contract:

| Role | Entity | Controller position | Dialogue | Progression |
| --- | ---: | --- | ---: | --- |
| main Archive Console D | 13 | `(45, -42)` | 0 | sole writer of persistent `0x03FE` bit 1 |
| rear archive-mail terminal | 14 | `(-89, 90)` | 1 | none; repeatable |

Entity 13 retains the room's existing main Zeboim console. Its action reports
that the accelerator banks respond, restores accelerator power, and marks the
rail condition satisfied. It carries no saved-mail page. This rail bit joins
the separate auxiliary-power bit at the Central Gate; the rail console does
not bypass the other required condition.

Entity 14 is an otherwise dormant donor controller repurposed for the rear
computer. Its action shows only the archive-mail record and contains no
rail-bit write. Reading it before or after the main console produces the same
mail and does not alter objective state.

## Rear terminal placement

The rear controller is fixed at `(-89, 90)` over native static model 4,
instanced by field-header node 25. Its interaction half-width is `0x1E`.
The nearest connected player position is walkmesh-0 vertex 19 at
`(-70, -3, 74)`, conventionally written as the horizontal point
`(-70, 74)`. This places the activation area beside the visible screen instead
of attaching the email to the main rail console.

Native static model 3 was considered because it is another terminal-like prop,
but its presentation is outside reachable player space. It was rejected rather
than creating an interaction that appears valid in field data but cannot be
used during ordinary play.

No new field model is appended. The relevant native assets remain exact:

| Component | Size | SHA-256 |
| --- | ---: | --- |
| field header | 976 | `1745402e7ac9bc03566a0546e8bce08b1d4316af20082ae8b0083d26b69bd22f` |
| model archive | 35,628 | `b734fbc3155ba006227ff9f2c0540558a283574d3b1beea0f3f988cac749af87` |
| static model 4 | n/a | `56625491e9d7d52225e3391cf6fe7cd905b6a59a2d54f80329b2a2403bfe8aed` |
| walkmesh | 1,604 | `5bae54017424c13437d0790f57e4b5be3eea2e3f6fd3952351a87b03bac12e6f` |

Header node 25 retains its audited model-4 record:
`(0x0010, 0, 0x0600, 0, 0, 0, 0, 4)`.

## Mail content

Dialogue 1 identifies itself as the Archive Mail Terminal and presents saved
mail from year 6081, sent by systems engineer Aron to guidance engineer Lena.
Aron reports that Lawine destroyed the central power station, leaving half the
capital dark. Strategic Command nevertheless orders the accelerator thermal
limits bypassed, while the Prime Minister's adviser frames any delay as an
invitation to attack. Aron admits that he is the person closing the breakers
and clings to the hope that a visibly ready weapon might prevent its use.

The final routing note explicitly directs accelerator-interlock control back to
the main console. This adds political and personal context without making an
optional email necessary for progression.

Dialogue 0 remains rail-only:

- accelerator interlock;
- remote test accepted;
- magnetic banks responding;
- accelerator power restored;
- Central Gate rail condition satisfied.

## Script isolation

The v69 verifier requires all of these properties together:

- entity 13 keeps its original non-action script pointers;
- entity 13's action begins with the `0x03FE` bit-1 write, native sound 0x50,
  and dialogue 0;
- that action contains no reference to dialogue 1;
- entity 14 keeps its donor update and collision STOP pointers;
- entity 14 receives the fixed rear-position initializer and dialogue-1
  action;
- entity 14's action contains no rail-bit write;
- no second routine writes the rail bit;
- the donor header, model archive, static model 4, and reachable walkmesh
  vertex remain byte-exact.

The retired donor nanoreactor-director interaction remains inactive.

## Packed change

Only canonical replacement 1342 differs between v68 and v69. Canonical 1343,
the matching graphics bundle, remains byte-identical.

| Canonical file | Role | v68 | v69 | v69 SHA-256 |
| ---: | --- | ---: | ---: | --- |
| 1342 | target-368 field bundle | 52,724 | 52,968 | `cc9e7439820586dd1e95fe8db961c0af6bc1a347e2a87d8976815b8b07f05ae1` |
| 1343 | target-368 graphics | 239,616 | 239,616 | `0406623aac1a16cfadebef4db2391916bfd797677c28eb112154ffc6d957f177` |

The v68 canonical-1342 SHA-256 was
`0ef8c32e797ad5ee30fadf6e667c95a362ab7e5d4716681981ad5dac6e511eec`.

The transformed target-368 script is 2,833 bytes with SHA-256
`d1ceae480eb8ebdd68c6a002c98d4ac253f73ff693f7ee94612702c81e96d282`.
Its 670-byte dialogue component has SHA-256
`8c266a3f82a692867cfe766cf6757587abcacb592e542a003f11ec45e733876c`.
For comparison, v68 used a 2,784-byte script with SHA-256
`65e4da259ffadfa389c2b4b0495a09a2d74c3946037d03effb58c9d5fb85577b`
and a 512-byte dialogue component with SHA-256
`00591c80ded86e6d39ae4298ee85ab9635fd9a4aecd82f65faad65153f9a3447`.
Only six raw sectors differ between the complete v68 and v69 images.

## Validation

The final automated suite passes **186 tests and 2,074 subtests**.

The stage contains 154 replacements totaling 9,833,443 bytes. Their
canonical-ID-order aggregate SHA-256 is:

```text
73dd850dd065c3a369bfce91952badb41c7fa3d85d4c13e6a405e64a1380b902
```

The final stage manifest is 172,327 bytes with SHA-256
`b61abe6a897c77cd2e65c5a951a92e51955faeccbb820a2fb1a8875c37436e4f`.

All 154 staged replacements re-extract byte-identically from the final image.
The 4,868 unique replacement sectors plus the standalone boot sector, 4,869
sectors in all, regenerate byte-exactly as MODE2/Form1. Including the FAT and
archive header expands the audited set to 4,886 sectors.

Comparing the retail source image with v69 finds 108,410 changed common
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

## v69 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v69.bin` | 694,881,936 | `f5118b524035eb6b6e531c5bd5c3d582177d8a9284845b4aaf7171bd8392db46` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v69.cue` | 106 | `faaad493364d186cd6b0c0a42fe687764087573db8196c41fbb23133c47672a9` |
| `work/mass_driver_v69_stage/manifest.json` | 172,327 | `b61abe6a897c77cd2e65c5a951a92e51955faeccbb820a2fb1a8875c37436e4f` |
| `output/MASS_DRIVER_V69_CONTINUE.sav` | 1,745,789 | `cf50d14ac8e77483783ac810da0816d46849e5c8308251aea2016431b66c92d1` |

The image contains 295,443 raw sectors. Its resident `0x8000`-byte archive
table has SHA-256
`38a38520810d4848d26e0b99b9fa18731ecc394c918518355db6ccded11ff12b`.

## Continuation and cold-boot acceptance

The supplied continuation was deterministically migrated from v68. Its state
header is `(2, 1647367, 3817114, 98422)`: frame format 2, a 1,647,367-byte
compressed frame, a 3,817,114-byte decompressed gameplay payload, and payload
offset 98,422. The migration changes two bytes in the resident archive table
and preserves the source state.

The continuation begins in resident field 376, after target 368 and Materials
Storage. It supports the unchanged post-Guardian route, but it cannot validate
the two Archive Console D interactions. Runtime acceptance requires a cold
boot:

1. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Choose New Game. Do not load an F1 state created in an older build.
3. Reach Archive Console D, target 368.
4. Use the main terminal near `(45, -42)`. Confirm it restores the accelerator
   rail, reports the Central Gate rail condition satisfied, and shows no saved
   mail.
5. Use the separate terminal in the back near `(-89, 90)`. Confirm it presents
   Aron's saved 6081 mail to Lena and its main-console routing note.
6. Read the rear terminal again and confirm the mail remains available.
7. Confirm the rear terminal does not repeat rail-restoration feedback or alter
   the Central Gate condition.
8. Continue to the Central Gate and confirm it still requires both the
   auxiliary and rail interlocks.

`output/CONTINUE_MASS_DRIVER_V69.cmd` is useful for the later route only. A
DuckStation state captured while field 368 is resident preserves the
already-loaded scripts and dialogue even after the v69 image is mounted, so it
cannot substitute for the cold-boot check.
