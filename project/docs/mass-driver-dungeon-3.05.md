# Mass Driver Dungeon 3.05 - live-camera authorization and automatic north lift

V144 is the current frozen package. It keeps the player's live Defense Archive
camera when the complete `0320 / A-2 / B-5 / C-8 / D-4` authorization is
accepted and makes the opened north lift a silent walk-through transition.
V143's aligned canonical 29 and exact retail field-507 Krelian/Ouroboros
laboratory remain byte-identical.

The declared/staged V143-to-V144 replacement delta and the exhaustive complete-
FAT payload delta are both exactly canonical 1358. Canonicals 17 and 22, every
FAT descriptor, and all other 172 declared payloads are byte-identical to V143.

## Authorization and north-lift behavior

Authorization no longer enters, moves, releases, or zooms a scripted camera.
The accepted-code tail keeps the live gameplay view, plays sound `0x77`, starts
helper entities 18 and 19 on script 4 to open both native-textured leaves, and
waits 32 field frames before returning control.

North-lift controller entity 17 is centered at `(0,308)`. Its no-facing bound
operand is `0x07`, giving 30 units of effective reach with the player collider.
Its X action remains a fallback: before authorization it displays locked
dialogue 9, while after authorization the player can simply walk through the
opened leaves. The collision action is silent while locked and performs the
field-384 parameter-0 transition only after authorization.

The aperture spans x=`-44..44`, and the player-usable centerline spans roughly
x=`-28..28`. An authorized player at z=`277` is safe; z=`278` is the first
contact row, including x=`-28` and x=`28` coverage at z=`279`. The reciprocal
return spawn remains `(0,245)`, 63 units from the controller center, so returning
from the lower bay cannot immediately bounce the player back through the lift.

The package manifest states the collision exception precisely: ordinary
mechanical collision slots remain STOP, except for this deliberate,
authorization-gated automatic walk-through transition.

## Guardian freeze and repaired diagnostic state

The repeated Guardian freeze was not a new V143 or V144 disc defect. The warm
V143 diagnostic state still contained V142's decoded canonical-29 system-name
archive in RAM. Opening the Gear command menu therefore repeated the genuine
odd-address `GetStringEntry` exception even though the mounted V143 media already
contained the corrected, even-aligned archive.

The source state was left untouched. A separately repaired V143 state installs
the V143 canonical-29 alignment without changing gameplay, field, camera, party,
actor, script, or VM state, and that repaired state has also been migrated to
the V144 CUE. The migrated V144 state still has V143 field 376 resident, so the
player must completely leave and re-enter field 376 from V144 media before
testing the camera-free authorization and automatic lift. A new Guardian battle
entered from the repaired state can validate the canonical-29 correction.

Ask the user to navigate and press controls; do not automate the emulator.

## Frozen V144 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v144.bin
size: 696,862,320 bytes (296,285 raw sectors)
SHA-256: b8368ca1bdd7a86f721de7195a577eb869fb2845f2ddc24c6df059c0105a5ba9

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v144.cue
size: 107 bytes
SHA-256: c3d6389a49011c18428119eaa12c557020c23573e92d02cd05adfaf2b8cd9552

manifest: work/mass_driver_v144_stage/manifest.json
size: 242,012 bytes
SHA-256: 25205460eadee811888a1ad9c5a7e87c6b63906765ab328711bf58d8089860f9
jobs: 138
unique replacements: 173
replacement bytes: 12,446,596
route: 35 fields / 70 directed edges

canonical 1358 size: 190,452 bytes
canonical 1358 SHA-256: db9395c7d3e11b73d98014236744ac3bc090d4b82d357a9af289c14cf79ded7f
prepared header size: 1,104 bytes
prepared header SHA-256: 5a1f9906041cea5aa585088bb3c8517f9033f767adf4bb81f2154dd31f2c31fd
packed header SHA-256: 8ec2ab8905031e890a34a70f5f204fd474916c33117b2801fbede1278d441738
script size: 48,937 bytes (47,013-byte bytecode)
script SHA-256: f3c08c932d04de87ac6dc8afb0e754193a8899d17ce6aaffd4c2f31479c75257
```

All 173 declared payloads were extracted directly from the V144 BIN and matched
the stage byte-for-byte. All 6,161 replacement sectors and the boot sector
passed MODE2/Form1 validation. The authoritative V144 full suite passed 263
tests / 3,350 subtests in 62.29 seconds. Fresh user-driven V144 runtime
acceptance remains pending.
