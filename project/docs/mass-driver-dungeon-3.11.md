# Mass Driver Dungeon 3.11 - Subjective memory and natural Citan reveal

V150 is the current frozen package. It preserves V149's 33-field, 66-edge
route, centered entity-13 control-panel frontage, retired native chest, and
Central Control launch. Only canonical 2062 changes. The memory now stays
strictly inside Elly's point of view, and Citan enters through the native east
door without a blocked walk, camera cut, or reprojected closed leaf.

Targets 388 and 507 and every Krelian-laboratory asset remain absent. Central
Control target 728 remains the active route's last room.

## Subjective Zeboim memory

The first entity-13 interaction still shows Elly a Zeboim-era command-room
memory while Emeralda sees an empty room. Only entity 17, the Launch Director,
and entity 18, the Systems Officer, are visible. Entity 19 is Miang's hidden
point-of-view actor at `(14,58)`; no scene command shows her and no camera
targets her.

Every memory view uses eye `(14,58,-125)`. The speaking views target only the
Director or Systems Officer. Miang remains an offscreen voice, and each of her
dialogue blocks is labelled `MIANG` without a visible Miang actor. Exact native
component-04 sprite archives remain installed, so the two visible apparitions
render as complete people rather than pixel-sized dots. Entities 14 and 15 and
all other Central Control assets are byte-identical to V149.

## Native-door Citan entrance and held camera

Citan is staged hidden at `(225,104,0)`, direction 6, on material-0 triangle 32
behind the native east-door leaf. His stage script sets scoped F8 mask `0x0038`.
The arrival establishes one camera targeting `(87,97,-72)` from
`(87,-380,-170)` over 24 frames and holds it through the complete entrance,
dialogue, launch, and world-map handoff.

The action shows the field immediately before calling native entity 15 script
4. The closed leaf therefore occludes hidden Citan, the native helper opens the
door, and the already-held camera reveals him naturally. There is no camera
release, second cut, final-camera reprojection, or closed-leaf reprojection.
The leaf stays visually open through the world-map transition.

Citan's bounded route is:

```text
hidden stage  (225,104), triangle 32, material 0, direction 6
first leg     (170,89),  bound 32, then clear scoped F8 0x0038
second leg    (100,89),  bound 32
third leg     (60,84),   bound 20
fourth leg    (20,80),   bound 20
final settle  (20,80,0), direction 7
```

The first chord traverses triangles 32, 27, and 28. The remaining material-1
route traverses connected triangles 28, 29, 30, 31, 23, 22, and 21. The scoped
F8 override applies only to the short door-pocket leg and clears immediately
after it. Citan then faces Elly, assists with the capsule launch, and is removed
by the guarded field-617 return.

## Frozen Central Control identity

Target 728 canonical 2062 is 126,444 bytes with SHA-256
`74badc327537c6fb5c5ca6c165f87a7c94a15f8de9cad944e402a9312bc65b42`.
Its prepared 1,088-byte header remains SHA-256
`b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31`;
the packed header is SHA-256
`cb5439aaa3b2bd00aa1fb103356f1fd7ff06c1de34c724eea1bed1b4193cd1db`.

The decoded components are:

