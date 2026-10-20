# Mass Driver v107 Zeboim freestanding stations

V107 replaces the misleading reserve-magazine archive cylinder/service
pedestal with option B from the retail-terminal audit: field 373's authentic
Zeboim freestanding station. The change applies consistently to targets 377,
378, 379, 382, and 383. Room entry remains silent, every existing mail record
remains repeatable, and the retained entity-7 controller still opens it with
Cross/X from the east-side approach.

## Authentic retail transplant

The selected object is exact retail field-373 static node 44/model 7, from the
inactive Zeboim control room. It is transplanted into retired field-673 model
slot 0 and static node 22, lowered from its original hanging installation to
stand on the magazine floor, and rotated so its controls face the player.

- Placement: `(486, 106, -41)`.
- Y rotation: `0x0600` (135 degrees).
- Visual center: `(500, -76, 0)`.
- Controller: entity 7 at `(420, 0)`, facing-required, repeatable dialogue 0.
- Source model SHA-256:
  `c7791afbe919aece2096c863e0cdff9677b091872e147d10bdbbdc37799d6c1c`.
- Relocated model SHA-256:
  `97fa8541e5cdb827212b42bf808b6560dfd46bf7007d1d9947ba74f8e7ded1d0`.

The relocation changes only the model's texture-page and CLUT selectors. Its
exact retail texels and 256-colour palette are copied into two checked,
otherwise-unused VRAM rectangles:

- texture: source `(448,192,65,64)` to target `(576,192,65,64)`;
- palette: source `(0,486,256,1)` to target `(256,486,256,1)`.

The original field-673 graphics remain an unchanged prefix. Every VRAM word
outside those two destination rectangles is byte-identical, and the room
background, walkmesh, six warheads, collision, dialogue, and scripts are
unchanged. The station render retains its original brown industrial body,
green status lights, red rail illumination, and control screen rather than
acquiring a mismatched silo palette.

## Exact v106-to-v107 delta

The manifest still contains 166 replacements across 130 jobs. Exactly ten
canonical resources change:

```text
1360/1361  target 377 bundle/graphics
1362/1363  target 378 bundle/graphics
1364/1365  target 379 bundle/graphics
1370/1371  target 382 bundle/graphics
1372/1373  target 383 bundle/graphics
```

There are no added or removed resources, no route change, and all other 156
replacement payloads are byte-identical to v106. The five scripts and five
dialogue streams are also unchanged.

## Runtime acceptance

Fully quit DuckStation, launch the v107 CUE, choose New Game, and load no old
F1 state or in-game save. A v106-or-earlier state saved with one of the five
magazines resident retains the older visual in RAM and cannot validate this
release.

For each target 377, 378, 379, 382, and 383:

1. Enter from both directions and confirm no automatic exposition appears.
2. Confirm the field-373 station stands on the east side and visually belongs
   to the Zeboim facility.
3. Approach its visible controls, face them, and press Cross/X.
4. Confirm that room's existing archive mail opens and can be read again.
5. Confirm both full-width proximity exits and all six warheads are unchanged.

## Packaged v107 identities

- BIN: 696,652,992 bytes, 296,196 raw sectors, SHA-256
  `147697121f12360986031e1f17b7eadac7e1c8c3495e6c8f5c47427c04c1e936`.
- CUE: 107 bytes, SHA-256
  `f74b944bcd30df14257faa9fc68215ffa5ebd3d7eb9a4b4d38640f06c841d96e`.
- Manifest: 208,284 bytes, SHA-256
  `1930c564f21f8e2e19938e102dc7c016e056b1fba12eac5b617a2f372a922d77`.
- Declared replacements: 166 across 130 jobs, totaling 11,584,900 bytes;
  canonical-ID-order aggregate SHA-256
  `a1609a31c97af0235a320a198a420f00e0ce89d16927e51f2b57594dc904d733`.
- Regression suite: 220 tests and 2,789 subtests passed with no failures,
  errors, or skips.

All 166 payloads re-extracted from the packaged BIN match the stage manifest
byte-for-byte. The v106-to-v107 raw-disc delta contains 85,518 changed or new
sectors and 177,407,112 differing raw bytes; every changed/new sector validates
as MODE2/Form1 with correct EDC/ECC.

The superseded v106 artifact identities and final-laboratory delta remain
preserved in [the v106 release notes](../../mass-driver-dungeon-2.83.md).
