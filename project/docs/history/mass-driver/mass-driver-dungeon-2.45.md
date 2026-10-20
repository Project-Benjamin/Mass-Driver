# Mass Driver v68: one Materials Storage archive and one treasure chest

Version 68 gives the two prominent objects in Materials Storage, target field
722, separate and immediately legible roles. The original north computer is
now the room's sole archive terminal. The elevated duplicate computer is
removed and field 374's genuine animated treasure chest is restored in its
place with one Omegasol.

Target 725 entity 16 remains the dungeon's only gold memory-cube Save point.
The Materials Storage computer and chest cannot open the Save menu.

This remains an original, canon-conscious fan reconstruction. It is not
recovered Square dialogue or evidence of deleted official content.

## One computer carries the complete archive

Entity 14 remains an invisible, facing-independent controller over the room's
original hooded models 7/8 computer at `(40, 150)`. Its broad `0x20`
interaction half-width keeps the terminal reachable from the edge of the
north walkmesh.

Dialogue 8 now combines everything the two v67 computers presented:

- Aron's missile-adapter test and Mara's refusal to classify it as civilian.
- The removed university weather package and survey carrier.
- Strategic Command's sealed replacement cargo and the order from the Prime
  Minister's Adviser's Office.
- Lena's missing survey cradle and Mara's dated evidence of the false public
  schedule.
- Directive `0320`, the `A-2 / B-5 / C-8 / D-4` four-point authority, its
  separation policy, and the emergency duplicate-credential abuse.
- Directions to the authorization terminal beyond Central Gate.

Using this one computer also sets the authority-record clue bit. There is no
second terminal interaction, so players do not need to check two visually
similar objects for overlapping parts of the same record.

## Native Omegasol chest

Entity 15 at `(220, 43, 66)` again uses field 374's complete native treasure
presentation: actor 2, sprite 1, and its original initialization, update,
action, and collision scripts. The award changes from the donor placeholder
to one-based retail object ID 49, whose system-menu name entry 48 is
`Omegasol`.

The unchanged retail action preserves the entire expected chest flow:

1. Check whether the item inventory has capacity.
2. If it is full, show the capacity-failure message without consuming the
   reward.
3. Otherwise award the Omegasol and show its receipt.
4. Play the native opening animation.
5. Remove the opened object and keep it collected on later field loads.

The collected state uses persistent variable `0x03FE`, bit 14
(`0x4000`). It is written only after the successful award path, so a
capacity failure remains retryable and the Omegasol cannot be collected
twice.

## Future custom items and additional facility chests

Omegasol deliberately uses a complete retail item definition. A genuinely new
item cannot be introduced safely by assigning a new number only in the field
script. A later custom-item pass must audit and extend the global item name,
category, effect, icon, sale/shop, and save-serialization data together.

The current standalone progression uses bits 0 through 14 of persistent word
`0x03FE`; only bit 15 remains free. More than one additional persistent chest
therefore needs a dedicated persistent bitset rather than consuming unrelated
progress flags or reusing bit 14.

## Native asset and layout restoration

Version 67 appended two header nodes to instance models 7/8 at the elevated
branch. Version 68 removes those duplicate nodes and restores the donor's exact
832-byte, 27-node header:

| Component | v68 result |
| --- | --- |
| field header | 832 bytes, SHA-256 `4015dba74e05433ce0574bebf20c76dd004272f574961825b48b74e9bbfbfa1e` |
| model archive | 28,060 bytes, SHA-256 `aff2acfc5174eabf374df807cad59aed8d8779136e7d7f795b2c9ca8878cb258` |
| actor archive | 7,944 bytes, SHA-256 `763cd7beb2ef61789fb372532899621dbadecd341a4bc8679bd8a082125d187b` |
| sprite archive | 8,100 bytes, SHA-256 `337209b64be352028122c9f4ee69761027975592abf1cc09086acefcab36c347` |

The model, actor, and sprite archives are byte-identical to v67 and the field
374 donor. Only the extra header instancing is removed; the original computer
and the native chest assets were already present.

The transformed target-722 script is 1,809 bytes with SHA-256
`85fadd7c7995e7dd3a12ccc5939e459f756d9f0b10679f455a340e2ddbe50a51`.
Its 1,799-byte dialogue component has SHA-256
`2a12d6235fbaf6abbbff4afc0a0fd5bcdb5b19d2f262f2f6420920ce8df41a5a`.

## Packed change

Only canonical file 2050 differs between v67 and v68:

| Canonical file | Role | v67 | v68 | v68 SHA-256 |
| ---: | --- | ---: | ---: | --- |
| 2050 | target-722 field bundle | 56,988 | 56,892 | `f75b4b1e26eca46567e8a2bbb9c880d15a7d7a5b64712ea0ca421f0795f5974f` |

The v67 bundle SHA-256 was
`daeabb4059da4effeed310246774feeadaeb6267b42fb25da727dad836ee731d`.
Canonical 2051 and the other 152 replacement payloads remain byte-identical.

## Validation

The final automated suite passes **185 tests and 2,073 subtests**.

All 154 staged replacements, totaling 9,833,199 bytes, re-extract
byte-identically from the final image. Their canonical-ID-order aggregate
SHA-256 is:

```text
180c19aec71c03735ad3f22ce7f01011a13d2ce756980f4eed6b1c244f3cd223
```

The raw-image audit covers 4,868 unique replacement sectors, 4,869 after the
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

## v68 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v68.bin` | 694,881,936 | `07b91acc39367e39653f87a8cc49b9d490d83f1cf783510ea38aa0d1fecc25b6` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v68.cue` | 106 | `1c89ce57695020108717876118da866e4b07a00426445845946d441b1fcd1d1c` |
| `work/mass_driver_v68_stage/manifest.json` | 171,598 | `a84a979098bda1f3d67ea50e8657fa8c1ef5983829fe857eaf370fac6151732f` |
| `output/MASS_DRIVER_V68_CONTINUE.sav` | 1,745,790 | `d6d3e4210a8f0e487840d76152d27fb4d22f3cae8599e18f0beaa9e3fe39a925` |

The image contains 295,443 raw sectors. Its resident `0x8000`-byte archive
table has SHA-256
`80b356de3f2246c74fdbb180f3649dd3bcc307c2c4b3a28ca53eff0c0c68948f`.

## Continuation migration and runtime acceptance

The supplied continuation was deterministically migrated from v67. Its zstd
frame header is `(2, 1647368, 3817114, 98422)`: frame format 2, a
1,647,368-byte compressed frame, a 3,817,114-byte decompressed gameplay
payload, and payload offset 98,422. The migration replaces the resident
archive table and same-length CUE name, changes one decompressed gameplay byte,
and preserves the v67 source state.

That continuation begins post-Guardian in resident field 376, after Materials
Storage. It supports the unchanged forward route but cannot validate target
722's new object roles. Runtime acceptance therefore requires a cold boot:

1. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Choose New Game; do not load an F1 state made in an older build.
3. Reach Materials Storage, target 722.
4. Use the north computer once and confirm it presents both the payload and
   authority records, including `A-2 / B-5 / C-8 / D-4`.
5. Confirm the elevated object is an animated chest rather than another
   terminal or a gold memory cube.
6. Open it, receive one Omegasol, leave and return, and confirm it cannot
   award another.
7. Continue to Magnetic Conduit, target 725, and confirm its one gold cube
   opens the normal Save menu.

A DuckStation state captured while field 722 is resident preserves that
already-loaded field's scripts, dialogue, and presentation even if v68 is
mounted afterward. Fresh visual acceptance of the combined computer and
native chest remains pending.
