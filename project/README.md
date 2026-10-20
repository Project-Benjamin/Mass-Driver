# Xenogears Reimagined

The workspace for **Mass Driver**, **Soylent System**, and **Rico's Backstory**, with shared tools and an optional combined Disc 2 build.

## Start here

The current focus is **Mass Driver V176**. It includes random battles, the approved dialogue, native New Game/Continue/Sound, the repaired north lift and early save entry, and corrected Missile Command Triangle controls. Use [PLAY_MASS_DRIVER.cmd](PLAY_MASS_DRIVER.cmd) to launch the selected verified build. Read the [V176 notes](docs/mass-driver-v176.md), [dialogue transcript](docs/mass-driver-dialogue-v173.md), or [release QA](docs/mass-driver-release-qa.md) for measured coverage and limits.

The [public Windows player](docs/mass-driver-public-player.md) bundles the patcher and GPL-era emulator. First Play asks for your untouched USA Disc 2 BIN and USA PlayStation BIOS, builds its own game copy and remembers setup. The public download contains no game image or BIOS. The [private all-in-one installer](docs/mass-driver-private-installer.md) is historical local packaging and is excluded from the public release.

| Chapter | Source and chapter guide | Launcher |
|---|---|---|
| Mass Driver | [modules/mass_driver](modules/mass_driver/README.md) | [Play Mass Driver](PLAY_MASS_DRIVER.cmd) |
| Soylent System | [modules/soylent_system](modules/soylent_system/README.md) | [Play Soylent](PLAY_SOYLENT_SYSTEM.cmd) |
| Rico's Backstory | [modules/rico](modules/rico/README.md) | [Play Rico](PLAY_RICO.cmd) |
| Combined anthology | [shared composition](shared/README.md) | [Play combined](PLAY_XENOGEARS_REIMAGINED.cmd) |

Launchers verify the selected release before opening the emulator. `project.py status` reports which releases are usable on this machine. The combined selector's previously reported New Game black screen remains unresolved.

## Where things belong

| Folder | Contents |
|---|---|
| `modules/` | Each chapter's builder, dialogue, tools, tests, and working notes; also the separate Definitive project |
| `assets/` | Organized game artwork, portraits, audio, and reference media |
| [docs/](docs/README.md) | Current guides, research, release notes, and an index to older documentation |
| `docs/history/` | Older release notes and transcripts that have no fixed-path build dependency |
| `shared/` | Common disc, dialogue, graphics, script, and build tools |
| `builds/<profile>/<release>/` | Named builds and their verification receipts; `builds/current.json` selects the launchers' releases |
| `work/` | Extracted build inputs, development captures, and verification evidence |
| `output/` | Older images and fixtures still required by donors, tests, and historical launchers |
| `emulator_data/` | Saves, memory cards, and their backups |
| `archive/` | Retained legacy material and earlier project organization |
| `tools/`, `tests/` | Compatibility entry points for existing commands |

Some historical notes remain directly under `docs/` because regression checks require those exact paths. The [documentation index](docs/README.md) groups them for navigation. The original retail Disc 1 BIN/CUE retain their root paths because existing tools and tests use those filenames.

## Build and develop

Run from this directory with the project environment:

```powershell
.\.venv\Scripts\python.exe project.py status
.\.venv\Scripts\python.exe project.py doctor
.\.venv\Scripts\python.exe project.py test mass_driver
.\.venv\Scripts\python.exe project.py build mass_driver --release my-next-mass-driver-build --activate
.\.venv\Scripts\python.exe project.py play mass_driver --check-only
```

Configure source discs and tools in `project.local.json`; [project.json](project.json) declares profiles. For a new Mass Driver environment, install [its requirements](modules/mass_driver/requirements.txt). See [source setup](shared/README.md#source-setup) and the [development workflow](docs/development-workflow.md) for other profiles and commands.

The [source distribution guide](docs/source-distribution.md) describes the project-source companion, authored asset allowlist, and external game inputs. Source packages contain no disc images, extracted game resources, BIOS, saves, or private machine configuration.

Give each build a new release name. `--activate` selects a completed build; prepare-only and experimental builds are not selected automatically. The normalized Soylent V166 donor remains at its existing `output/` path.

For historical context, use the [research index](docs/research/xenogears-five-pass-2026-09-16/README.md), [build inventory](docs/latest-build-inventory.md), and [archived project README](archive/README_before_consolidation.md). The [directory organization record](docs/directory-organization-2026-09-16.md) lists moved files and verification. Organization and automated checks do not establish gameplay acceptance.
