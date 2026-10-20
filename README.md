# Mass Driver 1.0 corresponding source

[Download all sources](https://github.com/Project-Benjamin/Mass-Driver/archive/refs/tags/source-mass-driver-1.0.zip).

These files are for developers. Players only need [Mass_Driver_Setup.exe](https://github.com/Project-Benjamin/Mass-Driver/releases/download/mass-driver-1.0/Mass_Driver_Setup.exe).

- `Xenogears_Reimagined_Source_V176.zip`: dungeon builder, dialogue, project code, tests, selected authored art and external-input inventory.
- `Mass_Driver_Player_Source_V176.zip`: native Windows installer and launcher.
- `Xenogears_Mass_Driver_Patcher_Source.zip`: native patcher, build scripts and dependency provenance/notices.
- `emulator/`: exact DuckStation v0.1-7371 source and matching dependency source archives, upstream build instructions, licenses and provenance. Start with `emulator/README_SOURCE.md`.

Preserve each component's licenses and notices. `SHA256SUMS.txt` identifies every source file. The game, BIOS, Microsoft binaries and user data are excluded. The full dungeon rebuild requires the external extracted inputs documented in the project source, including its captured initial-state fixture; a clean disc alone is insufficient.

The three source companions and all 26 emulator-source components are byte-for-byte identical to those originally supplied with Mass Driver 1.0 (V176). The emulator's former outer ZIP is expanded one level here; no component was modified. This source tag provides free public source access alongside the binary download under the applicable component licenses, including GPLv3 section 6(d).
