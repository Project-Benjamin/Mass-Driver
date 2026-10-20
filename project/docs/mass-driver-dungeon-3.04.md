# Mass Driver Dungeon 3.04 - Guardian menu alignment and Ouroboros laboratory

V143 is the current frozen package. It fixes the Guardian-battle
command-menu exception and restores the dungeon's final capsule launch to the
exact retail Disc 1 field-507 Krelian/Ouroboros laboratory shown in
`lastroom.png`. It preserves V142's Defense Archive controller frontages,
V141's distinct interceptor head and three-cell exhaust, V140's compact
five-cell blasts and Missile-only sound `0x51`, the real-time worker scheduler,
single-center-base rules, field-363 station, and complete 35-field route.

The declared/staged V142-to-V143 replacement delta is exactly canonical IDs
29, 1620, and 1621. The complete FAT also changes generated bookkeeping
canonicals 17 and 22 because the rebuilt archive and disc layout move their
recorded locations; that is structural packaging metadata rather than added
gameplay content.

## Guardian command-menu alignment

Canonical 29 contains a 53-entry outer archive. The Video Disk item-name patch
expands outer entry 22 to a 2,469-byte logical payload. V142 rebuilt the archive
without an alignment byte, shifting later entry 38--the El-Regulus command-name
table--to odd offset `0x51A7`. The battle menu then passed an odd string address
to `GetStringEntry`, whose `lhu` raised an address-error exception and left the
emulated CPU in the exception loop seen during the Guardian fight.

V143 appends one zero alignment byte to entry 22. Its stored size is 2,470
bytes, and entry 38 now begins at even offset `0x51A8`. The item still displays
as `Video Disk`; no command name, deathblow rule, Guardian AI, battle model, or
battle animation is changed. Canonical 29 remains 13,596 bytes and now has
SHA-256
`b2feb89ac7031b5007aa137e2711ca0ab2f5b48efbe0d55ee040f98f81192816`.

## Exact retail field-507 final room

Logical target 507 again uses the exact retail Krelian/Ouroboros research
laboratory from Disc 1 field 507: Krelian's holographic apparatus stands beside
the restrained-Elly installation. This is an existing retail room and asset,
not a newly modeled chamber. V111's later field-595 private-laboratory
presentation remains preserved only as historical release evidence.

The route remains `728 <-> 388 <-> 507`. The red tunnel enters at `(486,48)`
on walkmesh 0 with camera 4 and inward facing 5. Native entity 4 and helper 24
form the reciprocal east laboratory door back to target 388. The final launch
controller is entity 7 at `(187,-250)` on walkmesh triangle 141, directly on
the holographic apparatus. It is no-facing with bound `0x10`, for 48 units of
effective reach. Native apparatus entity 10 script 4 runs before the released
Mass Driver world-map sequence. Completion bit 6 still prevents a second
payload; later use of entity 7 reports active atmospheric dispersal.

Target 507 canonical 1620 is 166,096 bytes with SHA-256
`8714fe87a28273c42167bd30c89a71a87e21dab0f2579f680e2e9e798297812b`.
Its 5,499-byte script has SHA-256
`2dca3f1da9115bede0010fd480ec88fe8de8e3207da143856d3123faa84bea68`;
its 1,643-byte authored dialogue has SHA-256
`0ffe294fd9f9904c85679e476ec9af4aee264798df31671a8fbe7cf7990130e2`.
Canonical 1621 is the exact 374,784-byte retail graphics resource with SHA-256
`f4b06ecad813330a5085afb4fa85d491c9b3e6ddd295e9ac6c410e891182f900`.

## Frozen V143 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v143.bin
size: 696,862,320 bytes
raw sectors: 296,285
SHA-256: 085be8ee0efef9c4b18385c861f52985a3d7ae6bf456c02b97d23a377eb0b320

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v143.cue
size: 107 bytes
SHA-256: ddf8b7d073163e1546ed2bcedf26514e30e43336e2e4d2491a921b6347dfe3a6

manifest: work/mass_driver_v143_stage/manifest.json
size: 241,523 bytes
SHA-256: 73984157c2d66e6fe1c8385c3bebc5fbfecde6af69a2fdc32bc8aceaa94c4241
jobs: 138
unique replacements: 173
replacement bytes: 12,446,596
replacement aggregate SHA-256: 5756166a92f5549d37d6dacefb0b3a3d59ad882e73ba6ac974b01b06ea0dac41
route fields: 35
directed edges: 70
```

All 173 declared payloads were extracted directly from the V143 BIN and
matched the stage byte-for-byte. All 6,161 raw sectors occupied by replacements
passed MODE2/Form1 EDC/ECC validation.

## Automated and runtime acceptance

The authoritative V143 full suite passed 258 tests / 3,322 subtests in 44.29
seconds without failures, errors, skips, or expected failures. Fresh user-driven
V143 runtime acceptance remains pending; it is not implied by the completed
package extraction audit or automated suite.

For the Guardian regression, cold-boot V143 or finish any battle with older
resident data and enter a new Guardian battle from V143 media. Open, cancel,
and reopen El-Regulus's command menu, then attack and confirm play continues.

For the final-room regression, completely leave target 507 before re-entering
from V143 media. Confirm the exact holographic Krelian/Ouroboros laboratory,
the safe inward arrival, the reciprocal native east door, launch dialogue only
at entity 7's apparatus frontage, the native entity-10 mechanism, one capsule
launch, and the later dispersal-status response. Ask the user to navigate and
press controls; do not automate the emulator.
