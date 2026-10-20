# Soylent System 1.0 — final content release

The current release is [Soylent System 1.1 / V240](soylent-system-polish-1.1.md). This page retains the V239 build evidence.

Release: `soylent-v239-final-20260926`. Source revision: V239. One-hit combat remains enabled by the user's explicit choice; the Quarantine keycard room remains empty.

The authored eighteen-room dungeon has its complete route, clinic confrontation, separate Security and Quarantine keycards, diagnostic and resonance puzzles, interface cutoff, recovery/save checkpoint, distinct Sorting and Core decisions, Meld discovery, Sufal confrontation, persistent shutdown and reciprocal emergency return. Optional staff notes and patient conversations connect the treatment rooms to the production wing and respond to the shutdown.

The final pass adds an explicit **SOYLENT SYSTEM COMPLETE** epilogue and repeat acknowledgement, with native save and return guidance. Generation Hall survivors respond to the shutdown instead of describing machinery that is still running. The accepted Quarantine relay appearance persists on reentry. The resonance receipt spells out the existing five-direction pattern, and the permanently closed service shaft is described as decommissioned.

No rooms, actors, progression flags, battles or geometry are added by the final pass. Native boss handling, interrupted-epilogue recovery, save handoffs, rewards and doors retain their existing behavior. The one-hit archives remain identical to the preceding testing release. Historical candidates remain available; the root launcher selects the current verified build.

## Verification

The final release is built and activated. `project.py test soylent_system` passed **840 tests, 2 skipped, no failures** in 163.792 seconds; see [the full log](../work/soylent_final_full_tests.log). The focused integration run also passed all 80 tests. Build output is recorded in [the build log](../work/soylent_final_build.log).

The [installed-disc audit](../work/soylent_final_payload_audit.json) verified all **36 replacement resources**. Exactly four room bundles changed from V238: Service Manifold (565), Organic Resonance (589), Quarantine (620), and Generation (622). All 32 other resources remain byte-identical, including the empty keycard room and both one-hit enemy archives. Native models, textures, geometry, encounters, and actor/static records are preserved in the four changed rooms. Guidance changes preserve both original scripts; the appended relay/survivor actions preserve the prior native bytecode.

The BIN is 698,823,888 bytes. Exact source and media identities are recorded in the [build receipt](../builds/soylent_system/soylent-v239-final-20260926/project-build.json). Both the root and `output/` launchers passed `--check-only` from outside the repository and selected this release without opening the emulator. The output wrapper now forwards arguments and exit codes correctly.

The release remains **runtime unverified** until its native gameplay acceptance run is recorded. Earlier user evidence covers fresh dungeon entry, the Quarantine keycard, and reaching the relay gate; it does not establish a complete run of this final image.

The automated route test starts from reset state and earns every required flag through compiled interactions. It models successful movement/battle returns and supplies the native resonance input buffer, so it cannot certify physical access, rendering, battle transitions, or memory-card persistence in the emulator.

The remaining player acceptance pass is:

- Complete the full route from a fresh start on this exact release, including both battles, wrong-choice recovery, and every native door.
- Save and reload at the Ward and after the finale; confirm the completed state and both emergency-return directions persist.
- Revisit completed Quarantine and occupied treatment/Generation rooms; confirm accepted relay visuals and shutdown dialogue, and verify the keycard room has no NPCs.

No emulator controls, live memory cards or user savestates are changed by this release work. See the [player guide](soylent-system-player-guide.md) for the route and puzzle solutions.

## Current references

This page, the selected build receipt, final field manifest and [player guide](soylent-system-player-guide.md) describe the final release. [V238](soylent-system-v238.md) and [V237](soylent-system-v237.md) retain prior evidence. The V233 narrative and identity tables in `content/dungeon_plan.json` are explicitly historical; its `final_release` section points to the current content.
