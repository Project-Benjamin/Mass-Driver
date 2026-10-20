# Mass Driver v75: integrated doors and Goliath Factory lower route

V75 repairs the two created doors in the Defense Archive and replaces the
incorrect lower area with a reciprocal two-room Goliath Factory route.

The west bulkhead now divides the exact native field-394 wall aperture into
two moving leaves. The north lift does the same with the exact lower panel on
the north wall. Both retain the donor texture and UVs, place only a dim reveal
behind the original wall plane, and omit the bright trim that looked pasted
over the background. Each pair uses a finite 24-frame opening routine and a
bounded party crossing.

The resulting route is:

```text
Defense Archive 376
  <-> Goliath Factory lower-access hall 384 (retail source 260)
  <-> Goliath Factory defense bay 386 (retail source 263)
```

Target 384 retains two different native animated factory doors. The Guardian
reveal and battle occur only in target 386. Victory returns Elly and Emeralda
on foot in that bay; its native threshold leads back through target 384 and
the archive lift, so the party can continue through target 376's west door.
Citan remains absent from the dungeon and battle.

The launch-support hub's previously dead panel now enters target 367, a
compact blue materials laboratory cloned from retail field 380 instead of
another source-378 room. Its computer presents repeatable archive mail, and
its native west panel animates and returns to the matching hub doorway.

## Structural validation

- Route contains 33 target fields and reciprocal edges for
  `376 <-> 384 <-> 386`.
- Target 376's final header contains 36 actor records and has SHA-256
  `df510e6d99747438e61310596e4bdb5cb4f85d5589b6af25131d8d9b626658a8`.
- Its six door models have archive SHA-256
  `1720f5af5e753aa89bcbb9d6032e9127576e6ceb314ec99ec58219e9047bcd24`.
- Target 367 uses source 380, target 384 uses source 260, and target 386 uses
  source 263.
- The complete automated suite passes 197 tests and 2,240 subtests; the final
  manifest contains 125 jobs and 158 declared replacements.
- El-Regulus retains v74's `Atk Lv1/2/3 Max` loadout, complete Level-2 and
  Level-3 programs, and mixed melee-and-ether Infinity finishers.

## Packaged image

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v75.bin
size: 696,112,032 bytes (295,966 raw sectors)
SHA-256: 31bb91d6bb9d781ce39693c1eb5d77dc211717ea2c27d2381c6147db83845df4

output/Xenogears_PW_CD2_mass_driver_standalone_v75.cue
size: 106 bytes
SHA-256: 0eb635968ac69772a7772f4d9f2735daff322cde72b4713ac2780e4d3daaa952

work/mass_driver_v75_stage/manifest.json
size: 180,849 bytes
SHA-256: de960f5289a9c5a16893d1578177c3daec6cacde66178cd5406dbc047c5b33e1
```

Cold-boot this CUE and choose New Game. Older DuckStation states retain the
resident field code from the build that created them and cannot validate the
new doors or route.
