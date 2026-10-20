# Native weight verification

Date: 2026-09-07. Baseline: the actual `foundation-ui-v2` Disc 1 and Disc 2
images, compared with the configured USA retail sources. This investigation
found and corrected a real inventory-weight bug. It also established that
Gear accessory weight already has a native battle effect. It does **not**
certify every food scene, actual memory-card I/O, or an original body-weight
damage formula.

## New correction: a gain item could make a character lose weight

Native field food and inventory items use different limits. The inventory
gain path caps the mutable weight byte at 200. Field scripts can set a whole
weight of 255, which can exceed that mutable-byte cap after subtracting the
character's fixed weight. The inventory path originally stored the sum into
a byte before testing its cap.

The bug is reproducible by executing the instructions from the built image:

| Starting Fei record `[fixed, mutable, tenths]` | Item | Original result | Corrected result |
| --- | --- | --- | --- |
| `[26, 201, 0]` | Bulimy Seed | `[26, 200, 0]` | `[26, 201, 0]` |
| `[26, 229, 0]` | Bulimy Fruit | `[26, 200, 0]` | `[26, 229, 0]` |
| `[26, 252, 0]` | Bulimy Fruit | `[26, 0, 0]` | `[26, 252, 0]` |

The first two cases fit the observed field-food total cap of 255. The third
is an injected byte-boundary case; it demonstrates an arithmetic wrap without
claiming that a particular meal reaches that state.

`modules/definitive/weight_fix.py` changes exactly the existing 48-byte gain
span at decoded menu `0x1E4B0..0x1E4E0`. It checks the original mutable weight
before adding. A value already at or above 200 remains unchanged; values below
200 gain the native amount and retain the original cap. Subtraction, fixed
weight, fractional weight, field scripts, save structure, Gear weight and
combat formulas are unchanged.

All four menu copies are required: compressed canonical 39 and uncompressed
2597, 2599 and 2603. Their retail decoded image is the same 153,864 bytes,
SHA-256 `82f84a24ac1fd1979754e1cc9c861405fb59ce95dd78db00a76f00c8f1bd177d`.
The patch accepts that exact preimage and verifies compression round trips.
It uses the reserved assembler temporary register, explicit branch delay
slots, and an independent instruction between each load and its first use.
There is no code cave, decoded-overlay growth, new state or balance curve.

## Body weight: evidence from native instructions

Character records begin at GameState `0x26C`, have stride `0xA4`, and use
bytes `0x77`, `0x78` and `0x79` for fixed, mutable and fractional components.
The initial Fei record is `[26, 50, 0]` on both retail discs.

| Path | Native resource and offset | Verified behavior |
| --- | --- | --- |
| Inventory weight items | Menu 2599, `0x1E484..0x1E510` | Item flags at `+0xA & 2` select weight; `+0xC & 0x8000` selects gain; the low byte supplies the amount. |
| Status display conversion | Menu 2599, `0x128EC..0x1293C` | `hundredths_lb = 22 × (10 × (fixed + mutable) + tenths)`. Fei starts at 167.2 lb. |
| Native save-buffer copy | Menu 2599, `0x1FA28..0x1FAB4` | Copies all eleven complete character records to save buffer `+0x290`. |
| Native inverse copy | Menu 2599, `0x1FD10..0x1FDBC` | Restores those complete records, including all three weight bytes. |
| Field weight getter | Decoded field 36, `0x1ABF0..0x1AC9C` | Reads fixed + mutable whole weight. |
| Field weight setter | Decoded field 36, `0x1AB50..0x1ABEC` | Subtracts fixed weight from requested whole weight, floors below-zero to zero, then stores the mutable byte. |

The item data is canonical 2594, archive member 0, 150 records of 16 bytes:

| Native item ID | Name | Native whole-weight change | Display-unit change |
| --- | --- | ---: | ---: |
| 72 | Anoret Seed | −2 | −4.4 lb |
| 73 | Anoret Fruit | −4 | −8.8 lb |
| 74 | Bulimy Seed | +2 | +4.4 lb |
| 75 | Bulimy Fruit | +4 | +8.8 lb |

Limits can reduce or eliminate the change. These native item descriptions
make only relative claims; they do not promise an Attack or speed bonus.

