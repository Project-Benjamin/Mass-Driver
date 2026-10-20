# Mass Driver dungeon 1.1

> Historical story-integrated prototype. It is superseded by the
> [standalone development build](mass-driver-dungeon-1.2.md). Do not use this
> version to test the current route or asset policy. Its world-map experiment
> incorrectly repurposed Taura/Torah's House instead of activating the native
> Mass Driver complex; that design has been retired.

## Content status

This is a canon-faithful fan reconstruction, not recovered cut content. The
released game establishes the Mass Driver trip, Elly and Emeralda seeing the
old weapons, Citan helping with the launch, and the Nanoassembler payload. The
specific dungeon route, puzzles, encounters, ZD-808 boss, and authored lines
are original work designed to fit those story anchors.

## Obsolete world-map implementation

Do not use the 1.1 image to evaluate the current entrance. The corrected
standalone build preserves Taura's model, field-614 exit, and `Torah's House`
label. It instead activates the retail Mass Driver complex formed by map
records 59-62 / blocks 48-51, using the reachable position-21 spawn and
interaction apron documented in the 1.2 notes.

## Route

The dungeon has no room loop and requires no backtracking:

```text
617 -> world map -> 720 -> 721 -> 722 -> 723 -> 724
                  -> 725 -> 726 -> 727 -> 728 -> 618
```

| Field | Area | Required progression |
| ---: | --- | --- |
| 617 | Retail story hook | Explicitly stages Elly and Emeralda, then opens the playable world map |
| 720 | Zeboim subway approach | Facility-entry scene |
| 721 | Powered transit spine | Establishes the magnetic launch rail and active defenses |
| 722 | Cargo-routing concourse | Forward traversal with random encounters |
| 723 | Nuclear missile stockpile | Eight visible low-poly missiles, Elly's graveyard reflection, and random encounters |
| 724 | Guidance archive | Recovers Directive `0320` on the required route |
| 725 | Directive terminal | Requires `0320` and reveals four launch-authority addresses |
| 726 | Authorization level | Requires `A-2`, `B-5`, `C-8`, and `D-4` |
| 727 | ZD-808 security core | Citan arrives; the unavoidable boss must be defeated |
| 728 | Central control | Citan prepares the trajectory and Elly starts the magnetic launch rail |
| 618 | Retail continuation | Resumes the unmodified Disc 2 story |

The missile stockpile consists of eight generated PS1-native, flat-shaded
models on two side platforms. The central walkmesh, doors, and collision data
are unchanged. Their muted metal, warning-band palette, polygon budget, and
native display-list format match the donor field rather than introducing a
modern-looking external asset.

Elly's stockpile scene explicitly describes the missiles as tombstones in a
graveyard and monuments to Zeboim's pride and arrogance. Emeralda travels with
her from the world map onward. Citan arrives and joins before ZD-808, then
helps reach and operate the launch console after the fight.

## Puzzle solution

1. Inspect the archive in field 724 to obtain `0320`.
2. Enter `0`, `3`, `2`, `0` at the Directive terminal in field 725.
3. Use the revealed values at the four terminals in field 726:
   `A-2`, `B-5`, `C-8`, and `D-4`.
4. Release the launch lock and proceed to ZD-808.

ZD-808 is implemented as a fixed formation of four retail Defencer units. The
battle is unavoidable, and only victory transfers the party to field 728.

## Build and validation

From the repository root in PowerShell:

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_dungeon_release_v1_1 `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_dungeon_1.1.bin
```

Run the complete automated suite with:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Version 1.1 passes 57 tests. The builder hash-checks retail inputs, checked
script locations, world-map data, the world-map interaction instruction, model
geometry, dialogue structure, encounter formations, and forward transitions.
All 21 replacements were re-extracted from the finished BIN and matched
byte-for-byte. The missile-gallery field is 195,008 bytes, safely below the
game's `0x40000` field-loader limit. Its complete nine-page conversation is
packed into one native dialogue window so every page advances reliably before
control returns to the player. DuckStation cold-booted the final CUE with the
supplied BIOS and identified it as NTSC-U Xenogears Disc 2.

Final release integrity:

```text
BIN size: 688,769,088 bytes
SHA-256: A9AAAE12EF0F18B13BFB93D1632995B1884A7C9E17DC00DB0EA580BD7A2DEF4C
```
