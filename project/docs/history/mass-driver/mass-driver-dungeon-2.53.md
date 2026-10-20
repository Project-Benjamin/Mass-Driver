# Mass Driver v76: El-Regulus offensive-motion repair

V76 corrects El-Regulus's remaining collapse-motion mistakes while retaining
v75's complete dungeon route and v74's Attack-Level-Max repair. Beat Storm now
uses two confirmed offensive motions, and every Level-2, Level-3, and Infinity
physical prelude is restricted to El-Regulus clips `0x40` through `0x42`.

The inherited v75 facility work is unchanged. Both Defense Archive doors
still reconstruct the exact native field-394 wall aperture and use a bounded
party crossing. Target 384 remains the Goliath Factory hall from retail source
260, target 386 remains the distinct defense bay from retail source 263, and
target 367 remains the blue materials laboratory from source 380.
In compact contract terms: target 384 is retail source 260, and both archive
doors retain a bounded party crossing.

## Why the 14:50 state cannot test the repair

The DuckStation state captured at 14:50 on July 31, 2026 is a full-machine F1
snapshot, not a disc-independent game save. Its header explicitly mounts:

```text
Xenogears_PW_CD2_mass_driver_standalone_v73.cue
```

Its saved Gear 10 record also contains accessory bytes `5A 5B 5C`, the v73
Frame HP10/30/50 loadout. V75 was packaged later, at 16:06, so this snapshot
cannot contain or validate v75 or v76. Loading it restores its old mounted
disc, resident field and battle code, inventory, party, and gameplay RAM;
selecting a newer CUE first does not upgrade the state.

For v76 acceptance, completely exit DuckStation, launch the v76 CUE, choose
New Game, and do not load F1. A new F2 state may be created only after that
cold boot. The historical v71 continuation is also unsuitable.

## Attack-Level progression retained

The cold-boot GameState still assigns Elly Gear 10, writes her natural Gear
deathblow flags as little-endian `00 FC`, and equips:

```text
60 61 62  =  Atk Lv1 Max / Atk Lv2 Max / Atk Lv3 Max
```

Canonical 2594 verifies effect selectors `06/07/08` for those items. The
retired `5A/5B/5C` records instead use Frame HP selector `05`. On a v76 New
Game, ordinary attacks can therefore advance Attack Level `0 -> 1 -> 2 -> 3`,
after which the native Hyper roll can enter Infinity. Selecting a deathblow
resets the meter normally.

## Corrected motion contract

Clip `0x45` is the observed collapse/defeat clip and is absent from Beat Storm
and every higher-tier program. Clip `0x43` is the distinct ducking/down
motion and is not used by a physical prelude. Clip `0x44` is a valid beam
charge/firing pose, so beam finishers deliberately retain it. The physical
motions before those finishers still use only confirmed offensive clips
`0x40`, `0x41`, and `0x42`.

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

## Structural validation

- Beat Storm contains `0x40` once, followed by `0x41` once, with damage after
  both and no `0x43`, `0x44`, or `0x45` motion call.
- Programs 38-43 and 68-70 match the ordered physical sequences above and
  contain no collapse/defeat call to `0x45`.
- Beam variants retain the native blue-beam packet and valid firing pose
  `0x44`; physical-only programs do not borrow that pose.
- Canonical 2960 is 33,600 bytes with outer roots
  `(2, 0x10, 0x7FF4, 0x8340)` and SHA-256
  `627b332e5b2c15ca7e99d7d44e76fa8f72291634dbbfc32aae1ab19ef511c8c6`.
- Its relocated model root remains below the runtime-sensitive `0x8000`
  boundary, and the primary model/sound container remains byte-identical to
  retail.
- The complete automated suite passes 197 tests and 2,242 subtests.

## Packaged image

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v76.bin
size: 696,112,032 bytes (295,966 raw sectors)
SHA-256: 2335f0cf46a1bab32d54aeb221ca418af4cf417b879ce9141c9efc8da23c6c47

output/Xenogears_PW_CD2_mass_driver_standalone_v76.cue
size: 106 bytes
SHA-256: e25563d81464f96edc1f613d9c917db5616ced5513e6230951fcadd6fd2d1c28

work/mass_driver_v76_stage/manifest.json
size: 180,984 bytes
SHA-256: c19e255b216f8db7385f27946e8ecbfb0fe392d2faa6628fe3d95cab111f9b55
```

The manifest contains 125 jobs and 158 declared replacements totaling
10,912,047 bytes. Their canonical-ID-order aggregate SHA-256 is
`cd1df6976415128f68eb4392b854131bace4b987e0fd1a7b142c0582194f056f`.

Cold-boot this exact CUE and choose New Game. Do not load the 14:50 v73 state
or any other older F1 state during acceptance.
