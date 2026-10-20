# Mass Driver Dungeon 3.08 - compact final computer room

V147 is the current frozen package. It replaces target 507's large historical
laboratory presentation with the exact compact retail Disc 1 field-573 Krelian
computer room. The donor's small square shell, walkmesh, six static nodes, model
bank, actors, sprites, encounters, and graphics are retained wholesale. Physical
files 1752 and 1753 are the authoritative donor sources; they are installed as
target canonicals 1620 and 1621.

The room's six native static nodes are 11 through 16. The centered computer bank
is baked into opaque node 11 / model 1 and light-pass node 15 / model 5, so V147
does not import an apparatus, add a background, or transplant any field-507
geometry. The final room therefore contains the compact shell, its centered
control panels, the party, Citan during the finale, and the native northeast
door.

## Interaction and finale contract

Invisible facing-gated entity 7 owns the launch interaction at `(120,0)` on
walkmesh triangle 9. Bound operand `0x04` gives 24-unit effective reach. Entry
from target 388 places the party at `(295,295)` on walkmesh 0 with camera and
actor direction 5. Native entities 4 and 5 retain the finite northeast-door
return to target 388; the native crossing waypoint is `(365,365)`.

The active party remains Elly on entity 1 and Emeralda on entity 2. Citan uses
entity 3, stages at `(365,365)`, and follows the bounded waypoints
`(280,180,320)`, `(200,80,256)`, and `(180,-60,256)`. His arrival camera targets
`(240,140,-48)` from `(450,400,-420)` over 18 frames. The conversation camera
targets the console at `(120,0,-48)` from `(430,-310,-380)` over 18 frames.

The field-573 computer bank has no finite native apparatus animation suitable
for the launch. Entity 10 script 4 instead plays its native computer tone
`0xF9`, holds for 30 field frames, fades for 12 frames, and stops before the
world-map launch. This bounded beat cannot restart the donor's retired puzzle
director. The complete entity-7 finale action remains 340 bytes and owns Citan's
arrival, all four dialogue blocks, the completion write, launch, repeat status,
and guarded return.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v147.bin
size: 696,387,216 bytes / 296,083 raw sectors
SHA-256: 63fd1ceafee04c0346acddb27a9df0724f07e5587de608e6c6dc56cfb4eb0881

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v147.cue
size: 107 bytes
SHA-256: 6e00bd12d06042f3bf3d8a983d6d44b6241763287767c6773ff14ad5aaba4f55

manifest: work/mass_driver_v147_stage/manifest.json
size: 242,543 bytes
SHA-256: 0d6f9cc688916817f267d4fc0c656e6cb0f85583f0af3abf4e2b962370a795b0
jobs / replacements / bytes: 138 / 173 / 12,034,636
route fields / directed edges: 35 / 70
replacement aggregate: 92bf2aec3d943a096359f09e88e0ce76e0d96ea0a8a6f7f88fc5b361c6ff7096
framed aggregate: 139b1dc35af938680ab4012a620c31bf7e80dbaf010918b9394cec9ab2c8af40
```

Target 507 canonical 1620 is 68,540 bytes with SHA-256
`5a292fd2df08bff7af3bcb3c243748bb9f92a18ad2e469a4931d64b1b4364c97`.
Its prepared header is 672 bytes with SHA-256
`e49f9573e08e6b8d475bf9185dd79e843fad1ba75ef1f9c5e5fa60440846ed9d`;
the packed 672-byte header has SHA-256
`84f3ac2103a741855ce4f6dbc0c35e5c09935e84f0dd32f5196bdb0c9a1b8ec5`.
Its 2,405-byte script has SHA-256
`7e089ce88febe68ffa51709476a9e2eb4f0ab9cbb36baf9e21b6227b569dd51a`,
and its 1,643-byte dialogue has SHA-256
`0ffe294fd9f9904c85679e476ec9af4aee264798df31671a8fbe7cf7990130e2`.
Canonical 1621 is the exact 141,312-byte field-573 graphics payload with SHA-256
`c253c815b126a9527851057d9279b9646fed0ea982fde359d389020178f9d9d6`.

## V146-to-V147 delta and validation

The declared staged delta is exactly canonicals 1620 and 1621. The exhaustive
FAT payload delta is exactly 17, 22, 1620, and 1621; 17 and 22 are regenerated
FAT bookkeeping. Of 3,723 extractable payloads, 3,719 are byte-identical.

There are 2,361 changed FAT descriptor tuples: canonical 1620 resizes,
canonical 1621 moves and resizes, then 2,328 later files and 31 metadata aliases
shift backward by 162 sectors. Entry kinds and directory membership are
unchanged. All 173 packaged replacements re-extracted byte-for-byte, all
5,959 replacement sectors and the boot sector passed MODE2/Form1 validation,
and the exhaustive FAT audit passed.

The authoritative V147 suite passed 262 tests / 3,326 subtests in 43.82 seconds
with exit 0. Fresh user-driven runtime acceptance remains pending. The focused
state `work/runtime_capture/guardian_v147_authorization_console_compact_finale.sav`
has exact V147 media and archive-table identity, does not have field 507
resident, and can replay the route into a fresh compact room. It is diagnostic
finale coverage, not a substitute for cold-boot whole-release acceptance. Ask
the user to navigate and press controls; do not automate emulator input.
