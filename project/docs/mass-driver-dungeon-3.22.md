# Mass Driver Dungeon 3.22 - V161 Guardian music and El-Regulus refacing

V161 preserves V160's 33-field, 66-edge route, repaired Defense Archive
controls, five reserve magazines, Central Control finale, and all authored
progression. It changes only the target-384 Guardian battle handoff and
El-Regulus's shared post-action recovery: the fixed battle now selects the
normal Xenogears battle theme, and El-Regulus reacquires its formation target
after returning home so an attack cannot leave her Gear facing away from the
Guardian.

## Live V160 evidence

The user's in-battle V160 state is `output/SLUS-00669_1.sav`, 1,969,689 bytes
with SHA-256
`fdb1ae2803d5d70894bc10364fa03274e545f9dc5f2dc0bd7e620fd614431e65`.
The associated screenshot is
`%LOCALAPPDATA%/DuckStation/screenshots/Xenogears (Disc 2) 2026-08-12-20-10-05.png`,
1,104,018 bytes with SHA-256
`ec7cb8b0011efaa0295b082130aa17241384961ff9865dbb84bf8cfeb5d58792`.
It captures El-Regulus and Crescens fighting the Guardian in target 384's
Goliath Factory arena.

The resident El-Regulus root is at `(1720,0,1640)` with yaw `0x0C00`; the
Guardian is due west at `(1040,0,1640)`, whose correct target yaw is `0x0400`.
The failure appears after El-Regulus attacks: her target bit still identifies
the Guardian, but shared post-action animation 4 returns to her own home point
and never reacquires the formation target before the next command menu.

V160 also enters the fixed battle with the field music still active. Target
384 initializes the Goliath Factory hall with field-music ID `0x18`, and its
Guardian routine went directly from a 15-tick wait to `FE 84 0F 80` without
requesting a battle sequence. The battle engine therefore inherited the
resident field-music instance.

## V161 music contract

Immediately before the Guardian's fixed-battle opcode, V161 emits:

```text
75 14 80 FE 84 0F 80
```

Opcode `0x75` passes its operand unchanged to the field music loader. The
loader reads sequence `music_id * 2 + 0x14`, so `0x14` is the exact script and
sequence ID; it is not converted to `0x1D`. Noah's lookup has
`musicLookupTable[0x14] = {0x14,0}` while entry `0x1D` is `{0xFF,0}`.

This choice is independently retail-proven. Retail field 388 contains
`75 14 80 FE 84 0C ...` at raw script offset `0x0AFB`, and retail field 627
contains `75 14 80 FE 84 0F ...` at `0x1ABC`. Both explicitly select `0x14`
immediately before a fixed boss battle. Retail field 335 instead uses
`75 3F 80 FE 84 0B ...` for its special boss cue, confirming that the operand
is deliberately selected per encounter. No audited fixed-battle script uses
`0x1D` in this position. The normal battle theme is commonly called
"Stage of Death" and appears as "Deadly Dance" in Square Enix's current
English soundtrack listing; the release contract intentionally pins the
unambiguous game ID `0x14`.

Canonical 1374 remains 162,324 bytes. Its field-script component grows from
21,202 to 21,205 bytes, and ATEL bytecode grows from 19,278 to 19,281 bytes.
The three new bytes begin at raw script offset `0x5299`; the original
`FE 84 0F 80` moves from `0x5299` to `0x529C`. Checked branch destinations and
the later shared script pointers are relocated by the same three bytes. No
dialogue, encounter, model, actor, sprite, walkmesh, image, trigger, or field
graphics component changes.

Victory already reloads target 384 parameter 0. That normal field initializer
selects hall music ID `0x18` again, so the ambient track restores through the
existing same-field return rather than through a new post-battle special case.

## V161 facing contract

V160 canonical 2960 animation 4 contained one return-home handoff:

```text
4A FD 5B 02
```

V161 inserts the same native formation-target pair used by the entry animation
and audited peer player Gears:

```text
4A FD 60 00 43 00 5B 02
```

Opcode `0x60` reacquires El-Regulus's formation-slot midpoint, and opcode
`0x43` faces that nonzero target. The insertion begins after `4A FD` at archive
offset `0x735E`. Because animation 4 is the shared recovery reached after
actions, the one repair covers Triangle, Square, X, and deathblows without
duplicating facing packets inside every attack.

Animation 4 grows from 84 to 88 bytes and has SHA-256
`420fb39fa55df38c3a123ad61a04c35ecc27836e2de9d3961774f00d76bdf518`.
Canonical 2960 grows from 33,604 to 33,608 bytes, and its outer roots change
from `(2,0x10,0x7FF8,0x8344)` to `(2,0x10,0x7FFC,0x8348)`. The model root
remains below the strict `0x8000` boundary. Animation 0's existing native
entry-facing and idle handoff, every attack and deathblow, every other
animation, and the model/sound container remain unchanged.

## Current package

