# Xenogears Reimagined project source companion

This archive contains the canonical project entry point, modules, shared tools, tests, authored dialogue, selected authored images, public configuration templates, compatibility entry points, historical repair source and documentation for the release in release/BUILD_IDENTITY.json. Read docs/source-distribution.md first.

It contains no disc images, extracted game resources, prepared game payloads, patch payloads, executables, emulator, BIOS, memory cards, saves or private configuration. release/EXTERNAL_INPUTS.json identifies the external donor contract, including a captured initial-state fixture. Historical tests require additional excluded fixtures. This source archive alone is not a turnkey build from a clean disc.

The matching portable patcher and Windows player source companions are separate. Copy their tools/mass_driver_portable and tools/mass_driver_standalone directories into this project's tools directory. Their release metadata belongs alongside each companion; do not overwrite this project's release metadata. Dependency source and compiler requirements are documented in each companion. The player installer is also a separate artifact.

Preserve upstream notices. The included Perfect Works license/provenance does not grant rights to the underlying Xenogears game. Development reference screenshots are excluded; the workstation's complete source-tree fingerprint is not claimed for this reduced source package. Runtime and clean-install acceptance remain separate release requirements.
