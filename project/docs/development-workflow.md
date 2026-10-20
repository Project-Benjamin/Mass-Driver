# One workflow for every chapter

All active chapters use the current implementation in this workspace. Content
lives in `modules/<chapter>/`; common build and inspection tools live in
`shared/`. Historical images and donor resources remain pinned inputs, with
their role and hash recorded separately from the chapter version.

## Identify the build and tools

```powershell
python project.py status
python project.py tools
python project.py doctor
```

`status` shows each profile's explicitly active release and the newest built
receipt separately. It reports changes to source files, shared tools, Python
packages, configured native tools, source discs, and consumed extracted inputs.
Add `--verify` to hash the finished launch media too. A recent test build is
never selected merely because it has the newest timestamp.

`tools` lists canonical tool locations, reusable module helpers, the local
Python/package/native-tool identities, and checks for imports from retired
tool copies. This records the installed working toolchain. Package or donor
upgrades need compatibility validation before becoming the project's baseline.

The [build inventory](latest-build-inventory.md) establishes the content
baseline: Mass Driver V168, Soylent V236, and Rico's `rico-ch2-v1` expansion.
The shared-workflow baseline is `workspace-v1`. Subsequent fixes use distinct
release names, including Rico's `rico-ch2-opening-v2`; see its
[release notes](history/rico/rico-chapter-02-opening-v2.md). The active registry and each
build receipt identify the selected content and tooling.

## Edit, check, build, select

```powershell
python project.py test rico
python project.py build rico --release my-next-rico-build --activate
python project.py play rico --check-only
python project.py play rico
```

Replace `rico` with `mass_driver`, `soylent_system`, or `combined`. Use `test all`
to run the shared suite and every active module. Test discovery includes a
profile's implementation dependencies, so reused Mass Driver or Soylent
helpers are covered when working on Rico.

Make all source edits before the final build. The build fingerprints module
files, shared code, registry, tools, source discs, and extracted resources.
Changing these afterward makes its launch check stale and gives a rebuild
instruction. Changing a shared tool requires rebuilding affected candidates;
an existing disc cannot acquire new generated game data automatically.

`--activate` only changes `builds/current.json` after the full build and its
identity checks succeed. A separate build command without that flag leaves the
normal launcher alone. Use `activate <profile> --release <name>` to explicitly
select another current build. Existing build directories are preserved; `--force`
retains a nonactive replaced directory under a timestamped name. An active
release cannot be overwritten with `--force`; use a new name so a failed build
cannot disturb the current launcher.

Activation and gameplay acceptance are separate. `untested` is the default;
`known-issue` records an outstanding gameplay defect; `passed` requires actual
relevant gameplay evidence. The `workspace-v1` combined build retains the
unresolved New Game black-screen report. Its preceding selector route fix has
static regression coverage, but the display failure has not been verified as
fixed. A toolchain rebuild does not complete that investigation.

## Launchers and historical builds

The root launchers use the same verified path:

| Launcher | Profile |
|---|---|
| `PLAY_XENOGEARS_REIMAGINED.cmd` | `combined` |
| `PLAY_MASS_DRIVER.cmd` | `mass_driver` |
| `PLAY_SOYLENT_SYSTEM.cmd` | `soylent_system` |
| `PLAY_RICO.cmd` | `rico` |

The generic launchers under `output/` forward to these. Explicitly versioned
legacy launchers remain historical artifacts. Normal launch verifies the
selected receipt, image hashes, playlist/CUE references, and current tooling,
then prints the exact disc path. Rico uses its paired M3U.

For a deliberate historical comparison:

```powershell
python project.py play combined --release rico-ch2-v1 --allow-stale --check-only
```

This explicitly permits old tooling; it still requires matching image hashes.
It does not change the active release. Old unrecorded images in `output/` are
documented in the inventory rather than silently imported as current builds.

## Reuse and future projects

Import shared codecs from `shared.tools`. Helpers still owned by a chapter can
be imported from that module with an explicit `build_dependencies` entry.
Move broadly useful behavior into `shared/` when its assumptions are understood
and checked across callers. Keep story scripts, balance choices, and persistent
state contracts with their chapters.

```powershell
python project.py new-module mahanon --title "Mahanon"
```

The scaffold starts disabled and directs authors to the same tools and checks.
Register sources, resource ownership, state lifetimes, dependencies, and a
validated builder before enabling it. The starter folder is historical reference.