These are the audited V161 build identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v161.bin
size: 696,130,848 bytes (295,974 raw sectors)
SHA-256: b010fcb46946e5e1595d7225652bd78f04b91e97a5b6dce0cc8cf0675ed49bf4

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v161.cue
size: 107 bytes
SHA-256: 06149bd106fdd02fe1baacbae6b07b001411bb4ecfb6cc501efd199ea0379561

manifest: work/mass_driver_v161_stage/manifest.json
size: 252,161 bytes
SHA-256: 7b3a65389d7b557e52d94c353e717eb951e0afd4b05d4fd591a8e082754e6d8a
jobs / replacements / bytes: 136 / 169 / 11,804,464
route: 33 fields / 66 directed edges
canonical-order payload SHA-256: 1cebbdb3bbdc7a46ac4c86b7dabbd787bdb20813786eb1e87993145dd1112b7f
canonical-ID/size/payload SHA-256: de4dae7ab4f33a3081595b55ed51783f2728af833b25f3f9ecfb72fa99fb0d86

canonical 1374 / target 384 size: 162,324 bytes
canonical 1374 SHA-256: 3f294aacbf4a5fd1fc535015042364b7ce5a6a925547bc061906aee3edc57ba7
field 384 script size: 21,205 bytes (19,281-byte bytecode)
field 384 script SHA-256: a0f485a0e7537ff90754baacf1c5dbb62eab5922f84778b51cc3d3575bbae315

canonical 2960 size: 33,608 bytes
canonical 2960 SHA-256: 78eee071519dc5ee3cbbf5ca0080c69923580b6443b3e48e9759db451b6da46c

builder size: 1,399,262 bytes
builder SHA-256: 2a2559bdb602e437d163d9e97f2c838fb64cc29cc04120ddcb200d9264069077
```

The declared V160-to-V161 gameplay delta is canonicals 1374 and 2960. Direct
final-BIN extraction matches all 169 staged replacements exactly. The
exhaustive payload delta is canonicals 17, 22, 1374, and 2960: canonicals 17
and 22 carry the regenerated filesystem/control reflection of canonical
2960's four-byte size increase, while the two declared gameplay resources are
the only authored changes.

All 4,147 FAT entries and 61 directory tables were compared. Canonical 2960's
descriptor alone changes size, from 33,604 to 33,608 bytes; no start sector,
entry kind, directory membership, or payload allocation moves. The FAT changes
by one byte, from SHA-256
`b790e09f5d9d35ffb379ccf561f2f817826f8af8c7ccc9b57e9f873fa3c9ea59`
to
`2df83b480464ba290277b305e60da3b1a4967ad3073fc11c813a33f04d11d190`.

Ten of 295,974 raw sectors differ, at LBA 34, 172929, 197074,
197140-197141, 197152, 244670, and 244684-244686. The changed-sector raw
before/after SHA-256 values are
`804b93e33af80c78078bb1b5bbcfecdc9543204ac455666782edea57789fc41f`
and
`929025a808d19f3f06f3c3856f2711e389829721a25fbb19158a8145434b8b14`;
4,867 raw bytes differ. Their user-data before/after hashes are
`31a34e5bd3aa2ad8f00a2a85cff85a8b14865a36bbe990ded3a538e47a28ee97`
and
`d6d99ec475a1291bb264d8386273658f8d6056a04e6457509093b776a333f5b3`;
3,414 user bytes differ. All 5,846 replacement sectors and the 5,849-sector
union that includes every changed sector and the boot sector pass
Mode2/Form1 EDC/ECC validation.

An isolated repeat build matched all 550 stage files plus the manifest, BIN,
and CUE byte-for-byte; a short staging path was required by the legacy path
limit. Static and dynamic V161 installer QA also pass. The generated Play
launcher is version `1.6.1.0`, 446,464 bytes, with SHA-256
`7001509183bcc90986fbee68450cb33a8ae171134ecd7a85dde528162910f0c9`.
The installer EXE identity remains deliberately unpinned because rebuilding
documentation resources changes that container without changing the tested
payload contract.

The authoritative instrumented suite passes 262 tests and 2,706 successful
subtests in 20.355 seconds with exit 0. It records zero failed subtests,
failures, errors, skips, expected failures, or unexpected successes. Fresh
user-driven runtime acceptance remains pending; it is not represented as a
pass.

## Runtime acceptance still required

The captured state is useful failure evidence but cannot validate V161: loading
it restores V160 media, the resident V160 target-384 field script, the old
canonical 2960 animation, and the already running battle. Mount V161 and enter
a completely new Guardian battle from V161 media; a disc change inside the
old battle is insufficient.

In the fresh battle, confirm the normal battle theme begins as combat starts.
At every returned command menu, El-Regulus must face the Guardian after at
least Triangle, Square, X, one Level-1 deathblow, and one higher deathblow. In
the captured due-west layout, the expected El-Regulus root yaw is `0x0400`,
not `0x0C00`. Crescens and the Guardian must remain unchanged. After victory,
confirm the Goliath Factory hall ambience returns on the same-field reload.
Ask the player to choose actions and press controls; do not automate emulator
navigation.

Historical V160 package and validation facts remain unchanged in
[the V160 west-panel frontage notes](mass-driver-dungeon-3.21.md).
