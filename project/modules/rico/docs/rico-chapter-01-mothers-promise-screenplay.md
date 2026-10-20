# Rico's Arc — Chapter 1: Mother's Promise

## Complete routed screenplay and interaction script

> Current-build transcript for the playable Chapter 1 mod. This document includes every player-facing line, choice, conditional reminder, repeat interaction, and automatic story scene in the active route.

## Scope and notation

- Dialogue-window control codes have been removed. A paragraph break represents an in-game page break where one exists.
- **Bold names** identify speakers. *Italic prose* is displayed narration.
- *[Visual only]* identifies an animation, camera action, fade, movement, or other staging that occurs without a text box.
- The house is interactive, so its branches do not have one mandatory viewing order. The required task sequence and every optional branch are both documented below.
- Authored blocks 1 and 11 are retired draft directions and are never routed to the player. They are listed in the final appendix for provenance, not presented as part of the active screenplay.
- Every displayed sentence remains within one in-game page. Chapter 1 windows are fitted to the widest and tallest page they contain, up to the safe native 58-by-7 maximum.

## Contents

1. Chapter-select framing
2. Scene 1 — Anne and Rico's house
3. Required household sequence
4. Optional and repeatable house interactions
5. House-door reminder branches
6. Scene 2 — Gathering firewood
7. Scene 3 — Rico returns home
8. Scene 4 — Before dawn
9. Scene 5 — Anne's funeral
10. Chapter completion destination
11. Chapter 1 menu and inventory presentation
12. Retired authored blocks and active source map

## Chapter-select framing

*[At the Chapter 1 memory light on the Path of Sephirot.]*

### Choice

**CHAPTER 1: MOTHER'S PROMISE?**

- Enter
- Not yet

If **Not yet** is selected, the prompt closes and Rico remains at the chapter-select hub.

If **Enter** is selected:

---

**CHAPTER 1**  
**MOTHER'S PROMISE**

*[Music: “Faraway Promise” begins (native field-music ID 0x08).]*

*Many years before D Block calls him the Champ, young Rico lives with his mother, Anne, in the poor settlements beyond Nortune's outer wall.*

*As Anne's illness worsens, one cold day becomes a turning point in Rico's life.*

*Though Anne passes away when Rico is only ten years old, the words she leaves behind remain with him, shaping the man he will one day become...*

---

## Scene 1 — Anne and Rico's house

**INT. ANNE AND RICO'S HOUSE — COLD, RAINY DAY**

