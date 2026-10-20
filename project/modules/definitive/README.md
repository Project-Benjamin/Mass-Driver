# Xenogears Definitive

This is the independent `definitive` profile for the original USA retail campaign.
It is a development candidate, not a completed full-game restoration. It selects
no expansion modules, new scenes, new fields, or new save-state allocations.

Open `PATCH_XENOGEARS_DEFINITIVE.cmd` at the workspace root for the local patcher.
It checks both source disc identities, records immutable option selections, runs
the profile tests, creates separate BIN/CUE/M3U media, verifies every resource
and native lookup/boot table, then activates only the successful release.
`PLAY_DEFINITIVE.cmd` uses the normal checked project launcher. Existing disc
sources, saves, memory cards, chapter sources and donor contracts are preserved.

Available candidate switches: the documented bug-fix bundle, recognized single-page
yellow speaker rows, double enemy XP, and no random encounters. The last three
are off by default. Both field and world-map random dispatch are handled; forced
battle code is unchanged. Runtime verification of every feature is pending.

The bug-fix bundle includes the Mahanon Deus HP-halving camera guard, Def Up,
Charger recovery, Gear-shop Ether amplifier preservation, the Bulimy weight-gain
cap correction, and accurate Hob-Meat/Hob-Steak HP descriptions. The Deus guard
uses one declared transient battle byte; no save format or story state changes.
Native CPU regression checks are separate from emulator gameplay acceptance.

The patcher also exports the supplied HD portraits as an uninstalled DuckStation
texture-pack candidate. These images retain their 256x256 dimensions. Native
console images cannot supply HD replacement textures by themselves.

Full fan translation, complete yellow names, all bugs/spells/items, half
encounters, persistent max gold, one-hit story mode and whole-game acceptance
remain unfinished. Incomplete switches reject a request instead of silently
emitting an unchanged image under a success label.

See `docs/definitive/status.md` at the workspace root for scope, evidence,
acceptance work, and links to detailed inventories.

```powershell
python project.py status definitive
python project.py tools
python project.py test definitive
python project.py build definitive --release my-unique-release --activate
python project.py play definitive --check-only
python project.py play definitive
```

The default options are in `content/options.json`. The patcher writes immutable
files in `content/selections/` and supplies one with `--patch-options`; it does
not overwrite another window's selection. Required extra dependency for HD
export: `python -m pip install -r modules/definitive/requirements.txt`.
Optional native CPU audit dependency:
`python -m pip install -r modules/definitive/requirements-audit.txt`.
