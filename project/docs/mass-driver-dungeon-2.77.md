# Mass Driver v100 Defense Archive console records

V100 makes every physical console bank in the Defense Archive useful without
changing the room's authorization or route logic. Field 394's scenery contains
seven desk-console banks. The northeast bank remains entity 13, the dedicated
Directive 0320 and four-point ABCD authorization station. Each of the other
six banks now has its own optional, repeatable historical record.

The room also contains eleven operator chairs, but those chairs belong to the
seven connected desk banks. V100 deliberately creates one interaction per
physical bank instead of overlapping several interactions around multi-seat
stations.

## Record layout

| Bank | Entity | Dialogue | Operator point | Walkmesh triangle | Subject |
| --- | ---: | ---: | ---: | ---: | --- |
| East | 20 | 16 | `(350, 175)` | 68 | National economic, infrastructure, violence, and public-trust crisis |
| Southeast | 21 | 17 | `(115, -94)` | 252 | Warhead-adapter procurement ordered before civil review |
| South-center | 22 | 18 | `(-132, -40)` | 240 | The public "shared use" story versus same-day cancellation of civil launches |
| Southwest | 23 | 19 | `(-406, -94)` | 172 | Limited, first, and retaliatory strikes all escalating to full exchange |
| Northwest | 24 | 20 | `(-406, 225)` | 186 | Directive 0320 changed from hold on lost contact to release unless recalled |
| North-center | 25 | 21 | `(-220, 66)` | 197 | Miang routing decisions without signing the resulting orders |

All six points are strictly inside audited triangles on walkmesh layer 0's
single connected room component. Their no-facing `0x0C` interaction bounds are
small enough not to overlap one another, entity 13's authorization station,
entity 14's west bulkhead, or entity 17's north lift.

## Exposition

The six records reveal the conversion of an aspirational space-launch program
into a strategic weapon facility from different institutional perspectives:

- A national-security brief describes economic contraction, an unstable public
  grid, urban violence, collapsing trust, and rival governments answering the
  same internal crisis with blame and emergency rule.
- A procurement audit shows that Strategic Command commissioned a warhead
  adapter study in 6078, before the 6079 civil-program hearing had begun, with
  approval routed through the Prime Minister's adviser.
- A public-information archive contrasts the approved claim that "shared use"
  preserved the space program with the same day's internal cancellation of the
  science queue and civil launches.
- A sealed outcome model shows limited release, first strike, and retaliation
  all producing full exchange and civil survival below the recovery threshold;
  readiness was expanded anyway.
