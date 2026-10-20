# Mass Driver Facility: plan to finish the chapter

Prepared September 5, 2026 against the current standalone V167 sources and staged dialogue.

**Progress:** The first implementation batch is built as the [V168 candidate](../../../docs/mass-driver-dungeon-3.24.md): opening and Gear/Citan continuity, clearer Guardian dialogue, and immediate clue summaries with optional full correspondence. The original letters and protected Miang scene remain unchanged. Fresh in-game acceptance is pending. The broadcast chronology, wider dialogue pass, combat balance, and ending review below remain future work.

The aim is a finished, coherent chapter: a clear reason to enter, satisfying exploration, a readable authorization challenge, a consequential Guardian fight, the preserved Miang flashback, a successful capsule launch, and a reliable return to player control. The main work is improving the existing chapter and proving it plays correctly from beginning to end.

This document is a proposed production plan with sample dialogue. It does not change the active game, builds, or saves. The working writing direction is faithful to Xenogears, with more natural dialogue and stronger character voices. The delivery scope is the standalone Mass Driver chapter; integration into a larger campaign is a separate milestone.

## What we have now

- V167 is the current standalone release, identified by [release metadata](../content/reconstruction_metadata.json) and [release notes](../../../docs/mass-driver-dungeon-3.23.md).
- The current builder declares **33 fields and 66 directed connections**, including branches and return routes. This is not a mandatory linear tour through all 33 rooms.
- A fresh review recompiled all **33 active dialogue sources** and matched each byte-for-byte against `work/mass_driver_v167_stage/clones/field_N/07_dialogue.bin`: **176 compiled blocks / 439 text pages**. These totals include conditional and dormant blocks, not the reading load of one playthrough.
- The route already includes a Repair Bot shop, a save point, two power systems, recoverable authorization records, the Guardian, optional archives/video/arcade games, five reserve magazines, and the launch/return sequence.
- V167 uses **Elly in Vierge and Emeralda in Crescens**. The archived El-Regulus work belongs to its future chapter.
- Existing release records report boot, payload, and sector validation. **A fresh V167 start-to-finish runtime pass is still pending in those records.** This planning review did not run the emulator or repeat the complete release audit.

Sources: [active builder](../build.py), [current launcher](../../../output/PLAY_MASS_DRIVER_STANDALONE.cmd), [current metadata](../content/reconstruction_metadata.json). Older release transcripts are useful history, but the current authored sources are the writing baseline.

## Protect the Miang flashback

In [Central Control dialogue](../content/field_369_archive_control.authored.json), the active memory is **blocks 22–31 and 36**. Preserve every line, speaker, page break, window setting, and the scene's existing cameras, actors, timing, sound, and transition behavior.

For the first dialogue pass, also leave the immediate entry and return, **blocks 21 and 32**, unchanged. Revisions can improve the surrounding chapter without reopening that scene. Preserve the continuous transition from the memory into Citan's arrival and launch.

Blocks **33–34 are dormant**, with no emitted reference in the current scene. Rewriting or reactivating them is not part of this plan.

Before implementation, snapshot the current sources and record the protected blocks and scene contract. The SHA-256 of the protected memory block objects, in source order, serialized as UTF-8 JSON with sorted keys, `ensure_ascii=False`, and separators `(',', ':')`, is:

`2b0192e5583de560cf50756a9fadd41176dca8b28d9c18930ba43816cb61574b`

Use that comparison alongside the compiled scene checks. Compiled addresses may move mechanically; the memory's content and behavior must stay the same.

## The player experience from start to finish

