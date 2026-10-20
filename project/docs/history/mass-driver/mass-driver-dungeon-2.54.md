# Mass Driver v77: El-Regulus Attack-Level root repair

V77 repairs the actual state word that capped El-Regulus at Attack Level 1.
The earlier accessory correction was necessary but not sufficient: v76 is
genuinely broken for this progression test because Elly's active battle-command
loadout still selected a Gear ability word whose encoded maximum was Level 1.

All v76 combat presentation is retained. Beat Storm still uses confirmed
offensive clips `0x40` then `0x41`; every Level-2, Level-3, and Infinity
physical prelude still uses only clips `0x40` through `0x42`; the
collapse/defeat clip `0x45` remains absent; and the valid `0x44` charge/firing pose remains in
native beam finishers. Accessories `0x60/0x61/0x62` and all three mixed
melee-and-ether Infinity programs are unchanged.

The inherited facility route is also unchanged. Both Defense Archive doors
still reconstruct the exact native field-394 wall aperture and retain a
bounded party crossing. Target 384 is retail source 260, the Goliath Factory
access hall; target 386 is the distinct defense bay from retail source 263;
and target 367 remains the blue materials laboratory from retail source 380.
The authorization terminal, reciprocal lower route, post-Guardian backtrack,
west bulkhead, reserve magazines, and final-only Citan launch sequence are all
preserved.

## Root cause

Retail battle code keeps the combatant's current Gear Attack Level at entity
offset `+0x148` and its derived maximum at `+0x149`. The ordinary-attack path
increments the current value and then clamps it to that maximum.

Elly's initial battle-command loadout field is `m56 = 1`. For that loadout the
engine derives the maximum from the third ability halfword in her 0x20-byte
record, at initial GameState offset `0x16E4`. The neighboring halfword at
`0x16E0` is the on-foot ability word; setting it to `0xFC00` does not unlock
Gear levels for `m56 = 1`.

V76 had this state:

```text
0x16E0 = 0xFC00  on-foot ability word
0x16E4 = 0x1808  loadout-selected Gear word; runtime maximum Level 1
```

The v74-v76 images did retain the real `Atk Lv1 Max`, `Atk Lv2 Max`, and
`Atk Lv3 Max` accessories at Gear 10 offsets `0x0FE9..0x0FEB`:

```text
60 61 62
```

Canonical 2594 identifies their selectors as `06/07/08`, while the retired
`5A/5B/5C` items are Frame HP10/30/50 with selector `05`. Correcting those
items removed one error, but it could not override the Level-1 maximum derived
from `0x16E4`. The statement in the v74 and v76 notes that accessories alone
allowed full progression is superseded by this root-cause result.

## Exact v77 fix

V77 changes only the loadout-selected halfword in the initial GameState:

| Purpose | Mask |
|---|---:|
| Level-1 unlock group | `0x1C00` |
| Level-2 unlock group | `0x0380` |
| Level-3 unlock group | `0x0070` |
| Infinity command bit | `0x0008` |
| Exact combined word | `0x1FF8` |

Thus canonical 2595 now contains:

```text
0x16E0 = 0xFC00
0x16E4 = 0x1FF8
0x0FE9..0x0FEB = 60 61 62
Elly m56 = 1
```

The intended battle progression is ordinary attacks
`0 -> 1 -> 2 -> 3`, followed by the native Hyper roll's opportunity to enter
Infinity. Selecting any deathblow still resets the current meter normally.

## Retained deathblow presentation

The v76 animation resource is byte-identical in v77. Clip `0x43` is the
ducking/down motion and `0x45` is the observed collapse/defeat motion; neither
appears in a physical prelude. Clip `0x44` is a valid beam charge/firing pose,
so beam finishers deliberately retain it.

