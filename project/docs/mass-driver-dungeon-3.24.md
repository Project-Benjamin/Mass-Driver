# Mass Driver Dungeon 3.24: first dialogue finishing pass

V168 improves the opening, the Guardian exchanges, Citan's launch dialogue,
and the two main archive clue interactions. This is a local development
candidate built from the preserved V167 standalone baseline. Fresh in-game
acceptance is pending.

Launch it with [PLAY_MASS_DRIVER_V168.cmd](../output/PLAY_MASS_DRIVER_V168.cmd).
The existing `PLAY_MASS_DRIVER_STANDALONE.cmd` still launches V167.

## What changed

- The opening consistently credits Taura's crew with delivering Vierge and
  Crescens. It establishes that Citan is checking capsule guidance and will
  meet Elly and Emeralda at the controls.
- The Guardian exchange uses consistent character portraits/tags and natural
  dialogue. Emeralda notices the awakened defense system; the party no longer
  asserts an unexplained transfer of the Custodian Core. Victory points the
  player toward Central Control beyond the west bulkhead.
- Citan explains why he needs the local controls, then gives a concise launch
  instruction. Elly's "Please... reach them all" and Emeralda's "Go!" remain.
- The Research Annex archive immediately shows Directive **0320** and the
  Defense Archive destination. Materials Storage immediately shows
  **A-2 / B-5 / C-8 / D-4** and the required input order.
- Each clue summary is followed by **Close archive / Read full record**.
  Close is the default; only selecting Read full record opens the full letters.
  The same short overview is available on every visit. The original 13-page
  and 14-page correspondence blocks remain exactly intact.

The [before/after dialogue review](mass-driver-dialogue-v168-changes.md)
contains all five revised blocks and four added blocks. The
[complete V168 transcript](mass-driver-dialogue-v168.md) is compiled-source
verified and distinguishes live Central Control text from dormant blocks.

## Protected content and scope

Central Control changes only block **35**. Miang's memory blocks **22–31 and
36**, immediate entry **21**, return **32**, and dormant **33–34** remain
unchanged. Central Control's scripts, cameras, actors, sound sequence,
geometry, collision, and graphics match V167 byte-for-byte.

The two archive action routines each grow by 72 bytes to provide the new
overview/menu. They use the existing clue bits and leave the power controls,
door behavior, rewards, and five-entry authorization challenge intact.
Reading the full letters does not become a new progression requirement.

The route remains 33 fields / 66 directed connections. Vierge, Crescens,
Guardian combat, the five magazines, and the launch/return behavior are
unchanged. This batch does not complete the wider dialogue, broadcast,
combat-balance, or ending review in the [finishing plan](mass-driver-completion-plan.md).

## Verification

- **188 tests run:** 187 pass and the existing frozen V161 release audit skips
  as intended. All **2,580 subtests** pass; zero failures or errors.
- The tests cover the new overview/read/close branches, first and repeated
  access, unrelated progress-state preservation, held-input guards, original
  correspondence integrity, and existing route, authorization, and finale
  contracts. Simulated non-read menu results are checked; physical Circle
  cancellation is not claimed as tested.
- All **33 active authored sources** recompile exactly to staged dialogue:
  **180 blocks / 444 pages / 30,835 bytes**. The total includes optional and
  dormant content; it is not the required reading load of one playthrough.
- All **166 final-BIN replacement payloads** match their staged files; all
  **5,877 affected raw sectors** pass Mode2/Form1 EDC/ECC validation.
- An exhaustive comparison of **3,723 extractable files** against V167 finds
  changes only in the five intended room bundles plus the two regenerated
  filesystem mirrors. Only the two clue rooms change script components.
- An independent rebuild matches all **547 stage files**, including the
  manifest, and the final BIN byte-for-byte. Its CUE is equivalent apart from
  the different output filename.
- The native publisher/title boot sector passes the existing byte-identity
  check. This is structural verification, not a completed emulator playthrough.

Evidence is recorded in `work/mass_driver_v168_tests.json`,
`work/mass_driver_v168_audit.json`, and
`work/mass_driver_v168_repeat_audit.json`.

## Fresh in-game check

Close any running DuckStation session, use the V168 launcher, and choose
**New Game** for a complete test. An older emulator savestate can restore its
old disc and resident scripts, so it cannot validate the new interactions.
Existing saves are not modified by building this candidate.

Check the opening's flow and window fit. At both clue terminals, confirm the
code appears first, Close returns control, and Read full record opens the
original letters. Repeat both choices, release and hold Cross at the window
boundaries, and check the controller's native cancel behavior. Confirm the
usual power/authorization route still works, then review the Guardian dialogue
and the uninterrupted memory-to-Citan-to-launch sequence.

## Build identity

- BIN: `output/Xenogears_PW_CD2_mass_driver_standalone_v168.bin`
- CUE: `output/Xenogears_PW_CD2_mass_driver_standalone_v168.cue`
- BIN size: **696,144,960 bytes**
- BIN SHA-256: `b72f2fd563dea6252b21899d06f81b91489f15b1ea50728545c049faa65aaebd`
- CUE SHA-256: `04f393eea2669f1140afebc00874ed66054a63742ba10f2e93eb5608a32e0f56`
- Manifest: `work/mass_driver_v168_stage/manifest.json`
- Manifest SHA-256: `af8408ca13616ccfa08c0ccf08f6b7e4743bb63013f5787909f64bb39da91788`
- Stage: **133 jobs / 166 replacements / 11,871,754 replacement bytes**
- Changed room canonicals: **1328, 1374, 2050, 2062, 2064**

The installer and portable distribution remain their preserved historical
versions. This candidate is supplied as a separate local BIN/CUE and launcher;
it has not replaced the frozen release package.
