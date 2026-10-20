# Mass Driver Facility

The standalone Elly/Emeralda chapter contains the facility approach, authorization challenge, Guardian encounter, reserve magazines, and Central Control launch sequence. Elly uses Vierge; Emeralda uses Crescens.

The current candidate is **V173** (`mass-driver-v173-release-candidate-20261019`). It adds curated native on-foot Zeboim encounters in six passages, restores Elly's captured level 52 baseline, and tightens two Emeralda lines. The existing mission, clues, Guardian, Citan's off-screen Gear delivery and launch work, and Gear recovery remain. Protected Central Control dialogue, its scripts, actors, cameras, timing and sound remain unchanged. Full playthrough and clean-install acceptance must be recorded before declaring a final release.

```powershell
.\.venv\Scripts\python.exe project.py test mass_driver
.\.venv\Scripts\python.exe project.py build mass_driver --release my-next-mass-driver-build --activate
```

Run this from the repository root after configuring sources. For a new Python environment, create `.venv` and install this module's `requirements.txt`. The profile uses Perfect Works Disc 2 and the audited extracted resources under `work/`. The rebuilt 0.10.2 source is explicitly identified in current metadata and receipts; it does not claim the lost source image's hash. The supplied 0.11.4 patch is kept separate from this release foundation. Build/source receipts identify the inputs actually used. `PLAY_MASS_DRIVER.cmd` uses the project environment when available.

Random battles use three verified native Zeboim formations in fields727,372,723,375,387,726. Archive, shop/save, story, Guardian, magazine and control rooms remain quiet. Every other random weight is zero, including fixed Guardian slot15. Encounter frequency and combat balance require acceptance with the actual two-character party and Vierge/Crescens. See [the encounter policy](encounters.py).

- [Builder](build.py), [authored content](content/), [module tools](tools/), and [tests](tests/)
- [Current finishing status](docs/finishing-status.md)
- [V173 release candidate notes](../../docs/mass-driver-v173.md) and [complete transcript](../../docs/mass-driver-dialogue-v173.md)
- [V172 candidate notes](../../docs/mass-driver-v172.md), [approved review](../../docs/research/mass-driver-dialogue-fit-review-2026-09-30.md), and [complete transcript](../../docs/mass-driver-dialogue-v172.md)
- [Preserved completion plan](docs/mass-driver-completion-plan.md)
- [How the chapter was made](docs/how-mass-driver-was-made-simple.md)
- [V169 candidate notes](../../docs/mass-driver-v169.md), [dialogue changes](../../docs/mass-driver-dialogue-v169-changes.md), and [complete transcript](../../docs/mass-driver-dialogue-v169.md)
- [V170 candidate notes](../../docs/mass-driver-v170.md), [dialogue changes](../../docs/mass-driver-dialogue-v170-changes.md), and [complete transcript](../../docs/mass-driver-dialogue-v170.md)
- [V171 candidate notes](../../docs/mass-driver-v171.md), [reviewed writing](../../docs/research/mass-driver-dialogue-redraft-2026-09-28.md), and [complete transcript](../../docs/mass-driver-dialogue-v171.md)
- [Current verified launcher](../../PLAY_MASS_DRIVER.cmd)
- [Historical V168 notes](../../docs/mass-driver-dungeon-3.24.md)

`tools/build_mass_driver_dungeon.py` remains an import/CLI compatibility entry point. Versioned notes describe their own recorded builds; a new organized build has its own manifest and verification record.

After preparing the matching stage, export its current transcript into the release directory:

```powershell
.\.venv\Scripts\python.exe -m modules.mass_driver.tools.export_mass_driver_dialogue --version v173 --stage-root builds/mass_driver/mass-driver-v173-release-candidate-20261019/stage --manifest builds/mass_driver/mass-driver-v173-release-candidate-20261019/stage/manifest.json --output docs/mass-driver-dialogue-v173.md
```

The exporter requires an explicit version, stage, manifest, and output. Historical transcripts stay in `docs/`; explicit historical export commands remain supported when supplied their matching inputs.
