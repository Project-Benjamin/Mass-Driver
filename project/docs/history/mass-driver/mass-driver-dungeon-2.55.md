# Mass Driver v78: El-Regulus facing and factory staging

V78 fixes El-Regulus's battle-facing and field-scale presentation, and replaces
the two-room lower Defense Bay route with one coherent Goliath Factory staging
hall. It retains v77's working Attack-Level progression and completed
deathblows. Runtime acceptance is still pending a fully cold-booted v78 New
Game; the hashes below are structural and packaged-build evidence, not a claim
of emulator acceptance.

## El-Regulus presentation

Canonical battle overlay 38 previously applied the player-slot yaw path in the
wrong direction, so El-Regulus could present its back to the enemy. V78 changes
exactly 20 decoded bytes at `0x3D240` to give fixed player slot 0 the required
half-turn. The correction is deliberately slot-specific: Crescens, Guardian,
enemy actors, and canonical battle-animation resource 2960 are unchanged.

| Canonical 38 evidence | Size | SHA-256 |
|---|---:|---|
| Retail packed source | 166,665 | `93a4179fe3b31a4fffb9fe723f63511f15de5177bbfcbca2529124a4108ffbb1` |
| Retail decoded source | 343,948 | `ad4586923095715288377caea89f2cd15d70a2f80ef53394e2faec22b2e0b825` |
| V78 decoded result | 343,948 | `9409b10bdff27fb46f54df47f4b3ecab876d9aac95492c117e4d556b34007db3` |
| V78 packed replacement | 164,608 | `32bc80f7ebec84f2c7f24b88a3d9a4fa09ac98dc7fb2fbcf9a7aac95b0b1ebc8` |

Canonical 453 previously made field-scale Gear 10 use Vierge's global sprite.
V78 rebuilds it from the authentic five-direction El-Regulus art in field 657,
so the parked and mounted Gear in target 384 is visibly El-Regulus. The retail
16-animation, 65-frame field program remains intact; only its frame images are
redirected.

| Canonical 453 evidence | Size | SHA-256 |
|---|---:|---|
| Retail packed source | 38,516 | `204dd1e2d613d51107806498fd7e4283ecf2601e2a18597752ad2a987f31c1fc` |
| Retail decoded source | 45,510 | `dc9f6c407a0d33a6f249ec3cbf7c4023273be8a08c606f5fdbef850dccabbfd5` |
| V78 decoded result | 45,510 | `a7cfadae92bc7bbe1e6e63702a7c696af079b87ca24149fccd0e8f3d28182905` |
| V78 packed replacement | 8,848 | `41c2216b8169410295efbedd656297ddaf6d54dbbdbc96ded692c77df79d54c3` |
| Preserved retail animation | 336 | `beb29b73e796f48f7001e0470168708f0fc90f7cab8a17075a4261086a4431ea` |

## Revised lower route

The active lower route is now only `376 <-> 384`; target 386 and its source-263
Defense Bay are retired from the route.

After the code is accepted in target 376, its human-scale north lift explicitly
dismounts both party slots, clears the two staging bits, and enters target 384
parameter 0. Elly and Emeralda arrive on foot in source 260's large Gear-scale
hall. El-Regulus and Crescens are parked independently near the entrance.
Pressing X at either Gear assigns it to its pilot, mounts only that party slot,
sets its own persistent staging bit, and reloads target 384 parameter 0 through
the donor's native mode-3 party initializer. Either boarding order is valid.

The field director requires launch authorization, both staging bits, and the
mounted leader reaching the room midpoint (`z >= 0`) before the Guardian scene
can begin. Fixed formation 15 remains the isolated 36,000-HP Guardian with
Escape disabled. The battle party is exactly Elly/El-Regulus and
Emeralda/Crescens; Citan is explicitly excluded and Fenrir is never mounted.

Victory returns to the same hall with both pilots still mounted. The far north
door retains its native factory leaves but only reports that its drive is
offline; it does not animate or change fields. The player backtracks to the
south personnel entrance, whose action dismounts both slots, clears both
staging bits, opens the native door, and returns to target 376 parameter 2 on
foot. The west archive bulkhead can then continue the dungeon normally.

