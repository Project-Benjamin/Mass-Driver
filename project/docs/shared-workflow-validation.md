# Shared workflow validation - workspace-v1

All four profiles were rebuilt successfully from the same shared source and toolchain snapshot on September 5, 2026. The resulting gameplay content remains **Mass Driver V168**, **Soylent V236**, and **Rico rico-ch2-v1**.

**Full-suite result: passed.** 967 tests ran in 293.803 seconds; 7 were skipped. Process exit code was zero. The [log](../work/shared_workflow_tests.log) records the final run after correcting the historical V167 launcher assertion.

**Activation and final launch checks: passed.** All four profiles explicitly select `workspace-v1` in [builds/current.json](../builds/current.json). Their current source/tool/input identities, finished media, and CUE/M3U references were checked. Each `play --check-only` check passed; the emulator was not opened. Gameplay status remains `untested` for the standalones and `known-issue` for combined.

## Payload verification passed

The [audit script](../work/audit_workspace_v1.py) freshly hashed all five finished BINs, compared their receipts and gameplay baselines, and extracted and verified **582 replacement payloads** against both manifests and staged files. It found **zero violations**. All **75 content files** remain unchanged: 57 Mass Driver, 2 Soylent, and 16 Rico.

- Mass Driver's complete image is byte-identical to the organized V168 image, which also matches legacy `output/` V168.
- Soylent's complete image is byte-identical to the organized V236 image, which also matches legacy `output/` V236.
- Both Rico images are byte-identical to the expanded `rico-ch2-v1` images.
- Combined is byte-identical to the previously prepared `rico-ch2-bootfix-probe` image. Relative to `rico-ch2-v1`, **249 of 250 resources are unchanged**. Only shared selector resource **732** changes. Every Mass Driver, Soylent, Rico, and composed module-owned gameplay payload remains unchanged.

The complete Mass Driver Central Control bundle retains SHA-256 `67e159ec58689f121a9c4326efdb1b8f6e723595420ebf3ba2386bef8911baeb`. Protected Miang dialogue blocks 22-31 and 36 retain authored SHA-256 `2b0192e5583de560cf50756a9fadd41176dca8b28d9c18930ba43816cb61574b`.

The selector change corrects a premature route stop. **The reported New Game black screen remains unresolved and was not retested in an emulator during this workflow update.** Matching the diagnostic image is a precise description of its bytes, not gameplay acceptance of that experiment.

## Common toolchain

All four build receipts record exactly the same toolchain snapshot:

- Toolchain SHA-256: `112839ea5f198513ad1d81f84fc8c6fe77721e5e5b87ff82dde16aa1b376f475`
- Shared source/configuration SHA-256: `961e5ce886ded8cc622907926b733d83dff180e6fc69fe0f48237f4f796fef91`
- CPython **3.14.5**, Pillow **12.3.0**, NumPy **2.5.1**.
- Twenty canonical shared tool source files, plus recorded executable identities for the configured Xenoiso and DuckStation.

These are the installed tools actually used and recorded locally. This update does not claim that external packages or donor distributions were upgraded or checked against internet releases. Compatible tools and source discs remain explicit dependencies. The [development workflow](development-workflow.md) makes subsequent builds and normal launches check the current workspace identities.

## Finished images

| Image | Bytes | SHA-256 | Replacements verified |
|---|---:|---|---:|
| [mass_driver Disc 2](../builds/mass_driver/workspace-v1/Xenogears_Reimagined_mass_driver_workspace-v1_CD2.bin) | 696144960 | `b72f2fd563dea6252b21899d06f81b91489f15b1ea50728545c049faa65aaebd` | 166 |
| [soylent_system Disc 2](../builds/soylent_system/workspace-v1/Xenogears_Reimagined_soylent_system_workspace-v1_CD2.bin) | 698816832 | `e228a01d3dac8f491ef96ef5b175b73fb1a2b413e18e03549f2dbd232e562268` | 34 |
| [rico Disc 1](../builds/rico/workspace-v1/Xenogears_Rico_Arc_Disc_1.bin) | 719267472 | `c15d1a85a9203ec96d47197611c0a017b168b867524db2af762aa878b775529a` | 66 |
| [rico Disc 2](../builds/rico/workspace-v1/Xenogears_Rico_Arc_Disc_2.bin) | 696638880 | `ba37b78dec3fbb06e4ba00828ce9dfe5672d45a30d2779d95fce074867e3c2f4` | 66 |
| [combined Disc 2](../builds/combined/workspace-v1/Xenogears_Reimagined_combined_workspace-v1_CD2.bin) | 707568624 | `386f168d3d344998e9e8ec5b045eb07d4f4f79f4eed437bad8d134fdbe8b169c` | 250 |

Rico's launch target is its [paired playlist](../builds/rico/workspace-v1/Xenogears_Rico_Arc.m3u). The other profiles use their corresponding CUE descriptors; normal launch uses the active release registry through the root launchers.

The [machine-readable validation record](shared-workflow-validation.json) includes complete disc identities, shared toolchain details, and the final successful suite and activation records. The underlying [payload evidence](../work/workspace_v1_payload_audit.json) records all preservation checks. This audit did not open an emulator or modify memory cards or save states.
