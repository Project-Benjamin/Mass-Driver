# Mass Driver v105 Central Control terminal frontages

V105 separates Central Control's optional archive reader from its required
launch console. Each visible station now has one small, local X region, and
neither console can intercept the other console or the native east door.

## Runtime identification

The screenshot-era DuckStation state has target 728, the Zeboim Mass Driver
Central Control room, resident. Its 3,462-byte field script has SHA-256
`836e41d197db9534f10362f6e3d8d7f7a7c06e85ed34c004916562ecf5a9c1fd`,
which is byte-exact to v104's target-728 script. The controlled party actor is
at `(-26.9585, 84.0)`, rounded to `(-27, 84)`, in front of the visible launch
station.

The resident v104 controllers were:

- Entity 12, the optional Central Archive reader, remains at `(57, 71)`. Its
  native initializer required facing and used `0x82` by `0x82` interaction
  operands. The engine doubled those operands and included the 16-unit player
  extent, producing 276 units of effective reach on each axis.
- Entity 13, the required launch console, was centered behind the console at
  `(-154, 125)`. It did not require facing, but its `0x46` by `0x14` operands
  produced an offset 156-by-56 effective rectangle. The large rectangle was
  why the captured launch stance could still reach a distant hidden pivot.
- Entity 14, the native east door, remains at `(181, 88)`. Its `0x05` by
  `0x1E` operands give a 26-by-76 effective region.

The optional reader therefore covered much of the room through oversized,
facing-gated geometry, while the required launch action depended on an offset
rectangular controller rather than a local console frontage.

## Exact correction

V105 assigns the two console actions to distinct, audited walkmesh approaches:

- Entity 12 keeps the archive station at `(57, 71)` on triangle 23.
- Entity 13 moves the launch station to `(-54, 94)` on triangle 16.
- Both controllers are proximity-only, use encoded half-width `0x08`, and
  therefore have 32 units of effective reach after the player extent.
- Entity 12 retains repeatable archive dialogue block 1. Entity 13 retains the
  gated Elly-only memory, second-press Citan arrival, and capsule-launch logic.
  Dialogue, progression, and action ownership do not move between entities.

The archive and launch centers differ by 111 units on x. Their two 32-unit
regions are therefore disjoint. The nearer archive-to-door x separation is
124 units, greater than the archive's 32-unit reach plus the door's 26-unit x
reach, so the native east-door region is disjoint as well. The rounded captured
launch stance `(-27, 84)` lies inside entity 13's new region and outside entity
12's region.

The door controller, native opening animation, helper model, sound, destination,
walkmesh, terminal artwork, apparition actors, Citan route, dialogue, and
launch sequence are unchanged. Native treasure entity 16 at `(-121, 74)` and
its action also remain intact.

## Exact target-728 identities

This is a script-only canonical-2062 delta. Only canonical 2062 changes from
v104; canonical 2063 and every decoded component except the script remain
byte-identical.

| Resource | v104 | v105 |
|---|---|---|
| Target-728 bundle (canonical 2062) | 62,340 bytes, `cfeaad35cf9d5abdd96f1be414f82a4c6d7a07d677a8472b1014e77dc6f386b2` | 62,392 bytes, `645cd0a0bf03dc011eed3b71a58513ee7a70b86d8a283b41a3b9b282e1684c3a` |
| Script component | 3,462 bytes, `836e41d197db9534f10362f6e3d8d7f7a7c06e85ed34c004916562ecf5a9c1fd` | 3,510 bytes, `972d82f71c93189c685a24addab8a91ec6449be2834c6413ff81ed5ed9223a39` |
| Graphics (canonical 2063) | 245,760 bytes, `dc60d25ba5c4e73891e498363816abf043fe61a87081f828cd20bb45bd6abf7a` | unchanged |

The unchanged decoded target-728 data is:

- Header: 1,088 bytes,
  `15612fefcd1a4ec8fef6cba81d31370c8a4d8ced8705bd0453e7cb9202fbfd95`.
- Images: 4 bytes,
  `df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119`.
- Walkmesh: 2,540 bytes,
  `6a1f335cd2cf00bcec7a5412b8ab7392fcff378912fd2857880d69f2186e6a14`.
- Models: 13,504 bytes,
  `9bb9ef16cb1f85b0c2a4052d79a710cb91224ea78be7f7b72c246ac6183ab24e`.
- Actors: 18,640 bytes,
  `2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538`.
- Sprites: 10,660 bytes,
  `4aab88cc9fe7f19ec55b53e1eb4123e7cf6ea8f7772572cdb78e0b4a67663423`.
- Encounters: 528 bytes,
  `e88b412320050425ae87abad80b51749da8171b023e943604cf47a370535ab38`.
- Dialogue: 5,044 bytes,
  `c5300fd84da598f56215c5561feee6932de3f726524b53704cb56fa762503006`.
- Triggers: 0 bytes,
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

The script grows by 48 bytes; field packing makes canonical 2062 grow by 52
bytes. All other 161 declared replacements are byte-identical to v104. A raw
v104/v105 BIN comparison changes nine zero-based sectors and 8,958 raw bytes:
sectors 31, 172,926, 221,410, and 221,435 through 221,440. That count includes
the rebuilt image bookkeeping and MODE2 error-detection/correction bytes. All
nine changed raw sectors validate as MODE2/Form1 with correct EDC/ECC, and every
unlisted raw sector is byte-identical.

## Packaged v105 identities

- BIN: 695,815,680 bytes, 295,840 raw sectors, SHA-256
  `e495adefc0d01a1c284b23bb82f18f5f96bc7e058b2641ebe6cffa3c54e12be9`.
- CUE: 107 bytes, SHA-256
  `1e09351beed59f6d0521d2af179216bd9377de9f25ba1b142ffd64a887293b41`.
- Manifest: 200,496 bytes, SHA-256
  `ded64e33d94fc9e76487d83771bad0d50a770e486de096f446779bcda3de5f8f`.
- Declared replacements: 162 across 128 jobs, totaling 10,853,608 bytes;
  canonical-ID-order aggregate SHA-256
  `8b8f1fbccf6ddd35f3754de3dd4ae23092698462f307fad742ee9e2a0dd4e626`.
- Regression suite: 209 tests and 2,653 subtests passed with no failures,
  errors, or skips.

The release image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v105.cue
```

## Runtime acceptance

A v104 state saved with target 728 resident cannot validate v105. Loading that
state restores both the v104 mounted image and the already loaded v104 field
script; selecting the v105 CUE before loading the state does not replace either.

The clean acceptance path is to fully quit DuckStation, cold-boot the v105 CUE,
choose New Game, and load no older F1 state or in-game save. For a focused
Central Control retest, explicitly mount v105 media, completely leave Central
Control so target 728 is unloaded, and then re-enter it. Merely changing the
mounted image while target 728 remains resident is insufficient.

Press X at the east archive station and confirm that only the optional Central
Archive mail opens. Press X at the separate launch station and confirm that
only the required memory/launch sequence runs. Finally, use the east door and
confirm that neither console intercepts its native opening and reciprocal
transition.
