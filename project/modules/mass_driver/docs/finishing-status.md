# Mass Driver finishing status

## V176 Missile Command controls repair — October 19, 2026

Native testing found that Missile Command's actions labeled Triangle were bound to physical Square. The field opcode reads the configured game input word: physical Triangle produces `0x80`, while Square produces `0x10`. Cross and Circle already match the displayed instructions. V176 corrects the four affected mask operands: title release, title exit, active-game pause and pause release. Cross resumes and Circle exits the paused game.

The prepared-resource comparison against V175 proves that only these four script bytes in field 376 change. All other 165 replacements, all 33 room headers and dialogue components, the other 296 room components, and every protected Central Control byte remain identical. No score, enemy, timing, reward, scene, or persistence logic changes. All **426 profile tests pass**, with two existing skips. Five new regressions execute the emitted branches with the independently observed physical input words and reproduce the old mapping's failure. Fresh-disc native title-exit and pause/resume/exit acceptance must be recorded against the built V176 image before release; earlier V175 checkpoints inside field 376 retain the old script and cannot establish the fix.

## V175 save-resume repair — October 19, 2026

Cold Continue testing found a second, route-dependent save defect in V174. The memory-cube room had remapped the native save-resume variable's initializer to an unused local variable. Entering from the vertical connector could therefore save entry index 3, which points outside the room's three-entry table. Entering from the opposite side happened to leave a valid door-entry index and concealed the defect.

V175 restores the donor's native `0x54 = 2` initialization in field 725. Only its two-byte variable operand changes; the dedicated save entry, memory-cube action, puzzle state, dialogue, other room components and protected Central Control scene remain unchanged. Existing cards are preserved. A newly written save after entering the corrected room must cold-load at its native save entry `(41, 50, walkmesh 0)` from either arrival route; old malformed saves are not automatically rewritten.

All **421 profile tests pass**, with two existing skips. Four new regressions reproduce the failed and accidentally valid V174 contexts, execute the corrected initialization, and pin the exact two-byte change. The prepared-resource audit checks all 166 replacements and all 297 decompressed room components: only field 725's script changes; the other 165 replacements and all dialogue are identical to V174. Native saving from both approaches, cold Continue, a second save/reload, completed revisits and the full chapter still require acceptance on the built V175 candidate. A successful build or automated check is not that acceptance.

## V174 title repair — October 19, 2026

Fresh V173 testing reached the shop, random battle victory and escape, and a completed native save at the memory cube. Cold-start testing then exposed a release blocker: the earlier demonstration title deliberately disables Continue. V174 restores the native New Game/Continue/Sound title for the standalone Mass Driver profile, while keeping its Disc 2 New Game entry and preserving other profiles' legacy selector behavior. The repaired candidate must pass cold Continue, native saving, and a second cold reload before release. Existing V173 saves and artifacts are preserved; the private V173 installer is historical and is not a final release.

The straight approach to the authorized north lift could also stop just outside its activation range. V174 lowers that entry threshold slightly and widens the native proximity fallback, preserving the existing horizontal aperture and keeping the return spawn outside the trigger. Native approach/revisit checks must confirm the repair. No story, battle, or protected Central Control scene change is part of these repairs.

The all-in-one private installer includes the game, supplied BIOS, runtime, and required app-local Microsoft runtime files. Its packaging and startup checks passed for V173; those checks must be repeated against V174. Public redistribution has not been cleared. See [private installation notes](../../../docs/mass-driver-private-installer.md).

## Release candidate work — October 19, 2026

The user authorized the full final-release pass and explicitly requires random battles. **V173 (`mass-driver-v173-release-candidate-20261019`)** replaces the earlier exploration-only encounter intent with curated native Zeboim formations in six passages. Other random weights are zero; the single fixed Guardian remains. Elly returns to her captured level 52 state with existing stats, experience, money, equipment and supplies; Emeralda remains 49. The two narrow Emeralda voice refinements are installed. The Miang memory, its protected boundaries and all scene staging remain unchanged.

