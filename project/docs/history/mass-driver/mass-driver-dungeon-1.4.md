# Mass Driver Dungeon 1.4 — v15 Platform Vendor

Version 15 keeps the complete v14 route, doors, objective loop, boss, and
world-map bootstrap unchanged. Its only playable addition is a Repair Bot
merchant on field 721's abandoned employee subway platform, outside the
stationary train.

## Placement and interaction

- Field: target 721, retail Lighthouse subway donor 397.
- Entity: 11, an unused character-10 PC stub in this standalone party.
- Position: `x=1000`, `z=220`, walkmesh 0.
- Facing: cardinal parameter 1 (`+X`), toward the east-side arrival and
  platform lane.
- Bounds: a modest explicit NPC collider that does not overlap the existing
  rail-safety container, the route across the platform, or either automatic
  threshold.
- Controls: X opens an input-safe native choice window. Cancel closes it.

The merchant uses the retail shop engine rather than simulated dialogue:

- **Items** invokes normal item shop 32.
- **Gear parts** invokes Gear shop 17.
- Both paths return through retail `FE87` shop cleanup before player control
  is restored.

These are Big Joe's late-game Disc 2 catalogs. They provide restorative
items, permanent-stat drives, high-grade Gear frames, armor, engines, and
options. The standalone's existing 183,838 G starting balance is unchanged.

## Asset contract

The visible NPC is the game's actual Repair Bot from the Aveh mountain repair
station, field 172. It is reused as a surviving Zeboim-era depot service unit;
this is a fan-reconstruction role, not recovered cut-content provenance and
not Solaris or Krelian technology.

The donor is self-contained:

- actor bank 2 SHA-256:
  `1d0fb9c11104a1b90848db8ad39fa4e023a071cd826c92b60e62ab319ff6a382`
- embedded palette record SHA-256:
  `c2e7d3104119403c0e5a019f223d63bf3852a2f013cb76c677610773460697c5`
- 32-byte, 16-color CLUT SHA-256:
  `730e111722b592cc0bc0ae8e4c5bf4293b0ee3d5ee1a218aeaa7c090e7d9a8af`
- sprite bank 2 SHA-256:
  `0fb607468497aa16a89b900aea7a4bce92fe039ad541dff894e5f701b28327b2`

Those banks replace target 721's unused local bank 0. The existing chest in
bank 1 remains byte-for-byte unchanged. Bank 0 moves from `(832, 0, 0, 0)` to
checked free VRAM at `(768, 256, 0, 0)`; the Lighthouse room graphics archive
is not replaced. The actor bank's embedded CLUT is uploaded to local palette
slot 0 by the normal character-sprite path.

## Build

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v15_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v15.bin
```

## Runtime acceptance

1. Enter the Mass Driver, complete both inclined-lift segments, and cross the
   same two tunnels into the subway.
2. Confirm that the Repair Bot is visible on the platform outside the train,
   faces the player lane, and does not obstruct the rail-safety container or
   either exit.
3. Press X on the bot. The menu must offer Items and Gear parts without
   selecting an option from the same held X press.
4. Open each shop, buy one affordable entry, back out, reopen the bot, and
   confirm inventory and money changes persist normally.
5. Read the original train-container safety record and cross the far platform
   threshold without pressing X. Both v14 behaviors must remain intact.
