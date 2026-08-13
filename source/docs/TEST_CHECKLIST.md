# V161 playtest checklist

Please report your emulator name and version and whether you used a cold-boot
New Game. Screenshots or a short video are especially useful for visual,
camera, collision, or stuck-control problems.

## Package and setup

- [ ] I extracted the complete ZIP before opening `Xenogears_Mass_Driver.exe`.
- [ ] The patcher accepted my clean USA Disc 2 BIN and reported success.
- [ ] The source Disc 2 BIN remained unchanged.
- [ ] I booted the generated `.cue`, not the `.bin`.
- [ ] I fully quit and restarted the emulator, then chose New Game.
- [ ] I did not load an older save state or an older in-game save.
- [ ] The game begins outside the Mass Driver with Elly and Emeralda; no Disc 1
      or prior story save is required.

## Whole-route smoke test

- [ ] I can enter the Mass Driver and ride the inclined lift through both
      segments.
- [ ] External and internal doors complete their animations without trapping
      the party or immediately bouncing them back.
- [ ] Elly and Emeralda remain the only party characters before the finale.
- [ ] The Guardian battle begins with the normal battle theme, animates, and
      returns control normally.
- [ ] Archive consoles, the Video Disk choice, the gold Save cube, and optional
      side rooms behave normally enough to continue the route.
- [ ] I can reach all five containment vaults and then Central Control.

## Guardian battle - V161 regression

- [ ] I started a fresh Guardian battle after mounting the V161 CUE.
- [ ] The room ambience stops and the normal battle theme starts before the
      first battle command.
- [ ] El-Regulus initially faces Guardian.
- [ ] After each Triangle, Square, X, deathblow, and recovery animation,
      El-Regulus returns home facing Guardian instead of showing its back.
- [ ] Crescens, Guardian, the battle camera, damage, and victory flow still
      behave normally.

## Defense Archive west-bank panel

- [ ] After defeating Guardian, I can use the southwest console bank across
      its visible walkable frontage without precise aiming or timing.
- [ ] Pressing X opens strategic-outcome dialogue 19.
- [ ] Closing the dialogue shows the west bulkhead, plays the machinery sound,
      and opens both leaves.
- [ ] The panel does not activate at the bulkhead or neighboring consoles.
- [ ] Re-entering the room keeps the bulkhead open.

## Defense Archive north lift

- [ ] After entering the correct authorization code, both north-lift doors open.
- [ ] Walking north through the open doorway enters the Defense Bay without X.
- [ ] Pressing X from the final reachable stance also enters the Defense Bay.
- [ ] Returning from the Defense Bay does not immediately send the party back.

## Central Control - highest priority

- [ ] The distinct standing console appears near the east/north side of the room.
- [ ] The console has solid collision on all four sides.
- [ ] Before Citan arrives, pressing X at that console produces only Elly's
      one-page observation.
- [ ] Repeating the interaction remains harmless and repeatable.
- [ ] The broad story console starts the ending from both intended positions.
- [ ] After Elly returns from Miang's memory, no second X press is required.
- [ ] Citan enters through the east door without clipping into actors or scenery.
- [ ] Citan faces Elly for their dialogue.
- [ ] The camera frames Citan and the standing console clearly.
- [ ] Citan turns toward the console and operates it with animation and sound.
- [ ] The capsule launches only after Citan finishes using the console.
- [ ] The sequence returns to the world map without frozen input, a black
      screen, camera corruption, or a stranded actor.

## Also report

- Text overflow, incorrect speakers, missing portraits, typos, or awkward line
  breaks.
- Missing or incorrect textures, flicker, sprite corruption, or camera clipping.
- Doors, consoles, or collision hotspots that activate from the wrong side.
- Crashes, hangs, battle anomalies, audio issues, or reproducible input locks.
