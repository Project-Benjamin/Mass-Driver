# Directory organization — September 16, 2026

The project root now serves as the entry point, with artwork under `assets/`, older documentation under `docs/history/`, and development captures under `work/captures/`. The [project README](../README.md) and [documentation index](README.md) explain where to work.

## What moved

| Material | New location | Verification |
|---|---|---|
| 105 artwork, portrait, and audio files | `assets/mass_driver/`, `assets/definitive/portraits/`, `assets/reference/audio/` | All sizes and SHA-256 hashes preserved |
| 99 earlier release notes/transcripts | `docs/history/mass-driver/` and `docs/history/rico/` | Historical prose preserved; only link destinations adjusted |
| 99 loose screenshots and renders | `work/captures/legacy-2026-09-16/` | All sizes and SHA-256 hashes preserved |
| Original 11-file modding starter kit | `archive/xenogears_modding_starter/` | File hashes verified during move; its README workflow link rebased afterward |
| Old pytest cache and empty screenshot folder | `work/organization_20260916/` | Preserved by recoverable moves |

Top-level entries decreased from **40 to 32**. The documentation root decreased from **176 to 79 files**, including the new index and this report. Fixed-path historical notes remain directly under `docs/`; the history indexes include them too.

The root README now points to V169 and the chapter guides. Asset source references were updated in the Mass Driver builder/tests and Definitive portrait tool. No dialogue, scene logic, geometry, graphics bytes, combat data, or state behavior changed.

Saves, memory cards, original discs, historical releases, native tooling, the pinned Soylent V166 donor, and required extracted inputs remain intact. The two referenced loose work PNGs retain their original paths. No project files were permanently deleted.

## Verification

- `project.py doctor` passed all five source/donor hashes and project checks.
- `project.py test mass_driver`: **384 tests**, zero failures/errors, **2 skips**.
- `project.py test definitive`: **287 tests**, zero failures/errors, **14 conditional skips**. These suites share some common tests; their totals are not distinct-test counts.
- Definitive's seven portrait-pack tests passed, and all 91 portrait metadata entries resolve. The existing `xxhash` runtime dependency was installed in the local `.venv` to run those tests.
- The organization audit verified all **105 moved asset files** and **99 capture files** against their pre-move hashes. All 99 missing original text-file paths are accounted for in the document relocation journal.
- The documentation pass rebased **399 Markdown destinations**. All 192 new index links resolved, all previously valid rewritten links stayed valid, and all 51 literal Mass Driver metadata/test document paths remained available. New cleanup/index links were checked afterward.
- The full Mass Driver build completed as **`mass-driver-v169-organized`** and was selected for the root launcher. The complete **696,144,960-byte BIN is byte-identical** to `mass-driver-research-v169`.
- All **166 replacement payloads** are unchanged. The final disc audit passed source/input/output identities, 33 dialogue files, 297 unpacked field components, native boot identity, and EDC/ECC checks for **5,896 sectors**.
- `project.py play mass_driver --check-only` verified the selected media. It did not launch the emulator; gameplay acceptance remains pending.

The unchanged BIN SHA-256 is:

```text
9987579ac994758bb345a354a534f10a36b3934c349fe40d6a78db3f0a933001
```

[Selected build receipt](../builds/mass_driver/mass-driver-v169-organized/project-build.json) · [CUE](../builds/mass_driver/mass-driver-v169-organized/Xenogears_Reimagined_mass_driver_mass-driver-v169-organized_CD2.cue) · [regenerated V169 transcript](mass-driver-dialogue-v169.md)

## Move records and recovery

The cleanup records are grouped under [work/organization_20260916](../work/organization_20260916/):

- [Asset moves](../work/organization_20260916/asset-moves.json), [document moves and link rewrites](../work/organization_20260916/document-moves.json), [capture moves](../work/organization_20260916/capture-moves.json), and [legacy folder moves](../work/organization_20260916/folder-moves.json).
- [Text-source backups](../work/organization_20260916/before/) and [original hashes](../work/organization_20260916/source_before.json).
- [Game-content identity comparison](../work/organization_20260916/content-identity.json), [disc audit](../work/organization_20260916/disc-audit.json), and [file verification](../work/organization_20260916/final-file-verification.json).
- [Mass Driver tests](../work/organization_20260916/tests-mass-driver.log), [Definitive tests](../work/organization_20260916/tests-definitive.log), [doctor](../work/organization_20260916/doctor.log), and [launcher check](../work/organization_20260916/launch-check.log).

Each move journal identifies its original and current location. Restore a moved asset together with its corresponding source-path edits when reverting organization. Historical release receipts were not rewritten; a new receipt records the organized source layout. Other profiles' pre-existing relocation/receipt issues were outside this cleanup.
