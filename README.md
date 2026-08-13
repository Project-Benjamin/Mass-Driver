# Xenogears Mass Driver

This repository contains the Windows source and public build contract for the
Xenogears Mass Driver V161 one-app playtest package.

## Download and use

> [!WARNING]
> This unsigned V161.3 playtest currently has one VirusTotal detection:
> Microsoft reports `Trojan:Win32/Wacatac.B!ml`, while 70 supported engines
> report undetected. Microsoft false-positive review
> `5a76bd2d-caa4-47f4-a6ed-7c2d6139b169` is pending. If Defender blocks the
> file, do not disable protection or add an exclusion; wait for Microsoft's
> corrected determination.

Download the current package from the
[V161.3 release](https://github.com/Project-Benjamin/Mass-Driver/releases/tag/v161.3).

1. Extract the complete ZIP to a writable folder.
2. Open `Xenogears_Mass_Driver.exe`. It is the only app you need to open.
3. Browse to an unmodified USA Xenogears Disc 2 raw BIN.
4. Select **Build game**, then **Play**.

The app does not include Xenogears, an emulator, or a BIOS. It never changes
the source BIN and does not save application or emulator settings. Emulator
detection and selection are optional until you select **Play**.

The app is unsigned, so Windows SmartScreen can show a reputation warning. If
security software reports a threat, report the exact filename, SHA-256 value,
and detection name instead of adding an exclusion.

## Source layout

- `source/main.cpp` implements the manifest-driven patching and unified UI.
- `source/xdelta_decoder.cpp` applies the VCDIFF patch inside the app.
- `source/emulator.cpp` detects or launches a user-selected emulator.
- `source/build.ps1` produces the deterministic package folder and ZIP.
- `source/verify.ps1` validates archive safety and functional behavior.
- `source/release_manifest.json` pins every accepted input and output.
- `source/BUILDING.md` records the complete rebuild procedure.

Patch data, executables, disc images, emulator files, and BIOS files are
intentionally not committed. The release ZIP is distributed only as a GitHub
Release asset.

## Rebuilding the package

The app compiles a decode-only xdelta 3.2.0 core directly into the executable.
There is no bundled xdelta executable and patching does not start a helper
process.

Obtain the exact V161.3 patch from the release ZIP and a clean xdelta checkout
at the pinned commit, then run:

```powershell
git clone https://github.com/jmacd/xdelta.git .\external\xdelta
git -C .\external\xdelta checkout --detach ff322e592383227b0d65ddfde7e0e5bbc504dc15

.\source\build.ps1 `
  -PatchPath .\external\Xenogears_Mass_Driver_v161_USA_Disc2.xdelta `
  -XdeltaSourceDirectory .\external\xdelta
```

The build verifies both external inputs before use and writes generated output
under the ignored `dist` directory. See `source/BUILDING.md` for the exact
toolchain used for the published bytes.

Static verification:

```powershell
.\source\verify.ps1 -SkipDynamic
```

For the full functional test, also pass a privately supplied clean Disc 2 BIN
with `-SourceBin`. No disc image belongs in this repository.
