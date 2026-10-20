# Fan translation import and ROM mapping

The source is the **Fan Retranslation** edition at
[Xenoverse.world](https://xenoverse.world/#/xenogears/script), identified by
`Faithful fan localization; Japanese-checked`. The separate Direct Retranslation
edition is not substituted when a Fan passage is missing.

The 2026-09-07 import contains all 70 chapters listed by the website, 63 Fan story
files, and 10,804 Fan passages. Every Japanese passage selected by the chapter
catalogue has a Fan passage. The 133 alignment/Fan assets total 18,623,163 bytes.
Each Fan file passes the website's original Japanese-revision and
`JSON.stringify(units)` SHA-256 checks. Downloaded assets are also individually
hashed in the local manifest.

This establishes source availability, not a complete game patch. Transcript
passages have chapter/unit IDs rather than ROM addresses; some include menu
choices, arrows, commentary, typographic characters, and multiple game windows.
The website alignments contain 9,058 paired rows, 795 Japanese-only rows, and
1,952 official-only rows. These are transcript alignment counts, not counts of
missing game dialogue. Menus, item descriptions, battle messages, FMV subtitles,
and optional NPC coverage require separate inventories.

## Local results

| Result | Location |
| --- | --- |
| Source provenance and coverage | `modules/definitive/content/translation/source-audit.json` |
| Downloaded corpus and integrity manifest | `output/definitive/translation/` |
| Compact retail mapping summary | `modules/definitive/content/translation/rom-mapping-summary.json` |
| Full retail candidates | `output/definitive/translation/retail-disc1-mapping-audit.json`, `retail-disc2-mapping-audit.json` |
| Reviewed two-block compiler example | `modules/definitive/content/translation/reviewed-example-field014.json` |
| Compiled example field | `output/definitive/translation/compiler-example/0634.bin` |

The read-only retail scan uses the current `modules.definitive.dialogue`
enumerator and lossless retail reader. The field group ends at the FAT metadata
boundary after 768 slots. Disc 1 contains 730 actual fields and 38 empty slots.
Disc 2 contains 205 actual fields, 525 CDMAKE placeholders, and 38 empty slots.
Dialogue aliases and unreachable tails are retained during inventory.

| Retail source | Audited dialogue blocks | Exact normalized candidates | Candidates with one transcript-row match |
| --- | ---: | ---: | ---: |
| Disc 1 | 18,182 | 6,805 | 6,279 |
| Disc 2 | 6,154 | 2,002 | 1,828 |

The counts are per disc and can include shared/duplicated content. Candidates
remain unverified even when only one row matches. No dialogue is modified by a
source import or candidate audit.

## Guarded compilation

`compile_verified_field(source_bytes, mapping, fans)` returns rebuilt field
bytes and an audit. A mapping must name exact original field, component, and
payload hashes; source Fan unit IDs and wording hashes; explicit static review
evidence; and replacement token text with reviewed dimensions. The compiler
checks exact Fan wording, preserves the complete sequence of retail control and
dynamic-name tokens, checks line widths/page heights, preserves every unselected
payload, and compares all eight other field components after recompression.

The included example maps Lahan's painting opening, field 14 blocks 0 and 1, to
`story01-b003-u001` and `story01-b003-u002`. The website official transcript rows
match those retail lines exactly after whitespace normalization. The replacement
keeps the Fan wording, the original `Delay:20`, both `Close` controls, block IDs,
and original 3/4-row heights. Widths expand from 44 to 54 and 26 to 32 to fit the
Fan text. The original actor scripts, cameras, timing commands, sound and other
field content are byte-preserved.

This is a two-block static compiler proof, excluded from the complete
retranslation toggle. It has not been tested in an emulator. In particular,
screen placement and any cinematic assumptions about text box width still need
runtime inspection. The guarded compiler currently requires the stricter
authored-text dialogue format, so retail alias/missing-terminal variants that
can be inventoried still need an explicitly verified compilation strategy.

## Commands

```powershell
python -m modules.definitive.translation fetch
python -m modules.definitive.translation audit-disc "Xenogears (Disc 1).bin" --output output/definitive/translation/retail-disc1-mapping-audit.json
python -m modules.definitive.translation compile-field "Xenogears (Disc 1).bin" modules/definitive/content/translation/reviewed-example-field014.json --output output/definitive/translation/compiler-example/0634.bin
python -m unittest modules.definitive.tests.test_translation
```

The tools never write the source disc or user saves. Refreshing the website
import can invalidate a reviewed mapping if the selected Fan wording changed.
`load_corpus()` rejects modified local assets before compilation. The corpus is
generated data in ignored `output/`; the source/audit reports and reviewed
mapping are small repository artifacts.

The importer discovers the public application bundles and chapter catalogue
without executing website JavaScript. Its browser User-Agent is necessary for
the site's normal public asset access; the default Python User-Agent returned
403. All imports use `shared.tools` or current `modules.definitive` helpers.
