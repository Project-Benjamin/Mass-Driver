# Mass Driver Dungeon 3.14 - Wider console frontage and coherent memory

V153 is the current frozen package. It preserves V152's 33-field, 66-edge
route, subjective two-visible-actor Zeboim memory, native-east-door Citan
entrance, held arrival camera, local capsule launch, and guarded field-617
return. It changes only Central Control canonical 2062. Targets 388 and 507
and every Krelian-laboratory asset remain absent; target 728 remains the active
route's final room.

V153 fixes the second captured center-console dead zone and tightens the memory
sequence. Entity 13 moves to `(-48,97)` on triangle 16 and uses a no-facing
rectangular OP18 frontage with X/Z operands `0x1C/0x02`. Its effective region
is 72 units wide by 20 deep: inclusive X `[-120,24]`, Z `[77,117]`. Dialogue
12 and Emeralda's one present-day cue, dialogue 21, now finish before the fade,
party hide, and subjective camera. The remembered exchange contains only
dialogues 22 through 31 and 36, then restores the present under black without
the redundant post-memory dialogues 32 through 34.

## Captured second-position evidence

The authoritative user state is
`work/runtime_capture/user_v152_console_second_position.sav`, 1,884,059 bytes,
SHA-256
`d247400bb8a06745c834e9e760fe1a9c7994e8c51c5b1e5635cd07c41b420b1b`.
Its engine position is `(-113,113)` on triangle 15. The matching screenshot is
`work/duckstation/screenshots/Xenogears (Disc 2) 2026-08-10-20-12-47.png`,
2,028,365 bytes, SHA-256
`fae1ea2895c685ceb779a35ee80b7de5442ff088aa4da802166ca67a5f2b6ae7`.

The older V152 frontage was centered at `(-4,118)` with effective X/Z reach
`28x18`; it did not include the new user position. V153's shallow horizontal
strip accepts that stance, the earlier live `(-15,113)`/triangle-20 stance,
and both F2 readings `(-4,114)` and rounded `(-4,115)` on triangle 19. Because
entity 13 is no-facing, yaw does not create another dead zone.

The archive entity-12 region begins at X `25`, leaving an exact one-unit
coordinate gap after entity 13's maximum X `24`. Entity 14's east-door region
is also disjoint. The wider strip therefore covers the visible node-29/model-5
console bank without stealing the archive or door interactions.

## V153 interaction and memory choreography

Entity 13's first interaction keeps authorization bit 4 and the historical
memory-seen bit 12. Its ordered presentation is now:

1. Dialogue 12 and dialogue 21 play in the present, before any fade or hide.
2. The field fades and hides the party; entities 17 and 18 appear, while
   entity 19 remains hidden as Miang's point-of-view anchor.
3. A silent reaction shot establishes Elly's subjective sight.
4. The memory plays only dialogues 22-31 and 36. Miang remains an offscreen
   voice labelled `MIANG`.
5. After dialogue 36, the field fades to black, hides the memory actors, clears
   the memory grade, releases the camera under black, shows the party, fades
   in, and restores control.

Dialogues 32, 33, and 34 remain byte-identical in the authored dialogue archive
but are absent and unreachable from the action. There is no present-day camera
cut or repeated post-memory explanation. Dialogue 35 remains the later launch
commit on the second interaction.

The action owns exactly 17 F5 calls, all with control flag `0x01`:

```text
PC 0x03F6 d20       PC 0x0434 d35 recovery
PC 0x044F d12       PC 0x0457 d21
PC 0x04CF d22       PC 0x0500 d23
PC 0x0531 d24       PC 0x0562 d25
PC 0x0593 d26       PC 0x05C4 d27
PC 0x05F5 d28       PC 0x0626 d29
PC 0x0657 d30       PC 0x0688 d31
PC 0x06B9 d36       PC 0x0758 d35
PC 0x0788 d11
```

Dialogue 12 is at PC `0x044F` and dialogue 21 at `0x0457`, both before the
first fade at `0x045C`. The silent reaction begins at `0x046C`. Dialogue 36 is
followed by the second fade at `0x06BE`, actor hide at `0x06C4`, grade clear at
`0x06CA`, camera release at `0x06D8`, party show at `0x06E3`, and fade-in at
`0x06E9`. The action contains exactly one camera release.

All 12 subjective eyes remain the stable Miang-aligned ATEL `(x,z,y)` position
`(174,-102,-125)`. The silent reaction and every historical shot retain their
targets. Hidden entity 19 remains at `(14,58)`, direction 7; only entities 17
and 18 are visible. The authored dialogue JSON remains 9,451 bytes with SHA-256
`152cd76f4f77f203f6d6893f37c61064912306cd900484b25e4276802e77f192`.

## Byte-level Central Control identity

Target 728 canonical 2062 is 126,392 bytes with SHA-256
`9e5c5be2d6b858fb69375a7019224f2c253b0b7fb6aac955f2cb0d64175bb0c5`.
Its decoded script is 3,435 bytes with SHA-256
`bb34a0a6e652feef3a1f32bc422229a39c518cbef291e1a2eb9a7e8605747a73`.
Entity-13 action script 2 at PC `0x03DD` is 947 bytes with SHA-256
`ac24214ddc755d8e89f92be799a970f943ac2c7b4c1d5bc5bd1d9980e8c58f24`.

The 24-byte entity-13 initializer at PC `0x033E` has SHA-256
`16495b64a4f39fc843abf026726dddeb615e64412394a78b923100d60a7dcd46`
and exact bytes:

```text
BC 19 D0 FF 61 00 C0 F8 00 00 20 F8 07 04 00 18 1C 02 64 00 20 01 80 00
```

