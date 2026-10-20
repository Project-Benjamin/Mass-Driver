# Rico Chapter 2 — rico-ch2-v1 candidate

The complete chapter route is implemented and built into both standalone Rico discs and the combined Disc 2 candidate. It includes twelve connected fields, 53 scene hooks, 244 dialogue blocks, the Baptism, a playable Stier defense, sewer investigation with Fei and Citan, the native Redrum battle, wound treatment, Finals, title transfer, crash, and Chapter 3 handoff.

Launch [Xenogears Reimagined](../../../PLAY_XENOGEARS_REIMAGINED.cmd), then choose **New Game → Rico's Arc → The Champ**. The standalone [two-disc playlist](../../../builds/rico/rico-ch2-v1/Xenogears_Rico_Arc.m3u) is also available. Start fresh for this candidate: old emulator save states retain the previous field scripts and disc file table.

## Verified

The full suite discovered 950 tests: 944 passed and 6 were skipped. Real-donor integration checks verify the complete preparation path, native door returns, scene movement geometry, actor cleanup, source allocations, and battle resources. The progression model covers 76 reachable states and 205 transitions; every modeled state can finish.

| Output | Payloads checked | EDC/ECC sectors checked |
| --- | ---: | ---: |
| rico Disc 1 | 66 | 4388 |
| rico Disc 2 | 66 | 4388 |
| combined Disc 2 | 250 | 11452 |

All 382 payloads and 20228 sectors match their build records. Source snapshots remain current. The combined disc retains its checked native title boot. All 159 Mass Driver and 29 Soylent replacement payloads remain unchanged, including the protected Miang scene and the entire Central Control bundle.

## Remaining acceptance

An emulator playthrough has not been performed. Visual timing, controller behavior, battle balance, and save/reload behavior need the [runtime checklist](../../../modules/rico/docs/chapter-02-implementation.md). The crash's royal-box destruction and the duct passage use compressed presentation; the Finals use mounted Gear sprites. Play time has not been measured.

The [machine-readable release report](../../rico-chapter-02-release.json), individual build receipts, and [isolation audit](../../../work/rico_chapter2_audit/combined_release_isolation.md) preserve the verification evidence. Older organized-v1 releases remain available.
