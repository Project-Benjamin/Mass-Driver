# Project source distribution

The Mass Driver V176 release supplies separate project, Windows player, portable
patcher and DuckStation corresponding-source archives next to the public
installer. The project archive contains the canonical Python project, modules,
shared tools, tests, authored dialogue, selected art and public configuration.
The native player and patcher have their own source companions and build guides.

For a combined development tree, unpack the project archive, then copy the
companions' `tools/mass_driver_standalone` and `tools/mass_driver_portable`
directories into that project's `tools` directory. Keep each companion's release
metadata and manifest alongside that companion; do not overwrite the project's
`release/BUILD_IDENTITY.json`. The DuckStation archive contains the exact pinned
emulator source and matching dependency source archives and build instructions.
It does not need to be merged into the Python project.

Source downloads: [Mass Driver releases](https://github.com/Project-Benjamin/Mass-Driver/releases).

Some module guides and reconstruction metadata retain V173 development labels
inside the frozen implementation snapshot. The distributed release identity is
V176: use `release/BUILD_IDENTITY.json`, the final output hashes and
[V176 notes](mass-driver-v176.md). Earlier labels do not identify a different
game hidden in the installer.

## Reviewed scope

| Included | Excluded |
| --- | --- |
| `project.py`, `project.json`, public configuration examples and root launchers | `project.local.json`, `config.local.json`, environment files and machine settings |
| Current `modules/`, canonical `shared/` code and ledgers, tests and documentation | Raw discs, extracted donor files, prepared game payloads, patch payloads and historical output images |
| Compatibility `tools/` entry points and their historical repair source | Native executables, installers, emulator, BIOS, memory cards, saves and caches |
| The eight Mass Driver PNGs named by the active builder | Unused concept/reference media, retail reference screenshots and unrelated audio |
| Rico's authored source art and generated young-Rico portrait asset | The historical V161 installer; player and portable patcher sources are supplied separately |
| Release output hashes, external-input inventory and upstream license/provenance | Any game-data payload named by those inventories |

The [packaging script](../tools/package_project_source.py) starts with a manifest-only inventory. It reads the active builder's literal art declarations, uses text suffixes and explicit authored-asset exceptions, rejects linked inputs and unreviewed source-tree files, and excludes private configuration. The resulting `project-source-manifest.json` records every included file's size and SHA-256 before an archive is made. Archive mode verifies every ZIP entry against the selected source bytes and uses fixed ZIP timestamps.

## External build requirements

The current builder consumes audited extracted resources below the configured `tools.input_root`. The source companion's `release/EXTERNAL_INPUTS.json` lists their relative paths, sizes, and hashes, plus the source-disc and native-tool identities. It contains no extracted resource bytes. The full project declares additional sources for Soylent, Rico, and the combined profile in [project.json](../project.json).

The initial-state input `standalone_bootstrap/2595.bin` comes from a captured game-state fixture. Disc extraction alone does not recreate it. Other required donors include field bundles and components, graphics, battle data, menus, overlays, and title/world-map resources. Historical regression checks also depend on excluded old output images and captures. A new environment must supply or independently reproduce the matching inputs before running the complete build and historical tests. This companion does not claim a turnkey clean-disc rebuild.

The release's `release/FOUNDATION_PROVENANCE.json` records the rebuilt PW 0.10.2 recipe and identity. The rebuilt foundation differs from the unavailable historical image; the supplied 0.11.4 game patch was not used. Perfect Works' upstream GPL-3.0 text and pinned provenance are retained under `licenses/`. These notices do not grant rights to the underlying game. Portable patcher dependencies and notices remain in its separate source companion.

Development reference screenshots are deliberately omitted even though the workstation receipt fingerprints the entire `shared/` tree. Consequently this reduced source package does not claim the workstation's complete source-tree hash. Its own manifest identifies the distributed files precisely.

## Prepare and verify

Use a new output directory for each inventory or package so previous evidence is retained. From the project root:

```powershell
.\.venv\Scripts\python.exe tools/package_project_source.py `
  --receipt builds/mass_driver/mass-driver-v176-release-candidate-20261019/project-build.json `
  --output-dir work/mass-driver-release-20261019/packaging/project-source-scope `
  --perfect-works-license work/mass-driver-release-20261019/packaging/upstream-licenses/Perfect_Works_0.10.2_GPL-3.0.txt `
  --upstream-provenance work/mass-driver-release-20261019/packaging/upstream-licenses/provenance.json `
  --foundation-provenance work/mass-driver-release-20261019/upstream/base-recovery-report.json
```

Review the manifest, then use the same command with another new output directory and `--archive` to create the ZIP. The matching portable source companion and player patch are separate artifacts. A source archive's integrity does not establish native gameplay or clean-install acceptance.
