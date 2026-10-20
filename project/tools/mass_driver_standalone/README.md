# Mass Driver native installer and player

## Public player (V176)

The public mode creates **Mass_Driver_Setup.exe**, one native Windows x64
installer containing the GPL DuckStation runtime, its dependencies, the plain
portable patcher and patch data. It contains **no game image, BIOS or Microsoft
runtime binaries**. First Play uses Explorer file pickers to obtain the player's
untouched USA Disc 2 BIN and a supported 512 KB NTSC-U PlayStation BIOS dump.
Read [player directions](README_PLAYER.md) for input requirements and controls.

The public runtime is the official `v0.1-7371` x64 archive, source commit
`b2577ef8bdaae99840874b6dae8146f0316357b4`, licensed under GPLv3. Its binary's
embedded commit, official archive SHA256, complete source and dependency source
archives are recorded independently. The runtime binaries remain unchanged;
updater.exe is excluded. Settings are generated separately for this game.
The source companion must accompany the public download with clear matching
source directions. Preserve runtime/LICENSE.txt and resources/thirdparty.html.

```powershell
python tools/mass_driver_standalone/prepare_public_payload.py `
  --runtime-archive <official-7371-windows-x64.zip> `
  --emulator-source-archive <exact-b2577ef-source.zip> `
  --dependency-source-dir <matching-Qt-source-archives-directory> `
  --patcher-package <matching-plain-portable-patcher-directory> `
  --build-manifest <matching-portable-build-manifest.json> `
  --compiler <unpacked-llvm-mingw-directory> `
  --output-root <fresh-public-payload>

python tools/mass_driver_standalone/build.py --public `
  --payload-root <fresh-public-payload>/payload `
  --compiler <unpacked-llvm-mingw-directory> `
  --output-root <fresh-public-build>

python tools/mass_driver_standalone/verify_public.py `
  --installer <fresh-public-build>/Mass_Driver_Setup.exe `
  --build-report <fresh-public-build>/public-build.json `
  --payload-root <fresh-public-payload>/payload `
  --source-bin <own-clean-USA-Disc-2.bin> --bios <own-USA-BIOS.bin> `
  --qa-root <fresh-owned-QA-location> --test-microsoft-download
```

The verifier does not open UI, run the emulator, or execute Microsoft's installer.
It tests real native extraction, wrong/missing inputs, cancelled setup, exact
reconstruction, BIOS identity/copy, repeat setup, repair and data preservation.
Its optional download test checks Microsoft's actual Authenticode signature and
publisher, rejects an unsigned file, and never installs software.

Public mutable data is outside immutable version folders: `Game/<gameSHA16>`
holds the generated image; `UserData/bios/user-bios.bin` holds the selected BIOS;
UserData also holds cards/settings/states. Full SHA256 checks identify the game,
and the pinned emulator's seven known NTSC-U PS1 MD5s identify supported BIOS
dumps. Reinstall and repair preserve these files. The GPL frontend requires
`[Main] SettingsVersion = 3` to preserve first-run settings and skip its wizard.

Five VC DLL names are derived from this runtime's imports. The player checks
System32 using LoadLibraryEx. When missing, normal Play offers an official HTTPS
Microsoft download, verifies WinVerifyTrust plus the Microsoft Corporation
publisher, and opens standard visible `/install /norestart` setup. It uses no
silent EULA acceptance or forced administrator escalation. No Microsoft binary
is uploaded in our public package. An installed runtime skips this step.

Additional public headless diagnostics:

```text
Play Mass Driver.exe --headless --setup --source <BIN> --bios <BIOS>
Play Mass Driver.exe --headless --launch-check
Play Mass Driver.exe --headless --check-prerequisites
Play Mass Driver.exe --headless --verify-prerequisite --file <EXE>
Play Mass Driver.exe --headless --download-prerequisite --file <NEW-EXE-PATH>
```

The last action only downloads and verifies; it never opens the downloaded file.
`--launch-check` fails missing inputs without prompting or launching a runtime.
Setup's `--cancel-before` changes no input; `--cancel-during` exercises the
included patcher's cancellation before decoding after its staging is created.

Create the matching source companion after source/docs freeze:

```powershell
python tools/mass_driver_standalone/package_source.py --public `
  --player-release <public-payload>/payload/player-release.json `
  --output-root <fresh-player-source>
