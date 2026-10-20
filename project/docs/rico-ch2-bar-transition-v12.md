# Chapter 2 stair transition patch — v12

Active release: **rico-ch2-bar-transition-v12**.

Open **Play Rico.cmd**, choose **New Game**, then select **The Champ**. Finish the opening conversation and walk down the stairs to the bar. Check that Rico can also return upstairs.

Start this check fresh. An emulator save state from before this patch can retain the old room scripts even when the new disc is selected.

The Champion’s room and bar stairs now preserve Rico’s live party throughout departure. Each destination still initializes solo Rico while loading. The same correction applies to interval skips that reload the Champion’s room.

The previous transition faded to black, removed Rico, reloaded him, and waited for asynchronous character loading before changing fields. This patch removes that unnecessary intermediate load. Native-code inspection confirms that removing the sole party member temporarily hands the player-actor reference to the hidden director. It does not establish the exact live condition behind the reported stall.

Validation: the complete Rico regression suite passed (1084 tests run, 7 skipped, 352.151 seconds). Focused compiled-path checks cover both discs, both stair directions, all six intervals, correct reciprocal entries, party preservation, music, and return-to-room control restoration.

Both rebuilt disc audits passed. Every reachable command outside the exact reviewed transfer sequences remains equivalent to v11, including dialogue calls, choices, scene timing, actor movement, cameras, music and state. Portraits, native geometry and Rico’s level-24 profile remain unchanged. Other chapters and protected Mass Driver/Miang resources remain exact.

**In-game retest is still pending.** These checks verify source, compiled scripts and disc contents; they are not an emulator playthrough. No user saves, memory cards or emulator settings were changed.

## Build evidence

- Disc 1: 3,724 unchanged resources, 4 reviewed changes; all 17 movie streams unchanged.
- Disc 2: 3,719 unchanged resources, 4 reviewed changes; all 12 movie streams unchanged.
- `Xenogears_Rico_Arc_Disc_1.bin`: 719,323,920 bytes; SHA-256 `7812bd2109e3d7e40d9deeb8e1059a8cb0b711ee85816f7d1c85b91f158dcce4`.
- `Xenogears_Rico_Arc_Disc_2.bin`: 694,075,200 bytes; SHA-256 `aa1ad7ee570d5f835883d68a2bd12b7adbe1865757c7272fa0f82e77a3ca0d20`.

Source snapshot: `0447486694303f32204d8d90d5051904d29bf6c391f3585db061aeb2a61deb31`.
