# Mass Driver v98 native El-Regulus command-menu idle

V98 preserves v97's native battle-entry facing repair and fixes the remaining
static opening pose. El-Regulus now reaches the first command menu facing its
formation slot-center target and already running its own subtle native idle.
The first attack is no longer required to make the Gear begin moving.

The complete dungeon, Elly/Emeralda party, Guardian encounter, Central Control
finale, Attack-Level progression, attacks, deathblows, and battle overlay remain
unchanged from v97. The only intended replacement delta is canonical 2960's
animation 0.

## Root cause

The battle initializer requests animation ID 0 directly. The opening command
menu therefore inherits whatever loop, if any, animation 0 leaves armed.

Retail canonical 2960 stored animation 0 at `0x71BC..0x71DC`:

```text
0A 00 0C 00 10 00 48 00 4A FD 61 00 0A 00 5A 08
32 00 06 00 60 00 43 00 10 FF 11 FF 00 01 00 00
```

V97 restored the important native `60 00 43 00` sequence: opcode `60` obtains
the formation's slot-center target and opcode `43` turns the model toward it.
That fixed the backwards opening direction caused by v96's unconditional
relative-turn packet.

V97 nevertheless retained v24's completion repair at the end of the program:

```text
10 FF 21 00 6D 00 00 00
```

`10 FF` selected the model's default keyframe. `21 00` yielded and `6D 00`
cleared the delayed loader-completion flag, but the following terminator ended
the program. El-Regulus was correctly oriented yet frozen in a one-time pose.
Its first attack looked normal because the separate post-attack recovery path
armed the native repeating idle.

## Exact animation-0 fix

At v97 canonical-2960 offset `0x71D4`, v98 replaces the eight-byte completion
tail with this twelve-byte tail:

```text
10 FF 21 00 6D 00 11 FF 00 01 00 00
```

The `21 00 6D 00` delayed completion handshake remains in its proven order.
The added retail `11 FF 00 01` loop packet then repeats default keyframe 1,
instead of allowing animation 0 to terminate on a static pose.

The complete v98 animation 0 is 36 bytes at `0x71BC..0x71E0`:

```text
0A 00 0C 00 10 00 48 00 4A FD 61 00 0A 00 5A 08
32 00 06 00 60 00 43 00 10 FF 21 00 6D 00 11 FF
00 01 00 00
```

Its SHA-256 is
`f6cd4d7520356d3a25b4396a04d5a87d18811b2bb516912fa1320c394fe46939`.

The deterministic canonical-2960 result is:

| Build | Size | Outer roots | SHA-256 |
| --- | ---: | --- | --- |
| v97 | 33,600 | `(2, 0x10, 0x7FF4, 0x8340)` | `627b332e5b2c15ca7e99d7d44e76fa8f72291634dbbfc32aae1ab19ef511c8c6` |
| v98 | 33,604 | `(2, 0x10, 0x7FF8, 0x8344)` | `589a0d3c8c9481a0f1c336513ce727e5e88701dad311bda12239c7f93a0f3252` |

The four-byte insertion moves every later program pointer by four bytes.
Animation 1 moves intact from `0x71DC..0x71F0` to `0x71E0..0x71F4`, and attack
program 32 moves to `0x76D4`. No later program body changes.

## Native idle provenance

This is not a borrowed attack, defeat pose, or handmade motion. It is
El-Regulus's own default idle:

- Canonical 2959 model metadata at `0xBB76` declares default keyframe
  `mA = 0x01`.
- Canonical 2960 keyframe 1 occupies `0x0498..0x0F48`, is 2,736 bytes, has a
  30-tick duration, and contains 58 rotation tracks plus 30 translation tracks.
- El-Regulus animation 1 already invokes the same loop with exact bytes
  `0A 00 0C 00 13 00 FF 00 00 06 21 00 11 FF 00 01 03 00 00 00`.
- Nine of the eleven audited playable-Gear animation-1 wrappers use the common
  `10 FF 11 FF 00 01` default-keyframe loop. The other audited Gear models also
  declare keyframe 1 as their default.