The release must be tested as a complete experience with these encounters: direct route, full exploration, defeat/retry, ordinary save/Continue and completed revisits. The modern portable patch package must reproduce the accepted candidate from the verified clean USA Disc 2. The historical V161 installer remains a historical artifact. No earlier test or build receipt establishes these new runtime results. Current evidence is under `work/mass-driver-release-20261019/`; see [V173 release notes](../../../docs/mass-driver-v173.md).

## Earlier writing polish — September 30, 2026

The user approved implementation of the [script-fit review](../../../docs/research/mass-driver-dialogue-fit-review-2026-09-30.md). **V172 (`mass-driver-v172-dialogue-polish`)** refines V171's live writing: missing-code prompts describe facility requirements, overlapping defense and recall records are shorter, Emeralda takes the opening initiative, optional records use fewer unnecessary pages, and the Bank Four/capsule wording is corrected. The existing terminal roles, clue values and menus, dates, Guardian exchange, Mira's uncertain fate, Gear delivery/recovery premise, and hopeful launch remain intact.

The installation changes **13 dialogue blocks across eight authored files**, removing **16 page advances** from the complete stored transcript. That inventory includes optional and dormant text; it is not the mandatory route's reading load. Only approved live dialogue is changed. Protected Central Control blocks **21–34 and 36**, including dormant **33–34**, remain unchanged. Scripts, actors, cameras, timing, sound, geometry, encounters, rewards, and persistent state are unchanged. V171 and its evidence remain historical references. Installation and audit evidence is under `work/mass-driver-dialogue-polish-20260930/`; release evidence belongs in [V172 notes](../../../docs/mass-driver-v172.md), and exact installed pages in [the V172 transcript](../../../docs/mass-driver-dialogue-v172.md).

Fresh in-game acceptance of V172's writing, pagination, and complete route remains pending. A source/disc audit and successful build establish the installed bytes and preservation contract, not an emulator playthrough.

## Earlier writing revision — September 29, 2026

The user approved implementation of the dialogue rewrite and terminal overhaul for **V171 (`mass-driver-v171-dialogue`)**. This revision replaces 73 dialogue blocks in 23 source files, with native window wrapping and preserved menu dispatch. The earlier favorable editorial audits are not acceptance of the rejected writing. Working proposals, the pre-installation snapshot, and installation evidence are under `work/mass-driver-dialogue-20260929/`. See [the reading draft](../../../docs/research/mass-driver-dialogue-redraft-2026-09-28.md) for the reviewed prose and [V171 candidate notes](../../../docs/mass-driver-v171.md) for build and validation results.

Terminal text fits the station's physical purpose. In particular, the computer inside the stationary train now has a saved shift timetable and cancelled-service notice. All 36 live console/shop stations have a role review. The installed revision replaces repeated correspondence with local engineering, stock, access, duty, and dispatch records; removes the off-site Kim dossier; and moves the short civilian-probe/Mira introduction to Civil Payload Stores. Historical records are labeled, required clues remain at the beginning of the summaries, and menu choices keep their existing dispatch order.

The Miang memory, its entry and return, and all scene staging remain protected. The accepted Gear-delivery premise is direct exterior access to the hangar, with Citan delivering the Gears off screen before joining the pair at Central Control. The opening establishes the arrangement and the hangar encounter acknowledges its completion. This text installation adds no exterior map route or arrival animation. The sealed north door reports unavailable local controls; it is not presented as the delivery route. Neither "Taura's crew" nor transport through the dungeon's personnel lift/corridors is part of the installed explanation.

V171 needs fresh in-game acceptance of its writing, pagination, and pacing before content lock. Automated checks and a successful build do not establish that the writing works in play. The V170 implementation history below is retained as historical evidence; its superseded dialogue is not the current writing standard.

## Earlier V170 candidate

