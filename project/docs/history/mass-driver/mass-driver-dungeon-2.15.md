# Mass Driver Dungeon 2.15 - v36 Doors, Rail Interlock, and Returns

Version 36 repairs the three runtime defects reported after the v35 archive
annex expansion:

- the accelerator-rail control was too easy to miss and the Central Gate gave
  no useful route guidance;
- synthesized panels pitched outward like hinged doors and could leave a
  black opening instead of the intended Zeboim door presentation;
- every new annex return placed the party inside its own door controller,
  preventing movement after the room reloaded.

## Accelerator-rail control

Target 725 entity 16 keeps its original Zeboim terminal actor and sprite bank.
Its story-variable initializer is replaced with a deterministic retail NPC
initializer at `(100,-100)`, walkmesh layer 0, in the north control alcove.
That point lies strictly inside connected triangle 55 and does not overlap the
room's existing controller. Pressing X sets persistent rail-interlock bit 1
before dialogue and plays sound `0x50`.

Target 726's rail warning now directs the player to:

```text
Magnetic Conduit - north control alcove
```

## Native sliding doors

The v35 `BF`/`C0` pitch sequence was a literal 90-degree hinge. Version 36
removes it.

The two saved-state thumbnails isolate the visual defect: the `.bak` at
helper yaw 672 shows the reported black opening while the later `.sav` at
yaw 0 shows the blue/gray closed panel restored. Model 7's geometry, UVs,
texture page, CLUT, and winding match the baked panel exactly. The art was
not missing; the hinge had turned it edge-on. The retail slide fixes that
state without replacing the texture.

Target 363 preserves the donor's own static model 2 as the south double door,
turns that actor into helper entity 18, and calls its retail `FE 1B` sliding
routine at PC `0x0224`.

Target 726 exposes the donor's three correctly wound door models:

- model 6 with retail slide PC `0x017C`;
- model 7 with retail slide PC `0x019D`;
- model 8, recentered from the donor's model 2, with retail slide PC `0x01BE`.

The two perpendicular panels use an audited `-0x0400` header yaw. Every added
door retains native sound `0x77`, X-only activation, finite asynchronous model
animation, bounded party movement, and its reciprocal annex.

## Safe reciprocal returns

The eight corrected return records are:

```text
365 -> 363/p2: (   0,-100), direction 0
366 -> 726/p3: (  20,-176), direction 6
367 -> 726/p4: (-520, 485), direction 2
368 -> 726/p5: (-529,-560), direction 0
369 -> 726/p6: (-345,-545), direction 6
370 -> 726/p7: (-529, 510), direction 0
371 -> 726/p8: (  88,-560), direction 0
724 -> 726/p9: (  20, 441), direction 6
```

Each point is on the connected receiving walkmesh and more than 76 world
units from its 60-unit door controller plus the 16-unit player radius. The
camera and actor direction match, with the used door behind the party.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v36.bin

BIN size: 692,852,160 bytes
raw sectors: 294,580
BIN SHA-256:
b5689a330d38950315f8d539e349b406185dbf51e12c2a5316d95fbc3b35ffd4

packed staged replacement comparison:
138/138 exact, totaling 7,792,250 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 142 passed, 1,645 subtests passed
```

Runtime acceptance is not claimed until the manual checks below pass.

## Manual acceptance

Cold-boot v36. Do not load the v35 F2 state: DuckStation states retain the
old mounted image and already-loaded field script.

1. Close DuckStation and run `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Restore auxiliary power through the existing research-annex route.
3. In target 726, use the western door near `(-617,-572)` to enter the
   Magnetic Conduit.
4. Walk to the north control alcove and press X at the visible Zeboim
   terminal near `(100,-100)`. Confirm the bypass message and sound.
5. Return to target 726 and confirm the Central Gate no longer reports the
   accelerator rail as offline.
6. At the formerly black panel leading to annex 370, confirm the closed door
   art is visible. Press X once and confirm sound `0x77` and a vertical slide,
   with no hinged rotation or black-panel glitch.
7. Exit annex 370. Confirm the party appears clear of the door, faces into the
   room with the door behind it, and can move immediately.
8. Repeat the enter/return check for the other seven archive panels. Every
   visible panel must open, reach its own room, and restore control on return.
