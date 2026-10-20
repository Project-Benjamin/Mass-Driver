# Mass Driver v88 source-378 hanging-terminal correction

V88 aligns every copied source-field-378 hanging-terminal interaction with the visible computer in targets 365, 366, 368, 369, 370, 371, and 724. Entity 14 previously remained at `(-89, 90)` with no-facing bound `0x1E`, giving an effective 76-unit reach around an invisible aisle position. Each copy now places entity 14 at `(-124, -25)` with tight no-facing bound `0x08` and effective 32-unit reach beneath the actual beige/orange overhead-arm computer. The dialogues, progression roles, graphics, and walkmesh remain unchanged.

## Live evidence and corrected geometry

The exact v87 target-368 snapshot is 1,997,019 bytes with SHA-256 `616fe765c563e4b86a03c9396b9ba84e22241711de06fccee867c50ab79212e5`. Its resident 2,857-byte target-368 script has SHA-256 `416d252549fe2b7a44f369f3f61c041df62eaf8597f90f00cea0e4ca58b4a6d1`. The capture places the player at `(-124.075394, -24.551453)` on walkmesh layer 0, directly beneath the visible computer. Pressing X opens nothing in v87 because entity 14 remains at `(-89, 90)`: the `114.551453` z separation exceeds its effective 76-unit reach.

The visible overhead-arm computer is static node 25/model 4 with yaw `0x0600`; its checked model SHA-256 is `56625491e9d7d52225e3391cf6fe7cd905b6a59a2d54f80329b2a2403bfe8aed`. The corrected controller lies strictly inside walkmesh triangle 16. Its x/z vertices are `(-129, -28)`, `(-106, -5)`, and `(-80, -1)`, and the controller's barycentric weights are `(0.885375494, 0.023715415, 0.090909091)`. All weights are positive, so `(-124, -25)` is inside the connected operator surface used by the live capture.

Desk entity 13 remains at `(45, -42)` with no-facing bound `0x1E` and effective 76-unit reach. The hanging controller's right edge is x `-92`, while the desk controller's left edge is x `-31`, leaving a 61-unit x gap between their interaction zones.

## Preserved terminal roles

In Railway target 368, desk entity 13 keeps dialogue 0 and remains the sole writer of accelerator-rail bit 1. Hanging entity 14 keeps repeatable dialogue 1 containing Aron's 6081 mail to Lena and writes no progression bit.

In the six lore-only targets 365, 366, 369, 370, 371, and 724, desk entity 13 keeps repeatable dialogue 1 and hanging entity 14 keeps its distinct repeatable dialogue 0. Neither interaction writes a progression bit. V88 changes only the hanging controller position and bound; the paired mail and all authored text remain byte-identical.

## Packaged delta and identities

Only canonical IDs 1336, 1338, 1342, 1344, 1346, 1348, and 2054 differ from v87. Those are exactly the seven affected source-378 field bundles:

