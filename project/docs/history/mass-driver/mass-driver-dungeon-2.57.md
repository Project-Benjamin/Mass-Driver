# Mass Driver v80 adjacent-Gear encounter

V80 replaces target 384's two distant Gear interactions and later midpoint
trigger with one readable encounter composition. The July 31 DuckStation
thumbnail showed El-Regulus at `(-352,-1841)` and Crescens at `(380,-1838)`,
a 732-world-unit spread that placed the two machines at opposite sides of the
frame.

El-Regulus now stands at `(-200,-2035)` and Crescens at `(200,-2035)`. Both
anchors are on connected, flat source-260 walkmesh, with enough edge clearance
for the field actors and a 400-unit visual gap between the large sprites. The
on-foot party approaches them along the center aisle.

Director entity 0 now owns a single automatic trigger at `z=-2100`. Crossing
it locks control, plays the El-Regulus and Crescens boarding beats followed by
the surviving-Guardian warning, assigns Gear 10 to Elly and Gear 9 to Emeralda,
mounts party slots 0 and 1, sets both persistent mounting bits, and immediately
starts fixed no-Escape battle configuration 15. The parked Gear action and
collision slots are inert, so there are no tiny or competing X prompts.

The battle still contains only Elly/El-Regulus and Emeralda/Crescens against
one 36,000-HP Guardian in the Goliath Factory arena. Citan and Fenrir remain
absent. In the post-victory tail, bit 5 is set and the existing response plays
before one checked target-384 parameter-zero reload rebuilds both resident actors as
visibly mounted Gears. The north bulkhead remains nonfunctional. The south
personnel lift still dismounts both pilots, clears both staging bits, and
returns them to target 376 on foot.

V79's terminal-role separation is retained: large control panels own switches,
small terminals own optional exposition, Archive Console D keeps its rail/mail
split, and Central Control keeps separate archive and launch interactions.
El-Regulus's canonical-38 facing repair, canonical-453 field sprite, exact
GameState `0x16E4 = 0x1FF8` Attack-Level word, and canonical-2960 deathblows are
unchanged.

The final package contains 126 jobs and 158 declared replacements totaling
10,755,907 bytes. Their canonical-ID-order aggregate SHA-256 is
`efccfc74f52dd8c04aa146cdd3c9d1a4e0ef2f45f3d597d5f11de775c5ac74e1`.
The automated suite passes 201 tests and 2,274 subtests.

- BIN: 695,702,784 bytes,
  `1bbe79d3cda8548403f01f7d3f44ff36fb6ba53359a8501b4962772448b5057e`
- CUE: 106 bytes,
  `98205231632947108773af7601ebd5dd885eb7ab8fc930329f3f6ee800cc9186`
- Manifest: 184,986 bytes,
  `43f4c2009f2cd68432d247664f76a2c84bf6713b80805b985413f35bcb8a6ea3`
- Target-384 bundle: 162,460 bytes,
  `31fbb31fa4768873196c7095515c4248a9d4a23c2f5207abc8b047ccba918f2d`
- Target-384 script: 21,207 bytes,
  `ca016611e19974493f7b8e32d8451ed64bde18ba0953476864e216664f259b3a`

Runtime acceptance requires a fully quit DuckStation, a cold boot of the v80
CUE, and New Game without loading any old F1 state or in-game save. In target
384, confirm both Gears frame together, the approach starts the combined scene
without pressing X, combat follows immediately, victory returns with both
pilots visibly mounted, and the south lift safely restores the on-foot party.
