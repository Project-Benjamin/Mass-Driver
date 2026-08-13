# Xenogears Mass Driver

This repository contains the Windows patcher source and build contract for
Xenogears Mass Driver.

## Download and use

Download `Xenogears_Mass_Driver.zip` from this repository's Releases page.

1. Extract the complete ZIP to a writable folder.
2. Open `Xenogears_Mass_Driver.exe`.
3. Browse to an unmodified USA Xenogears Disc 2 raw BIN.
4. Select **Build game**, then **Play**.

The patcher does not include Xenogears, an emulator, or a BIOS. It reads but
never changes the source BIN. Emulator setup is optional until **Play** is
selected.

The executable is unsigned, so Windows SmartScreen or antivirus reputation
systems may show a warning. If security software reports a threat, do not
disable protection or add an exclusion. Report the exact filename, SHA-256
value, detection name, and security-definition version so it can be
investigated.

## Update-neutral design

The public filenames remain stable:

- `Xenogears_Mass_Driver.zip`
- `Xenogears_Mass_Driver/Xenogears_Mass_Driver.exe`
- `Mass Driver Game/Xenogears_Mass_Driver.cue`

The executable reads a strict data-only
`MassDriverData/patch_manifest.txt` at runtime. Publishing a future game
update changes the supplied patch, CUE template, sizes, and hashes; it does not
require a new patcher name or a displayed game-update number.

The runtime manifest cannot provide commands, programs, URLs, arguments, or
output paths. The patcher verifies the source disc, patch, CUE template, and
finished output before making the game available.

## Source layout

- `source/main.cpp` implements manifest-driven patching and the unified UI.
- `source/xdelta_decoder.cpp` applies VCDIFF inside the app.
- `source/emulator.cpp` detects or launches a user-selected emulator.
- `source/build.ps1` produces the deterministic package folder and ZIP.
- `source/verify.ps1` validates archive safety and functional behavior.
- `source/build_manifest.json` records the accepted inputs and outputs.
- `source/BUILDING.md` contains the complete rebuild procedure.

Patch data, executables, disc images, emulator files, and BIOS files are not
committed. The downloadable ZIP is distributed separately as a GitHub Release
asset.

## Rebuilding

The build compiles a decode-only xdelta core directly into the app from the
pinned Apache-licensed source commit. It does not bundle or run an xdelta
executable.

```powershell
git clone --branch release3_1_apl https://github.com/jmacd/xdelta.git .\external\xdelta
git -C .\external\xdelta checkout --detach 7508fd2a823443b1f0173ca361620f21d62a7d37

.\source\build.ps1 `
  -BuildManifest .\source\build_manifest.json `
  -PackageSource <folder-containing-the-license-inputs> `
  -PatchPath <path-to-Mass_Driver.xdelta> `
  -CuePath .\source\game.cue.template `
  -XdeltaSourceDirectory .\external\xdelta
```

The build verifies all external inputs and writes generated output under the
ignored `dist` directory. See `source/BUILDING.md` for requirements and
verification commands. No game disc image belongs in this repository.
