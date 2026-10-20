# Build inventory baseline â€” September 5, 2026

October 19 Mass Driver V176: `mass-driver-v176-release-candidate-20261019` is
selected. The 426-test suite passes with two existing skips. The BIN is
696,140,256 bytes, SHA-256
`0dc54a5306e97f41989ddd519daec860821af1038817c29f35b5d4b5d8ad87f8`.
V175 repaired the early native save entry; V176 corrects exactly four Missile
Command input-mask bytes to match the displayed Triangle controls. All other
V175 prepared content, dialogue and protected Central Control remain identical.
See [V176 notes](mass-driver-v176.md), [release QA](mass-driver-release-qa.md) and
[public player directions](mass-driver-public-player.md). Earlier paragraphs
below preserve historical candidate status.

October 19 Mass Driver V174: `mass-driver-v174-release-candidate-20261019` is selected. It restores native New Game/Continue/Sound and repairs the authorized north lift's straight approach. The full suite passes (417 tests, two existing skips). The built BIN is 696,140,256 bytes, SHA-256 `28e712461ccababebb2ce654a27fc0004ac51a1b5a4615158b6e2d568d052ade`. Only three prepared resources differ from V173; protected Central Control and all dialogue remain unchanged. Native V174 save/reload and full route acceptance are in progress. See [V174 notes](mass-driver-v174.md).

October 19 Mass Driver V173: the selected standalone candidate is `mass-driver-v173-release-candidate-20261019`. Six passages now use curated native on-foot Zeboim encounters; other random encounters are disabled, and the fixed Guardian encounter is preserved. Elly starts at the captured level 52 baseline, and two Emeralda lines receive final voice adjustments. The suite passed (406 tests run, two skips), and the candidate built successfully. Static auditing verifies all 166 replacements, 297 components across 33 fields, 3,556 unchanged unreplaced payloads, and 5,905 Mode 2 sectors. Its rebuilt Perfect Works 0.10.2 foundation has SHA-256 `7585d2ebadab82f9d982d871e05c02a9fb930167e8fe85d249c266a0e1885d8e`; it is explicitly distinct from the unavailable historical `505f4ac0â€¦` source. No Perfect Works 0.11.4 game patch was applied. Automated clean-retail reconstruction passes for the single EXE and portable ZIP. Fresh gameplay and native patcher GUI acceptance remain pending. See [V173 notes](mass-driver-v173.md) and [the staged transcript](mass-driver-dialogue-v173.md).

Earlier September 30 Mass Driver V172: `mass-driver-v172-dialogue-polish` implemented the approved script-fit polish in 13 dialogue blocks across eight files, removed 16 pages, and preserved the Miang memory, its boundaries, and all field scripts. The suite passed (394 tests run, one skip); the final disc and launcher passed verification. All 166 replacement resources matched, with exactly eight field bundles changed from V171 and 158 replacements identical. Native gameplay acceptance remained pending. See [V172 notes](mass-driver-v172.md) and [its installed transcript](mass-driver-dialogue-v172.md).

September 26 Soylent 1.1 / V240: the active standalone release is `soylent-v240-polish-20260926`. Faster production controls keep instructions optional; clinic records remain readable beside a separate status report; an existing physician offers a care-plan conversation after shutdown. The service directory and Ward's Next objective option improve guidance. Sorting material movement stops on committed reentry while Core containment and native music remain intact. One-hit combat and the empty keycard room remain. The suite passed (856 tests, 2 skipped); build and both launcher checks passed. All 36 installed resources match their manifest, with exactly seven field bundles changed and the other 29 identical to V239. Native emulator acceptance remains pending. See the [1.1 polish notes](soylent-system-polish-1.1.md) and [player guide](soylent-system-player-guide.md).

Earlier September 26 Soylent 1.0 / V239: `soylent-v239-final-20260926` added an explicit completion epilogue, shutdown-aware Generation survivors, persistent accepted relay visuals, a written resonance pattern, and a clear decommissioned-shaft notice. The user's chosen one-hit combat remained enabled, and the keycard room remained empty. The suite passed (840 tests, 2 skipped); build and both launcher checks passed. All 36 installed resources matched the manifest, exactly four field bundles changed from V238, and the other 32 resources were identical. Full native gameplay acceptance remained pending. See the [1.0 release notes](soylent-system-final-1.0.md).

Earlier September 26 Soylent V238: `soylent-v238-discoveries-20260926` added explicit relay feedback, a production-clearance report, optional staff memoranda with puzzle clues, and NPC responses to discovery and shutdown across five rooms. One-hit combat and the empty keycard room remained. The suite passed (823 tests, 2 skipped); build and launcher checks passed. All 36 installed replacements were verified, with exactly five field bundles changed and all other resources identical to the preceding release. Full emulator acceptance remained pending. See the [V238 notes](soylent-system-v238.md).

