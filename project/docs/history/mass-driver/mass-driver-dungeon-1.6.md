# Mass Driver Dungeon 1.6 - v17 Shop Loader Correction

Version 17 preserves the complete v16 dungeon, retail-proven Repair Bot VRAM
layout, and isolated 29-item/58-Gear-part inventories. It corrects the
black-screen hang observed when selecting **Items** from the bot.

## Root cause

The v16 catalog contents, archive offsets, shop IDs, and disc injection were
valid. The failure was in the final LZSS command group of each newly
compressed catalog stream.

Xenogears' PlayStation heap decoder executes all eight commands represented
by a control byte before comparing the output pointer with the declared end:

- v16's normal-shop stream reached its declared 3,684 bytes after the first
  command, then emitted seven more bytes;
- v16's Gear-shop stream reached its declared 3,009 bytes after the third
  command, then emitted five more bytes.

The decoder therefore passed the end pointer instead of landing on it. The
normal shop overwrote its heap allocation and continued decoding, leaving
the field faded to black with only the character sprites visible.

The previous Python validation stopped as soon as it had decoded the requested
logical size, so it did not reproduce the retail decoder's full-group
behavior.

## v17 correction

The v17 catalog encoder completes every final control group with zero
literals and includes those literals in the stream's declared allocation:

| Catalog | Logical table | Declared/runtime output | Final padding |
| --- | ---: | ---: | ---: |
| Normal shops | 3,684 bytes | 3,691 bytes | 7 zero bytes |
| Gear shops | 3,009 bytes | 3,014 bytes | 5 zero bytes |

The added bytes follow the fixed-size records and are never indexed by either
shop overlay. The native decoder now lands exactly on its declared end after
the eighth command. The rebuilt canonical 2593 resource is 65,564 bytes with
SHA-256
`eaffb76f83f29365b2c5c7946cafb1148bd702e02d6a04a026988372f0b6a604`
and remains within its original 33-sector allocation.

The builder now contains a second validator that models the PlayStation
decoder's complete eight-command loop. It rejects any stream that overruns
its declared heap allocation or reads beyond its archive entry.

Shop IDs remain:

- normal shop 36 with 29 items;
- Gear shop 20 with 58 parts across category counts 13, 8, 6, 12, and 19.

Both IDs are inside their native tables. No companion metadata resource is
indexed by shop ID, and all source retail catalogs remain byte-for-byte
unchanged.

## Build

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v17_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v17.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v17.cue
```

## Runtime acceptance

1. Cold-boot v17 and reach the Repair Bot outside the stationary subway.
2. Press X, select **Items**, and confirm the shop interface appears.
3. Browse the complete 29-entry list, cancel to the field, and confirm that
   the bot and chest still render normally.
4. Reopen the bot, select **Gear parts**, browse all five categories, and
   cancel to the field.
5. Repeat both menus twice and buy one affordable entry from each.
6. Confirm that the far platform threshold still enters the Zeboim
   vestibule automatically.

## Accepted build

The Repair Bot Item and Gear-parts menu regression was confirmed working
in-game on July 24, 2026. The accepted v17 image also passed 115 automated
tests, 134 subtests, and a byte-for-byte extraction comparison of all 37
injected resources.

- BIN size: 690,368,448 bytes
- BIN SHA-256:
  `fec501b46ad7468c4bd831d5c101e50742ecfc0e638407ef63725e16961bafeb`
- implementation commit: `22d0ebf`
