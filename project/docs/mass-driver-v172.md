# Mass Driver V172 dialogue polish

V172 implements the approved [script-fit review](research/mass-driver-dialogue-fit-review-2026-09-30.md) on the V171 dialogue. **`mass-driver-v172-dialogue-polish`** was built and selected on September 30, 2026. Run [PLAY_MASS_DRIVER.cmd](../PLAY_MASS_DRIVER.cmd). Fresh in-game acceptance remains pending.

## Installed changes

The installation changes **13 dialogue blocks across eight authored files** and removes **16 pages** from the complete stored transcript. The transcript includes optional and dormant text; its page count is not the mandatory route's reading load.

| Location | Change |
| --- | --- |
| Opening arrival | Emeralda says "Then let's get the launcher ready!" after Elly explains the mission; Elly's Central Control destination is shorter. |
| Defense Archive missing-code messages | Facility software requests the directive number or four authority codes, names the relevant register, and directs the player to the east service stairs. |
| Saved director's briefing | A two-page record retains the Adviser's Office request for increased readiness and the unchanged shelter capacity. |
| Launch recall record | A two-page record retains Directive 0320, the refused recall, confirmed strategic release, lost command link, and sealed reserve magazines. |
| Optional engineering and shipping records | Four blocks use fewer page breaks. The Stores reply still requests the missing instrument connections; dates, correspondence, and the survey carrier remain. |
| Final shift | "Bank Four banks opened" becomes "Bank Four opened." Mira's messages and the uncertain answer remain. |
| Video Disk news | Removes the invented twelve-year birth-rate interval and changes exactly three wealthy districts to several; the collapse report and separate emergency recording remain. |
| Completed launch | "No further capsule available" describes the expended mission capsule precisely. |

The installed words and original comparisons are recorded in the [source change report](../work/mass-driver-dialogue-polish-20260930/source-changes.json). The baseline copies and native-layout checks are in [the evidence directory](../work/mass-driver-dialogue-polish-20260930/).

## Preserved dialogue and gameplay

Protected Central Control blocks **21-34 and 36**, including the Miang memory, its entry/return, and dormant blocks, retain their exact text, encoded payloads, and dimensions. The Guardian exchange, Citan's off-screen Gear delivery and practical launch work, Elly's hopeful wish, and Gear recovery are preserved. The target link remains disconnected, and reserve rockets and missiles remain available for the original game's later events.

No script behavior, actors, cameras, timing, sound, geometry, encounters, rewards, menus, clue values, or persistent state is changed. Central Control's dialogue-dependent build fingerprints are refreshed; its script and every other builder byte remain fixed.

## Validation

- **394 tests run: 393 passed, one existing skip.** The [passing profile log](../work/mass-driver-dialogue-polish-20260930/tests-final.log) covers the required module and shared checks, including native text layout, menu dispatch, persistent-state interactions, and scene protections. Current prose and its derived binary snapshots were refreshed; protected and script fingerprints were retained.
- The [final source and disc audit](../work/mass-driver-dialogue-polish-20260930/audit.json) verifies **all 166 replacement resources** against the final BIN. Exactly **eight field bundles** differ from V171; the other **158 replacements** are identical.
- All **33 active authored sources** agree with staged and final-disc dialogue. All **297 decompressed field components** agree, and every non-dialogue field component remains identical to V171. All eight Central Control non-dialogue components, including its 3,593-byte script (`39f7a1cf08cbe8721ac39fa471a29b69a9e5ca1a944948c88cbd0f6bda73c020`), are unchanged.
- **5,905 distinct sectors** pass EDC/ECC integrity verification. The shorter records change resource packing; relocated payloads were compared by logical file identity. Raw differences are confined to the eight dialogue fields, verified resource relocations, and the corresponding primary/embedded file tables. The main executable is byte-identical outside its exact file-table mirror.
- The [compiled transcript](mass-driver-dialogue-v172.md) contains **184 blocks / 423 pages / 28,112 dialogue bytes** across 33 fields, compared with V171's 439 pages / 28,887 bytes. The [export log](../work/mass-driver-dialogue-polish-20260930/transcript-export.log) confirms every active source recompiles exactly to the selected stage.
- [Launcher verification](../work/mass-driver-dialogue-polish-20260930/launch-check.log) passed, and [registry verification](../work/mass-driver-dialogue-polish-20260930/status-verify.log) reports this release current. The emulator was not opened. Prior builds, other chapter selections, saves, and memory cards were preserved.

## Build identity

- [Selected CUE](../builds/mass_driver/mass-driver-v172-dialogue-polish/Xenogears_Reimagined_mass_driver_mass-driver-v172-dialogue-polish_CD2.cue)
- [Build receipt](../builds/mass_driver/mass-driver-v172-dialogue-polish/project-build.json) and [build log](../work/mass-driver-dialogue-polish-20260930/build.log)
- BIN size: **696,137,904 bytes**
- BIN SHA-256: `95315fe3f9733db452e8b525ef40fc288dd14902f2d2dd667bdc65287a3e265c`
- CUE SHA-256: `8ebbf49fe2e9a32b07bb891bb0dfb597e9b9b89232a44b8814a69af48159a030`
- Stage manifest SHA-256: `dcb82349ad830446e7881d8baa810ef9d723b8f6255b4612e0ebc1858d51f0c5`

## In-game acceptance

Use [PLAY_MASS_DRIVER.cmd](../PLAY_MASS_DRIVER.cmd), which now selects V172. A fresh game is the cleanest way to assess the opening and complete route; old savestates may retain resident dialogue from an earlier build. Check the missing-code windows, optional record pages, Guardian, protected memory, launch, and Gear recovery for pacing and presentation.

Runtime acceptance remains **untested**. This installation does not declare the dungeon content-locked or publicly packaged.
