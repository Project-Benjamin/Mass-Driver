# Flying Weltall-2 + Disc 1 replacement mod (v6)

This is an isolated USA Disc 1 mod. It keeps Xenogears' native publisher and
title sequence. Choose **New Game** and the game enters the world map at the
first playable position after Lahan is destroyed.

Version 6 also replaces regular Weltall throughout Disc 1. Story assignments
use native Gear ID 1, and every audited Gear-0 presentation/data path is a
Weltall-2 compatibility alias. This includes the separate real-time Nortune
Battling engine and the separate model-7 cinematic Weltall that Citan delivers
before the Blackmoon Forest Rankar battle. Version 6 retains Weltall-2's native
deployed-wing, vertically bobbing flight loop and a pair of compact white
engine lights pinned to its wings while it is airborne.

## Ready-to-play image

- `output/Xenogears_US_CD1_Flying_Weltall2_v6.cue`
- `output/Xenogears_US_CD1_Flying_Weltall2_v6.bin`
- BIN size: `718448976` bytes
- BIN SHA-256: `48fce808c14c08eca91ed4611c03147c2c46d0fbfe76e1077e37197c2a76d6b6`

The earlier images remain separate artifacts; rebuilding v6 does not
overwrite them.

Load the CUE file in an emulator. The image is MODE2/2352 and should not be
converted to a plain ISO.

## Controls

- **Jump / physical Square:** take off while Weltall-2 is on the world map.
- **X / physical Cross:** move forward while flying, using the direction
  Weltall-2 is facing.
- **Triangle:** request landing.
- **Jump / physical Square again:** also request landing.

Landing uses the original Yggdrasil terrain and landing validation. If the
native game considers the current spot invalid, Weltall-2 remains airborne.
The Yggdrasil deck transition is disabled so Triangle is dedicated to landing.

On takeoff, Weltall-2 switches to its native deployed-wing flight animation,
including the built-in vertical bobbing loop. Two single-particle white engine
lights, duplicated from a compact native effect, remain pinned to the left and
right wings. They do not spray, expand, or leave a fire trail. The lights stay
active through ascent, cruise, and descent, then the native touchdown event
clears them as the ground pose is restored. Their private world-map particle
channel does not replace the Yggdrasil terrain or wake effects used by the
underlying flight task.

Normal world-map memory-card saves made while flying retain the native
airborne state. When such a save is loaded, a lazy flight-state guard restores
Weltall-2's deployed-wing animation and rebuilds its two private wing lights
before normal airborne updates continue.

## Starting state

- Scenario flag `0x18`, position 1: the immediate post-Lahan world map at
  `(29947, 11075)`.
- Fei is the only party member and is level 99 with full HP/MP and all on-foot
  and Gear deathblows enabled.
- Fei pilots Weltall-2 (Gear ID 1), fully repaired and refueled.
- Weltall-2 has the maximum-output endgame loadout: XENO-30400 frame,
  OMEGA100 engine, Z Gold100 armor, and three GNRS50 accessories. Its checked
  cached totals include 30,400 HP, 1,000 fuel, and +150% engine output.

"Best" is defined here as maximum Gear output. Xenogears' endgame parts have
real tradeoffs: OMEGA100 sacrifices fuel capacity, Z Gold100 favors physical
defense, and Z Chargers favor fuel recovery.

Version 6 fixes v5's Fei/Elly on-foot battle switching. Canonical 2595 now
starts from the retail USA Disc 1 GameState and imports only Fei's audited
high-level character record before applying the declared Fei/Weltall-2 edits.
All other character records, inventory, and unrelated field/story variables
remain retail. The battle-frame mask also retains retail `0xFFFF`; membership
still makes the initial party Fei-only, while later story scripts can safely
add or reorder temporary companions without dropping Fei from the battle
loader's sparse slot list.

## What the mod changes

The finished image contains 32 checked replacements:

