# Mass Driver V169: research implementation

V169 applies the [five-pass research](research/xenogears-five-pass-2026-09-16/README.md) to the current Mass Driver reconstruction. It is a development candidate awaiting fresh gameplay acceptance. The new material is authored reconstruction, not recovered dialogue or proof of Square's plans for an omitted dungeon.

## Content and sequence changes

- The broadcast archive distinguishes the **6081 evening report** from the **6083 emergency recording**. Its report is shorter while preserving the relevant social conditions.
- Lena's final letter recalls the earlier probe conversation consistently. Mira's fate remains unknown.
- Emeralda asks to leave after reading about Kim; Elly follows her lead. Staff correspondence gives Mara and Lena more concrete responses to the facility's militarization.
- Aron's magazine record distinguishes restoring power from reconnecting the missiles' target link.
- Central Control's arrival and readiness exchanges are shorter and leave the final guidance check to Citan.
- The Guardian threat now appears before boarding. Each pilot's boarding text is followed by that pilot's mount operation before the next pilot and battle.
- After the launch cinematic, the party returns briefly to the existing Gear hall, acknowledges Citan going ahead, recovers Vierge and Crescens, and returns outside. This uses a guarded entry parameter and existing completion state, without another battle or required backtracking.

The [before/after review](mass-driver-dialogue-v169-changes.md) covers all nine changed authored files: sixteen revised blocks and one added block. The [complete transcript](mass-driver-dialogue-v169.md) inventories the matching compiled build, including optional and dormant text.

The intended interior remains exploration-led with one fixed Guardian encounter. Existing exterior encounters, preparation facilities, rewards, optional activities, and combat statistics retain their prior behavior. The facility remains intact for its later role in the released story.

## Protected scene

Central Control edits are limited to dialogue blocks **0 and 12**. Memory blocks **22–31 and 36**, entry **21**, return **32**, and dormant **33–34** remain unchanged. No dormant explanation is activated.

The independent baseline comparison checks every protected compiled dialogue block and every non-dialogue component. The Central Control script remains **3,593 bytes**, SHA-256 `39f7a1cf08cbe8721ac39fa471a29b69a9e5ca1a944948c88cbd0f6bda73c020`. Its actor, camera, timing, sound, graphics, and scene transition instructions remain identical. Packed bundle offsets necessarily change because the two unprotected dialogue blocks are shorter.

## Build and verification

Original research release: `mass-driver-research-v169`. The selected release is **`mass-driver-v169-local-emulator`**, rebuilt after pointing the launcher at the current account's DuckStation installation. Its BIN is byte-identical to both the original V169 and `mass-driver-v169-organized`; see the [cleanup verification](directory-organization-2026-09-16.md) and [emulator repair record](../work/emulator-repair-20260916/repair.json). The current installation's libpng and Qt DLLs load successfully; emulator settings and saves were preserved. Launch it with [PLAY_MASS_DRIVER.cmd](../PLAY_MASS_DRIVER.cmd). The evidence and CUE identity below describe the original research release; earlier builds are retained.

The module's [requirements](../modules/mass_driver/requirements.txt) record the Python packages used. The launcher prefers the project's `.venv`; `project.local.json` now points at the matching verified source discs and emulator on this machine. Source-disc hashes were checked before restoring those paths.

Verification completed on 2026-09-16:

- The canonical Mass Driver dependency test suite ran **384 tests: 382 passed, 2 skipped**, zero failures or errors. The existing frozen V161 audit skips deliberately; the Windows symlink test skips because symlink creation is unavailable. The final run used the exact `shared.project_registry.test_plan` dependency closure with verbose output.
- The full build completed and was activated. The build receipt records **V169** and the exact module, shared-tool, donor, and extracted-input identities.
- All **33 active authored sources** recompile byte-for-byte to the staged and final-disc dialogue: **181 blocks / 434 pages / 29,884 bytes**. These totals include optional and dormant text, not one playthrough's required reading.
- All **166 replacement payloads** match the final BIN; all **297 unpacked field components** match staging.
- All **5,877 replacement sectors**, plus **19 filesystem/header/boot sectors**, pass Mode2/Form1 EDC/ECC validation. The native publisher/title boot signature also matches.
- The independent protected-scene comparison passed with ordinary build guards enabled. The final-disc audit separately verifies protected dialogue and matches the staged field components to disc.
- The audit verified **146 source files**, **358 consumed inputs**, and **36 recorded outputs**, as well as the source-disc and native-tool identities.
- `project.py play mass_driver --check-only` verified the selected V169 media and launcher identity. Gameplay status remains **untested**; this check did not open the emulator.

Evidence: [test log](../work/mass_driver_v169_tests_final_verbose.log), [protected-scene audit](../work/mass_driver_v169_protected_audit.json), [final-disc audit](../work/mass_driver_v169_audit.json), [build receipt](../builds/mass_driver/mass-driver-research-v169/project-build.json), [launcher check](../work/mass_driver_v169_launch_check.log), and [source change inventory](../work/mass_driver_v169_change_inventory.json).

Build identity:

- [CUE](../builds/mass_driver/mass-driver-research-v169/Xenogears_Reimagined_mass_driver_mass-driver-research-v169_CD2.cue)
- BIN size: **696,144,960 bytes**
- BIN SHA-256: `9987579ac994758bb345a354a534f10a36b3934c349fe40d6a78db3f0a933001`
- CUE SHA-256: `294f633ec7cc6fd856082258a9c18d82bb8d76e8cf26e296efa4f0a7b7a732d8`
- Stage manifest SHA-256: `dcfe4243d9847d1498dd95fa0bed0d2c26ddec72b279e81bfdb324b9d732de8d`

## Gameplay acceptance still required

Automated and binary checks cannot establish camera quality, controller feel, visual fit, or combat balance. No fresh V169 emulator playthrough is claimed.

Use the verified launcher and start a **New Game**. Old savestates can restore old resident scripts and disc state. Check:

1. Clue summaries, Close/Read choices, repeated inspections, held input, and all five authorization entries.
2. Broadcast dates, reading pace, and dialogue-window fit.
3. Guardian approach, warning, individual boarding, battle, victory, and subsequent visits.
4. The uninterrupted protected memory and launch sequence.
5. Post-launch Gear recovery, Citan's absence, mounted exterior return, and normal later visits without repeating the recovery scene or boss.
6. The direct route, full exploration, optional-game exits, save/reload, preparation, and Guardian balance.

The [finishing status](../modules/mass_driver/docs/finishing-status.md) tracks what remains before declaring the dungeon content-complete. The user's release goal is to resolve content decisions before that declaration and reserve later updates for bug fixes.