| Stage | What the player does | Finishing work | Acceptance condition |
|---|---|---|---|
| 1. Arrival and descent | Starts outside the facility, enters, descends the lift, reaches the abandoned transit route | Tighten the mission briefing; establish why Elly and Emeralda are here, where the Gears are, and Citan's role | A new player understands the capsule objective and can find the first destination without external instructions |
| 2. Explore the launch works | Uses the hub, reads records, restores auxiliary power and the accelerator interlock | Consistent room names and directions; distinctive staff voices; prompt clue access; short repeat messages | Both power objectives and the authorization records remain understandable in different exploration orders |
| 3. Defense Archive | Enters Directive 0320 and four authority points; optionally explores records, video, and games | Clear input feedback and next step; concise optional broadcast with coherent dates; reliable menu exits | All five entries are required, wrong entries remain recoverable, authorization opens the north lift without starting combat |
| 4. Guardian | Reaches Vierge and Crescens, boards, fights, returns on foot | Fix Gear-delivery continuity; establish immediate stakes; assess difficulty and recovery with the current Vierge party | Combat begins and ends cleanly, victory persists, and the player can open the west bulkhead and continue |
| 5. Reserve magazines | Crosses five vaults on the way to Central Control | Give optional records distinct purposes; reduce repeated condemnation; build tension with silence and short reactions | Forward and return paths work; stopping to read adds meaning without becoming another progression gate |
| 6. Central Control | Checks the capsule, experiences the preserved memory, meets Citan, launches | Tighten present-day exposition outside the protected boundary; motivate Citan's arrival; make the launch payoff clear | One continuous sequence preserves the memory, shows the keypad operation, and reaches the launch without another interaction |
| 7. After launch | Returns to the playable chapter state and can revisit completed areas | Confirm the accomplishment, party state, and practical next step; honor or resolve the promise to retrieve the Gears | Control returns, completion persists through saving/reloading, and the capsule cannot launch twice |

## Dialogue direction and priority revisions

**Elly:** observant, compassionate, and technically capable. Let her make decisions and respond to people. Move routine operating instructions into terminal messages when appropriate. Use natural contractions and avoid repeatedly restating the whole mission.

**Emeralda:** concise, perceptive, and emotionally direct. Keep her distinctive speech consistent, without exaggerated baby talk or unexplained technical deductions. Give her observations Elly would not make, rather than only questions that invite exposition.

**Citan:** precise and composed. Seed his practical role before the finale, then let his arrival and actions complete that setup. Keep the capsule's atmospheric explanation brief once the opening has established it.

**Staff correspondence:** retain Lena, Aron, Mara, and Mira. The paper star, falsified absence, unsent protests, and changing willingness to cooperate are strong material. Polish repetition and clarity while preserving their individual circumstances and choices.

**Systems and broadcasts:** use consistent terminology. A terminal should clearly state its condition and the next useful action; a broadcast should sound like a report, with concrete details and a clear chronology.

| Priority | Current source and blocks | Proposed change |
|---|---|---|
| First | `field_361_zeboim_access_tunnel` #0; `field_260_goliath_factory_hall` #3; Central Control #35 | Settle one account of Gear delivery. The opening credits Taura's crew, while the Guardian scene credits Citan. Recommended setup: Taura's crew delivered the Gears; Citan is checking the capsule/guidance connection. Verify that setup against the existing scenes before final wording. |
| First | `field_373_control_research_annex` #0; `field_374_storage_annex` #8 | These clue records currently run 13 and 14 pages. Make the recovered code and its destination easy to retrieve. Prefer a short repeat summary with a deliberate option to read the full correspondence; this requires an interaction change as well as editing. |
| First | `field_260_goliath_factory_hall` #3–4 | Normalize speaker formatting, clarify what the Guardian is doing, and remove the unsupported-sounding inference that the Core "transferred into it" unless the scene visibly establishes that event. Give victory a clear consequence and next destination. |
| First | `field_394_defense_archive` #35 and #25–30 | The broadcast begins in 6081 and ends with an undated emergency, while other project records place the exchange in 6083. Make the archive's time jump explicit or reconcile the date. The current playback has 27 pages; remove repeated points while preserving distinct reports and the final interruption. |
| Next | Opening #0; service hub #0–1; Defense Archive #0/#6/#8/#11; Central Control #0/#12/#35 | Reduce repeated mission, code, and route explanations. On revisits, show the current state and next destination instead of replaying an introduction. Check that hints do not assume unread optional records. |
| Next | `field_371_archive_annex` #0; `field_673_silo_vault_5` #0 | Give personal memories room to land. Keep the tombstone image, but replace the broad "pride and arrogance" judgment with a reaction grounded in the people whose letters the player has read. |
| Next | Central Control #20 and the actual post-launch return | Preserve "Please... reach them all." Establish that the capsule launched and dispersal began without claiming immediate worldwide success beyond what the scene demonstrates. Close the chapter's practical loose ends. |

