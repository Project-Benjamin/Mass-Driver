# Mass Driver v106 Ouroboros laboratory finale

V106 extends the final route beyond Central Control and moves the capsule
launch to a room built for that purpose. Central Control retains Elly's
subjective Zeboim memory and Citan's carefully staged arrival, but it no longer
sets launch completion or invokes the world map. The party instead crosses a
red Zeboim pressure tunnel and reaches the exact retail field-507
Krelian/Ouroboros laboratory, where its surviving apparatus owns the final
manual launch commit.

V106 also makes the Defense Archive's two progression changes visible. A
correct code visibly and audibly opens the north lift. After the Guardian,
only the nearby west-bank record/control panel can open the west bulkhead, and
both openings retain their state when the room is loaded again.

## Extended final route

The end of the active route is now:

```text
target 383  reserve magazine 5
    <-> target 728  Central Control and Elly's memory
    <-> target 388  red final-service pressure tunnel
    <-> target 507  Krelian/Ouroboros laboratory and launch apparatus
    -> retail Mass Driver launch and guarded outside return
```

This raises the active dungeon from 34 to 36 target fields. Target 728 remains
between the fifth reserve magazine and the new final wing; it has not been
replaced by the laboratory.

## Target 388 red pressure tunnel

Target 388 clones retail source field 376's Zeboim personnel
pressure-transfer airlock. It therefore uses the same red industrial room art,
walkmesh, paired native door leaves, and machinery sound as an established
facility asset rather than introducing a visually unrelated connector.

- The south door returns to Central Control target 728, parameter 1.
- The north door enters the Ouroboros laboratory target 507, parameter 0.
- Both doors are deliberate Cross/X interactions. Contact alone does not
  change fields.
- Each action retains the donor's native helper animation and sound before the
  bounded party crossing and field transition.
- The laboratory's native east door supplies the reciprocal return to target
  388.

## Exact retail field-507 laboratory

Target 507 uses retail field 507 itself, the Krelian laboratory scene commonly
identified by its retail event in which Krelian examines Elly. This is the
actual Ouroboros research room: the donor dialogue explicitly references the
Ouroboros Ring, and the room contains the large surviving laboratory apparatus
used for the new finale.

The standalone adaptation preserves the retail room's graphics, model layout,
walkmesh, apparatus, and native east door. It removes the unrelated retail
story directors and neutralizes the two original CD1-only scene exits, then
rebuilds Elly, Emeralda, and the final-only Citan actor in the room. The new
route controller sits on connected floor inside the east doorway; it does not
place an interaction at the door model's wall pivot.

The final apparatus interaction presents both surviving context and the launch:

- Its prelude exposes the surviving archive index, which identifies Krelian as
  the primary user and names the Ouroboros Ring, Miang, and intron-pattern
  analysis. It does not invent a recovered visual record where none survived.
- The same local Cross/X action requires accepted launch authority and Citan's
  completed arrival, runs the apparatus's native mechanism animation, and only
  then invokes the authentic Mass Driver launch.

## Central Control handoff and final launch

Elly and Emeralda still enter target 728 alone. The first activation of its
central console remains one complete interaction: only Elly sees the
warm-filtered first-person memory, Emeralda sees her reacting to an empty room,
and every apparition, grade, and fixed-camera state is cleared before control
returns.

A fresh second activation opens the native east door and presents Citan's full
arrival under the retained smooth profile camera. He walks the verified
three-leg path around the console notch, reaches Elly without a visible snap,
and faces her before the camera eases into their conversation. This action no
longer launches the capsule. It adds Citan only for the final handoff and sends
the party into target 388.

After crossing the tunnel, the player must walk to the field-507 apparatus and
press Cross/X. The laboratory interaction exposes the surviving Ouroboros
index, has Citan stabilize the guidance solution, and leaves the final manual
commit to Elly. The apparatus animation precedes the retail Mass Driver
world-map sequence at position `0x0FFF`, mode `17`. The guarded field-617 return
removes temporary Citan and restores Elly and Emeralda outside. Citan remains
absent from every dungeon battle.

## Visible north-lift authorization

The Defense Archive authorization console still requires Directive `0320`
followed by `A-2`, `B-5`, `C-8`, and `D-4` as five separate accepted choices.
The success path now makes the result visible instead of ending on text alone:

