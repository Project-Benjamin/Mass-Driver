# Mass Driver console and interaction audit — 25 September 2026

**September 29 update:** the live/compiled-only binding inventory below remains useful. Its editorial conclusion is superseded by the user's rejection of the writing outside the Miang flashback and the [current full rewrite](mass-driver-dialogue-redraft-2026-09-28.md). This audit is not approval of the dialogue's quality.

This is a **static interaction audit**, extending the earlier complete dialogue reading. The active console content serves the dungeon's progression, abandoned workplace, civilian-to-military history, or optional activities. It does not need another general lore rewrite. The audit found one additional, definite repeat-state instruction error in the Research archive; its state-neutral correction is included in V170.

It would be inaccurate to say that every compiled dialogue block is a readable console, or that every console has been tested in-game. This report separates actual installed readers and controls from retained donor/director dialogue, and separates source verification from runtime acceptance.

## Scope and evidence

- Reviewed all **33 active authored sources**, their **181 V169 blocks**, and the current `CLONES` specifications and relevant installers in [build.py](../../modules/mass_driver/build.py).
- Read the V169 staged script and dialogue components for all 33 fields. The **66 components** in `mass-driver-v169-organized` and the selected `mass-driver-v169-local-emulator` release matched byte-for-byte. The latter was selected when this audit began; its runtime status was `untested`.
- Used declared entity/action bindings, their installer bodies, current state conditions, and staged ATEL entry points to identify interactions. Supplementary decoding used the canonical `shared.tools.xgatel` reader and the local Noah opcode metadata as data, not as an active implementation import.
- The generic decoder does not understand every native opcode. It also starts from *all* script slots, including dormant director tasks. Its output is supporting evidence, not an exhaustive proof that every reported reference can execute in normal play. In particular, a raw dialogue instruction in retired code is not a live console.
- The inventory identifies **36 authored console/shop stations in 20 fields**, counting each physical reader/controller once, including the two Research power controls. Item pickup, treasure, save, door, lift, and automatic scene interactions are covered separately. This is not a count of every decorative computer model.
- Current source was also checked for the V170 changes below. V170 runtime behavior remains subject to the acceptance checks in [the candidate report](../mass-driver-v170.md). No emulator session or new gameplay observation was performed for this audit.
- Historical and character knowledge was checked against the [five-pass research](xenogears-five-pass-2026-09-16/README.md), especially the [setting chronology](xenogears-five-pass-2026-09-16/setting-and-sources.md) and [Disc 2 knowledge boundaries](xenogears-five-pass-2026-09-16/disc2-and-revelations.md). Original staff correspondence remains authored connective material, not a recovered Square dungeon script.

Here, **bound** means the current builder installs a normal interaction on the named entity and explicitly emits the listed blocks. It does not certify controller feel, visibility from every camera angle, or successful navigation with a gamepad. Directions are checked against declared route/door destinations and the recorded room arrangement, not a fresh visual walkthrough. Block IDs are local to their source file. `e13` means entity 13, normally its action slot 2.

## Definite issues and V170 disposition

| Interaction | V169 finding | Current V170 correction | Acceptance still needed |
|---|---|---|---|
| Surface arrival, field 729, block 0 | Returning from the world map after launch could repeat the unfinished-mission briefing. The lower-landing return already had a separate exclusion. | `AutoScene.skip_if_flag_set=(0x03FE, 0x0040)` suppresses the briefing after launch; `skip_previous_field=364` remains. | Initial entry, lower-landing return, and completed world-map return. |
| Central arrival, field 728, block 0 | The arrival could ask whether the capsule was ready and claim a payload was present after it had been launched. The action itself already selected completed status correctly. | Arrival now observes Central Control and asks to examine the console without asserting payload state. The Central Control script is unchanged. | Completed revisit must reach completed block 20 without suggesting another payload. |
| West bulkhead, field 376, e23 | Every operation first displayed the five-page Strategic Outcome Model, including repeat attempts and already-open use. | Blocks 39–41 provide Operate / Read archived report / Leave and direct locked/open status. Existing report 19 is optional. | All three choices before Guardian, after Guardian, and after opening; reading or leaving must not operate the door. |
| Authorization handoff, field 376, block 6 | It directed the party toward its Gears without clearly advising preparation for the approaching forced encounter. | The handoff identifies active Custodian defense and advises checking equipment before descending. | Warning precedes descent and remains readable. This is preparation guidance, not a change to battle statistics. |
| Research archive, field 361, e16, source block 0 | The repeatable full record ended with Elly saying the Auxiliary Grid should be restored "now", even if either independent power control had already restored it. | The final sentence now explains that the accelerator banks have a separate interlock. No script or progression change. | Read the full record before and after using each grid control, including a revisit. |

