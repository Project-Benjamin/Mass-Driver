# Building the Xenogears Cut Content Patcher

The package has stable public names:

- `Xenogears_Mass_Driver.zip`
- `Xenogears_Mass_Driver/`
- `Xenogears_Mass_Driver.exe`
- `Mass Driver Game/`

The executable is update-neutral. It reads a strict, data-only
`MassDriverData/patch_manifest.txt` at runtime. A future game update changes the
supplied VCDIFF patch, CUE template, sizes, and hashes in `build_manifest.json`;
it does not require a C++ change or an executable rename. The runtime manifest
cannot provide commands, programs, URLs, arguments, or output paths.

## Requirements

- 64-bit Windows 10 or Windows 11.
- Visual Studio C++ x64 Build Tools.
- A clean Apache-licensed xdelta source checkout at commit
  `7508fd2a823443b1f0173ca361620f21d62a7d37`.
- A plain VCDIFF patch with no secondary compression or application header.
- A CUE template whose filename matches the stable output BIN name.

The build compiles a decode-only xdelta core directly into the app. It does not
download dependencies or use a prebuilt xdelta executable.

```powershell
.\build.ps1 `
  -BuildManifest <path-to-build-manifest.json> `
  -PackageSource <path-containing-the-license-inputs> `
  -PatchPath <path-to-plain-vcdiff-patch> `
  -CuePath <path-to-cue-template> `
  -XdeltaSourceDirectory <path-to-clean-xdelta-checkout> `
  -OutputDirectory <destination>
```

For each update, copy `build_manifest.json` and change only the source, patch,
CUE, and expected output sizes and SHA-256 values. Stable package and output
names are enforced by the build script.

The build refuses an xdelta checkout at a different commit or with modified or
untracked files. It fixes ZIP timestamps and uses reproducible compiler and
linker flags. Two builds from identical inputs must be byte-identical. Because
the app reads update metadata at runtime, builds for different valid payloads
must also produce an identical executable.

Run `verify.ps1 -BuildManifest <path> -SkipDynamic` for static verification.
For full functional verification, also supply a privately obtained clean USA
Disc 2 BIN with `-SourceBin`. No game disc image belongs in source control.
