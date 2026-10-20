# Mass Driver Dungeon 3.12 - Reliable center-console interaction

V151 is the current frozen package. It preserves V150's 33-field, 66-edge
route, subjective two-visible-actor Zeboim memory, hidden-Miang point of view,
native-east-door Citan entrance, held camera, local capsule launch, and guarded
field-617 return. Only canonical 2062 changes. Targets 388 and 507 and every
Krelian-laboratory asset remain absent; Central Control target 728 remains the
active route's final room.

V151 changes only the invisible entity-13 interaction volume in front of the
real center control panel at prepared header node 29/model 5. No dialogue,
cutscene, camera, Citan route, action routine, actor, sprite, model, graphics,
walkmesh, or field-617 byte changes.

## Exact V150 dead-zone cause

The live rejected V150 stance placed Elly at fixed-point
`(-926741,0,7458345)`, or `(-14.140945,0,113.805313)` in world units. The
engine used integer position `(-15,113)`, walkmesh triangle 20, and yaw
`0x0C00`. Entity 13 remained centered at `(-4,118)` on triangle 19.

That stance was already inside V150's old `0x04/0x04` interaction box. The
engine doubles both OP18 operands and adds the player's fixed 16-unit radius,
so the effective X/Z reach was `24x24`; the integer center delta was only
`(+11,+5)`. Bounds therefore were not the rejection.

V150 still set the facing-required flag. For the vector to the single
controller center, the engine produced `ratan2 = 0x0116`, desired facing
`0x0EEA`, and delta `0x0D16` (`3350`). The accepted cone is delta below 700 or
above 3396, so 3350 was rejected even though Elly was visibly facing the wide
console bank and stood inside its interaction box.

## V151 controller contract

Entity 13 stays at `(-4,118)` on walkmesh triangle 19 and continues to own the
complete two-interaction finale. Its initializer is now:

```text
PC 0x033E, 24 bytes
BC 19 FC FF 76 00 C0 F8 00 00 20 F8 07 04 00
18 06 01 64 00 20 01 80 00
SHA-256: 181a80e903ce97b95af8b25c499265262879e1c5c680025446cefef371a92ba1
```

`F8 07 04 00` removes the point-target facing cone. OP18 independently uses X
operand `0x06` and Z operand `0x01`, producing effective selection reach
`28x18` after the player's radius is included. The captured `(-15,113)`,
triangle-20, yaw-`0x0C00` stance is accepted by entity 13 alone.

The neighboring interaction zones remain separate:

- entity 12 archive: center `(57,71)`, no-facing operands `0x08/0x08`,
  effective reach `32x32`;
- entity 13 launch console: center `(-4,118)`, no-facing operands
  `0x06/0x01`, effective reach `28x18`;
- entity 14 east door: center `(181,88)`, facing-gated operands
  `0x05/0x1E`, effective reach `26x76`.

The decoded walkmesh verifier proves both console centers are strictly inside
their assigned walkmesh triangles, the captured stance is inside walkable
triangle 20, only entity 13 accepts it, and the e12/e13/e14 X regions are
pairwise disjoint where required.

## Byte-identical finale sequence

The only decoded V150-to-V151 script changes are the three initializer bytes:

```text
offset 0x08CE: 03 -> 07  (remove facing gate)
offset 0x08D2: 04 -> 06  (independent X operand)
offset 0x08D3: 04 -> 01  (independent Z operand)
```

Every other decoded script byte is unchanged. In particular:

- Citan stage script 21: PC `0x039F`, 15 bytes, SHA-256
  `9a5aa669a5e137e3039f0e744cf0da4a926869f388d2e4a270a4140da5561cbc`;
- Citan walk script 22: PC `0x03AE`, 47 bytes, SHA-256
  `00b90ce55c17beb780b028d81a1f61e40b2c955ce58887eba7b9b43f5d58728f`;
- entity-13 finale action script 2: PC `0x03DD`, 994 bytes, SHA-256
  `fb6eae5e3f1645ffe2bf53752215f01370fded4cc44e8b2c953ddd7b2d27a91b`;
- arrival sequence: 76 bytes, SHA-256
  `2462b1808c776a34fce501d091e03bdaeb96f82e46d94a60279693ca3b073427`;
- held arrival-camera body: 35 bytes, SHA-256
  `f5d04c00fe5de8f416e95735ff10cd6b211096283983ad66d7809814e5690103`.

Citan is still hidden at `(225,104,0)`, direction 6, behind the native east
leaf. Scoped F8 `0x0038` covers only the bounded first leg to `(170,89)/32`,
then clears before `(100,89)/32`, `(60,84)/20`, and `(20,80)/20`; he settles
direction 7. SHOW still precedes native entity-15 script 4. The one 24-frame
camera targeting `(87,97,-72)` from `(87,-380,-170)` remains held without a
release, conversation retarget, final-camera body, or closed-leaf
reprojection, and the leaf remains visually open through world-map unload.

Only entities 17 and 18 remain visible in Elly's memory. Hidden entity 19
remains Miang's point-of-view actor at `(14,58)`, every memory eye remains
`(14,58,-125)`, no camera targets Miang, and her offscreen dialogue remains
labelled `MIANG`. All 32 entity-16 action slots still point to STOP at PC
`0x0299`; the native chest remains retired.

