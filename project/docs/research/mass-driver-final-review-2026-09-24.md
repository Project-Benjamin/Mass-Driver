# Mass Driver: final content review

**September 29 update:** the user subsequently rejected the writing outside the Miang flashback. This historical review's favorable editorial recommendation is superseded by the [current full dialogue rewrite](mass-driver-dialogue-redraft-2026-09-28.md). Its technical findings can still be consulted; its writing verdict is not user acceptance.

Review date: September 24, 2026. Candidate: **V169**, selected release `mass-driver-v169-local-emulator`.

**Recommendation:** retain the current story, character writing, rooms, and exploration-led structure. Finish the three bounded items below before content lock. This review found no reason for another broad rewrite, a new character scene, or additional combat content.

This is a review and proposal, not an implementation or release declaration. No game content, scripts, assets, build selection, or saves were changed.

September 25 follow-up: the user approved the finishing batch. The [console binding audit](mass-driver-console-audit-2026-09-25.md) distinguishes active interactions from compiled-only text, including the optional prose-polish suggestions below. [V170](../mass-driver-v170.md) records implementation and validation separately from this historical proposal.

## Basis

- Read all 33 active authored dialogue sources: 181 blocks and 434 pages, including optional and dormant material. These totals are not the required reading load of a playthrough.
- Independent continuity and dialogue reviews reached the same conclusion: the current character voices and historical arc do not require a broad rewrite. Source hashes and compiled dialogue were checked against the selected V169 stage.
- Inspected relevant event paths for clue records, archive interactions, the west bulkhead, Guardian commitment, Central Control arrival/completion, world-map entry, and Gear recovery. The findings below distinguish source behavior from observations requiring play.
- Visually inspected the seven source PNGs actually selected for the broadcast, and checked their playback mapping. This was asset inspection, not a current emulator presentation or audio review.
- Used the [five-pass research ledger](xenogears-five-pass-2026-09-16/README.md), especially its original-script revelation order, voice findings, and setting-book chronology. The earlier V168 recommendations describe an earlier version; V169 already resolves their principal writing issues.
- The user reports that playtesting looks good. This review adds specific acceptance questions; it does not imply that no playtesting has occurred.

Build BIN SHA-256, as recorded in the [V169 evidence](../mass-driver-v169.md): `9987579ac994758bb345a354a534f10a36b3934c349fe40d6a78db3f0a933001`.

## The finite finishing batch

### 1. Make arrival dialogue agree with a completed mission

**Classification: source-confirmed repeat-state writing defect.**

[Central Control block 0](../../modules/mass_driver/content/field_369_archive_control.authored.json) asks whether the capsule is ready and states that the cradle contains a payload. The normal entry from field 383 plays this block without checking launch completion. By contrast, the main console correctly uses block 20 to report a completed launch and no second payload.

The active dispatch is `standalone_entry=True` in the Central clone, followed by `_repoint_standalone_entry`, whose normal-entry branch displays block 0. It is not the generic auto-scene installer. See [builder](../../modules/mass_driver/build.py), the Central declaration around lines 6845–7048, `_repoint_standalone_entry` around 24160, and dispatch around 24720.

The same family of problem occurs at the surface: field 729's opening briefing has only a previous-field exception for returning from the lower lift. Entering from the world map can repeat the uncompleted mission briefing after launch. The world-map entry remains connected to field 729. See the surface `AutoScene` around 5285 and `_prepare_worldmap` around 32328.

**Proposed remedy:** use the existing launch-completed state to suppress the obsolete surface briefing after completion. For Central Control, use state-neutral block 0 wording so its entire script can remain unchanged:

> Elly: “Central Control...”
>
> Emeralda: “Elly... the console.”
>
> Elly: “Let's take a look.”

This preserves a first-arrival exchange without asserting that a second capsule exists. The launch console already supplies the appropriate pre-launch or completed information. It does not require a new postgame scene or a new persistent flag.

**Acceptance:** first arrival still establishes the mission; returning before launch works; returning from the world map after launch does not repeat the pending-mission briefing; Central Control no longer claims a loaded capsule; its console reports completion without replaying the launch.

### 2. Separate the west bulkhead's controls from its archived report

**Classification: source-confirmed pacing and interaction problem; recommended before content lock.**

The west panel displays all five pages of [Defense Archive block 19](../../modules/mass_driver/content/field_394_defense_archive.authored.json), the Strategic Outcome Model, before checking either Guardian victory or the open-door state. It therefore forces the report during progression and repeats it even when the door is already open. See [builder](../../modules/mass_driver/build.py), `panel_dialogue=19` around 6598 and the action around 17997–18015.

This is a separate panel from the two clue archives, which already have concise summaries and optional full records.

**Proposed remedy:** retain the report unchanged behind an explicit reading choice at this same console. Give the player a short control menu:

```text
WEST BULKHEAD CONTROL
  Operate bulkhead
  Read archived report
  Leave
```

