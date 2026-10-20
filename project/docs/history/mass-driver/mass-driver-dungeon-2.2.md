# Mass Driver Dungeon 2.2 - v23 El-Regulus Forward Poses

Version 23 preserves the complete standalone dungeon, El-Regulus ownership,
menu models, field-657 world-map art, and v22's working six-phase movement
timing. It adds the part that v22 missed: a separate forward-driving pose for
each world-map direction.

## Corrected retail animation audit

All ten audited Disc 2 party-Gear bundles use the same 35-frame contract:

```text
idle bases:       1, 4, 7, 10, 13
movement bases:   16, 20, 24, 28, 32
movement phases:  base + 0, +1, +2, +3, +2, +1
draw-y offsets:   0, -2, -4, -6, -4, -2
```

The four records in each movement direction share their pixel pointers and
change only the draw position and logical bounds. However, the idle and
movement bases do not share art. Across the ten retail resources, all 50
idle-to-movement direction comparisons have different pixel pointers.

Version 22 reproduced the phase geometry but pointed both banks at the same
upright El-Regulus canvas. Its bob was correct, but its conclusion that the
other Gears lacked forward artwork was not.

Vierge canonical `3941` is the closest pose reference. Its idle logical
bounds have an RMS distance of `2.11` from El-Regulus, compared with `4.82`
for Weltall and `4.91` for Fenrir. It also has the same slender pilot Gear
proportions and long trailing armor.

## Forward art

Field 657 still supplies the only five authenticated El-Regulus map
directions. Version 23 creates the missing movement bank by reposing those
exact 4-bpp pixels:

- rear and front headings use depth foreshortening;
- rear three-quarter rotates forward by 40 degrees;
- side rotates forward by 50 degrees;
- front three-quarter rotates forward by 55 degrees;
- nearest-neighbor sampling preserves the original 16-color index set;
- the bob remains draw-time geometry and is not baked into the pixels.

The staging transform is deterministic. Its five `64x72` canvases have
combined SHA-256:

```text
ff0b678761580790331e58d0c71b4a98ac409be5cb5acb342b49975fcd86c382
```

Transparent margins are then removed without clipping:

| Direction | Packed canvas | Draw origin | Base W/D/H | Canvas SHA-256 |
|---|---:|---:|---:|---|
| Rear | `56x72` | `(-28,-64)` | `(35,25,69)` | `41a96bb8404107c76885a98bbc480777269537d65e9d56cdd8c08643a0f526c9` |
| Rear 3/4 | `56x68` | `(-28,-62)` | `(32,28,66)` | `cfe9b0b6cecce6a0f21cc83e1dc7c2dc479304591940491c5dd1a71a139038b6` |
| Side | `52x52` | `(-26,-55)` | `(25,24,51)` | `04543b0affa847661457e9a1ff410f67ccc9b675c933ec8e4351042266ee58f0` |
| Front 3/4 | `60x52` | `(-30,-55)` | `(24,34,48)` | `cff5dba3627f31c2f242b085bf23cc590df02ae2159b10cdf215e1a3efe70731` |
| Front | `48x52` | `(-23,-55)` | `(22,24,45)` | `cf0d594de3962a907ae0550381b639b6f8edc32c630287800cb9684cf0488092` |

Opposite headings continue to use the retail renderer's mirroring behavior.

## Bundle and VRAM contract

Every pose retains v21/v22's proven two-subsprite format. Each canvas is
divided into equal top and bottom halves, placed side by side in the Gear's
temporary VRAM cell, and reconstructed at its checked draw origin.

Movement uploads peak at `30` words wide and `36` rows tall; the largest by
area is `28x36`. The retail party-Gear cell is `32` words by `64` rows, so no
pose exceeds it. All frame records are halfword aligned, all pixel pointers
are four-byte aligned, and the frame header remains `0x1423` (35 frames,
allocation maximum 10 subsprites).

Adding the five movement canvases expands canonical `3949`, but does not
require a fixed loader allocation. The world-map loader allocates from the
FAT entry size. The new resource remains smaller than retail Stier-2
canonical `3953`, which is 19,368 bytes.

```text
canonical ID:       3949
size:               17,788 bytes
SHA-256:            035e43d9bab45f91ffb12dd31874b863eda1b43a8ec38cc19f051d82168db69a
root offsets:       0x14, 0x94, 0x4538, 0x457C
animation section:  128 bytes, unchanged retail SHA-256
frame section:      0x44A4 bytes
frame records:      35 x 20 bytes
texture blob region: 0x41A0 bytes (0x4150 packed pixels + 0x50 headers)
movement uploads:   28x36, 28x34, 26x26, 30x26, 24x26
```

## Build

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v23_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v23.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v23.cue
```

The rebuilt BIN is 690,375,504 bytes with SHA-256:

```text
dfafb51ed881207b692ec6eb7cd70c1179c28d2cbfef78c7e8c17ff5b5fc9a09
```

It passed 119 automated tests, 139 subtests, and an exact extraction
comparison of all 40 injected resources.

## Runtime acceptance

A mounted-state DuckStation probe loaded the expanded resource and moved
continuously without freezing or stopping the emulator. Rear, rear
three-quarter, side, front three-quarter, and front travel frames all
rendered in the authentic crimson, white, silver, and dark-red palette.
Mirrored left-facing travel art also rendered correctly. Stopping returned
to the upright directional pose.

For manual acceptance:

1. Start New Game and open the world-map Gear menu.
2. Tell Elly to get into El-Regulus.
3. Move in a diagonal or side direction and confirm that the upright sprite
   changes immediately into the forward flight stance.
4. Keep moving and confirm that the travel pose rises and falls smoothly.
5. Turn through all headings, stop, move again, dismount, and remount.