These are candidate revisions, not instructions to replace every block. Short signs, useful status messages, and strong existing exchanges can remain.

## Sample rewrite direction

These excerpts demonstrate voice and pacing. They are not yet full block replacements or engine-wrapped dialogue.

**Arrival — opening block 0**

> **Emeralda:** "Still awake...?"
>
> **Elly:** "Taura said it would be. We only need one launcher."
>
> **Emeralda:** "To carry the capsule?"
>
> **Elly:** "High enough for the nanomachines to spread. If it works, we can break the Limiter's hold."

The completed opening still needs its concise navigation and Gear/Citan setup.

**Guardian approach — Gear hall block 3**

> **Elly:** "Our Gears... They made it."
>
> **Emeralda:** "Something else is awake."
>
> **Elly:** "The defense system. It still sees us as intruders."
>
> **Emeralda:** "Then it won't let us pass."
>
> **Elly:** "Stay clear of the launch controls!"

**Final magazine — vault 5 block 0**

> **Elly:** "Here in the dark... they look like tombstones."
>
> **Emeralda:** "Someone thought these would keep them safe."
>
> **Elly:** "Yes..."
>
> **Elly:** "Let's make sure our capsule reaches the people who need it."

## Other improvements worth making

1. **Navigation and feedback.** Audit every visible door and terminal from ordinary approach positions. Keep room labels consistent with actual routes. After power, authorization, and victory, give immediate feedback about what opened and where to go. Historical trigger fixes make this a high-value runtime check, not proof that those defects remain.
2. **Clue handling and revisits.** Keep the five-entry authorization challenge. Make discovered values easy to recall and failed entry easy to retry. Separate a concise status/recovered-clue view from optional long records where the current interaction supports it or can be extended cleanly.
3. **Exploration rewards.** Give each optional archive one distinct contribution: a clue, a character detail, a new piece of history, or a useful reward. Existing storage chests already offer rewards; review their value before adding more items or rooms.
4. **Guardian preparation and balance.** Assess the existing shop and save point along the actual route. The current Guardian is a no-Escape encounter, so check that the player naturally finds the save point and has a fair opportunity to prepare. Measure travel from the last save, supplies, damage, fuel, and recovery using the V167 Vierge/Crescens party. Add a nearer recovery opportunity only if playtesting demonstrates the need.
5. **Pacing and atmosphere.** Let the route alternate reading, movement, operation, and combat. The five vaults can provide a quieter approach to the finale. Evaluate ambient sound and camera framing outside the protected flashback after the text and route are stable.
6. **Optional-content reliability.** Keep the archive video and arcade games optional and clearly labeled. Confirm that Back, Cancel, Leave, completion, and failure all restore normal field control without altering story progress. Expand them after the chapter ships if desired.
7. **Ending and release clarity.** Verify the post-launch party/Gear state and revisit behavior. Give the player a concise ending/handoff appropriate to the standalone chapter. Present one current launcher and release identity with straightforward start instructions.

Avoid adding more rooms, bosses, or story branches during this finishing pass. Reconsider structural changes only when a playthrough identifies a specific problem that smaller revisions cannot solve.

## Production order

