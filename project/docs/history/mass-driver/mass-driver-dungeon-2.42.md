# Mass Driver v65: Reserve Magazine 02 political mail

Version 65 expands the record shown in Reserve Magazine 02 after the user
reported the room from a fresh screenshot. The existing 6083 launch-log page
and Elly/Emeralda reactions remain unchanged. Six manually paginated 6079 mail
pages now connect the facility's original space program to its military
conversion.

This remains an original, canon-conscious fan reconstruction. It is not
recovered Square dialogue or evidence of deleted official content.

## Exact runtime target

The screenshot uniquely matched target field 378, `Containment vault 2 of 5`,
whose replacement is canonical file 1362. The authored source is:

```text
content/mass_driver_v2/field_673_silo_vault_2.authored.json
```

The perceived terminal is not an X-operated actor. Field 378 has no usable
console entity: invisible retired scene-controller entity 7 automatically
shows dialogue block 0 on forward arrival from field 377. Arrival from field
379 skips the record. Version 65 therefore extends that existing automatic
block without changing field scripts or route behavior.

## Added 6079 thread

After the unchanged launch-log page, the record now shows:

```text
ARCHIVED MAIL / YEAR 6079
FROM: FACILITY DIRECTOR
TO: LAUNCH STAFF
SUBJECT: FUNDING REVIEW

Civil funding was cut.
Strategic Command offers
to restore it for control
of the accelerator.

They want final authority
over every payload.
The Adviser calls this
"shared use."

MARA / PAYLOAD SAFETY
The attached manifest says
NUCLEAR WARHEAD.
I will not certify it.

FROM: ARON / SYSTEMS
If we refuse, banks shut.
Maybe the space program
survives if we agree.

REPLY: LENA / GUIDANCE
Mira kept the paper star
you made for her.
What do I tell her now?
```

This fills a distinct narrative gap. The optional 6078 and 6079 archive
consoles already show Strategic Command inspecting the survey cradle and
emergency law overriding Mara's refusal. The new mandatory-route thread shows
the institutional pressure behind that conversion: civil funding disappears,
military funding is conditional on control, and the Adviser supplies the
euphemism. Mara, Aron, and Lena retain their established roles and voices, and
the paper star links back to the successful probe launch.

## Text-window and field packing

The block retains the five-vault contract: declared width 52, runtime capacity
53 font units, and height four. Every page has at most four explicit lines and
every ordinary Latin line is at most 26 glyphs. The authored dialogue compiles
to 736 bytes.

Only one replacement differs between v64 and v65:

| Canonical file | Role | v64 | v65 | v65 SHA-256 |
| ---: | --- | ---: | ---: | --- |
| 1362 | field 378 bundle | 96,524 | 97,036 | `d8e73ea237eaa30ad38fcdcfab8ff912d05d100a88673d5c4ec08de2911d0949` |

The packed bundle remains 1,268 bytes below the fixed `0x18000` field ceiling.
All other 153 replacement payloads and all other 357 staged field components
are byte-identical to v64.

## Validation

The full automated suite passes **182 tests and 2,074 subtests**. The content
regression checks the political-pressure sequence, Mara's established
`PAYLOAD SAFETY` title, the explicit nuclear-warhead manifest, Aron's space
program line, and Mira's paper star. The authored-dialogue compiler checks all
ten pages against the retail renderer's font-unit and line-count limits.

All 154 staged replacements, totaling 9,832,755 bytes, re-extract
byte-identically from the final image. Their canonical-ID-order aggregate
SHA-256 is:

```text
a4b596d85310490c088a596ef48290391799c73f1286900f78187e10c6ea757b
```

The raw-image audit covers 4,868 unique replacement sectors plus the standalone
boot sector, and 4,886 unique replacement/FAT/header/boot sectors in total.
All regenerate byte-exactly as MODE2/Form1. Comparing the complete source and
output images finds 108,410 changed common sectors plus 2,732 output-only
sectors; all 111,142 likewise regenerate with valid EDC/ECC and no mismatch.
All 3,567 ordinary undeclared FAT files, totaling 624,830,582 bytes, remain
byte-identical; their aggregate SHA-256 is
`b25684ad3d74a5cef80900f415cf793babf96ee12e6c8a2090873d99968b8d29`.
Canonical 22 is the patched system executable; canonical 17 is an overlapping
umbrella entry spanning that executable and the rebuilt archive region, so
neither is classified as untouched.

## v65 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v65.bin` | 694,881,936 | `3d926a27ba9d3cb1b9546be2d1255bcd68bccf3f9a0b3ffc8be6e22d6321ec85` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v65.cue` | 106 | `6419a73a9e81e1ace498a9921e6bff8e4ca04e4e711fa9674ccab9d704578ad3` |
| `work/mass_driver_v65_stage/manifest.json` | 170,285 | `9175dad3993dca98826ba5ec4c8e7c4ec957793499c2ab7a849c7ec734f72ad2` |
| `output/MASS_DRIVER_V65_CONTINUE.sav` | 1,745,789 | `2d145e69ce290536724683d3a53f621c0f345e90568c82d5a2073b131140dc93` |

The continuation was migrated from v64 by replacing only its resident
`0x8000`-byte archive table and same-length media name. The decompressed
gameplay payload changes by one byte, within canonical entry 1362's size
record. Its final resident-table SHA-256 is
`2f67e7d7e84ee1c96a3feca5857123da5689e56a937bffef14cee2cd08ee71f8`.
Exact field-376 components are resident in the checkpoint; field-378
components are absent, so the updated room loads fresh from v65.

## Runtime acceptance

Fresh visual acceptance remains:

1. Run `output/CONTINUE_MASS_DRIVER_V65.cmd`.
2. Open the paired bulkhead and cross Reserve Magazine 01.
3. Enter Reserve Magazine 02 from the south.
4. Confirm the original four-line 6083 launch log remains the first page.
5. Advance through all six 6079 mail pages and confirm no line is clipped.
6. Confirm Elly and Emeralda's original reactions follow the mail.

Do not use the captured mid-dialogue field-378 state for this check. A
DuckStation state preserves the already loaded field; the supplied v65
continuation starts earlier in field 376 specifically so field 378 is fetched
from the new disc.
