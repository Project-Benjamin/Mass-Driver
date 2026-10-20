# Mass Driver v87 hanging-terminal geometry correction

V87 corrects the remaining Auxiliary Grid room interaction mismatch. Both sections of the floor-mounted control bank remain Auxiliary Grid switches: entity 12 at `(-31, 165)` and entity 13 at `(110, 117)` both present switch/status dialogue 1. The optional mail now belongs only to entity 16 beneath the actual beige/green-lit overhead-arm Guidance Archive terminal, where it presents dialogue 0 and Directive 0320.

## Live evidence and corrected geometry

The user's latest v86 state was inspected without changing its saved position or progress. Its SHA-256 is `c57d3c3336e75f11190aa0218326d657a8f4c096d9a9505d2c5ca0a3b6aba519`; it mounts v86 and contains the exact resident target-361 script SHA-256 `ca38838eb8df1178ef47921b36bd8af7fc341cc77aaac47f656eeb626d1c8a44`. That script placed entity 16 at `(-40, 97)` on triangle 7, which reproduced the mail in an invisible empty-aisle hotspot. Standing beneath the visible hanging computer produced no dialogue.

The visible computer is static header node 44/model 7 with yaw `0x0200`. Its corrected no-facing, bound-`0x08` controller is centered at `(-31, -105)` strictly inside walkmesh triangle 26. The captured operator approach was `(-30.75, -104.82)`. Its effective 32-unit per-axis reach leaves a 206-unit z gap from the left floor zone and a 33-unit x gap from the right floor zone (the right-side z gap is 114), so neither desk-switch action overlaps it.

This corrects v86's mistaken node 27/model 2 identification; the floor-switch scripts and all archive text remain unchanged.

## Packaged delta

Only canonical ID 1328 differs from v86. All other declared replacement resources are byte-identical.

- Target-361 bundle: 89,856 bytes, SHA-256 `4534da671ab007a29131e69d1869d78f68bdc1ebe62c5c275cd4277cdec29f73`
- Target-361 script: 2,193 bytes, SHA-256 `6f6e9dc53f3929c5a80c6e8b53269017be062823ce67b82196b33db4c69b9dc3`
- Target-361 dialogue: 1,387 bytes, unchanged SHA-256 `980551a72dd726363dd8fe6126ce5cf6c74f68c15d53b02e0d9c0ca6849e31ae`
- BIN: 695,293,536 bytes / 295,618 sectors, SHA-256 `314d30de4d77ec2383aa865a741d8253c475b57581994da656fc686a30ace0e5`
- CUE: 106 bytes, SHA-256 `9c70fa98a3528c82ecebf9dbb4b493974d4aa97b382ed65fb8f57a6e8dea4e50`
- Manifest: 187,073 bytes, SHA-256 `e4dbe810a2a029302d5f3ee9e735b49f787b058b089bf4649ec5e5c2193f2b41`
- Replacement aggregate: 126 jobs, 158 replacements, 10,392,651 bytes, SHA-256 `705b40523fa34a6d64b27c8ebc0eb51a788277e5dd3fd520dc75f05eb95e5298`

The focused Auxiliary-room suite passes 4 tests and 33 subtests (95 tests deselected). The complete suite passes 204 tests and 2,342 subtests with no failures, errors, or skips.

## Runtime acceptance

Fully quit DuckStation, boot `Xenogears_PW_CD2_mass_driver_standalone_v87.cue`, choose New Game, and load no older F1 state or in-game save. In target 361, verify both floor-console sections operate only the Auxiliary Grid, then press X directly beneath the beige/green-lit hanging computer and verify that it opens the Guidance Archive mail and Directive 0320. The captured v86 state restores the obsolete resident script and cannot validate v87.
