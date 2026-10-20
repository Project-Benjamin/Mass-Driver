# Mass Driver Dungeon 2.0 - v21 PS1-Safe El-Regulus World-Map Sprite

> **Superseded by v22:** v21 fixed the freeze and rendered the correct art,
> but repeated each directional image across all four movement phases. Use
> [the v22 movement-animation notes](mass-driver-dungeon-2.1.md).

Version 21 preserves the accepted standalone dungeon, El-Regulus ownership,
battle model, and menu previews. It corrects the freeze introduced by v20's
first conversion of the authentic field-657 art.

## Freeze diagnosis

The v20 resource used five 13-byte frame records at offsets:

```text
0x0C, 0x19, 0x26, 0x33, 0x40
```

Frames 2 and 4 therefore began on odd PS1 addresses. The world-map sprite
loader reads each inline texture descriptor with `lhu` instructions. When
**Get In Gear** selected frame 4, the CPU raised an address-error exception at
PC `0x8001DE94`; `BadVaddr` was the unaligned descriptor halfword. The stopped
music and frozen image were consequences of that CPU trap, not a disc-loading
failure.

The same v20 bundle also replaced the retail world-map Gear animation program
with a five-frame field animation and uploaded a 48x72 image into a fixed
64-row world-map Gear VRAM cell. Version 21 corrects all three contracts.

## Corrected conversion

The builder still reconstructs the authentic five-direction El-Regulus actor
from Execution Site field 657:

- canonical `1920`, actor 7: layered frames, animation, and palette;
- canonical `1921`: the external field graphics uploaded into PS1 VRAM;
- five 48x72 directions flattened without changing any source pixels;
- opposite headings supplied by the original world-map mirroring behavior.

It now uses canonical `3949` as a structural template:

1. Preserve the retail 128-byte, five-entry world-map Gear animation section.
2. Supply all 35 frame IDs expected by its idle, action, and movement groups.
3. Use even-aligned 20-byte records with two subsprites per frame.
4. Preserve the authentic per-direction logical bounds.
5. Split each 48x72 direction into two 48x36 halves.
6. Pack those halves side by side in a 24-word by 36-row VRAM upload.
7. Preserve the retail two-bank palette container, duplicating the authentic
   El-Regulus colors into the unused second bank.

Frames 1-15 map the five authentic directions in three-frame groups. Frames
16-35 map them in four-frame groups. Because the cutscene source has static
directional art, repeated IDs remain visually stable while retaining every
frame address and state transition expected by the retail world-map runtime.

The corrected resource contract is:

```text
canonical ID:       3949
size:               10,960 bytes
SHA-256:            8ac2a842b7c842a7092e65a52c57f5fc34e797c4200820a40629160668e11e59
root offsets:       0x14, 0x94, 0x2A8C, 0x2AD0
animation entries:  5
animation SHA-256:  41d11406b30f197cce21bf0fcccc34cbd91dee4e71ec5e5910e7954719863306
frame header:       0x1423 (35 frames, retail allocation maximum 10)
actual subsprites:  2 per frame
frame records:      0x48 through 0x2F0, even-aligned, 20-byte stride
upload envelope:    24 VRAM words x 36 rows
canvas SHA-256:     6e25e76eafff4342b8765cebf4e068e2cae36fb102f86176f85ced4891339a77
```

## Build

After extracting the audited resources listed in the v20 notes, build with:

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v21_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v21.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v21.cue
```

The rebuilt BIN is 690,368,448 bytes with SHA-256:

```text
30bf74e9c5c77f55feb2c24f114c96803b8c1897cd746cbc54b651c116ea2a00
```

It passed 119 automated tests, 134 subtests, and an exact post-build
comparison of all 40 injected disc resources.

## Runtime acceptance

The corrected resource was first injected into a direct mounted-state probe.
DuckStation cold-booted it, instantiated El-Regulus, continued running, and
rendered the authentic crimson, white, silver, and dark-red sprite on the
world map.

For the release candidate:

1. Start a New Game and open the world-map Gear menu.
2. Tell Elly to get into El-Regulus; the transition must finish without a
   freeze or stopped music.
3. Turn and move in every direction.
4. Dismount and remount.
5. Confirm the Repair Bot and normal Gear-equipment menus retain the accepted
   neutral El-Regulus model.
6. Complete the solo Gear battle and confirm its native battle model and
   animations are unchanged.

This replacement changes only Gear 10's world-map resource. It does not alter
Renmazuo, Vierge, Weltall, El-Regulus's battle assets, or shared field actors.
