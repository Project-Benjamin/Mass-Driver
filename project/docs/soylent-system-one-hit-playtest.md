# Soylent one-hit playtest — September 26, 2026

The current standalone release is `soylent-v240-polish-20260926`; see the [1.1 release notes](soylent-system-polish-1.1.md). The user explicitly chose to retain one-hit kills. Both enemy archives remain byte-identical to the testing releases below, and the Quarantine keycard room remains empty.

This option originated as a testing variant of the V237 completion candidate. The source-tracked `modules/soylent_system/content/playtest.json` enables one-hit kills for the standalone build. Enemy HP is reduced to 1 for the clinic security team and every member of the Sufal encounter, including its supporting enemies. A damaging hit defeats its target; misses and non-damaging actions retain native behavior.

The setting changes enemy data loaded from the disc. It does not edit character stats, saved progression, memory cards, or savestates. The one-hit option preserves field scripts, native battle-result handling, rewards, party resources, and the eighteen-room route. The normalized V166 donor is read-only.

The preceding release, `soylent-v237-keycard-room-20260926`, kept this setting enabled and separately removed the patient and doctor from field 593. The Quarantine keycard and terminal remain available, including the stored diagnostic record after pickup. Build and launcher verification passed, along with **805 tests (2 skipped)**. The [installed-payload audit](../work/soylent_v237_keycard_room_payload_audit.json) verified all 36 replacements: only field 593's bundle changed from the preceding one-hit release. A fresh room-entry check remains pending.

The user has reported acquiring the Quarantine keycard and reaching field 620's east door, which requested three biological relays. The full progression run and normal combat acceptance remain pending.

Use the root `PLAY_SOYLENT_SYSTEM.cmd` after the selected release is activated. Close the currently running game and launch the new release before testing. New battles read the patched enemy data from this disc, including after loading native memory-card progress. A savestate captured during battle can retain its old loaded enemies.

To restore normal combat, set `one_hit_kills` to `false` in the options file and rebuild through `project.py build soylent_system --release <new-name> --activate` using the project Python environment. Direct builder calls also accept `--no-one-hit-kills`. The library API defaults to normal combat, and combined builds do not inherit this standalone testing setting.

This option remains selected for the final release. It does not establish acceptance of normal combat balance.

## Previous verified release

For `soylent-v237-one-hit-20260926`, build and launcher identity checks passed. The output-disc audit verified all 36 installed replacements: the previous 34 V237 payloads remain byte-identical, and the only two additions are enemy-data replacements 2684 and 2706. These results predate the field-593 room cleanup. The [audit report](../work/soylent_v237_one_hit_payload_audit.json) records each patched HP field and its original value. No emulator controls or saved games were changed for this build.

`project.py test soylent_system` completed with **798 tests run, 2 skipped, no failures**. The six enemy-data tests verify the active HP pools for all nine enemy instances and byte preservation outside those pools. Nine integration tests cover configuration, normal-combat defaults, CLI overrides, replacement collision protection, and manifest emission. Full output is in `work/soylent_v237_one_hit_tests.log`. Runtime combat confirmation is still pending the user playtest.
