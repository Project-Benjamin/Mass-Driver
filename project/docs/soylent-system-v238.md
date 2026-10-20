# Soylent System V238: discoveries and guidance

The selected release is now [Soylent System 1.1 / V240](soylent-system-polish-1.1.md). This page retains the V238 expansion evidence.

This pass deepens five rooms within the existing eighteen-field dungeon. It retains the NPC-empty Quarantine keycard room and the temporary one-hit combat setting. No new fields, actors, graphics, walkmeshes, battles, or persistent state are allocated.

- Quarantine's four pod controls explain that the player selects diagnostic readings. Each interaction reports the resulting **INCLUDED** or **EXCLUDED** state. Genome, Limiter and Nanomachines belong in the check; Caste Index does not. First-use instructions explain the east-door submission and reset on leaving. Completed checks are read-only, and both native exits retain their existing behavior.
- The Stabilization Ward's terminal gains **Clearance report**. It identifies every missing production prerequisite and points toward the clinic, Quarantine, resonance clue and actual lock, or bio-interface scanner. It distinguishes readiness from completed shutdown. Enter production, Restore HP and EP, Save progress, and Leave retain their existing selections and native behavior.
- The occupied treatment rooms (591, 592 and 594) offer **Patient record**, **Staff memorandum**, and **Leave**. Staff notes supply optional Sorting and Core clues alongside personal details about the patients. No note is required to advance.
- Patients and doctors retain their original hopeful dialogue before the Meld reveal. They respond differently after the discovery and after local production stops. Revisiting a memorandum after shutdown reports halted transfers. The change acknowledges surviving patients without claiming their mutations have been cured or every Soylent installation has been destroyed.

The keycard terminal and empty occupancy in field 593 remain unchanged. The other thirteen field bundles and all non-field resources match `soylent-v237-keycard-room-20260926` exactly.

## Verification

Historical candidate release: `soylent-v238-discoveries-20260926`. Build and launcher checks passed. The profile suite ran **823 tests with 2 skipped and no failures** in 156.997 seconds; see `work/soylent_v238_full_tests.log`. Focused tests exercise every relay configuration, all sixteen clearance combinations, optional terminal cancellation, NPC story phases, original native gate/save/recovery paths, dialogue fit, and preservation outside the intended scripts and dialogue.

The [installed-payload audit](../work/soylent_v238_payload_audit.json) verified all **36 replacements** directly from the built BIN. Exactly five bundles changed: fields 590, 591, 592, 594 and 620. Only script and dialogue components changed within those bundles; every actor/static record, model, texture, walkmesh and encounter table remains exact. Of the original dialogue blocks, only the Ward menu changed; 40 new blocks were added across the five rooms. The other 31 replacement resources, including the empty keycard room and both one-hit enemy archives, remain byte-identical.

The release BIN is 698,823,888 bytes. Its build receipt records the exact source and media identities. `PLAY_SOYLENT_SYSTEM.cmd --check-only` passed from outside the repository without opening the emulator. Build output is in `work/soylent_v238_build.log`.

Emulator acceptance is pending. The user previously confirmed fresh entry, Quarantine keycard acquisition, and reaching the Quarantine relay gate. That report predates this candidate. No emulator input, memory card, or user savestate is changed by this work.

Launch the selected release through the root `PLAY_SOYLENT_SYSTEM.cmd`. A running game must load the new disc to use these scripts. A savestate can retain old resident scripts until the room is entered again.

The [V237 notes](soylent-system-v237.md) preserve the earlier route-completion and keycard-room evidence; the retained V233 plan remains historical. This expansion's manifest describes V238; current source revision is V240.
