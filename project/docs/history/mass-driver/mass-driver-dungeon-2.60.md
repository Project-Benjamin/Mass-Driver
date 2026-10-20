# Mass Driver v83 terminal-controller accessibility repair

V83 fixes the remaining mismatch between visible computers and their invisible
interaction controllers. In target 361, Guidance Archive entity 12 moves from
the donor pivot `(17,190)` to `(-31,165)`, aligned with the hanging screen's
reachable walkmesh approach. Auxiliary Grid entity 13 remains at `(110,117)`.
Their archive and switch responsibilities are unchanged.

Both target-361 controllers now clear the facing-only flag and encode
interaction-bound operand `0x1E`. The same no-facing `0x1E` operand is applied
to both readable computers in source-378 lore rooms 365, 366, 369, 370, 371,
and 724: desk entity 13 at `(45,-42)` retains dialogue 1, while hanging entity
14 at `(-89,90)` retains dialogue 0. Railway target 368 keeps entity 13 as the
rail switch and entity 14 as mail, but both controllers now use the same
no-facing operand. Target 367's source-382 lift-service archive keeps mail
entity 18 at `(0,45)` and makes it no-facing as well.

`0x1E` is the encoded controller-bound operand, not a claim of a literal
30-world-unit half-width. Noah shifts these opcode `0x18` bound operands left
once before applying the engine's additional actor radius.

No dialogue ownership or progression role changes in v83. Auxiliary entity 12
still owns Directive 0320 and clue bit 2; entity 13 still owns Auxiliary power
bit 0. Railway entity 13 remains the sole accelerator-bit writer. Every lore
mail action remains repeatable and progression-free, and v82's Zeboim
vertical-lift archive and native return remain intact.

The changed canonical field bundles are:

| Field | Canonical | Bundle bytes and SHA-256 | Script bytes and SHA-256 |
| --- | ---: | --- | --- |
| 361 | 1328 | 89,784 — `aa62f48d5617445d11cd235915ece12b07b5b8e11d1429e33ad2073097ade26c` | 2,135 — `21223942e0e375a02e181c837f52d5eb85def4613438a366032c508f2814bc0d` |
| 365 | 1336 | 53,156 — `48dab97dc98ee4b53f591fcb90737fa92da0236f4a5bc8c56caea1908c974397` | 2,848 — `619dbde29937d9efad7094e53106cd9601ad09adfbe0f1770a49fa135f5fb169` |
| 366 | 1338 | 53,364 — `e9283b25eda786c56e8daec9ab9737436651dd5cc17442966e7d78fb5f5ad6e0` | 2,848 — `54cc964885c4a022861d0d52d1d3a5525c0ec69b941918621d0c59a134f5cab3` |
| 367 | 1340 | 29,216 — `d7e81ccab64186a3edd8132b999b4918e414b37e9f6e15cdd60280ffe8d4133a` | 1,835 — `42fd9706f0ca70dc15eb3e517ff5e5d8bf1bb65c2e146a68cb87ef73644917de` |
| 368 | 1342 | 52,996 — `079e39f3f395031d11181bec86c4e884bb2d97ac431bc7d8034687d06f540b49` | 2,857 — `416d252549fe2b7a44f369f3f61c041df62eaf8597f90f00cea0e4ca58b4a6d1` |
| 369 | 1344 | 53,384 — `69834f481d3f33f1143570edf5f1a03cf7b742faaf8db452e4fcd95b33238f1f` | 2,848 — `56ab8433a8d7c6a1cb6f6c5871dd16c2cd8857b9ee9731e293abb44b61a65350` |
| 370 | 1346 | 53,384 — `798e3e73f7663bc1a604787f4d11bf2d35f8a1689022a293af3f2f1ed6ee82ac` | 2,848 — `4e4a723d8b79ad9c7026df0e3b4403d2cebf1d450dbd726ff3737fc90ca111df` |
| 371 | 1348 | 53,552 — `6cd15166bd3c256ca48a72ccc60a5495677ee4c21b4691cd606ec7627225cca7` | 2,848 — `066f96ab1b72768affbad83e3adff951583062e1f91bb27e4a7ebe1ab910faab` |
| 724 | 2054 | 53,616 — `a267dd84f343b2947c453d0aa7174cc8877de8c98850ffbed2d67d82ed76e56c` | 2,848 — `75f5e0af39f7e9525ed6adcac9834fb9b4fe7606d382f214cf084e050242dad7` |

The packaged v83 artifacts are:

- BIN: 695,291,184 bytes,
  `a5352e79566acf9a6f49b37fdcaa36afb633f38f2952493e65a6dd1afba7cd83`
- CUE: 106 bytes,
  `aa6f4b24ed101face03440b7ddf8a30ec4fed2327ea305c46b9223b0241965de`
- Manifest: 185,646 bytes,
  `683fe1a937263f5bf17eefef0260fa8a6d6c4331d6d84ba3feab416dd16455b6`
- Manifest contents: 126 jobs and 158 declared replacements totaling
  10,390,715 bytes, with canonical-ID-order aggregate SHA-256
  `09028f5746b88720bea4d54e1016ac0091518f546fb29058c8482bd35bfcd53f`

The August 1 06:41 DuckStation capture is useful evidence: its embedded image
shows target 361 from the south, with Elly facing the hanging Guidance Archive
screen and the Auxiliary console farther right. The state mounts v82, however,
and restores a resident v82 target-361 script. It cannot validate v83 merely by
selecting the newer CUE before loading. Cold boot v83 and enter normally; at
minimum, leave the resident room and re-enter it from v83 media before testing.

The final automated suite passes 202 tests and 2,325 subtests with no failures,
errors, or skips. Cold-boot runtime acceptance remains pending.