The final row was established from the interaction logic: e12/e13 independently set the Auxiliary bit, while e16 always permits the optional full record. It was not merely a wording preference. No other definite new status, directional, or historical contradiction was found in the bound interactions below.

## Live console/shop inventory

### Arrival, research, and progression controls

| Field and source | Bound object / blocks | Role and story connection | Data, state, and reachability assessment |
|---|---|---|---|
| 721 — [Subway terminus](../../modules/mass_driver/content/field_397_subway_end.authored.json) | Archive station **e14 → 0** | Optional history: the 6072 civilian probe, Lena, Aron, and Mira establish what the facility used to do. | Repeated examination is appropriate for an archived record. The probe's separate engines explain how its journey continues beyond the accelerator. Its open-ended promise agrees with the later Mira letter. Bound by `OptionalInteraction`, then aligned to the freestanding archive station. |
| 721 — same source | Maintenance robot **e11 → 1, 2; first use 3** | Optional support: item and Gear-part shops; surviving machinery makes the ancient workplace usable. | The shop actually dispatches the item/Gear categories advertised. Elly's first-use observation has a persistent seen bit. The generic exit line does not promise a specific free repair or reward. Bound by `RepairBotShop`. |
| 363 — [Service junction](../../modules/mass_driver/content/field_363_zeboim_service_junction.authored.json) | South-wall archive reader **e17 → 4**, with separate solid body e12 | Optional final duty log: communication failure, suspended transit, and an unanswered release order. | The abandoned final log is explicitly archival; it need not match the present door's open state. Elly and Emeralda respond to the failed human command chain. Bound by `ServiceJunctionArchiveStation`; this is distinct from the working pressure-lock door. |
| 727 — [Operations junction](../../modules/mass_driver/content/field_377_inner_access.authored.json) | Clock/notice station **e19 → 4**, body e18 | Optional workplace notice: clocking in, reporting suspicious activity, safety rules. | Relevant mundane detail without a new lore claim. It is a readable notice, not a simulated clock-in requirement: it sets no progression condition. Bound by `InnerAccessClockStation`. |
| 361 — [Control and Research](../../modules/mass_driver/content/field_373_control_research_annex.authored.json) | Auxiliary controls **e12 → 1** and **e13 → 1** | Progression: two access points for the same Auxiliary Grid. | Both set bit 0 of 0x03FE before reporting restored power. They do not set the accelerator bit or claim the entire Central Gate is open. Reuse is idempotent. Bound by two `InterlockInteraction` entries. |
| 361 — same source | Guidance archive **e16 → 2, 3, optional 0** | Progression clue plus optional history: Directive 0320, command-loss policy, and its safety exemptions. | The short summary supplies **0320** and the Defense Archive destination immediately; Close is the default. The letters are optional and do not add a hidden requirement. The record sets clue bit 2. Its only confirmed stale instruction is corrected in V170, as recorded above. |
| 722 — [Materials Storage](../../modules/mass_driver/content/field_374_storage_annex.authored.json) | Materials archive **e14 → 9, 10, optional 8** | Progression clue plus staff history: four independent authorities are consolidated and Safety is bypassed. | Summary supplies **A-2, B-5, C-8, D-4** and the downstream terminal. These match the actual five-stage authorization check. Clue bit 3 is supplied even when the player closes the optional letters. The document contains separate record headers; its initial 6079 mail does not prove that every later appended directive entry is also dated 6079. No demonstrated dating error. |
| 368 — [Accelerator archive](../../modules/mass_driver/content/field_368_archive_annex.authored.json) | Main control **e13 → 0** | Progression: Archive Console **D** restores the magnetic banks. | Sets accelerator bit 1 before reporting that the rail condition is satisfied. This is the actual Console D named by the other live control records. Administrative room/file labels must not be confused with the terminal's in-world letter. |
| 368 — same source | Mail reader **e14 → 1** | Optional history: the 6081 attack, blackouts, and Aron's deterrence rationale. | Clearly saved mail, not a current attack warning. Its main-console routing note agrees with e13. It develops Aron's later acknowledgment that readiness failed. |
| 728 — [Central Control](../../modules/mass_driver/content/field_369_archive_control.authored.json) | Standing keypad observation **e12 → 1** | Optional environmental observation; the conspicuous terminal has a different role from the central launch panel. | Repeatable and state-neutral. It neither requests the obsolete Central code menus nor starts the finale. Its controller is separate from e13. |
| 728 — same source | Launch console **e13 → 11 / 20 / 12 and protected sequence / 35** | Required conclusion: authorization, Elly's subjective memory, Citan's guidance correction, launch. | The completion action checks completed status first, giving **20**; lack of authorization gives **11**. The normal first launch emits prelude 12, the protected memory/boundaries, and 35. A seen-memory branch proceeds without replaying the vision. Directions back through five magazines to Defense Archive are correct. The V170 arrival change does not alter this state machine. |

