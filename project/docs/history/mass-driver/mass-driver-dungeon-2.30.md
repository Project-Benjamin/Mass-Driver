# Mass Driver Dungeon 2.30 — v51 Defense Checkpoint and Missile Galleries

Version 51 moves the post-gate scene out of target 726's launch-support
hallway and builds a complete route from the powered Central Gate to Central
Control:

```text
726 <-> 376 <-> 377 <-> 378 <-> 379 <-> 728
        checkpoint    three missile galleries    Central Control
```

This is an original, canon-conscious fan reconstruction. It is not recovered
Square script or official cut-content data.

## Central Gate

Target 726 entity 14 remains a native animated Zeboim door. It checks exactly
two persistent conditions:

- auxiliary power;
- accelerator-rail power.

Launch authorization and the four-digit record do not operate this door.
When both power conditions are active, its bounded native transition enters
target 376 parameter 1. The reverse target-376 door returns to target 726
parameter 1.

## Defense checkpoint

Target 376 clones source field 385's complete two-door Zeboim industrial hall.
On first entry it:

- locks player control before any asynchronous party loading;
- adds Citan to the party;
- stages Elly, Emeralda, and Citan as visible field actors;
- shows the checkpoint conversation;
- returns control with the entrance behind the party.

The existing memory-cube actor is placed on connected walkmesh and repurposed
as the authorization console. It requires the already recovered Directive
0320 and `A-2 / B-5 / C-8 / D-4` records. Wrong choices are retryable.

The correct answers are accepted, but the ancient system reports that command
authority has expired. Its emergency custodian now classifies all living
personnel as intruders, so the defense protocol attacks despite valid codes.

## Three-Gear Guardian battle

The fixed no-Escape encounter uses formation 15 and the enclosed Goliath
Factory interior arena `0x0B`. Before battle the script explicitly enables
all three battle frames, assigns the intended Gears, and mounts all party
slots:

- Elly — El-Regulus, Gear ID 10;
- Emeralda — Crescens, Gear ID 9;
- Citan — Fenrir, Gear ID 11.

The opponent is one mechanical `Guardian` with 36,000 current and maximum
Gear HP. It is an isolated clone of the retail mechanical Pedestal:

- enemy resource set `0x10`;
- stats/AI canonical 2650;
- model/animation canonical 2651;
- retail Pedestal resources remain unchanged.

After victory, all three slots are unmounted, ownership is restored, the
complete on-foot party returns, and boss bit 5 unlocks target 376's forward
door.

## Missile galleries

Targets 377, 378, and 379 reuse the same authentic Zeboim industrial donor and
unchanged walkmesh as the checkpoint. Each field adds eight non-colliding
horizontal missiles in four overhead racks, for 24 visible missiles total.
Every entrance and exit is an X-operated native sliding door with finite
party movement and a reciprocal destination.

The final gallery connects to target 728 Central Control. Target 728's visible
return door now leads back to target 379 parameter 0. Its cold-boot gateway
also recognizes field 379 as the only normal predecessor, preventing a normal
gallery arrival from being mistaken for standalone boot.

## Release artifacts

```text
work/mass_driver_v51_stage
output/Xenogears_PW_CD2_mass_driver_standalone_v51.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v51.cue
```

Final BIN:

- size: 694,731,408 bytes;
- raw sectors: 295,379;
- SHA-256:
  `089f38f53e574060fcccedc0604192d17cd04cc2e8fdb91aa33aa3f2ee2471f3`.

Final CUE SHA-256:
`9bd0ca52a95365b28482c4a07a692039ea8f68e5dd7136d89e47fdd1c177498f`.

The 149 staged replacements total 9,624,983 bytes and compare exactly against
all 149 packed disc entries. The standalone boot sector retains valid
MODE2/Form1 EDC/ECC and SHA-256
`79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc`.

## Focused runtime acceptance

Cold boot the v51 CUE and choose New Game. Do not use an F1 state made with an
older build, because it restores the older mounted image and loaded field
code. A new F2 state may be made after v51 has cold-booted.

1. Restore auxiliary and rail power, then approach target 726's Central Gate.
2. Confirm the gate opens without requesting launch authorization and enters a
   separate room.
3. Confirm the party faces into target 376 and Citan is visibly present beside
   Elly and Emeralda.
4. At the console, enter `0320`, then `A-2 / B-5 / C-8 / D-4`.
5. Confirm the script says the code was accepted before the custodian warning.
6. Confirm battle contains El-Regulus, Crescens, and Fenrir against one
   mechanical Guardian in an enclosed industrial Gear arena.
7. Confirm normal enemy damage is possible, Escape is unavailable, and
   victory returns safely to target 376 with all three characters visible.
8. Open the forward door and traverse targets 377, 378, and 379. Each should
   show eight missiles and allow immediate backtracking through the door used.
9. Enter target 728 and verify its return door leads to the final missile
   gallery rather than target 726.
10. Use the launch console and confirm the normal standalone completion flow.

