# Mass Driver v82 Zeboim service archive and paired-terminal mail

V82 replaces target 367's superseded field-380 room with retail field 382, a
compact, human-scale Zeboim vertical-lift service archive that fits the Mass
Driver facility. Target 726's formerly dead side panel enters parameter 0 at
`[0,-169,0,0,4]`. The room's visible freestanding computer is the donor's real
static model 10/header node 26 at `(0,0,110)`; entity 18's reachable controller
at `(0,45)` presents repeatable archive dialogue 0 without setting a
progression bit. The donor's native return uses entity 15 with helpers 12 and
13 and leads back to target 726 parameter 4.

V82 also makes both computer props readable in the six lore-only source-378
rooms: targets 365, 366, 369, 370, 371, and 724. In every one of those rooms,
desk controller entity 13 at `(45,-42)` presents repeatable dialogue 1, while
hanging-terminal controller entity 14 at `(-89,90)` presents separate,
repeatable dialogue 0. Neither interaction writes a progression bit. The new
desk records cover the civilian space charter and budget pressure, Strategic
Command's access and nuclear-payload demands, emergency political authority,
denied civilian generator requests, the order to seize Kim's molecular
machinery, and the rejected attempt to recall Directive 0320.

The Railway and Auxiliary rooms remain deliberate mechanical exceptions. In
target 368, the desk/main console remains the accelerator-rail switch and the
hanging terminal remains its separate mail reader. In target 361, the
farther-right main console remains the Auxiliary Grid switch while the
freestanding terminal in front of Elly carries Directive 0320 and the room's
mail. Neither switch console is repurposed for exposition.

The packaged v82 artifacts are:

- BIN: 695,291,184 bytes,
  `d37cc0684434bcb1438ab14d2455121e83ed9a35d08520708bdd3d025d8889b7`
- CUE: 106 bytes,
  `a6b8393a4a42ecb1e8ef8037d3678aba78efb61275053340f9f6df92ed5f9d86`
- Manifest: 185,646 bytes,
  `46dcd07c54c415a55368510fe8c7b98ca4f4f9c729fc44c7e064bc26f9448fcb`
- Manifest contents: 126 jobs and 158 declared replacements totaling
  10,390,635 bytes, with canonical-ID-order aggregate SHA-256
  `bb9c509abdb0cd83269b4dcb1ddfc992590b342e839f959d50e41bc46a6077dd`

The final automated suite passes: 202 tests and 2,311 subtests. Runtime
acceptance requires a
fully quit DuckStation, a cold boot of the v82 CUE, and New Game without an
older F1 state or in-game save. Confirm that target 367 renders as the Zeboim
service archive, its freestanding computer and native return are usable, both
mail interactions work independently in all six paired-terminal rooms, and
the Railway and Auxiliary main consoles still operate only their respective
interlocks.