Earlier September 26 Soylent room cleanup: `soylent-v237-keycard-room-20260926` removed the patient and doctor from the field-593 Quarantine-keycard room while retaining its terminal, keycard, stored diagnostic record, bed, and return route. One-hit testing remains enabled. Build and launcher checks passed, as did 805 tests (2 skipped). All 36 installed replacements were verified; only field 593's bundle changed from the preceding one-hit release. A fresh room-entry check remains pending. The user reported acquiring the Quarantine keycard and reaching field 620's east door, which requested three biological relays; the full dungeon run remains unverified. See the [V237 notes](soylent-system-v237.md).

Earlier September 26 testing release: [soylent-v237-one-hit-20260926](soylent-system-one-hit-playtest.md) is the previous verified enemy-HP variant. All 34 prior V237 field/party replacements were unchanged; two enemy archives gave every member of the clinic and Sufal battles 1 HP. That disc and the corrected project-environment launcher passed verification. Those results predate the room cleanup; normal combat acceptance remains pending.

September 25 Soylent release: [V237 completion candidate](soylent-system-v237.md), `soylent-v237-completion-20260925`, restored the Quarantine continuation and added distinct production puzzles, a midpoint save/recovery menu, and deliberate finale interactions. The suite passed (783 tests run, 2 skipped), the disc built and verified, and the user confirmed fresh-start dungeon entry from the Soylent menu using K. A complete emulator playthrough remains unverified. The V236 records below remain historical baseline evidence.

This records the builds that existed **before the shared-workflow update**. It identifies gameplay content by build receipts, full-disc SHA-256 hashes, and replacement payloads. A recently modified folder or a familiar title screen is not sufficient evidence of its contents. These are candidates, not completed gameplay acceptance records.

For the subsequent Rico opening corrections, see [rico-ch2-opening-v2](history/rico/rico-chapter-02-opening-v2.md). Use the root `PLAY_RICO.cmd` and `python project.py status` for the current release; the tables below remain historical baseline evidence.

The active September 6 Rico release is [rico-ch2-bar-transition-v12](rico-ch2-bar-transition-v12.md): Championâ€™s room/bar stair departures and interval reloads preserve the live Rico party, with destination setup retained in room initialization. This addresses the black-screen transition reported during v11 testing; the exact runtime stall remains unconfirmed. The full suite passed (1084 tests run, 7 skipped), and both disc audits passed. V11 dialogue, portraits, music, native geometry and other gameplay remain unchanged. Play Rico opens the verified current media. In-game retest is pending; older builds remain historical evidence.

## Latest gameplay candidates at the audit baseline

| Project | Content revision | Organized launch target | Matching legacy artifact |
|---|---|---|---|
| Mass Driver | **V168** dialogue/clue candidate | [`builds/mass_driver/organized-v1/Xenogears_Reimagined_mass_driver_organized-v1_CD2.cue`](../builds/mass_driver/organized-v1/Xenogears_Reimagined_mass_driver_organized-v1_CD2.cue) | `output/Xenogears_PW_CD2_mass_driver_standalone_v168.bin` is byte-identical to the organized BIN. |
| Soylent System | **V236** | [`builds/soylent_system/organized-v1/Xenogears_Reimagined_soylent_system_organized-v1_CD2.cue`](../builds/soylent_system/organized-v1/Xenogears_Reimagined_soylent_system_organized-v1_CD2.cue) | `output/Xenogears_PW_CD2_mass_driver_surface_soylent_v236.bin` is byte-identical to the organized BIN. |
| Rico | **rico-ch2-v1**, expanded Chapter 2 | [`builds/rico/rico-ch2-v1/Xenogears_Rico_Arc.m3u`](../builds/rico/rico-ch2-v1/Xenogears_Rico_Arc.m3u) | Supersedes `output/rico_arc/` and `builds/rico/organized-v1/`, whose two discs match each other exactly and precede the Chapter 2 expansion. |
| Combined | **rico-ch2-v1**, all three current content revisions above | [`builds/combined/rico-ch2-v1/Xenogears_Reimagined_combined_rico-ch2-v1_CD2.cue`](../builds/combined/rico-ch2-v1/Xenogears_Reimagined_combined_rico-ch2-v1_CD2.cue) | Supersedes `builds/combined/organized-v1/` and the older `output/Xenogears_PW_CD2_reimagined_unified_v1.bin`. **User-reported New Game black screen remains unresolved at this baseline.** |

Mass Driver's fresh start-to-finish acceptance remains pending. Soylent's authored route still ends at the field-620 content boundary; its prepared future rooms do not establish a finished campaign. Rico Chapter 2 has 12 connected fields, 53 scene hooks, and 244 dialogue blocks, with fresh emulator acceptance pending. See the module READMEs and [Chapter 2 release evidence](history/rico/rico-chapter-02-release.md).

## What the combined image actually contains

The `rico-ch2-v1` combined image is a modified anthology image, not an unmodified retail disc. Its receipt records **250 replacements**. Its module snapshots exactly match the corresponding latest standalone receipts:

