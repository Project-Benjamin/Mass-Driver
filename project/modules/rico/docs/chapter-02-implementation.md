# Chapter 2: The Champ — implementation and validation

The approved expansion follows Rico from Fei's delivery to D Block through the loss of the title and his flight into the Central District. The theme is that Rico has learned to make people fear him; Fei begins to challenge his belief that strength earns all respect. The chapter ends before the room discovery in Chapter 3.

## Status

The dialogue is authored and the expanded field campaign is implemented in [chapter_two.py](../chapter_two.py), with audited locations in [chapter_two_resources.py](../chapter_two_resources.py) and visible scene staging in [chapter_two_scenes.py](../chapter_two_scenes.py). The opening correction candidate is `rico-ch2-opening-v2`; build receipts and validation results accompany its output. **A complete emulator playthrough of the expansion has not been performed.** Static checks do not establish that movement, encounters, transitions, or save behavior work in the game.

The proposed 45–60 minute duration is a design target, not a measured play time. The implementation should earn that time through exploration, changed interactions, evidence collection, and combat rather than repeated dialogue.

## Connected field campaign

The expansion uses 12 rooms: the Champion's sitting room and bedroom, intake infirmary, D Block commons, Baptism yard, Gear preparation area, sewer entrance, sewer hub, maintenance passage, treatment drain, arena, and Central District corridor. Ten additional field locations support the two inherited rooms. The active release implementation replaces the old room-only progression; the earlier six-step contract is retained for historical regression checks.

The authored route runs from delivery and Hammer's report through the Baptism, defense and explosion report, murders and investigation agreement, three sewer prerequisites, Redrum, bandaging, Finals, title transfer, crash, and final flight. Persistent chapter flags carry progress across field changes. The static model currently explores 76 reachable states and 205 transitions; every modeled state can still reach completion.

Standalone output is under `builds/rico/rico-ch2-opening-v2/`, with the replacement payloads in `stage/` and the paired Disc 1/Disc 2 playlist at the release root. The combined candidate is under `builds/combined/rico-ch2-opening-v2/` and receives the same expansion through the Rico preparation path. Use the root `PLAY_RICO.cmd` after activation; its verified release selection remains the launch authority.

The opening correction addresses the reported sitting-room/infirmary/sitting-room bounce and visible Rico-to-Fei swaps. Both chapter select and the Chapter 1 handoff now enter the infirmary directly. Outgoing Chapter 2 party changes occur only after a completed native fade to black. Intake locks control from initialization and has no Fei player update; it presents a cutaway, then enters Rico's room once. Completed delivery is not replayed, and native saves already in Rico's room stay there.

The infirmary stages Fei at the donor's floor position `(-185, 133)` instead of the bed/platform edge `(144, -111)`. Its fixed shot uses field 213's native camera vectors and reveals only after staging. These coordinates and bytecode ordering are checked automatically; the corrected composition and transitions still need observation in the emulator.

## Authored scope

[chapter_02_expansion.json](../content/chapter_02_expansion.json) contains 53 named scene hooks and 244 independently encoded dialogue blocks. Each scene value is an ordered list of strings; each string ends with `<Close>` and may contain explicit `<New>` page turns. Descriptions are implementation notes and must not appear in the game. The sewer passkey and bell are persistent chapter objectives rather than shared inventory items. The bandage is a story gesture.

The hooks cover:

- Fei's delivery, Hammer's report, and Rico's coercive Baptism confrontation, ending with Fei's defeat and Rank A assignment on the chosen route.
- A small D Block circuit, Stier preparation, and one short title defense.
- News of Weltall's explosion, missing Battlers, and Rico approaching Fei with suspicion and an apology.
- Sewer evidence, the passkey and bell, Citan's observations, and the Redrum encounter.
- The wound, Hammer's bandaging, the Finals, and the transfer of room privileges.
- The Group League return, arena crash, incomplete public account, and Central District flight.

`fei_explosion_report` belongs after the title defense and before the missing-person reports. It establishes the sabotaged bout that Rico later discusses; omitting it would leave the investigation without its immediate cause. The compact key route is a deliberate adaptation of the retail sewer puzzle.

Four repeat-response hooks support the state graph: `fei_before_investigation`, `fei_after_investigation`, `sewer_after_redrum`, and `treatment_gate_locked`. The gate hook contains separate key, slime, and bell hints; choose the applicable missing objective rather than replaying already completed directions.

[chapter_02_the_champ.json](../content/chapter_02_the_champ.json) retains its 38 legacy block IDs and order for existing routing compatibility. Narration remains marked at IDs 1, 12, 17, 23, 26, 29, and 36. Its chapter-select description introduces Fei without revealing the murders or later outcomes. This compatibility script is not evidence that all expanded scenes are already routed.

Dialogue uses explicit speaker rows and up to three body rows per page. Lines are wrapped to fit the existing 58-unit native window. Integration must preserve the plain speaker labels as well as `<Rico>`, `<Fei>`, and `<Citan>` when reflowing text.

## Story boundaries