1. The camera moves to a clear view of the north-wall lift.
2. Native machinery sound `0x77` plays.
3. Helper entities 18 and 19 run their finite 24-frame opposed slides, opening
   both native-textured leaves together.
4. The normal camera and player control return without combat or a field
   transition.

The authorization bit also initializes both leaves at their open endpoints on
later target-376 loads. Pressing Cross/X at the open lift then performs only
the bounded personnel crossing into target 384; code acceptance itself never
starts the Guardian battle.

## West bulkhead control ownership

The west bulkhead no longer opens when the player presses Cross/X on the door.
Its sole opening control is nearby entity 23 at `(-406, -94)`, the west-bank
record/control panel beside the aperture. The panel continues to present its
strategic-outcome archive before evaluating the mechanism.

Before the Guardian is defeated, the panel and doorway report the existing
custodian lock. After victory, the next panel activation:

1. holds input and switches to a fixed view of the west bulkhead;
2. plays native machinery sound `0x77`;
3. runs helper entities 15 and 16 together, sliding the weathered leaves away
   from the center of their original wall aperture;
4. records a dedicated persistent-open bit; and
5. releases the fixed camera and restores control without changing fields.

Entity 14 at the doorway reads that persistent state. While closed it cannot
open the leaves; once entity 23 has released them, it only performs the bounded
party crossing and transition to target 377. Reloading target 376 initializes
both helpers at their open endpoints, so the door cannot visibly close again or
require the panel sequence a second time.

## Runtime acceptance

Use a fully quit DuckStation session, cold-boot the v106 CUE, choose New Game,
and load no older F1 state or in-game save. A state with target 376 resident
retains the old door scripts, and a state with target 728 resident retains the
old direct-launch finale even after newer media is selected.

Confirm the following in order:

1. Enter the complete code in target 376. The camera must show the north lift,
   sound and both leaf animations must play, and control must return upstairs.
   Leave and re-enter the room and confirm the lift remains visibly open.
2. Defeat the Guardian and return on foot. Pressing X at the west doorway must
   not open it. Use entity 23 instead; confirm its archive text, fixed-camera
   reveal, sound, paired opening, and restored player control. Reload the room
   and confirm the west leaves remain open, then traverse entity 14 normally.
3. Cross all five reserve magazines and enter Central Control. Confirm the
   first console action ends after Elly explains the memory, and the second
   action presents Citan's smooth entrance without launching the capsule.
4. Confirm the second action leads through target 388. Traverse both native
   doors in both directions and verify the reciprocal Central Control and
   laboratory arrivals.
5. In target 507, confirm the room is retail Krelian/Ouroboros laboratory art,
   not a Yggdrasil room or generic Zeboim ruin. Activate the final apparatus.
   That single interaction must expose the Ouroboros index, animate the native
   mechanism, and start the retail launch in that order.
6. Confirm the guarded return restores Elly and Emeralda outside and removes
   Citan from the playable party.

## Packaged v106 identities

- BIN: 696,547,152 bytes, 296,151 raw sectors, SHA-256
  `bfb7dbbe6c3cd1f9162b89cd990a9a2c2d898189f712a3d1f95c9edd52c192a9`.
- CUE: 107 bytes, SHA-256
  `e1efb24054e787c80db28c89abea3dda8fd500a231cf3699e7fe00f9c1f81204`.
- Manifest: 206,831 bytes, SHA-256
  `050181b0304b0e154d27d1544fc58a64b5a99fb9e7a768152160c30edf925dc6`.
- Declared replacements: 166 across 130 jobs, totaling 11,494,440 bytes;
  canonical-ID-order aggregate SHA-256
  `42221214703826686729b170acf9fb2f5010acec01b3026dcb986d2d930a4247`.
- Regression suite: 217 tests and 2,704 subtests passed with no failures,
  errors, or skips.

All 166 replacement payloads extracted from the packaged BIN match the stage
manifest byte-for-byte. Every v106 sector that differs from v105 validates as
MODE2/Form1 with correct EDC/ECC.

The superseded v105 artifact identities remain preserved in
[the v105 release notes](mass-driver-dungeon-2.82.md).
