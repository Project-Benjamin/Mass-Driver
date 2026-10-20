# Mass Driver Dungeon 3.21 - V160 west-bulkhead panel frontage repair

V160 preserves V159's 33-field, 66-edge route, repaired Defense Archive north
lift, five reserve magazines, Central Control finale, and all authored
progression. It changes only the Cross/X selection frontage on Defense Archive
entity 23: after the Guardian victory, the west-bank terminal can now be used
across the complete walkable face of its visible panel instead of through a
very small facing-dependent window.

## Live V159 evidence

The user's V159 save is `output/SLUS-00669_1.sav`, 1,842,614 bytes with
SHA-256
`8e84ed934352124b807291fc71404c087b851f93f1f3faa73d5c1cc5565550db`.
The associated screenshot is
`%LOCALAPPDATA%/DuckStation/screenshots/Xenogears (Disc 2) 2026-08-12-19-09-36.png`,
619,100 bytes with SHA-256
`77c8bd680cbc2b75e197be09ee1120354c0c44745f5c64d9de094b30bea5f5af`.

The live leader position was
`(x=-474.812835693359, z=-160.151718140625)`, yaw `0x0C00`, on connected
walkmesh triangle 177. This is a valid operator stance directly in front of
the west control bank. V159 nevertheless gave entity 23 the same tight
facing-gated `0x04` square used by the ordinary record readers. Its effective
reach was only 24 units per axis and its facing cone made selection depend on
aiming at one invisible pivot.

The Guardian-victory prerequisite was not the problem. Entity 23's existing
action already checks progression variable `0x03FE` bit 5, shows locked
dialogue 10 before victory, and after victory owns dialogue 19, the fixed
camera, sound `0x77`, both sliding helpers, and persistent bulkhead-open bit
`0x03FA:2`.

## V160 interaction contract

Entity 23 remains anchored at `(-465,-161)` and its action script remains
byte-identical. V160 changes only two initializer bytes at field-script offsets
48,490 and 48,494:

```text
V159: facing mode 0x03, square operand 0x04
V160: no-facing mode 0x07, X operand 0x20, Z operand 0x04
```

The resulting OP18 rectangle has effective reach 80 units in X and 24 units in
Z. Its selectable region is X `[-545,-385]`, Z `[-185,-137]`, which covers the
audited walkable panel frontage X `[-485,-425]` and includes the exact live
stance. Keeping the Z depth shallow prevents the widened control from reaching
across the room. The panel region remains disjoint from entity 14's west-door
transition and every other console, disk, authorization, and north-lift
controller.

The V160 entity-23 initializer is still at PC `0xB5DA`; its 24-byte body has
SHA-256
`1b119dc578b70a03b6a5ba0f3ebe6cf7221a9f75b7d3f29d82bf8f1334502e7a`.
Entity 23 action PC `0xB5F2` is unchanged from V159, with SHA-256
`053f0de057f96eb4e73dc4c4321704039bfb3f271d99cd3a47aeec9affbb1aa1`.
No dialogue, progression bit, camera, sound, door animation, walkmesh, model,
actor, sprite, encounter, image, or trigger changes are part of this repair.

## Current package

These are the frozen V160 build identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v160.bin
size: 696,130,848 bytes (295,974 raw sectors)
SHA-256: 8f37d9ddf3487abbd599ca2daaef10ed17006ef054107fcd36ab71197709f7d0

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v160.cue
size: 107 bytes
SHA-256: 051d53cc064e25b37dd5497e62f3fda4788d5a2080b0b0092256b2b89d61f6a9

manifest: work/mass_driver_v160_stage/manifest.json
size: 251,375 bytes
SHA-256: c77dd76e5dff304fbb348a71dc9269cc01f87bc3f3b0651d8efb5891d1b46cf3
jobs / replacements / bytes: 136 / 169 / 11,804,460
route: 33 fields / 66 directed edges
canonical-order payload SHA-256: 06ad32f3a4296ae642eb2ce8a597dce3a00385c6a8a87da239d52dc520689e3b
canonical-ID/size/payload SHA-256: dedc1fc799dd7d092b8d2832770b4c185d33915b0084e10a19527b107d483b5b

canonical 1358 / target 376 size: 190,444 bytes
canonical 1358 SHA-256: 3badf3f1718522e5c798954017a96d104cb75713f4becf4eeeaa932b22350bd9
field 376 script size: 48,930 bytes (47,006-byte bytecode)
field 376 script SHA-256: bdbcfacf464841df93ba2a415aea03559273f715298e6ad98a189c29cfb3bcbc

builder size: 1,394,401 bytes
builder SHA-256: f7843d91f344936d3b6fd884538a440bfcaf3a58dcf7281b92c1df5df356d3b1
```

The V159-to-V160 staged and exhaustive gameplay delta is canonical 1358 only.
All 169 packaged replacements extract exactly. All 4,147 FAT descriptors,
including start sectors, sizes, and kinds, are byte-identical; zero files
relocate, all 61 directory tables match, and 3,722 of 3,723 extractable files
are unchanged. The FAT SHA-256 remains
`b790e09f5d9d35ffb379ccf561f2f817826f8af8c7ccc9b57e9f873fa3c9ea59`.

Exactly one of 295,974 raw sectors changes: LBA 196167. Its user data changes
by two bytes and its regenerated raw sector by 46 bytes; the other 295,973 raw
sectors are byte-identical. The changed-sector before/after raw SHA-256 values
are
`44c29a8c4804683e1cac1f5dd6166ae1a2e7c234a9fbc953c7bf151366eef6cd`
and
`a0bb60d6b223dfe54f3254d2a2a505aff3704d612c631cfd6206858f69e3f6fe`;
the corresponding user-data hashes are
`c1fa5f62a4b8e37bbd32f55177aec051022a0a05cb004517730e7a50c2f6069a`
and
`b96df2b3408d9544c572f7f7ae79464f9a23dea4e148e4524dff3fe6dff81989`.
All 5,846 replacement sectors pass Mode2/Form1 EDC/ECC validation. An
independent build from the checked source disc and xenoiso reproduces both the
BIN and manifest byte-for-byte. Focused structural validation passes. The
authoritative suite passes 262 tests / 2,707 successful subtests in 22.097
seconds with exit 0 and every failure counter at zero. The one-file installer
passes static PE/manifest/import/resource/hash/path-leak inspection with only
the expected unsigned warning. Its dynamic offline audit passes exact positive
patching, launcher creation and recovery, existing-build reuse, wrong-size
exit 11, wrong-hash exit 12, output collision exit 30, corrupt-patch exit 21,
sentinel/source preservation, and residue cleanup. The stable version-1.6.0.0
Play launcher is 446,464 bytes with SHA-256
`1cb8141cef86662157e1fc76e78370b8fab99bed45d2f89a88455e63a5004df0`.
The installer executable hash is deliberately not pinned here because it is
rebuilt after these release notes are embedded.

Fresh user-driven runtime acceptance is also pending. A V159 save with target
376 already resident retains the old tight initializer even after the V160 CUE
is mounted. To retest the captured progression safely, mount V160, completely
leave target 376, and re-enter it before approaching the west-bank panel. After
the Guardian victory, stand anywhere along the visible front of the panel and
press Cross/X. Confirm dialogue 19 appears, the camera and sound play, both
leaves open, the route into field 377 works, and the open state survives a room
reload. Also confirm the panel remains locked before victory and that the
nearby door and other consoles still select only their own actions.

Historical V159 package and validation facts remain unchanged in
[the V159 north-lift notes](mass-driver-dungeon-3.20.md).