Target 384's rebuilt canonical-1374 bundle is 162,552 bytes with SHA-256
`6db4ed197cc5a76e123efbb18e893212a2dc27770769b47f2714aa7dff15cf8e`.
Its script is 21,284 bytes with SHA-256
`b5366ce3e4442cdd55364a27d07a3cdf7ae28dc9f4ad71c6b15372224661cf3f`;
its dialogue is 1,143 bytes with SHA-256
`edbc866c9f7708224a70e25cf65d196ae18c35a8c6156dd9ce0017a996f66db5`.

## Retained v77 Attack-Level repair

V78 preserves canonical 2595 byte-for-byte from v77: 9,048 bytes, SHA-256
`6c81d365be39a4fa66fe7f8e0d19cae4a48201e7107513402c861636654c0b04`.
Elly still uses battle-command loadout `m56 = 1`; the selected Gear word at
`0x16E4` remains `0x1FF8`, the adjacent on-foot word at `0x16E0` remains
`0xFC00`, and Gear 10 retains the real `Atk Lv1/2/3 Max` accessories
`60/61/62`. Thus ordinary attacks are intended to advance
`0 -> 1 -> 2 -> 3`, followed by the native Hyper/Infinity opportunity.

Canonical 2960 is also byte-identical to v77 at 33,600 bytes with SHA-256
`627b332e5b2c15ca7e99d7d44e76fa8f72291634dbbfc32aae1ab19ef511c8c6`.
Beat Storm retains offensive clips `0x40 -> 0x41`; the completed Level-2,
Level-3, and Infinity programs retain their checked damage, fuel, recovery,
and mixed melee/ether presentation. The observed collapse clip `0x45` remains
absent from every physical prelude.

## Build evidence

The v78 manifest contains 126 jobs and 158 declared replacements totaling
10,755,835 bytes. Their canonical-ID-order aggregate SHA-256 is
`f2b64d9c47e6b31b8a278049d2bddfcfbf6aa0f8c3bb9c7a8c5579f2b82ce1c1`.
The builder completed successfully, and the final image's boot-sector
MODE2/Form1 EDC/ECC check passed.

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v78.bin
size: 695,702,784 bytes (295,792 raw sectors)
SHA-256: 32080e0d5745f36af5b9b56a68be1c95dfae1947797aa29e285c18651df86286

output/Xenogears_PW_CD2_mass_driver_standalone_v78.cue
size: 106 bytes
SHA-256: c4ca61dcd7fe5aec3de7da0a75d6da2dee919c41e54fd8df9811ecdc89c39434

work/mass_driver_v78_stage/manifest.json
size: 182,800 bytes
SHA-256: d07e90b205b4a0b2d762efad3a26d9fc72428d497696f1575b6a48abaa9a59c9
```

## Pending runtime acceptance

Fully quit DuckStation, boot the exact v78 CUE above, choose New Game, and do
not load any older F1 state or in-game save. Runtime acceptance still needs to
confirm:

1. Target 384 starts with Elly and Emeralda on foot and shows authentic parked
   El-Regulus and Crescens sprites.
2. Either Gear can be boarded first; the mixed mounted/on-foot reload is stable,
   and the midpoint does nothing until both are mounted.
3. El-Regulus faces Guardian correctly while Crescens, Guardian, and other
   battle actors retain their normal facing.
4. Citan and Fenrir are absent from the hall, scene, battle, and post-battle
   party; Citan still first appears only for the final capsule launch.
5. Victory leaves both pilots mounted, the north door reports offline without
   opening, and the south entrance dismounts both before returning to target
   376 on foot.
6. Ordinary attacks still reach Levels 2 and 3, the native Hyper roll can reach
   Infinity, and every retained deathblow resets and completes normally.

Until those cold-boot checks are completed, v78 remains structurally built and
hash-verified but not runtime accepted.
