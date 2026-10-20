# Mass Driver v90 opt-in reserve-magazine archive terminals

V90 removes the automatic exposition that interrupted traversal through the
missile reserve. All five magazines now enter silently. Their existing records
remain available from a visible archive terminal that the player deliberately
approaches, faces, and activates with Cross/X.

## Five-room presentation

The reserve route remains:

```text
377 <-> 378 <-> 379 <-> 382 <-> 383 <-> 728
```

Each of targets 377, 378, 379, 382, and 383 uses the same compact,
texture-free Zeboim archive terminal presentation:

- Static field prop: node 22/model 0 at `(500, 0, 0)`
- Interaction controller: entity 7 at `(420, 0)`
- Interaction: facing required, half-width `0x28`, Cross/X
- Content: that room's existing dialogue block 0
- Persistence: repeatable, with no progression-state write

Targets 377, 379, 382, and 383 no longer invoke dialogue during their entry
scripts. Target 378 already had the intended silent-entry terminal behavior;
its canonical 1362 bundle is preserved byte-identically from v89. The text in
all five records is retained: the reserve inventory and lost guidance network,
the 6083 release log and 6079 political mail, Aron's severed target link, the
failed shelter call log, and Elly's final tombstone reflection.

This presentation changes only how the player elects to read the exposition.
The automatic full-width north and south passage boundaries remain active, and
all 30 warheads retain their placement, supports, and collision. Traversal in
either direction does not require a button and does not trigger narration.

## Packaged delta from v89

Exactly four declared canonical resources differ from v89: 1360, 1364, 1370,
and 1372. They correspond to the four rooms that previously presented their
records automatically. Canonical 1362 / target 378 remains 93,824 bytes with
SHA-256
`40c16f67d39a075718ba612013b22374ce2bb80dd3f0004aa5da9a8abd4aca58`.
Its unchanged 3,494-byte script has SHA-256
`e1e36173bf5bf9cf7073b2588e58e7f62d1f8aefa1a35d18ec269a00ed427ca6`,
and its unchanged 736-byte dialogue payload has SHA-256
`fd19f01c182c3f034d90b2ae27a50656599575f1e3037e52debade0b30aa2270`.

The rebuilt resources are:

| Canonical | Target | Bundle | Script | Dialogue |
|---:|---:|---|---|---|
| 1360 | 377 | 93,356 bytes; `654145fc0415d6c5e530b0a36170c9f84d2c597fc8043f25c8b5c1d826e310f9` | 3,494 bytes; `5528ff596e3f91998bb80d02b886156d8bcd092c7574cecc9967c84582f30cbb` | 236 bytes; `58fdde3162c171100cb4982ed8c9c6ecd45cad3866c5cba700926da1a6228719` |
| 1364 | 379 | 93,364 bytes; `dc7af0485661a8981248407a48032150905cdb3ae24cf33895395f38403375e0` | 3,494 bytes; `636201caaaf990816b0f421fd06a96b0589bdbd51ed9b240c78a18d776a53a62` | 238 bytes; `5910fc39a0cc8c331f0afc1ef2e72f05c212aa8ecc7542e666649bfd93efca96` |
| 1370 | 382 | 93,312 bytes; `89550821cf4a6d3a46f19da59780c6d5dac6ee562b7b29960f0861d0790da05f` | 3,494 bytes; `398ec93ffccaf05f7aef9f333761592f519b241decfea054b440ba3390753f47` | 205 bytes; `c4972f16466276880ab4382c2cd93c2cf5f2835540b2a71928a0c0c348bd2bc8` |
| 1372 | 383 | 93,352 bytes; `dc7e6485affba2dbe15f8f15b7ac5ff78da7d65586ca25bc7688111400bb1c21` | 3,494 bytes; `d293c223717ad959a65f321a626ffd1a61debae63aa60761395336a4375e0f76` | 238 bytes; `5ca5d9105a71ab7f80fca26f513f337c92636570da2cce413e14e9c2ae3a3e0f` |

Every other declared replacement is byte-identical to v89. In particular,
V89's native El-Regulus target-facing correction and Citan-left-the-Gears
dialogue remain intact, as do the Gear battle, deathblows, power interlocks,
other archive terminals, warhead geometry, and final launch sequence.

## Packaged v90 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v90.bin`: 695,277,072 bytes / 295,611 raw sectors, SHA-256 `f5858cc302778547cd58a7a33b107405741db37d7e2362bf953e8894a0eb29ad`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v90.cue`: 106 bytes, SHA-256 `80fb194ea647d7d74bbbedde5ab5b19481797c1206f5938a0823ffabd6005891`
- Manifest `work/mass_driver_v90_stage/manifest.json`: 189,601 bytes, SHA-256 `7c63af98c085e3a86803965c272b3107fd16a95fd73f0f3d2ebd474d1785d982`
- Replacement aggregate: 126 jobs, 158 declared replacements, 10,381,828 bytes, SHA-256 `b6ef1c67b57c3724227bda1ff324a0bf8545eef6b84335ab1efc4d5519a28ef7`

The complete automated suite passes 204 tests and 2,347 subtests with no
failures, errors, or skips.

## Runtime acceptance

Fully quit DuckStation, boot
`output/Xenogears_PW_CD2_mass_driver_standalone_v90.cue`, choose New Game, and
load no older F1 state or in-game save. A v89 state restores its old mounted
disc and resident field scripts, including the automatic missile-room
narration, so it cannot validate this change.

After the Guardian battle, enter target 377 through the Defense Archive's west
bulkhead and traverse all five reserve magazines in both directions. Confirm
that no dialogue appears on any room entry or north/south passage. In each
room, find the same compact console on the east side, approach it from the
aisle, face it, and press Cross/X. Confirm that the room's complete existing
record opens, that it can be opened again immediately, and that reading it does
not change progression. Finally, confirm that every automatic boundary still
works and that all six warheads in each room remain visible and solid.
