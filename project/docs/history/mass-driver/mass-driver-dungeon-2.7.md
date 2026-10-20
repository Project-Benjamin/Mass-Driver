# Mass Driver Dungeon 2.7 - v28 El-Regulus Deathblow Suite

Version 28 repairs the reported main-menu names, renames and expands the
blue-beam Level-1 attack, makes the accessory deathblows available in the
standalone loadout, and replaces El-Regulus's empty Level-2, Level-3, and
Infinity battle programs.

## Main-menu name repair

Canonical 2595 does not store compact zero-terminated names on disc. Its
loader expects 31 fixed 20-byte records, each containing ten little-endian
glyph cells. The earlier bootstrap wrote compact runtime strings into that
region, causing Elly to appear blank and Emeralda to appear as garbage.

The builder now reconstructs the complete 620-byte name region in its actual
on-disc format. It preserves every retail character and Gear name, uses the
retail spelling `Emeralda`, and writes `El-Regulus` into Gear-name slot 21.

```text
canonical 2595 patched size: 9,048 bytes
canonical 2595 patched SHA-256:
ba2f99c3f54775e4649fb688d9cb19196a540e758b044f4699a281d5cb1423a1

patched 31-record name region SHA-256:
c56c15e575083dab1a0cd6d07f674be523d260767565760686f9bfee7d65c22a
```

## Complete command names and standalone access

Canonical system resource 29 now gives El-Regulus all twelve deathblow names:

| Attack Level | Triangle | Square | X |
|---|---|---|---|
| 1 | DoubleImpact | Ether Beam | Beat Storm |
| 2 | Sonic Drive | Heart Strike | Mega Impact |
| 3 | Flash Drive | High Diva | Blaze Dance |
| Infinity | Flash Flail | Blue Blast | Dark Diva |

The names retain Elly/Vierge's retail English command table except for
`Ether Beam`. That slot was previously called `Hard Smash`, which did not
describe its native blue-beam visual.

```text
canonical 29 patched size: 13,600 bytes
canonical 29 patched SHA-256:
99a3ef4a9e4d6435c96ab4e552589ec43bdfc5a1eeaa2d4eb02993f65ac669da

decoded canonical 29 patched SHA-256:
c39d15e8399096e34a447e23178a85aa5e5b944344eab93a34aab066a34cceeb
```

Beat Storm, Mega Impact, and Blaze Dance are Deathblower1/2/3 commands, not
ordinary learned-bit commands. The standalone GameState therefore equips
all three accessories, starts Elly at level 70, and sets all natural Gear
deathblow flags. This is a test loadout for the standalone dungeon; it does
not add maximum stats or restore the removed one-hit-kill setting.

## Ether Beam

Program 36 now uses:

1. the full player-Gear target-facing header;
2. the accepted Square camera envelope;
3. El-Regulus's native `0x44` firing pose;
4. a 30-tick charge hold;
5. a finite retail Vierge Gear sound event;
6. a four-tick event-dispatch guard;
7. El-Regulus's native blue-beam packet;
8. a 60-tick beam hold;
9. one damage dispatch, recovery, and normal completion.

The sound donor is Vierge program 41, `Flash Drive`, from canonical 2931.
Disassembly confirms that opcode `0x0163` registers its skipped eight-byte
type-5 sound event. Vierge and El-Regulus contain byte-identical 812-byte
SEDS banks, so the selected bank-1 sound is compatible and ends naturally.
No speculative resource-2964 patch or `0x003C` fade is used.

```text
sound event:
63 01 0C 00 04 00 05 04 00 01 05 00

shared SEDS SHA-256:
b67baaa48bb1f0dc868c4b4ab63ca5cdf3891b95a47ab22187dc9d6c21f98505

program 36 size: 168 bytes
program 36 SHA-256:
4d4b12d23be149a5aa72a598c23b17cc778fb5f13e685e40151894c1fd5b9312
```

The four-tick guard is required because the sound and visual wrappers share
one asynchronous event slot. It lets the sound fire before the native beam
wrapper replaces that slot.

## Higher Attack Levels

Retail programs 38-43 and 68-70 were each only `02 00 00 00`. Version 28
replaces all nine stubs with complete programs built exclusively from
El-Regulus's audited local motion clips `0x40` through `0x45`.

| Name | Program | Power | Fuel | Program size |
|---|---:|---:|---:|---:|
| Sonic Drive | 38 | 34 | 70 | 128 |
| Heart Strike | 39 | 38 | 80 | 184 |
| Mega Impact | 40 | 42 | 20 | 128 |
| Flash Drive | 41 | 42 | 100 | 148 |
| High Diva | 42 | 46 | 110 | 204 |
| Blaze Dance | 43 | 50 | 30 | 148 |
| Flash Flail | 68 | 50 | 10 | 164 |
| Blue Blast | 69 | 55 | 20 | 220 |
| Dark Diva | 70 | 60 | 30 | 164 |

Every program has one damage dispatch and one completion. The Square-column
programs are progressively longer blue-beam variants; the other programs
use two-, three-, or four-motion combinations.

The generic relocator updates every following animation pointer and both
outer roots while preserving null aliases and the complete model-data tail.

```text
canonical 2960 source SHA-256:
8ccee45222b6245fdcb4556ce15f69746bf5e2ebd88ec76aa77ec4381ab07d6d

canonical 2960 v28 size: 33,588 bytes
canonical 2960 v28 SHA-256:
a8d29df4ec60ddb40051740a7001889444b21e285cadae06a5ad19024c2b7b6c

v28 roots:
0x0010, 0x7FE8, 0x8334
```

## Release validation

The finished v28 image contains all 121 staged replacements byte-for-byte.
The standalone executable boot sector is present with valid MODE2/Form1
EDC/ECC.

```text
BIN size: 690,377,856 bytes
BIN SHA-256:
dff6888c830400f2a0b750fe081bd1ba3a327d37cdbaf73f333f616dcebc7ae2

automated tests: 132
automated subtests: 317
post-build replacement comparison: 121/121
```

## Manual runtime test

1. Cold-boot v28 and press `J` to open the ordinary main menu. Confirm that
   `Elly` and `Emeralda` display normally.
2. On the world map, put Elly in El-Regulus and move near the Mass Driver
   until the native 18,000-HP Dragon encounter begins.
3. Use an ordinary attack to reach Attack Level 1, then open the Level-1
   submenu. Confirm `DoubleImpact`, `Ether Beam`, and `Beat Storm`.
4. Use Square (`J`) for Ether Beam. Confirm the camera sequence, charge,
   audible Gear effect, sustained blue beam, nonzero damage, recovery, and
   return of the command menu.
5. Continue using ordinary attacks until Attack Levels 2 and 3 appear. Open
   each submenu and verify all three named commands.
6. At Attack Level 3, continue taking ordinary non-deathblow turns until the
   retail Hyper/Infinity roll succeeds. Infinity is intentionally still
   chance-based; level 70 satisfies its native level threshold.

The Dragon's normal HP should allow several commands to be tested in one
battle. The final perceptual timing and sound-volume judgment requires this
manual emulator check even though the binary structures and event sequencing
are statically verified.
