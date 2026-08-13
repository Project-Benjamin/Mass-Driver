# Credits and licenses

This one-app patch package applies the included Mass Driver release to a
tester-provided, legally obtained clean USA Xenogears Disc 2 BIN. It contains
no game disc image.

## Perfect Works

This release was developed from and incorporates changes derived from
Xenogears: Perfect Works Build 0.10.2. The included
`Perfect_Works_GPL-3.0.txt` records its license notice.

- Project: https://github.com/PWBuild-Team/Perfect_Works_Build

## xdelta3

The visible decoder in `MassDriverData/tools/xdelta3.exe` is a reviewed, reproducible x64
build from unmodified xdelta 3.2.0 and XZ Utils 5.8.3 source. Deterministic
path remapping prevents local source or build paths from being embedded. Its
exact build description and SHA-256 identity are recorded in
`MassDriverData/patch_manifest.json` and `MassDriverData/SHA256SUMS.txt`.

- Project: https://github.com/jmacd/xdelta
- Source commit: `ff322e592383227b0d65ddfde7e0e5bbc504dc15`
- License: Apache License 2.0, included as `xdelta-Apache-2.0.txt`

## XZ Utils / liblzma

The decoder links liblzma from XZ Utils 5.8.3.

- Project: https://tukaani.org/xz/
- Source: https://github.com/tukaani-project/xz/releases/tag/v5.8.3
- Source commit: `4b73f2ec19a99ef465282fbce633e8deb33691b3`
- License for liblzma: 0BSD, included as `xz-libLZMA-0BSD.txt`

Xenogears and its original game content belong to their respective copyright
holders. This unofficial playtest release is not affiliated with or endorsed
by Square Enix.
