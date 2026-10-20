# Mass Driver V173 release candidate

**`mass-driver-v173-release-candidate-20261019`** was built and selected on October 19, 2026. It adds the requested random battles, restores Elly's captured starting level, and makes two final adjustments to Emeralda's voice. Use [PLAY_MASS_DRIVER.cmd](../PLAY_MASS_DRIVER.cmd), which verifies the selected release before launch. **A complete fresh playthrough and native patcher GUI acceptance remain pending.** Automated clean-retail reconstruction checks pass.

## Changes from V172

| Area | Installed behavior |
| --- | --- |
| Random battles | Fields 727, 372, 723, 375, 387, and 726 use three verified native Zeboim on-foot formations. Shellbelle and Hammerhead retain their native enemy data and models. Escape is allowed. |
| Quiet rooms | Random encounters are disabled in the other 27 fields, including archive, shop/save, story, Guardian, magazine, and control rooms. All unused random formation weights are zero. |
| Guardian | Its fixed encounter remains unchanged. Its formation is excluded from random selection. |
| Starting party | Elly starts at level 52 instead of the former level 70 test override. Her captured HP 335 / EP 66 and Emeralda's level 49 / HP 357 / EP 74 remain. Starting money, items, equipment, and the existing learned-command flags are unchanged from V172. |
| Opening | Emeralda says, "Emeralda ready! Come on, Elly!" after Elly explains the mission. |
| Recovery | Emeralda says, "Elly! Emeralda want to tell Fei!" Elly's existing reply remains. |

The [encounter policy](../modules/mass_driver/encounters.py) sets a window of 900 movement-input ticks with one native timer entry. This is a static configuration; encounter frequency, difficulty, and rewards still require a full route test with the actual two-character party. Elly retains six learned on-foot deathblows and six Gear deathblows; these flags do not mean every on-foot command is unlocked.

The [complete transcript](mass-driver-dialogue-v173.md) contains **184 blocks / 423 pages / 28,113 dialogue bytes across 33 active fields**. Its optional and dormant appendices are marked separately. Stored dialogue totals do not measure the mandatory route's reading time.

## Preserved story and scenes

The mission, authorization clues, optional records, Mira exchange, and ending remain. Citan still handles the off-screen Gear delivery and practical launch work; Elly uses Vierge and Emeralda uses Crescens. Gear recovery remains part of the route. The target link remains disconnected, and the reserve rockets and missiles remain available for the original game's later events.

Protected Central Control blocks **21–34 and 36**, including the Miang memory and its boundaries, retain their exact dialogue. Its script, actors, cameras, timing, and sound remain unchanged. Central Control's encounter data changes only to disable random selection in the room. The fixed Guardian scene is preserved.

The [voice validation](../work/mass-driver-release-20261019/voice-validation.json) checks the two revised dialogue blocks, their native wrapping and control streams, all other blocks in those files, and the protected Central Control dialogue. The broader [static presentation audit](../work/mass-driver-release-20261019/voice-static-audit.json) records the installed text review.

## Foundation and build identity

This candidate uses an explicitly rebuilt **Perfect Works 0.10.2** Disc 2 foundation. The historical source image could not be recovered byte for byte. The new image is recorded under its own identity; it does not inherit the old hash.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| Verified clean US retail Disc 2 | 688,700,880 | `5eab85c683d4d7087d345b587472db9c44df29b35ce66553c2626d26018b947e` |
| Rebuilt PW 0.10.2 foundation used by V173 | 688,456,272 | `7585d2ebadab82f9d982d871e05c02a9fb930167e8fe85d249c266a0e1885d8e` |
| Unavailable historical foundation | 688,456,272 | `505f4ac038ca40db5675d37717f261cd016ef14df39b1d4b713ae1e51ec496f2` |

The [recovery report](../work/mass-driver-release-20261019/upstream/base-recovery-report.json) records the official 0.10.2 story-script patch and the official no-deathblow-levels transformation used to create the rebuilt foundation. The supplied 0.11.4 distribution provided standalone patching tools only. No 0.11.4 game patch, translation, executable, or balance was applied.

- [Selected CUE](../builds/mass_driver/mass-driver-v173-release-candidate-20261019/Xenogears_Reimagined_mass_driver_mass-driver-v173-release-candidate-20261019_CD2.cue)
- [Build receipt](../builds/mass_driver/mass-driver-v173-release-candidate-20261019/project-build.json) and [consumed-input inventory](../builds/mass_driver/mass-driver-v173-release-candidate-20261019/consumed-inputs.json)
- BIN: **696,137,904 bytes**, SHA-256 `d78294b5db653231bde3d29ff1acd3509af91cef2a4aefbac13f737e674193b1`
- CUE SHA-256: `3211a87782f61736bb88d3519c0f1d54e2cae21a90bdf21a924fa738ec1eaad0`
- Stage manifest SHA-256: `edf2955c96be2b23fae24cb24826cb49e384ad0ce89a553f934f83904fbf8693`
- Current source snapshot SHA-256: `4d9e2605cb11257e340eadc3a0b566abc6bfb458544716282261ca945e7e9bf5`