- Target 365 / canonical 1336: bundle 53,156 bytes, SHA-256 `58ee3ea6a64aa6a5d9d3bde1e73b48d7d2c913df79aa7d986213bb2316832030`; script 2,848 bytes, SHA-256 `990cbf8cfa0ef3f2d584358a064e5f9c67e028f7855ee116ddb1bd99b57f1072`; dialogue 828 bytes, SHA-256 `100bd65fba3837f97cbe6607fbbf8a22db04f49def804e2cc0706ac004e6dd25`.
- Target 366 / canonical 1338: bundle 53,364 bytes, SHA-256 `e7f7a1f7eb9b60baefd952632269bc74ec9834d76bb2a90fac4100a9fb348c0d`; script 2,848 bytes, SHA-256 `cb8822ef9aee7b3248b9e5963a209375033bc3c5c35155242482d4afcb0a9ea2`; dialogue 1,016 bytes, SHA-256 `c5e3c781b8da6cfab78baf9cfbcf835cf41e7ca47872ffbeaa1d40783fb7ffdc`.
- Target 368 / canonical 1342: bundle 52,996 bytes, SHA-256 `83d69e0bd52ea4c9c8521f917e5f3666b50df50dd41d4f31a9492b476e9ea3b9`; script 2,857 bytes, SHA-256 `354290be6cdfc1eeb7f45d969648412c8b4322d86de40f22f467b5de843a4434`; dialogue 672 bytes, SHA-256 `fb0c59b3d3753dea0ed78c7e596672ebd0d48132c77d598084005b3495281ea8`.
- Target 369 / canonical 1344: bundle 53,384 bytes, SHA-256 `6aca0fcb907f33dd835073adec3b32ee1e27059bd658f14a245f22c537e93f89`; script 2,848 bytes, SHA-256 `c17e5a2d6066203fd281f4dfdbba9fa2f6b121c4f27744027622b337d6ecb977`; dialogue 1,031 bytes, SHA-256 `8fcf2877ad397636eb74ae199eb48b8d2f1d1639c7e1cbf53c81de78afd00a8f`.
- Target 370 / canonical 1346: bundle 53,384 bytes, SHA-256 `c825df5828b1c7dddbbb95303d4a5ccba1f0b65d7cb7dddcc9aff3a85459e5f8`; script 2,848 bytes, SHA-256 `2513c1ffe0ef06fea1fa955082029469bbf36a24a45252b36017756cc3ed0dac`; dialogue 1,025 bytes, SHA-256 `7f638cb5bc01354ef721c2a25576aa774d1437e665f605a7bfee1d569c0ef2f9`.
- Target 371 / canonical 1348: bundle 53,552 bytes, SHA-256 `d9301e58372b8b4c77001222591c575e375803f4b258cbaf54651fc8636e25da`; script 2,848 bytes, SHA-256 `c827771ebdada65a356a60a21aef6f578018ac3f9ee26c1e395071c5774a2d17`; dialogue 1,177 bytes, SHA-256 `29a35967240f1c18707eeb48f7d78ccf857243961055a243f379a1f7caee0421`.
- Target 724 / canonical 2054: bundle 53,616 bytes, SHA-256 `875e0f31c304a393cdad6d18a49249f984c2c9a0649178ce7c563c241509c9d4`; script 2,848 bytes, SHA-256 `23aca742b7fb275560d96bc00d9338fbfcb9ed9ad11e664be77c0472ee353624`; dialogue 1,233 bytes, SHA-256 `5c1ab3417dbb52eb2a434a3411a34ed33b3b09d49bb83878fe3c952b84ed0dad`.

The packaged v88 artifacts are:

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v88.bin`: 695,293,536 bytes / 295,618 raw sectors, SHA-256 `a0098bf0b3c4a3872de1dc052a0f776b35361e7e4f0aef2534eb22b8e1ffab4f`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v88.cue`: 106 bytes, SHA-256 `4f2fa15aaee05816c08374c4c64e5b1ab44a8b8ac65dc83ed82cbd86ef67c13e`
- Manifest `work/mass_driver_v88_stage/manifest.json`: 187,765 bytes, SHA-256 `b9c3a1abc806f50fa98cd6c4a1d2a91c4b02c1c7968386d6d610e4a1c4112ed9`
- Replacement aggregate: 126 jobs, 158 declared replacements, 10,392,651 bytes, SHA-256 `e1425b597abc170063ffd313f29af6084a008d0cba75000af513d92849ccc035`

The complete automated suite passes 204 tests and 2,349 subtests with no failures, errors, or skips.

## Runtime acceptance

Fully quit DuckStation, boot `Xenogears_PW_CD2_mass_driver_standalone_v88.cue`, choose New Game, and load no older F1 state or in-game save. In target 368, confirm the desk at `(45, -42)` still performs only the rail switch, then press X beneath the beige/orange overhead-arm computer near `(-124, -25)` and confirm it opens Aron's mail without writing the rail bit. In targets 365, 366, 369, 370, 371, and 724, confirm both the desk and hanging computer present their separate repeatable mail and that neither interaction changes progression. The old `(-89, 90)` hotspot must open nothing.

The preserved v87 full-machine state is evidence for the old failure, not an acceptance state: loading it restores v87 media and the resident source-378 script with entity 14 at `(-89, 90)`. Cold-boot v88, or leave and re-enter the room from v88 media, before testing the correction.