```

To use modified emulator/Qt files, replace them in a prepared payload, update its
descriptive release identities and rebuild with `--public`, or run the upstream
emulator directly. The builder records the supplied bytes; no signing key is
needed. Integrity checks do not alter the component licenses or prevent using
their corresponding source. This player is unsigned and remains a candidate
until native setup, controls, save/Continue and gameplay checks are accepted.

## Historical private mode

This separate tool builds an offline Windows x64 installer containing the exact
V174 game image, the user's local BIOS, an unmodified installed DuckStation
runtime, and independently verified app-local Microsoft VC runtime DLLs.
It is for the authorized private noncommercial local build. It does not publish
anything or establish public redistribution clearance. Public patch packages
and historical installers are separate and remain unchanged.

The native installer installs without administrator rights and provides
**Install**, **Cancel**, **Play**, **Open folder**, and an optional per-user Start
menu shortcut. The installed `Play Mass Driver.exe` is a small native launcher;
neither it nor the installer needs Python, a compiler, an existing emulator
installation, an original-disc picker, or a BIOS picker.

## Build inputs

Use the canonical project root and a fresh private destination on a drive with
space for the payload, compressed installer, and extraction QA. All inputs are
verified and read only. No existing saves or global emulator configuration is
copied. The runtime input inventory is reviewed separately; updater/uninstaller
executables are explicitly excluded. Runtime license/dependency notices and
private source/firmware/CRT provenance are retained.

```powershell
python tools/mass_driver_standalone/prepare_payload.py `
  --release-dir <built-V174-release> `
  --runtime-root <installed-DuckStation-directory> `
  --runtime-inventory <independent-runtime-file-inventory.json> `
  --bios <user-local-ps-22a.bin> `
  --crt-inventory <independent-signed-Microsoft-runtime-inventory.json> `
  --compiler <unpacked-llvm-mingw-directory> `
  --output-root <fresh-private-payload-directory>

python tools/mass_driver_standalone/build.py `
  --payload-root <fresh-private-payload-directory>/payload `
  --compiler <unpacked-llvm-mingw-directory> `
  --output-root <fresh-private-build-directory>
```

The build compiles the Play launcher first, embeds it as a native resource in
the installer stub, then appends a chunked archive. Windows Compression API
XPRESS_HUFF compresses each 4 MiB chunk when useful; other chunks remain raw.
The archive and every file are hashed, bounded and verified. Extraction streams
instead of loading the game image into memory. The footer parser accounts for
a future final Authenticode certificate table, but these artifacts are unsigned.

## Installation and preservation

Immutable content lives in `v/<first 16 archive SHA256 characters>`; the full
identity and full compiled content hashes remain verified. A new installation is
staged and verified before commit. Reinstalling exact content is a no-op for
private user files; repairing damaged content preserves the previous version
instead of deleting it. Failed cleanup reports its exact temporary path.

`UserData` is stable across versions and holds memory cards, saved states,
settings and caches. Fresh settings bind a normal keyboard and SDL gamepad and
refer explicitly to the bundled BIOS. The launcher prepares an isolated runtime
configuration from the user's latest private settings and synchronizes it after
the game exits. Required BIOS/save paths are kept inside the private installation.
It never uses or modifies the existing global DuckStation data directory.
The root is normalized and installation/game sessions share a per-root mutex.
The included upstream Qt runtime failed to initialize at a long test path, so
the installer keeps version paths compact and rejects version-root paths longer
than 120 UTF-16 characters with a request to choose a shorter location.

## Verification

```powershell
python tools/mass_driver_standalone/verify.py `
  --installer <private-build>/Mass_Driver_Private_V174_Setup.exe `
  --build-report <private-build>/private-build.json `
  --payload-root <private-payload>/payload `
  --qa-root <fresh-private-QA-directory>
```

This runs native headless installation, exact extraction checks, pre/mid-stream
cancellation and retry, existing-user-file preservation, damaged-content repair,
changed-installer rejection, and installed-launcher dry-run diagnostics. It
creates no shortcuts and never opens the GUI or starts the game runtime.
The returned `qa-report.json` records the actual evidence and limitations.
`verify_upgrade.py` separately checks an explicitly identified prior successful
QA installation: switching from the older `versions/` layout to `v/` must preserve
every old version file and every canonical private settings/card file.

`package_source.py --output-root <fresh-source-directory>` creates and verifies
a reproducible source-only ZIP. It excludes all runtime, game, BIOS and user data.

Native GUI/gameplay checks are separate. A workstation dependency review is
also separate from clean-machine acceptance; optional upstream plugins and
Windows version/API requirements still need honest reporting.
