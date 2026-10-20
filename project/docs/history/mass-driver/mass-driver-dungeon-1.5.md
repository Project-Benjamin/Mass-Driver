# Mass Driver Dungeon 1.5 - v16 Repair Bot Menu Return

> Superseded by v17. Runtime testing found that v16's rebuilt catalog streams
> ended in incomplete LZSS command groups, causing a black-screen hang when a
> shop opened. See [the v17 correction](mass-driver-dungeon-1.6.md).

Version 16 preserves the complete v15 route, doors, objective loop, boss,
world-map bootstrap, and platform-vendor interaction. It fixes the Repair
Bot graphic corruption seen after leaving either native shop menu and expands
the bot's stock without changing any original retail merchant.

## Placement and interaction

- Field: target 721, retail Lighthouse subway donor 397.
- Entity: 11, an unused character-10 PC stub in this standalone party.
- Position: `x=1000`, `z=220`, walkmesh 0.
- Facing: cardinal parameter 1 (`+X`), toward the east-side arrival and
  platform lane.
- Controls: X opens an input-safe native choice window. Cancel closes it.
- **Items** invokes isolated normal shop 36.
- **Gear parts** invokes isolated Gear shop 20.
- Both paths return through the native shop cleanup before player control is
  restored.

The bot remains outside the stationary train and does not overlap the
rail-safety container, the platform route, or either automatic threshold.

## Menu-return graphics fix

The v15 bot sprite was uploaded at `(768, 256)`. Native Item and Gear shop
overlays use the framebuffer rectangle from `(704, 256)` through
`(1024, 480)` as menu scratch space. Opening a shop therefore overwrote the
bot's sprite data, leaving colored vertical strips when the field became
visible again.

Version 16 uses a retail-proven two-payload layout:

| Local bank | Payload | Size | VRAM origin |
| --- | --- | --- | --- |
| 0 | Repair Bot | 128 x 256 | `(832, 0)` |
| 1 | Existing platform chest | 64 x 6 | `(960, 0)` |

Neither rectangle intersects the menu scratch framebuffer or the other
payload. Disc 2 scene 418 uses the byte-identical Repair Bot actor and sprite
at `(832, 0)`, the byte-identical chest sprite at `(960, 0)`, and a real Gear
shop. The target field's room graphics end before these two character-sprite
regions.

The transplanted bot assets remain:

- actor bank SHA-256:
  `1d0fb9c11104a1b90848db8ad39fa4e023a071cd826c92b60e62ab319ff6a382`
- embedded palette record SHA-256:
  `c2e7d3104119403c0e5a019f223d63bf3852a2f013cb76c677610773460697c5`
- 32-byte, 16-color CLUT SHA-256:
  `730e111722b592cc0bc0ae8e4c5bf4293b0ee3d5ee1a218aeaa7c090e7d9a8af`
- sprite bank SHA-256:
  `0fb607468497aa16a89b900aea7a4bce92fe039ad541dff894e5f701b28327b2`

Only the local character banks and their checked VRAM mappings change. The
Lighthouse room graphics archive is not replaced.

## Expanded isolated catalogs

Version 16 reserves two shop records that are unused by the released Disc 2
field scripts:

- normal shop 36: 29 item entries;
- Gear shop 20: 58 Gear-part entries across the five native categories.

The normal list remains below the engine's 48-entry aggregate capacity. Each
Gear category remains at or below its native 20-entry capacity. The records
are written into the shared menu catalog as new standalone inventories;
retail shop 32, retail Gear shop 17, and every other original merchant remain
byte-for-byte unchanged.

The added choices are established late-game supplies and Gear maintenance
parts suitable for a depot service unit. This inventory expansion does not
change the facility's fiction or asset policy: the bot is treated as
surviving Zeboim-era industrial hardware, and no Solaris or Krelian room,
architecture, story state, or Mass Driver technology is introduced.

## Build

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v16_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v16.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v16.cue
```

Record the v16 BIN size and SHA-256 only after automated validation and a
successful runtime playtest.

## Runtime acceptance

1. Enter the Mass Driver, complete both inclined-lift segments, cross the two
   tunnels, and reach the stationary subway platform.
2. Confirm that the Repair Bot and the rail-safety chest both render normally
   before opening a shop.
3. Press X on the bot, open Items, browse the expanded list, cancel back to
   the field, and confirm that the bot and chest graphics remain intact.
4. Reopen the bot, open Gear parts, browse all five categories, cancel back
   to the field, and confirm that neither sprite becomes strips, blocks, or
   corrupted colors.
5. Confirm that Items presents 29 entries in shop 36 and Gear parts presents
   58 total entries in shop 20.
6. Buy one affordable entry from each menu and confirm that inventory and
   money changes persist after closing and reopening the bot.
7. Repeat both open-and-cancel paths at least twice to verify that shop
   cleanup does not progressively corrupt either local sprite bank.
8. Read the train-container safety record and cross the far platform
   threshold without pressing X. The v15 route and all later dungeon
   progression must remain intact.
