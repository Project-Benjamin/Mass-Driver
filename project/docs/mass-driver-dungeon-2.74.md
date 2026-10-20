# Mass Driver v97 native El-Regulus battle-entry restoration

V97 removes the formation-specific El-Regulus entry turn introduced in v96
and restores the native playable-Gear facing sequence. The complete v95 dungeon,
archive branch, Central Control finale, party, encounters, item progression,
attacks, and deathblows remain unchanged. Canonical battle overlay 38 remains
exact retail.

## Captured v96 regression

The user-created DuckStation state
`work/duckstation/savestates/SLUS-00669_1.sav` is 2,127,154 bytes with SHA-256
`3db10c4b78708120964806ed18a46a29c5f99da74dd21a7be283c5a9ae7e4de6`.
Its state header mounts the exact
`output/Xenogears_PW_CD2_mass_driver_standalone_v96.cue`, and its embedded
256-by-192 screenshot records El-Regulus's incorrect opening pose in the
nearby one-Dragon world-map battle.

The state supplies direct runtime evidence:

- El-Regulus is visual entity 0 at `(4020, 0, 3640)`.
- Its animation target is the slot center at `(3580, 0, 3640)`.
- The Dragon is visual entity 3 at `(3140, 0, 3640)`.
- Both targets are due west, whose correct yaw is `0x0400`.
- El-Regulus's root yaw is instead `0x0800` at the opening command menu.
- Exact v96 animation 0 is resident at RAM `0x8015D2E0`; its relative-turn
  packet is resident at `0x8015D2F6`, and the current bytecode pointer at
  `0x8015D306` is its completed tail.

This proves that the v96 packet loaded and executed. The problem was not stale
media, an old in-battle state, the model, or the shared overlay. V96 applied a
signed relative `-0x0800` turn to a formation that began El-Regulus at yaw
`0x0000`, producing the observed `0x0800`. After El-Regulus attacked, the
native target-facing path restored the expected presentation, matching the
user's report.

## Why the v96 correction was too narrow

V96 was based on a different formation. In the preserved Guardian evidence,
El-Regulus began at yaw `0x0C00`, while opcode `60` produced a slot-center
target coincident with its own root. Native opcode `43` therefore received a
zero vector and left the formation yaw unchanged. A `-0x0800` relative turn
mapped that one captured pose to `0x0400`, but a relative correction cannot
serve formations with different starting yaw.

An audit of all 17 retail playable Gears establishes the common native entry
contract: opcode `60` obtains the formation's slot-center target and opcode
`43` faces it. V97 follows that retail contract instead of retaining a
Gear-10-only unconditional rotation.

## Canonical 2960 restoration

V97 restores canonical 2960 to the exact v95 resource. Its animation 0 is:

```text
0A 00 0C 00 10 00 48 00 4A FD 61 00 0A 00 5A 08
32 00 06 00 60 00 43 00 10 FF 21 00 6D 00 00 00
```

The operative native entry pair is `60 00 43 00`. The v96-only packet

```text
62 20 00 00 00 00 00 F8 00 00
```

is absent. Removing its eight inserted bytes restores every subsequent pointer
and the original outer roots.

| Build | Size | Outer roots | SHA-256 |
| --- | ---: | --- | --- |
| v96 | 33,608 | `(2, 0x10, 0x7FFC, 0x8348)` | `86807cb3d54acb40649b174e384f31aa82a167274976faa2e7ed283c2b62ec0a` |
| v97 | 33,600 | `(2, 0x10, 0x7FF4, 0x8340)` | `627b332e5b2c15ca7e99d7d44e76fa8f72291634dbbfc32aae1ab19ef511c8c6` |

Canonical battle overlay 38 remains the exact retail 166,665-byte packed
resource with SHA-256
`93a4179fe3b31a4fffb9fe723f63511f15de5177bbfcbca2529124a4108ffbb1`.
Its decoded 343,948-byte payload remains SHA-256
`ad4586923095715288377caea89f2cd15d70a2f80ef53394e2faec22b2e0b825`.

Only declared canonical 2960 changes from v96. Crescens, enemies,
El-Regulus's model and sound container, standard attacks, Level-1 programs,
Level-2/3 and Infinity deathblows, and every other animation are unchanged.
The complete v97 replacement set and BIN are byte-identical to v95.

## Packaged v97 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v97.bin`:
  695,834,496 bytes / 295,848 raw sectors, SHA-256
  `64816abe1a2b26eee020b2f5416f0384df69277329a0feb486215380844e3166`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v97.cue`: 106 bytes,
  SHA-256
  `e44b987e6975e9c7462a7d5f1c20c2b64db2cd0482e392451fa9d4b3a599090b`
- Manifest `work/mass_driver_v97_stage/manifest.json`: 197,378 bytes,
  SHA-256
  `cc283a215d79f2b30d011bfbf5537925f40df6d08490a9d898f01fed9ea7d56e`
- Replacement aggregate: 128 jobs, 162 declared replacements, 10,870,884
  bytes, SHA-256
  `52611121fef39fc1c7748b9d25973fa50f0616ce34781832bb36f82a216c7d9a`

The BIN identity matches v95 exactly because v97 restores its complete
replacement set. The v97 CUE differs because it names the v97 BIN, and the
manifest records the new release and regression evidence.

## Runtime acceptance

Fully quit DuckStation and launch
`output/Xenogears_PW_CD2_mass_driver_standalone_v97.cue` through
`output/PLAY_MASS_DRIVER_STANDALONE.cmd`. Choose New Game and load no older F1
state or in-game save.

An in-battle F1 state restores its old mounted media and resident canonical
2960. In particular, the captured v96 Dragon state necessarily restores the
invalid relative packet and cannot validate v97. Enter a completely new battle
from v97 media.

In the nearby Dragon encounter, confirm that El-Regulus uses its correct
opening direction at the command menu and that its first attack does not need
to repair an initial `0x0800` quarter-turn. Confirm ordinary attacks still
advance Attack Level, every deathblow completes, enemy turns and victory flow
remain normal, and the game returns to the saved world-map position. Then
confirm the factory Guardian battle, Crescens, and post-battle dungeon return
remain unchanged.

The superseded v96 implementation and its earlier Guardian-only reasoning are
preserved in [the v96 release notes](mass-driver-dungeon-2.73.md).
