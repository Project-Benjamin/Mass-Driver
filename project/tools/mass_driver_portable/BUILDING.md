# Building the Mass Driver patcher

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
- Visual Studio C++ x64 Build Tools, or an unpacked Windows x64 UCRT
  [llvm-mingw toolchain](https://github.com/mstorsjo/llvm-mingw/releases).
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

## Prepare an exact release

`prepare_release.py` creates a new input kit from a completed project build
receipt. It validates the clean retail source and built target, generates a
plain VCDIFF patch, and reconstructs the exact target from that source before
writing a release-specific build manifest. Existing kits and historical
manifests are never overwritten. This does not certify gameplay acceptance.

```powershell
python tools/mass_driver_portable/prepare_release.py `
  --source-bin <clean-USA-Disc-2.bin> `
  --release-dir <built-release-directory> `
  --content-version V176 `
  --output-dir <new-input-kit-directory> `
  --xdelta <xdelta3.exe> `
  --xdelta-source <clean-pinned-xdelta-checkout> `
  --perfect-works-license <Perfect-Works-license-file> `
  --mingw-directory <unpacked-llvm-mingw-directory>
```

When space is limited, `--scratch-directory <temporary-parent>` puts the
full reconstructed BIN on another drive. Its unique temporary directory is
removed after verification; the finished input kit remains at `--output-dir`.

Pass that kit's `portable-build-manifest.json`, `Mass_Driver.xdelta`,
`Mass_Driver.cue.template`, and its directory as `-PackageSource` to
`build.ps1`. For the portable compiler, also pass `-MingwDirectory`; omit it
to retain the Visual Studio build path. The generated manifest pins the
compiler runtime license, which is included in the resulting package.

The unpacked compiler and encoder remain private build tools. They are not
included in the player ZIP. Record their official download URLs, archive
digests, and the decoder source commit with release engineering evidence.

## Single downloadable EXE

Add `-SelfContained` to the same build command and use a new output directory.
This produces one `Xenogears_Mass_Driver.exe` containing the patch, strict data
manifest, CUE template, documentation and dependency notices as a native data
resource. It extracts no executable and starts no patching helper. The plain
ZIP build remains available by omitting the switch.

On launch, the app verifies the embedded resource, materializes it in a
per-user LocalAppData hash directory, and verifies every cached file. Existing
changed cache data is rejected. A repeated launch reuses exact cached data
without rewriting it. The one-file app defaults the generated game to a
per-user folder; **Choose game location** selects another parent for this
session. Both formats still require the supported clean retail Disc 2 BIN and
an independently installed emulator/BIOS.

Run `verify_single_file.py --exe <EXE> --build-manifest <manifest> --source-bin
<clean-BIN> --qa-parent <scratch-parent> --report <evidence.json>` for resource,
cache, tamper, reconstruction, cancellation/retry and preservation checks.
This uses headless diagnostics and does not launch the GUI or an emulator.
The embedded payload changes the one-file EXE hash on each content update;
the ZIP's separate-data executable remains update-neutral. Neither artifact
is code-signed by these scripts.

## Cancellation and diagnostics

The GUI's **Cancel build** action cooperatively stops the integrated decoder,
discards staging, and enables a fresh attempt. The headless
`--cancel-before-decode` option deterministically exercises the same flag after
staging exists; `verify.ps1` checks cancellation cleanup followed by a successful
retry. It also checks both wrong-size and same-size wrong-hash inputs, safe
reuse of an existing exact output, changed patches, and emulator command
construction without launching an emulator. Native GUI acceptance remains a
separate check.

## Source companion

`source_companion.py` creates a reproducible source-only ZIP of this directory,
verbatim dependency notices, and official download/source provenance. Supply
the pinned decoder checkout, compiler directory, downloaded provenance JSON,
and the exact upstream license/provenance files. An actual generated
`--build-manifest` can be included after the game candidate exists. Keep this
archive beside the matching full Mass Driver project-source companion and
player ZIP; it does not contain the game builder or claim to replace the full
project source. Historical payload templates are clearly identified.
