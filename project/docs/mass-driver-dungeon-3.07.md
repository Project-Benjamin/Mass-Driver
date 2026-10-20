# Mass Driver Dungeon 3.07 - Krelian laboratory finale relocation

V146 is the current frozen package. It removes the historical apparition and
Citan-arrival sequence from Central Control and makes the exact retail
field-507 Krelian/Ouroboros laboratory the sole finale room. Citan first
appears there, the complete capsule dialogue occurs there, the native
apparatus animates there, and Taura's nanomachine capsule launches there.

This remains a canon-conscious fan reconstruction. It is not recovered or
official deleted Xenogears content.

## Central Control handoff

Target 728 entity 13 remains the required route console at `(-54,94)`, but its
authorized action now gives one brief neutral instruction and transfers the
party directly to target 388 parameter 1. The already-completed compatibility
path gives the repeat guidance and makes the same transfer.

The active Central Control action contains no historical apparition, camera
scene, Citan actor or party mutation, arrival-bit work, launch-completion
write, apparatus call, or world-map opcode. It neither checks nor writes the
retired afterimage bit 12 or Citan-arrival bit 7. Field 388 remains the silent,
reciprocal red service tunnel between Central Control and the final laboratory.

Canonical 2062 is now 46,952 bytes with SHA-256
`6dc4ae2b720b81ff3afc224e3471bab591235fd269c6f8f505dcebad758926c3`.
Its 2,233-byte script has SHA-256
`9d13d94f49bddfcbd4f1ce458737655ea3a1afe9260d52420ff21fadc26d0772`.
Entity 13 script 2 begins at PC `0x0362`, is 104 bytes long, and has SHA-256
`c833f972eca4ce8c4d4cbb06ebc0ca34877bc21e8ec72c3957e32deaeb1ff6b4`.
Canonical 2063 cleanly returns to the donor's unused-ghost-free 180,224-byte
graphics payload with SHA-256
`4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28`.

The complete V145 apparition implementation remains frozen as historical
evidence in the V145 stage, tests, metadata, and 3.06 release note. It is not
reachable in V146.

## Field-507 finale

Invisible controller entity 19 is centered at `(191,-522)`, strictly inside
walkmesh triangle 1 and directly in front of the visible model-16 workstation
component. It requires facing and uses bound operand `0x04`, giving 24 units of
effective player-center reach. The live marker stance `(191,-503)`, yaw
`0x0400`, is 19 units away: target yaw is exactly `0x0400`, yaw error is zero,
and the interaction has a five-unit proximity margin. The marker evidence is
`work/runtime_capture/finale_v145_krelian_terminal_marker_latest.sav`, SHA-256
`b020de8e395223b2be13a4ab3ec214d430e9efeaab05869731adb552d727f8c3`.
That capture proves placement only; it is not V146 runtime acceptance.

Authorization bit 4 is the only story prerequisite. Bit 7 is retained only as
a compatibility and recovery marker: if an old state already has it, the
controller skips the entrance but still ensures Citan is available. Otherwise
the same field-507 action stages Citan hidden at `(580,145)`, plays sound
`0x77`, runs native east-door helper entity 24 script 4, and walks him along
three bounded legs:

- `(70,-183)`, bound 704
- `(23,-390)`, bound 320
- `(150,-540)`, bound 320

The arrival camera uses target `(325,-198,6)`, eye `(325,689,-506)`, and a
24-frame transition. The conversation camera uses target `(112,-531,6)`, eye
`(112,356,-506)`, and an 18-frame transition. Citan faces the party leader,
bit 7 is set, and Citan is added only after the connected-floor walk. Dialogue
blocks 1 and 3 then play in the laboratory, native apparatus entity 10 script
4 runs, completion bit 6 is set, and the retained retail world-map launch and
guarded field-617 return restore Elly and Emeralda with temporary Citan
removed. Repeat use reports active dispersal and cannot launch another payload.

Canonical 1620 is 166,368 bytes with SHA-256
`a28d753a2ad7ac07cb014805fc3ca09207723b1d0f0357552641f9e4a4d95f26`.
Its 5,743-byte script has SHA-256
`2956fa72af66bd172c83fb40b58330a9f8ea04ddf603122ee5050e2fcd1212f5`.
Entity 19 script 0 begins at PC `0x0DB9`, is 25 bytes long, and has SHA-256
`bbf1eb262e63426976b64685196172eede8edef566de4ae9c305542855696e48`.
The complete entity-19 script-2 finale remains at PC `0x0E00`, is 340 bytes
long, and has SHA-256
`55da192e072f632c9266e34f8b20bcca9e65513936c6ae0b18cbe607a651e872`.
Canonical 1621 remains byte-identical at 374,784 bytes with SHA-256
`f4b06ecad813330a5085afb4fa85d491c9b3e6ddd295e9ac6c410e891182f900`.

## Frozen V146 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v146.bin
BIN size: 696,768,240 bytes
BIN raw sectors: 296,245
BIN SHA-256: 47d4ef0586189e4489f4ef2a7b0e6f870024c4b050b87a8ccf1e44b5d9f1fb71

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v146.cue
CUE size: 107 bytes
CUE SHA-256: 4e6f116b42c848d39d2513e7c4fcac76f4cc03b605a712771c5e7d050ed88192

manifest: work/mass_driver_v146_stage/manifest.json
manifest size: 242,367 bytes
manifest SHA-256: f3de56cf394ebe39505a9c80afde7ef9713bd280c1363d4d048b55cda5355712
jobs: 138
declared replacements: 173
declared replacement bytes: 12,365,936
route fields: 35
directed edges: 70
replacement aggregate SHA-256: e407aae53977230c59fbb41673bc40f7b72e1b3dfb07b1fbf2ce0f4189bcb926
framed aggregate SHA-256: b9489e0bee7537782919147f597528393082d30efce30aa7c3841d3ce99c3fc5
```

The declared V145-to-V146 stage delta is exactly canonical IDs 1620, 2062,
and 2063. The exhaustive FAT payload delta is exactly canonicals 17, 22, 1620,
2062, and 2063; 17 and 22 are regenerated FAT bookkeeping payloads, not added
gameplay content. Of 3,723 extractable payloads, 3,718 remain byte-identical.

Both FATs contain exactly 4,147 entries: 3,723 extractable files, 378 empty
entries, and 46 metadata entries. No ID, kind, or directory membership changes.
There are 1,920 changed descriptor tuples: canonical 1620 remains at sector
203014 and grows by 272 bytes; canonical 2062 remains at sector 221624 and
shrinks by 15,396 bytes; canonical 2063 moves from sector 221655 to 221647 and
shrinks from 245,760 to 180,224 bytes; the 1,917 later nonempty descriptors
shift backward by 40 sectors with sizes and kinds unchanged. All 173 declared
payloads re-extracted from the final BIN exactly, and all 6,121 replacement
sectors plus the boot sector passed MODE2/Form1 validation.

The authoritative V146 full suite passed 263 tests / 3,375 subtests in 49.10
seconds with exit 0. Fresh user-driven V146 Central-Control handoff, field-507 entrance,
dialogue, apparatus, launch, repeat, and guarded-return acceptance also remains
pending. Ask the user to navigate and press controls; do not automate emulator
navigation.
