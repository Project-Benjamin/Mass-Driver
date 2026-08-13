# Xenogears Mass Driver

This package applies the included Mass Driver update to a disc image that you
provide. It does not contain Xenogears, a PlayStation emulator, or a BIOS.

## What you need

- 64-bit Windows 10 or Windows 11.
- An unmodified USA Xenogears Disc 2 BIN (`SLUS-00669`, raw MODE2/2352).
- About 1 GB of free space in this package folder.
- A PlayStation emulator with your legally obtained BIOS configured when you
  are ready to play.

## Build and play

1. Extract the complete ZIP to a writable folder. Do not run it from inside
   the ZIP preview.
2. Open `Xenogears_Mass_Driver.exe`. It is the only file you need to open.
3. Select **Browse** and choose your original Disc 2 `.bin` file.
4. Select **Build game** and wait for all checks to finish.
5. Select **Play** in the same app.
6. If the app cannot find an emulator, choose your emulator's `.exe` or use one
   of its official download links.

The patcher reads the original BIN but never changes it. It creates the
verified game in the `Mass Driver Game` subfolder. The xdelta decoder is built
into the app, so applying the patch does not start a helper program or open a
console window.

The app checks for a supported emulator each time it runs. It does not save an
emulator path or other application settings. Your emulator remains responsible
for its BIOS, controller, graphics, and memory-card setup.

Always boot the generated `.cue`, not the `.bin`. Fully close and restart the
emulator, then choose New Game for a clean playtest. An older save state can
restore older resident game code and should not be used to check a new update.

## Transparent package

The ZIP root contains only `Xenogears_Mass_Driver.exe` and the
`MassDriverData` support folder. The patch, manifest, documentation, and
licenses are organized inside that folder. The app does not contain or unpack
another executable. It validates the strict data-only manifest, verifies every
runtime file before building, then verifies the finished BIN and CUE.

`MassDriverData/SHA256SUMS.txt` lists every distributed file and its SHA-256
value. The app is not code-signed, so Windows SmartScreen may show a warning.
If antivirus software reports a threat, stop and report the exact filename,
SHA-256 value, and detection name instead of adding an exclusion.