The Central memory and boundaries — **21–34 and 36** — remain protected. Blocks 33–34 are not reactivated by this audit. The native historical actors, cameras, timing, sound, and transition behavior are outside the authorized editorial changes.

### Optional staff archives

Each paired archive below has two distinct installed readers: **e14 shows block 0**, and **e13 shows block 1**. Both are ordinary repeatable examinations. Their dates describe stored documents, not current facility status. The interpretation column explains why they belong; it does not treat every character's belief as objective historical fact.

| Field and source | Block 0: archive mail | Block 1: operations desk | Relevance and accuracy assessment |
|---|---|---|---|
| 366 — [Launch-support archive](../../modules/mass_driver/content/field_366_archive_annex.authored.json) | 6078: Aron answers a dimensional question before recognizing a warhead request. | Funding and institutional access replace an open charter amendment. | Specific mechanical cooperation becomes political complicity. The accounts agree with the 6079 conversion records; no new present-day task is implied. |
| 369 — [Archive E](../../modules/mass_driver/content/field_369_archive_annex.authored.json) | 6081: several leaders repeat the same advice; Aron worries about Mira in Shelter Four. | Emergency authority bypasses an absent safety officer; Mara asks who signed. | Staff can notice recurring rhetoric without knowing Miang's full nature. Aron's reply keeps deterrence personal; Mara's response concerns a concrete signature. No later identity revelation is supplied. |
| 370 — [Archive F](../../modules/mass_driver/content/field_370_archive_annex.authored.json) | 6081 medical crisis and Kim's proposed response. | Clinics request standby generators withheld for strategic readiness. | Links the civil/military resource conflict to the setting's short life expectancy and fertility crisis. Mara's judgment that Kim is addressing the underlying damage is a staff opinion, not a claim that she understands all nanotechnology. |
| 371 — [Archive G](../../modules/mass_driver/content/field_371_archive_annex.authored.json) | Explicit 6077, 6081, and 6083 sections trace Kim's exclusion, sponsorship, and laboratory assault. | State ownership of the colony and an order copied to unrelated Payload Safety. | Dates remain individually labeled. Emeralda asks to leave; Elly accepts. They do not solve Emeralda's later Lighthouse recognition or consciously recover the whole family history. The unexplained circulation is itself the point of Mara's question. |
| 724 — [Archive H](../../modules/mass_driver/content/field_724_archive_annex.authored.json) | 6083: Aron's failed abort, Mira, the release log, and Lena's unsent letter. | Conflicting warning tracks and a denied recall. | Pays off the 6072 probe promise precisely. Mira's fate stays unknown; Elly does not invent closure. The contradictory warnings are part of the crisis, not inconsistent omniscient reporting. |

The two treasure annexes each have **one** archive reader, rather than the paired arrangement:

