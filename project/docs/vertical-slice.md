# Mass Driver standalone vertical slice

## Goal

Provide a complete, self-contained Xenogears exploration dungeon that begins
outside the native world-map Mass Driver, requires no retail story progress,
and can later be integrated into the story without redesigning its field
graph.

## Implemented v11 slice

- Cold boot uses target 728 as a hidden black gateway, then opens playable
  world-map position 21 outside the existing Mass Driver complex.
- The world-map landmark itself is interactive. X (Cross; keyboard `K`) enters
  target 729. Taura/Torah's House is not repurposed.
- Target 729 and target 364 preserve the released two-field inclined lift.
  Target 729/source 361 runs the original 30-step upper-half descent, then
  target 364/source 362 continues it for 15 native movement steps and performs
  the lower-landing SFX and velocity cleanup before control returns. Target
  364's far threshold enters target 360. The reverse route is target 360 to
  target 364 parameter 1, then the native ascent to target 729 parameter 1;
  target 729's introduction is suppressed on that return. Source 386's
  vertical/deep elevator is not used.
- Targets 360 and 720 are exactly two underground approach tunnels.
- Target 721 is the stationary employee subway/platform. Its existing chest
  is a repeatable train-safety notice and gives no item. Walking through the
  far passage enters target 362 parameter 0 automatically; there is no exit
  prompt and no X press.
- Target 362/source 376 is a Zeboim personnel pressure-transfer airlock, not a
  second lift room. Its clean animated north door returns to target 721
  parameter 1. Its preserved south pressure cycle and mechanical door enter
  target 727 parameter 2. Target 727's entity-14 door animates on the reverse
  route and enters target 362 parameter 1.
- Target 727 is a three-door operations junction with fixed destinations.
  Progression never dynamically changes where a junction door leads.
- Target 724 is a four-way service concourse. Its open side passages reach
  target 361/source 373's research annex and target 722/source 374's storage
  annex. Its mechanical routes reach target 727 and the target 723/source 375
  connector.
- The connector reaches target 726's third branch. A second path runs from 727
  through targets 363 and 725 to 726, making a coherent backtracking loop.
- The auxiliary interlock is restored at a record in target 361. The
  accelerator-rail interlock is restored by the optional Ravine/grid record in
  target 725.
- Target 726 owns the final locked door. Once both interlocks are set, its
  sound and field-model animation play before target 728 loads.
- Target 728 recognizes normal route predecessor `726`, presents Central
  Control/archive and the finale, then returns the party outside.

## Target graph

```text
world map -> 729 -> 364 -> 360 -> 720 -> 721 -> 362 -> 727

727 <-> 724 <-> 361
        |      auxiliary interlock
        +<-> 722
        +<-> 723 <-> 726 -> 728 -> world map

727 <-> 363 <-> 725 <-> 726
                    rail interlock
```

## Donor mapping

```text
729<-361, 364<-362, 360<-398, 720<-399, 721<-397, 362<-376,
727<-377, 724<-382, 361<-373, 722<-374, 723<-375,
363<-363, 725<-385, 726<-384, 728<-369
```

Lighthouse resources are limited to the two approach tunnels and stationary
employee platform. Every actual facility room uses the Disc 1 Ethos Dig
Site/Zeboim ruins asset family. No train ride, Solaris room, Krelian material,
or Anima Relic technology is present.

## Interaction standard

Visible mechanical doors retain or recreate the donor sequence of door sound,
field-model helper animation, and only then a field transition. Open passages
and tunnel/subway thresholds remain automatic collision boundaries. The v11
route has no legacy prompt-based exit, no explicit subway-exit confirmation,
no parked usable door, and no dynamic hub-routing action.

Automatic dialogue is limited to targets 729, 720, and 728, with target 729's
introduction skipped on a return ascent from target 364. Other exposition is
found on physical records, terminals, containers, and the platform chest.
Elly's observations and Emeralda's responses support the discoveries without
stopping the party after every screen.

## Completion boundary

This vertical slice is complete when a fresh human playthrough can:

1. enter the native Mass Driver with X;
2. see target 729 run the native 30-step upper descent and target 364 continue
   it for 15 steps to the actual lower landing;
3. confirm that the landing stops the motor and clears platform velocity
   before control returns, then cross target 364's far threshold into 360;
4. backtrack once through target 360 to target 364 parameter 1 and take the
   native ascent to target 729 parameter 1 without replaying the introduction;
5. cross exactly two tunnels and leave the subway automatically;
6. enter the personnel airlock at its north arrival, verify its north door
   animates back to the subway, then pass through its south pressure cycle and
   animated door into target 727;
7. visit both annexes and traverse both paths into target 726;
8. restore interlocks in targets 361 and 725;
9. open the gated target-726 door into Central Control;
10. complete target 728 and return outside.

If scripted emulator movement cannot reliably reach or operate a particular
door, a human playtest should perform that step and report the exact entrance,
door, and result instead of inferring it from guessed input.

This remains a canon-conscious fan reconstruction, not recovered Square
cut-content data. Retail-story placement, random battles, and a boss battle
remain intentionally outside this standalone slice.