Rico's refusal of a pardon remains a question, not a newly invented definitive motive. His men sabotaged Fei's Gear; Rico can acknowledge that without knowing who killed them. Citan is present in the sewers. The party treats its immediate investigation as over, but neither narration nor Citan certifies Redrum as the murderer. The later Id revelation remains intact.

The crash has an incomplete public explanation. Rico's private dialogue does not establish innocent failed controls, a new sabotage device, or full knowledge of the Committee's plan. The final flight does not reveal the room's family connection, DNA access, or Rico's parentage. The new bandaging and title-transfer gestures are authored additions, not recovered Square dialogue. See the [approved plan and source references](chapter-02-the-champ-plan.md).

## Static validation

[test_chapter_two_content.py](../tests/test_chapter_two_content.py) checks the complete scene-hook contract, the legacy ID count, lossless encoding, native dialogue bounds, sentence-safe pagination, key narrative dependencies, and the knowledge boundaries above. The existing Rico build tests retain their engine and binary assertions; only obsolete Chapter 2 wording expectations are updated.

[test_chapter_two_progression.py](../tests/test_chapter_two_progression.py) explores the actual action and automatic-event branch emitters with presentation replaced by symbolic events. It checks completion reachability, milestone order, prerequisite gates, scene coverage, and repeated interactions. It assumes successful battle returns and excludes native movement, menu timing, and the preserved bedroom doorway; those still require their binary checks and emulator observation.

Run the content checks with:

```powershell
python -m unittest modules.rico.tests.test_chapter_two_content modules.rico.tests.test_chapter_two_progression -v
```

## Runtime checklist — not yet performed

Record the profile, release name, disc, start method, and save used for each run. Use both standalone Rico and combined builds once engine integration and packaging checks pass. Mark each item only after observing it in the emulator.

- [ ] Start Chapter 2 normally and through chapter select. Fei's delivery precedes Hammer's report that he is awake.
- [ ] Explore Rico's room and bedroom before speaking to Hammer. His stair arrival completes; returning from the bedroom does not duplicate or skip it.
- [ ] Follow the route to the Baptism. The scene establishes Fei's reluctance, defeat, and Rank A assignment, then returns control without trapping the player or replaying the introduction.
- [ ] Visit the D Block workers, Battlers, and prisoners. Complete preparation and the Stier defense; repeat interactions and verify they describe the current stage.
- [ ] Hear the Gear-explosion report before the missing-person reports. Return to earlier NPCs and observe the changed activity. Check that entering the sewers early gives useful direction without advancing the story.
- [ ] Begin the investigation with Rico, Fei, and Citan. Verify the visible actors, battle party, and spoken contributions agree.
- [ ] Follow the compact sewer landmarks. Collect the passkey and bell, inspect evidence in different orders, revisit Gramps, and verify objective gates and repeated text remain coherent.
- [ ] Trigger the Redrum encounter once. Test victory and defeat/retry. After victory, check the wound and Citan's limited explanation; no text identifies Redrum as the proven murderer.
- [ ] Return to the rooms, complete the bandaging interaction, and revisit the bed. Check that required progress does not depend on finding an unmarked optional interaction.
- [ ] Play the Finals presentation through Fei's victory. Check that there is no unwinnable player-controlled fight presented as a normal objective. Verify the room and NPC changes after the title transfer.
- [ ] Follow the later Group League incident and Central District flight. Check that the public report remains attributed, that pursuit/transition cues are readable, and that completion stops before Chapter 3's door and memory sequence.
- [ ] Save and reload before the sewer entry, after Redrum, before the Finals, and before the final transition. Check party restoration, completed objectives, inventory cues, repeated battles, and chapter-select re-entry.
- [ ] Repeat critical steps using held confirm, repeated interaction, cancellation where offered, and quick doorway re-entry. Dialogue must finish and control must return without accidental skips or duplicate events.
- [ ] In the combined build, enter Chapter 2 from its content menu, complete its Chapter 3 handoff, and revisit the menu. Confirm the other chapter entries and Mass Driver/Soylent entry points still load correctly.
- [ ] Measure play time and note long stretches of repeated walking, unexplained objectives, or redundant conversation. Adjust pacing only after this observed run.

Keep failed cases with the last objective, expected behavior, observed behavior, and the relevant save or screenshot. No checklist item above is currently recorded as passed.

## Presentation choices

Fei uses the verified native fallen reaction during his brief infirmary reception. The opening does not add a stretcher model or a sleeping-bed animation. Hammer is visibly transplanted into the preparation bay, where speaking to him launches the Stier defense. Finals use mounted Stier and Weltall sprite choreography. The crash uses a visible charge, impact, and attributed public aftermath; royal-box destruction and the duct passage are compressed transitions.

Runtime Gear numbers are corrected for Stier (6), Weltall (0), and Brigandier (4), including the other Rico chapter battles that share the helper.

Start this candidate through New Game and chapter select. Older emulator save states retain their old resident field scripts and disc file table; changing the mounted image alone does not exercise this release.
