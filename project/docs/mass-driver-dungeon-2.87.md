# Mass Driver v110 Defense Archive terminal alignment

V110 tightens the interaction regions in target 376, the Defense Archive
code-entry room. Every visible console, controller center, dialogue owner,
walkmesh assignment, and facing policy remains in place. The smaller regions
remove empty-aisle activation and make the authorization station, six record
readers, and north lift mutually distinct.

## Exact controller policy

The engine doubles each encoded horizontal bound and includes the player's
16-unit extent. An operand of `0x04` therefore gives 24 units of effective
reach per axis; `0x18` gives 64 units.

| Role | Entity | Center | Facing | Operand | Effective reach |
| --- | ---: | ---: | --- | ---: | ---: |
| Directive 0320 / ABCD authorization | 13 | `(175, 123)` | required | `0x04` | 24 |
| East record, dialogue 16 | 20 | `(350, 175)` | not required | `0x04` | 24 |
| Southeast record, dialogue 17 | 21 | `(115, -94)` | not required | `0x04` | 24 |
| South-center record, dialogue 18 | 22 | `(-132, -40)` | not required | `0x04` | 24 |
| Southwest record / west-panel logic, dialogue 19 | 23 | `(-406, -94)` | not required | `0x04` | 24 |
| Northwest record, dialogue 20 | 24 | `(-406, 225)` | not required | `0x04` | 24 |
| North-center record, dialogue 21 | 25 | `(-220, 66)` | not required | `0x04` | 24 |
| North lift | 17 | `(0, 245)` | not required | `0x18` | 64 |

Authorization still requires Directive `0320` followed by A-2, B-5, C-8,
and D-4. The six records remain repeatable and write no progression. Entity 23
still owns the Guardian-gated west-bulkhead panel sequence, and entity 17 still
requires authorization before entering target 384.

The retired empty-aisle stance `(-30, 141)` now selects no interaction. The
authorization, record, and lift regions are pairwise disjoint; the lift no
longer reaches the center aisle.

## Runtime proof

Target 376 was completely reloaded from v110 media. The actor base changed to
the fresh v110 field script rather than retaining a resident v109 script.
Pressing Cross at approximately `(-11.93, 127.34)` on walkmesh triangle 70
produced no dialogue. This directly confirms that the tested center-aisle
position is no longer an invisible terminal hotspot.

Three positive probes on that same fresh load confirm that the smaller regions
remain usable at their visible controls:

- At approximately `(171.77, 104.97)` on triangle 213, physically in front of
  the visible two-seat wall console, Cross opened the `AUTHORIZATION TERMINAL`
  workflow owned by entity 13.
- At approximately `(6.81, 254.94)` on triangle 73, Cross opened entity 17's
  `DEFENSE BAY LIFT / ACCESS LOCKED` workflow.
- At approximately `(-218.13, 54.99)` on triangle 197, Cross at the
  north-center desk opened entity 25's dialogue 21,
  `EXECUTIVE ROUTING AUDIT`.

A state saved with target 376 resident on v109 or earlier media cannot validate
this correction: DuckStation restores the old resident field script and its
old interaction operands. Cold-boot v110, or completely leave target 376 and
re-enter it from v110 media before testing.

## Exact v109-to-v110 delta

Only canonical 1358, target 376's field bundle, changes:

| Controller | v109 policy | v110 policy |
| --- | --- | --- |
| Authorization entity 13 | Facing required; operands `0x28` by `0x14`, effective reach 96 by 56 | Facing required; operand `0x04`, effective reach 24 per axis |
| Record entities 20-25 | No facing; operand `0x0C`, effective reach 40 per axis | No facing; operand `0x04`, effective reach 24 per axis |
| North-lift entity 17 | No facing; operand `0x40`, effective reach 144 per axis | No facing; operand `0x18`, effective reach 64 per axis |

| Resource | v109 | v110 |
| --- | --- | --- |
| Canonical 1358 bundle | 135,248 bytes, `50dc8ea328caa5a0d8bf17b05a2cd53d459376457dc7963b35b1192d9d8b0048` | 135,276 bytes, `3d67cce05c269280393e96bb4776934b275248b173d44f8fb862ad6c6c419ad7` |
| Decoded script | 4,284 bytes, `e6eae048cca84580d91cc5342d0ac6a85539b3749347091502bda765fc08158d` | 4,308 bytes, `38790a5f6cc4745ce0f434761571df2ba9d52e63048ba7dface38790619c6442` |

Among the decoded field streams, only the script changes. The prepared
1,072-byte, 42-record header remains
`29055284994bc48db466e0f63bbc9d76e722c48354c442cd2d56b41d25385eb9`;
images, walkmesh, models, actors, sprites, encounters, dialogue, and triggers
are byte-identical. The fixed bundle stream directory changes only as required
by the larger packed script. Canonical 1359 graphics remains 239,616 bytes with
SHA-256
`969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd`.
The other 165 declared payloads are byte-identical to v109.

## Packaged v110 identities

- BIN: 696,561,264 bytes, 296,157 raw sectors, SHA-256
  `7aa6020bf6b0dd72f96e29802d4d3c0601cf2a60d2c0786fe8588df5d5e95fd6`.
- CUE: 107 bytes, SHA-256
  `d310517cb15cbfe2b5fcd888e66d15e05775a54f17cd1cd7d83e3a46b3af83bf`.
- Manifest: 210,069 bytes, SHA-256
  `1d6593e9971b439bbfb2841c31caa39d0fed25e44bfa8e995473f697f2011e28`.
- Declared replacements: 166 across 130 jobs, totaling 11,505,876 bytes;
  canonical-ID-order aggregate SHA-256
  `13410685fa094105499697f9b66a619eb4dcbad46bc61960e177c11a20a59ca4`.
- Complete automated validation: 225 tests and 2,882 subtests passed with no
  failures, errors, or skips.

The superseded v109 subway-station change and its complete packaged identities
remain documented in
[the v109 release notes](mass-driver-dungeon-2.86.md).

## Cold-load acceptance

1. Fully quit DuckStation, launch
   `output/Xenogears_PW_CD2_mass_driver_standalone_v110.cue`, choose New Game,
   and load no older F1 state or in-game save.
2. Enter target 376 and confirm `(-30, 141)` and the tested triangle-70 center
   aisle produce no dialogue when Cross is pressed.
3. Confirm the northeast authorization station still accepts the complete
   five-part code and rejects incorrect entries.
4. Press Cross at each of the other six physical banks and confirm dialogues
   16 through 21 remain individually repeatable.
5. Confirm the authorized north lift opens visibly and remains usable without
   intercepting either the authorization station or a record reader.
6. After Guardian victory, confirm entity 23 alone opens the west bulkhead and
   its historical record remains readable.
