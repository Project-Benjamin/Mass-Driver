# Mass Driver Dungeon 1.9 - v20 Authentic El-Regulus World-Map Art

> **Superseded by v21:** v20's converted frame records were not consistently
> halfword-aligned and could freeze the PS1 when Elly selected **Get In Gear**
> on the world map. Use
> [the corrected v21 notes](mass-driver-dungeon-2.0.md).

Version 20 preserves the accepted standalone dungeon, El-Regulus ownership,
battle model, and menu fixes. It corrects the world-map sprite after the v19
asset identification proved to be Renmazuo.

## Retail asset audit

Xenogears maps the shared global field Gear resources as canonical
`443 + Gear ID`. The relevant retail slots are:

| Use | Gear ID | Canonical file | Retail content |
| --- | ---: | ---: | --- |
| Global field sprite | 5 | `448` | Renmazuo |
| Global field sprite | 10 | `453` | Vierge alias |
| World-map sprite | 10 | `3949` | Weltall alias |

This explains both observed failures: the original retail Gear 10 world-map
slot showed Weltall, while the v19 replacement showed Renmazuo. Neither is a
palette error; both have the wrong silhouette and animation data.

Authentic Square-authored El-Regulus 2D art does exist in Execution Site
field 657, “Regulus / Amphysvena / Opiomorph”:

- Disc 2 canonical `1920`: field bundle, 83,296 bytes;
- Disc 2 canonical `1921`: external graphics, 339,968 bytes;
- actor index `7`;
- five directions: rear, rear three-quarter, side, front three-quarter, and
  front;
- opposite directions are produced by horizontal mirroring, as in the
  original actor animation;
- one original 16-color PSX palette.

The art is crimson, dark red, silver, and white and matches El-Regulus's
menu and battle design.

## Conversion

The field actor cannot be copied directly to world-map canonical `3949`.
Its ten-layer frames refer to pixels prebacked into field 657's external
graphics page. The builder therefore performs a deterministic conversion:

1. Validate canonical `1920` and `1921` by exact size and SHA-256.
2. Replay all twelve external graphics uploads into a 1024×512 PSX VRAM
   image.
3. Read actor 7's five ten-layer frame compositions and original palette.
4. Flatten each direction onto a 48×72, 4-bpp canvas without altering its
   pixels or colors.
5. Encode each canvas as one inline world-map subsprite.
6. Alias world-map animation IDs 0 through 10 to the authentic static
   directional program.

Field header mapping `(384, 256, 0, 1)` is significant. Its final flag tells
the retail loader not to upload actor sprite bank 7 because the coherent
El-Regulus pixels are already in the external graphics. Applying that bank
again produces blocky overlay corruption, so the converter deliberately
matches the retail loader and does not apply it.

The converted resource contract is:

```text
canonical ID:       3949
size:               8,852 bytes
SHA-256:            73aae8bf655d1ce0a93667c93f8780790407bc274779543df0ae8f9e53641606
root offsets:       0x14, 0x4C, 0x2270, 0x2294
animation entries:  11
frame header:       0x0205 (5 frames, maximum 1 subsprite)
canvas SHA-256:     6e25e76eafff4342b8765cebf4e068e2cae36fb102f86176f85ced4891339a77
```

The `0x0200` frame-header allocation bit is required. A bare five-frame
header would allocate no subsprite polygons and fail when the first frame is
loaded.

## Build

For a newly prepared workspace, extract the audited resources from a legally
obtained US Disc 2 image:

```powershell
$sourceDisc = "C:/path/to/Xenogears_PW_CD2.bin"
python tools/xgdisc.py extract $sourceDisc work/_audit_el_regulus_field657 `
  --canonical-disc2 1920 1921 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_el_regulus_worldmap `
  --canonical-disc2 3949 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_shop_models `
  --canonical-disc2 2260 2261 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_regulus `
  --canonical-disc2 2998 --force
python tools/xgdisc.py extract $sourceDisc work/shop_menu_data `
  --canonical-disc2 2602 --force
```

Build the candidate with:

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v20_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v20.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v20.cue
```

The built BIN is 690,366,096 bytes with SHA-256:

```text
e331b2d0a19ce7d0e91000974cb832ea3562130a18f8ddf536560eecd56db913
```

It passed 119 automated tests, 134 subtests, and an exact post-build
comparison of all 40 injected disc resources.

## Focused runtime acceptance

Use a cold New Game:

1. Mount El-Regulus on the world map.
2. Confirm its crimson-and-silver Execution Site silhouette appears instead
   of Renmazuo's blue-and-white body or Weltall.
3. Turn through every direction and move several steps. All headings should
   remain coherent; the source actor contains static directional art, so
   movement should not invent a walking cycle.
4. Dismount and remount, then confirm the palette and scale remain stable.
5. Enter the facility and check the Repair Bot's Gear-parts preview and the
   normal Gear-equipment preview. Both should retain the accepted neutral
   El-Regulus model.
6. Complete the solo Gear battle and confirm its native battle geometry and
   animations are unchanged.

The conversion changes only Gear 10's world-map resource. It does not replace
Renmazuo, Vierge, Weltall, battle assets, or any shared field resource.
