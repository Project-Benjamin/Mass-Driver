# Mass Driver v64: M-07 dialogue-window repair

Version 64 fixes the maintenance-robot dialogue reported at the abandoned
subway and adds one short, one-time Elly response. The rest of v63's dungeon,
story script, combat, route, and launch sequence is unchanged.

This remains an original, canon-conscious fan reconstruction. It is not
recovered Square dialogue or evidence of deleted official content.

## Text-window correction

M-07's shop block declared width 46, which the retail renderer oddifies to 47
font units. The line:

```text
"Reserve stores available."
```

uses 54 units, so the end of `available` could not fit. The closing block was
also undersized: its 38-unit declaration provided 39 usable units, while the
robot header and `Maintenance complete.` line require 42 and 46.

Both blocks now declare width 58, giving 59 usable font units. The four shop
rows remain unchanged, so the native choice results still map row 2 to Items
and row 3 to Gear parts.

## Elly's first-interaction response

After the first completed M-07 interaction, Elly says:

```text
Elly
"I can't believe this robot
is still operational after
all this time..."
```

The response is a manually checked 58-by-5 block. M-07's action waits one
frame after its closing window, presents Elly's screen-positioned response,
then sets persistent variable `0x03FE`, bit 13. Later interactions skip only
Elly's response; the Item and Gear-parts menus and M-07's normal closing line
remain repeatable.

The shipped action has one bit-clear test using mask `0x2000`, one dialogue-3
call, and one bit-13 write. Bit 13 was previously unused, the standalone New
Game state clears the containing word, and no other field script reads,
writes, or clears it.

## Validation

The full automated suite passes **182 tests and 2,074 subtests**. Regression
coverage now checks both M-07 window widths and their visible font-unit bounds,
the exact Elly text, the persistent branch/write order, the unchanged native
shop opcodes, and the repeat-path control restore.

Canonical 2048 was re-extracted from the final image and matched the staged
field-721 payload byte-for-byte:

```text
size:   148,396 bytes
SHA-256: 5130b2dc3aac775ec20ed4b669535ba747c499688b57c6557fbe38ee4f4b449d
```

Comparing all v63 and v64 staged records confirms canonical 2048 is the only
replacement payload that changed.

All 154 staged replacements, totaling 9,832,243 bytes, re-extract
byte-identically. Their canonical-ID-order aggregate SHA-256 is:

```text
576aed2c4f2488af0aaf1500debfa96d5bf3144637ee573224463b28d44a4e84
```

The raw-image audit covers 4,868 unique replacement sectors plus the standalone
boot sector, and 4,886 unique replacement/FAT/header/boot sectors in total.
All regenerate byte-exactly as MODE2/Form1. Comparing the complete source and
output images finds 108,410 changed common sectors plus 2,732 output-only
sectors; all 111,142 likewise regenerate with valid EDC/ECC and no mismatch.
All 3,567 non-overlapping, undeclared archive files remain byte-identical.
Canonical 22 is the patched system executable; canonical 17 is an overlapping
umbrella entry spanning that executable and the rebuilt archive region, so
neither is classified as untouched.

## v64 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v64.bin` | 694,881,936 | `bffd030dd52a57842e6d361f080cbfbc4c0ac14c410a3a67f846c5b3dccb210d` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v64.cue` | 106 | `18f2d41a6d43b1299b380f922ed2261cf2a737450df06bf709b1464b5ba6b8c8` |
| `work/mass_driver_v64_stage/manifest.json` | 170,285 | `a736148855f7c196d53fb859c48f918cff87247910f84cf3e912862bde225154` |
| `output/MASS_DRIVER_V64_CONTINUE.sav` | 1,745,789 | `a5be3959aee43bd905cef75f43f0572f9d08d5fe36d00e8ee9e245905d39d1ef` |

The continuation was migrated from v63 by replacing only its resident archive
table and same-length media name. Its decompressed gameplay payload changes by
six bytes, and its new resident-table SHA-256 is
`4dcc44bf6297f379669f47f92b0065630b9c894101074b9c19efb1ad72daef43`.
It begins after the subway, so use a fresh New Game to accept the M-07 change.

## Runtime acceptance

Fresh cold-boot visual acceptance remains:

1. Confirm the complete word `available.` is visible above both choices.
2. Complete or cancel the first M-07 menu interaction and confirm Elly's
   response appears after `Maintenance complete.`
3. Interact again, then leave and re-enter the field, and confirm her response
   does not replay.
4. Confirm both Item and Gear-parts menus remain repeatable and both robots
   remain visible after either menu closes.

Use `output/PLAY_MASS_DRIVER_STANDALONE.cmd` for that test. The separate
`output/CONTINUE_MASS_DRIVER_V64.cmd` remains available for the unchanged
post-Guardian route.
