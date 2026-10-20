# Storage cleanup â€” September 6, 2026

The cleanup preserves every recorded release in `builds/`, all active sources and donors, all saves and memory cards, and the unfinished Rico V11 work. No gameplay content, protected Miang scene, build configuration, or launcher was edited.

## Storage changes

- Replaced 17 fully SHA-256-matched duplicate disc copies with NTFS hardlinks (11.118 GiB of redundant logical data). Every existing release/output path still works.
- Permanently deleted the unreferenced `work/md168_repeat.bin` repeat-build image (0.648 GiB) and its CUE; the identical image remains in the active Mass Driver release. Its build log and stage evidence remain.
- Relocated 13 historical Rico folders (17.204 GiB of logical data) to F: after verifying every file. Directory junctions preserve their original paths, including migration-test fixtures.
- Deleted 13.22 MiB of Python caches with corresponding source files. Three compiled files without source were preserved; exact paths are in `cleanup-summary.json`.

File sizes are logical sizes. NTFS compression, hardlinks, open file handles, and concurrent builds mean they do not equal the change in drive free space. Use the final drive reading below to assess available space.

## Preserved dependencies

The normalized Soylent V166 donor remains at `output/Xenogears_PW_CD2_mass_driver_standalone_v166.bin`. Other old Mass Driver/Soylent outputs and stages are retained because regression tests use them. Current extracted inputs, `work/xenoiso.exe`, reference artwork, source discs, `.git`, authored content, compatibility tools, and runtime evidence remain. The Flying Weltall2 outputs are also retained.

The `work/raudio` tree and `.pytest_cache` were left untouched because their contents could not all be listed. The three orphaned bytecode files for the old Weltall2 battling UI were also preserved. Permissions were not changed.

## F: locations

F: must remain available for the relocated historical fixtures. These are live linked working paths, so do not delete the F: folder as if it were an extra backup. All relocated files are under:

`F:\Xenogears_Reimagined_Archive\cleanup-2026-09-06_172417\relocated`

| Original workspace path | F: relative path |
|---|---|
| `work/rico_intro_stage` | `relocated/work/rico_intro_stage` |
| `work/rico_arc_dialogue_stage` | `relocated/work/rico_arc_dialogue_stage` |
| `work/rico_sig_stage` | `relocated/work/rico_sig_stage` |
| `work/rico_dad_stage` | `relocated/work/rico_dad_stage` |
| `work/rico_firewood_reply_stage` | `relocated/work/rico_firewood_reply_stage` |
| `work/rico_arc_menu_fix_stage` | `relocated/work/rico_arc_menu_fix_stage` |
| `work/rico_night_cleanup_stage` | `relocated/work/rico_night_cleanup_stage` |
| `work/rico_flower_stage` | `relocated/work/rico_flower_stage` |
| `work/rico_funeral_mercy_stage` | `relocated/work/rico_funeral_mercy_stage` |
| `output/rico_v02` | `relocated/output/rico_v02` |
| `output/rico_arc_herbal_tea` | `relocated/output/rico_arc_herbal_tea` |
| `output/rico_arc_tea_sequence` | `relocated/output/rico_arc_tea_sequence` |
| `output/rico_arc_staged` | `relocated/output/rico_arc_staged` |

## Validation

Before cleanup: `python project.py test all` ran 1,081 tests; OK, 7 skipped.
After cleanup: `python project.py doctor` passed all five configured donor/source hashes. `python project.py status --verify --json` completed, and the full file audit verified 110 retained large-file hashes, 264 save/emulator-file hashes, 17 hardlinks, and 13 junctions with zero failures.
After cleanup: `python project.py test all` ran 1,081 tests in 354.064 seconds; **OK, 7 skipped**, matching the baseline. All 27 valid completed releases were media-verified; no prior release was removed or acquired a cleanup-related error.

All four active profiles were already stale at the initial audit. A separate task rebuilt Rico V11 during cleanup; its new release/activation is independent of these storage changes. The cleanup did not launch the emulator or claim gameplay acceptance.

## Restoration and safe editing

To return a linked folder to C:, first copy its F: target into a new local sibling folder with sufficient space, then compare every file with the corresponding `tree-*.json` SHA-256 manifest. Confirm that the original path is the expected junction, remove only that junction (never recursively delete its target), and rename the verified local copy to the original folder name. Keep the F: copy until `python project.py test all` passes.

Hardlinked disc names share immutable image bytes. The normal build workflow creates a new release or atomically replaces the destination, so it remains compatible. For a custom in-place binary patch, first copy the image to a new filename and patch that independent copy.

## Audit records

The audit directory above contains `inventory-before.json`, `large-file-hashes.json`, `cleanup-plan.json`, `actions.jsonl`, per-folder SHA-256 manifests, protected-save hashes, before/after Git status, project status, doctor output, test output, and `verification-after.json`. The `cleanup.ps1` file is an execution record, not an idempotent maintenance command.

## Final available space

C: had **34.82 GB free** (32.43 GiB) at completion, compared with 5.30 GB at the initial check. F: had **246.65 GB free**. These are measured drive values, and include concurrent activity.
