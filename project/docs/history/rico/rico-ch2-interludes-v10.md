# Chapter 2 — narrated interludes, v10

Active release: **rico-ch2-interludes-v10**.

Open **Play Rico.cmd**, start **New Game**, then choose **The Champ**. Inspect the bout card in Rico's room or the bed next door and choose **Continue** to advance. **Stay here** keeps the current interval.

Chapter 2 now adds six private Rico interludes and uses narration to skip original campaign events. The previous recreated Baptism, sewer quest, title-defense battle, Finals, crash and flight are absent from its active route. The chapter ends at the original Central District story boundary and returns to Chapter Select.

Optional conversations cover every retained resident. Named speakers have portraits and yellow names; anonymous residents have neither invented names nor portraits. Suzarn has the tighter face-and-neck framing, and Latina has a portrait based on her native sprite.

Validation: **1081 tests passed**, 7 skipped (398.906 seconds). Both disc audits passed. The default launcher verified the fresh source snapshot and exact media.

**Runtime status: untested in the emulator.** The original upper routes to two rooftop residents still need a movement playtest. Small hand actions and possessions in the interludes are described in narration, without new animated props. Enter through Chapter Select; old emulator states contain the previous scripts and progression format.

This remains a standalone narrated prototype. Seamless integration into ordinary campaign progression is future work.

## Disc verification

- Disc 1: 3,700 resources exact against v8, 28 reviewed changes; all 17 movies exact.
  - 719,330,976 bytes; SHA-256 `2c24341d324ba4f8bb4b6bbaeefe86c5d7f45e2fc3851c2f5416db1d9155b01f`.
- Disc 2: 3,695 resources exact against v8, 28 reviewed changes; all 12 movies exact.
  - 694,082,256 bytes; SHA-256 `fe4fe91aa526bef19f5b4083f587b1c7776fc1b48af9b02a8935e9223abbe67a`.

All original Disc 1 Nortune donor scenes remain exact. Retired anthology resources equal the respective original disc. Other portraits, Rico's level-24 state, and the protected Miang resources remain exact against v8. Mass Driver and Soylent module source snapshots are unchanged.

Source snapshot: `1bb867b3ba51edc2c0cc406af4a8b4ab2d3efcedf8ffa399ce9a58a2bbbd1b25`.