The prepared 1,088-byte header has SHA-256
`b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31`;
the packed header has SHA-256
`ca3430010f31aa89d01bdb1a1046b8d6e6a0468c11ed7486835cc3531b7f8ad5`.
The decoded components are:

```text
images:       4 bytes / df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119
walkmesh: 2,540 bytes / 6a1f335cd2cf00bcec7a5412b8ab7392fcff378912fd2857880d69f2186e6a14
models:  13,504 bytes / 9bb9ef16cb1f85b0c2a4052d79a710cb91224ea78be7f7b72c246ac6183ab24e
actors:  18,640 bytes / 2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538
sprites: 67,668 bytes / e09e0ca20423abd18fbbbee63c37b47e0d89c8a7a1cb32a61d54d37de452b805
script:   3,435 bytes / bb34a0a6e652feef3a1f32bc422229a39c518cbef291e1a2eb9a7e8605747a73
encounters: 528 bytes / e88b412320050425ae87abad80b51749da8171b023e943604cf47a370535ab38
dialogue: 4,998 bytes / f9b38b8cef89b1b4b212a3eb41fb3d464beea71cdaa35777a33614f2b4f1a948
triggers:     0 bytes / e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Citan's stage and walk scripts remain byte-identical, with SHA-256 values
`9a5aa669a5e137e3039f0e744cf0da4a926869f388d2e4a270a4140da5561cbc`
and `00b90ce55c17beb780b028d81a1f61e40b2c955ce58887eba7b9b43f5d58728f`.
He remains hidden at `(225,104)`, uses scoped F8 `0x0038` only for the first
bounded leg to `(170,89)/32`, then walks through `(100,89)/32`, `(60,84)/20`,
and `(20,80)/20`. SHOW still precedes native entity-15 script 4. The arrival
camera remains held through unload, the east leaf stays open, canonical 2063
graphics remain SHA-256
`4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28`,
and field 617 remains SHA-256
`d35a13ab5be99c4ebb6e3934bd4ab0c00613839d810c2a4984dae70adbdefb26`.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v153.bin
size: 696,130,848 bytes / 295,974 raw sectors
SHA-256: d5e50afa2f5288eeab63bf52a55f9d7167bbf48eef7bbead4fb5757dcff52b94

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v153.cue
size: 107 bytes
SHA-256: c01e5dca6c9a3ed6405e7ba7eb3951e973856dbb585c13e0c93397e016070766

manifest: work/mass_driver_v153_stage/manifest.json
size: 238,991 bytes
SHA-256: 5e7ee65fd047484fcb5d378a1991ede34e89f5bdeab2079804df3c980fa8c3e0
jobs / replacements / bytes: 136 / 169 / 11,804,480
route fields / directed edges: 33 / 66
replacement aggregate: 479f4359f1f6ff222abf959b176c8dea02ea6be63ba85119c886c71654a4fce5
framed aggregate: d64931dacb4e7d768d4a2bb3e66f7658cb3eaea4ddf98313eee43367dc9eda0a
```

## V152-to-V153 delta and validation

The declared stage delta is exactly canonical 2062. The exhaustive complete-
FAT payload delta is canonicals 17, 22, and 2062: canonicals 17 and 22 differ
only where their generated FAT mirrors record canonical 2062's size changing
from 126,444 to 126,392 bytes. Of 4,147 FAT descriptors, exactly canonical
2062/physical 2057 changes from `(sector 221314, size 126444, file)` to
`(sector 221314, size 126392, file)`. Entry kinds and all 61 directory tables
are unchanged; 3,720 of 3,723 extractable payloads are byte-identical.

Exactly nine raw sectors change: LBAs 31, 172926, 221314, and 221370 through
221375. The exhaustive delta contains 6,759 changed user bytes and 8,183
changed raw bytes after valid MODE2/Form1 regeneration. All 169 packaged
replacements re-extracted byte-for-byte. All 5,846 replacement sectors, the
two additional changed sectors, and the boot sector passed MODE2/Form1
EDC/ECC validation, 5,849 of 5,849 audited sectors. A deterministic second
stage and BIN rebuild reproduced every identity above.

The authoritative V153 structural run passed 262 tests / 2,689 subtests in
20.106 seconds with exit 0 and zero failures, errors, subtest failures, or
skips. Fresh user-driven acceptance of the widened console, coherent memory,
preserved Citan entrance, launch, and return remains pending.

The preferred focused state is
`work/runtime_capture/near_final_v153_from_v108_vault1.sav`, 1,701,665 bytes,
SHA-256
`f0277210b6cb45786bf4d7466740c17239647f21f645fd9b0080dd57d8032dac`.
It mounts the exact V153 CUE. Historical V108 field 377 is resident; target 728
is absent and will cold-load from V153 media. Its resident FAT SHA-256 is
`d03a2a9168dbff1a76a3a939162c1784810763628cb374b6a5451ecc89155e07`
at payload offset `0x11A66` / RAM `+0x10004`. Flags are `0x0033`, with bits 4
and 5 set and bits 6, 7, and 12 clear; party bytes are `01 06 FF`. Ask the
player to navigate and press controls; do not automate emulator input.

The stable V151 failure copy is
`work/runtime_capture/v151_hidden_controller_dialogue_abort.sav`, 1,752,967
bytes, SHA-256
`8bc81de760fda0ba5522c01b439a4aa152082bd8c48182e560c62f8747419717`.
It remains historical evidence only and cannot validate V153.

## Historical V152 boundary

Historical V152 release facts follow unchanged.

V152's frozen hidden-owner dialogue and camera repair, package, runtime state,
and validation record remains byte-for-byte in
[`mass-driver-dungeon-3.13.md`](mass-driver-dungeon-3.13.md). V153 changes only
canonical 2062's controller initializer and first-interaction choreography; it
does not rewrite that historical release record.
