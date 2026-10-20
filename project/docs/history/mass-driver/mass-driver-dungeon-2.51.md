# Mass Driver v74: El-Regulus attack-level and Infinity repair

Version 74 repairs El-Regulus's reported Attack Level 1 cap and rebuilds all
three Infinity attacks as mixed melee-and-ether finishers. The rest of v73's
dungeon, two-character Guardian party, optional Reserve Magazine 02 archive,
and final-only Citan sequence is unchanged.

## Root cause and progression repair

The cap was a bootstrap inventory error, not an engine restriction or a
missing higher-tier attack record. Gear 10 begins at GameState offset `0xFE0`,
and its three accessory slots are `0xFE9..0xFEB`. V73 wrote:

```text
5A 5B 5C
```

Retail canonical 29 identifies those items as `Frame HP10`, `Frame HP30`, and
`Frame HP50`. Canonical 2594 independently proves it: their `0x1C`-byte item
records use effect selector `05` with parameters `01/03/05`.

V74 writes the actual retail progression accessories:

```text
60 61 62  =  Atk Lv1 Max / Atk Lv2 Max / Atk Lv3 Max
```

Their checked canonical-2594 effect selectors are `06/07/08`. Elly's natural
deathblow word remains the correct little-endian `00 FC` (`0xFC00`) at
GameState `0x16E0`, so her six natural Gear commands and the three
accessory-only commands are available together. Ordinary attacks can now
advance `0 -> 1 -> 2 -> 3`; the native Hyper roll can then enter Infinity.

```text
canonical 2595 size: 9,048 bytes
canonical 2595 SHA-256:
692ed1e040f11cfbccf5eaebcbbe51d508fbda94d5821b48750352f5bffbb4dc
```

## Level 2, Level 3, and Infinity programs

The existing record wiring is retained and checked:

| Tier | Records | Animation programs | Power | Fuel |
|---|---:|---:|---:|---:|
| Level 2 | 6-8 | 38-40 | 34 / 38 / 42 | 70 / 80 / 20 |
| Level 3 | 9-11 | 41-43 | 42 / 46 / 50 | 100 / 110 / 30 |
| Infinity | 12-14 | 68-70 | 50 / 55 / 60 | 10 / 20 / 30 |

Every program has exactly one damage dispatch, one recovery path, and one
normal completion. Level 2 and Level 3 no longer use local clip `0x43`, which
is El-Regulus's ducking motion.

All three Infinity programs now combine physical strikes with the native blue
ether beam:

| Program | Melee prelude | Ether finish | Size |
|---:|---|---|---:|
| 68 `Flash Flail` | `0x40`, `0x45` | short Guided Shot cue and beam | 128 |
| 69 `Blue Blast` | `0x41`, `0x45` | cinematic Raimai cue and beam | 204 |
| 70 `Dark Diva` | `0x42`, `0x45` | longest Raimai cue and beam | 192 |

The `50/55/60` power and `10/20/30` fuel curve matches the common retail
Omnigear Infinity tier. The new programs are 24 bytes smaller in aggregate,
moving the runtime-sensitive model root away from `0x8000`:

```text
canonical 2960 size: 33,584 bytes
outer roots: (2, 0x10, 0x7FE4, 0x8330)
canonical 2960 SHA-256:
7a332d57ca4b2e67a0649bcc6d0cef8f2121f75d3087c942bde6b964fa3749f7
```

## V74 artifacts and integrity

| Artifact | Size | SHA-256 |
|---|---:|---|
| `output/Xenogears_PW_CD2_mass_driver_standalone_v74.bin` | 695,531,088 | `40fd54346f6ec4b08367da68b521fa7b6ca0cc140c12a273b43c02c7dc981018` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v74.cue` | 106 | `998e9eacb3bda0d6f6c3ecc6182b3a8e34521280afbad2d0bfd3681e4800974e` |
| `work/mass_driver_v74_stage/manifest.json` | 178,120 | `f775619acb0ed238f227345ebc8f1bd197208d103b5ac4913f296aeeef6345a3` |

All 156 declared replacements re-extract byte-exact from the finished disc.
They total 10,403,551 bytes and have canonical-ID-order aggregate SHA-256
`bbafe542075623454f0fe01e5e6d9cb44bc4a2adad213d2aa609f39534bfa85a`.
Only canonicals 2595 and 2960 differ from v73; the two images differ in six
raw sectors. All 111,767 retail-changed or output-only sectors regenerate
exactly as MODE2/Form1 with valid EDC/ECC. All 3,565 undeclared ordinary FAT
files remain byte-identical to retail.

The final automated suite passes **193 tests and 2,238 subtests**.

## Manual acceptance

Cold-boot the v74 CUE and choose New Game. An older save or F1 state retains
the incorrect Gear inventory and cannot validate this repair.

1. Mount El-Regulus and enter a native Gear battle.
2. Use only ordinary attacks and confirm Attack Levels 1, 2, and 3 appear.
3. At each level, confirm all three named commands are available and return
   normally after dealing damage and consuming fuel.
4. Hold Level 3 until the native Hyper roll enters Infinity.
5. Exercise `Flash Flail`, `Blue Blast`, and `Dark Diva`; confirm each shows a
   distinct two-motion melee prelude flowing into the blue ether beam.

Static validation proves the item IDs, records, animation pointers, damage
dispatches, archive boundary, and disc integrity. Final timing, camera, sound,
and perceived damage still require this emulator acceptance pass.