Operating it should immediately report the relevant state: defense still active, opening the bulkhead, or already open. Keep the existing Guardian prerequisite, door animation, sound, camera behavior, and persistent open state. Reading the report must not unexpectedly operate the door.

**Acceptance:** test before Guardian victory, after victory, and after opening. A player can operate or inspect the door without rereading the report; the full report remains available by choice.

### 3. Make the Guardian commitment clear before the player triggers it

**Classification: design recommendation, not demonstrated unfairness or a balance defect.**

After authorization, approaching the Gears crosses a trigger that locks input, shows the warning, boards both pilots, and starts combat. There is no preparation decision between the warning and battle. The existing save cube is in field 725, which the hub-to-stairs route can bypass. See [builder](../../modules/mass_driver/build.py), the Guardian approach around 20255, the save point around 6051, and route edges beginning around 4244.

**Proposed remedy:** revise the existing authorization handoff, [Defense Archive block 6](../../modules/mass_driver/content/field_394_defense_archive.authored.json), so the terminal's Custodian status becomes a clear warning before the player descends. Suggested final character pages:

> Elly: “Our Gears should be in the bay below.”
>
> Elly: “The defense system is still active. Let's check our equipment before we go down.”

Keep the existing north-lift directions on the preceding terminal page. This adds one short preparation cue to an existing exchange. It does not require another save point, a new room, a new fight, or an arbitrary HP change.

**Acceptance:** an unfamiliar player understands that the bay may lead to combat and has a chance to prepare before crossing the trigger. If current play evidence already establishes that this is clear, treat the wording as polish rather than a release blocker.

## Story and voice decisions to keep

| Element | Judgment |
|---|---|
| Mission and ending | The launch remains successful and hopeful. Citan has a practical guidance task; the post-launch return resolves the promise to recover the Gears. |
| Elly and Emeralda | Their connection already exists in observations, uncertainty, and choices. Emeralda asks to leave Kim's record; Elly respects her. Another bonding speech is unnecessary. |
| Mira | The probe callback is consistent. Elly's admission that she does not know Mira's fate is more credible than an invented resolution. |
| Staff correspondence | Aron moves from technical pride through rationalization to regret and action. Mara concentrates on certification and responsibility; Lena on the civilian work and people affected by it. |
| Chronology | The staff sequence develops from the civilian program through militarization to catastrophe. The broadcast explicitly distinguishes 6081 from 6083. No new historical contradiction was confirmed. |
| Later revelations | The current played material leaves the later Lighthouse resolution and larger revelations available to do their work. Dormant Central blocks 33–34 must not be activated. |
| Rockets and targeting | The disconnected target link distinguishes restoring power from rearming the old weapons. The facility and reserve rockets survive. |
| Dungeon identity | Keep the machinery, separate power and authorization tasks, optional archives, five silent magazine entries, and single fixed Guardian. More encounters are not an authenticity requirement. |

The original game's tombstone reflection remains a valid anchor. Do not remove it as allegedly out of character. The protected Miang memory and its immediate boundaries remain outside the finishing batch: Central blocks **21–34 and 36**, plus their actors, cameras, scripts, timing, sound, and transitions.

## Optional polish that should not delay completion

- Two terminal phrases could use a more mechanical register: “Read this room's record” could become “CONSULT MATERIALS ARCHIVE”; “Power opens this gate. The launch records do not” could become “GATE RELEASE: POWER ONLY / LAUNCH CODES NOT REQUIRED.” Their current meanings are useful and clear. These are not continuity errors.
- The sepia broadcast stills form a consistent archival presentation, but their realistic figures and dense detail differ visibly from the party portraits. My visual concern is how clearly they read at native display size and beside the game's text windows. The source images alone do not justify declaring them wrong or commissioning replacement art. Keep them unless the in-game comparison exposes a specific mismatch.
- The compiled “GOLIATH FACTORY” label was investigated. No active display was established; the relevant donor handling is retired. It is not a confirmed player-facing defect and should not drive a content change.

## What the final play review must decide

Use the accepted candidate to answer these specific questions, incorporating the user's existing observations wherever they cover that build:

1. **Direct route:** do instructions, controls, Guardian, magazines, and launch form a satisfying chapter when optional records are skipped? Check whether the west-panel change removes the identified interruption.
2. **Full exploration:** do the letters deepen the people and place without repeated interactions forcing the same long material? Are the broadcast and optional-game return paths clear?
3. **Preparation and combat:** can a new player identify preparation opportunities and understand the Guardian commitment? Assess meaningful turns, fuel pressure, and retry cost before changing stats or rewards.
4. **Presentation and completion:** do music transitions, boarding, the protected finale, launch, Gear recovery, and return outside read smoothly? Then revisit the completed dungeon and verify its dialogue agrees with its state.

These are acceptance criteria for existing content, not an invitation to keep expanding the chapter. Once the bounded fixes and this acceptance are complete, freeze content and package the exact accepted build. The previously identified installer/patch-manifest updates are release engineering; eventual integration into the original campaign remains a separate project.
