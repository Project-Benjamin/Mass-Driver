# Mass Driver Dungeon 2.6 - v27 El-Regulus Level-1 Deathblows

Version 27 fixes the two independent faults reported in El-Regulus's
Attack-Level-1 menu while preserving the accepted v26 standard attacks and
the rest of the standalone Mass Driver dungeon.

## Runtime symptoms and causes

The missing names did not come from Gear attack-stat archive 2594. Xenogears
loads them from canonical system resource 29. El-Regulus's command-name entry
38 contains Japanese double-byte glyph codes in Level-1 slots 3-5, but the US
font has no visible glyph bitmaps for those codes. The result is a blank
Triangle/Square/X name even though the menu slot exists.

The no-damage behavior was separate. Native El-Regulus battle-animation
programs 35, 36, and 37 contained their motion, effects, waits, recovery, and
completion operations, but none contained mecha opcode `0x003F`. That opcode
is the battle engine's damage-result dispatch. Program 35 therefore appeared
to cancel, while program 36 could show its blue beam without applying or
displaying the calculated result.

## Retail names and native stats

Playable Omnigears reuse the command naming of their pilots' base Gears.
Accordingly, v27 copies only Elly/Vierge's three retail Level-1 names from
system-name entry 30 into El-Regulus entry 38:

| Controller | Keyboard | Name | Program | Power | Fuel |
|---|---|---|---:|---:|---:|
| Triangle | I | DoubleImpact | 35 | 26 | 40 |
| Square | J | Hard Smash | 36 | 30 | 50 |
| X | K | Beat Storm | 37 | 34 | 10 |

The name patch copies each donor string and its original display dimensions.
It does not change the three intentionally blank standard-attack labels,
higher-level labels, archive offsets, or any other system-name entry. The
Level-1 powers, accuracy, fuel costs, and other attack-stat fields were
already valid and remain unchanged.

```text
canonical 29 source:
13,756 bytes
SHA-256 67546805e7e52c8c36561b1f5dc38477aee0d87b788ed980d2a859936ed86029

decoded source:
29,023 bytes
SHA-256 845027957c098c69175a2b98e63b0d49c0c7c8d420ba195ef1287e72e49cc879

canonical 29 patched:
13,684 bytes
SHA-256 f6f62f7e8f8ed20c72b118de7f99b61e352d195dea21ecd9c24ee2552cdb3056

decoded patched:
29,023 bytes
SHA-256 83f39f4ac19cd355708658489bb27a799c6d455ae5578c97f6bc176be0cf3ac7
```

The original stream relies on harmless sector padding for its final retail
LZSS command group. The replacement is recompressed as an exact-size stream
whose last group is complete inside the resource itself.

## Damage dispatch and relocation

Each native Level-1 program gains one `3F 00` damage dispatch at its audited
impact point:

| Program | Source size | Patched size | Dispatch offset | Patched SHA-256 |
|---:|---:|---:|---:|---|
| 35 | 44 | 44 | `0x18` | `535ea110194914182f70cbf6e4ac8ab6e60d67cdb7f2886014ff1b7d580be256` |
| 36 | 52 | 56 | `0x2E` | `6c9db117a19eebd5320b939786fb1c1cee469b3006b5ce90f93c979cf4ddea8b` |
| 37 | 28 | 28 | `0x14` | `5609910ca4f2e52ff32b8cf4d287b2a6abfbac498a8e9ca0c10d7d31e803ad7c` |

Program 36 grows by four bytes overall, so the builder relocates every
subsequent nested pointer and both outer archive roots. Null and alias entries
in the retail pointer table are preserved rather than rebuilt.

```text
canonical 2960 source SHA-256:
8ccee45222b6245fdcb4556ce15f69746bf5e2ebd88ec76aa77ec4381ab07d6d

canonical 2960 v27 SHA-256:
97ada0b0b26d2d9df0cdbbbc114af9f496c4b975a46ff1f4d413678cac455dfd

v27 outer roots:
0x0010, 0x79CC, 0x7D18
```

Programs 32, 33, and 34 retain their exact v26 sizes and hashes. Canonical
2594 also retains its v26 SHA-256
`cb902074fe68f7876f5e8791e87daa64fa9cc42c9b660be4a675a9047f5e7a43`;
the Level-1 repair does not alter any attack-stat record.

## Build and binary validation

For a newly prepared workspace, extract canonical 29 in addition to the v26
inputs:

```powershell
python tools/xgdisc.py extract $sourceDisc work/_audit_system_data `
  --canonical-disc2 29 --force

python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v27_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v27.bin
```

The v27 build passed 130 automated tests and 265 subtests. All 121 staged
resources were independently re-extracted from the finished BIN and matched
byte-for-byte, including canonical 29, 2594, and 2960.

```text
BIN size: 690,375,504 bytes
BIN SHA-256:
c50f7070ae06dbc0337ce597623bab413e5252b307f7774ed54d1afced8246a0
```

## Runtime acceptance

Cold-boot v27, mount El-Regulus outside the Mass Driver, and keep moving near
the landmark until the native Dragon encounter starts. Build Attack Level 1,
then open its deathblow submenu.

1. Triangle/I must display `DoubleImpact`, complete its action, and show a
   nonzero damage result.
2. Square/J must display `Hard Smash`, show its blue beam, and then show a
   nonzero damage result.
3. X/K must display `Beat Storm` and show a nonzero damage result if that
   command is available in the current battle state.
4. Each action must return El-Regulus to its ready stance and restore the
   normal command flow.

The Dragon has 18,000 normal HP, so it should survive long enough to test
multiple commands.
