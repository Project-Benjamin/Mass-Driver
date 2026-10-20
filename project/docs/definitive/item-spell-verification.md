# Item and spell verification

Audited 2026-09-07 against the exact `foundation-ui-v2` media on both discs.
**The existing build did not have every item/spell description corrected.**
Its native names, item data, descriptions and battle action tables were still
identical to retail. Two incorrect food descriptions were independently
confirmed and a guarded correction was implemented. Whole-game effect
semantics and gameplay remain incomplete.

## Confirmed corrections

| Item | Previous description | Actual native recovery | Corrected description |
| --- | --- | --- | --- |
| Hob-Meat, item 58 | 150 HP, non-battle | 100 HP, capped by maximum HP | 100 HP, non-battle |
| Hob-Steak, item 59 | 500 HP, non-battle | 150 HP, capped by maximum HP | 150 HP, non-battle |

Both the menu explanation and shop explanation are corrected. Each numerical
replacement uses the same three character positions, preserving the string
offsets, length, width and height. No item potency, cost, availability, effect
flag, battle instruction or weight value is changed by this patch.

This is not a choice to rebalance food. Native item records in canonical 2594,
archive member 0, start at byte zero and have a 16-byte stride. Their HP
potency byte at `+8` is 1 for Hob-Jerky, 2 for Hob-Meat and 3 for Hob-Steak.
The menu routine in canonical 2599 at decoded offset `0x1E234` loads 50,
`0x1E240` reads that potency byte, and `0x1E248` multiplies them. The following
code adds HP and caps it to the character's maximum.

The battle-context check is independent: canonical 2615, loader offset
`0xD74..0xD84`, only admits nonzero item IDs below 49 to the normal battle
inventory. Food IDs 57–59 do not enter that inventory. The separate ammunition
inventory that follows reads weapon IDs, so its similarly numbered IDs do
not make these foods usable in battle.

The audit executes the actual native HP and battle-inventory instructions in
isolated RAM through Unicorn. **36 HP recovery cases and 150 battle-inventory
cases pass per disc.** HP cases cover zero HP, low HP, near maximum and full
HP at maximums 100, 499 and 999. The battle test covers every native item ID
0–149 with a positive quantity. This is CPU execution, not an emulator scene,
menu rendering check, memory-card test or full battle playthrough.

Implementation:

- `modules/definitive/description_fixes.py` provides
  `build_description_replacements(read) -> ({2594: bytes}, audit)`.
- It requires the exact clean USA 2594 hash and guards the independently
  traced menu and battle inventory instructions.
- Only description members 14 and 41 are recompressed. All other 54
  compressed archive members remain byte-identical. The native archive remains
  40,336 bytes.
- Patched resource SHA-256:
  `5e3e38f3d88060c7378d51b798b098054d1eb45a706390e30a6e5166fdef8baa`.

The original baseline artifacts retain both discrepancies. Run the audit on
a rebuilt candidate to verify the corrected descriptions are actually in that
candidate; successful unit tests alone do not establish installation.

## Inventory coverage

`modules/definitive/item_spell_audit.py` now extracts native text and effect
records reproducibly. It imports the canonical shared disc/LZSS/dialogue tools.
Raw bytes, decoded offsets and unrecognized character/control codes are kept
in its JSON, instead of filling unknown semantics with guesses.

| Native table | Resource / member | Raw record slots |
| --- | --- | ---: |
| Items, including key/debug/unused slots | 2594 / 0 | 150 |
| Character weapons | 2594 / 1 | 100 |
| Character accessories and armor | 2594 / 2 | 200 |
| Gear frames | 2594 / 16 | 180 |
| Gear armor | 2594 / 17 | 150 |
| Gear engines | 2594 / 18 | 150 |
| Gear accessories | 2594 / 19 | 150 |
| Gear weapons | 2594 / 42 | 100 |
| Character ability slots | 2614 / 4–14, action rows 22–37 | 176 |
| All Gear action rows | 2614 / 16–34, 41 rows each | 779 |

These are record-slot counts, **not distinct usable item/spell counts**. They
include blanks, unused records, alternate forms and ordinary attacks. The
eight item/equipment tables contain 1,180 slots. Of the 176 character ability
slots, 95 contain a readable nonempty English name; this does not establish
that all 95 are obtainable.

The report inventories 5,152 text slots across names, description variants,
Gear Ether explanations and special-option explanations. Character ability
names and two-line descriptions are joined to native action rows and base
EP cost. Equipment modifiers, targets and effect flags are retained as raw
values until their consumers are independently verified. Gear Ether/special
names and descriptions are present as separate tables; their complete joins
to action rows still need verification.

The pinned primary [Noah battle loader](https://github.com/yaz0r/Noah/blob/d725fe231e56a895c17df0554042b9e2bd1acb78/NoahLib/battle/battleLoader.cpp)
and [ability menu](https://github.com/yaz0r/Noah/blob/d725fe231e56a895c17df0554042b9e2bd1acb78/NoahLib/battle/menu_chi.cpp)
document the character table selection and 22-plus-slot action index. The
matching project's [menu structures](https://github.com/ladysilverberg/xenogears-decomp/blob/0feb30011917c55e26ca1dd68010f7c689605385/include/system/menu.h)
identify Gear record strides and fields. These are incomplete reverse
engineering references, not certification of every effect.

## Findings still open

- All three source resources (29, 2594, 2614) match retail on both baseline
  discs. Other item descriptions have not been silently rewritten.
- Of 29 comparisons between meaningful menu/battle data copies, 28 match.
  Gear record 16 differs by 11 bytes across action rows 5, 8, 11, 20 and 36
  in retail itself. The report records the exact differences. Their purpose
  and runtime relevance are not established; they are not automatically
  treated as corruption or a required fix.
- Blank armor or weapon explanations are not automatically bugs; ordinary
  numeric stats can be shown elsewhere in the menu. Named equipment with
  conditional effects still needs consumer and interaction tests.
- Spell target scope, damage/healing formulas, element/resistance handling,
  status duration and immunity, resurrection, support effects and equipment
  interactions remain unverified outside separately documented mechanics
  tests. A row inventory or a lack of reported bugs is not a passing test.
- The food correction does not resolve or certify Bracer, Wither, Weaken,
  Ether Veiler, EtherDoubler, Life Stone, learning/experience accessories, or
  every other outstanding gameplay issue.

## Reproduce

```text
python -m unittest modules.definitive.tests.test_item_spell_audit -v
python -m modules.definitive.item_spell_audit --retail "Xenogears (Disc 1).bin" --build builds/definitive/foundation-ui-v2/Xenogears_Definitive_CD1.bin --disc 1 --output output/definitive/verification/foundation-ui-v2-items-disc1.json
python -m modules.definitive.item_spell_audit --retail "C:\Users\Chad\Desktop\Noah\Xenogears (Disc 2).bin" --build builds/definitive/foundation-ui-v2/Xenogears_Definitive_CD2.bin --disc 2 --output output/definitive/verification/foundation-ui-v2-items-disc2.json
```

Nine targeted tests pass. They cover both retail discs, native execution,
compression, unchanged members, exact text allocation, repeated/foreign
patch rejection and text parser boundaries. The module and profile test
results are recorded separately by the overall verification work.

Baseline evidence is in
`output/definitive/verification/foundation-ui-v2-items-disc1.json` and
`output/definitive/verification/foundation-ui-v2-items-disc2.json`, including
the whole media hashes and individual native execution cases. No user saves
or memory cards were used or modified.
