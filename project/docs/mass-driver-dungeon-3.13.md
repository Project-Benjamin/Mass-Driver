# Mass Driver Dungeon 3.13 - Reliable hidden-owner memory dialogue

V152 is the current frozen package. It preserves V151's 33-field, 66-edge
route, repaired center-console frontage, subjective two-visible-actor Zeboim
memory, native-east-door Citan entrance, held camera, local capsule launch, and
guarded field-617 return. Only canonical 2062 changes. Targets 388 and 507 and
every Krelian-laboratory asset remain absent; Central Control target 728 remains
the active route's final room.

V152 repairs two related presentation failures in entity 13's completion
action: every entity-13-owned dialogue now uses the native F5 control flag
`0x01`, and all 12 subjective-memory eyes use the stable Miang-aligned authored
ATEL coordinate `(174,-102,-125)`. Authored dialogue, its labels and IDs, the
hidden Miang anchor, every camera target, the visible actors, Citan's entrance,
the native door, the launch, and the return remain unchanged.

## Exact V151 saved-state failure

The captured failure state is
`work/duckstation/savestates/SLUS-00669_1.sav`, 1,752,967 bytes, SHA-256
`8bc81de760fda0ba5522c01b439a4aa152082bd8c48182e560c62f8747419717`.
It has V151 target 728 resident and reaches memory dialogue 21 after staging
entities 17 and 18 and the reaction camera. Entity 19 and the party remain
hidden, launch bit 6 and memory bit 12 remain clear, and all entity-13 action
slots have stopped.

The first memory F5 used control flag `0x00`. Native `WAIT_DIALOG` sees that
the talking owner is hidden entity 13, whose actor flags include `0x0200`.
Because F5's trailing bit 0 is clear, that hidden-owner condition takes the
native OP_STOP path. The completion action terminates before dialogue 21 can
finish, leaving the memory actors and reaction camera stranded. The saved
textbox evidence is the stopped closing state `flags=0x0081`, `openTimer=7`,
owner `-1/255`, talking actor 13. This was not malformed authored dialogue, a
pad-release problem, or a camera-wait race.

## V152 hidden-owner dialogue contract

V152 emits F5 control flag `0x01` for every dialogue owned by hidden entity 13.
The native WAIT_DIALOG bypass bit prevents the hidden-owner OP_STOP while
retaining normal dialogue completion and cleanup. The complete set is 20 calls:

```text
PC 0x03F6 d20       PC 0x0434 d35 recovery
PC 0x044F d12       PC 0x049B d21
PC 0x04CC d22       PC 0x04FD d23
PC 0x052E d24       PC 0x055F d25
PC 0x0590 d26       PC 0x05C1 d27
PC 0x05F2 d28       PC 0x0623 d29
PC 0x0654 d30       PC 0x0685 d31
PC 0x06B6 d36       PC 0x06FE d32
PC 0x0706 d33       PC 0x070E d34
PC 0x0787 d35       PC 0x07B7 d11
```

This covers the completed response, recovery commit, prelude, dialogues 21
through 34 and 36, final commit, and locked response. The decoded verifier
requires all 20 flags to equal `0x01` and rejects any entity-13 F5 flag `0x00`.
No other controller or dialogue call changes, and the 4,998-byte authored
dialogue component remains byte-identical with SHA-256
`f9b38b8cef89b1b4b212a3eb41fb3d464beea71cdaa35777a33614f2b4f1a948`.

## Stable subjective camera

Hidden entity 19 remains Miang's physical point-of-view anchor at `(14,58)`,
direction 7, and is never shown. Every one of the 12 memory-eye operands is now
the authored ATEL `(x,z,y)` coordinate `(174,-102,-125)`: a `(+160,-160,-125)`
offset behind Miang along her gaze. Camera targets remain unchanged and no shot
targets Miang. Against the reaction, director, and officer targets, the new eye
provides approximately `2.79x` through `3.25x` the prior camera distance,
preventing the extreme close-up while retaining a subjective composition.

Only entities 17 and 18 render. Miang remains an offscreen voice labelled
`MIANG`; her hidden entity-19 anchor, physical position and facing cues remain
unchanged. The memory still clears actors and camera without launching. The
present-day Citan arrival continues to use its separate held camera.

## Byte-level Central Control identity

Target 728 canonical 2062 is 126,444 bytes with SHA-256
`3cb22422077995d06e35097fe943de5e6de9dc658fcbbe15d3c7f94b0e3035f9`.
Its decoded script is 3,482 bytes with SHA-256
`b6e7023c38a03801ae00cd15b326954127330a3da58d5216725e073e142a8eb5`.
Entity-13 action script 2 at PC `0x03DD` is 994 bytes with SHA-256
`3c48e815b5815bdbb6acf1b4afd74b581ed05779a61d538ce4859b54efe1cc23`.

The packed 1,088-byte header remains SHA-256
`cb5439aaa3b2bd00aa1fb103356f1fd7ff06c1de34c724eea1bed1b4193cd1db`;
the prepared header remains SHA-256
`b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31`.
The unchanged decoded components are:

