# Shared workspace workflow

This repository is the active workspace for Mass Driver, Soylent System, Rico,
and future chapters. Work from this root; preserve existing unrelated changes.

- Start with `python project.py status` and `python project.py tools`. Identify
  the requested profile and its active build before editing or testing.
- Use `shared/tools/` for common disc, field, dialogue, ATEL, image, and battle
  tools. Active code imports `shared.tools` directly. `tools/` entry points are
  compatibility aliases; `work/`, `archive/`, and `xenogears_modding_starter/`
  contain historical artifacts and must not become active tool imports.
- Reuse current module helpers by canonical import and declare the owning
  module in `build_dependencies`. Extract a common helper into `shared/` when
  its behavior is independent of a chapter; do not copy a frozen implementation.
- Check `shared/resources.json` before allocating fields, global records, or
  state. A shared tool fix does not authorize merging chapter state or changing
  donor contracts. Keep the pinned normalized Soylent V166 donor until its
  normalization has been independently replaced and verified.
- Create future projects with `python project.py new-module <slug> --title ...`.
  Do not create another copied starter project.
- Run `python project.py test <profile>` after relevant changes. It includes
  shared checks and the profile's transitive implementation dependencies.
- Rebuild current sources with `python project.py build <profile> --release
  <unique-name> --activate`. Prepared, failed, and experimental builds are not
  automatically selected. Record gameplay status honestly; a built receipt
  does not prove an emulator playthrough.
- Before emulator work run `python project.py play <profile> --check-only`.
  Use its exact reported media and configured emulator, then launch through
  `python project.py play <profile>`. Never infer build identity from the game
  title, a folder timestamp, or a resume save. Historical tests require an
  explicit `--release` and, when needed, `--allow-stale`.
- Preserve user saves and memory cards. Diagnose New Game independently of
  saved states. The combined selector's reported black screen is still open;
  see `docs/latest-build-inventory.md` and record actual runtime evidence.
- Protect Mass Driver's Miang flashback, its boundary dialogue, scripts,
  actors, cameras, timing, and sound unless the user explicitly changes that
  instruction. See `modules/mass_driver/docs/finishing-status.md`.

See `docs/development-workflow.md` for commands and the current-build policy.
