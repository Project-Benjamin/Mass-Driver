# Mass Driver v91 retail reserve-magazine computer

V91 replaces the tall custom console in all five missile reserve magazines
with an existing retail Xenogears asset: the exact two-part hooded facility
computer from Zeboim Materials Storage, field 374. Its smaller silhouette,
dark industrial housing, screen, indicator lights, texture pixels, and palette
now match the surrounding room art.

This is a visual-asset replacement only. All five rooms still enter silently,
and their existing exposition remains available deliberately and repeatably by
pressing Cross/X at the computer.

## Five-room presentation

The reserve route remains:

```text
377 <-> 378 <-> 379 <-> 382 <-> 383 <-> 728
```

Each of targets 377, 378, 379, 382, and 383 now uses the same retail computer:

- Donor: field 374, Materials Storage, models 7 and 8
- Destination: static nodes 22/23 and model slots 0/1
- Shared anchor: `(350, 0, 40)`, yaw `0x0400`
- Visual center: approximately `(500, 0, 0)`
- Interaction controller: entity 7 at `(420, 0)`
- Interaction: facing required, half-width `0x28`, Cross/X
- Content: that room's existing dialogue block 0
- Persistence: repeatable, with no progression-state write

Both model halves retain their exact retail geometry. Only their audited
TPAGE/CLUT state is relocated so the original texture pixels can occupy unused
field-673 VRAM. The texture goes to word rectangle `(576,192,64,64)` and the
palette to `(0,489,256,1)`. Reconstruction checks prove that every other VRAM
word is unchanged.

The resulting shared field resources are:

- Header: 1,520 bytes; SHA-256 `9cab20b3bb1760425a9e5b7482feb2f100722ab67ffb796b67d4ddae1d4662df`
- Model archive: 63,488 bytes; SHA-256 `549136ce6efdee2e5db6bbc3b1884d8b5c88b7af87444a3174808a7c617053a2`
- Relocated model 0: SHA-256 `05e04f10d424869f94862a1d777c1fcff45fa384029885865ee2cb5ca6471b63`
- Relocated model 1: SHA-256 `65d10dd8240b8d0759c7de67ed6e07727e0134be82554dc37c8d118491aa855d`
- Graphics: 116,736 bytes; SHA-256 `3ad95d9772b60da8358731e3e78488afd944a1c7799f0519584bddc0dd40c8ea`

Every room remains below field 673's `0x18000` staging ceiling. The largest
packed room is 90,284 bytes, leaving 8,020 bytes of headroom.

## Packaged delta from v90

Exactly ten declared canonical resources differ from v90: 1360, 1361, 1362,
1363, 1364, 1365, 1370, 1371, 1372, and 1373. These are the five reserve-room
bundles and their five graphics streams. Every other declared replacement is
byte-identical to v90.

| Canonical | Target | Resource | Size and SHA-256 |
|---:|---:|---|---|
| 1360 | 377 | Field bundle | 89,232; `b37a2a58b76f81d02ebc9152e39f11d9999d7144a5e5589c514de169dd2d749e` |
| 1361 | 377 | Graphics | 116,736; `3ad95d9772b60da8358731e3e78488afd944a1c7799f0519584bddc0dd40c8ea` |
| 1362 | 378 | Field bundle | 89,700; `38cbc8746132dc8b5bd8a856d3914c180d66cdacde91250aa11b7d8da3145a59` |
| 1363 | 378 | Graphics | 116,736; `3ad95d9772b60da8358731e3e78488afd944a1c7799f0519584bddc0dd40c8ea` |
| 1364 | 379 | Field bundle | 89,240; `09956587e3e49db8ade8e8d2d3be3e64a2106a4cb52a0adf15fb987db06eb175` |
| 1365 | 379 | Graphics | 116,736; `3ad95d9772b60da8358731e3e78488afd944a1c7799f0519584bddc0dd40c8ea` |
| 1370 | 382 | Field bundle | 89,188; `d9f2fc414e7de51e993d83bd393677ec68fdabcbf177c134eba9dd578ecd573f` |
| 1371 | 382 | Graphics | 116,736; `3ad95d9772b60da8358731e3e78488afd944a1c7799f0519584bddc0dd40c8ea` |
| 1372 | 383 | Field bundle | 89,228; `5d0d1b316aecf220c6c43ba2d93dd05bd786bd165f2020f2640ecde18609231e` |
| 1373 | 383 | Graphics | 116,736; `3ad95d9772b60da8358731e3e78488afd944a1c7799f0519584bddc0dd40c8ea` |

All five scripts and dialogue payloads are byte-identical to v90. The 30
warheads, their solid colliders, silent-entry behavior, repeatable mail,
automatic reciprocal boundaries, black-layer handoff, and progression logic
are also unchanged.

## Packaged v91 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v91.bin`: 695,335,872 bytes / 295,636 raw sectors, SHA-256 `1d8cec5041c2ff98c0e61665b3715e5350d893104efb25d8a57493e22dd9036e`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v91.cue`: 106 bytes, SHA-256 `410400d43d651a93f1ade4ec20420227b42d1db84375212a29266d3538f8d4b6`
- Manifest `work/mass_driver_v91_stage/manifest.json`: 190,187 bytes, SHA-256 `56f0aad56327417060f49505ba8e12d48fc99b8cab6545a7c5c37232aa9da00e`
- Replacement aggregate: 126 jobs, 158 declared replacements, 10,432,888 bytes, SHA-256 `55cdd97208b9d60c3fac9d85ee58abb462231ecb755d095f405ede7fb361f2e8`

The complete automated suite passes 204 tests and 2,374 subtests with no
failures, errors, or skips.

## Runtime acceptance

Fully quit DuckStation, boot
`output/Xenogears_PW_CD2_mass_driver_standalone_v91.cue`, choose New Game, and
load no older F1 state or in-game save. A v90 full-machine state restores its
mounted v90 disc, resident room resources, and the superseded custom console,
so it cannot validate the v91 visual.

After the Guardian battle, enter target 377 through the Defense Archive's west
bulkhead and traverse all five reserve magazines. Confirm that each room shows
the same small hooded Materials Storage computer near the east-side aisle and
that the tall custom console is gone. Face the computer and press Cross/X;
confirm that the complete room record opens and can be opened again. Also
confirm that entry remains silent, all six warheads in each room remain visible
and solid, and both automatic north/south passages still work.