```text
images:       4 bytes / df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119
walkmesh: 2,540 bytes / 6a1f335cd2cf00bcec7a5412b8ab7392fcff378912fd2857880d69f2186e6a14
models:  13,504 bytes / 9bb9ef16cb1f85b0c2a4052d79a710cb91224ea78be7f7b72c246ac6183ab24e
actors:  18,640 bytes / 2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538
sprites: 67,668 bytes / e09e0ca20423abd18fbbbee63c37b47e0d89c8a7a1cb32a61d54d37de452b805
encounters: 528 bytes / e88b412320050425ae87abad80b51749da8171b023e943604cf47a370535ab38
dialogue: 4,998 bytes / f9b38b8cef89b1b4b212a3eb41fb3d464beea71cdaa35777a33614f2b4f1a948
triggers:     0 bytes / e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

The V151-to-V152 decoded script delta is exactly 56 bytes: 20 F5 control bytes
change from `00` to `01`, and 36 operand bytes encode 12 replacement eyes.
There are no other script differences. Entity 13's 24-byte initializer remains
SHA-256 `181a80e903ce97b95af8b25c499265262879e1c5c680025446cefef371a92ba1`.
Citan stage script 21 remains SHA-256
`9a5aa669a5e137e3039f0e744cf0da4a926869f388d2e4a270a4140da5561cbc`;
walk script 22 remains
`00b90ce55c17beb780b028d81a1f61e40b2c955ce58887eba7b9b43f5d58728f`.

Citan is still hidden at `(225,104,0)`, direction 6, behind the native east
leaf. Scoped F8 `0x0038` covers only `(170,89)/32`, then clears before
`(100,89)/32`, `(60,84)/20`, and `(20,80)/20`; he settles direction 7. SHOW
still precedes native entity-15 script 4. The one 24-frame arrival camera
targets `(87,97,-72)` from `(87,-380,-170)` and stays held through world-map
unload. The native leaf remains visually open. Canonical 2063 graphics and
field 617 are byte-identical to V151.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v152.bin
size: 696,130,848 bytes / 295,974 raw sectors
SHA-256: 8dcb5e62607350832af926562a75dbb07b624ece41fd2edb7fee09d8b4b23cf4

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v152.cue
size: 107 bytes
SHA-256: 244144983c6e13c499122cf26eaeed59e62870de92567e0a7b959bd3d3865f65

manifest: work/mass_driver_v152_stage/manifest.json
size: 237,913 bytes
SHA-256: fe7d6b8ecc2bb1af358757090227c2e8d58d7c666c5d88b8e485ec193eff8f41
jobs / replacements / bytes: 136 / 169 / 11,804,532
route fields / directed edges: 33 / 66
replacement aggregate: 9542a7978bb3b0793939d305b0e9cc59275b4b81963def02575bc48ebc98683a
framed aggregate: f1ea7670fa5617d9538e83383c2a0ef9abbdbdfd205c7bc000e8479a57368ea0
```

## V151-to-V152 delta and validation

The declared stage and exhaustive complete-FAT payload deltas are both exactly
canonical 2062. All 4,147 FAT descriptor tuples, entry kinds and directory
memberships are unchanged; 3,722 of 3,723 extractable payloads remain
byte-identical. Exactly one raw sector changes, LBA 221,372. That sector has 56
changed user bytes and 250 changed raw bytes after valid MODE2/Form1 EDC/ECC
regeneration.

All 169 packaged replacements re-extracted byte-for-byte. All 5,846 replacement
sectors plus the boot sector passed MODE2/Form1 EDC/ECC validation. A second
complete stage and BIN rebuild reproduced the exact identities above. The five
structural verifiers and direct target-728 header, component, action, dialogue,
CFG/VM, F5, camera, Citan and field-617 invariance audits passed.

The authoritative V152 structural run passed 262 tests / 2,682 subtests in
20.391 seconds with exit 0 and zero failures, errors, subtest failures or skips.
Fresh user-driven acceptance of the repaired memory dialogue and camera, plus
the preserved Citan entrance, held arrival camera, launch and return, remains
pending.

The preferred focused state is
`work/runtime_capture/near_final_v152_from_v108_vault1.sav`, 1,701,665 bytes,
SHA-256
`882a1fa4090b5607b0574a08f64349d454a84edd3d04346b52e8c52278d55444`.
It mounts the exact V152 CUE. Historical V108 field 377 is resident; its FAT
table SHA-256 is
`d03a2a9168dbff1a76a3a939162c1784810763628cb374b6a5451ecc89155e07`
at payload offset `0x11A66` / RAM `+0x10004`. Flags are `0x0033`: bits 4 and 5
are set and bits 6, 7 and 12 are clear. Party bytes are `01 06 FF`; target 728
is absent and will cold-load from V152 media. Ask the player to navigate and
press controls; do not automate emulator input.

## Historical V151 boundary

V151's frozen center-console repair, package, runtime state and validation
record remains byte-for-byte in
[`mass-driver-dungeon-3.12.md`](mass-driver-dungeon-3.12.md). V152 changes only
the completion action's 20 entity-13 F5 controls and 12 subjective eye operands;
it does not rewrite that historical release record.
