# Restoration verification â€” September 7, 2026

The patcher's existing **Bug fixes** option now composes these original-content
corrections on both USA retail discs:

- Mahanon's first Deus fight: mark the HP-halving move to skip the problematic
  camera sequence. Damage, enemy statistics, rewards and ordinary camera
  commands retain their behavior. The patch uses one declared transient byte
  in existing battle-overlay alignment padding; it is consumed/reset and never saved.
- Hob-Meat and Hob-Steak: menu and shop descriptions now say **100 HP** and
  **150 HP**, matching their actual non-battle recovery.
- Bulimy Seed/Fruit: gain items cannot lower already-above-cap body weight or
  overflow it. All four menu copies are corrected. Existing below-cap amounts,
  weight-loss items and save format are retained.
- Existing Def Up, Charger multiplier and Gear-shop Ether-amplifier corrections
  remain installed and pass native CPU regression checks.

The minimal patcher layout is unchanged. Yellow-name selection is retained in
the active candidate; double XP and no encounters remain independently optional.

## Evidence and limits

Source/CPU checks reproduce the original defects and exercise the corrections.
The Deus tests cover marked-command suppression, normal camera dispatch and
state, flag consumption/reset, and R3000 load-use spacing. Camera callees are
stubbed in the dispatch comparison; this does not render the attack or emulate
the whole PlayStation. The three older fixes pass 512 built-disc native block
cases across the pair, with corresponding retail defects reproduced.

The item audit inventories 1,180 item/equipment rows, 176 character ability
slots and 779 Gear action rows per disc, including duplicates and empty slots.
It executes 36 recovery and 150 battle-availability cases per disc. Only the
documented description corrections are semantically certified by those cases.

Weight checks cover consumables, display conversion, save-buffer copies,
Gear accessory load penalties and the battle agility/ATB consumers. They do
not prove actual card I/O or every food event. An original body-weight combat
formula has not been established, so no new balance curve is installed.

**Not a whole-game bug certification.** Billy ammunition, broader status
behavior and all remaining spell/item semantics still require work. Actual
Deus battle playback, New Game/Continue, menus, real save/load, disc change and
the full campaign remain gameplay-untested. A normal pre-Mahanon-Deus save is
needed for the targeted emulator regression.

Detailed evidence: [Deus](deus-fix-verification.md),
[items/spells](item-spell-verification.md), [weight](weight-verification.md),
[remaining known bugs](remaining-bug-verification.md).

## Installed release

Active/current release: [deus-restoration-v2](../../builds/definitive/deus-restoration-v2/Xenogears_Definitive.m3u).
Use [PATCH_XENOGEARS_DEFINITIVE.cmd](../../PATCH_XENOGEARS_DEFINITIVE.cmd) to
build another option selection, or [PLAY_DEFINITIVE.cmd](../../PLAY_DEFINITIVE.cmd)
to launch this checked release.

- Full profile suite: **287 tests run, one skipped; passed**.
- Both discs: all 3,710 ordinary resources plus native directory/FAT/boot tables
  verified. Original raw sectors of all 17 Disc 1 and 12 Disc 2 movies match.
- Independent regeneration confirms all eight restoration resources per disc
  match the installed media exactly, including the Deus overlay and script flag.
- Actual-disc CPU checks pass for the older fixes, corrected food descriptions
  and native weight paths. The gain-cap regression is explicitly absent, and
  all four menu copies agree.
- `status definitive --verify` reports current. `play --check-only` verifies the
  paired-disc launch identity without opening the emulator.

The CPU audits name `deus-restoration-v1`. The final `deus-restoration-v2` changes only an optional
audit-test dependency guard; both complete BIN hashes match the audited v1
images. The [verification record](restoration-verification.json) asserts those
identities and links the exact reports. No CPU result is relabeled as a gameplay pass.

| Media | SHA-256 |
| --- | --- |
| Disc 1 | `f0276e623432d2eaf71123754fe5c58ea70ab568f20dbc2091de83be1bce963c` |
| Disc 2 | `cb01f4d5cf72681ae1f7f9c2898ce03122b90eff13102aef060f53f1345f6a9d` |

[Build receipt](../../builds/definitive/deus-restoration-v2/project-build.json),
[installed-byte audit](../../output/definitive/verification/deus-restoration-v2-installed.json),
[test log](../../output/definitive/verification/deus-restoration-v2-tests.log).

