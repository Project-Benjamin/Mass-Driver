# Mass-Driver dungeon 1.0

> Superseded by [Mass Driver dungeon 1.1](mass-driver-dungeon-1.1.md), which
> adds the playable world-map approach, world-map interaction, visible missile
> stockpile, and Citan's corrected pre-boss arrival.

## Content status

**Disclaimer:** This is a canon-faithful reconstruction; not recovered cut content.

This dungeon is an original, canon-faithful reconstruction of the playable
Mass-Driver sequence described by the released *Xenogears* story. It is not
recovered cut content, a leaked Square script, or a claim that these exact
rooms, puzzles, enemies, or lines were present in an unfinished retail build.

The reconstruction keeps the known story anchors: Elly and Emeralda enter the
powered Zeboim Mass Driver Facility together, Citan meets them in central
control, and the group launches the Nanoassembler payload that removes the
Limiter. The route, access procedure, ordinary encounters, and ZD-808 defense
unit were created for this playable version.

## Final route

Version 1.0 replaces the three-room graybox with a ten-area linear route: the
field-617 story hook followed by nine distinct dungeon fields. Every fixed exit
advances to the next field, so there are no room loops or required backtracking.

```text
617 -> 720 -> 721 -> 722 -> 723 -> 724 -> 725 -> 726 -> 727 -> 728 -> 618
```

Field 618 is the untouched retail-story destination and is not counted as one
of the ten patched stages.

| Stage | Field | Area and purpose | Progress condition |
| ---: | ---: | --- | --- |
| 1 | 617 | Retail Mass-Driver story hook | Adds Emeralda beside Elly and redirects both retail narration branches to field 720 |
| 2 | 720 | Zeboim subway approach | Elly and Emeralda enter the facility together |
| 3 | 721 | Powered transit spine | Introduces the magnetic launch rail and active automated defenses |
| 4 | 722 | Cargo-routing concourse | Forward traversal with random encounters |
| 5 | 723 | Missile-conversion gallery | Missile and freight-rail presentation, dialogue, and random encounters |
| 6 | 724 | Guidance archive | Recovers archive access code `0320` on the required route |
| 7 | 725 | Directive 0320 terminal | Requires `0320`; success reveals the four launch-authority addresses |
| 8 | 726 | Four-terminal authorization | Requires `A-2`, `B-5`, `C-8`, and `D-4` before the security lift opens |
| 9 | 727 | ZD-808 security core | Unavoidable boss gate; victory alone transfers the party to field 728 |
| 10 | 728 | Central control and launch | Citan arrives, the Nanoassembler payload launches, and the exit unlocks |

After the launch, field 728 leads directly to retail field 618 and resumes the
original Disc 2 story.

## Puzzle solution

The two authorization steps are deliberately sequential:

1. In field 724, inspect the required guidance archive and recover `0320`.
2. Enter `0`, `3`, `2`, `0` at the field-725 Directive terminal. The route out
   remains locked until the terminal accepts the entry.
3. The accepted record reveals `A-2`, `B-5`, `C-8`, and `D-4`.
4. In field 726, enter the revealed value at each matching A, B, C, and D
   terminal, then release the launch lock. The security lift will not advance
   to the boss until all four addresses are authorized.

## Combat and party staging

- Elly and Emeralda are together from the field-617 hook through the dungeon.
- Fields 722 and 723 retain ordinary random encounters.
- Field 727 presents ZD-808 as a surviving Zeboim central-control defense
  array. Mechanically, the fixed boss formation uses four retail Defencer
  units. It is unavoidable and advances only after victory.
- Citan appears only after the boss, in field 728. The launch-console event
  must complete before the exit to field 618 opens.

## Build

The build requires the staged and hash-audited field inputs under `work/`, the
dialogue specifications under `content/mass_driver_v2/`, a user-supplied Disc
2 BIN, and Xenoiso 0.95. The legacy Xenoiso executable, source image, and output
paths must not contain spaces.

From the repository root in PowerShell:

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_dungeon_release_v1 `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_dungeon_1.0.bin
```

The builder validates source hashes, checked script bytes, the forward-only
route, rebuilt field components, and replacement IDs before invoking Xenoiso.
It writes a matching MODE2/2352 CUE beside the BIN and does not overwrite the
source image.

## Test and verify

Run the dungeon-specific tests:

```powershell
python -m unittest discover -s tests -p "test_build_mass_driver_dungeon.py" -v
```

Run the complete automated suite:

```powershell
python -m unittest discover -s tests -v
```

Verify the finished BIN independently:

```powershell
(Get-FileHash -Algorithm SHA256 `
  output/Xenogears_PW_CD2_mass_driver_dungeon_1.0.bin).Hash
```

The final 1.0 BIN is 688,881,984 bytes. Its expected SHA-256 is:

```text
6264E535F6F3B34A62B69E92D1A4E3D7832E0DF0D4443D8DE01F2B818771F45B
```

## Play

For the prepared cold-boot path, double-click:

```text
output/PLAY_NEW_MASS_DRIVER_DUNGEON.cmd
```

The 1.0 launcher boots
`output/Xenogears_PW_CD2_mass_driver_dungeon_1.0.cue`. Do not use an older
graybox direct-entry save state with this build.

At the title screen, use the standard PS1 memory card:

```text
output/Xenogears_PW_mass_driver_pre_hook_No05.mcd
```

Choose **Continue**, choose **Load**, select the sole `No.05 Shot Down!` save,
and confirm **Yes**. From the save-point corner, walk down, cross the room to
the left, and enter the upper-left lab doorway. Continue through the retail
story sequence; its patched field-617 hook places Emeralda with Elly and enters
field 720.

To launch manually instead, configure that memory card in DuckStation slot 1
and cold-boot `output/Xenogears_PW_CD2_mass_driver_dungeon_1.0.cue`, then follow
the same Continue/Load route.
