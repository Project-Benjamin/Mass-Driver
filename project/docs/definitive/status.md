# Xenogears Definitive development status

Date: 2026-09-07. The objective is the original game with repaired existing
content and optional presentation/convenience patches. **The whole-game
definitive version is not finished.** This report separates implemented
candidates from imported source data and unresolved work.

The independent `definitive` profile uses the configured USA retail discs.
It does not select Mass Driver, Soylent System, Rico, or their chapter content.
Their protected scenes, donor contracts and saves are not modified. The shared
registry/renderer updates make older chapter receipts stale under workspace
policy; their existing media and active selections are retained. Rebuild a
chapter under a new release name before launching it with current sources.

## Patcher and current feature coverage

Run [PATCH_XENOGEARS_DEFINITIVE.cmd](../../PATCH_XENOGEARS_DEFINITIVE.cmd).
The GUI supports verified retail inputs, independent switches, immutable
selection files, isolated release output, test execution and activation only
after successful media verification. This is a Python Windows application,
not yet a packaged standalone executable or distributed binary patch release.

The patcher uses a single compact page: two disc inputs, four patch checkboxes,
HD pack export and one build button. There is no main-page canvas, scrollbar or
expanding section. Unfinished features and coverage details are in Patch notes;
the build log opens separately.
Inputs lock during work; progress reports the current stage. Successful builds
and portrait exports expose their output folder. Missing inputs are reported in
the form, and errors retain a readable log. The window uses the form's measured
height and cannot be shortened to clip controls. At 100%, 150% and 200% display
scaling its measured sizes are 620×388, 929×574 and 1239×750 pixels. Layout
checks also cover completion with the output-folder action visible.

The September 7 verification pass adds a targeted first-Deus camera correction,
two food-description corrections, and the Bulimy gain-item cap correction to
the existing bug-fix option. See [restoration release verification](restoration-release.md)
for the exact installed release, tests and media hashes. All builds remain
gameplay-untested. Earlier releases, including `foundation-ui-v2` and
`supported-options-v2`, are retained with their older source snapshots.
Historical media hashes, selections and checks are in [validation.json](validation.json).

| Requested feature | Current implementation | Remaining acceptance work |
| --- | --- | --- |
| Fan retranslation | All 10,804 Fan passages imported with integrity checks; both-disc candidate mapping; guarded compiler with two reviewed opening blocks | Complete ROM mapping, optional NPC coverage, nonfield text, annotation handling, line layouts and playthrough. Full toggle is disabled. |
| Bugs, spells and items | Existing Def Up, Charger and Gear-shop fixes pass native CPU checks; targeted Mahanon Deus camera guard; Hob-Meat/Hob-Steak descriptions corrected to 100/150 HP | Deus battle playback and complete item/spell effect semantics; Billy ammunition and broader status behavior remain open. Inventory counts do not certify effects. |
| Weight | Bulimy gain cap repaired; native item changes, display, save-buffer copies, Gear-load penalty and its battle consumer checked | Real meals, card save/load and combat timing. Body weight has no established original Attack/ATB formula; no invented curve applied. |
| HD portraits | All 91 supplied assets mapped to retail bank resources; lossless 256x256 PNG export for both disc serials | Runtime upload/hash/crop/palette checks and installation. Exported sidecar is not installed automatically. Menu and battle portraits are separate resources. |
| Half encounters | Field and world-map scheduling paths identified | Complete timer scaling, both travel modes, threshold restore paths and overflow checks. Disabled. |
| No encounters | Optional two-instruction candidate suppresses field/world random dispatch; forced handlers unchanged | Runtime encounter sampling and required story-battle progression. |
| Story mode / one-hit kills | Explicitly tracked | Enemy scripts, invulnerable phases, transformations, battles that must be lost and final bosses. Disabled until a safe implementation exists. |
| Max gold | Native cap, storage, transaction/reward/refuel paths identified | Reliable existing-save behavior, load/save hooks and independent spending paths. A starting-money edit is not labeled persistent max gold. |
| Double XP | Optional exact 32-bit scaling of eight reward records in every one of 76 enemy files per disc | Runtime reward/level-up checks, including bosses. Gold, stats, drops and learning rules stay unchanged. |
| Yellow names | Optional 6,426 Disc 1 and 1,864 Disc 2 recognized single-page labels across 379/106 fields | Multipage, inline and unidentified speakers; native display validation. Prose and choices are not guessed to be names. |

