# Soylent System 1.1 — interaction and aftermath polish

Release `soylent-v240-polish-20260926`, source V240. One-hit combat stays enabled by user choice; the Quarantine keycard room (593) stays NPC-empty.

Sorting and Core controls now show their current setting immediately. The same choices and Leave selections remain; Review instructions is available separately and returns to the menu. Help never changes settings. Brief confirmations explain that the forward exit commits a configuration and leaving beforehand resets it. Completed controls stay read-only.

Occupied clinic terminals retain their original patient records and unique staff memoranda after shutdown. A separate Current status choice reports whether transfers remain active or have halted. Speaking with the physician in treatment room 591 after completion offers a short, optional care-planning conversation with Citan. It awards nothing and promises no implemented evacuation or mandatory rescue quest.

The decommissioned-shaft panel in Service Manifold includes a directory describing the actual routes and functions of Intake, Resonance, Scanner, Quarantine, and the Ward. The Ward's existing menu adds Next objective: one concise task based on earned clearance, production and finale flags. The detailed Clearance report remains available; entry, healing, saving and Leave retain their original choices.

After committing the Sorting diversion and returning, its transported biological material stays stationary. Existing visible assets remain; this is a change to native movement, observed on reentry. Core motion and containment remain intact because there is no checked mapping that safely distinguishes containment machinery from its other moving parts. Native Lab music remains unchanged.

No new rooms, actors, battles, persistent state allocations, rewards, or geometry are introduced. The eighteen-room route, native door behavior, battle/epilogue recovery, save handoffs and reciprocal emergency return remain.

## Verification

The release is built and activated. The full profile suite passed **856 tests, 2 skipped, no failures**, in 162.347 seconds; see [the full test log](../work/soylent_v240_full_tests.log). Tests cover optional Help loops, cancellation, native selectable menu ranges, all clearance combinations, ordered objectives, permanent memoranda, the completed care-plan dialogue, and active/completed Sorting behavior. The Sorting placement check verifies 72 distinct native positions, including four required native position overrides.

The [installed-disc audit](../work/soylent_v240_payload_audit.json) verified all **36 replacement resources** against the built BIN. Exactly seven field bundles changed from V239: 565, 590, 591, 592, 594, 624 and 626. The other 29 resources are byte-identical, including both one-hit enemy archives, the empty keycard room, the finale, and Quarantine. Only script/dialogue components changed; models, textures, geometry, actor/static records and encounter assets remain exact.

The BIN is 698,823,888 bytes. [Build output](../work/soylent_v240_build.log) and the [build receipt](../builds/soylent_system/soylent-v240-polish-20260926/project-build.json) record its source and media identities. Both the root and `output/` launchers passed `--check-only` from outside the repository and selected this release without opening the emulator.

Native emulator acceptance remains pending. Automated interaction tests cannot certify rendered presentation, physical access, movement, battle transitions, or memory-card persistence. No emulator controls or live saved games are changed by this work.

The remaining in-game checks are:

- Select Review instructions repeatedly, cancel and change settings in both production rooms; confirm the existing commit/reset rules remain clear.
- Select Current status in occupied treatment rooms before and after shutdown; reread each original memorandum and speak with the field-591 physician afterward.
- Use the Ward's sixth choice, Next objective, at different stages; confirm the seven-line menu displays correctly and native saving still works.
- Reenter Sorting after diversion and after saving/reloading. Its transported pieces should stay at their distinct native starting locations with room access intact; Core containment presentation should be unchanged.
- Finish a fresh route through both battles, the epilogue, native saves and both emergency-return directions on this exact image.

For the gameplay route, see the [player guide](soylent-system-player-guide.md). [Version 1.0](soylent-system-final-1.0.md) retains the preceding release evidence.
