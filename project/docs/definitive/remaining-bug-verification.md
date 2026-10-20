# Known-bug verification of foundation-ui-v2

This is the historical baseline audit. The subsequent Deus correction is
documented in [deus-fix-verification.md](deus-fix-verification.md), and its
installed release in [restoration-release.md](restoration-release.md).

Audit date: 2026-09-07. **The claim that all bugs have been fixed is false for
the inspected build.** The two game images contain the three implemented
corrections, but retain the original code at the inspected Deus camera-freeze
and Billy elemental-ammunition sites. Gameplay has not been tested.

This audit reads the actual released images, not just the builder's intended
patch list. It does not change game images, saves, memory cards, or emulator
configuration.

| Image | SHA-256 |
| --- | --- |
| `foundation-ui-v2/Xenogears_Definitive_CD1.bin` | `6d59e4444be32da45ecbe1327ba689d3b39f1d03a290d33c4ba5b850c48a2dbb` |
| `foundation-ui-v2/Xenogears_Definitive_CD2.bin` | `d631cd78340630bbeaf8ff805b2ceab4b333a78ca6a44a6cbbac15cc415ebe9d` |

The machine-readable receipts are
`output/definitive/bug-audit/foundation-ui-v2-cd1.json` and `...-cd2.json`.
They include resource and probe hashes. Source comparison uses the configured
USA retail discs, with Disc 2 canonical resource IDs mapped to physical ID
minus five.

## Results

| Case | Binary result in both discs | Remaining evidence |
| --- | --- | --- |
| Gear Charger multiplier | Corrected instruction is present at decoded 38:`0x2A894`. | In-game recovery/capping cases. |
| Def Up mask | Corrected instruction is present at decoded 38:`0x27C28`. | Actual status application, target, blocking, and expiration cases. |
| Gear-shop Ether amplifier clearing | NOP is present at 2602:`0x11428`. | Equip/shop/battle/save-load sequence. |
| Deus HP-halving side-angle freeze | All three inspected overlay blocks and affected enemy-script flag remain retail. | Isolated repair, scratch-state ownership, and camera/attack playback. |
| Billy elemental Ether ammo | Both inspected overlay ranges remain retail. | Safe repair and changes between every available ammunition element. |
| Bracer / Wither / Weaken | Shared effect and duration ranges inspected here remain retail. | Recover each original effect and compare actual application; the Def Up mask alone cannot certify them. |
| Ether Veiler and other item/spell cases | No passing behavior evidence established by this audit. | Individual descriptions, execution, targets, stacking, immunity, duration and cap checks. |

An unchanged site establishes that the inspected correction is absent. An
arbitrary different byte does not establish a fix: the auditor reports
`modified_requires_validation` in that case. It always records its bounded
coverage and never issues an “all bugs fixed” certificate.

## Deus: isolated source changes, not installed

The author's [Deus correction commit](https://github.com/PWBuild-Team/Perfect_Works_Build/commit/c054f82f8e8dab8c6ad5106ed270d301d586aa54)
provides an unusually narrow comparison against retail:

- Decoded resource 38: 158 differing bytes within complete instruction
  ranges `[0xAD64,0xAD78)`, `[0x3D0E0,0x3D0EC)`, and
  `[0x3E104,0x3E1A4)`.
- Resource 2746: exactly one byte, `0xC25`, changes from `00` to `01`.
- No enemy stats, rewards, or HP are altered by that one-byte script change.

Local MIPS inspection shows the first block records byte 3 of the script
command in address `0x800C2048`. A reset clears that state. A guard consumes
and clears it before the existing camera routine, bypassing that routine for
the marked command. The ordinary camera path is relocated in place, with
redundant address-loading instructions removed to recover space.

This is a concrete candidate, not an installed fix. The transient scratch
byte's complete lifetime and all consumers require independent verification;
the camera animation and battle-script interaction also need actual gameplay.
The current build has the retail `00` at 2746:`0xC25` and none of the three
overlay changes.

## Billy: corrected dependency analysis

The [Billy ammunition commit](https://github.com/PWBuild-Team/Perfect_Works_Build/commit/7a9f6e74826c623e028793194a5017a71d320a8b)
renames `deus_fix` to `bug_fix`. **Resource 2746 is unchanged by this commit.**
Its SHA-256 before and after is
`86c439808a674c7a3a507fa675ee9ea8fb92631ec18ed3b0ea8513798d17ddc7`.
The 2746 change belongs to Deus and is not a Billy-ammunition dependency.
The earlier mechanics queue's warning based on two changed paths was too
broad; rename-aware byte comparison resolves that uncertainty.

The meaningful decoded Billy overlay delta is 505 bytes. The original
`0x248A0` path reads the element from a cached attack entry, while the new
routine retrieves the current equipped-ammunition byte and then the item's
element. The new routine occupies space obtained by compacting repeated
initialization instructions around `0x2B748`.

Copying that old patch would introduce an avoidable implementation concern:
at `0x2B884` its `LW at` is consumed by the immediately following `ADDU`.
The R3000 load delay needs attention. The newer
[9759174 source revision](https://github.com/PWBuild-Team/Perfect_Works_Build/commit/9759174b644da91e7139f3dd6f2b7a39a0cb83a8)
inserts a NOP there, but also adds other code. Both inspected versions have
an `LBU v1` immediately followed by a store of `v1`, so cache-store timing
also requires examination. A general MIPS execution engine may not model
PlayStation load delays. No version was installed wholesale.

The author's [item/character documentation](https://github.com/PWBuild-Team/Perfect_Works_Build/wiki/Items-and-Characters)
identifies the elemental-ammo change problem. Broader Billy questions such
as displayed level-up Attack and reloading ammunition are separate issues;
this audit does not silently treat every unusual mechanic as a bug.

## Status effects and the limit of upstream change lists

The author's [battle-executable change map](https://github.com/PWBuild-Team/Perfect_Works_Build/wiki/Battle-Executable-edits)
explicitly combines effect repairs with redesigned effect handling,
different durations, new effects, and combat balancing. An entire donor
overlay is inappropriate for this project's original-content scope.

The following complete ranges were compared and remain byte-identical to
retail in both foundation discs:

- `0x25694–0x258CB`: intertwined defense, Wither, and Weaken processing.
- `0x25E3C–0x26257`: effect dispatch and target handling.
- `0x29B3C–0x29CA3`: duration handling.

The implemented `0x27C28` mask correction is outside those ranges. Its
presence does not prove Bracer, every defensive effect, status duration,
immunity or stacking behavior. The original intended behavior must first
be recovered before changing a description or applying a repair.

The upstream [bug-fix list](https://github.com/PWBuild-Team/Perfect_Works_Build/wiki/Bug-Fixes)
also includes scene, audio, shop, and camera issues outside battle.
The source version history contains bugs introduced by that mod as well as
retail issues. Treating all entries as original Xenogears defects would be
incorrect. No claim of complete game-wide bug coverage is made here.

## Reproduction and tests

Read-only CLI:

```text
python -m modules.definitive.bug_audit --retail "<retail disc>" --current "<built disc>" --disc 1 --output "<report.json>"
```

`python -m unittest modules.definitive.tests.test_bug_audit -v` passes five
tests using both configured retail discs. They check the known preimages,
ensure the three existing fixes do not falsely pass remaining-bug checks,
reject foreign/truncated inputs, and ensure an isolated changed flag or
instruction is reported as unverified rather than repaired.

No emulator was started. There is no New Game, save/load, combat, complete
campaign, or original-hardware acceptance pass attached to these results.
