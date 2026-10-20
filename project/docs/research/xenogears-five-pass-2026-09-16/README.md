# Five research passes for Mass Driver

Research date: 2026-09-16. Purpose: establish a source-backed basis for finishing the existing Mass Driver dungeon before changing its content.

**Recommendation:** finish the current dungeon through targeted continuity, dialogue, staging, and ending revisions. Its premise and major emotional structure fit Xenogears. It does not need another major plot, a new wing, or an early explanation of every mystery. It is not yet ready for content lock, and this research does not certify a bug-free build.

Only research documents were added. Game dialogue, scripts, builder, local configuration, builds, emulator state, and saves were left unchanged.

## The five passes and what completion means here

| Pass | Work completed | Durable result and limits |
|---|---|---|
| 1. Original game text | Sequential reading of 68 English chapter files, plus opening/front matter, including the NPC, optional, menu, and alternate dialogue present in those files. | [Disc 1 coverage](disc1-and-voices.md) and [Disc 2 coverage](disc2-and-revelations.md). This is a complete reading of the selected corpus, not proof that it contains every retail line or that every extracted variant is reachable. |
| 2. Setting and chronology | Studied 100 selected page entries of translated *Perfect Works*, covering history, institutions, mechanisms, characters, and author commentary; compared conflicting translations directly with Japanese pages 12–13. | [Setting and source review](setting-and-sources.md), including exact page coverage. This is a substantial targeted setting pass, not a cover-to-cover Japanese reading of every art/mechanical page. |
| 3. Character voice and knowledge | Compared Elly, Emeralda, Citan, and Miang across situations and stages of the plot; distinguished historical truth from what a particular character knows at Mass Driver. | Voice and knowledge sections in both script reviews. The original English localization is the working dialogue baseline; Japanese comparison was targeted, not comprehensive. |
| 4. Storytelling and presentation | Compared original dungeon/script structure, sampled recorded scene visuals, and read creator interviews and music commentary. | [Presentation review](presentation-and-mass-driver.md). Visual sampling is identified as such; this was not a continuous game/footage playthrough or a fresh auditory evaluation of the mod. |
| 5. Apply the evidence to this dungeon | Read all 33 active-source transcript sections and their blocks; checked source hashes and relevant script sequences; reassessed the existing finishing plan. | [Mass Driver findings and room coverage](presentation-and-mass-driver.md), plus [source snapshot](mod-source-snapshot.json). Source-level findings are separated from matters needing an actual playthrough. |

Three independent reviewers handled the setting, Disc 1, and Disc 2 readings while the main review handled presentation, the mod, and synthesis. Findings were cross-checked; for example, an incorrect reference to Citan promising to follow Fei was removed after checking the original exchange. He promises to accompany Elly.

## Findings that materially change the writing brief

### The central historical premise has stronger support than a generic fan invention

The official setting book describes the Mass Driver's civilian space-transport purpose and its subsequent military use. The reconstruction can confidently build around that reversal. Its particular staff, letters, directives, authorization puzzle, and Guardian remain authored connective material, not recovered Square scenes. See the Japanese page and translation comparison in [setting and sources](setting-and-sources.md).

That distinction matters when describing the mod publicly: it recreates a playable experience around established events. We have not found a surviving complete original dungeon scenario to restore line for line.

### Later scenes impose two specific constraints

