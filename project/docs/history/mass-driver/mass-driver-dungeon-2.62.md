# Mass Driver v85 El-Regulus name and subway terminal correction

V85 fixes Elly's Omnigear name in the fixed-cell initial GameState record.
The separator byte was `0x13`, which the runtime renders as the numeral `3`,
producing `EL3Regulus` in the Repair Bot's Gear-items screen. The byte is now
the retail hyphen glyph `0x1A`, so the runtime name is `El-Regulus`.
Canonical 2595 is 9,048 bytes with SHA-256
`aefb06e0c4e4ef508dab80fbcdc3005449cd2bcf8432fb9f20d7f94d4e2caea3`.

Target 721 also no longer presents its train archive as a second Repair Bot.
The archive is now a compact, texture-free Zeboim terminal using static model
15 and node 30 at `(-1114,-88,185)`, with Y rotation `0x0800`. Entity 14 is
only its invisible X-action controller at `(-1025,185)`; it is no-facing and
uses interaction-bound operand `0x0C`. The platform's M-07 service unit remains
the sole visible Repair Bot and retains the shop interaction.

The target-721 release evidence is:

| Resource | Bytes | SHA-256 |
| --- | ---: | --- |
| Field bundle, canonical 2048 | 150,260 | `82f4778367dbde6e2c9749fae9ee77589656a191c9e2e5d5cd1f2594c3e39362` |
| Graphics bundle, canonical 2049 | 319,488 | `8fc521c8500270878422a012a074559a822437bcae682e08681b85d2178ed02a` |
| Header | 896 | `0416a4df29a9d3005f43f402aadd402b4c7dce43f7a6c9d451d7e656e0a07b7a` |
| Model archive | 51,044 | `70b27ae2656a73a4bcc79588bbb193340835b0c8b2384dfc96bc0255f9876feb` |
| Added terminal model | 1,604 | `ea8ba6b044f48b2d5e8c5f23cce0dd3fe7fab7c9082d292fe3296bd74635cf6c` |
| Actor archive | 9,164 | `fc30d26a29d9a98b87f818024d96cd5f1c11189c874d01c972bce5f454367c18` |
| Sprite archive | 63,916 | `764d863a1959f526341f81128cf8aeca2d93a57323162432b8401603f6cec6a5` |
| Script | 1,692 | `cd7b6abdf2efde3f3038f32f2ffede7533cc19dc6d271a04f651ec7e1212e0df` |
| Dialogue | 802 | `9ac63fd3538e58788dd188dafaa17dcfa948e46a77d04d7acad0acacef15573c` |

The packaged v85 artifacts are:

- BIN: 695,293,536 bytes,
  `b206af92c86fa07c3adb2e47eef6cc689649fee4c6b29da442c38b3c4b75a154`
- CUE: 106 bytes,
  `8363970585c93a6e67c7d1e7f64dbe9159e93a064bcb543ef30db8f516f8ed3b`
- Manifest: 186,320 bytes,
  `93df0245b87f08dae77cf8b18f1fc7ee5d3dee7dc59303140a021f6c18e201b8`
- Manifest contents: 126 jobs and 158 declared replacements totaling
  10,392,579 bytes, with canonical-ID-order aggregate SHA-256
  `72a21ab6f229271c162465f3ed95b9fef466f92d0fe2a1fa140887d8b6cc575d`

Relative to v84, only canonical IDs 2048 and 2595 differ; every other
declared replacement is byte-identical.

The final automated suite passes 203 tests and 2,332 subtests with no failures,
errors, or skips.

A cold boot of v85 is required for acceptance. Loading an older in-game or
emulator save state preserves its old GameState name and can also restore a
resident v84 field. Cold boot v85, then enter target 721 from v85 media before
checking both the Gear-items label and train terminal. Runtime visual
acceptance of the terminal remains pending. V84's superseded artifact details
are retained in [the v84 guidance archive notes](mass-driver-dungeon-2.61.md).
