# Mass Driver Dungeon 3.10 - Center-panel finale alignment

V149 is the current frozen package. It keeps V148's 33-field, 66-edge route
ending in Mass Driver Central Control target 728, its two-interaction memory and
local capsule finale, and its exact native component-04 apparition sprites.
Targets 388 and 507 and every Krelian-laboratory asset remain absent. V149
changes only canonical 2062.

## Center-panel interaction

Central Control entity 13 now belongs to the visible center back-wall computer:
prepared header node 29/model 5. Its controller is at `(-4,118)` on connected
walkmesh triangle 19. It requires facing and uses operand `0x04`, giving 24-unit
effective reach. The fresh F2 capture places Elly at
`(-3.642,114.571)`, yaw `0x0C00`, touching and facing the panel. The retired
`(-67.44,91.93)` trigger is outside the new region, and entity 12's separate
archive reader remains disjoint.

The native treasure actor, entity 16, no longer competes for Cross/X near the
computer. All 32 of its active script slots point to the donor STOP at PC
`0x0299`. The donor chest initializer and action remain audited as historical
identity evidence, but neither can run in V149.

The first valid entity-13 interaction remains Elly's subjective Zeboim-era
memory. Miang, the Launch Director, and the Systems Officer still use their
complete exact component-04 sprite archives, and the memory returns control
without launching. The second valid interaction stages Citan and runs the
complete local capsule finale.

## Material-safe Citan entrance

Citan stages behind the native east door at `(170,89,0)`, direction 6. His
bounded route crosses only material-1 connected Central Control floor:

```text
stage (170,89), triangle 28
walk  (100,89), 32 steps, triangle 30
walk  (60,84),  20 steps, triangle 23
walk  (20,80),  20 steps, triangle 21
final (20,80,0), direction 7
```

The final conversation camera targets `(8,98,-72)` from eye
`(8,-379,-170)` over 18 frames. The route remains separated by more than 32
units from both checked Elly positions near the center panel. This replaces the
non-walkable material-0 door-pocket start that could make Citan walk in place.

## Frozen Central Control identity

Target 728 canonical 2062 is 126,524 bytes with SHA-256
`e70ce6317a634b447eb941a87407112306304d3086b89ba8bde0555470f191ea`.
Its prepared 1,088-byte header remains SHA-256
`b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31`;
the packed header remains SHA-256
`9512cf649f6834c5cd641684f708bf8d57ae34c48660acaeeb8e57790a082740`.

The 3,510-byte script has SHA-256
`1aa6dd7fbeb32846a8139e12a57efd3bbc8a5899d2c97c842e8087069f592177`.
The exact changed routines are:

- entity-13 initializer: PC `0x033E`, 24 bytes, SHA-256
  `c655d253d88189b3385d8db76d745126ed37b867e90b252a40704526d6979b4a`;
- Citan stage script 21: PC `0x039F`, 11 bytes, SHA-256
  `d9358abd4ed27e8dbab0e9b89e7a826b93b648d26acc490d853463595df118f8`;
- Citan walk script 22: PC `0x03AA`, 35 bytes, SHA-256
  `4e9589542aec71a6c446ab3a7c1183ee1cc7ecc55a4dc3616d6bf8fa59cbaa2c`;
- entity-13 finale action script 2: PC `0x03CD`, 1,038 bytes, SHA-256
  `c248e21886a1309ba5c3c59d6c9e4d8dfb3b71a8c2827f9470fd041cd9407c86`.

The 18,640-byte actor component remains SHA-256
`2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538`;
the 67,668-byte component-04 sprite archive remains SHA-256
`e09e0ca20423abd18fbbbee63c37b47e0d89c8a7a1cb32a61d54d37de452b805`;
the 5,044-byte dialogue component remains SHA-256
`c5300fd84da598f56215c5561feee6932de3f726524b53704cb56fa762503006`;
and canonical 2063 remains the exact 180,224-byte native graphics payload,
SHA-256 `4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28`.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v149.bin
size: 696,130,848 bytes / 295,974 raw sectors
SHA-256: e5125cfcf4b9a876a6b605b0bbac8152ee60476fd989b4824050ca27cb7363de

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v149.cue
size: 107 bytes
SHA-256: 3b8b5e4cbcb0d2ec5e05a83f8ffea424adcd7a740c98b32674c1b8b7d61fb173

manifest: work/mass_driver_v149_stage/manifest.json
size: 237,200 bytes
SHA-256: be30b9fd1974050c52992d98989486ddb17eed95a24986cfd130101ad94aeeb5
jobs / replacements / bytes: 136 / 169 / 11,804,612
route fields / directed edges: 33 / 66
replacement aggregate: 86d4d110f86b4d1e6c95f97acd0adc0b9cdb3dcd1ed074035e304f6c007c0768
framed aggregate: f7cdc39db4a4cd6b954dee33117995cf29f74df1c0719882bef79a8aaf35162e
```

## V148-to-V149 delta and validation

The declared stage delta and exhaustive FAT payload delta are both exactly
canonical 2062. Canonical 2062 keeps its size and location, so all 4,147 FAT
descriptor tuples are unchanged. No entry kind or directory membership
changes, and 3,722 of 3,723 extractable payloads remain byte-identical.

All 169 packaged replacements re-extracted byte-for-byte. All 5,846 replacement
sectors plus the boot sector passed MODE2/Form1 validation, and an independent
full rebuild matched the frozen package byte-for-byte.

The authoritative V149 suite passed 262 tests / 2,681 subtests in 20.918
seconds with zero failures, errors, subtest failures, or skips. Fresh
user-driven replay of the center-panel interaction, complete apparition actors,
Citan's material-safe entrance, local launch, and guarded return remains
pending.

The preferred focused state is
`work/runtime_capture/near_final_v149_from_v108_vault1.sav`, 1,701,664 bytes,
SHA-256
`b044a007a583fc47e376571784dea534fa34f1cc5265b5cd5fdc75f06cefa6d5`.
It has historical V108 field 377 resident, progression flags `0x0033` (bits 4
and 5 set; launch, Citan, and memory bits 6, 7, and 12 clear), party bytes
`01 06 FF` for Elly/Emeralda/an empty third slot, and no active finale field.
Walk north so every later vault and Central Control load fresh from V149. This
is focused finale coverage, not cold-boot whole-release acceptance. Ask the
user to navigate and press controls; do not automate emulator input.
