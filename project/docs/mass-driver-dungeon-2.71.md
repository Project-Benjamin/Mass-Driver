# Mass Driver v94 native subway archive relay

V94 removes the visually mismatched handmade terminal from the abandoned
subway train and replaces it with archive relay H-10, a compact native
Harquebus mechanical actor from retail Goliath Factory field 250. H-10 keeps
the train archive's repeatable 6072 space-program mail, writes no progression
state, and awards no item. Repair Bot M-07 remains outside the train as the
separate item and Gear-parts merchant.

## Native presentation and asset isolation

H-10 uses local actor/sprite bank 1 and M-07 uses bank 0. Their silhouettes,
palettes, actor data, and sprite data are independent; the archive relay is not
a second copy of the shop robot. Entity 14 initializes H-10 at the established
train-mail interaction point, while entity 11 initializes only M-07.

The final checked VRAM layout is:

| Actor | Local bank | Texture pages | Vertical extent |
| --- | ---: | --- | --- |
| Archive relay H-10 | 1 | x768/x832 | y0..256 |
| Repair Bot M-07 | 0 | x896/x960 | y0..256 |

Field scenery ends at x728. Both robot payloads stop at y256, exactly where
the shop overlay's scratch framebuffer begins, so neither actor overlaps the
room art or shop work area. M-07's x896 placement is the retail-proven mapping
from its Aveh donor; H-10 occupies the two preceding canonical texture pages.

The former prop had appended handmade model 15 and header node 30. V94 removes
both. Parsed target 721 now retains the retail 880-byte, 30-node header and the
retail 49,436-byte, 15-model archive. The replacement is wholly actor/sprite
backed, so no untextured model remains juxtaposed against the train interior.

## Field packing and retained return fix

The packed target-721 bundle is 192,848 bytes, leaving 69,296 bytes below the
general `0x40000` field-loader ceiling. Its relevant parsed components are:

- Parsed packed-field header: 880 bytes; SHA-256
  `193eae1c1bca66ce85abc7245d92fcaec13ca77ef21c36b38611afa25bc9e40f`
- Model archive: 49,436 bytes; SHA-256
  `51193f0e147e06ee137b6678e5b4128cee57d07e0aaa9277ac673b43b5eb4b64`
- Script: 1,687 bytes; SHA-256
  `0c056c888553b8f520c886976435ba351ed4b5d03d74f62d5c81be80af716ac3`
- Dialogue: 804 bytes; SHA-256
  `2c9f94a66d876c35f39a517de0ec035ba681dac312cee7bc314c18316add22a1`

V93's subway return correction is retained. Target 363 still returns to target
721 parameter 1 at `(-1250, -218)`, 61 units beyond the expanded automatic-exit
edge. Replacing the train prop does not change that arrival, the connected
walkmesh, or the intentional subway exit.

## Packaged delta from v93

Exactly one declared canonical resource differs from v93: canonical 2048, the
target-721 field bundle. It is 192,848 bytes with SHA-256
`8a5de95aee56a70f430ba75d076b0867e3af5d5d0fa0f4d7b5f405b3e3d63d74`.
Canonical 2049 subway graphics remain byte-identical to v93 with SHA-256
`8fc521c8500270878422a012a074559a822437bcae682e08681b85d2178ed02a`.
Every other declared replacement is byte-identical to v93.

## Packaged v94 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v94.bin`: 695,387,616
  bytes / 295,658 raw sectors, SHA-256
  `f3ef3bcd120fb389d3602be6088d423d007f0a50ccedf0997196efceef9450d0`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v94.cue`: 106 bytes,
  SHA-256
  `c47aaa2ee3fee0155aef53a547a8ce5cb166169fd1eb417eefd5367a7eb60e33`
- Manifest `work/mass_driver_v94_stage/manifest.json`: 190,503 bytes,
  SHA-256
  `0dc1306e8488236b9181ecbe52f2c3850f3196b37537a089cb6e1749328453bf`
- Replacement aggregate: 126 jobs, 158 declared replacements, 10,475,944
  bytes, SHA-256
  `ac16c91de9486fd15a4091ac9ac8eae6e7c523988dc565fbc2965e274bab23ef`
- Complete automated suite: 205 tests and 2,384 subtests, with no failures,
  errors, or skips

## Runtime acceptance

Fully quit DuckStation and cold-boot
`output/Xenogears_PW_CD2_mass_driver_standalone_v94.cue`. Do not load an older
F1 state or in-game save: a full-machine v93 state restores the old resident
target-721 bundle and its handmade terminal even after newer media is selected.

Inside the stationary subway train, confirm that H-10 is a compact native
mechanical actor rather than an untextured freestanding terminal. Press Cross/X
and confirm that the `TRANSIT ARCHIVE RELAY H-10` record opens, can be reread,
and awards no item. Outside the train, confirm that the visually distinct M-07
still opens both shop catalogs and that returning from either menu leaves both
actors intact.

Finally, take the service-junction stairs out of the subway and immediately
walk back. Confirm that the party returns to target 721 parameter 1, remains in
the subway without bouncing upstairs, and can still trigger the normal exit
deliberately.