| Field and source | Binding | Relevance and accuracy assessment |
|---|---|---|
| 385 — [Civil-payload stores](../../modules/mass_driver/content/field_385_storage_treasure_annex.authored.json) | **e14 → 2** | The restored appropriation comes with military claims on the rail and bays. The director's resistance and Lena's public manifest are specific attempts to keep civilian work alive. No extra approval quest is attached. |
| 386 — [Strategic stores](../../modules/mass_driver/content/field_386_storage_treasure_annex.authored.json) | **e14 → 2** | Mara refuses certification; alternate approval removes her from the list. This develops the four-authority system's failure rather than adding a new code. Her disappointment and Lena's request to keep a copy are consistent with their other records. |

### Defense Archive: each physical console

The six `DefenseArchiveRecordTerminal` specifications require care: **e21 is deliberately replaced by the arcade/video program**. The list of six original record IDs is not evidence that six reports are independently readable.

| Object in field 376 — [source](../../modules/mass_driver/content/field_394_defense_archive.authored.json) | Live blocks / role | Accuracy, story connection, and state assessment |
|---|---|---|
| Authorization wall console **e13** | **1–7, 13–15**; progression | The displayed choices and accepted values agree: 0320, A-2, B-5, C-8, D-4. Missing-record messages point back to Research or Materials through the east stairs. Manual entry is intentionally allowed even without recorded clues; knowledge and possession of clue flags are separate. Invalid values do not confer authorization. Reuse gives status 3. Success 6 unlocks the north lift and now warns about Guardian preparation. |
| National Security Brief **e20** | **16**; optional history | Economic contraction, failing infrastructure, violence, and emergency rule establish the crisis exploited by the adviser. The final readiness claim is explicitly the adviser's summary, not the narrator's endorsement. |
| Arcade/video computer **e21** | **37–38**; games, or **23–24, 25–30, 33, 35** for video | Arcade choices actually select NUKE or Missile Command; Back and Leave have exit paths. Video requires the disk and permits cancellation. Startup says **6081–6083**, the opening report is **6081**, and the final clip explicitly announces the next **6083** recording. This fixes the earlier uninterrupted-date ambiguity. The stories explain social collapse and the nuclear exchange. Arcade controls and score displays are also generated directly by the builder, outside authored dialogue; they are optional activities and not lore evidence. |
| Public Information Archive **e22** | **18**; optional history | A 6079 public preservation claim is juxtaposed with the same-day cancellation of civilian launches. The unsent editor's response concerns the trusted space-program name. The contradiction is deliberate propaganda versus internal record. |
| West bulkhead panel **e23** | V169: **19** followed by control logic; V170: **39–41**, optional **19** | The outcome model predicts catastrophe regardless of first strike/retaliation; the sealed policy response exposes institutional failure. It is meaningful history, but should not be forced every time the door is used. V170 separates the report and command. Operate checks the open bit, then Guardian victory; Read and Leave do not write the door bit. |
| Directive draft log **e24** | **20**; optional history | Shows the change from holding after lost contact to release unless recalled, and the removed expiration. The current terminal status concerns the still-live old directive, not a claim that present-day Zeboim is intact. This explains why obsolete authorization can still operate the facility. |
| Executive routing audit **e25** | **21**; optional history | Identifies the adviser by the recorded name Miang and contrasts her control of options with the director's signature. Mara's unsent interpretation fits what the paperwork exposes. Reading it does not grant the party later cosmic knowledge or activate the dormant Central explanation. |

**Procurement audit block 17 is compiled but is not emitted by the current e21 action.** Its material is not contradictory, but it must not be counted as an extra live console or required exposition. The staff archives independently establish the military conversion.

### Five reserve magazines

All five magazines enter silently. Each has the same separately installed reader **e7 → block 0**, distinct from its north/south exits. These are **five optional stations**, not five mandatory entry speeches.