*[Visual only: Young Rico is playable inside the worn one-room house. Anne stands near the bed. A kettle rests on the cold cooking stove beside the room's small cooking canister, used in the narration as the jar of dried herbs. Two dented water buckets stand underneath the window, the small blue flower stands in its rusty orange clay vase on the table, and a separate round iron woodstove glows weakly near the middle of the room.]*

*[Visual only: Anne coughs as the scene begins, returns to idle, and coughs periodically while Rico remains in the house. Her authored dialogue branches also trigger a visible cough animation. No cough stage direction appears in a dialogue box.]*

No dialogue plays automatically on entry. Before speaking to Anne, Rico may inspect the room and the central woodstove, but he cannot operate its valve until Anne assigns the chores.

### Initial environmental interactions

#### Settlement-facing window

*Rain streaks the glass. Beyond the low roofs, Nortune's outer wall rises beneath a pale sky.*

This line repeats on later inspections.

#### Gate-facing window

*The road toward Nortune's gate is gray with rain.*

*The poor settlement huddles outside the Imperial Capital's wall.*

This line repeats on later inspections.

#### Side window by the bed

*Rico looks through the glass at the weathered houses of the poor settlement on Kislev's outskirts. Beyond them, the Imperial Capital fades into the cold haze.*

This line repeats on later inspections.

#### House door, before Rico speaks to Anne

**RICO**  
I can't leave Mom right now.

#### Water buckets, before Anne assigns the chores

*Two dented water buckets stand underneath the window. Both hold clear water. A ladle rests across the nearer rim.*

#### Cooking stove and kettle, before Rico gathers water

*A worn-down iron cooking stove stands beside the counter. The empty kettle rests on its cold cooktop. A small chipped cup sits beside the jar of dried medicinal herbs.*

#### Flower, before Rico has water for it

*A small blue flower rises from a rusty orange clay vase. Its pale blue bells hang over dry soil.*

### Rico speaks to Anne

*[Visual only: Anne coughs.]*

**ANNE**  
Rico... come closer, my sweet boy. Don't hide your hands from me.

**RICO**  
The kids near the city gate called me a beast today, Mom. They threw stones. They said monsters like me don't belong in Kislev.

**ANNE**  
Listen to me carefully, Rico. People often fear what they do not understand.

Sometimes that fear hardens into hate.

**RICO**  
It hurts, Mom.

**ANNE**  
What those children did was cruel. Their violence does not excuse violence in return.

If you hurt them back, the hatred only finds a new home. Mercy is choosing to end that cycle.

Your body is strong, but keep your heart gentle. Never let their cruelty decide who you become.

**RICO**  
I'll try, Mom.

**ANNE**  
I know you will.

Now... help me with a few tasks today, alright?

### Anne assigns the chores

**ANNE**  
Rico, would you fetch some water from the bucket and make me some tea?

## Required household sequence

### Task 1 — Gather water for the kettle

When Rico interacts with the water buckets after speaking to Anne:

*Rico dips the ladle into the nearer bucket and gathers a ladleful of clear water.*

The interaction ends there. Rico remains controllable to carry the water across the room to the cooking stove.

### Task 2 — Fill the kettle and turn on the cooking stove

When Rico returns to the cooking stove with the first ladleful:

*Rico fills the kettle with water from the ladle.*

The kettle remains on the cooktop.

#### Choice

**Turn on the stove?**

- Turn It On
- Leave It Off

#### If Rico chooses Leave It Off

*Rico leaves the stove off for now.*

On the next interaction, the kettle is still filled and resting on the stove. The game returns directly to the **Turn on the stove?** choice without asking Rico to place the kettle again.

#### If Rico chooses Turn It On

*[Sound only: One short Zeboim computer power-click plays. No computer boot-up sounds follow.]*

*[Sound only: A moment later, the burner catches with a brief fire crackle.]*

*[Visual only: Anne coughs.]*

*Rico turns on the cooking stove. Heat begins to build beneath the kettle.*

**RICO**  
The stove is on, Mom. It'll boil soon.

**ANNE**  
Thank you, Rico.

**ANNE**  
Second... take another scoop of water from that same bucket.

Give a drink to the stonebell in the vase on the table.

Then open the woodstove valve so more heat can spread through the house.

*[System action: The kettle's background boil timer begins after this exchange. The water reaches a boil after approximately fifteen seconds of active field time, not instantly. Rico remains controllable while it heats.]*

### Task 3 — Gather water for the flower

If Rico tries to take the second scoop before turning on the cooking stove:

**RICO**  
I need to turn on the stove before I take water for the flower.

After the cooking stove is on:

*Rico dips the ladle into the same bucket again and lifts a careful scoop for the stonebell.*

After both requested scoops have been taken, later bucket inspections display:

*The ladle rests across the bucket. Rico has taken all the water Anne asked for.*

### Task 4 — Water the flower

If Rico inspects the vase before gathering the second scoop:

*A small blue flower rises from a rusty orange clay vase. Its pale blue bells hang over dry soil.*

With the second scoop in hand:

*Rico tips the ladle slowly, giving the stonebell a drink. Its pale blue bells lift above the damp soil.*

*[Visual only: Anne coughs.]*

**ANNE**  
Do you remember where you found that stonebell, Rico?

**RICO**  
In the streets near the market.

I felt bad because it was stepped on.

Remember you said we could try to save it?

**ANNE**  
Yes, I remember.

That stonebell is the most precious gift I've ever received.

Look how healthy it is now because you've been taking care of it.

Stonebells take root between bare stones, where almost nothing else can grow.

Still, their pale blue bells always turn toward the light.

You have a good soul, Rico.

Never let this world forget that.

**RICO**  
I won't, Mom...

Later vase inspections display:

*The stonebell's pale blue bells lift above the damp soil.*

### Task 5 — Open the central woodstove valve

The round iron woodstove can be inspected at any time, but its valve choice remains unavailable until Anne assigns the chores. The choice becomes available immediately afterward and stays available, including while the kettle heats. Opening the valve is still a required chore and gates both the completed tea handoff and the house door.

On the first interaction:

*A low fire glows inside the round iron woodstove. Its valve is nearly closed, holding back the heat.*

#### Choice

**Open the valve?**

- Open Valve
- Leave It Closed

#### If Rico chooses Leave It Closed

*Rico leaves the valve closed for now.*

On the next interaction, the opening woodstove description appears again before the choice is offered again.

#### If Rico chooses Open Valve

*Rico opens the valve. The fire takes a deeper breath, and more heat spreads through the house.*

Later inspections display:

*The open valve feeds the round iron woodstove, and steady warmth spreads through the house.*

### Task 6 — Wait for the boil and prepare the herbal tea

Rico can water the flower, inspect the room, read, or complete the woodstove-valve chore while the kettle heats.

The cooking-stove response varies with the flower and kettle state.

#### Flower not watered; kettle not yet boiled

*The cooking stove is on. The water is heating. Rico still has the flower to water.*

#### Flower watered; kettle not yet boiled

*The cooking stove is on. The water is heating, but it has not boiled yet.*

#### Kettle boiled; flower not yet watered

*The kettle has boiled, but Rico still has the flower to water.*

#### Flower watered and kettle boiled

*The kettle begins to whistle. The water has boiled.*

*Rico takes a pinch of dried medicinal herbs from the jar on the counter and places it into the cup.*

*He pours in the steaming water, then sets the kettle back on the cooktop.*

*The herbal tea is ready for Anne.*

### Task 7 — Bring the cup to Anne

After Anne assigns the chores and before Rico delivers the cup, checking on her identifies the next unfinished task. Each branch begins with a visual cough and contains no printed cough direction.

#### Water for the kettle is next

*[Visual only: Anne coughs.]*

**ANNE**  
The bucket and ladle are in the corner, my sweet boy.

Bring water for the kettle first.

#### Turning on the cooking stove is next

*[Visual only: Anne coughs.]*

**ANNE**  
The stove is still cold, Rico.

Turn it on beneath the kettle so the water can heat.

#### Gathering the flower's water is next

*[Visual only: Anne coughs.]*

**ANNE**  
The kettle can heat while you take another scoop from the bucket.

The stonebell needs a drink.

#### Watering the flower is next

*[Visual only: Anne coughs.]*

**ANNE**  
You have the water, Rico.

The stonebell's soil is still dry.

#### Opening the woodstove valve is next

*[Visual only: Anne coughs.]*

**ANNE**  
The woodstove valve is still nearly closed, Rico.

Open it so more heat can spread through the house.

#### Waiting for the kettle is next

*[Visual only: Anne coughs.]*

**ANNE**  
The flower has its water now.

Give the kettle a little more time to boil, my sweet boy.

#### Preparing the cup is next

*[Visual only: Anne coughs.]*

**ANNE**  
The water should be ready now, Rico.

Please finish the tea and bring it to me.

### Rico delivers the prepared cup

*[Visual only: Anne coughs.]*

**RICO**  
I brought your cup, Mom.

**ANNE**  
Thank you, Rico.

*Rico brings Anne the cup and steadies it while she takes a small drink.*

*She presses the cloth to her mouth. When she lowers the cloth, Rico sees blood.*

**RICO**  
There is blood again. The medicine isn't helping.

Tell me what to do, Mom. I can find another doctor.

**ANNE**  
The doctors can do no more.

This sickness will take me soon.

**RICO**  
No. There must be something I can do.

I can't just let you die.

**ANNE**  
You cannot fight this sickness for me, my sweet boy.

But you can choose what you carry after I am gone.

**RICO**  
What do you want me to carry?

**ANNE**  
Mercy.

After I am gone, you may feel angry at the whole world.

Do not make others suffer because you are suffering.

One day, you may have power over those who looked down on you.

Use that power to protect people, not to take revenge.

Then the cruelty that wounded us will end with you.

Promise me.

**RICO**  
I will. I promise.

**ANNE**  
Rico, the fire in the woodstove won't last through tonight.

Would you bring in the dry slats stacked outside beside the house?

**RICO**  
I'll be just outside. Call if you need me.

**ANNE**  
I will.

Take only what you can carry. The rest can wait.

If Rico speaks to Anne again before leaving:

*[Visual only: Anne coughs.]*

**ANNE**  
The dry slats are stacked just outside, beside the house.

Take only what you can carry, Rico.

## Optional and repeatable house interactions

The reading scene does not gate the door and is available at any time. The meal scene is also optional and becomes available after Rico prepares the tea.

### Reading desk

On the first interaction:

*[Visual only: Anne coughs.]*

*Rico inspects The Emerald Traveler, a book his mother has been reading with him.*

*It tells of a heroine whose journey will be key to saving the world.*

Later inspections display:

*The Emerald Traveler lies open where Rico and his mother stopped reading.*

*Its heroine's journey will be key to saving the world.*

### Meal bowls on the cooking counter

This interaction becomes active after the herbal tea has been prepared.

*[Visual only: Anne coughs.]*

*A dented pot and two chipped bowls sit on the narrow counter. Anne taught Rico how to make a handful of grain feed them both.*

**RICO**  
You always give me the fuller bowl.

**ANNE**  
And you always put some back when you think I am not looking.

**RICO**  
Then give me the smaller bowl.

**ANNE**  
And miss this argument?

Later inspections display:

*Two chipped bowls sit beside the dented pot. Neither bowl stays fuller for long.*

## House-door reminder branches

The door uses the first unfinished step in the order below. Only one reminder appears per interaction.

### Before Rico has spoken to Anne

**RICO**  
I can't leave Mom right now.

### Before gathering water for the kettle

**RICO**  
Mom asked me to fill the kettle.

The bucket and ladle are in the corner.

### Before turning on the cooking stove

**RICO**  
I need to turn on the stove so Mom's water can boil.

### Before gathering the second scoop

**RICO**  
Mom asked for another scoop from the same bucket.

It is for the stonebell.

### Before watering the flower

**RICO**  
I have water in the ladle.

The stonebell's soil is still dry.

### Before opening the woodstove valve

**RICO**  
The woodstove valve is still nearly closed.

I need to open it so the room stays warm for Mom.

### Before preparing the herbal tea

**RICO**  
I still need to finish Mom's tea at the stove.

I need to put a pinch of medicinal herbs in the cup.

Then I can pour in the hot water and bring it to Mom.

### Before delivering the cup

**RICO**  
I have Mom's cup of hot tea.

I should take it to her now.

### Successful departure

Once Rico has spoken to Anne, gathered both scoops, turned on the cooking stove, watered the flower, opened the woodstove valve, prepared the herbal tea, and delivered the cup, the following exchange plays at the door.

*[Visual only: Before the door opens, Rico turns away from it to face Anne.]*

**RICO**  
Mom... how come I don't have a dad?

*[Visual only: Anne coughs.]*

**ANNE**  
Rico, you do have a father.

**RICO**  
Then where is he?

**ANNE**  
He's... away.

Fighting in the war.

**RICO**  
Is he ever coming back?

**ANNE**  
W-Well... that is...

I don't know.

**ANNE**  
But your father is a great man, Rico.

And someday...

I know you'll follow in his footsteps.

*[Visual only: The wooden door opens with its native hinge sound. Rico walks to the inner threshold. The screen fades to black.]*

## Scene 2 — Gathering firewood

**EXT. POOR SETTLEMENT OUTSIDE NORTUNE — PALE DAYLIGHT**

*[Visual only: Fade in on a residential exterior. Young Rico stands at the house door. A fixed establishing camera holds on the low facade and broken packing crate while Rico walks to the crate, then shifts to the closer work composition.]*

*Outside their house, pale daylight lies over the settlement beyond Nortune's outer wall.*

*Beside the house, Rico pulls the driest slats from the broken packing crate and gathers a small armful for the stove.*

**RICO**  
These will burn.

This should keep Mom warm tonight.

*[Visual only: A short fade conceals the pickup. Rico walks back to the house. The screen fades to black.]*

## Scene 3 — Rico returns home

**INT. ANNE AND RICO'S HOUSE — DAY INTO NIGHT**

*[Visual only: The real bedroom door opens in daylight. Rico walks inside and the door closes behind him. Anne is visible at her sickroom position near the bed. She performs one complete cough animation; no text box appears. The scene then fades to black. Under that blackout, the lighting changes to a subdued blue moonlight grade before the closer sickroom composition fades in.]*

*As night falls, Rico feeds the woodstove until the room is warm, but Anne's shivering has not stopped.*

**RICO**  
The fire is warm now.

Why are you still shaking?

*[Visual only: Anne coughs again; no text box appears.]*

**ANNE**  
This sickness has been with me a long time.

Tonight it is stronger than I am.

**RICO**  
Then I'll get the doctor.

I'll make him come this time.

**ANNE**  
No. Stay with me, Rico.

Just until I fall asleep.

**ANNE**  
My stubborn boy. You have done everything I asked.

*[Visual only: Fade to black.]*

## Scene 4 — Before dawn

**INT. ANNE AND RICO'S HOUSE — BEFORE DAWN INTO MORNING**

*[The following narration box remains visible while the room stays black.]*

*Before dawn, Anne's breathing grows quiet.*

*Rico keeps holding her hand long after it has gone cold.*

*[Visual only: Time passes under black. Anne is removed from the scene rather than shown in an unsupported death pose. The moonlight grade clears, then the empty bed and Rico beside it fade in under daylight.]*

*When morning comes, a local Ethos priest prepares Anne for burial. Rico remains beside the empty bed in silent vigil.*

*He does not move until the rain stops.*

**RICO**  
Mom... I did everything you asked.

The flower has water. The room is warm.

Why wasn't it enough?

*[Visual only: Fade to black. The camera turns toward the watered flower, and Rico is hidden from the final room composition. Fade back in with the daylight unchanged.]*

*Daylight enters through the window.*

*Across the room, the watered stonebell turns its pale blue bells toward the light.*

*[Visual only: Fade to black.]*

## Scene 5 — Anne's funeral

**EXT. BURIAL GROUND BEYOND NORTUNE'S OUTER WALL — DAYS LATER**

*[Visual only: Fade in on a live wide graveside composition. Young Rico, a hooded Ethos priest, Anne's fresh grave marker, and another weathered marker are visible.]*

*Days later, thin daylight lies across the burial ground beyond Nortune's outer wall.*

*Among its weathered markers, fresh earth and a plain wooden post bear Anne Banderas's name.*

*Only Rico and the Ethos priest stand at her grave.*

**ETHOS PRIEST**  
Anne Banderas never had much, but she shared whatever she could.

When a neighbor fell ill one winter, Anne brought her firewood and stayed until the fever broke.

Through her own long sickness, she endured with quiet courage.

She leaves behind her young son, Rico, and her husband, who is still fighting far from home in the war.

Her suffering is over now, and her soul has returned to God.

May she rest in His peace.

*[Visual only: The priest walks closer to Rico. The camera moves into a closer composition for his final blessing.]*

*The priest lowers his head and gives Rico a final, silent blessing.*

**RICO**  
Mercy...

*[Visual only: The camera holds on Rico, then eases back to the wide graveside tableau.]*

**END OF CHAPTER 1**

## Completion destination

### Choice

**Where will Rico go?**

- Continue to Next Chapter
- Return to Chapter Select

### Continue to Next Chapter

*[System action: The item and equipment inventory hidden during young Rico's chapter is restored, then the next chapter launches directly. No next-chapter title or exposition appears in Chapter 1's ending.]*

### Return to Chapter Select

*[System action: The item and equipment inventory hidden during young Rico's chapter is restored. Rico returns directly to the Path of Sephirot chapter-select hub without further dialogue.]*

An invalid or closed selection repeats the destination prompt without replaying the funeral.

## Chapter 1 menu and inventory presentation

This interface state is not screenplay dialogue, but it is part of the complete Chapter 1 presentation.

### Ordinary inventory retained during the chapter

- Hob-Jerky ×10
- Bizfruit ×12

In the standard standalone build, the other 16 checked baseline item stacks—36 items in total—are temporarily hidden during Chapter 1. The same chapter-only restriction hides seven spare weapons or armor pieces, one Economether, and three EtherStones. All of them are restored when Rico leaves the chapter.

### Young Rico's equipped keepsakes

These are the only three items young Rico has equipped. The Equip menu's
description panel shows the short hover text below for each keepsake.

| Equipped item | Hover description |
|---|---|
| Toy Gear | Rico's favorite toy |
| Old Blanket | Mended many times by Anne |
| Wooden Medal | A make-believe arena prize |

Young Rico has no Gear. The **Gear** menu row remains visible, but it is gray
and cannot be selected.

## Retired authored blocks — not player-facing

These three source blocks remain in the authored Chapter 1 data but have no reachable script route in the current build.

### Retired opening draft — authored block 1

> Long before D Block called him the Champ, Rico lived with his mother in the poor settlements beyond Nortune's outer wall.

The active chapter-select exposition replaces this draft card.

### Retired blood-reveal direction — authored block 11

> Anne turns away and raises the cloth to her mouth. When she lowers it, Rico sees blood.

The active bedside scene instead displays the routed narration in **Rico delivers the prepared cup**. It does not print a cough direction.

### Retired wide-shot direction — authored block 19

> The camera holds on Rico, then eases back to the wide graveside tableau.

The live funeral camera performs this direction visually. It is not printed before the end card.

## Active source map

- Authored chapter blocks and chapter-select exposition: [chapter_01_mothers_promise.json](../content/chapter_01_mothers_promise.json)
- Interactive routes, conditional text, timers, cough actions, and live cutscene staging: [build_rico_arc.py](../build.py)
- Chapter 1 inventory, keepsake names, descriptions, and disabled Gear presentation: [xgrico_balance.py](../tools/xgrico_balance.py)

Active authored coverage is block 0, blocks 2–10, blocks 12–18, and blocks 20–45. Blocks 30–45 are routed exactly once through the automatic firewood, sickroom, mourning, and funeral scenes; block 20 alone provides the final graveside close.
