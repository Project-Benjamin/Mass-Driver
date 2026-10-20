# Project consolidation validation

The three chapters now share one registry, source configuration, common tool layer, and build layout. Their authored content and chapter builders remain independent modules. The combined Disc 2 was rebuilt from the current sources of all three chapters.

Open [the combined launcher](../PLAY_XENOGEARS_REIMAGINED.cmd), choose New Game, and select a chapter. This is a structurally verified candidate; fresh gameplay acceptance remains pending.

## Verified results

- All four CLI build profiles succeeded under `builds/<profile>/organized-v1/` and record their source, dependency, native Xenoiso, and extracted-input identities in `project-build.json`.
- All **499** prepared replacement payloads match the pre-consolidation baseline byte for byte. Each corresponding payload was then extracted from its finished disc and checked again.
- All **21,319** sectors occupied by those replacements have valid Mode 2 Form 1 EDC/ECC. The Mass Driver, Soylent, and combined native Disc 2 title-boot checks pass.
- The complete Mass Driver image is byte-for-byte identical to V168. The protected Miang memory hash is unchanged. The generated Mass Driver manifest changes only the 33 dialogue source paths.
- 79 authored-content/asset files are byte-identical to the source snapshot. The only remaining content-tree edits update archive/donor path references in two planning/metadata files. The original README is preserved exactly in `archive/README_before_consolidation.md`.
- **906 tests passed**, with **6 skipped** (912 discovered). All 89 legacy tool aliases resolve to their canonical implementations; 17 command-line entry points pass `--help` from outside the project folder.
- Existing release artifacts remain in `output/`; replaced consolidation attempts are retained as dated build folders. No emulator playthrough or live-save repair was performed.

| Profile / image | Bytes | Replacement payloads checked | Sectors checked |
|---|---:|---:|---:|
| mass_driver / Disc 2 | 696,144,960 | 166 | 5,877 |
| soylent_system / Disc 2 | 698,816,832 | 34 | 1,640 |
| rico / Disc 1 | 719,175,744 | 38 | 2,245 |
| rico / Disc 2 | 692,205,360 | 38 | 2,245 |
| combined / Disc 2 | 703,135,104 | 223 | 9,312 |

## Disc SHA-256 identities

- `mass_driver` Disc 2: `b72f2fd563dea6252b21899d06f81b91489f15b1ea50728545c049faa65aaebd`
- `soylent_system` Disc 2: `e228a01d3dac8f491ef96ef5b175b73fb1a2b413e18e03549f2dbd232e562268`
- `rico` Disc 1: `39e48aacfbc98422d30cb3c1c08cb2383b2de062a15a52eae27a9103099d1fd8`
- `rico` Disc 2: `0dc39d87f0520b2309dda46df30e6284e8d2a097cd4b3d7064a6d3583810693b`
- `combined` Disc 2: `4b9a056d64c847d2c0b5ce66651f65f1e31a62ffc183b4c5612bfaec246dd907`

The [machine-readable validation record](project-consolidation-validation.json) includes full paths, hashes, test totals, and the protected-scene digest. The local baseline and detailed logs remain under `work/consolidation_*`.

## Build and compatibility behavior

Use `python project.py list`, `python project.py doctor`, and `python project.py build <profile> --release <name>` from the project root. A named release is protected from replacement unless `--force` is supplied; the registry retains the previous folder when replacing one. The shared Xenoiso wrapper uses short temporary aliases to support deeper paths and checks process failure before publishing a disc.

Use `python project.py new-module <slug> --title "Chapter title"` to create the next module in the same structure. Scaffolds start disabled; implement the builder and its registry adapter, declare resources and state ownership, and validate it before adding a playable profile or menu route.

Standalone Soylent retains its verified V166 normalized Mass Driver base dependency. The [shared resource/state ledger](../shared/resources.json) documents combined-resource merges, the `0x03FA` bit partition, and the contextual `0x03EE` resets. Chapter selection does not establish continuous save progression across all projects.

## Remaining acceptance

Play the combined selector and each intended chapter route on this candidate, including save/reload, chapter re-entry, inventory, and return behavior. Follow the [Mass Driver finishing status](../modules/mass_driver/docs/finishing-status.md) for its remaining dialogue pass and start-to-finish acceptance. Soylent's current field-620 boundary and other module completion limits remain as documented in their module READMEs.
