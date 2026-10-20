# Mass Driver V171: dialogue and terminal overhaul

The approved writing is installed in **`mass-driver-v171-dialogue`**, built and selected on September 29, 2026. Run [PLAY_MASS_DRIVER.cmd](../PLAY_MASS_DRIVER.cmd). This is a development candidate awaiting fresh in-game acceptance of the writing and pagination.

## Installed changes

- Replaced **73 dialogue blocks across 23 authored files**. The opening, Guardian encounter, Citan's launch exchange, mission-status messages, and Gear recovery now use the reviewed prose.
- The opening establishes Citan bringing Vierge and Crescens through an exterior hangar entrance, and the hangar dialogue acknowledges his delivery. It is an off-screen arrangement; this revision adds no exterior map route or delivery animation. The personnel lift and hallways are not the delivery route.
- The computer inside the stationary train now displays a saved shift timetable, passenger instructions, and cancelled-service notices. Its timetable fits together on one page. The shop offers its actual supplies and Gear parts.
- Rewrote terminals around their physical roles: staff attendance, pressure-lock duty, power distribution, load and cooling tests, guidance files, dispatch, inventories, access controls, safety records, and magazine handling. The unrelated Kim dossier was removed; the civilian-probe/Mira material is in Civil Payload Stores.
- Kept directive **0320** and codes **A-2, B-5, C-8, D-4** at the beginning of their clue summaries. Historical records are labeled. Optional records remain optional, and menu choices retain their dispatch order.
- Wrapped the revised text to native window limits, preserving the approved words. Four awkward page breaks were corrected. The robot's exit window grew from two rows to three to fit its farewell. Menu dimensions and choice rows remain intact.

Read the [exact compiled transcript](mass-driver-dialogue-v171.md) or the [editorial reading draft](research/mass-driver-dialogue-redraft-2026-09-28.md). The transcript includes optional and dormant text; its total page count is not the mandatory reading load.

## Protection and validation

The Miang memory, its entry and return, and its scene data are unchanged. Protected Central Control blocks **21–34 and 36** retain their text, encoded payloads, and dimensions. All eight Central non-dialogue components match V170, including the unchanged 3,593-byte script (`39f7a1cf08cbe8721ac39fa471a29b69a9e5ca1a944948c88cbd0f6bda73c020`).

- **394 tests run: 392 passed, 2 existing skips.** The [passing log](../work/mass-driver-dialogue-20260929/tests-final.log) covers the complete required profile and shared tests. Old prose and dialogue-dependent binary expectations were updated; native assets, interactions, menus, progression, and scene protections remain checked.
- All **166 replacement resources** match the final BIN. All **33 authored sources** match both staged and disc dialogue; all **297 decompressed field components** match. **5,895 distinct sectors** passed EDC/ECC integrity verification. See the [comprehensive disc audit](../work/mass-driver-dialogue-20260929/disc-audit.json).
- Exactly the **23 intended field bundles** differ from V170; the other **143 resources** are unchanged. Every non-dialogue component in the affected fields is unchanged. The [independent focused audit](../work/mass-driver-dialogue-20260929/final-disc-dialogue-audit.json) checks the final BIN against the installed sources and anchors protected text and components directly to V170.
- The transcript contains **184 blocks / 439 pages / 28,887 compiled dialogue bytes** across 33 fields. The 73 replacement blocks account for 283 pages.
- [Launch identity verification](../work/mass-driver-dialogue-20260929/launch-check.log) passed. The selected release is V171; the emulator was not opened. Other chapter selections, prior builds, saves, and memory cards were preserved.

## Build identity

- [Selected CUE](../builds/mass_driver/mass-driver-v171-dialogue/Xenogears_Reimagined_mass_driver_mass-driver-v171-dialogue_CD2.cue)
- [Build receipt](../builds/mass_driver/mass-driver-v171-dialogue/project-build.json)
- BIN size: **696,142,608 bytes**
- BIN SHA-256: `f6de018286898222bbcb80d7a8d9bc8265285e799f1fe8b19916dfc87e0bea80`
- CUE SHA-256: `b2ca6b5860c298ae0cad9fc1350b3c20ba984886d1431a6b89aebc4dea5a3940`
- Stage manifest SHA-256: `e41697bff936d0ff09fafba5b5a88d5fc41a326c597ebf5135303d38d1219db0`

The [installation report](../work/mass-driver-dialogue-20260929/install-report.json) records exact source identities and changes. The pre-installation snapshot and audit tools are in [the working evidence directory](../work/mass-driver-dialogue-20260929/).

## In-game acceptance

Start a fresh game through the launcher to assess the opening and complete writing in order. Old emulator savestates can retain resident scripts and dialogue from the previous build. Check the train timetable, code summaries and optional records, Guardian dialogue, the protected finale, Citan's launch exchange, and Gear recovery. Assess voice, clarity, reading pace, page transitions, and held input alongside the existing direct-route and exploration checks.

Runtime status remains **untested** for this candidate. Automated verification does not establish visual pacing, voice fidelity, or a completed emulator playthrough. Public patch packaging and a declaration of content completion remain separate from this text installation.
