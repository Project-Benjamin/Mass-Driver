# Rico Chapter 2 opening corrections

The corrected candidate is **rico-ch2-opening-v2**, built from the current
shared toolchain on September 5, 2026. Open the root [PLAY_RICO.cmd](../../../PLAY_RICO.cmd),
start **New Game**, and choose **The Champ**. The launcher resolves the paired
Disc 1/Disc 2 playlist through the active release registry. Both `rico` and
`combined` explicitly select this release; Mass Driver and Soylent remain on
their current `workspace-v1` images.

## Corrected sequence

- Chapter select and the Chapter 1 handoff enter the infirmary directly,
  removing the visible sitting-room/infirmary/sitting-room bounce.
- Chapter 2 field transitions lock input and finish a native fade before
  removing or reloading party members. The outgoing room no longer exposes
  Rico disappearing and Fei being registered at its entry position.
- The reception locks input during initialization and gives Fei no player
  update. It stages a single fall and the existing delivery dialogue, then
  transfers to Rico's room once.
- Fei occupies the donor's verified floor position instead of the bed/platform
  edge. A fixed camera from the original infirmary scene is installed under
  black before the cutaway is revealed. It stays fixed through the closing fade.
- Completed delivery does not replay. Native saves already in Rico's room stay
  there; the optional bedroom return retains its original route and progress.

The dialogue, later chapter objectives, and scene knowledge boundaries are
unchanged. The change reuses the existing actors, animation, graphics, and
allocated fields.

## Validation

The canonical command `python project.py test rico` passed: **975 tests run,
7 skipped, zero failures or errors**, in 261.931 seconds. See the
[test log](../../../work/rico_opening_v2_tests.log) and
[result](../../../work/rico_opening_v2_tests_result.json). Regression checks exercise
the compiled opening on both discs, fade and control ordering, chapter launch
targets, persistent progress flags, camera bytes, connected ground positions,
and scene instruction coverage.

Both standalone discs and the combined candidate were rebuilt through
`project.py`. Each receipt records the current module sources and shared tools.
The [disc audit](../../../work/rico_opening_v2_audit.json) **passed with zero violations**:
all 382 staged replacements match their final disc payloads. The combined image
changes 12 Rico-owned replacements; 198 non-Rico replacements, all 12 movies,
and 3,472 unstaged payloads remain unchanged. Its executable differs only in 10
authenticated file-table size bytes corresponding to changed Rico resources.
The protected Miang bundle and authored memory dialogue retain their original
hashes. Receipt freshness, complete output hashes, and playlist order also pass.

A launch check used the exact new Rico playlist and configured installed
DuckStation. The game booted to its native title/attract sequence, but automated
controller input did not reach chapter select. **The corrected opening has not
been visually accepted in the emulator.** Test saves used a separate directory;
the diagnostic session closed without a resume save and original emulator
settings were restored byte-for-byte.

For a meaningful opening test, use New Game and chapter select. Emulator save
states retain their old resident scripts; swapping discs beneath an old state
does not test the new opening. Native memory-card saves and existing emulator
states were preserved.

The combined selector's earlier New Game black-screen report remains a
separate known issue. This Rico correction does not claim to resolve it.