## Distribution

A separate [private all-in-one installer](mass-driver-private-installer.md) now includes the game, locally supplied BIOS, runtime and required Microsoft dependencies. Its extraction, repair, reproducibility and local native startup checks pass. It is unsigned and has not been cleared for public redistribution. The patch packages below remain separate artifacts.

| Artifact | Purpose |
| --- | --- |
| [Xenogears_Mass_Driver.exe](../dist/mass-driver-v173-release-candidate-20261019/Xenogears_Mass_Driver.exe) | Primary single-download Windows patcher; patch, manifest, CUE template, documentation, and notices are embedded. |
| [Xenogears_Mass_Driver.zip](../dist/mass-driver-v173-release-candidate-20261019/portable/Xenogears_Mass_Driver.zip) | Portable fallback with the executable and separate data folder. |
| [Project source companion](../dist/mass-driver-v173-release-candidate-20261019/project-source/Xenogears_Reimagined_Source_V173.zip) | Canonical game builder, dialogue, shared tools, selected authored assets, tests, and documentation. |
| [Patcher source companion](../dist/mass-driver-v173-release-candidate-20261019/patcher-source/Xenogears_Mass_Driver_Patcher_Source.zip) | Windows patcher source, exact release manifest, build scripts, and dependency notices. |

Both player packages require the clean US retail Disc 2 BIN identified above and a separately supplied emulator/BIOS. Neither contains a game image, emulator, BIOS, card, or save. The single EXE defaults generated game files to `%LOCALAPPDATA%/Xenogears Mass Driver/Mass Driver Game`; **Choose game location** selects another parent for the session. The ZIP defaults to `Mass Driver Game` beside its executable.

The EXE is unsigned. Published SHA-256 identities are:

- Single EXE, **10,411,008 bytes**: `a09d79ab8b3c2b87477ed5937264e4f419745ed62e656f76c7601a5a281cd3e3`
- Portable ZIP, **7,532,698 bytes**: `f212c93adc424a2dfe4270ae7ef7bacc09e6374aadafbaa4066662d0a64e2493`
- Patcher source ZIP, **99,596 bytes**: `03ffa8009f0d1c3fd7f9bb1e5f9160e11aba99222b875c078dcb76f14f630f0a`

The EXE and ZIP reproduce the candidate BIN from the supported retail source and rebuild byte-identically from identical release inputs. Their automated checks cover integrity, wrong-input rejection, output preservation, cancellation/retry, and exact reconstruction. The single EXE extracts verified data and notices to its per-user cache, with no decoder/helper executable. These checks do not establish native GUI or gameplay acceptance. See [source scope and external requirements](source-distribution.md) before rebuilding either companion.

## Validation and remaining acceptance

**406 tests ran: 404 passed, two existing skips, in 24.715 seconds.** The [latest profile log](../work/mass-driver-release-20261019/tests-build-fix.log) covers module and shared checks, dialogue layout, menu dispatch, persistent state, all 33 fields' encounter policy, native battle resources, and the protected scene. Historical fingerprints remain separate from current-source snapshots. The transcript exporter verified every active authored source against its staged dialogue.

The [candidate static audit](../work/mass-driver-release-20261019/candidate-static-audit.json) verifies **all 166 replacements** in the final BIN and **all 297 decompressed components across 33 fields**. It also verifies **3,556 unreplaced resource payloads** unchanged from the rebuilt foundation. Native directories remain unchanged, and main-executable changes are confined to its exact file-table mirror. **5,905 Mode 2 sectors** covering replacement extents, the file table, and its executable mirror pass EDC/ECC checks; this is not a scan of every untouched movie sector. Every Central Control formation and protected scene component remains unchanged; only its random encounter weights differ.

The remaining release gate is a fresh native playthrough: opening and navigation, authorization and optional records, random battle frequency and balance, shop/save and reload, fixed Guardian, protected memory, launch, Gear recovery, and completion/return. The patcher also needs its native GUI build/retry/play flow accepted against the documented retail input. Automated clean-retail reconstruction has passed. Build and static checks do not establish the remaining native results. See the [finishing status](../modules/mass_driver/docs/finishing-status.md) for the current acceptance record and the [source distribution guide](source-distribution.md) for companion scope.