| Field and source | Purpose and story connection | Accuracy/state assessment |
|---|---|---|
| 377 — [Magazine 1](../../modules/mass_driver/content/field_673_silo_vault_1.authored.json) | Establish the reserve scale and lost targeting network. | Lost strategic target data does not imply that a newly configured capsule cannot use the accelerator. Elly infers a reserve from visible storage and the readout. |
| 378 — [Magazine 2](../../modules/mass_driver/content/field_673_silo_vault_2.authored.json) | Juxtapose the **6083 launch log** with separately labeled **6079 mail** about funding, certification, and Mira's paper star. | The time shift is explicit. It summarizes an optional staff thread for a reader who may have skipped the side archives. It does not require assuming Mira's eventual fate. |
| 379 — [Magazine 3](../../modules/mass_driver/content/field_673_silo_vault_3.authored.json) | Aron's refusal: leave the targeting link disconnected. | The wording distinguishes restored power from restored targeting. The cradles can remain powered while the weapons network is severed. It preserves the later possibility of salvaging rockets. |
| 382 — [Magazine 4](../../modules/mass_driver/content/field_673_silo_vault_4.authored.json) | Failed calls continue until grid failure; Emeralda notices the persistence. | This is an archived outbound-call log. The terminal does not promise that an active rescue call is presently possible. |
| 383 — [Magazine 5](../../modules/mass_driver/content/field_673_silo_vault_5.authored.json) | Central Control direction and Elly's tombstone reflection. | The northern exit does lead to Central Control. The reflection adapts original Mass Driver narration and is not a voice defect to remove. It does not resolve Emeralda's later identity scene. |

## Other active interactions and the remaining fields

These rows cover all 13 fields outside the 20-field station inventory, plus the non-console interactions located beside live stations. **Quiet does not mean broken:** ordinary native doors need not display every retained label in a dialogue component.

| Field(s) | Actual control/interaction | Authored text status and assessment |
|---|---|---|
| **729** surface lift | Native descent control and world-map exit; automatic opening owned by e17. | Opening **0** is live. Other numbered dialogue is retained in donor/director or retired NPC routines, not additional installed signs. e12's initializer is STOP. V170 adds the completed-mission briefing guard. |
| **364** lower landing | Native ascent back to 729 and onward threshold to 360. | No new archive/sign reader is installed for compiled **0**. The lift-state variable and destination pairing are preserved. Do not describe its retained terminal label as a separate live console. |
| **360, 720** transit tunnels | Automatic reciprocal thresholds. | Staged scripts contain no decoded dialogue references, and current specs install no reader or arrival dialogue. Compiled **0** in each is not displayed signage. |
| **362** transfer airlock | Two native animated doors, hardened to finite traversal, linking 363 and 727. | Current door actions do not emit the retained equalization/venting blocks **1–4**. Do not invent an extra pressure-management puzzle from that prose. |
| **372** service hub | Four local passage controls and route doors to the junction, Research, Materials, and the post-auxiliary stair. | Directory/status blocks **0–8** remain in donor/director task bodies; no current physical reader is installed for them. NPCs e13/e14 have STOP initializers/actions. The apparent fixed "NO POWER" text is therefore not established as a misleading live status screen. Route directions in the text were checked, but should not be advertised as available player guidance. |
| **723, 375** sealed stair connectors | Native passage controls, with the old branch bypassed and finite door handling. | Compiled containment/scan blocks **0–4** are not emitted by the current door actions. These are not two active safety-scan puzzles. |
| **387** vertical connector | Native doors connecting the junction and conduit. | No installed reader for compiled **0**. Its simple shaft label is not additional usable lore. |
| **725** magnetic conduit | Native doors and restored save point **e16**. | The cube performs its native save function; it does not supply an authorization code. No installed reader for compiled navigation blocks **0–1**. |
| **726** launch-support hall | Central Gate controller **e14**; ordinary surrounding exits. | Live blocked states select **0** for missing Auxiliary power or **1** for missing accelerator power. Each names the correct live control location. Both bits permit traversal to Defense Archive. Compiled **2–4** are not current status-console outputs. |
| **367** archive junction | Three native doors: launch support and the two treasure annexes. | No installed reader for compiled junction label **0**. The route graph supplies the three actual destinations. |
| **384** Gear/Guardian hall | Automatic approach sequence, inert parked-Gear interactions, north error control, south return, later recovery entry. | Installed sequence emits **3 → 1 → 2**, battle, then **4**; recovery uses **7 → 1 → 2**. North action displays **5**, accurately describing its offline/nonfunctional route. **0** (GOLIATH label) and **6** are not established live terminal outputs. They must not be presented as confirmed player-facing location errors. |
| **722, 385, 386** treasure | Each native chest **e15** awards Omegasol using independent recorded state. | Receipt/full-inventory blocks **0–1** use the actual item token. Chests do not grant missing story credentials or require reading the adjacent archive. |
| **376** disk pickup | **e26 → 22, 36, 31 / 34; later 32**. | The player may take or leave the disk; inventory-full failure does not award it. Later examination reports the remaining disks damaged. The reader referred to as the computer on the right is the adjacent e21 media console. Its documented placement was checked statically; a fresh visual check remains appropriate. |
| **376** north lift | **e17 → 9** while authorization is missing; otherwise transition to Gear bay 384. | The lock message names the actual five-stage console requirement. The V170 preparation warning is emitted by authorization success before the lift becomes usable. |
| **376** west door | **e14 → 10** until the local panel opens it; then passage to magazine 1. | Text correctly distinguishes beating Custodian from operating the nearby panel. V170 preserves this separate door interaction. |

