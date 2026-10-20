# Chapter 2: The Champ — missing-story interludes

The current release path uses `chapter_two_interludes.py` and
`content/chapter_02_interludes.json`. The former expanded battle route remains
available only to explicit historical builder calls and regression fixtures.
It is not the Chapter 2 release graph.

## Story boundary

The eventual destination is seamless insertion into the original campaign.
For this prototype, short time/location captions bridge its unchanged events. Original
dialogue, fights, puzzle solutions, rank outcomes and rewards are not recreated
inside Rico's new scenes. Continuing advances only this anthology's private phase
state; it does not execute or mark original events complete.

Chapter 2 begins with Rico in his rooms during Fei's recovery. It ends with
a brief "After the Group League / Central District" caption. Neither the
incident, his original hiding scene, nor the locked-room
discovery is staged here. Completion returns to Chapter Select; it does not
automatically launch the older Chapter 3 draft.

| Interval | New material | Original story boundary |
|---|---|---|
| During Fei's recovery | Suzarn suggests assigning the unconscious newcomer the bottom rank. Rico insists on seeing him fight first. | Before native awakening, summons and introduction (213/104, 213/26–30, 218/2–10). |
| After the Baptism | Suzarn wants the title and freedom. Rico respects her ambition as a possible rival. | After all native rank branches in 199; before Fei's early Battling events. |
| After Suzarn's death becomes known | Rico remembers the fight she expected to win. He decides to approach Fei himself. | After 211/70; before the original apology and request to investigate in 213/78–97. |
| After the sewer return and original care | Rico fears letting his opponent see how badly his arm is affecting him. | After the return, care and rivalry conversation in 211/178–201; before the Finals. |
| After the Finals | Rico questions where he could have gone had he accepted the pardon. No definitive reason for refusing it is supplied. | After 221/154–159; before Group League and Rue's later visit. |
| Before Group League | Rico's resentment over the expulsion persists after losing his title. No family connection or plan is disclosed. | Before the original incident later described in 218/35. |

Field/dialogue references above identify native source evidence, not new calls.
The data file retains the complete preceding/following anchor notes.

The arc is deliberately unfinished here. Rico begins by trusting strength as a
fair measure, including Suzarn's ambition to challenge him. Her death, his own
injury and the loss of his title expose the limits of that belief. He takes a
small step toward personal responsibility by going to Fei himself, but his
isolation and resentment toward Sigmund remain unresolved. Later new scenes
must develop belonging without rewriting existing choices or revealing family
information early.

Voice references are the retail Suzarn dialogue in 213/26–30, 218/2–5 and
199/2–4, 20, 33; Rico's uncertainty and responsibility in 213/83–92, his guarded
response to concern in 211/183–191, and his defeat in 221/146–159. Hammer's
supplier talk and deference inform his brief attempts to help. The new dialogue
is authored expansion, not recovered or restored original script.

## Playing this prototype

Start New Game and select **The Champ**. Rico can explore his rooms, Latina's
Bar, the D Block street and the dormitory. Inspect the bout card in his room or
the bed next door, then choose **Continue** to cross to the next interval.
**Stay here** keeps the current interval. A scene plays once per interval.

Suzarn remains available in intervals 1–2. Hammer remains in 1–3; his repeat
after Suzarn's death is specific to that moment. Intervals 4–6 are solitary in
Rico's room. Every retained resident receives distinct optional speech. Rico
listens during these interactions; his spoken replies belong to story scenes.
Anonymous residents have no name labels or portraits; named speakers use their
allocated portraits and yellow names. In-scene text contains spoken dialogue
only. Action descriptions, stage directions, interior prose and event summaries
are not printed. Short time/location captions and system prompts remain outside
the spoken scenes. The existing actor staging is unchanged; no new prop assets
or hand animations are claimed.

The original physical route is Champion's rooms → Latina's Bar → D Block street
→ dormitory. The Wildcat is a separate establishment. The native stairs, door
entries and walkmesh are retained. The Champ plays upstairs; Nortune plays in
the bar, street and dormitory.

## Implementation and limits

Only five existing anthology locations are emitted. The nine former intake,
yard, preparation, sewer, arena and flight clones and their Chapter 2-only
battle/cinematic copies are omitted. There is no playable Baptism, forced rank,
Rico-led sewer quest, added title-defense battle, recreated Finals or Stier crash.
The party is Rico alone throughout the interludes.

Reserved variable 0x03EC stores availability bits 0–5 and seen bits 8–13; 0x07D0
is its field-local mirror. The launch and hub reset clear this state. Old v8
objective masks and emulator save states are incompatible; enter the chapter
through the selector to initialize the current format.

This remains a standalone anthology. Its bootstrap, party initialization and
remaining repurposed Disc 1 field slots are not compatible with ordinary retail
save progression. Seamless campaign hooks, entry/return state preservation and
the later Rico chapters still require a separate audit and implementation.

Native script, geometry, resource and control-flow tests do not constitute an
emulator playthrough. Build receipts record runtime status separately.