| Milestone | Deliverable | Ready to move on when |
|---|---|---|
| 1. Lock the baseline and story | Snapshot of the current working sources; protected-memory comparison; active block inventory; short continuity sheet covering mission, Gear delivery, Citan, archive dates, and ending | The live route and protected scene are identified, and the chapter's causal sequence is consistent |
| 2. Rewrite the active chapter | Scene-by-scene script with original/proposed text, purpose, block ID, and first-use/repeat context | Opening-to-ending read-through works both with and without optional lore; strong staff letters remain; no protected material changed |
| 3. Integrate dialogue and useful interaction changes | Authored text compiled with valid tags, IDs, line wrapping, window dimensions, menu indices, and correct state-dependent messages | The text compiles, menus and state transitions remain correct, and changed scenes fit the actual game windows |
| 4. Finish gameplay and presentation | Targeted fixes from route, interaction, boss, audio, and ending review | Changed areas work on first use, repeat use, backtracking, and fresh reload; the full route is ready for acceptance |
| 5. Prove the complete experience | Recorded results for minimal-route, full-exploration, and save/revisit runs on the same candidate build | All completion criteria below pass; remaining issues are explicitly documented and do not block completion |
| 6. Package the finished release | Matching build, patch/installer, launcher, transcript, metadata, concise player instructions, and changelog | A clean installation produces the verified candidate and boots successfully; every published version/hash agrees |

Milestones 2–4 should proceed in chapter order: arrival and hub, archives and authorization, Guardian and magazines, then present-day finale/return. This makes each batch reviewable while retaining the full story context. Estimate duration after the baseline playthrough and first rewritten section; the existing pending runtime checks make a precise schedule premature.

## Definition of finished

- [ ] A cold boot and New Game reach the facility with the intended Elly/Emeralda party, without relying on an old emulator state.
- [ ] The player can complete the mandatory route without reading every optional archive, watching the video, or playing either arcade game.
- [ ] Both power systems and all five authorization prompts work, including incomplete/wrong inputs, retries, and different exploration orders.
- [ ] Doors, lifts, terminals, optional branches, and reverse routes work from reachable positions; return spawns do not immediately trigger another transfer.
- [ ] The shop and save point work; ordinary saves made on the candidate build reload correctly before authorization, before/after the Guardian, and after launch.
- [ ] Guardian combat works with Vierge/Crescens and ordinary balance: commands, cancellation, representative attacks/deathblows, music, victory, and defeat/reload. The no-Escape rule works as intended, with a practical preparation and retry path.
- [ ] Victory and the west-bulkhead state persist, and the party returns through the human-scale passage correctly.
- [ ] Video and arcade exit paths restore camera, screen, input, and player control; optional rewards cannot be duplicated.
- [ ] Revised dialogue fits the game windows, uses consistent voices/names, and never promises a state change that does not happen.
- [ ] The Miang memory and its protected boundary remain unchanged in content and presentation.
- [ ] The uninterrupted memory-to-Citan-to-keypad-to-launch sequence completes; the return restores the intended party and control.
- [ ] Saving, reloading, and revisiting after completion preserve the ending state and cannot launch a second capsule or restart the boss.
- [ ] The ending resolves the standalone chapter's objective and clearly handles the stated plan to recover the Gears.
- [ ] Relevant structural/behavior checks pass; final-disc extraction matches staged replacements, affected sectors validate, and an independent rebuild reproduces the release.
- [ ] Current player instructions and the distributable patch/installer describe the same verified build.

Runtime results must be recorded separately from structural tests. Old savestates contain old field/battle data and cannot establish that a new scene works. Use fresh entries and saves created on the candidate build, with a complete cold-start run for final acceptance.

## Release housekeeping

The existing installer manifest deliberately preserves V161, while the standalone launcher selects V167. The portable manifest also describes an older disc identity. Align the release artifacts when producing the final candidate; their historical state is not evidence of a V167 gameplay defect.

Refresh the dialogue exporter to select the current release metadata and explicit candidate paths. It presently expects a `release` metadata key, whereas the current document uses `current_release`; its default paths also point to an older version. Generate a new active transcript instead of labeling the old V161 transcript as current.

Keep historical engineering notes as history and give the finished release one concise current overview. The player's launch instructions should explain how to start, save, and resume; detailed version-by-version technical records belong in the development documentation.
