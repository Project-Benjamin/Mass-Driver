# Mass Driver 1.0

An unofficial Xenogears dungeon restoration featuring Elly and Emeralda,
exploration, random battles, the Guardian, archive records and minigames, and a
complete capsule-launch ending. This release uses content revision **V176**.

## Download and play

**[Download Mass_Driver_Setup.exe](https://github.com/Project-Benjamin/Mass-Driver/releases/download/mass-driver-1.0/Mass_Driver_Setup.exe)**

1. Run the installer on Windows 10/11 x64, choose **Install**, then **Play**.
2. When Explorer opens, select your **untouched USA Xenogears Disc 2 BIN**, dumped
   from your own disc.
3. Select a supported **512 KB USA PlayStation BIOS dump** from your own console.
4. Let the app build its separate game copy. Choose **New Game** to begin.

Later launches remember setup. No Python, compiler, manual patching, or separate
emulator installation is required. The original disc and BIOS files remain
unchanged. Missing inputs open file pickers. Invalid inputs produce an explanation; choose Play again to select another file.

**The download contains no Xenogears disc image or PlayStation BIOS.** You must
supply both through sources you are entitled to use. Do not share a populated
installation: it contains the game and BIOS you supplied. This fan project is
unaffiliated with Square Enix, Sony or the emulator's developers.

[All release downloads and checksums](https://github.com/Project-Benjamin/Mass-Driver/releases/tag/mass-driver-1.0)
Ã‚Â· [Player guide](project/docs/mass-driver-public-player.md)
Ã‚Â· [Test coverage and limits](project/docs/mass-driver-release-qa.md)

## Controls and saves

Arrows move; **K** confirms/Cross, **L** cancels/Circle, **J** is Square,
**I** is Triangle, Enter is Start, Backspace is Select, Q/E are L1/R1 and 1/3 are
L2/R2. F11 toggles fullscreen; Escape opens the emulator pause menu. Standard SDL
gamepad bindings are supplied; change them in the emulator's controller settings
if needed. Physical controller hardware was not tested in this release audit.

Save at a memory cube and choose **Continue** to reload. Keep a backup of
**UserData**, which holds cards, settings and your BIOS copy. Reinstall and
repair preserve it. Use in-game saves across game revisions; emulator states may
contain an older revision's loaded scripts. An older candidate's malformed save
is not migrated by reinstalling the player.

## Release checks

A fresh **V176 New Game-to-ending run with Sony BIOS passed**, including Guardian
victory, the protected memory, full launch movie, Gear recovery and world-map
movement. Separate V175 runs completed Guardian defeat/retry, ending,
Gear recovery, cold saves and completed revisits. Encounters, shops, puzzles,
optional records, archive video and both minigames received separate native
checks. V176 changes four Missile Command input-mask bytes and received fresh
field/control and high-score save checks. The profile suite ran **426 tests:
424 passed, two existing skips**. Exact compiled-content comparison identifies
which prior gameplay results carry forward. The linked QA record gives the
version and method for each scope.

The compiled public installer was checked for exact reconstruction, missing and
invalid inputs, cancellation, retry, repair, preserved data, native startup and
remembered setup. Testing used an existing Windows x64 PC; a clean Windows VM
and every driver/controller configuration were not tested. The installer is
**unsigned**. `SHA256SUMS.txt` identifies the release files; it is not a code
signature.

If Microsoft Visual C++ runtime components are missing, Play offers Microsoft's
official installer, verifies its signature and publisher, and opens standard
Microsoft setup. Complete it and run Play again. Our download contains no
Microsoft runtime DLLs. The download/signature checks were tested; Microsoft's
installer was not executed during this audit.

## Source and notices

| Download | Contents |
| --- | --- |
| `Xenogears_Reimagined_Source_V176.zip` | Canonical project, dungeon builder, dialogue, tests, selected authored art, public configuration and input inventory |
| `Mass_Driver_Player_Source_V176.zip` | Native installer/launcher and preparation/verification scripts |
| `Xenogears_Mass_Driver_Patcher_Source.zip` | Native patcher, build scripts and dependency provenance |
| `DuckStation_7371_Corresponding_Source.zip` | Exact GPL-era emulator source, matching dependency sources, upstream build instructions and licenses |

The source is also browsable under [project](project/). Player and patcher code
is in `project/tools/mass_driver_standalone` and
`project/tools/mass_driver_portable`. Read the
[source distribution guide](project/docs/source-distribution.md) before building.
The complete project build requires external extracted game inputs, including
a captured initial-state fixture; it is not a turnkey source rebuild from a
clean disc alone. None of those game-data inputs are included in the source.

The player contains unchanged GPL-era **DuckStation v0.1-7371**, source commit
`b2577ef8bdaae99840874b6dae8146f0316357b4`. Matching source is available next to
the binary without charge. Component licenses, dependency notices and Perfect
Works provenance are preserved. These licenses do not grant rights to the
underlying Xenogears game or Sony firmware. No endorsement is implied.

## Earlier Soylent demo

The previous **Xenogears Cut Content Patcher / Surface Soylent System demo**
remains available in the [original patcher release](https://github.com/Project-Benjamin/Mass-Driver/releases/tag/patcher).
Its [earlier README](release/history/SOYLENT_DEMO_README.md), `source/` tree and
`xenogears_modding_starter/` remain preserved. That demo is separate from the
Mass Driver 1.0 Windows player.