- Directive 0320's draft history changes loss of command contact from `HOLD
  RELEASE` to `RELEASE UNLESS RECALLED`, removes its expiration clause, and
  leaves it active after Central Command disappears.
- An executive routing audit names Miang as the Prime Minister's adviser. Her
  office routes the budget cuts, strategic access, safety waivers, and Directive
  revision, while the final orders carry the Director's signature rather than
  hers. Mara's unsent note recognizes that Miang controls which choices reach
  the person who must sign.

These are authored, canon-compatible reconstruction records rather than claims
of verbatim retail dialogue. They connect established Zeboim themes already
used elsewhere in the dungeon: political collapse, military appropriation of
the Mass Driver, Directive 0320, nuclear exchange, and Miang's indirect
manipulation.

## Interaction and route isolation

The six readers are deliberate X interactions only. Each action contains one
automatic-dialogue wrapper followed by a normal stop. They do not run on room
entry and contain no progression write, field transition, battle, reward,
save, shop, or menu operation.

The existing functional actors remain isolated:

- Entity 13 still owns the complete five-entry authorization routine.
- Entities 14-16 still own the Guardian-gated west bulkhead.
- Entities 17-19 still own the authorization-gated Defense Bay lift.
- Entities 20-25 own only the six new optional records.

The final ATEL table has 26 entities. The six controllers share stop routine
`0x079E`; their init/action pairs are `079F/07B7`, `07D0/07E8`, `0801/0819`,
`0832/084A`, `0863/087B`, and `0894/08AC`.

The field header grows from 36 to 42 records. Controllers are inserted at
records 20-25, so every retained static node shifts by exactly six records.
The native desk/display models remain records 30/31, chairs remain 32/33, room
models remain 34-39, and the fixed west/north frames remain 40/41. No baked
console, chair, door, texture, model archive, or graphics resource is replaced.

## Target 376 delta

| Component | v99 | v100 |
| --- | --- | --- |
| Complete canonical 1358 bundle | 132,132 bytes, `1f828cabf8b9f86ac46e44f748b248c905fa675caf961018a8f3ee1a0d61549e` | 134,996 bytes, `153a02d315fbeedd17b96dd6f3ff6a54f91e58702061cb560d166217561dcc15` |
| Prepared header | 976 bytes / 36 records, `df510e6d99747438e61310596e4bdb5cb4f85d5589b6af25131d8d9b626658a8` | 1,072 bytes / 42 records, `29055284994bc48db466e0f63bbc9d76e722c48354c442cd2d56b41d25385eb9` |
| Script | 3,398 bytes, `89b9d8c77608c4b2786faefeb59a063e40ec05ce9b3e23e49b804aa4f0942b52` | 4,077 bytes, `3a28d451eb084489cc49ff5b80c5d2f0e06af5beab010f1a134034a6f1b54814` |
| Dialogue | 2,209 bytes, `c357dfe6ad636f5e1d0f80f8b8e598ce17c5623ceccad6979c83c36ab51d892c` | 4,000 bytes, `6121d866bd3105e2651fc21f90a1f0cb7617828ca21a69b6a936ebccc8cc38f4` |

Canonical 1359 graphics remains byte-identical at 239,616 bytes with SHA-256
`969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd`.
Relative to v99, canonical 1358 is the only changed declared replacement.

## Packaged v100 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v100.bin`: 695,841,552
  bytes, 295,851 raw sectors, SHA-256
  `11bd8e140b272dee22bf5da6a6349069341bd81bb1c5d00e3b8558877906e43f`.
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v100.cue`: 107 bytes,
  SHA-256
  `2303521cea39b6e7b6c82338779e7dd82a4f260033d787e003e9f5b52040feb3`.
- Manifest `work/mass_driver_v100_stage/manifest.json`: 199,944 bytes,
  SHA-256
  `e32dccc8c0872796586b45cfcccd93327f0edc41bba6aa72ab8de2fa16ba97bc`.
- The manifest has 128 jobs and 162 declared replacements totaling 10,878,648
  bytes. Their canonical-ID-order aggregate SHA-256 is
  `bf72649459017c3292d7326f5953f4307042b569e66ea651adffe673d69007dd`.
- The complete automated suite passes 208 tests and 2,600 subtests with no
  failures, errors, or skips.

## Cold-boot acceptance

1. Fully quit DuckStation and launch
   `output/PLAY_MASS_DRIVER_STANDALONE.cmd`. Confirm it selects the v100 CUE,
   choose New Game, and load no older F1 state or in-game save.
2. Enter the Defense Archive from the east stairs. No record should open
   automatically.
3. Use the northeast built-in console and confirm it still owns Directive 0320
   and the A-2/B-5/C-8/D-4 authorization workflow.
4. Visit each of the other six desk-console banks and press X. Confirm all six
   subjects listed above appear once each and can be reread.
5. Confirm no hotspot opens from an adjacent bank, the west bulkhead, or the
   north lift.
6. Authorize the facility and confirm the north lift still reaches the Goliath
   Factory Gear hall. The west bulkhead must remain locked until Guardian
   victory.

A v99 state saved inside target 376 retains the old resident room script and
cannot validate these interactions. Leave and re-enter the room from v100
media, or use the full cold-boot path.