The final assault uses rockets salvaged from Mass Driver. Preserve recoverable rockets and plausible future access. This does not require adding a salvage quest. The optional Lighthouse later revisits the Mass Driver missiles and gives Emeralda an important recognition and growth scene. Mass Driver should prepare that development without completing it early. [Original chapter 67](https://xenogears.us/static/media/67_Xenogears_Wakes.2bbbacd578a084dc83e3.txt); detailed locators in [Disc 2 notes](disc2-and-revelations.md).

### Elly's uncertainty and competence must coexist

She is grieving and experiencing partial recognition, but she is also an educated soldier who investigates, objects, chooses, and jokes. Turning her into a permanently serene guide would be less faithful than allowing practical confidence beside personal uncertainty. Her dreamlike recognition also has Disc 1 precedent; she should not be written as either completely blank or already possessing her later understanding. [Disc 1 voice evidence](disc1-and-voices.md), [immediate predeparture scene](https://xenogears.us/static/media/56_Shot_Down.b7677cf681c300305ed8.txt).

### Emeralda needs initiative, not a mechanical speech filter

Her original speech already varies between abbreviated phrases and longer fluent passages. The later growth scene is not a grammar toggle. Attachment, pride, stubbornness, and unfamiliar associations are better guides. Keep her able to notice something first, contribute, and resist being excluded. The reviews give original scene references rather than applying one rule to every line.

### The rescue mission and subsequent catastrophe have distinct causes and reveal times

Successful Limiter-removal delivery, Krelian's earlier virus operation, and the later Gaetia Key activation should not be collapsed. In particular, the launch party does not hear Krelian's private explanation. The hopeful launch is not a continuity error simply because the player later learns more. [Original chapter 57](https://xenogears.us/static/media/57_Break_the_Seal.91e3ac4d1441388af9b9.txt), [causality ledger](disc2-and-revelations.md).

### Translation can create a false canon problem

The older English timeline's account of Kim and Ravine conflicts with the Japanese page. The direct scan supports refusal in 6082, followed by Kim discovering his sponsor's identity/purpose in 6083. Do not carry the older subject reversal or compressed chronology into new archive text. The [setting report](setting-and-sources.md) records the evidence and distinguishes this resolved case from remaining uncertainties.

## Recommended finishing work, in order

| Priority | Concrete work | Why it matters |
|---|---|---|
| First | Resolve the broadcast's 6081 introduction leading uninterrupted into the 6083 nuclear exchange. | A demonstrable chronology ambiguity in an active sequence. |
| First | Align Mira's recalled promise with the earlier probe conversation. | The main personal archive thread needs a precise emotional payoff. |
| First | Put Gear recognition, threat, boarding, and Guardian battle in a coherent order. | The current source emits boarding descriptions before the recognition exchange. |
| First | Resolve the promised Gear recovery and the chapter's departure/handoff. | The dungeon should finish an action it tells the player to expect. Exact runtime consequences still need verification. |
| Then | Refine unprotected dialogue scene by scene: stronger staff distinctions, more Emeralda initiative where earned, less duplicate mission explanation. | Improve voice and rhythm while preserving the existing story. |
| Before content lock | Decide the final encounter structure, Guardian experience, optional rewards/games, and ending presentation. | These are content decisions; they should not remain deferred additions after declaring the dungeon finished. |
| Acceptance | Play the direct route, full exploration, and save/reload/revisit routes on one verified build. | Source and structural checks cannot certify navigation, pacing, combat, staging, or persistence in play. |

The [detailed findings](presentation-and-mass-driver.md) identify affected files, distinguish proven source issues from playtest questions, and retain successful existing work. In particular, V168 already has concise clue summaries and optional long records; the five magazine inspections are optional; the tombstone reflection has an original-game basis. Those should not be mistakenly rewritten as missing features or voice errors.

The Miang flashback, its boundaries, actors, cameras, timing, sound, and transition behavior remain protected by the repository's current instruction. None of these recommendations authorizes changes to it. Dormant Central Control blocks 33–34 must not be reactivated simply to explain the scene.

## Source policy for subsequent writing

1. Use the released game's scene context to establish what happens and when information becomes available. A later revisit line stored in an early chapter file is not early-story knowledge.
2. Use the official setting book for background, while recording corrections, contradictions, and translation provenance. The book and the fan-made Perfect Works ROM project are different things.
3. Use creator interviews for attributable statements, not to invent a lost design document or assign one writer to an uncredited line.
4. Treat fan transcripts, translations, and recordings as access to evidence with identifiable limitations. Treat fan summaries and theories as leads, not automatic canon.
5. Label every proposed addition as established, inferred, or newly authored. A plausible addition need not pretend to be established canon.

These passes establish a much stronger working reference. They do not support a claim of universal Xenogears expertise: remaining gaps include comprehensive Japanese dialogue comparison, complete retail trigger coverage, exhaustive audiovisual study, and current-build playtesting. The practical standard is that we can now explain and source a proposed change, identify its uncertainty, and check its effect on the surrounding game.

The next review should present **current mod text versus recommended revision**, by scene and block ID, before implementation. “Current” here means the project's existing authored text. It does not imply that there is a recovered original Mass Driver script.
