# Shared tools and composition

The shared layer contains generic Xenogears codecs, checked ATEL operands and variable operations, the project registry, and the combined Disc 2 builder. Chapter-specific scenes and mechanics belong in their modules.

Every profile uses this same current implementation. Run `python project.py tools`
to inspect the local toolchain and `python project.py status` to compare active
builds against it. Normal launch goes through `python project.py play <profile>`;
it verifies the receipt and media before opening the configured emulator. See
the [common development workflow](../docs/development-workflow.md).

[project.json](../project.json) selects profiles and source variants. [resources.json](resources.json) records shared resources, field allocations, persistent-state ownership, and entry/reset policies. The combined builder merges global records instead of allowing an arbitrary module to replace another module's complete global file.

Current composition includes Video Disk and Rico equipment records, the young-Rico menu portrait, shared title/party data, and reviewed battle-resource ownership. Canonical IDs 47 and 2614 use the Mass Driver normal-combat versions in the combined profile; Rico's independent build retains its own preparation contract.

## Source setup

Create a local `project.local.json` at the repository root. Source values can be paths or objects containing a path and a pinned SHA-256. For example, replace these example paths with your verified inputs:

```json
{
  "sources": {
    "pw_disc1": {"path": "C:/XenogearsSources/PerfectWorks_Disc_1.bin"},
    "pw_disc2": {"path": "C:/XenogearsSources/PerfectWorks_Disc_2.bin"},
    "retail_disc1": {"path": "C:/XenogearsSources/Retail_Disc_1.bin"},
    "retail_disc2": {"path": "C:/XenogearsSources/Retail_Disc_2.bin"},
    "mass_driver_base": {"path": "output/Xenogears_PW_CD2_mass_driver_standalone_v166.bin"}
  },
  "tools": {"xenoiso": "C:/XenogearsTools/xenoiso.exe", "input_root": "work", "duckstation": "C:/XenogearsTools/DuckStation/duckstation-qt-x64-ReleaseLTCG.exe"}
}
```

Use `python project.py doctor` to inspect configuration, file identities, and registry consistency. Existing extracted donor files in `work/` remain audited inputs; the organized build receipts record the files actually read. A source's variant and hash matter as well as its path.

## State and saves

Mass Driver and Surface Soylent share persistent word `0x03FA` through assigned bit ranges. Surface Soylent's appointment data and Rico's Hammer state both use `0x03EE`; Rico chapter/hub entry has explicit resets. The ledger must retain those ownership and lifetime rules when future modules are added.

Selecting Mass Driver currently clears all of `0x03FA`, along with its lift and interlock words. Selecting Soylent clears its bits 4–15 while retaining the low four Mass Driver bits, and resets the appointment word. These are chapter-entry rules; they do not preserve simultaneous progress in every chapter.

Chapter selection, chapter restart, and chapter resume are different operations. Verify their intended party, inventory, Gear, and persistent-state behavior in each profile. A save-state repair script pinned to one capture and disc is historical repair evidence, not a general save conversion system.

## Compatibility and checks

The old `tools.*` modules resolve to the canonical implementation, preserving private symbols and patches. Legacy `tests/` wrappers retain their own file locations for unittest discovery while exposing canonical test classes and helper functions.

Current module tests live under `modules/<chapter>/tests/`; generic codec tests live under [shared/tests](tests/). Byte comparisons against pre-consolidation outputs establish whether organization changed game payloads. Fresh gameplay runs establish chapter acceptance.

`python project.py test <profile>` includes shared checks and tests for the
profile's transitive implementation dependencies. `build ... --activate` records
the current Python/package/native-tool identities and selects the new release
only after its full build and media validation succeed. Source and tool changes
make earlier builds stale. `builds/current.json` is the explicit per-profile
selection; build timestamps do not change it.

See [scripting and scene planning](../docs/xenogears-scripting-and-scene-planning.md) for the broader engineering approach.
