# Building the V161.3 one-app package

The package builds on 64-bit Windows 10 or Windows 11. It requires:

- PowerShell 5.1 or later.
- Visual Studio C++ x64 Build Tools.
- A clean xdelta source checkout at commit
  `ff322e592383227b0d65ddfde7e0e5bbc504dc15` (xdelta 3.2.0).
- The exact V161 plain-VCDIFF patch pinned by
  `release_manifest.json`.

The CUE template and required license texts are included in this source tree.
The patch payload, game disc image, emulator, BIOS, executable, and xdelta
checkout are not committed.

## Prepare the external inputs

From the repository root:

```powershell
git clone https://github.com/jmacd/xdelta.git .\external\xdelta
git -C .\external\xdelta checkout --detach ff322e592383227b0d65ddfde7e0e5bbc504dc15
git -C .\external\xdelta status --short
```

The final command must print nothing. Copy
`Xenogears_Mass_Driver_v161_USA_Disc2.xdelta` from the V161.3 release ZIP
into the ignored `external` directory. Its required identity is:

```text
Size:    8,094,235 bytes
SHA-256: 5acf90906eb1373ae2804566c114a692b9ef9ffd0126af92158055c366bbaef2
```

## Build

```powershell
.\source\build.ps1 `
  -PatchPath .\external\Xenogears_Mass_Driver_v161_USA_Disc2.xdelta `
  -XdeltaSourceDirectory .\external\xdelta
```

The script checks the patch size and hash, checks the xdelta commit and clean
worktree, compiles only the decode core with every secondary compressor
disabled, and creates `dist\Xenogears_Mass_Driver_V161.3_One_App.zip`.
It does not download dependencies or use a prebuilt xdelta executable.

The published executable was built with:

```text
Visual Studio Build Tools: 18.6.2
MSVC tools directory:       14.51.36231
C/C++ compiler:             19.51.36246
Linker:                     14.51.36246
Windows SDK / UCRT:         10.0.26100.0
PowerShell:                 5.1
```

The build uses reproducible compiler, linker, archive-order, and timestamp
settings. Two builds with the same sources, external inputs, and toolchain
must be byte-identical. A newer compiler or SDK can produce a different
executable even when its behavior and source are unchanged.

## Verify

Static package verification:

```powershell
.\source\verify.ps1 -SkipDynamic
```

Full verification with a privately obtained clean USA Disc 2 BIN:

```powershell
.\source\verify.ps1 `
  -SourceBin <path-to-clean-USA-Disc-2.bin>
```

Full verification checks the exact output BIN/CUE, source and package
immutability, repeat-build no-op behavior, wrong-source and tamper rejection,
emulator diagnostics, checksum coverage, and ZIP path safety. No disc image
belongs in source control.