Counts are per disc and can include duplicate/shared content. Yellow candidates
cover existing labels; they are not a claim of complete name coverage.

## Audits and assets

- [Translation import, mapping and compiler](translation.md).
- [Complete field-dialogue inventory and name-color rules](dialogue-audit.md).
- [Minimal bug fixes, weight and encounter evidence](mechanics-audit.md).
- [Mahanon Deus correction and limits](deus-fix-verification.md).
- [Item/spell inventory and proven description corrections](item-spell-verification.md).
- [Native weight verification](weight-verification.md).
- [Unresolved known bugs in the baseline](remaining-bug-verification.md).
- [Persistent money investigation](max-gold-audit.md).
- [Portrait identity, emulator format and mapping evidence](portrait-mapping-notes.md).
- [Supplied portrait pack integrity](portrait-audit.json).
- [Generated HD candidate manifest](../../builds/definitive-audit/texture-pack/manifest.json).
- [Generated HD candidate usage notes](../../builds/definitive-audit/texture-pack/README.txt).

The 91 portrait IDs correspond to original bank images, not directly to the
engine's remapped speaker-selector numbers. The export collapses one duplicate
native texture and leaves the transparent placeholder unmapped, producing 89
unique texture aliases per serial. All decoded pixels survive conversion.

## Verification policy

Every disc builder accepts only the pinned retail SHA-256 inputs and writes a
new output directory. Patch helpers check exact preimages and preserve all
unselected bytes. The final image verifier checks every resource, the native
directory table, nonfile FAT group counts and relocated pointers, the boot
executable and its FAT mirror,
ISO boot links, and both-disc playlist references. It rejects unapplied patches. XA movies are checked as complete raw 2,352-byte
sectors using their 2,336-byte stored-payload sizes, not ordinary file reads.
The initial v1 attempts exposed that verification distinction and remained
failed/unactivated; replacement candidates are rebuilt under new names.

The profile suite includes shared checks and registry/release checks. The
earlier chapter regression suite passed with 1,084 tests run (seven explicit
skips) after the shared renderer extraction. The previous Definitive profile
suite passed with 244 tests run (one explicit skip), including
patch composition, both-disc reward tables, immutable patcher selections,
corruption rejection, translation guards, portrait pixel preservation and
patcher input/busy/error/completion behavior.
The new restoration pass adds native CPU and installed-resource checks;
its final test count and results are recorded in [restoration-release.md](restoration-release.md).

No emulator playthrough has been performed. The user stopped Computer Use with
Escape during patcher UI inspection, and UI interaction stopped. File-based
verification can establish correct patch bytes, but not gameplay acceptance.
New Game, ordinary memory-card Continue, disc change, menus, combat and ending
must be exercised independently of resume states before release acceptance.

The pre-existing combined-selector New Game black screen is still open in its
own profile. This retail profile does not establish that it is fixed.

## Next acceptance work

1. Validate the generated base candidate from New Game and ordinary Continue;
   inspect yellow names in native windows and exercise every installed repair,
   especially the first Deus HP-halving attack from a normal pre-fight save.
2. Validate the HD aliases against actual DuckStation uploads, then connect the
   HD toggle to reversible installation preserving existing texture packs.
3. Complete field/script-context translation mapping and nonfield text stores,
   preserving controls, speaker identities and scene timing; review every page.
4. Continue isolated spell/item bugs and native weight tests, including Gear
   equipment separately from character body weight.
5. Finish half encounters, persistent money and one-hit story mode; test option
   combinations across both discs and required battle sequences.
6. Perform the full campaign regression and publish a patch-only distribution
   once the acceptance evidence exists.
