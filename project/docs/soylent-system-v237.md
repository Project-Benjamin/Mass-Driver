# Soylent System V237 completion candidate

The selected release is now [Soylent System 1.1 / V240](soylent-system-polish-1.1.md). This page retains the V237 completion and room-cleanup evidence.

V237 implements the completion work identified in the [dungeon analysis](soylent-system-completion-analysis.md). It restores the full existing eighteen-field route and gives the production wing distinct interactions. No new rooms are allocated.

The September 26 release, `soylent-v237-keycard-room-20260926`, removed the patient and doctor from field 593, the Quarantine-keycard room. Its keycard terminal, stored diagnostic record, bed, and return door remain. The temporary [one-hit playtest setting](soylent-system-one-hit-playtest.md) stays enabled. Build and launcher verification passed; a fresh room-entry check remains pending.

The room-cleanup suite passed: **805 tests run, 2 skipped, no failures** (`work/soylent_v237_keycard_room_tests.log`). The [installed-payload audit](../work/soylent_v237_keycard_room_payload_audit.json) verified all 36 replacements and confirmed that only field 593's bundle changed from `soylent-v237-one-hit-20260926`; the other 35 resources, including both one-hit enemy archives, are byte-identical. The root launcher passed `--check-only` from outside the repository without opening the emulator.

During the user playtest before this room cleanup, the user acquired the Quarantine keycard and reached field 620's east door, which reported three biological relays. Completion of that puzzle and the full dungeon run remain unverified.

## Playable changes

- **Quarantine:** Enable Genome, Limiter, and Nanomachines, leave Caste off, and use the east door. The confirmation closes before permanent clearance is recorded and the native door opens. Incorrect settings preserve the lock; completed visits do not repeat the award.
- **Sorting:** Each feed offers Stasis, Reclamation, Containment, and Leave. Tissue belongs in stasis, the nanomachine medium in reclamation, and unstable Meld in containment. Choices can be corrected. Use the onward exit to commit the complete routing.
- **M-Project Core:** Set Fusion OFF, Pattern OFF, and Containment ON. Incorrect configurations cannot open the onward route. Both production rooms explain that uncommitted settings reset when leaving; committed rooms remain solved and their controls become read-only.
- **Stabilization checkpoint:** The production door offers Enter production, Restore HP and EP, Save progress, and Leave. Saving uses the native menu. Enter still enforces all four clearances. Recovery restores character HP/EP; it does not repair Gears or change progression.
- **Meld:** The first scene completes before the onward clearance is awarded. Repeat visits acknowledge the continuing danger; visits after shutdown acknowledge the quieted line.
- **Sufal:** The confrontation requires confirmation. Not yet restores control and identifies the nearby save control and ward recovery. The native battle and recoverable epilogue remain; completed saves cannot repeat the boss. Both directions of the emergency return remain available after shutdown.

In the September 25 completion candidate, the clinic, examinations, patients, two keycards, native resonance puzzle, graphics, and geometry remained intact. Twelve room bundles retained their previous exact identities; the six intentionally changed fields were 590, 620, 622, 624, 625, and 626. The September 26 room cleanup additionally changes field 593's occupancy; fields 591, 592, and 594 keep their patients and doctors.

## Build and verification

Use the root `PLAY_SOYLENT_SYSTEM.cmd` launcher after the candidate is built and activated. `.venv\Scripts\python.exe project.py status soylent_system` identifies the selected release; `PLAY_SOYLENT_SYSTEM.cmd --check-only` verifies its media and current source identity without opening the emulator.

September 26 launcher correction: `PLAY_SOYLENT_SYSTEM.cmd` now explicitly uses the project `.venv\Scripts\python.exe`, matching the V237 build receipt. The previous bare `python` command resolved to system Python and incorrectly appeared as a changed toolchain. Running the corrected launcher with `--check-only` from outside the repository passes without opening DuckStation. The V237 disc, receipt, and selected release are unchanged.

Tests now resolve active donor discs from the project registry. The normalized V166 dependency remains pinned; historical migration fixtures retain their original identities. New tests cover actual compiled progression writers, all production configurations, cancellation, repeat interactions, midpoint recovery/save branching, and finale recovery. The test VM models released input, completed movement, and successful battle returns; it is not the emulator.

### September 25 verification

- September 25 standalone release: `soylent-v237-completion-20260925` (superseded as the active selection by the September 26 testing variant).
- `project.py test soylent_system`: **783 tests run, 2 skipped, no failures**, including the complete compiled route regression. Full output: `work/soylent_v237_full_tests.log`.
- `project.py build soylent_system --release soylent-v237-completion-20260925 --activate`: completed, with exact source and donor receipts. Build output: `work/soylent_v237_build.log`.
- `project.py play soylent_system --check-only`: passed; the verified CUE was launched through the same command without `--check-only`.
- Independent output-disc audit: all **34 staged replacements** (3,334,688 payload bytes) match their manifest and extracted BIN contents byte-for-byte, with zero errors. BIN/CUE/manifest identities and the CUE target match the receipt. Report: [payload audit](../work/soylent_v237_payload_audit.json).
- DuckStation reached the animated title screen at normal emulation speed. Initial automated inputs did not advance it. In the subsequent user-controlled playtest, the user confirmed that **K** is the working confirm key in their configuration, saw the Mass Driver / Soylent / disabled Mahanon menu, selected Soylent, and confirmed successful dungeon entry. Fresh-start entry is therefore user-verified; the earlier input attempt is not evidence of a game defect.

The [build receipt](../builds/soylent_system/soylent-v237-completion-20260925/project-build.json) records a 698,819,184-byte BIN with SHA-256 `0f2d0ea7abe790cd6ee54f051056fa6155e5c7f999382cb15b94db24c7b31b78`. The [field manifest](../builds/soylent_system/soylent-v237-completion-20260925/stage/manifest.json) contains the exact compiled puzzle, checkpoint, award-writer, and final route metadata.

Full emulator acceptance remains pending. Fresh-start entry and progress through Quarantine-keycard acquisition are user-reported on the preceding candidate. The field-593 cleanup needs verification after re-entering the room from the new disc; physical traversal, actual battles/defeat/retry, native save/Continue, and a completed return still need evidence before gameplay status can be marked passed. Legacy savestates may retain older resident scripts; no migration or user save replacement is performed by this release.

The retained campaign guide and `content/dungeon_plan.json` preserve historical V233 release details; the plan's room occupancy metadata reflects the field-593 cleanup. The current blueprint, final build manifest, V237 helpers, and these notes describe the candidate. Standalone and combined-selector acceptance are separate.
