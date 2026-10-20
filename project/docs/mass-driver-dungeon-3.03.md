# Mass Driver Dungeon 3.03 - Defense Archive controller frontage

V142 is the frozen package for the Defense Archive operator-side interaction
correction. It preserves V141's distinct foreground-only interceptor head and
three hot/bright/dim exhaust cells, V140's compact five-cell explosions and
Missile-only retail explosion sound `0x51`, V139's bounded incoming tails, the
real-time worker scheduler, safe `(640,384)` arcade atlas, single-center-base
rules, field-363 station, and complete 35-field route.

The V141-to-V142 delta across both the declared replacements and the complete
Xenogears FAT is exactly canonical 1358. Canonical 1359 field graphics,
canonical 2475, canonical 2476's 8,212-byte arcade atlas, every model resource,
and all Missile Command workers and actions are byte-identical to V141.

## Operator-side interaction

The Defense Archive's authorization, record, arcade/video, and Video Disk
controllers now use the native facing gate. Their controller initializer
contains exact bytes `F8 03 04 00`. Authorization entity 13 and entities 21
through 26 use bound operand `0x04`, giving 24 units of effective reach. The
long east-bank record reader on entity 20 retains operand `0x24` and 88 units
of effective reach, but now requires facing as well.

Dialogue-21 reader entity 25 moves from the old controller at `(-220,66)` to
the visible northwest console's operator side at `(-260,105)`. The accepted
user marker is `(-260.214,92.209)`, yaw `0x0C00`, on walkmesh triangle 196.
The rejected empty-floor marker is `(-221.548,55.813)`, yaw `0x0800`, on
walkmesh triangle 197. It is outside the corrected interaction bounds and must
remain silent.

This release changes controller frontage only. The authorization and archive
dialogue actions, arcade/video root and submenu actions, Video Disk pickup and
playback actions, every Missile Command worker and action, all models, and all
graphics resources remain unchanged.

## Frozen V142 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v142.bin
size: 696,709,440 bytes
raw sectors: 296,220
SHA-256: 1e16bffd110c048c6c40085a176536cab5cb4b76541dd7f42974c582a3adfbdd

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v142.cue
size: 107 bytes
SHA-256: 0fb2e62fe4030d12d78db45969b28b0417d294493553284a7c48edd9a17edb8a

manifest: work/mass_driver_v142_stage/manifest.json
size: 241,290 bytes
SHA-256: cc66f4fc59e7f86bb3c1e422c246710a158a05e165e33d0bf6fb3a00f088ce42
jobs: 138
unique replacements: 173
replacement bytes: 12,314,508
route fields: 35
directed edges: 70
```

Target 376 canonical 1358 is 190,452 bytes with SHA-256
`5e2996b1c7f9d2bce2b8e3e30d3b2e1ff8f6116125dbbe3f29b2bb0b9a849514`.
Its prepared header is 1,104 bytes with 44 records and SHA-256
`62e0fd0d2b4512971a0ee1d81e06547adc0bba55fc29249dc33210de10bd4daf`.
Its 1,104-byte packed header has SHA-256
`f1d54532db4bdcbcda53ee2583fbe4a0e95de684bd012a2aca02cdb79a2f0897`.
Its 48,943-byte script contains 47,019 bytes of bytecode and has SHA-256
`daee4fdd6ee9cf7e127d28a6c6e613aea4100190b3c269ef9cc5491c155927da`.

Worker script-1 entry PCs remain e16 `0x5EA0`, e17 `0x5FCC`, e18 `0x600A`,
e19 `0x6048`, e20 `0x6086`, e22 `0x60C1`, e23 `0x60FC`, e24 `0x6137`,
e25 `0x65BE`, e26 `0x6737`, and e27 `0x678E`. The 28 cycle boosters,
904-cycle soft budget, maximum call depth of three, and audited V141 worker
maxima are unchanged.

## Validation and reload

All 173 declared payloads were extracted directly from the final V142 BIN and
matched the stage byte-for-byte. The authoritative V142 full suite passed
257 tests / 3280 subtests in 41.10s. Fresh user-driven V142 runtime acceptance
also remains pending.

V141's authoritative result of 257 tests and 3,286 subtests remains historical
evidence only. Its exact package identities, extraction evidence, worker
maxima, and pending runtime status remain frozen in
[the V141 release notes](mass-driver-dungeon-3.02.md); V140 and older records
remain unchanged in their own release notes.

Fully mount the V142 CUE, completely leave target 376, and re-enter it so its
resident script is reloaded. Face each visible operator console before pressing
Cross/X. Verify entity 13 and entities 21 through 26 respond only from their
tight front-side regions, entity 20 retains its longer east-bank reach while
requiring facing, the accepted dialogue-21 marker selects entity 25, and the
rejected empty-floor marker stays silent. Then replay authorization, all five
records, both menu levels, Back, Leave, Video Disk pickup and playback, Nuke,
and the complete Missile Command loop. Ask the user to navigate and press
controls; do not automate the emulator.
