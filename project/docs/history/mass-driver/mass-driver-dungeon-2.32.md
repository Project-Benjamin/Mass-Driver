# Mass Driver Dungeon 2.32 - v53 Terminal Archive

Version 53 replaces the placeholder and abbreviated facility records with a
complete optional archive script. It also removes every exposition-bearing
treasure chest from the playable dungeon.

This remains an original, canon-conscious fan reconstruction. It is not
recovered Square script or official cut-content data. The historical spine
uses the released game and *Xenogears Perfect Works*: the Mass Driver was
conceived to move goods from the surface toward space by magnetic attraction
and repulsion, was militarized by Zeboim as a missile launcher, and is used in
the present to disperse Taura's nanoassemblers.

## Archive structure

The optional terminals form one readable progression:

1. Subway archive robot M-08 introduces the civil service line, the
   surface-to-space freight purpose, and the magnetic principle shared with
   maglev transport.
2. The Research Annex explains the launch system, its military conversion,
   Directive 0320, divided authority, and the separate auxiliary and rail
   power buses.
3. Materials Storage explains the four-point authority code and why payload,
   guidance, and rail power were separately controlled.
4. Archive consoles A-H cover the civil project charter, sequential magnetic
   acceleration, ascent-stage trajectory, rail safety, military requisition,
   Zeboim's hereditary crisis and thirty-year average life span, Kim's
   molecular-machine research, the 6081 Ravine bombing, and the separate 6083
   all-out nuclear-war report.
5. The defense archive explains why a valid four-point code still fails
   against an autonomous custodian obeying expired emergency law.
6. The three missile-gallery records explain how former freight bays received
   missile cradles, establish that custodians could seal and guard the assets
   but not launch without recognized human authority, and record that the
   surviving weapons were left locked.
7. Central Control preserves a final operator entry and deliberately reverses
   the facility's wartime purpose by launching Taura's capsule.

The terminals supply facts. Elly carries the moral throughline, Emeralda
responds directly to Zeboim's human and technological legacy, and Citan joins
the interpretation only after he physically reaches the defense archive.

## Retail text-window contract

The English field renderer uses four-pixel width units. Most one-byte Latin
glyphs consume two internal units, while the high-code asterisk consumes
three. Version 53 uses the established `58 x 5` story window for the new
prose:

- at most 29 standard two-unit Latin glyphs on a physical line;
- at most five rendered lines on a page;
- a speaker-name line counts as one of those five;
- literal line breaks are placed at word boundaries;
- `<New>` explicitly advances and clears the window;
- every block ends in exactly one reachable `<Close>`.

Blocks marked `manual_wrap: true` are now checked during the build. The
builder measures encoded glyph units, expands named-character controls,
rejects opaque raw controls, and rejects either an overlong line or a page
exceeding the window height. This prevents the retail renderer's
character-level fallback from splitting words.

## No exposition chests

The three former chest presentations are handled without importing new
graphics or changing rewards:

- Target `721:e14`, formerly the platform chest, initializes from local bank
  zero and therefore appears as a second maintenance robot. Its repeatable
  archive action remains at the same position and awards no item.
- Target `361:e16` was a redundant chest operating the same auxiliary bit as
  the real `e13` wall console. Both its initializer and action handler now
  resolve directly to `STOP`; the genuine console remains the sole control,
  with no hidden interaction left at the donor origin.
- Target `722:e15` retains its required authority-record bit and position,
  but initializes from the room's already loaded bank-one terminal/memory-cube
  actor instead of the chest bank.

The original unused sprite payloads remain loaded where necessary to avoid
unrelated VRAM and field-bundle risk. Target 725's genuine memory-cube save
point and target 376's genuine wall console are unchanged.

## Files and validation

Release paths:

```text
work/mass_driver_v53_stage
output/Xenogears_PW_CD2_mass_driver_standalone_v53.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v53.cue
```

The final BIN is 694,797,264 bytes (295,407 raw sectors), with SHA-256
`40361391e06566f6d9b08545a4c2502f912aba76ea5fa4a6572a34441858eb03`.
The CUE SHA-256 is
`5c0cdb02f6323a2334a703d535e5a4c43a84463f7610d7e3b0b162cd3d6e26ce`.
All 149 staged replacements, totaling 9,687,723 bytes, were extracted from
the packed image and matched exactly. The automated suite passes 165 tests
and 1,940 subtests.

Automated validation covers dialogue encoding and pagination, the complete
terminal/entity inventory, the three chest conversions, all progression
bits, reciprocal doors, the Guardian battle, the missile galleries, and the
authorization-gated launch.

Focused runtime acceptance must cold-boot the v53 CUE and confirm:

1. M-07 still opens both shops and M-08 repeatedly displays its archive.
2. Both robots remain visible after entering and cancelling both shop menus.
3. No exposition chest appears in targets 721, 361, or 722.
4. Every optional terminal advances through clean pages without broken words,
   scrolling overflow, control loss, or skipped text.
5. The Research Annex wall console and Annex 368 console still set their
   original interlock bits.
6. The converted Materials Storage terminal still records
   `A-2 / B-5 / C-8 / D-4`.
7. The defense authorization, Guardian battle, galleries, and final capsule
   launch remain unchanged mechanically.