- El-Regulus post-attack recovery tails independently end in either
  `13 00 FF 00 00 04 21 00 11 FF 00 01` or
  `13 00 FF 00 00 02 21 00 11 FF 00 01`, proving that the model normally
  returns to this loop after acting.

Seibzehn's model-specific 80-byte bobbing wrapper was rejected because it is
not portable to El-Regulus. Offensive clips `0x40..0x42`, ducking clip `0x43`,
beam clip `0x44`, and collapse/defeat clip `0x45` were likewise rejected for
the opening idle. The fix uses no combat motion at all.

## Isolation

Relative to v97, only declared canonical 2960 is expected to differ. Its
844-byte primary model/sound container remains SHA-256
`8090fef41466cf3558edc9c512105572b8dab19f74770010d1e531eca886e5ed`.
Every standard attack, Level-1 program, Level-2/3 program, Infinity deathblow,
and nonzero animation other than its relocated pointer remains byte-identical
to v97.

Canonical battle overlay 38 remains exact retail: the packed 166,665-byte
resource has SHA-256
`93a4179fe3b31a4fffb9fe723f63511f15de5177bbfcbca2529124a4108ffbb1`,
and its 343,948-byte decoded payload has SHA-256
`ad4586923095715288377caea89f2cd15d70a2f80ef53394e2faec22b2e0b825`.
Shared target-yaw behavior, Crescens, enemies, and all field content therefore
remain outside this correction.

## Packaged v98 identities

The completed v98 package is:

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v98.bin`: 695,834,496
  bytes, 295,848 raw sectors, SHA-256
  `68ea0467edd054bbbe90cde57fe921ae5b7bd2bfa6ff88d82de04735bf8852ed`.
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v98.cue`: 106 bytes,
  SHA-256
  `9797eb2009f06d69c2d6facec7908185174aa8e208c766ebfa990fefc40e1d67`.
- Manifest `work/mass_driver_v98_stage/manifest.json`: 197,378 bytes, SHA-256
  `51630346126a178e4ee36a2a6ee4dcf6e887a81d41b052427fe4aab55252f119`.
- The manifest has 128 jobs and 162 declared replacements totaling 10,870,888
  replacement bytes. Its canonical-ID-order aggregate SHA-256 is
  `bbc99d82d5198ea5f5c278c2d9ae24ec617352cf02fc7945783b40840f81a5e5`.

The preserved packaged v97 identities and its v96-facing delta remain in
[the v97 release notes](../../mass-driver-dungeon-2.74.md).

## Cold-boot runtime acceptance

Perform this test only after the v98 package exists:

1. Fully quit DuckStation. Do not merely change discs inside a running session.
2. Launch `output/PLAY_MASS_DRIVER_STANDALONE.cmd`, verify that it selects the
   v98 CUE, and choose New Game.
3. Do not load an older F1 state or in-game save. An F1 state restores its old
   mounted media, resident battle code, and resident canonical 2960. In
   particular, a v97 battle restores the static animation-0 tail and cannot
   validate v98; the captured v96 Dragon state additionally restores the
   invalid relative turn.
4. Mount El-Regulus outside the facility and enter a completely new nearby
   Dragon battle from v98 media.
5. At the first command menu, before selecting any attack, confirm that
   El-Regulus faces its slot-center target and visibly performs the subtle
   native keyframe-1 idle. Observe more than one 30-tick cycle.
6. Cancel and reopen commands. The idle must remain alive and the opening
   direction must not change.
7. Perform one ordinary attack. After recovery, confirm that the same idle
   continues; the attack must not be what starts movement or repairs facing.
8. Confirm enemy turns, damage, Attack-Level progression, deathblows, victory,
   and mounted world-map return remain normal.
9. Repeat the opening-menu check in the factory Guardian encounter and confirm
   Crescens, the Guardian, post-battle mounting, and dungeon backtracking are
   unchanged.

The v98 acceptance condition is both correct orientation and active native idle
at the initial command menu. A still pose that only becomes animated after the
first attack does not pass.