## Compiled text is not a second hidden dungeon

The following distinctions prevent false conclusions from the transcript:

1. **Central Control:** e12 is one observation and e13 is the launch interaction. The archived index labels **2–9**, cradle label **10**, and superseded authorization entries **13–19** do not constitute independently usable terminals. Central's exhaustive source classification also excludes **33–34** from the emitted finale. Generic decoding can still find legacy director instructions; that does not override the installed-flow classification.
2. **Defense Archive:** **0, 8, 11, 12** are not additional bound speeches or consoles in the current layout. Block **17** is superseded by the media/arcade action as described above. Blocks **16, 18–21** are the five actually available historical reports, with 19 optional from V170's west-panel menu.
3. **Materials:** current archive e14 emits **9 → 10 → optional 8**. Compiled **2–7** belong to an older interaction design; the current reader does not display them. Authorization happens later in Defense Archive.
4. **Launch Support:** the live gate uses **0–1**. The previously suggested stylistic rewrite of block **2**, the Materials block **3** rewrite, and the Defense Archive block **0** rewrite would not improve a current player interaction. Those earlier optional suggestions are withdrawn from the live-edit list.
5. Dormant source dialogue is neither proof of an unimplemented promised feature nor permission to activate it. In particular, do not resurrect a donor sign, duplicate code menu, or protected explanatory scene merely to make every compiled block reachable.

## Overall story and usability judgment

The staff consoles form a coherent progression: civilian exploration in 6072; strategic access in 6078; funding and payload conversion in 6079; emergency doctrine and civil/medical collapse in 6081; release, failed recall, and personal loss in 6083. Explicitly collected records sometimes juxtapose dates. Institutionally approved claims and a worker's unsent response are intentionally different viewpoints.

The optional stations are specific enough to justify their presence. They develop Aron's responsibility, Lena's concern for the civilian project and Mira, Mara's attempts to enforce safety, and the director's constrained authority. Emeralda's observations and refusal, Elly's uncertainty about Mira, and the later launch do not need another bonding scene or a new explanatory record. The history supports the mission without prematurely explaining the Lighthouse or later catastrophe.

Progression data is consistent across the bound readers: **two power bits**, the **0320** directive, the **A-2/B-5/C-8/D-4** sequence, authorization before the north lift, Guardian victory before local bulkhead release, five magazines, then Central Control. Brief clue acquisition already permits skipping long correspondence. V170 similarly separates the west door command from its long report.

The accurate answer to "were all the consoles audited?" is: **their installed purposes, emitted text, story relevance, and state branches have now received this source-level audit; every physical interaction has not been replayed and verified in-game.** The remaining runtime questions concern reaching the correct frontage, input behavior, readable windows, branch transitions, and revisit/save persistence. This audit does not turn those unknowns into passed tests.

## Implementation evidence pointers

Function names remain the primary locators if later edits move line numbers. The source snapshot inspected near completion had builder SHA-256 `76defa4160196133c6b051ca5be009c568b6bf753a6d39e1dbff954a97f123e0`; release/build verification belongs to the V170 candidate report.

