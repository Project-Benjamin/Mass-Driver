# Mass Driver v66: Materials Storage terminal presentation

Version 66 removes the two misleading gold memory-cube props from Materials
Storage, target field 722. Both optional discoveries remain in their original
parts of the room, but each is now operated from a genuine native facility
computer. The gold memory cube in Magnetic Conduit, target 725 entity 16,
remains the dungeon's only active Save point.

This remains an original, canon-conscious fan reconstruction. It is not
recovered Square dialogue or evidence of deleted official content.

## Two independent facility computers

The retail field-374 donor contains one hooded computer assembled from static
models 7 and 8. Earlier standalone builds left target-722 entity 14 visibly
initialized as the donor's gold Save cube after replacing its Save action with
payload-handling mail. Entity 15 likewise used the same gold cube appearance
for the authority record. That taught the player that a Save-point visual
might instead be a lore terminal.

Version 66 keeps the two discoveries separate:

| Controller | Position | Presentation | Result |
| --- | --- | --- | --- |
| entity 14 | `(40, 150)` | room's original models 7/8 computer | repeatable payload-handling mail, dialogue 8 |
| entity 15 | `(220, 66)` | second instance of models 7/8 | authority record, dialogue 1, and persistent A-2 / B-5 / C-8 / D-4 clue bit |

Both use invisible, facing-independent X / Cross controllers. Entity 14 has a
`0x20` interaction half-width so the original computer remains reachable from
the audited edge of the north walkmesh. Entity 15 uses `0x0F` on the elevated
side branch. The former entity-14 sprite update and contact wrapper are
parked, and neither controller initializes the memory-cube actor.

## Header-only native-model instancing

The second computer adds no model geometry, texture, sprite, or VRAM upload.
The builder retains the donor's exact models 7 and 8 and appends two static
actor records to the field header. Those records reference the existing model
indices with a header translation of `(+180, +43, -84)`, placing the duplicate
at the former authority-record branch.

The checked asset contract is:

| Asset | Source | v66 result |
| --- | --- | --- |
| field header | 832 bytes, 27 nodes, SHA-256 `4015dba74e05433ce0574bebf20c76dd004272f574961825b48b74e9bbfbfa1e` | 864 bytes, 29 nodes, SHA-256 `02e5fda0504906097a6b3f28f47cf037eefcce9e542a0a56332106b8b85f0341` |
| model archive | 28,060 bytes, SHA-256 `aff2acfc5174eabf374df807cad59aed8d8779136e7d7f795b2c9ca8878cb258` | byte-identical |
| native model 7 | SHA-256 `475fb3ae6e42235ebb5e0acc62c6186bbf1d452e1c9d0b00a7a9401191b5812d` | reused directly |
| native model 8 | SHA-256 `3f2987485d9a0a1e40637071d578526619cf1c8e0730fb2ca45a9d8d92ba1195` | reused directly |
| field graphics, canonical 2051 | 165,888 bytes, SHA-256 `d38d2ae9a2136b497403b917d04a052ecfd0b476f7f2799c10bfb86a8c235596` | byte-identical |

The transformed target-722 script is 1,858 bytes with SHA-256
`1951707ea5830e928559a6223ac5530261a936776e5be3aca768011e3fce2b05`.
Its 1,404-byte dialogue component remains byte-identical to v65 with SHA-256
`a95ec27c76d4b2712a5bf477c14ab0f1b1b5a650a703dbb88a7fce358ccd7ca2`.

## Global Save-point contract

The release verifier audits every active field in the 31-field route. It
requires the exact native Save action
`FE 99 00 FE 55 FE 87 00` to resolve only to target 725 entity 16. That entity
must also retain its exact bank-one initializer `0B 01 80` and collision
wrapper `FE 99 00`.

The verifier separately recognizes the retail memory cube's actor and sprite
payloads by SHA-256:

```text
actor:
42d88ff3385229ef53fdcf468b13ab61b6413a9ee47d756ece61756c246b8c52

sprite:
69060c5d8f1f25c3a3a4c438baaaabb18551f250abf66364b60cbbc28ac468d0
```

Target 722 still carries the donor payloads inside its source archives, but no
active initializer displays them. The build fails if either Materials Storage
controller regains the cube presentation, if its two records are merged, if
another route actor gains the native Save action, or if Magnetic Conduit loses
the genuine Save behavior.

## Packed change

Only one staged replacement differs between v65 and v66:

| Canonical file | Role | v65 | v66 | v66 SHA-256 |
| ---: | --- | ---: | ---: | --- |
| 2050 | target-722 field bundle | 56,448 | 56,536 | `588599c203d33c0d1ec2be48a2abaa665ae69361e36b2d497d83f24c2c67d2e7` |

Canonical 2051 and all other 152 replacement payloads are byte-identical to
v65.

## Validation

The full automated suite passes **183 tests and 2,074 subtests**. All 154
staged replacements, totaling 9,832,843 bytes, re-extract byte-identically
from the final image. Their canonical-ID-order aggregate SHA-256 is:

```text
7bac80f191d415bc2408dfb9f45478708718a09c76f66d33c9d43b69c57a9c23
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

## v66 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v66.bin` | 694,881,936 | `31e20109118cc712d603fe5df44c0cd90a2dd0de0521b79f17b5cb1f9753d228` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v66.cue` | 106 | `54a8c4d4e2baeb8379fe08489e8e57c6b6c625b605e9bffafbcb1e8ca4664f7d` |
| `work/mass_driver_v66_stage/manifest.json` | 171,487 | `6ab680d367dc7e1213ec8e5f980fd8b0614d5658e07c9e54e661e3deb308530c` |
| `output/MASS_DRIVER_V66_CONTINUE.sav` | 1,745,787 | `deb7ca7a75367c0c5205192459d4827727fa31d73d4d5c6f9386e57b47e8820a` |

The image contains 295,443 raw sectors. Its resident `0x8000`-byte archive
table has SHA-256
`bfd2c657d2232e33d2d529a30738be68ce8988cdec1d015f314531bf0bdf2e9a`.

## Continuation migration and runtime acceptance

The supplied continuation was deterministically migrated from v65. It replaces
the resident archive table and the same-length CUE name, changes one byte in
the 3,817,114-byte decompressed gameplay payload, and recompresses its zstd
frame from 1,647,367 to 1,647,365 bytes. A read-only reconstruction matched
the shipped v66 state byte-for-byte.

That continuation begins post-Guardian in resident field 376, after Materials
Storage. It is useful for the unchanged reserve-magazine and launch route, but
it cannot accept the target-722 presentation change. Visual acceptance of v66
therefore requires a cold boot:

1. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Choose New Game; do not load an F1 state made in an older build.
3. Reach Materials Storage, target 722.
4. Confirm the north computer shows payload-handling mail and no gold cube is
   visible there.
5. Follow the elevated side branch and confirm the second matching computer
   shows A-2 / B-5 / C-8 / D-4 and no gold cube is visible there.
6. Confirm both interactions remain independent and repeatable as designed.
7. Continue to Magnetic Conduit, target 725, and confirm its one gold cube
   opens the normal Save menu.

A DuckStation state captured while field 722 is already resident preserves
that loaded field's scripts and presentation even if v66 is mounted
afterward, so it cannot validate this change. Fresh visual acceptance of both
computers remains pending.
