# Definitive mechanics audit

Date: 2026-09-07. Scope: USA retail Discs 1 and 2, existing content only.

This document describes the original three corrections. The later
[restoration verification](restoration-release.md) adds native CPU evidence,
the Deus camera guard, corrected food descriptions, and the Bulimy cap fix.
Refer to [native weight verification](weight-verification.md) for the completed
code-level weight investigation and its remaining gameplay limits.

Three isolated binary corrections are implemented in
`modules/definitive/mechanics.py`. They have passed binary and compression
checks against both configured retail discs. **No emulator test or full-game
playthrough has been performed for these corrections.** This is an initial
audited subset, not a claim that every spell, item, or game bug is fixed.

## Implemented corrections

| ID | Resource / offset | Exact instruction change | Result |
| --- | --- | --- | --- |
| `gear_charge_multiplier` | Decoded canonical 38 / `0x2A894` | `00 00 A3 94` → `0A 00 03 34` | Charger multiplication uses ten instead of loading a halfword from the first entry in the battle damage table. |
| `defense_up_status` | Decoded canonical 38 / `0x27C28` | `00 01 42 30` → `00 40 42 30` | The existing on-foot defense adjustment checks status bit `0x4000` instead of `0x0100`. |
| `gear_shop_ether_amp` | Uncompressed canonical 2602 / `0x11428` | `54 00 00 A2` → `00 00 00 00` | The Gear Parts menu stops clearing the equipment Ether-amplifier byte at Gear-record offset `0x54`. |

The Charger correction was isolated by comparing the binary before and after
the author's [Charger fix commit](https://github.com/PWBuild-Team/Perfect_Works_Build/commit/c81044cce6ee9a9876073a4d87d261124ba114fc).
Only the one instruction differs in the meaningful decoded overlay; the
compressed stream's terminal padding also changes. Independent inspection of
the local retail MIPS confirms the value feeds the existing multiplication.
The zero-Charger path still supplies 30 fuel, and the existing attack-level
and Infinity-mode adjustments are preserved byte for byte.

