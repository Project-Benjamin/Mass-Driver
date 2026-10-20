# Mass Driver portable patcher source

This archive contains the portable Windows patcher's source, build and verification scripts, release-input preparation script, and dependency notices/provenance. It contains no game data.

Keep the tools/mass_driver_portable path when combining this archive with the matching full Mass Driver project-source companion. prepare_release.py imports the project's canonical shared.tools.xgdisc; that shared code and the game builder belong to the full project companion.

The GUI builder can also be used on its own with explicit input paths. Follow tools/mass_driver_portable/BUILDING.md. Obtain the exact clean pinned xdelta source and the official portable compiler described in DEPENDENCY_PROVENANCE.json. No machine-wide compiler installation is needed for the llvm-mingw path.

tools/mass_driver_portable/build_manifest.json is a historical V161 payload template. Its old output hashes do not describe a new release. Use a newly prepared release manifest; when supplied, the matching one is at release/portable-build-manifest.json.

The player patch EXE/ZIP and matching full project source are separate companion artifacts. This archive alone does not claim to be the full corresponding source of the game mod, nor does source availability establish gameplay acceptance. Preserve dependency notices.