## Frozen Central Control identity

Target 728 canonical 2062 is 126,444 bytes with SHA-256
`094a504a9b7d51e7f0beefbf83df1729b7f582f8e932589a567ff70bc5fd936d`.
The prepared 1,088-byte header remains SHA-256
`b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31`;
the packed 1,088-byte header remains SHA-256
`cb5439aaa3b2bd00aa1fb103356f1fd7ff06c1de34c724eea1bed1b4193cd1db`.

The decoded components are:

```text
images:       4 bytes / df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119
walkmesh: 2,540 bytes / 6a1f335cd2cf00bcec7a5412b8ab7392fcff378912fd2857880d69f2186e6a14
models:  13,504 bytes / 9bb9ef16cb1f85b0c2a4052d79a710cb91224ea78be7f7b72c246ac6183ab24e
actors:  18,640 bytes / 2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538
sprites: 67,668 bytes / e09e0ca20423abd18fbbbee63c37b47e0d89c8a7a1cb32a61d54d37de452b805
script:   3,482 bytes / f3c72efec276d82deb51dfdf9c18bab27db9207263aeface5cd3c9aeec3e476f
encounters: 528 bytes / e88b412320050425ae87abad80b51749da8171b023e943604cf47a370535ab38
dialogue: 4,998 bytes / f9b38b8cef89b1b4b212a3eb41fb3d464beea71cdaa35777a33614f2b4f1a948
triggers:     0 bytes / e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Canonical 2063 remains the exact 180,224-byte graphics payload, SHA-256
`4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28`.
Field 617 canonical 1840 remains 71,180 bytes, SHA-256
`d35a13ab5be99c4ebb6e3934bd4ab0c00613839d810c2a4984dae70adbdefb26`.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v151.bin
size: 696,130,848 bytes / 295,974 raw sectors
SHA-256: 60cdf6e6ab9292908e7e20e0095da3dd6d34f89ce291d6a185fdbb1f07bf24a7

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v151.cue
size: 107 bytes
SHA-256: 18dd7904fb0b60a40258a1fdf03fa011ed17ad377d7c317d8f728aa060d1e3dc

manifest: work/mass_driver_v151_stage/manifest.json
size: 237,578 bytes
SHA-256: a62687e0bc871410d6dd461e36ff79776d80a9b3b7ee268cc623dac8206775c0
jobs / replacements / bytes: 136 / 169 / 11,804,532
route fields / directed edges: 33 / 66
replacement aggregate: 402453c4d884741f653ccaa29620fce59da7ad2bb19c7a7cf9b3db81fbc252c6
framed aggregate: 4b703993944fc5911a6e41003f714a95ed7ec2a594011b1b2dcf721346854777
```

## V150-to-V151 delta and validation

The declared stage and exhaustive complete-FAT payload deltas are both exactly
canonical 2062. All 4,147 FAT descriptor tuples, entry kinds, and directory
memberships are unchanged; 3,722 of 3,723 extractable payloads remain
byte-identical. Exactly one raw sector differs, LBA 221,372, within canonical
2062's unchanged sector range 221,314 through 221,375.

All 169 packaged replacements re-extracted byte-for-byte. All 5,846 replacement
sectors plus the boot sector passed MODE2/Form1 EDC/ECC validation. A second
complete stage and BIN rebuild reproduced the exact identities above. The
five structural verifiers and the direct decoded target-728 walkmesh,
initializer, CFG/VM, routine, component, and header audits passed.

The authoritative V151 structural run passed 262 tests / 2,682 subtests in
22.641 seconds with exit 0 and zero failures, errors, subtest failures, or
skips. Fresh user-driven acceptance of the repaired center-console stance and
the preserved memory, Citan entrance, held camera, launch, and return remains
pending.

The preferred focused state is
`work/runtime_capture/near_final_v151_from_v108_vault1.sav`, 1,701,665 bytes,
SHA-256
`c0a105bddcc3d2b28cc32ab3a710d07c84f411cd3f5f69fb8bf3aed7661619de`.
It mounts the exact V151 CUE. Historical V108 field 377 is resident; its FAT
table SHA-256 is
`d03a2a9168dbff1a76a3a939162c1784810763628cb374b6a5451ecc89155e07`
at payload offset `0x11A66` / RAM `+0x10004`, while payload bytes outside the
FAT and the complete decompressed gameplay payload remain byte-identical to
the V150 state. Progression flags are `0x0033`: authorization and Guardian
bits 4 and 5 are set; launch, Citan, memory, and related bits 6, 7, and 12 are
clear. Party bytes are `01 06 FF`, target 728 is absent, and it will cold-load
from V151 media. Walk north so every later vault and Central Control load
fresh. This is focused finale coverage, not cold-boot whole-release
acceptance. Ask the user to navigate and press controls; do not automate
emulator input.

## Historical V150 boundary

V150's frozen subjective-memory, native-door, held-camera, package, runtime
state, and validation record remains byte-for-byte in
[`mass-driver-dungeon-3.11.md`](mass-driver-dungeon-3.11.md). V151 changes only
the Central Control entity-13 selection contract and does not rewrite that
historical release record.