The status-mask correction was isolated from the author's
[Def Up fix commit](https://github.com/PWBuild-Team/Perfect_Works_Build/commit/6a6dac9164bf12eadef34dcf6b73e5aeab22ba00).
Local disassembly confirms a single `ANDI` immediate changes. The
[upstream version history](https://github.com/PWBuild-Team/Perfect_Works_Build#version-history)
reports increased blocking as well as working Def Up. That outcome requires
runtime coverage; the patch does not claim a separately recovered defense
formula or modify status duration.

The Gear-shop correction was isolated from the author's
[canonical 2602 commit](https://github.com/PWBuild-Team/Perfect_Works_Build/commit/9355acf5cc507edc12bb72f3d63100c7edca5054).
Its entire 82,080-byte image matches retail except that one `SB zero,0x54(s0)`
becomes a NOP. The author's [Bug Fixes documentation](https://github.com/PWBuild-Team/Perfect_Works_Build/wiki/Bug-Fixes)
identifies the trigger as opening the Parts menu and losing the Ether amp
boost from equipment. The surrounding stores remain untouched.

These patches reproduce minimal independently inspected instruction changes.
They do not import a donor overlay, rebalanced enemies, new items, new spells,
new scene scripts, or another project's translation.

## Preimage identity and verification

Both configured retail discs supplied the same bytes for these canonical
resources. Disc 2's physical FAT index is canonical ID minus five.

| Resource | Size | SHA-256 |
| --- | ---: | --- |
| Packed retail battle 38 | 166,564 | `b9c3a15bf5f3eb06bcb3824ef62793b9a500fe1dcb3717fe8963e23e9f27628b` |
| Decoded retail battle 38 | 343,936 | `1830b4ef1fe37129972fc310dfad534f8161d6c0b123e74254c3711334a3e291` |
| Retail Gear shop 2602 | 82,080 | `5a08a22f2c5cc1d131b33a944d3167a2ac460c5f9f17f2dcf94dd8860158a25c` |
| Corrected Gear shop 2602 | 82,080 | `18ea2428cad59024e1facb509bdb0d29b9873fe68df79666d52df8a65fe8f7a2` |

The builder API is `build_mechanics_replacements(read_canonical, fixes)`.
It returns a dictionary of canonical replacements and a JSON-ready audit.
The reader belongs to the builder so input reads can be recorded by the
project's source tracking. `SUPPORTED_FIX_IDS` lists the three selectors.
The packed-battle and decoded-battle APIs select only `BATTLE_FIX_IDS`.

Only exact clean preimages are accepted. Unknown selections, duplicates,
foreign images, unrelated modifications, and repeated patching fail closed.
Recompression imports `shared.tools.xgfield.compress_lzss_retail` directly and
checks the complete output, including at most seven zero allocation-padding
bytes. No historical tool or chapter implementation is imported.

Validation command:

```text
python -m unittest modules.definitive.tests.test_mechanics -v
```

Result: 11 tests passed. Tests exercise both configured retail discs, selected
instruction boundaries, Charger multipliers, status masks, Gear-shop bytes,
compression round-trips, canonical reads, and rejection of modified inputs.
Tests that require user retail discs skip explicitly when none are configured.

## Weight: existing behavior versus a newly designed formula

The shared `shared/tools/xgbattle_weight.py` already implements a body-weight
combat option. Its character record reads use offsets `0x77`, `0x78`, `0x79`
and interpret weight as:

```text
hundredths of a pound = 22 × (10 × (fixed byte + mutable byte) + tenths byte)
```

Its combat curves are a **project design**, with Fei's initial 167.20 lb as
neutral, heavier characters receiving more physical Attack and slower ATB.
Those constants were not recovered as an original Square formula. Installing
them as an undisputed bug fix would violate the distinction between repairing
existing behavior and changing balance. The definitive fixes therefore leave
that option unapplied. The shared implementation remains unchanged.

Body weight, Gear total weight, and Gear accessory load are distinct fields.
The [matching decompilation's Gear structure](https://github.com/ladysilverberg/xenogears-decomp/blob/main/include/main/game.h)
identifies equipment weight separately from total weight. This confirms that
a body-weight damage/ATB hook cannot certify the Gear-weight mechanic.

Still required: independently trace native food/consumable changes and clamp
behavior, verify memory-card persistence and menu display, then test Gear
accessory-load limits and their actual effect on battle readiness. Lack of
a verified body-weight combat consumer is not evidence for a particular new
balance curve. The current audit makes no claim that food or weight saving
is broken.

## Remaining bug and spell/item queue

These are investigation targets, not installed fixes:

| Target | Evidence and next check |
| --- | --- |
| Deus first battle HP-halving freeze at a side angle | Upstream Bug Fixes page documents the trigger. Isolate its battle-resource patch and reproduce both camera positions before claiming fixed. |
| Billy ammunition handling | [Author's ammo-fix commit](https://github.com/PWBuild-Team/Perfect_Works_Build/commit/7a9f6e74826c623e028793194a5017a71d320a8b) changes both overlay 38 and resource 2746. A single overlay replacement is not sufficient evidence; inspect event scripts and ammunition transitions together. |
| Bracer, Wither, Weaken, status durations and immunities | Upstream history describes repairs, but [Battle Executable edits](https://github.com/PWBuild-Team/Perfect_Works_Build/wiki/Battle-Executable-edits) shows they share broad changes with new effect handling and rebalancing. Extract no code until retail semantics and dependencies are independently separated. |
| Ether Veiler, healing/resurrection and elemental resistance cases | Establish reproducible retail cases and inspect native effect tables. Do not turn community reports into fixes without evidence. |
| Every other item/spell | Inventory every native item/ability row and its targets, cost, effect, duration, cap and immunity. A missing issue report is not a passing test. |

Keep balance changes such as increased stats, altered learn levels, revised
critical rates, new status durations, and removal of damage caps separate
from repair claims. Optional user-requested cheats belong in their own toggles.

## Runtime acceptance cases

1. Gear shop: equip Ether-amplifying parts, record stats/damage, open Parts
   without buying, leave the shop and immediately battle. Repeat after
   purchase, with multiple Gears, no accessories, stacked accessories and a
   memory-card reload. The equipped bonus must persist without visiting Equip.
2. Charge: test no Charger plus A/S/X/Z Chargers at attack levels 0–3 and
   Infinity; vary first attack data, Gear, Booster, fuel capacity and near-full
   tanks. Recovery must use the correct base and remain capped at maximum fuel.
3. Def Up: compare identical physical attacks with/without the status,
   separately from Defend, blocking, shields, Ether damage and Gear battles.
   Check expiration and enemy application. Record the upstream blocking effect.
4. Use a new game independently of existing saves. Retain original memory
   cards, record the exact activated release/media, and run the project's
   `play --check-only` identity check before emulator work.

Only add a runtime pass after those cases have actual captured results.

## Optional no-random-encounters candidate

`modules/definitive/encounters.py` implements a separate `none` option, with
normal mode returning no replacements. It changes two instructions and leaves
all field/event scripts intact. Its state is **binary-verified candidate;
emulator validation pending**. This option is a user-requested gameplay
preference, not a bug fix.

The [matching decompilation's overlay map](https://github.com/ladysilverberg/xenogears-decomp/blob/main/tools/scripts/overlays.yaml)
places the field overlay in canonical 36 and the world map in canonical 37;
battle is canonical 38. Each overlay loads at `0x8006FAF0`.
The [Noah field random-battle implementation at the inspected revision](https://github.com/yaz0r/Noah/blob/d725fe231e56a895c17df0554042b9e2bd1acb78/NoahLib/field/fieldRandomBattles.cpp)
provides a primary reverse-engineering reference for the timer and weighted
formation selection. Its naming was verified against the local retail MIPS;
the patch is generated from retail, with no Noah code imported.

| Canonical resource | Decoded offset | Before → after | Static effect |
| --- | --- | --- | --- |
| 36: field | `0x99CC` | `1C 00 A0 10` → `1C 00 00 10` | Changes `BEQ a1,zero` to `BEQ zero,zero` at the final random-dispatch gate. |
| 37: world map | `0x5940` | `0C D8 22 AC` → `0C D8 20 AC` | Changes the random timer's readiness store from `SW v0` to `SW zero`. |

The field branch retains its existing target `0x9A40`, the function's normal
register-restoring epilogue, and its NOP delay slot. Timer advancement and RNG
selection execute before this gate. The forced encounter VM handler at
`0x8009F5F4` is outside that function and unchanged. The
[matching decompilation's forced-encounter handler](https://github.com/ladysilverberg/xenogears-decomp/blob/main/src/field/main/misc6.c)
is a separate call path. This is why the candidate modifies this late random
gate rather than clearing encounter tables or changing battle opcodes.

World-map disassembly shows the timer function first clears readiness address
`0x8009D80C`, then increments it only when a generated countdown reaches zero.
After this patch, every direct store to that address in the overlay writes
zero: offsets `0x1D78`, `0x5790`, `0x58F8`, and `0x5940`. The call paths for
movement, menus and battle transitions remain byte-identical. This is local
binary evidence; world-map story transitions still require runtime coverage.

| Retail input | Packed SHA-256 | Decoded SHA-256 |
| --- | --- | --- |
| Field 36, 125,304 packed bytes | `7735f4e2f204b7afd053d95f2812053b56eb03306c7d2de38c08b2d78ba392dd` | `38a1ce829a6f094c505f67143d6ace2d328418c65425a7383991179467e1fdfc` |
| World map 37, 92,180 packed bytes | `0f7e7a283fc5ef25d4a82960e16b119d09e1ba5594cc02069cf3dd2113f48803` | `4c15fd32b3a03d7cd5ea4403dcaabc70abaf99b6aaca65d63d6866803edaac70` |

Both retail discs match these identities. The field compressed stream's
declared trailing bytes use zero-filled disc-sector tail, so the reader adds
16 zero bytes only after matching the exact source identity and then checks
the entire decoded hash. Repacked outputs use complete LZSS groups and verify
their entire decoded content and allocation padding.

API: `build_encounter_replacements(read_canonical, mode="none")` returns
canonical replacements 36 and 37 plus a JSON-ready audit. `normal` reads
nothing. `half` is explicitly rejected by this API until a separately audited
implementation exists.

Validation: `python -m unittest modules.definitive.tests.test_encounters -v`
passed 8 tests. They compare every byte outside both patch words, inspect
branch registers/target/delay-slot/epilogue, check all direct world-map
readiness stores, verify forced-handler bytes, check both discs, round-trip
compression and reject modified inputs.

Runtime acceptance still needed: New Game, a normal field battle area, world
map walking and Gear travel, entering/exiting transport, save/load, forced
Rankar and other story bosses, chained mandatory battles, Disc 2 transitions,
and switching back to a normally patched image using memory-card saves.

### Half-rate evidence gap

World-map offset `0x5774` loads `0x180`; changing it to `0x300` is only one
mode. The branch at `0x576C` already selects `0x300` from its delay slot for
another flag state. Additionally, a saved world-map timer can be restored
through a different store at `0x5CBC`. Field schedules are set separately by
the F7 script handler at decoded field offset `0x1ED6C`.

Therefore changing a single world-map constant or only formation-selection
weights cannot certify half encounters throughout the game. A complete
implementation must cover both world-map modes, persisted timer state and all
field scheduling paths without altering forced battle scripts, and must
define overflow handling for doubled timer values. No half-rate code is
silently substituted by the no-encounter API.
