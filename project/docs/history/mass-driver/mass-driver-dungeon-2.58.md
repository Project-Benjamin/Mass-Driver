# Mass Driver v81 auxiliary-terminal controller correction

V81 corrects target 361 against the July 31 auxiliary-room screenshot. The
freestanding terminal directly in front of Elly is entity 12 at `(17,190)`;
its native action at `0x00EF` now presents Directive 0320 and the complete
maintenance/political mail in dialogue 0, writes only clue bit 2, and plays no
switch sound. The farther-right Auxiliary Grid console is entity 13 at
`(110,117)`; its native action at `0x0190` now presents switch/status dialogue
1, writes Auxiliary-power bit 0, and plays SFX `0x37`.

This exchanges only the two controllers' authored action responsibilities.
Their native art, positions, interaction hitboxes, dialogue text, room doors,
and all other dungeon behavior are unchanged. Dialogue 0 and dialogue 1 remain
byte-identical; each is now dispatched by the controller matching the object
shown in the screenshot.

Only canonical replacement 1328 changed from v80 to v81.

- BIN: 695,702,784 bytes,
  `fe09652ec5961bf5680ea61e7cf911b208eb7dee4ab099e46c058f966f4d1d7e`
- CUE: 106 bytes,
  `57a57cd76ca502451e7151a955a77d425fd5669ddcc72119a6e3c6cc58c35fde`
- Manifest: 184,996 bytes,
  `49bd9d6cd07464127560f4180590b313a8fa929fabc6fa05588940da4edbe86d`
- Canonical 1328 / target-361 bundle: 89,732 bytes,
  `9c5b62e0d3db2ed7e03b6ccb29fcdcc458e9b75d1b6d46dd2f67a2f25c619611`
- Target-361 script: 2,087 bytes,
  `012e54e975fb53566ab56f08b074dbfa775aa46fd13a2f6cd046ccc77721a361`
- Target-361 dialogue: 1,390 bytes,
  `969a9b40deef2189f804ec8aae109efcffdb4f6b62003244753484413a1d504f`

The complete automated suite passes 201 tests and 2,290 subtests. Runtime
acceptance remains pending a fully quit DuckStation, cold boot of the v81 CUE,
and New Game without loading an older F1 state or in-game save. In target 361,
confirm that Elly's directly faced terminal opens the archive and the
farther-right console restores Auxiliary power.
