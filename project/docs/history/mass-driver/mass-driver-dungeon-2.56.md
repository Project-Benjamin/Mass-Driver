# Mass Driver v79 terminal-role separation

Version 79 makes the dungeon's control language consistent. **Large control panels
operate machinery, authorization, launch, or concise status; small terminals
carry optional archive mail and political exposition.** This is an
original fan reconstruction, not recovered or official cut content.

## Corrected rooms

| Target | Large control | Small archive terminal |
|---|---|---|
| 361 | entity 12 at `(17, 190)`: Auxiliary Grid switch, bit 0, dialogue 1 | entity 13 at `(110, 117)`: Directive 0320 and mail, bit 2, dialogue 0 |
| 365 | entity 13 disabled; static station art retained | entity 14 at `(-89, 90)`: Archive Mail Terminal A |
| 366 | entity 13 disabled; static station art retained | entity 14 at `(-89, 90)`: Archive Mail Terminal B |
| 369 | entity 13 disabled; static station art retained | entity 14 at `(-89, 90)`: Archive Mail Terminal E |
| 370 | entity 13 disabled; static station art retained | entity 14 at `(-89, 90)`: Archive Mail Terminal F |
| 371 | entity 13 disabled; static station art retained | entity 14 at `(-89, 90)`: Archive Mail Terminal G |
| 724 | entity 13 disabled; static station art retained | entity 14 at `(-89, 90)`: Archive Mail Terminal H |

In Target 361, the entity ownership was fully swapped while retaining each
native action pointer. Entity 12 action `0x00EF` now sets only Auxiliary bit 0,
plays sound `0x37`, and opens switch/status dialogue 1. Entity 13 action
`0x0190` now sets only Directive clue bit 2 and opens archive dialogue 0. The
maintenance mail, Adviser waiver, Aron/Lena thread, and party response all live
in dialogue 0. Dialogue 1 contains only the bypass result, bus status, Central
Gate condition, and pointer to Archive Console D.

The lore-only targets 365, 366, 369, 370, 371, and 724 now use the same reachable small terminal
contract already proven by Target 368: native static model 4/header node 25,
entity 14 controller at `(-89, 90)`, and a repeatable dialogue action that
writes no progression bit. Their large entity-13 controller is fully disabled
with init `0x02CD -> 0x030F` and action `0x02E6 -> 0x030E`; the large station's
static scenery remains visible. Together with the already-correct materials
lab and rail room, the labels now read Archive Mail Terminal A through H.

## Dungeon-wide audit

Target 368 remains the intended exemplar: its large entity-13 Archive Console
D operates the accelerator rail, while its small rear entity-14 terminal holds
Aron's mail. Target 367 has a single small mail computer and separate door
control. Target 722 has one archive computer plus a separate Omegasol chest.
Target 376's wall console contains authorization UI and operational status,
not passive mail. Reserve Magazine 02 uses its dedicated repeatable archive
terminal. Central Control keeps optional mail on entity 12 and the required
capsule launch on entity 13; its one-time historical afterimage remains part of
the launch mission rather than passive exposition.

The build now runs a terminal-role verifier over Target 361, all seven
source-378 annexes, and Central Control. It proves bit and dialogue ownership,
the six disabled large-station controllers, each reachable small-terminal
initializer, the exact repeatable mail action, and the preserved Target 368
rail/mail split.

## Retained v78 gameplay

Retained v78 gameplay includes the single-room Goliath Factory Gear-staging
route, Elly/Emeralda-only Guardian battle, final-only Citan assistance,
El-Regulus combat-facing repair and field art, exact GameState word
`0x16E4 = 0x1FF8`, correct `0x60/0x61/0x62` Attack-Level accessories, and the
complete Level-1/2/3/Infinity deathblow suite. Old F1 states and old in-game
saves still cannot validate the current field controllers or Attack-Level
state; use a fully quit, cold-boot v79 New Game.

## Packaged evidence

The final v79 package contains 126 jobs and 158 declared replacements totaling
10,755,999 bytes. Their canonical-ID-order aggregate SHA-256 is
`e9fa862430b5c2a0d022c75a215110305a958adbc88e2ef9db70d5bdfb4290a6`.
The complete automated suite passes 201 tests and 2,275 subtests.

- BIN: 695,702,784 bytes, 295,792 raw sectors,
  `de4349ad3d3dd8af475a324913a88c56c9d696668d26235a3d385b48a210cc30`
- CUE: 106 bytes,
  `073a188de5e1555d6171683c4144d0afb5280d1cf90a2408ddb50359700f360b`
- Manifest: 184,677 bytes,
  `605310cbbc07886e3f48f4405877dfaf235c8851ff233c5d3ce931022ab1ed5b`

Cold-boot acceptance should first check Target 361, then any of targets 365,
366, 369, 370, 371, or 724. The large station must not open lore in those six
rooms; facing the small rear terminal and pressing X must present the complete
record repeatedly. Reconfirm Target 368's large rail/small mail split and
Central Control's separate archive and launch consoles.
