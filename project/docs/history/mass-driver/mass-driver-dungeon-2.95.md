# Mass Driver Dungeon 2.95 - authentic service-junction terminal

V134 corrects the field-363 service-junction addition. The south-wall object is
not a newly invented room, door, or terminal. It reuses the exact retail
field-373 Zeboim computer already transplanted into target 727, including its
geometry, triangle order, texture atlas, and palette. The proposed field-365
control room and every route to it are absent.

The station is centered at `(0,-189)`, faces the playable aisle, and sits in
front of the original inert wall panel. Its solid body and its tight,
facing-gated reader are separate actors, so Cross works only from the front.
The reader opens one repeatable local record and writes no story state. A state
with field 363 already resident must completely leave and re-enter the room
from v134 media before this correction can be judged.

## Existing-asset proof

- Target-363 model 10 decodes to the same 165 triangles, geometry, and order as
  target-727 model 5. Only the field-local texture V coordinates and CLUT
  binding are rebased.
- In the frozen v134 package, the 5,120-byte atlas and 512-byte palette were
  copied byte-for-byte from the target-727 terminal. V135 supersedes that
  allocator choice: it keeps identical station geometry, triangle order, and
  sampled 16-bit colors through a lossless index remap, but does not claim
  byte-identical atlas indices or install a standalone 512-byte station row.
- Both revisions keep the field-363 MIM's original nine registered upload
  rectangles and file length. V135 additionally preserves native row 488,
  native models 0/1, and their door texture bytes exactly; see the
  [2.96 candidate notes](../../mass-driver-dungeon-2.96.md).
- The original south panel remains inert. There is no working south door, no
  target-365 clone, no field-365 arrival, and no field-363-to-365 transition.

## Missile Command arcade-authenticity pass

V134 retains v131's native field-script Missile Command arcade-authenticity
pass. The game has independently controlled and stocked batteries. Square
fires left, Cross fires center, and Circle fires right. Each battery owns one
ABM/fireball lifecycle, allowing three ABMs in flight together, while destroyed
attackers can seed three bounded secondary fireballs.

Incoming missiles select among six cities and all three batteries. A battery
hit loses its remaining ammunition, and every battery is rebuilt and rearmed
at the next wave. The ordinary-missile quota sequence is `12, 15, 18, 12, 16,
14, 17, 10, 13, 16, 19, 12, 14, 16, 18, 14, 17, 19, 22`; later waves retain
22.

An intercepted missile is worth 25 points, each surviving city 100, and each
unused ABM 5. All three values use the arcade multiplier from x1 through x6.
Every crossed 10,000-point threshold banks a reserve city. There is no wave-10
victory. Maximum pressure continues while the displayed and persisted best
wave caps at 31; zero cities after bonus-city deployment produces `THE END`.

Triangle pauses during play, Cross resumes, and Circle exits from the pause
screen. Signature `0x4E4C` stores the score in exact five-point units. On first
use, a valid `0x4E4B` record is decoded, converted losslessly, and repacked
without changing the shared Nuke score, level, pilot letters, or story state.

Run the focused Missile Command contract with:

```text
python -m pytest -q tests/test_build_mass_driver_dungeon.py -k missile_command
```

No live v131 emulator acceptance result is claimed; v131's static and package
results remain the historical baseline for this inherited game. Fresh v134
field-363 runtime acceptance passed after a complete user-driven room reload:
the authentic terminal rendered correctly, its front Cross interaction opened
dialogue, and no door transition occurred.

## Frozen v134 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v134.bin
BIN size: 696,711,792 bytes / 296,221 raw sectors
BIN SHA-256: 3e57ed1f5656820115cf5fe843e0869e2671ce9840c301ca378a578f122490fe

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v134.cue
CUE size: 107 bytes
CUE SHA-256: bc4906c0eee984d2f225658538707f9a0f6ee66d1f2776840b5cb97b836947ac

manifest: work/mass_driver_v134_stage/manifest.json
manifest size: 236,040 bytes
manifest SHA-256: 0e5e7525bd09e18d5e7b6f276088b24961421c6f3dc0e053c4214243d937b188
declared replacements: 173 across 138 jobs, totaling 12,316,324 bytes
```

All 173 declared replacements were re-extracted from the finished BIN and
matched the staged size and SHA-256 exactly. The complete automated suite
passes 257 tests. Broader v134 emulator regression coverage remains pending.

Relative to the rejected v133 package, only canonical 1332 (field 363) and
canonical 1333 (its graphics) change among declared payloads. Canonical 1332
changes from 20,316 bytes / `1ecd5abe56b0abf78ae62931e2b6afb3bc8bfe4e18b30ebc45d64c9ccdaa356b`
to 21,352 bytes / `1eeccea9de3a5636db2c4cfebf74a474ff5bc5f511b2ac1c1d19f66b158b87b9`.
Canonical 1333 remains 106,496 bytes and changes from
`0d561e4850c1ca2205d3e68e7886849412af053816be7c71c76d7f1a6ffc1965`
to `c6a3f288c071c211bcbef4b0b32ca2f4e082eaa0a73d92275dc615bb8292adfc`.
The job, replacement, route-field, and directed-edge counts remain
138 / 173 / 35 / 70.
