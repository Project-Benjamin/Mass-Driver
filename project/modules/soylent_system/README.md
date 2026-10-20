# Soylent System 1.1

This module reconstructs the **Disc 2 Surface Soylent** installation from the narrated sequence. Content 1.1 is source revision **V240**, release `soylent-v240-polish-20260926`. Its authored scope is the Ignas surface facility.

The eighteen-room dungeon includes the clinic confrontation, two distinct keycards, diagnostic and resonance puzzles, interface cutoff, recovery/save checkpoint, Sorting and Core decisions, Meld discovery, Sufal confrontation, persistent shutdown, and reciprocal emergency return. The finale gives an explicit **SOYLENT SYSTEM COMPLETE** acknowledgement. Optional records and conversations connect the treatment rooms to the production wing and respond to its shutdown.

The polish pass makes production instructions optional, preserves clinic memoranda beside a separate status report, adds an optional care plan with a physician, provides a service directory and next-objective guidance, and stops Sorting material movement on a completed revisit. Core containment visuals and native music remain intact.

See the [1.1 release notes](../../docs/soylent-system-polish-1.1.md) for verification evidence and the [player guide](../../docs/soylent-system-player-guide.md) for the route and puzzle solutions. Full runtime acceptance remains pending: a fresh run, both battles, native save/Continue, and the completed return must be verified on this exact release. Earlier user reports establish entry and progress through Quarantine-keycard acquisition, not a complete final-image playthrough.

Launch the selected verified release with the root `PLAY_SOYLENT_SYSTEM.cmd`. Use `PLAY_SOYLENT_SYSTEM.cmd --check-only` to verify the selected media without opening the emulator. A running game must load the new disc; a savestate can retain old room scripts until the room is entered again.

Build from the project root with the project Python environment. Choose a new release name for each build; this is an illustrative local name:

```powershell
.\.venv\Scripts\python.exe project.py build soylent_system --release soylent-local-review-001 --activate
```

The standalone profile requires `pw_disc1` and **`mass_driver_base`**, the normalized V166 Mass Driver Disc 2 source currently declared in [project.json](../../project.json). A raw Perfect Works Disc 2 image does not satisfy that base's audited clinic-resource contract. Keep that dependency explicit until the normalizing preparation is independently extracted and verified.

The combined profile instead composes reviewed Mass Driver, Surface Soylent, and Rico resources from its declared source variants. Standalone and combined acceptance remain separate.

The Quarantine keycard room (field 593) remains unoccupied: the doctor and patient do not spawn. Its terminal, keycard pickup, stored record, and return door retain their existing behavior. The other examination rooms retain their NPCs.

**One-hit combat is retained in the final standalone release at the user's request.** The setting in [content/playtest.json](content/playtest.json) gives enemies in both authored battles 1 HP, including the Sufal encounter's supporting enemies. A damaging hit defeats its target; misses and non-damaging actions retain native behavior. This option preserves party stats, progression, scripts, rewards, and source discs. A separately named build with `one_hit_kills` set to `false` restores normal combat. The standalone CLI applies the setting; the `prepare_campaign` API and combined composition do not enable it.

- [Campaign builder](build.py) and [base field builder](base.py)
- [Authored content and donor plans](content/), [module tools](tools/), and [tests](tests/)
- [Content 1.1 polish notes](../../docs/soylent-system-polish-1.1.md) and [player guide](../../docs/soylent-system-player-guide.md)
- [Earlier final content 1.0 notes](../../docs/soylent-system-final-1.0.md)
- [Earlier V238 expansion notes](../../docs/soylent-system-v238.md) and [V237 completion notes](../../docs/soylent-system-v237.md)
- [Retained campaign guide](docs/surface-soylent-campaign.md), whose V233 release narrative and development endpoint describe historical builds
- [Shared resource/state ledger](../../shared/resources.json)

The original `tools/build_surface_soylent_campaign.py` and `tools/build_surface_soylent_dungeon.py` commands remain compatibility entry points.