| Evidence | Location |
|---|---|
| Current route, explicit clone bindings, reciprocal doors | [build.py](../../modules/mass_driver/build.py:5226), `_CLONE_SPECS`, `CLONES`, `ROUTE_EDGES`, `VISIBLE_DOOR_CONTRACTS` |
| Repeatable archive readers | [build.py](../../modules/mass_driver/build.py:17139), `_install_optional_interaction` |
| Clock notice and junction archive | [build.py](../../modules/mass_driver/build.py:17202), `_install_inner_access_clock_station`; `_install_service_junction_archive_station` |
| Robot/shop and first-use state | [build.py](../../modules/mass_driver/build.py:18462), `_install_subway_archive_robot_script`; `_install_repair_bot_shop` |
| Power controls and optional full-record menus | [build.py](../../modules/mass_driver/build.py:18625), `_install_interlock_interaction` |
| Actual authorization values and state checks | [build.py](../../modules/mass_driver/build.py:19749), `_install_authorization_terminal` |
| Media override and six physical archive stations | [build.py](../../modules/mass_driver/build.py:17769), `_install_defense_archive_record_terminals` |
| V170 west-panel menu and independent report | [build.py](../../modules/mass_driver/build.py:17691), `_defense_archive_west_bulkhead_action` |
| Guardian hall, dormant donor interactions, recovery | [build.py](../../modules/mass_driver/build.py:20118), `_install_goliath_factory_hall` |
| Optional magazine terminals | [build.py](../../modules/mass_driver/build.py:20709), `_install_cloning_silo_gallery` |
| North lift and Central Gate locks | [build.py](../../modules/mass_driver/build.py:21518), `_install_defense_bay_lift_exit`; `_install_interlocked_door_exit` |
| Central state machine and surface briefing guard | [build.py](../../modules/mass_driver/build.py:23243), `_install_completion_interaction`; `_repoint_auto_dialogue` |
| Central compiled/live classification | [export_mass_driver_dialogue.py](../../modules/mass_driver/tools/export_mass_driver_dialogue.py:28), `CENTRAL_LIVE_DIALOGUE_IDS`; [V169 transcript](../mass-driver-dialogue-v169.md) |

## Independent V170 script regression review

After completing the inventory, this reviewer compared the current builder with `work/mass-driver-v170-20260925/baseline/modules/mass_driver/build.py` and generated the relevant scripts from identical extracted inputs. This was a separate comparison with the saved baseline, rather than acceptance of new digest constants alone.

| Field | Independent result |
|---|---|
| **376** Defense Archive | The script grows from **48,958 to 49,157 bytes**. Only the e23 action-2 entrypoint changes, from **46,606 to 47,034**; the menu occupies a **199-byte appended suffix**. Restoring that one pointer reproduces every original byte through the old end of the script. Existing video, arcade, worker, door-helper, and other record program counters are retained. |
| **729** surface | The script grows from **2,253 to 2,264 bytes**, with no changed entrypoint values. Omitting only `skip_if_flag_set` from the current specification reproduces the baseline script exactly. The added condition checks the existing completed-launch bit; it does not allocate or write state. |
| **728** Central Control | The entire **3,593-byte script** remains identical to the baseline, SHA-256 `39f7a1cf08cbe8721ac39fa471a29b69a9e5ca1a944948c88cbd0f6bda73c020`. This check concerns the whole generated script; the coordinating task owns the separate compiled-dialogue and component protection checks. |

The conditional directions were also checked against the local Noah `OP_JUMP_IF` implementation: conditions 0x40/0x41 branch on inequality/equality respectively, while 0x46 branches when the requested mask is clear. Thus a completed surface visit reaches the one-shot terminator without acquiring input locks, and the existing lower-landing exclusion remains independent. The unguarded caller default preserves previous behavior.

The west menu uses the same actor-owned choice convention as the existing media menu. Its Read branch shows report 19 and returns to the menu; Leave and unexpected choice values restore control without dispatching helpers or writing progression. Operate first checks the existing opened bit, then Guardian victory. Only the unopened, post-Guardian path plays the existing release sound, calls the existing two door helpers, and sets the existing open bit. Repeated operation reports open status without replaying the release. Every terminating branch restores control, and input-release waits protect entry and the return from the report.

No additional regression defect was identified in this comparison. The new behavioral tests were inspected as supporting coverage; this subtask did not run the full suite or an emulator. Menu placement, physical input, animated door completion, and save/revisit behavior remain runtime acceptance items.

Only this audit document was written by this review subtask. All source changes described above were implemented by the coordinating task under the user's accepted V170 scope.
