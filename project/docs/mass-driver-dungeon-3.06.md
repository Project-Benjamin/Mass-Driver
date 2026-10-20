# Mass Driver Dungeon 3.06 - Krelian laboratory workstation restoration

V145 is the current frozen package. It restores the complete native
workstation presentation around the final capsule-launch apparatus in the exact
retail field-507 Krelian/Ouroboros laboratory while keeping the standalone
launch route and native mechanism choreography.

The declared/staged and exhaustive complete-FAT V144-to-V145 payload deltas are
both exactly canonical 1620. Canonical 1621 graphics and all other payloads
remain byte-identical to V144. All 4,147 FAT descriptor tuples are identical;
3,723 extractable payloads were hashed on both discs and 3,722 are unchanged.
The only changed raw user-data LBAs are 203014 and 203090 through 203093.

## Restored workstation and launch frontage

Native workstation base entity 10 is visible at y=`0`. Entities 11 through 16
restore the six native holographic panels, and entity 7 restores the native
model-16 workstation component. These are the retail field-507 presentation,
not replacement art or a new asset transplant.

Launch input is separated from the visible models. Invisible controller entity
19 is centered at `(187,-250)` on walkmesh triangle 141, requires facing, and
has 48 units of effective reach. It gates the standalone capsule launch while
the unchanged native entity-10 script-4 action performs the apparatus sequence.
The reciprocal east laboratory door, safe arrival, Krelian/Ouroboros room art,
and V144's Guardian and Defense Archive corrections remain unchanged.

Ask the user to navigate and press controls; do not automate the emulator.

## Frozen V145 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v145.bin
size: 696,862,320 bytes (296,285 raw sectors)
SHA-256: 47967238893931325d5209a1f7fb3e04ac7f64b2f96af3d642c2f392bf460a00

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v145.cue
size: 107 bytes
SHA-256: 748cac8a5b2e4ecedbc6cba8381464b32d876d0c8c27bb05816924eadadf9997

manifest: work/mass_driver_v145_stage/manifest.json
size: 242,068 bytes
SHA-256: 2b050f3987b7bb4a9fea1e7facf24ab4a6620ec5a938dfb3e4448ba1d3f589f3
jobs: 138
unique replacements: 173
replacement bytes: 12,446,596
route: 35 fields / 70 directed edges
replacement aggregate SHA-256: 0b38f9ebb7e3b974c74e4c1d7f6c300220d746872d7b891039008a56eb9662e4
framed aggregate SHA-256: a3f8c1f6c3751fc0e48f5b30a4c27628e647167e12a6f285a3aafe1a252b5c87

canonical 1620 size: 166,096 bytes
canonical 1620 SHA-256: 52cd716c936725c1fb7cd4003b79432bbeae261af0bfe726d859f2c2626c695b
script size: 5,500 bytes
script bytecode: 3,768 bytes / 25 entities
script SHA-256: 32a729aa5bd3bfce3266e9150e858903ce60c05cf7689f2358ae017d14cfdc31
prepared header size: 1,104 bytes
prepared header SHA-256: 947be8203a4308ac58c1d20377a2bc35f4ce29298d2afadd35041410b05716f4
packed header size: 1,104 bytes
packed header SHA-256: dc3372557cbc896d9f0d4c933d882cbe5117fe87dd8a10f68e1fc74ae71d010c

canonical 1621 size: 374,784 bytes
canonical 1621 SHA-256: f4b06ecad813330a5085afb4fa85d491c9b3e6ddd295e9ac6c410e891182f900
```

All 173 declared payloads were extracted directly from the V145 BIN and matched
the stage byte-for-byte. All 6,161 replacement sectors and the boot sector
passed MODE2/Form1 EDC/ECC validation. The authoritative V145 full suite passed
263 tests / 3,384 subtests in 59.24 seconds without failures, errors, skips, or
expected failures. Fresh user-driven V145 runtime acceptance remains pending and
is not implied by the completed build, extraction, and automated-suite checks.
