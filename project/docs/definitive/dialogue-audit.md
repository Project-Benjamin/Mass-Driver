# Retail dialogue inventory and yellow-name option

The 2026-09-07 inventory read both configured USA retail images without
modifying them. It decoded every populated field dialogue component in the
retail field group; there were no field parse failures. This is a field-text
inventory, not a complete gameplay or translation acceptance test.

| Inventory | Disc 1 | Disc 2 |
| --- | ---: | ---: |
| Field slots before the next FAT resource group | 768 | 768 |
| Fields with dialogue directories | 643 | 180 |
| Fields with native no-dialogue sentinels | 87 | 25 |
| CDMAKE placeholders for fields absent on this disc | 0 | 525 |
| Empty field slots | 38 | 38 |
| Dialogue IDs, including aliases and blank blocks | 18,182 | 6,154 |
| Eligible standalone speaker rows | 6,426 | 1,864 |
| Fields containing eligible rows | 379 | 106 |
| Multipage blocks requiring renderer review | 4,225 | 1,272 |
| Choice blocks preserved | 1,502 | 1,117 |
| Unidentified/ordinary/blank blocks preserved | 6,027 | 1,901 |
| Terminal-control blocks requiring review | 2 | 0 |

Disc duplicates and aliases are counted separately by dialogue ID; these
totals are not a count of unique lines in the story. The 38 empty slots are
730 through 767. A metadata record at the next slot begins other resource
types and prevents accidentally treating non-field archive assets as scenes.

The optional pass currently colors a verified name occupying the complete
first row of a single-page block. Exact party-name tokens and an explicit
list of labels observed in the retail inventory establish a speaker; capital
letters alone never do. Names in prose, choices, unknown labels, later pages,
or ambiguous control sequences remain unchanged and are counted for review.
Native dimensions, dialogue IDs, alias relationships, and all original
payload bytes remain intact. The only inserted payload bytes are the three
bytes of the shared renderer's opt-in marker. The writer rebuilds checked
16-bit offsets and refuses growth beyond the component's 65,535-byte limit.

Retail dialogue contains forms that authored-text validation intentionally
rejects: multiple IDs sharing an offset, unused data after the first Close,
and native variable-length controls whose conservative token interpretation
does not show a Close. The inventory reader preserves these forms without
relaxing `shared.tools.xgdialog`'s strict authored-text writer. The two
terminal-control cases are Disc 1 field 127/block 6 and field 209/block 98;
those blocks are preserved and left for control-flow review.

The kernel renderer implementation now lives at
`shared/tools/xgdialog_name_color.py`. Rico imports the same implementation
through its compatibility module; no kernel instructions changed during the
extraction. Its existing differential instruction tests still check branch
and load delays, the five native substitution tables, marker consumption,
both sprite halves/parities, and resetting the next queued block. Existing
boot-file, embedded FAT, and executable-region checks still pass.

`modules.definitive.dialogue.patch_disc_dialogue(image_path, disc,
yellow_names=False, replacements=None, include_text=False)` returns a mapping
of canonical file IDs to replacement bytes and a JSON audit. Supplied
translation replacements are read before the donor, then preserved in the
returned mapping. A changed field is rebuilt with canonical shared field
helpers, preserving every other compressed component byte-for-byte. The
caller must install the shared executable renderer if it enables markers.

The local full inventories are generated as
`builds/definitive-audit/dialogue-disc1.json` and `dialogue-disc2.json`. They
include field/file/block identities, original dimensions, source hashes,
text, classifications, and coverage limitations. Regenerate either with:

```powershell
python -m modules.definitive.dialogue '<retail image.bin>' --disc 1 --include-text --output builds/definitive-audit/dialogue-disc1.json
```

Validation: 14 focused dialogue/inventory safety tests and all 7 existing
Rico kernel-renderer tests passed. An in-memory pass rebuilt all 379 Disc 1
and 106 Disc 2 eligible fields without parse or rebuild failures; its audits
are `builds/definitive-audit/yellow-names-disc1.json` and
`yellow-names-disc2.json`. Full-profile checks and rebuilt-media
verification belong to the definitive build receipt. No emulator playthrough
or whole-game visual review has been performed for this option. Inline and
multipage speaker coloring, unidentified NPC labels, non-field text, menus,
battle text, and movie subtitles remain outside the current completed pass.
