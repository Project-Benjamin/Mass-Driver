# Mass Driver Dungeon 2.34 - v55 Defense Archive Arrival

Version 55 preserves the natural doorway arrival in target 376, turns Citan's
Defense Archive briefing into a player-triggered conversation, and adds
far-bulkhead directions to all three missile galleries.

This remains an original, canon-conscious fan reconstruction. It is not
recovered Square script or official cut-content data. Version 55 changes the
presentation and wayfinding around the retained v54 progression repair; it
does not add another objective condition.

## Natural threshold arrival

The Central Gate still enters target 376 parameter 0 through field 394's
native east service-stair threshold. Elly and Emeralda now keep that receiving
entry exactly: they arrive at `(668, 192)`, face into the room, and remain under
the inward-facing camera. No checkpoint routine moves them from the doorway to
a mid-room tableau.

Citan is loaded silently while the destination is fading in. He waits on
connected floor at `(130, 50)`, beside the archive console but outside both
the console's X-activation area and Emeralda's observed follower path. His
stationary room update prevents him from walking into the terminal approach;
ordinary party-following behavior resumes in adjacent fields.

The result is one continuous arrival. The east stairs remain visibly behind
the party, the room can be read before any conversation begins, and control
returns without an automatic dialogue window.

## Player-triggered Citan briefing

Citan's field actor now has a reliable, bounded X interaction. The first
conversation begins only when the player faces him and presses X. He:

- greets Elly and Emeralda after their arrival;
- explains that restored power opened the eastern service route he used;
- says Taura sent El-Regulus, Crescens, and Fenrir through the freight lift
  to the defense bay;
- points the party to the wall console and its emergency directive and
  four-point authority code;
- states that the archive records reveal the entries while allowing direct
  entry if the party already knows them.

The briefing sets its own persistent bit, separate from Citan's party-join bit
and every authorization bit. Speaking to him again before the Guardian gives a
short console reminder. Speaking to him after victory points through the open
west bulkhead, the missile galleries, and toward Central Control.

## Independent wall console

Target 376 entity 13 remains field 394's genuine wall terminal. Its native
visual controller, layered scenery, collision, and X-activation area are
preserved. Citan's position and collider do not steal the approach used to
operate it.

The console does not depend on the Citan-briefed bit. The player may speak to
Citan first, use the console first, or return to either interaction later.
Citan's action contains no authorization write and cannot start the Guardian
battle. Conversely, the console continues to:

1. name either unread clue record and say manual entry remains available;
2. open the Directive and four-point authority menus;
3. reject wrong combinations without consuming anything;
4. accept `0320` and `A-2 / B-5 / C-8 / D-4`;
5. start the retained custodian sequence.

The record bits remain knowledge flags, not credentials. Auxiliary and rail
power still open the Central Gate, accepted codes still authorize the launch,
Guardian victory still opens the west bulkhead, and Central Control still
releases Taura's capsule.

## Gallery wayfinding

The three missile-gallery record scenes now name the visible far bulkhead
rather than leaving the player to infer which identical industrial door
continues the route:

- Gallery A says the far bulkhead leads through the remaining galleries and
  that Central Control lies beyond them.
- Gallery B says the far bulkhead leads to the final gallery.
- Gallery C says Central Control is beyond the far bulkhead.

These directions follow the physical sequence
`376 -> 377 -> 378 -> 379 -> 728`. They do not change the reciprocal animated
doors, the eight visible missiles in each gallery, or immediate backtracking.

## Regression contract

The focused builder coverage verifies:

- target 376 parameter 0 retains the audited threshold coordinates, actor
  direction, and camera direction;
- Elly and Emeralda keep their donor initialization and update scripts, with no
  hidden staging action;
- entering the room silently loads Citan but opens no dialogue and performs no
  mid-room party movement;
- Citan is visible, stationary, X-interactable, and clear of the console stance
  and follower trail;
- first, pre-Guardian, and post-Guardian talks select the correct dialogue
  state, while only the first sets the briefing bit;
- Citan's action cannot write launch authorization or dispatch the battle;
- entity 13 remains independently reachable and keeps the nonblocking clue
  behavior introduced in v54;
- every added dialogue page obeys the retail 58-unit by five-line window;
- Galleries A, B, and C contain their distinct far-bulkhead directions.

## Focused runtime acceptance

Cold boot the v55 CUE. A state made while target 376 was already loaded from an
older image still contains that older field routine and cannot validate this
presentation until the room is reloaded.

1. Restore auxiliary and rail power, then open target 726's Central Gate.
2. Confirm Elly and Emeralda walk naturally through the east service-stair
   threshold and remain at the target 376 doorway when control returns.
3. Confirm no dialogue opens automatically and Citan waits beside, not on top
   of, the wall-console approach.
4. Walk directly to the wall console without speaking to Citan. Confirm X
   still opens its authorization flow.
5. Re-enter if necessary, face Citan, and press X. Confirm he explains the
   freight-lifted Gears and directs the party to the console.
6. Speak to him again before authorization and confirm the concise reminder.
7. Enter the correct codes, defeat the Guardian, and confirm Citan's repeat
   dialogue points through the west bulkhead.
8. In Galleries A, B, and C, read the record scene and follow each stated far
   bulkhead to Central Control.

The v55 build targets are:

```text
work/mass_driver_v55_stage
output/Xenogears_PW_CD2_mass_driver_standalone_v55.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v55.cue
```

## Frozen build evidence

The final v55 BIN is 694,799,616 bytes (295,408 raw sectors), SHA-256
`da914b0302244490f3f22187ea780af971ea928381520c89e9a685bd9af78267`.
Its CUE is 106 bytes, SHA-256
`98024e0a2c63d546331887c2d9705df22d693ebb00c26f2d69c58cb58b51dfcb`.
The stage manifest is 163,468 bytes, SHA-256
`a625fe2522dbf72ffb937ce6389d9318a2b638bf69b9d413052da0b0b5c6c003`.

All 149 declared replacements, totaling 9,688,659 bytes, re-extract
byte-exactly from the final image. The 4,794 unique replacement sectors plus
the standalone boot sector all regenerate byte-identically as MODE2/Form1;
no EDC/ECC mismatch remains. The full suite passes 165 tests and 1,944
subtests.

`output/MASS_DRIVER_V55_CONTINUE.sav` is a separate 1,776,517-byte
continuation, SHA-256
`be5a153f760848d46394bd8981d5140fc634b18ee8ee82c8a408a747a1fafb45`.
Its v55 resident archive table is SHA-256
`edd76ce06ae303cedc62d22953c5d6510b15d0eb2a3665966b5e60246523d0f5`.
The migration leaves the v54 source state untouched. Because the saved screen
already has v54 field code loaded, use the east stairs and re-enter through
the Central Gate once before evaluating the new arrival and Citan interaction.
