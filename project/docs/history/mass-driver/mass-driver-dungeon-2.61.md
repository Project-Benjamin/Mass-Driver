# Mass Driver v84 Guidance Archive interaction-bound correction

V84 narrows only the Guidance Archive interaction in target 361. Entity 12
remains centered at `(-31,165)`, remains no-facing, keeps dialogue 0 and clue
bit 2, and changes only its opcode `0x18` interaction-bound operand from
`0x1E` to `0x08`. Auxiliary Grid entity 13 remains at `(110,117)`, remains
no-facing, keeps switch/status dialogue 1 and Auxiliary bit 0, and retains
operand `0x1E`.

The operands are encoded values, not literal world-unit half-widths. Noah
doubles entity 12's `0x08` operand to runtime X/Z extent 16. The player has
extent 16, so the corrected effective per-axis interaction reach is 32. This
still covers the audited Guidance Archive walkmesh points `(-57,161)` and
`(1,166)`, but rejects the unintended saved floor point
`(-39.700211,96.628967)` because it lies 68.371033 units south of the
controller center.

The August 1 07:23 DuckStation slot-1 state documents the v83 behavior. Its
256-by-192 thumbnail shows Elly at that south floor point with the Guidance
Archive mail already open. The state mounts v83 and contains the resident v83
target-361 script, whose `0x1E` operand becomes runtime extent 60; combined
with the player's extent, its effective per-axis reach was 76. Loading that
state cannot validate v84's resident script. Cold boot v84, or at minimum
leave the room and re-enter it from v84 media.

Only target field 361 / canonical 1328 differs from v83. Its dialogue is
byte-identical; every other declared replacement, terminal position, terminal
role, and interaction operand is preserved. In particular, target-361 entity
13 and all retained source-378, Railway, and lift-service terminal controllers
remain no-facing at operand `0x1E`.

The changed field evidence is:

| Field | Canonical | Bundle bytes and SHA-256 | Script bytes and SHA-256 | Dialogue bytes and SHA-256 |
| --- | ---: | --- | --- | --- |
| 361 | 1328 | 89,784 — `56e795e9bd9b0eb72f1ee42810fbeff0d0b92db51f9baea5c94185a4ca141fc2` | 2,135 — `f28d44fc3074db9849713b65b172fec35462ef1f369112c13f120b7fcd19da7a` | 1,390 — `969a9b40deef2189f804ec8aae109efcffdb4f6b62003244753484413a1d504f` |

The packaged v84 artifacts are:

- BIN: 695,291,184 bytes,
  `013bcbef26724893a350ccc3b37edda11a078ccff72cc91a3f55e66ddcbd124e`
- CUE: 106 bytes,
  `51bec94c44e7f582ed7c385853905a62ae0a1d77aff815072ba4edf7cc5b5c79`
- Manifest: 185,744 bytes,
  `06724f266c3ea2f5a5e65c4469b582b74b5b2951e34547fa894d854f7153579c`
- Manifest contents: 126 jobs and 158 declared replacements totaling
  10,390,715 bytes, with canonical-ID-order aggregate SHA-256
  `297ad8d985d3057ef7008192ede3cc6b3e40f6075e39b7ccf1ca461b5d2bbe4f`

The final automated suite passes 202 tests and 2,334 subtests with no failures,
errors, or skips. Cold-boot runtime acceptance remains pending. The superseded
v83 artifacts and broader no-facing terminal rollout remain documented in
[the v83 terminal-access notes](mass-driver-dungeon-2.60.md).