The field overlay's native extended-opcode table assigns FE 69 to the getter
and FE 6B to the setter. Retail canonical 842 script offsets `0x9AA..0x9CA`
contain a getter, variable addition, comparison with 255, clamp to 255 and
setter. Canonical 852 repeats the same sequence at `0xAF7..0xB17`. Canonical
856 calls its clamp helper at `0x131A` before the setters around `0x12E9`.
These are concrete bytecode references, not inference from English dialogue.
Their entire scripts are unchanged by this correction.

The raw field setter itself has no upper clamp. An injected total of 282
with Fei's fixed 26 produces mutable zero by byte truncation. The inspected
meal clamp prevents that particular input; other food and event paths still
need complete reachability coverage. No blanket claim that every field setter
call is safe is made.

The save-copy check executes both native loops and restores 1,804 distinct
bytes exactly. It proves serialization of weight into the game's save buffer;
it does not simulate a card controller, save UI, power cycle or disc change.

## Gear weight: a native combat consumer is present

Gear weight is separate from pilot body weight. Relevant Gear-record fields
are accessory weight `+0x44`, computed agility penalty `+0x4A`, frame weight
`+0x68`, load allowance byte `+0x75`, and agility `+0x98`.

The native menu/shop code adds each of the three accessory weights from its
28-byte data record `+0x06`. Canonical 2594 archive member 19 contains 150
accessory records. The largest native accessory weighs 600, so a three-slot
sum cannot exceed 1,800. The status view displays frame + accessory weight.

The native penalty routine at Gear-shop 2602 `+0x1190C` and its menu copy
at 2599 `+0x1F928` computes:

```text
penalty = max(0, trunc((floor(accessory_weight / 120) - gear[0x75]) / 2))
```

The Gear shop stores this result into `+0x4A` at `+0x116C0`. The menu view
subtracts the penalty from Gear agility. Battle resource 38 `+0x287D0`
loads that same penalty and subtracts it when preparing Gear agility at
`+0x98`. The Gear ATB path reads the resulting `+0x98` value at battle
`+0x290F0`. This completes a static native data-to-battle-consumer chain;
equipment load is not merely a cosmetic number.

CPU-block checks exercised all 12,607 combinations of accessory sum 0–1,800
and seven initial allowance values on the baseline Disc 1 code with no
mismatch. The repeatable test suite checks both sides of every 120-unit
threshold across those allowances. It also executes 96 battle preparation
cases varying agility, equipment bonus and penalty.

Changing pilot body bytes among low, initial and high weights leaves the
deterministic ATB input unchanged in 30 executed on-foot/Gear cases. The
original body-weight Attack/ATB formula has not been recovered. The existing
project-designed body-weight combat curves remain excluded from Definitive.

## Validation and limits

Command: `python -m unittest modules.definitive.tests.test_weight_audit -v`.
Result: **8 tests passed**. Tests execute original/patched MIPS instructions
using Unicorn 2.1.4 and verify whole-image preconditions, all 256 mutable-byte
values for all four weight items, preservation of every other character byte,
550 display inputs, save-buffer round trips, Gear thresholds, native battle
consumers, and rejection of foreign/previously patched images.

The [machine-readable report](weight-verification.json) separates what was
installed in `foundation-ui-v2` from the corrected candidate resources.
The release built after this audit has its own receipt and post-build checks;
an in-memory candidate result alone is not an installed-media claim.

Unicorn executes CPU blocks; it does not model complete PlayStation gameplay,
GPU/UI, asynchronous disc I/O or R3000A timing. No memory card, save state,
user save or emulator configuration was changed. Runtime cases still needed:
normal meals, repeated meals at limits, inventory use after meals, Status
display, real save/load, menu/Gear-shop equipment changes, combat timing,
food-related field checks and disc transitions.

Primary reverse-engineering references were checked against local retail
instructions: the matching decompilation's [Gear structure](https://github.com/ladysilverberg/xenogears-decomp/blob/0feb30011917c55e26ca1dd68010f7c689605385/include/main/game.h),
[Gear-shop implementation](https://github.com/ladysilverberg/xenogears-decomp/blob/0feb30011917c55e26ca1dd68010f7c689605385/src/gear_shop_menu/main/render.c),
and [overlay load address](https://github.com/ladysilverberg/xenogears-decomp/blob/0feb30011917c55e26ca1dd68010f7c689605385/config/gear_shop_menu.yaml).
