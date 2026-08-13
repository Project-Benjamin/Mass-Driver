# Xenogears Mass Driver

This repository contains the Windows source and public build contract for the
Xenogears Mass Driver V161 one-app playtest package.

## Download and use

Download the current package from the
[V161.2 release](https://github.com/Project-Benjamin/Mass-Driver/releases/tag/v161.2).

1. Extract the complete ZIP to a writable folder.
2. Open `Xenogears_Mass_Driver.exe`. It is the only app you'll need to open.
3. Browse to an unmodified USA Xenogears Disc 2 raw BIN.
4. Select **Build game**, then **Play**.

The app does not include Xenogears, an emulator, or a BIOS. It never changes
the source BIN and does not save application or emulator settings. The
emulator helpers are optional.

The executable and xdelta3 decoder are currently unsigned, so Windows
SmartScreen can show a reputation warning. If security software reports a
threat, report the exact filename, SHA-256 value, and detection name instead
of adding an exclusion.

## Source layout

- `source/main.cpp` implements the manifest-driven patching and unified UI.
- `source/emulator.cpp` detects or launches a user-selected emulator.
- `source/build.ps1` produces the deterministic package folder and ZIP.
- `source/verify.ps1` validates archive safety and functional behavior.
- `source/release_manifest.json` pins every accepted input and output.

Patch data, executables, and game images are intentionally not committed.
Release binaries are distributed only as GitHub Release assets.

## Rebuilding the package

Requirements:

- 64-bit Windows 10 or Windows 11.
- Visual Studio C++ x64 Build Tools.
- The exact V161 `.xdelta` payload from the release package.
- The reviewed `xdelta3.exe` from the release package.

Place the two supplied files under an ignored `external` directory, then run:

```powershell
.\source\build.ps1 `
  -PatchPath .\external\Xenogears_Mass_Driver_v161_USA_Disc2.xdelta `
  -XdeltaPath .\external\xdelta3.exe
```

The script verifies both external inputs against the release manifest before
using them. It writes generated output under the ignored `dist` directory.

Static verification:

```powershell
.\source\verify.ps1 -SkipDynamic
```

For the full functional test, also pass a privately supplied clean Disc 2 BIN
with `-SourceBin`. No disc image belongs in this repository.
