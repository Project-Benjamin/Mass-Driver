# Mass-Driver graybox 0.1

## What is playable

Graybox 0.1 turns the Disc 2 Mass-Driver narration into a short on-foot field
sequence. The normal and fallback narration paths in retail field 617 now send
Elly to scene 724. The route is contained entirely in three previously
unreferenced scene slots and returns to the untouched story chain at scene 618.

| Scene | Graybox role | Retail donor | Runtime result |
| --- | --- | --- | --- |
| 724 | Entry/service corridor | 633 | Loads, renders, and accepts movement |
| 721 | Machinery hub | 634 | Loads and renders at parameter 0 |
| 726 | Launch control | 631 | Loads, runs custom dialogue/event, and exits to 618 |

All exits from 724 are contained in 721. The hub's audited exits lead either
back to 724 or forward to 726. The only exit from 726 resumes retail field 618.

## Implemented changes

- Cloned both field bundles and their paired graphics into scenes 724, 721,
  and 726; donor fields remain unchanged.
- Redirected the retail Mass-Driver branch before its narrated text and
  world-map interlude.
- Disabled donor random battles so the solo-Elly story state cannot enter an
  Anima Relic encounter table.
- Removed the copied live treasure actor from scene 724.
- Redirected copied Anima Relic state writes from persistent save variables to
  field-local scratch state.
- Rebuilt the control room's variable-length dialogue section and pointer
  table with Mass-Driver, silo, and nanomachine launch text.
- Redirected the control-room hatch to retail field 618.

## Runtime verification

The rebuilt cue was tested under DuckStation 0.1-11580-ge7f2f101c with a real
US PS1 BIOS:

1. BIOS fast boot recognized the image as `Xenogears (Disc 2)`, serial
   `SLUS-00669`, and initialized the game kernel.
2. Xenogears' retail debug room loaded scenes 724/0, 721/0, and 726/0 from the
   rebuilt disc; all three rendered successfully.
3. The scene-726 console displayed consecutive rebuilt lines including
   `Mass-Driver launch sequence accepted.`, `Nanomachine payload loaded.
   Opening silo.`, and `Launch.`
4. The copied launch animation completed without a hang and returned control.
5. Interacting with the scene-726 exit loaded retail field 618 and resumed its
   narration event.
6. Every replacement was re-extracted from the final disc and matched the
   manifest byte-for-byte; every cloned bundle also decompressed and reparsed.
7. A standard PS1 memory card containing `No.05 Shot Down!` was loaded through
   Disc 2's normal Continue/Load menus. It restored Fei and Elly in field 615.
8. The unmodified retail chain was played through Taura's lab, the Shevat
   emissary scene, the forest departure, the Karellen intercut, and the
   mandatory Gear battle. Its field-617 transition entered scene 724 with Elly
   alone, where the blue service corridor rendered and accepted movement.

Automated unit tests cover disc-sector parsing, field bundle packing, LZSS
handling, event-script patch validation, dialogue rebuilding, Xenoiso command
construction, and the graybox builder.

## Known limitations

- This is a short technical graybox, not yet the planned 20-30 minute dungeon.
- It uses copied Anima Relic visuals rather than a purpose-built Mass-Driver
  facility. Scene 724 inherits conspicuous camera/foreground occlusion that
  should be replaced or retuned.
- The real story path currently prepares Elly alone. Emeralda's presence,
  Citan's entrance, and character-specific dialogue remain future work.
- There are no enemies, puzzles, launch prerequisites, optional terminals,
  music edits, new cinematics, or unique rewards.
- The three rooms, the real field-617 story hook, and the 726-to-618 handoff all
  have runtime coverage. The supplied one-save memory card provides a repeatable
  entry point for future playtests.
- The control interaction reuses a donor animation; it is functional but not a
  bespoke missile-silo sequence.

## Next production pass

The next useful pass should replace scene 724's awkward presentation, add one
facility-operation puzzle, and stage Emeralda/Citan before adding combat or
expanding the map count.
