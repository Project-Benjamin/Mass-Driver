# Mass Driver Dungeon 2.96 - conservative field-363 station allocation

V135 is the frozen package that keeps v134's authentic field-373
Zeboim station, placement, collider, front reader, dialogue, and sealed south
wall. It changes only the station's field-363 texture/palette allocation.

After v134's initial terminal visual and interaction replay passed, the user
reported a gray transition/backdrop while entering field 363. The audited
field-721-to-363 transition is unchanged between v133 and v134: it remains the
retail mode-0, 32-frame fade-to-black. No field-363 transition opcode or fade
parameter changed, so the report does not establish the palette allocation as
the cause. V135 nevertheless removes the remaining native-door remap as a
conservative hardware, filtering, and transient-load precaution.

## Allocation proof

- The 5,120-byte 80-by-64 station atlas samples 192 palette indices. Native
  field-363 model 3 is the only existing row-485 user and samples 28 indices,
  leaving 228 proven-free slots. A deterministic one-to-one station mapping
  uses 192 of them and leaves 36 spare.
- Each used station palette word is copied unchanged into its mapped row-485
  slot. The resolved 16-bit color of all 5,120 station texels, including PS1
  transparency and semitransparency bits, is therefore exact.
- Only the station's single CLUT command is retargeted to `0x7940`. Its two
  texture pages, UV geometry, 165 triangles, triangle order, placement, and
  model size remain unchanged.
- Native row 488 remains byte-identical. Native models 0 and 1 and their
  complete 1,118-byte door texture footprint remain byte-identical. Native
  row-485 colors at all 28 sampled indices also remain byte-identical.
- The MIM remains 106,496 bytes with the same nine upload rectangles. Outside
  the station atlas carrier and the newly occupied, previously unused row-485
  entries, its reconstructed word-addressed VRAM is exact.

The station atlas index bytes are deliberately remapped, so they are not
byte-identical to target 727. There is no complete standalone 512-byte station
palette row in field 363; visual identity is the exact geometry/order plus the
exact sampled 16-bit colors produced by the lossless mapping.

## Field-363 identities

These deterministic prepared-source identities were re-extracted unchanged
from the final package:

```text
field 363 bundle: 21,352 bytes
SHA-256: bc450a6117ebd3e4dc60eb6bc0a39c4175ebac77dbbcf193c384dd9829937c3b

field 363 header: 832 bytes
SHA-256: c5dd92f8b149eee4e8287b622d0cd70c730c82eb796115dc0642464d2df6a182

field 363 models: 9,904 bytes
SHA-256: b756da8c20274bf8a6c3c136eafe63c73a830566b0c9aaefb56c5bf7db4f9d20

field 363 script: 1,995 bytes
SHA-256: 1d11ad410628d1d7e1e64a5885144f8529171188cb6e626bafcc2e79af688f30

field 363 graphics: 106,496 bytes
SHA-256: 0f90479813717a6aa250691ec85f02b2c3fb009aed9adbab003212a80bda2561
```

The v135 source stage prepared cleanly. Its 236,056-byte manifest has SHA-256
`f841abf690eb47557ab003931c256c69544b03503ebc48faa1816619f02b6afb`
and declares 138 jobs, 173 unique replacements, 12,316,324 replacement bytes,
35 fields, and 70 directed edges. Relative to v134, only canonicals 1332 and
1333 change among declared payloads.

## Frozen v135 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v135.bin
BIN size: 696,711,792 bytes
BIN raw sectors: 296,221
BIN SHA-256: f124100fc5fec53d9d82ed7e9efb5cedca919a161ae437099f44e6b846d4491b

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v135.cue
CUE size: 107 bytes
CUE SHA-256: d66eca6a83ec53c9d32243b098d8a56b591dd658244c1d0f0692677083b6c70a

manifest: work/mass_driver_v135_stage/manifest.json
manifest size: 236,056 bytes
manifest SHA-256: f841abf690eb47557ab003931c256c69544b03503ebc48faa1816619f02b6afb
```

All 173 unique declared replacements were extracted directly from the final
BIN and matched the staged payloads byte-for-byte, totaling 12,316,324 bytes.
Relative to v134, only canonicals 1332 and 1333 changed; their sizes remain
21,352 and 106,496 bytes respectively. Static tests and package validation
pass. Fresh v135 emulator acceptance remains pending: ask the player to reload
field 363 from v135 media and navigate and interact manually. V134's earlier
terminal interaction acceptance and later gray-backdrop report remain
historical evidence, not v135 runtime acceptance.