```text
images:       4 bytes / df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119
walkmesh: 2,540 bytes / 6a1f335cd2cf00bcec7a5412b8ab7392fcff378912fd2857880d69f2186e6a14
models:  13,504 bytes / 9bb9ef16cb1f85b0c2a4052d79a710cb91224ea78be7f7b72c246ac6183ab24e
actors:  18,640 bytes / 2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538
sprites: 67,668 bytes / e09e0ca20423abd18fbbbee63c37b47e0d89c8a7a1cb32a61d54d37de452b805
script:   3,482 bytes / 172d20ae35f6d63b247610c245adbdc4f4baa226f746a456f23d748f7099028c
encounters: 528 bytes / e88b412320050425ae87abad80b51749da8171b023e943604cf47a370535ab38
dialogue: 4,998 bytes / f9b38b8cef89b1b4b212a3eb41fb3d464beea71cdaa35777a33614f2b4f1a948
triggers:     0 bytes / e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

The exact audited routines are:

- entity-13 initializer: PC `0x033E`, 24 bytes, SHA-256
  `c655d253d88189b3385d8db76d745126ed37b867e90b252a40704526d6979b4a`;
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

All 32 entity-16 action slots still point to STOP at PC `0x0299`. Canonical
2063 remains the exact 180,224-byte graphics payload, SHA-256
`4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28`.
Field 617 canonical 1840 remains 71,180 bytes, SHA-256
`d35a13ab5be99c4ebb6e3934bd4ab0c00613839d810c2a4984dae70adbdefb26`.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v150.bin
size: 696,130,848 bytes / 295,974 raw sectors
SHA-256: b28288e1a276b1a56dbe07ee9cb610ce85ee45473af1eeae18bb4898afeb915d

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v150.cue
size: 107 bytes
SHA-256: d0c5ecd25396b40d09009bd0b2960e68e9453594fe377b801c096fdc2fd66e4e

manifest: work/mass_driver_v150_stage/manifest.json
size: 237,297 bytes
SHA-256: 2c3585a1a22ca46049597536e40759d00c7708a40756de591a5ac09e37578328
jobs / replacements / bytes: 136 / 169 / 11,804,532
route fields / directed edges: 33 / 66
replacement aggregate: 988cd68d882303ceef30d7d8c7d2d45f488424b6fa01dbe6fe702320691afeab
framed aggregate: b8d78bb4bc92f1e0e09efe80205712d7d97d96bf0efc5dfb1cbc7263c8a57392
```

## V149-to-V150 delta and validation

The declared stage delta is exactly canonical 2062. The exhaustive FAT payload
delta is canonicals 17, 22, and 2062; canonicals 17 and 22 are regenerated FAT
mirrors and add no gameplay content. One of 4,147 descriptor tuples changes:
canonical 2062 remains at sector 221,314 and shrinks from 126,524 to 126,444
bytes. Entry kinds and directory memberships are unchanged, and 3,720 of 3,723
extractable payloads remain byte-identical.

All 169 packaged replacements re-extracted byte-for-byte. All 5,846 replacement
sectors plus the boot sector passed MODE2/Form1 EDC/ECC validation. An
independent stage and complete BIN rebuild matched byte-for-byte. The five
route, door, save-point, role, and scene-continuity verifiers passed; the action
CFG and augmented target-728 VM audit found no invalid target or unsafe loop.

The authoritative structural run passed 262 tests / 2,681 subtests in 23.044
seconds with zero failures, errors, subtest failures, or skips. Fresh
user-driven visual acceptance of the subjective memory, native-door reveal,
held camera, open leaf through launch, and guarded return remains pending.

The preferred focused state is
`work/runtime_capture/near_final_v150_from_v108_vault1.sav`, 1,701,665 bytes,
SHA-256
`9704f618da1834db9e0ab9ea3223348006456bb762cc4401ada94075b06b6808`.
It mounts the exact V150 CUE. Historical V108 field 377 is resident; its FAT
table SHA-256 is
`d03a2a9168dbff1a76a3a939162c1784810763628cb374b6a5451ecc89155e07`
at payload offset `0x11A66` / RAM `+0x10004`, while payload bytes outside the
FAT are unchanged. Progression flags are `0x0033`: authorization and Guardian
bits 4 and 5 are set; launch, Citan, memory, and related bits 6, 7, and 12 are
clear. Party bytes are `01 06 FF`, target 728 is absent, and it will cold-load
from V150 media. Walk north so every later vault and Central Control load fresh.
This is focused finale coverage, not cold-boot whole-release acceptance. Ask
the user to navigate and press controls; do not automate emulator input.
