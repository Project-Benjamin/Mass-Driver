# Chapter 2 dialogue update — v11

Active release: **rico-ch2-dialogue-v11**.

Open **Play Rico.cmd**, start **New Game**, then select **The Champ**. Use the bout card or bed and choose **Continue** to advance between intervals.

All six added story scenes have been rewritten. The cup exchange is gone. Suzarn wants to earn her freedom through Battling; Rico respects her ambition as a rival. Her death, his injury and his loss of the title challenge his faith in strength. His refused pardon and later choices remain unresolved.

No action narration is printed in Chapter 2 scenes. Time skips use brief captions. Optional NPC interactions contain only the NPC’s speech; Rico listens. All 21 interaction entries retain NPC speech, including the phase-specific Hammer repeat. Named characters retain portraits and yellow names.

The rewrite uses extracted retail Nortune dialogue as its voice and continuity reference. It is newly authored material, not recovered original dialogue. A public [English/Japanese script reference](https://xenogears.us/) is also available.

Validation: the full regression suite passed (1081 tests run, 7 skipped, 441.546 seconds). Both native disc audits passed. The default launcher verified the current source snapshot and exact media.

The audit verified unchanged actor placement, movement, cameras, music, choices, routes and progression against v10. All portraits and the level-24 Rico state remain exact. The new interludes do not replay original campaign scenes or battles.

**Emulator playtest: not performed.** This remains a standalone chapter prototype. Enter through New Game and Chapter Select; an older emulator state retains its old scripts.

Build recovery: the initial build exhausted C: storage. Its incomplete disc outputs were removed before retrying. Windows LZX compression reduced storage for the two older v8-fixed disc images; both still match their recorded SHA-256 hashes. The successful tests and build then ran sequentially.

## Disc evidence

- Disc 1: 3,721 unchanged resources, 7 reviewed changes; all 17 movies exact against v10.
- Disc 2: 3,716 unchanged resources, 7 reviewed changes; all 12 movies exact against v10.
- `Xenogears_Rico_Arc_Disc_1.bin`: 719,323,920 bytes; SHA-256 `0d8102f4d7e7df91256abceb68f2aa8ca2632e09814673788baa6e6877e68ca7`.
- `Xenogears_Rico_Arc_Disc_2.bin`: 694,075,200 bytes; SHA-256 `b380a6c93ec854593bd75285909afa3563acc486efc04443adea6f5ce8476595`.

Source snapshot: `13d724094959eb7e7ded737754a6361e1aa5c80993ca98077eb04604bd149de7`.