| Module | Source snapshot SHA-256 |
|---|---|
| Mass Driver | `06e7566e0e39cbabf0f4ba6c431de3a84796c8864ddad17cea1bfd33569970db` |
| Soylent System | `fccd9282a7720efff7b3e1b5dedba510effdf08f1dbfe44ea36a28eda1b7d6dd` |
| Rico | `7547dde7a682df2a93a16289cad72073c4a665d80d2c89088c8b3ea11860238d` |

This audit rehashed every staged replacement in the combined, Mass Driver, and Soylent candidate manifests. All matched their recorded hashes. Cross-profile comparison found:

- **159 Mass Driver payloads** match the latest standalone exactly. The six differing replacements are deliberately composed shared resources: New Game handoff, title/Continue overlay, character profiles, menu/portrait/shop data, item names, and item descriptions/balance. Standalone title graphics ID 1587 are not installed as a replacement in combined.
- **29 Soylent payloads** match the latest standalone exactly. Four differing replacements are those profiles' composed title/menu/character resources; standalone title graphics ID 1587 are not installed as a replacement in combined.
- Against the previous combined `organized-v1`, **218 of 223 existing resources are unchanged**, five Rico resources change, and 27 resources are added for the Chapter 2 work. The five changes are Rico's bedroom, chapter selector description, Chapter 2 main room, and the shared Gear-battle helper in Chapters 5 and 6. All Mass Driver and Soylent owned gameplay payloads remain unchanged.

The [combined manifest](../builds/combined/rico-ch2-v1/stage/manifest.json) explicitly preserves the native **New Game / Continue / Sound** title and original source title graphics, and directs New Game to the anthology selector in field 63. Seeing the original title design alone cannot identify a disc as retail. The black screen is a separate runtime problem; it does not show that the module content is absent.

The [Chapter 2 isolation audit](../work/rico_chapter2_audit/combined_release_isolation.json) reports no violations and preserves the entire Central Control bundle (`67e159ec58689f121a9c4326efdb1b8f6e723595420ebf3ba2386bef8911baeb`). Protected Miang memory blocks 22â€“31 and 36 retain authored SHA-256 `2b0192e5583de560cf50756a9fadd41176dca8b28d9c18930ba43816cb61574b`. The current standalone/combined Mass Driver payload comparison independently agrees with that unchanged bundle.

## Launcher ambiguity found

At this baseline, the repository contained launchers with similar names and different targets:

| Launcher | Actual target at the audit baseline |
|---|---|
| Root `PLAY_XENOGEARS_REIMAGINED.cmd` | `builds/combined/rico-ch2-v1/` |
| `output/PLAY_XENOGEARS_REIMAGINED.cmd` | Old `output/Xenogears_PW_CD2_reimagined_unified_v1.cue` |
| `output/PLAY_MASS_DRIVER_STANDALONE.cmd` | Older Mass Driver **V167** |
| `output/PLAY_MASS_DRIVER_V168.cmd` | Mass Driver **V168** |
| `output/PLAY_SURFACE_SOYLENT_V236.cmd` | Soylent **V236** |

These are historical observations, not instructions to keep using the old targets. Use the current project workflow once the shared-workflow update is installed.

## Diagnostic and external artifacts

`builds/combined/rico-ch2-bootfix-probe/` was built later than the content candidates, but is an **unaccepted diagnostic experiment**. Its manifest differs from `rico-ch2-v1` only in selector resource **732**, with no added resources. It must not become the default merely because its timestamp is newest.

The audit also checked the visible related folders in Desktop, Downloads, and `Xenogears_Reimagined_snapshots`. The Desktop Noah folder contains a retail Disc 2 source. Downloads contains an older Mass Driver package and a newer Perfect Works **0.11.2** donor distribution. The audited project currently pins Perfect Works **0.10.2** discs. A newer donor distribution is not a newer version of this project's authored content, and substituting it requires a compatibility check. Standalone Soylent's declared V166 Mass Driver base is a normalized donor dependency; its resulting gameplay content is V236.

## Full-disc hashes verified during this audit

| Candidate BIN | Bytes | SHA-256 |
|---|---:|---|
| Mass Driver `organized-v1` / legacy V168 | 696144960 | `b72f2fd563dea6252b21899d06f81b91489f15b1ea50728545c049faa65aaebd` |
| Soylent `organized-v1` / legacy V236 | 698816832 | `e228a01d3dac8f491ef96ef5b175b73fb1a2b413e18e03549f2dbd232e562268` |
| Rico `rico-ch2-v1` Disc 1 | 719267472 | `c15d1a85a9203ec96d47197611c0a017b168b867524db2af762aa878b775529a` |
| Rico `rico-ch2-v1` Disc 2 | 696638880 | `ba37b78dec3fbb06e4ba00828ce9dfe5672d45a30d2779d95fce074867e3c2f4` |
| Combined `rico-ch2-v1` Disc 2 | 707568624 | `ff27393fa3370ab4c612d3db92d03b07beb4dc38a4311e61d5fe665c2860bd67` |

Verification here is filesystem, receipt, and payload verification. No emulator was opened or controlled for this inventory audit, and no memory card or save state was changed.
