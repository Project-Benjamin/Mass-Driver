# Rico: Emotion and Resolve

Rico's module contains seven authored chapters and an in-field chapter selector. Its standalone builder produces retail-based Disc 1 and Disc 2 images with their own field allocations; the generated playlist is the paired launch target. The combined profile places the anthology behind the unified Disc 2 content selector.

```powershell
python project.py build rico --release my-next-rico-build --activate
```

The standalone profile requires verified **retail Disc 1 and Disc 2** sources. Those inputs are distinct from the Perfect Works donors used elsewhere. The project adapter uses `stage/` for organized replacements; direct legacy calls retain their `prepared/` default.

To play the active release, open the root `PLAY_RICO.cmd`. Start New Game and choose **The Champ**. The current Chapter 2 source contains six unseen Rico interludes written as spoken dialogue, with brief time/location captions between intervals. Inspect the bout card or bed and choose Continue to advance. Emulator save states preserve old resident scripts and objective masks, so enter through the selector to test this format.

- [Builder](build.py) and [chapter manifest](content/manifest.json)
- [Chapter content and assets](content/), [module tools](tools/), and [tests](tests/)
- [Chapter 1 routed screenplay](docs/rico-chapter-01-mothers-promise-screenplay.md)
- [Current Chapter 2 interludes and campaign boundaries](docs/chapter-02-interludes.md)
- [Historical Chapter 2 expansion](docs/chapter-02-implementation.md)
- [Shared resource/state ledger](../../shared/resources.json)

Chapter entry establishes a specific party and chapter state. Young Rico also has a restricted inventory presentation and an explicit restoration path. These entry/exit behaviors need cross-profile save and inventory checks before treating chapters as a continuous campaign.

`tools/build_rico_arc.py` remains an import/CLI compatibility entry point. Exact-state repair scripts are retained in [the repair archive](../../archive/repairs/rico/) and continue to require their audited captures and media.