The final review's finishing batch is implemented in the **V170 candidate**, following V169's research-backed improvements. Current build and validation evidence belongs in [V170 candidate notes](../../../docs/mass-driver-v170.md). The user reports positive prior playtesting; the V170 changes still need in-game acceptance.

## Earlier V170 implementation history (writing superseded)

- Completed-mission surface entries suppress the obsolete mission briefing; Central Control's arrival text works before and after launch without altering its script.
- The west-bulkhead console offers explicit operation, optional archived reading, and Leave. Its report no longer blocks door operation or repeats automatically on an open door.
- Authorization success warns that the defense system is active and gives the player a chance to prepare before descending to Guardian.
- The research archive describes the floor controls accurately whether auxiliary power is off or already restored.
- Opening and Gear dialogue consistently credit Taura's crew with delivery and establish Citan's guidance work.
- Guardian dialogue has consistent speaker controls, clearer observations, and a useful post-victory destination.
- Both main clue archives show their code and destination first. Close archive is the default; Read full record opens the unchanged correspondence. Repeat visits show the concise overview again.
- Citan's present-day launch dialogue is shorter and connected to his established role.
- The news archive explicitly separates the 6081 report from the 6083 emergency recording, with less repeated commentary.
- Mira's recalled probe conversation agrees with the earlier record. Emeralda chooses to leave the Kim archive; staff correspondence uses more concrete personal requests.
- The targeting record explicitly distinguishes restoring power from reconnecting the missiles' target link.
- Central Control avoids repeating the full mission explanation. Guardian recognition precedes boarding, and the post-launch return resolves recovering Vierge and Crescens.
- The intended interior structure is exploration-led with one fixed Guardian. Donor interior random encounters are excluded deliberately; the existing exterior encounters and optional activities remain.

The protected Miang memory is Central Control blocks **22 through 31 and 36**. Entry **21**, return **32**, and dormant **33 and 34** also remain unchanged. The scene's scripts, actors, cameras, timing, sound, and transitions are outside this dialogue pass.

The [V168 release notes](../../../docs/mass-driver-dungeon-3.24.md) record structural tests, compiled dialogue checks, final-disc extraction, sector validation, and an independent rebuild. Fresh start-to-finish in-game acceptance is still pending.

## Remaining work, in order

1. **Accept V173's encounters and text in-game.** Check the opening, train timetable and shop, both code-first archives, missing-code prompts, optional records, Guardian dialogue, Citan's launch exchange, and post-launch Gear recovery. Check pagination and pacing, including held input and all menu choices. Confirm the uninterrupted protected finale. Record actual observations separately from structural checks.
2. **Accept the complete chapter in order.** The [final editorial review](../../../docs/research/mass-driver-final-review-2026-09-24.md) is complete. Check its pacing and presentation criteria with and without optional archives; the [console audit](../../../docs/research/mass-driver-console-audit-2026-09-25.md) records relevance and static interaction coverage.
3. **Address measured gameplay and presentation issues.** Assess navigation, the existing shop/save route, Guardian difficulty and recovery, optional-content exits, and ending clarity. Make changes in response to playtest evidence rather than arbitrary stat changes.
4. **Prove the full chapter on one candidate.** Run the direct route, full exploration, and save/reload/revisit routes. Verify persistent victory and completion, no repeated boss or launch, and correct return to player control.
5. **Package the accepted build.** Align its launcher, transcript, release manifest, patch/installer, and player instructions. Preserve prior candidates and their evidence.

The [complete original finishing plan](mass-driver-completion-plan.md) retains the scene inventory, writing direction, proposed examples, protected-scene contract, and full acceptance checklist. Its V167 baseline and historical version references describe when the plan was prepared.

The user's content-lock objective supersedes the old plan's suggestion of adding optional-game content after release: finalize or exclude content before declaring the dungeon finished; later updates should be bug fixes. V173 is a candidate for that acceptance, not a declaration that all runtime checks have passed.