| Canonical IDs | Purpose |
|---|---|
| 37 | Weltall-2 presentation, native-flight input routing, deployed-wing animation, and private wing lights |
| 52 | Battling roster-0 fallback bundle aliases native Weltall-2 roster 10 |
| 443 | Mounted field sprite aliases native Weltall-2 |
| 610, 654, 714, 728, 734, 1006, 1052, 1056, 1106, 1452, 2062 | All 24 persistent Fei-to-Weltall assignments become Gear ID 1 |
| 1048, 1050, 1052 | Every Disc 1 Nortune Battling player-Weltall selector becomes native roster ID 10; the Weltall mirror opponent is replaced too |
| 1586 | Native title-field New Game route |
| 2054 | Inert field-724 gateway that calls `WORLD_MAP(1,1)` |
| 2144, 2145 | Weltall-2-native 3D field/cutscene controller and geometry in Weltall's compatibility slot |
| 2158, 2159 | Weltall-2-native controller and geometry in the scripted model-7 Weltall slot used by five Disc 1 scenes |
| 2594, 2614 | Gear-0 menu/system and live-battle records alias Gear 1 |
| 2595 | Fei, equipment, post-Lahan state, Gear-0 fallback record, and fixed display-name alias |
| 2602 | Gear-parts shop model and pose selector |
| 2641 | Blackmoon Rankar intro battle bundle, with only its embedded dropped Weltall rebuilt from native Weltall-2 data |
| 2926, 2927 | Standard battle geometry and animations |
| 2988 | Equipment-screen 3D preview |
| 3939, 3949 | Both byte-identical regular-Weltall world-map sprite slots |

The world-map flight implementation deliberately reuses the retail Yggdrasil
task for altitude, terrain collision, camera behavior, particles, and landing
checks. The Yggdrasil models are hidden while Weltall-2 is synchronized to its
native flight entity.

Nortune Battling uses a different engine and roster from standard battles.
The Disc 1 overlay's own table identifies selector 0 as `WELTALL` and selector
10 as `WELTALL-2`; its loader resolves those selectors to canonical resources
52 and 62. The mod changes the field selectors to 10 and also installs resource
62 in slot 52 as a visual fallback. It does not transplant incompatible normal
battle assets into the Battling engine. The late optional roster menu's old
third Weltall entry is removed, leaving only Xenogears and Weltall-2.

Weltall and Weltall-2 also have different 3D field skeletons. The compatibility
controller keeps Weltall-2's native keyframes and native animation programs,
then expands its nine-entry table to the 23 indices requested by Disc 1 story
scenes. Weltall-only motions use conservative Weltall-2-native substitutes;
the result is skeleton- and index-safe, though a complete end-to-end emulator
playthrough of every cutscene has not been claimed.

The Rankar intro is a separate case: its on-screen dropped Weltall is model-7
entry 2 embedded in canonical 2641, not the normal player-Gear resource.
Version 6 replaces that geometry and rebuilds its 32-program event controller
from native Weltall-2 animation data. Entry 0 is Rankar Dragon and entry 1 is
Citan's flying carrier; their complete controllers and models, along with the
trailing sprite payload, remain byte-identical. The matching standalone
model-7 pair (2158/2159), used in five Disc 1 story scenes, is replaced too.
Canonical 2150/2151 is Rankar and is deliberately untouched.

DuckStation save states include already-loaded model data in emulated RAM.
Loading a v3/v4 state saved during this dialogue therefore restores the old
Weltall even when v6 is mounted. Test v6 by cold-booting it and entering the
Rankar sequence from a normal memory-card save made before the battle event.

Likewise, v5 memory-card saves and save states retain v5's old GameState.
Choose New Game for a clean v6 party test, or migrate an existing save
explicitly before using it to validate this fix.

The build verifies the USA retail source by size and SHA-256, builds all 32
replacements in one Xenoiso pass, re-extracts and byte-checks all 32 from the
result, checks an untouched post-Lahan map resource, validates MODE2/Form1
EDC/ECC, verifies native title boot, and confirms the source disc was not
modified.

## Rebuild

The expected source is `Xenogears (Disc 1).bin` in the repository root:

```powershell
python tools/build_weltall2_flight_mod.py --force
```

Expected retail source identity:

- Size: `718738272`
- SHA-256: `39c547a9afc6da15d847ef81a2c6cea1a6516bdfa562cf13b0999b04e8598bda`

The checked replacements and machine-readable manifest are staged under
`work/weltall2_flight_v6_stage`.

Run the focused verification suite with:

```powershell
python -m unittest tests.test_weltall2_flight_mod -v
```
