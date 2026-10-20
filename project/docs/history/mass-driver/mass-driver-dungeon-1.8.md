# Mass Driver Dungeon 1.8 - v19 El-Regulus Presentation

> **Superseded by v20:** the v19 world-map asset identification below was
> incorrect. Canonical `448` is Gear ID 5, Renmazuo, which caused the
> blue-and-white world-map sprite seen in testing. Gear ID 10's global field
> slot is canonical `453`, but it aliases Vierge; its world-map slot `3949`
> aliases Weltall. Version 20 instead reconstructs Square's authentic
> El-Regulus art from Execution Site field 657, canonical `1920/1921`. See
> [the corrected v20 notes](mass-driver-dungeon-1.9.md).

Version 19 preserves the accepted v18 dungeon and El-Regulus ownership work.
It fixes the two presentation failures found in the world map and the Repair
Bot's Gear-parts shop, then covers the separate Gear-equipment preview path.

## Root causes

The engine was already reading Elly's Gear ID 10 correctly. The retail
world-map resource assigned to that ID was the problem:

- Gear 10 world-map canonical file: `3949`;
- retail size: 10,960 bytes;
- retail SHA-256:
  `d2d36a82bc67a3e79ac3d966e0b2d4a09049c3bb047fba384df0f9fa901cc79d`;
- byte-for-byte identical to Gear 0/Weltall canonical file `3939`.

The same placeholder exists on both retail discs. The world-map overlay was
therefore left unchanged.

The Gear-parts shop has an independent model table in canonical file `2602`.
Its Gear 10 record pointed to Weltall pair `0x06BA/0x06BB`, and its pose byte
selected combat-idle animation 1. Xenogears already contains the intended
dormant El-Regulus shop pair at `0x072E/0x072F`:

- canonical `2260`: one keyframe table plus six valid menu/field animation
  programs;
- canonical `2261`: 48,000-byte model geometry;
- canonical `2261` is byte-identical to El-Regulus battle geometry canonical
  `2959`.

## World-map sprite

The native field Gear 10 sprite in canonical `448` is LZSS-packed. Its
81,348-byte decoded payload is already the same three-entry
`sSpriteActorAnimationBundle` structure consumed by the world-map loader.
Version 19 writes that decoded bundle, not the compressed field file, into
canonical `3949`.

The replacement retains:

- 11 valid animations, including world-map IDs 0, 1, and 3;
- 75 native El-Regulus frames;
- native frame dimensions and palettes;
- SHA-256
  `b15ce02ea0e4b1cc4ff02475d2e9e5e251676ee2142633559be0fffd7391c52c`.

A mounted cold-boot probe reached the playable map and rendered the native
blue El-Regulus sprite with a valid palette and no loader failure.

## Shop and menu previews

Canonical `2602` receives two guarded table edits:

```text
offset 0x11D90: BA 06 -> 2E 07  (Weltall -> dormant El-Regulus pair)
offset 0x11DAA: 01    -> 00     (combat idle -> static neutral pose)
```

No shared Weltall record or model asset is overwritten. The patched file
SHA-256 is:

```text
4579fcf9a077f73e352de0a9c274b893a9d2271cfbf14bc1b534590ce8e9c8f8
```

The normal Gear-equipment preview uses a different resource. Canonical `2998`
redirects its animation-23 pointer to validated base animation 0:

```text
offset 0x44: 8E 01 -> 04 01
```

Its patched SHA-256 is:

```text
367e8daf4a7cc905d4eb33f14e27011e9a9205782b3ecfe7db6c96da9d854663
```

Battle assets, field assets, Gear statistics, equipment, and commands are not
changed by either preview fix.

## Build

For a newly prepared workspace, extract the v19 retail resources from a
legally obtained US Disc 2 image:

```powershell
$sourceDisc = "C:/path/to/Xenogears_PW_CD2.bin"
python tools/xgdisc.py extract $sourceDisc work/_audit_el_regulus_field `
  --canonical-disc2 448 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_el_regulus_worldmap `
  --canonical-disc2 3949 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_shop_models `
  --canonical-disc2 2260 2261 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_regulus `
  --canonical-disc2 2998 --force
python tools/xgdisc.py extract $sourceDisc work/shop_menu_data `
  --canonical-disc2 2602 --force
```

The extractor writes canonical file 448 as `0448.bin`, which is the filename
the builder validates.

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v19_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v19.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v19.cue
```

The built BIN is 690,448,416 bytes with SHA-256:

```text
9dea5e9890999b69678d377e10cab1850fb9d86bb95c90eda31e9246545b1901
```

It passed 119 automated tests, 134 subtests, and a byte-for-byte comparison of
all 40 injected disc resources.

## Focused runtime acceptance

Use a cold New Game:

1. Mount El-Regulus on the world map and confirm it is the native blue
   El-Regulus sprite rather than Weltall.
2. Turn and move in several directions, then dismount and remount. Confirm
   frames, scale, and palette remain stable.
3. Enter the facility and reach the Repair Bot outside the train.
4. Open Gear Parts, choose Buy, and select Elly. Confirm the preview is
   El-Regulus in a neutral pose rather than Weltall in a combat stance.
5. Cancel and reopen that shop twice to confirm the preview, Repair Bot, and
   adjacent container remain intact.
6. Open the normal Gear-equipment menu and confirm its El-Regulus preview is
   also neutral.
7. Complete the solo Gear battle and confirm native El-Regulus battle
   geometry and animations remain unchanged.

The BIN remains a runtime candidate until the in-shop checks are confirmed on
the user's route save.
