# Mass Driver Dungeon 3.19 — V158 solid east-wall console

V158 keeps the frozen 33-field, 66-edge route and the continuous Central
Control finale, while moving the compact retail field-361 keypad to the user's
newest captured east-wall marker and giving it solid collision. The target-728
story controller, memory sequence, automatic Citan arrival, dialogue 35,
keypad-operation routine, launch, and guarded field-617 return remain intact.

## Console placement and ownership

Retail field 361 model 5 remains losslessly relocated as target model 11.
Passive static node 43 now has exact record
`10 00 00 00 00 08 00 00 C5 00 B7 01 6C 00 0B 00`, anchor
`(197,439,108)`, and yaw `0x0800`. Its world AABB is X `133..174`, Y
`-61..0`, Z `153..190`, centering the base at `(153.5,171.5)` beside the
captured Elly marker `(153.731155,171.069839)`, triangle 24. Model and graphics
bytes remain the frozen V157 values: model 11 is 360 bytes with SHA-256
`7177eada7ba59ea9a442661702a6d8dbe32924550d9e2a69ca74fe91f368078b`;
canonical 2063 is 180,224 bytes with SHA-256
`201c89767211545e039422ab8791b48ff5a22f3f5383c4d0b234387a3c25aef7`.

Retired hidden entity 16 is appended after every V157 routine as a solid-only,
immovable contact carrier at `(154,171)`, triangle 24. Its collision operand is
`0x0B`, raw radius 22, and effective player-contact radius 38. It has no X
action and writes no progression state. Entity 12 alone owns the optional
interaction at `(136,131)`, triangle 26. Its no-facing OP18 operands
`0x01/0x01` retain raw extent `2x2`, effective reach `18x18`, and inclusive
player-centre region X `[118,154]`, Z `[113,149]`.

Dialogue 1 is now a repeatable, state-neutral, single-page Elly observation:

```text
<Elly>
"This console looks out of
place among the other
computer terminals..."<Close>
```

No Emeralda line, mail record, treasure behavior, or progression write is
attached to the relocated console. The broad entity-13 story frontage remains
at `(-48,97)`, triangle 16, no-facing OP18 `0x1C/0x02`, effective `72x20`.

## Citan route and operation camera

Citan still stages hidden at `(225,104)`, triangle 32, behind the native east
leaf. The direct connected-floor route is now:

```text
(170,89), max 32  -> triangles 32/27/28
(160,110), max 32 -> triangles 28/29
(136,131), max 20 -> triangles 29/26
```

He ends on triangle 26, direction 0. Dense walkmesh checks prove the complete
chords, the last endpoint remains outside the solid console body, and the
static model needs no walkmesh edit. Citan and Elly retain reciprocal facing
for dialogue 35. After that dialogue closes, the already-held camera
interpolates for 12 frames to target `(145,160,-45)` from eye
`(170,-80,-135)`. This inside-room shot has no static front-facing ray blocker.
One blocking entity-3 script-23 call then performs the frozen field-378 keypad
animation, three sound-`0xF9` calls, and waits `25/35/24` before its finite
STOP; only afterward are completion and world-map launch committed.

## Frozen package

The official image is
`output/Xenogears_PW_CD2_mass_driver_standalone_v158.bin`, 696,130,848 bytes
(295,974 sectors), SHA-256
`5b2b5aecd15c9aaf4bbcb7a3e555c391a22148f7645fc42fba53d4ad775accd4`.
Its 107-byte CUE has SHA-256
`8f205b83f6e0232a6ea3fdda39027cd4728024b2305cd37a269f3d06b93c2955`.
The 249,070-byte manifest has SHA-256
`c01792fae7de6ab3bdcdf214c2b16e30dca7101ebc31a92e45ad021bb56ffe7f`.
It records 136 jobs, 169 replacements, 11,804,468 replacement bytes, 33
fields, and 66 edges. Canonical-order payload and framed aggregates are
`ca18e714f9b02f5467ac7bdaf42b2567578088bf987ed84073e31233e2fd7130`
and `bed7f0270c73c209920d27eaea389e750b89c878a40a9ce04933af2f0d2b953e`.

The declared V157-to-V158 stage delta is canonical 2062 only. The exhaustive
FAT payload delta is 17, 22, and 2062. Exactly one of 4,147 descriptors changes:
canonical 2062 remains at LBA 221314 and changes size from 126,840 to 126,380;
there are no relocations. The FAT changes by two bytes. All 3,720 other
extractable payloads, all 61 directory tables, canonical 3722, canonical 3723,
and every later LBA remain unchanged. Direct extraction passed 169/169. All
5,846 replacement sectors and the 5,849-sector audited union including the nine
logical-delta sectors and boot pass MODE2/Form1 EDC/ECC. A second complete
stage, manifest, and BIN rebuild matched byte-for-byte.

Canonical 2062 is 126,380 bytes with SHA-256
`3ed0527021cc4d09ef8e6297dd335e09f435018dd305299dcf200ae3c8f1210c`.
Its prepared and packed headers are 1,104 bytes with SHA-256
`9a2f2fb373a52b3d64e865db3356b67bbaa3fa977129aa5703d32ab646f80c52`
and `fb7dd25da1ff29aedaae013a1aaa057d3efccb816dbde46cb8dafd819ae8d6e9`.
The 3,593-byte script has SHA-256
`39f7a1cf08cbe8721ac39fa471a29b69a9e5ca1a944948c88cbd0f6bda73c020`;
the 1,053-byte entity-13 action has SHA-256
`41e90c56f716d18b670e26e28204a0309be3d811dd4a5e0d651a5bc168cebfdf`;
the appended 31-byte entity-16 body has SHA-256
`5c4d5eb5c599b119653ac90a6746eee799f1dc71a2ff15e5e4f4eafff43e97df`.

The preferred focused state is
`work/runtime_capture/near_final_v158_from_v108_vault1.sav`, 1,701,664 bytes,
SHA-256
`5be101fd30f7f6c1bcec66b363ca82e5f7cf5cccb7dbac232801648dfdd6f301`.
It mounts the exact V158 CUE once, has historical V108 field 377 resident,
target 728 absent, FAT SHA-256
`5a8bbb4ca9333f427b0674c18e7f1ebde55ac7c4d76c332acd968c8657459af6`,
flags `0x0033`, and party bytes `01 06 FF`. Walk north so Central Control loads
fresh from V158.

The authoritative V158 release run passed 262 tests, 2,693 successful
subtests, 20.844 seconds, exit 0, with zero failures, errors, failed subtests,
skips, expected failures, or unexpected successes. Fresh user-driven V158 console,
collision, remark, route, operation, launch, and return acceptance remains
pending.

Historical V157 release facts are preserved unchanged in
[the V157 compact-keypad notes](mass-driver-dungeon-3.18.md).
