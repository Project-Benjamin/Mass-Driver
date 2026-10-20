# Mass Driver V174 release candidate

Historical candidate: superseded by [V176](mass-driver-v176.md). V174's early
387-to-725 save entry had a confirmed fault repaired in V175. Use the current
[public player](mass-driver-public-player.md), not this candidate's installer.

**`mass-driver-v174-release-candidate-20261019`** is the selected build. Use [PLAY_MASS_DRIVER.cmd](../PLAY_MASS_DRIVER.cmd) for the verified project launch. This candidate repairs two issues found during V173 gameplay acceptance; full gameplay acceptance remains in progress.

## Repairs

- The standalone Mass Driver title uses the original **New Game / Continue / Sound** menu. Its New Game disc check accepts Disc 2. Continue uses the native saved-field path without reseeding the party or mission state. Other profiles retain their existing selector behavior.
- The authorized north lift activates on a normal straight approach. Its entry threshold changes from Z274 to Z270, and its native proximity reach changes from 34 to 38. The horizontal polling aperture remains unchanged; the return spawn remains outside the trigger. Native approach acceptance is pending.

The title repair addresses a confirmed V173 blocker: an ordinary game save could be written, but the earlier demo title disabled access to Continue. V173 installers are historical candidates and must not be described as final releases.

All V173 dialogue, encounter tables, starting party data, fixed Guardian data and protected Central Control content are preserved. Only three prepared resources change: title resources **2593/2599**, and field 376 resource **1358**. The latter changes exactly three script bytes; all other components of that field and the other 163 prepared replacements remain byte-identical. The [V173 transcript](mass-driver-dialogue-v173.md) remains the exact dialogue transcript for V174.

## Build identity and checks

**417 tests ran: 415 passed and two existing skips.** Eleven new regressions cover native title/Continue dispatch and the captured straight-approach lift position, authorization, return spawn and exact script changes. The successful profile run took 28.551 seconds. No build or test result alone establishes native save loading or a complete playthrough.

- [Build receipt](../builds/mass_driver/mass-driver-v174-release-candidate-20261019/project-build.json)
- [Selected CUE](../builds/mass_driver/mass-driver-v174-release-candidate-20261019/Xenogears_Reimagined_mass_driver_mass-driver-v174-release-candidate-20261019_CD2.cue)
- BIN: **696,140,256 bytes**, SHA-256 `28e712461ccababebb2ce654a27fc0004ac51a1b5a4615158b6e2d568d052ade`
- CUE SHA-256: `eaa42ee247bde96f6ff5301973491330a1acdda1c210d77921d39053fb4282db`
- Stage manifest SHA-256: `a4b61b46533719df0e947a7428defadc8119ab6d439f61f9e06b346a2175e0f5`
- Source snapshot SHA-256: `4488ce0f158155aca4a15c34f83b6e33a2f470dbd4212615089507e4198690c4`

The [final-disc static audit](../work/mass-driver-release-20261019/v174-candidate-static-audit.json) verifies every replacement, 3,556 unchanged unreplaced payloads, the executable's exact file-table mirror, 5,906 Mode 2 sectors, and the narrow V173-to-V174 changes. The clean retail and rebuilt Perfect Works 0.10.2 foundation identities remain those documented in [V173 notes](mass-driver-v173.md#foundation-and-build-identity). The supplied Perfect Works 0.11.4 game patch has not been applied.

## Runtime and packaging acceptance

V173 testing established the opening, transit/shop access, a random battle victory and Escape return, an ordinary memory-cube save, Guidance and material records, auxiliary and accelerator power, authorization, and Guardian boarding. Those observations remain attributed to V173. Its blocked Continue and unreliable straight lift approach are the reason for V174.

V174 requires fresh cold Continue, native resave/reload, the straight lift approach, Guardian completion, the protected memory, launch, recovery and completed revisits. Tests must load V174's new field script rather than reuse an older emulator state already inside field 376.

The [private all-in-one installer](mass-driver-private-installer.md) is being rebuilt for this candidate. It contains the game, locally supplied BIOS, runtime and required Microsoft dependencies, and needs separate V174 extraction/startup/save checks. It is unsigned and has not been cleared for public redistribution. Patch-only packages remain separate artifacts.
