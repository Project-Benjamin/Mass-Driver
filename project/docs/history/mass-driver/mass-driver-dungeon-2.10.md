# Mass Driver Dungeon 2.10 - v31 Ether Beam Audio

Version 31 changes only Ether Beam's sound selection from the accepted v30
deathblow implementation. Its native blue-beam visual, camera, charge and
hold timing, damage dispatch, recovery, and completion remain unchanged.
DoubleImpact, Beat Storm, and every Level-2, Level-3, and Infinity program
also remain unchanged.

## Retail sound provenance

The selected cue is the two-layer energy sound authored for Xenogears's
`Raimai` attack, not a newly synthesized approximation:

```text
canonical 2594, Gear 15 record 9:
animation 41, power 42, fuel 100

canonical 29, Gear 15 command-name entry 43:
slot 9 = Raimai

canonical 2981:
program 41 -> local clip/program 65
program 65 -> sound IDs 7 and 8 + visual effect 0x19
```

Canonical 2981 audit:

```text
size: 0x6248 / 25,160 bytes
SHA-256:
a806f1d8f6030aae806f03b73222ece61b7187359c86ef5376e41ff3df52d1c0

program 65 size: 108 bytes
program 65 SHA-256:
93a415f15212a783c91241e62a39791f9c2be2833e3f9ede15a40b33deb08f18

SEDS bounds: 0x5EE0..0x6248
SEDS SHA-256:
ca09057448fe4e461a17157c0c669dce2b147ee27a6107ca27bdab0190ec0d51

effects 7+8 bounds within SEDS: 0x15F..0x1B5
effects 7+8 size: 86 bytes
effects 7+8 SHA-256:
5f8b4067e4217937a7fad4c91753872ade0dfd4992dffa7ea83dd91782a00625
```

The four copied streams select bank 1/sample 3, bank 0/sample 14, bank
0/sample 35, and bank 1/sample 6. El-Regulus's own retail SEDS already
references all four pairs, proving that the normal Gear battle path has the
required waveform banks loaded.

Alpha Weltall was audited separately. Its embedded SEDS is byte-identical to
Weltall's and its opcode-63 packets are generic movement/action cues. The
named `Grahf Beam` belongs to Grahf's non-Gear sprite/global-sequence path,
not to a transplantable Alpha Weltall Gear SEDS. It was therefore rejected
for this fix.

## Isolated auxiliary bank

El-Regulus retail animation 29 already preloads canonical 3368 as selector 2.
That resource's six-entry sound container is empty in retail. Version 30 put
Guided Shot's seven-effect checked SEDS there. Version 31 retains every byte
of those seven effects, grows only the SEDS pointer table, and appends the
86-byte Raimai cue as effects 7 and 8.

Composite SEDS:

```text
size: 0x1F0 / 496 bytes
effect count: 9
data offset: 0x44
additive checksum: 0
SHA-256:
d922c9c85dae0dae5e4206fb3c30811d854c50dbce915362d7cae4d350a9ef7c

pointers:
0000 0000 004B 0069 007E 0092 00A9 00BB 00D9
00FB 0114 0135 0165 017C 019A 01B4 01C9 01DD
```

Patched canonical 3368:

```text
size: 0x228C / 8,844 bytes
outer roots: (2, 0x10, 0x207C, 0x228C)
nested pointers:
(0x20, 0x20, 0x210, 0x210, 0x210, 0x210, 0x210)
SHA-256:
ecbd52b38f9ccff189626d0cc9f752331db1d3eb203f14acb0d76e953e6cd1d7
```

Ether Beam's 12-byte audio-only event is now:

```text
63 01 0C 00 00 00 05 07 00 02 08 00
```

The selector remains 2. The existing four-tick dispatch guard and native
blue-beam visual packet follow it unchanged.

## Isolation proof

Comparing staged v30 and v31 replacements shows that only canonical 2960 and
canonical 3368 differ. Within canonical 2960, only program 36 differs, its
size remains 168 bytes, and the whole file has exactly two changed bytes:

```text
offset 0x78D5: effect 4 -> effect 7
offset 0x78D8: effect 5 -> effect 8
```

Program 36 hashes:

```text
v30:
3e41bd6309bc875dfb7389dd52da326156a00f1be17b14c6ef4fc77db4b17150

v31:
beb3d02a0d815e9587582eb57212a14521a4a6d4333a3aaadb2e6ba50094ad78
```

Patched canonical 2960 remains 33,608 bytes with roots
`(2, 0x10, 0x7FFC, 0x8348)` and now has SHA-256:

```text
a8f2cc9572af8ebbf9f8183664c7149f2ef1edb3011a1ad5afa996d3c2815930
```

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v31.bin

BIN size: 690,377,856 bytes
BIN SHA-256:
0fcc7f330baebc991ba16dd4a1dc34957204ecd5814b7710cce1a62e5750a635

automated tests: 132 passed, 317 subtests passed
post-build replacement comparison: 122/122 exact

boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid
```

## Manual audio acceptance

1. Close any running v30 session and cold-boot
   `output/PLAY_MASS_DRIVER_STANDALONE.cmd`; it now targets the v31 CUE.
2. On the world map, put Elly in El-Regulus and move near the Mass Driver
   until the Dragon encounter begins.
3. Use an ordinary attack to reach Attack Level 1. Open the Level-1 menu and
   select `Ether Beam` (Square; `J` in the portable keyboard profile).
4. Confirm that the new two-layer energy sound starts with the blue beam,
   sounds like a sustained Gear energy discharge rather than the prior
   Guided Shot cue, stops normally, displays nonzero damage, and returns
   control to the command menu.

Binary validation proves the exact retail cue and isolation. Perceptual
quality and synchronization still require this emulator test.