| Tier | Animation | Physical motion order | Finish |
|---|---:|---|---|
| Level 1 Beat Storm | 37 | `40 -> 41` | physical |
| Level 2 | 38 | `40 -> 41` | physical |
| Level 2 | 39 | `41` | native blue beam |
| Level 2 | 40 | `42 -> 40` | physical |
| Level 3 | 41 | `40 -> 41 -> 40` | physical |
| Level 3 | 42 | `41 -> 41` | native blue beam |
| Level 3 | 43 | `42 -> 40 -> 42` | physical |
| Infinity | 68 | `40 -> 41` | native blue beam |
| Infinity | 69 | `41 -> 42` | native blue beam |
| Infinity | 70 | `42 -> 40` | native blue beam |

Each program contains one aggregate damage dispatch and one normal completion.
Infinity retains the common retail Omnigear balance of `50/55/60` power and
`10/20/30` fuel.

## Save compatibility and runtime acceptance

Old DuckStation F1 states and old in-game saves must not be used for v77
acceptance. F1 restores its mounted media and resident gameplay RAM; an in-game
save persists the old ability word. Merely selecting the v77 CUE before loading
either one does not replace `0x16E4`.

The v76 image itself is not a valid comparison boot for successful
progression: it contains `0x16E4 = 0x1808` and is genuinely capped at Level 1.
For acceptance:

1. Fully quit DuckStation.
2. Launch `Xenogears_PW_CD2_mass_driver_standalone_v77.cue`.
3. Choose New Game.
4. Do not load any old F1 state or in-game save.
5. Create any new state or save only after the v77 New Game has started.
6. Mount El-Regulus and use only ordinary attacks until Levels 2 and 3 appear;
   then hold Level 3 long enough to exercise the native Hyper/Infinity roll.

Runtime acceptance requires all three named attacks at Levels 2 and 3, all
three Infinity commands, one normal reset after each selected deathblow, and
the retained offensive motion, beam, damage, fuel, recovery, and command-menu
behavior described above.

## Structural validation

- Canonical 2595 is 9,048 bytes with SHA-256
  `6c81d365be39a4fa66fe7f8e0d19cae4a48201e7107513402c861636654c0b04`.
- Its Elly loadout is `m56 = 1`, `0x16E0` remains exact `0xFC00`, and
  `0x16E4` is exact `0x1FF8`.
- Relative to v76, canonical 2595 changes exactly bytes `0x16E4..0x16E5`,
  from little-endian `08 18` to `F8 1F`.
- Gear 10 retains accessories `60/61/62` at `0x0FE9..0x0FEB`.
- Canonical 2960 is unchanged at 33,600 bytes, with outer roots
  `(2, 0x10, 0x7FF4, 0x8340)` and SHA-256
  `627b332e5b2c15ca7e99d7d44e76fa8f72291634dbbfc32aae1ab19ef511c8c6`.
- Programs 37-43 and 68-70 retain the exact ordered motion contract above,
  one damage dispatch, normal completion, and no physical use of `0x45`.
- The v75-v76 door, route, field, dialogue, and launch assets remain unchanged.
- The manifest contains 125 jobs and 158 declared replacements totaling
  10,912,047 bytes. Their canonical-ID-order aggregate SHA-256 is
  `0afb4e1990d16f265f37e2cc76dada582732d91f4ebb6499130254022f9422c8`.
- The complete automated suite passes 197 tests and 2,246 subtests.

## Packaged image

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v77.bin
size: 696,112,032 bytes (295,966 raw sectors)
SHA-256: f7a695632b1d176fba5c30456c1ea9063a0cc15cf43c1a542353ecfa1afb8a71

output/Xenogears_PW_CD2_mass_driver_standalone_v77.cue
size: 106 bytes
SHA-256: d46e98209dd1f484b4af29d8c036e314739189b245ec734adba15dd40857b6d1

work/mass_driver_v77_stage/manifest.json
size: 180,984 bytes
SHA-256: 304df64bbbbd833949ad3b3a0d9f67050f45c109dc6591ed150dbe26b7a3aa53
```

Cold-boot this exact CUE and choose New Game. No older savestate or in-game
save can validate the v77 Attack-Level repair.
