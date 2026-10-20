# Max gold audit

Date: 2026-09-07. USA retail Discs 1 and 2. Read-only investigation; no disc,
memory-card file, save state, or emulator memory was changed.

**Persistent Max gold is not implemented.** The money cap and several native
update paths are now identified, but there is no verified load/save hook and
the write-path inventory is not exhaustive. A New Game-only data edit would
not satisfy the persistent option and is recorded separately below.

## Storage and cap

The native money field is a 32-bit value at game-state offset `0x1924`.
`g_GameState` is `0x8006D634`, so its live address is `0x8006EF58`.
`g_pGameState` is a pointer held at `0x8005A39C` and is used by field scripts.
The normal cap is **9,999,999 G**, hexadecimal `0x0098967F`, little-endian
bytes `7F 96 98 00`.

The primary [game-state structure and cap definition](https://github.com/ladysilverberg/xenogears-decomp/blob/0feb30011917c55e26ca1dd68010f7c689605385/include/main/game.h)
and [symbol map](https://github.com/ladysilverberg/xenogears-decomp/blob/0feb30011917c55e26ca1dd68010f7c689605385/config/symbol_addrs.slus_006.64.txt)
give those locations. The field and shop cap constants were independently
confirmed in the local retail instructions. `0xFFFFFFFF` is not the normal
cap and conflicts with code paths that interpret money as signed.

The kernel debug menu sets 999,999,999 rather than the normal cap. This is
debug behavior and is not suitable evidence for a retail maximum. The local
retail main executable contains that debug-gated store at raw canonical 22
offset `0xCBAC`; enabling it would also enter unrelated debug-menu behavior.

## Native update paths located

All offsets below are resource offsets. Field resource 36 is decompressed
before interpreting offsets; the menu resources listed here are uncompressed.
Disc 2 uses physical FAT index `canonical - 5`.

| Path | Canonical resource | Offset(s) | Local retail observation |
| --- | ---: | --- | --- |
| Field money comparison | 36 | function `0x26434`, read `0x26484` | Reads `g_pGameState->gold` and branches according to script amount. |
| Field add money | 36 | function `0x264C8`, store `0x2650C` | Adds the argument, clamps above 9,999,999, then stores. |
| Field subtract money | 36 | function `0x2652C`, store `0x26568` | Subtracts argument, floors negative results at zero, then stores. |
| Battle reward settlement | 2596 | stores `0x43C0`, `0x43D0` | Adds accumulated reward to current gold, then caps overflow. |
| Ordinary shop transaction commit | 2601 | stores `0xA2C8`, `0xA2D8` | Stores computed post-transaction amount, then caps above maximum. |
| Second ordinary shop commit | 2601 | stores `0xBC78`, `0xBC88` | Another transaction path with an independent money store/cap. |
| Gear shop transaction commit | 2602 | stores `0xCF78`, `0xCF88` | Independent transaction store/cap. |
| Second Gear shop commit | 2602 | stores `0xF524`, `0xF534` | Independent transaction store/cap. |
| Gear refuel payment, insufficient-funds branch | 2602 | store `0x10618` | Reduces money through the partial-service arithmetic path. |
| Gear refuel payment, sufficient-funds branch | 2602 | store `0x10664` | Stores current money minus service price. |

The primary [field money handlers](https://github.com/ladysilverberg/xenogears-decomp/blob/0feb30011917c55e26ca1dd68010f7c689605385/src/field/game_logic/gold.c)
confirm that comparisons, increases and decreases are distinct handlers.
Both lower and upper clamps matter. Replacing only a money-reward store does
not stop spending or populate the balance after loading an existing save.

The [ordinary shop implementation](https://github.com/ladysilverberg/xenogears-decomp/blob/0feb30011917c55e26ca1dd68010f7c689605385/src/shop_menu/main/misc.c)
holds an initial balance and a proposed post-purchase balance while the cart
is open, then commits the transaction on confirmation. Updating the live
balance alone does not rewrite those cached values. The retail Gear shop has
additional service-payment paths, including a partial-payment branch, so a
buy/sell-only patch is incomplete.

This is a targeted inventory, not proof that all writers have been found.
An immediate-offset search misses stores through a precomputed pointer,
bulk game-state copies, and memory-card deserialization. Each listed pointer
store was therefore checked in its local MIPS context. Battle script money
reads also exist in canonical 38, at `0xBC94` and `0xD6D8`.

## Verified New Game-only data candidate

The clean initial state is canonical **2595**, length **9,048 bytes** on both
retail discs. Its SHA-256 is:

```text
d892fa678f66ab12e0d2cb5ccb6cd432ecbc055b41360d8a4c4404fd38f1e20b
```

Its money bytes at `0x1924` are `64 00 00 00`: **100 G**.
Changing only those four bytes to `7F 96 98 00` gives this in-memory candidate
hash:

```text
1ba6d9df268bd07af4d0287f3e591d5813b3ab6e8e0d4deb20e199a051233fd9
```

The [inspected initial-state loader](https://github.com/yaz0r/Noah/blob/d725fe231e56a895c17df0554042b9e2bd1acb78/NoahLib/kernel/gameState.cpp)
reads directory `0x10`, local file 3, which resolves to canonical 2595. This
establishes the purpose of the data resource. That edit would give a new
game a larger starting balance; purchases would still subtract money and
existing saves would retain their balance. **No patch file or enabled option
was created for this candidate.**

## Exact remaining work for a persistent option

The principal missing hook is **after a successful memory-card state restore,
before the restored state reaches a field/shop affordability check**. A
corresponding invariant must hold **before the save payload/checksum is
assembled**, not merely after the user returns from the menu. The inspected
[Noah save/load dispatcher](https://github.com/yaz0r/Noah/blob/d725fe231e56a895c17df0554042b9e2bd1acb78/NoahLib/menus/menuHandler.cpp)
has `MissingCode()` in `updateSaveState` for the actual selected card actions;
it cannot ground those two hooks. The New Game action is separate from the
load action in that source.

Next audit the retail menu overlay and menu subresources to locate the final
game-state copy on successful load, the save serializer and checksum, and
the failure/cancel branches. Prove that forcing the cap touches only live
game money after a successful load and is serialized normally only if the
player chooses to save. Then trace all currency writes, including pointer
aliases and services, and decide how shop preview values should display the
non-decreasing balance.

A frame/VBlank write is not accepted as proof: a transaction may cache a
balance, a save operation may copy state between refreshes, and menu code
may run in a different update loop. Such a hook requires ordering evidence.

Runtime acceptance must cover: starting a New Game; loading preexisting low-
money and zero-money saves; ordinary buy/sell and cancellation; Gear upgrades,
parts, repairs/refuel and partial-service branches; inns and script fees;
battle rewards at the cap; a saved/reloaded capped balance; and returning to
an unmodified-money build. Source saves remain untouched during preparation.

## Additional retail identities checked

| Resource | Bytes | SHA-256, identical on both discs |
| --- | ---: | --- |
| 2596 | 25,856 | `f474fd482506b89eaff9601d5958a1c867d35a4ad11c1f58f0ecef630008a0c8` |
| 2601 | 53,860 | `fd894b5113e4e12bb6aba5f775f1036744eb7f98ff2d1462ee10673868370c2a` |
| 2602 | 82,080 | `5a08a22f2c5cc1d131b33a944d3167a2ac460c5f9f17f2dcf94dd8860158a25c` |

No new runtime or unit-test pass is claimed for Max gold because no executable
patch was installed. The binary inventory and in-memory New Game candidate
were calculated by read-only extraction from the configured retail images.
