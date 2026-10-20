# Mass Driver v67: Materials Storage political archive

Version 67 expands the original north computer in Materials Storage, target
field 722, with four more pages of archived 6079 mail. The room keeps v66's
clean two-computer presentation: entity 14 at `(40, 150)` carries the expanded
payload-handling record, while entity 15 at `(220, 66)` remains the independent
four-point authority record.

This remains original, canon-conscious fan writing. It is not recovered Square
dialogue or evidence of deleted official content.

## Expanded north-computer record

Dialogue 8 now develops the political conversion of the facility through a
specific storage discrepancy. Aron reports that the launch banks accepted a
missile frame without modification and that he was told to classify the test
as civilian. Mara refuses the euphemism and tells him to write `MISSILE`.

The four added pages then preserve:

1. A civilian inventory naming a university weather package and the next
   survey carrier.
2. Their removal from the launch queue, replacement by sealed cargo,
   transfer to Strategic Command, and an order from the Prime Minister's
   Adviser's Office.
3. Lena's discovery that the public schedule still lists the carrier even
   though its survey cradle is missing.
4. Mara's instruction to archive both versions so their dates can disprove
   any later claim that the civilian staff agreed.

The record closes with the existing route to the Defense Archive and the
Directive `0320` / `A-2, B-5, C-8, D-4` reminder. It adds exposition at the
computer already visible in the room without changing progression.

## Why the room still has two computers

A geometry audit tested whether the additional exposition should receive a
third full-size terminal. The candidate footprint would span the room's narrow
walkable corridor. A static model instance would also be non-colliding, so it
would appear to block the aisle while allowing the party to walk through it.

Version 67 therefore retains v66's readable two-computer composition and puts
the new material on the existing north computer. No model, texture, field
header, controller, interaction position, or Save-point behavior changes.
Target 725 entity 16 remains the route's only gold memory-cube Save point.

## Packed change

Only canonical file 2050 differs between v66 and v67:

| Canonical file | Role | v66 | v67 | v67 SHA-256 |
| ---: | --- | ---: | ---: | --- |
| 2050 | target-722 field bundle | 56,536 | 56,988 | `daeabb4059da4effeed310246774feeadaeb6267b42fb25da727dad836ee731d` |

The v66 bundle SHA-256 was
`588599c203d33c0d1ec2be48a2abaa665ae69361e36b2d497d83f24c2c67d2e7`.
Canonical 2051 and the other 152 replacement payloads remain byte-identical.

Target 722's transformed script remains 1,858 bytes with SHA-256
`1951707ea5830e928559a6223ac5530261a936776e5be3aca768011e3fce2b05`.
Only its dialogue component changes, growing from 1,404 bytes in v66 to 1,801
bytes in v67 with SHA-256
`bd7d6572b10e8a12dbb000cec0efdad818c1a70e5dc9e1a5e36b95606df10bc3`.

## Validation

The full automated suite passes **183 tests and 2,074 subtests**. All 154
staged replacements, totaling 9,833,295 bytes, re-extract byte-identically
from the final image. Their canonical-ID-order aggregate SHA-256 is:

```text
caee68c85cc32c03c142b9be3326a60f9d64bc7d7e931660a5a1677fe485c208
```

The raw-image audit covers 4,868 unique replacement sectors plus the
standalone boot sector, and 4,886 unique replacement/FAT/header/boot sectors
in total. All regenerate byte-exactly as MODE2/Form1. Comparing the complete
source and output images finds 108,410 changed common sectors plus 2,732
output-only sectors; all 111,142 regenerate with valid EDC/ECC and no
mismatch.

All 3,567 ordinary undeclared FAT files, totaling 624,830,582 bytes, remain
byte-identical. Their aggregate SHA-256 is
`b25684ad3d74a5cef80900f415cf793babf96ee12e6c8a2090873d99968b8d29`.
Canonical 22 is the patched system executable; canonical 17 is an overlapping
umbrella entry spanning that executable and the rebuilt archive region, so
neither is classified as untouched.

## v67 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v67.bin` | 694,881,936 | `e0e601cd158efd963e9c631617cc056ae521f5d6fd12f6bfc39125b2b1453554` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v67.cue` | 106 | `10c1a52080beb6150300ac993e76f4a47c315cee0e4080fe46a7d2e1b734a945` |
| `work/mass_driver_v67_stage/manifest.json` | 171,499 | `90cd7d945d2aacbd5a868813be92e7d5ea9bf72dd46a1a9109e2f7da40ff28d0` |
| `output/MASS_DRIVER_V67_CONTINUE.sav` | 1,745,792 | `a421f998e16bff0dde0f2220e6c791bbca3f36f2069fa552db74a5b5d98a6605` |

The image contains 295,443 raw sectors. Its resident `0x8000`-byte archive
table has SHA-256
`e371e2e39b56bf77cf3f9cd19020cf3cc29200e76de19e189c0e0e37e01c104a`.

## Continuation migration and runtime acceptance

The supplied continuation was deterministically migrated from v66. It
replaces the resident archive table and same-length CUE name, changes two
bytes in the 3,817,114-byte decompressed gameplay payload, and preserves the
v66 source state.

That continuation begins post-Guardian in resident field 376, after Materials
Storage. It supports the unchanged forward route but cannot validate target
722's expanded computer. Runtime acceptance therefore requires a cold boot:

1. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Choose New Game; do not load an F1 state made in an older build.
3. Reach Materials Storage, target 722.
4. Read the north computer and confirm the four added storage-inventory and
   political pages appear.
5. Confirm the elevated computer still independently presents the authority
   record.
6. Confirm no gold memory cube appears in Materials Storage.
7. Continue to Magnetic Conduit, target 725, and confirm its one gold cube
   opens the normal Save menu.

A DuckStation state captured while field 722 is resident preserves that
already-loaded field's scripts and dialogue even if v67 is mounted afterward.
Fresh visual acceptance of the expanded record remains pending.
