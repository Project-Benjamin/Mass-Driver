# Mass Driver v108 native-allocation Zeboim stations

V108 makes the field-373 Zeboim station transplant runtime-safe in reserve
magazines 377, 378, 379, 382, and 383. Its model, sampled texture pixels, full
palette, placement, controller, and repeatable room records remain unchanged.

## Root cause and native-layout repair

V107 appended structurally valid texture and palette uploads. They replayed
correctly in the offline MIM audit, but they were outside field 673's registered
native runtime allocations; the live field/actor VRAM allocator did not retain
them.

V108 losslessly repacks the station's 21 conservatively selected used 8bpp
islands into the exact native fourth upload at `(512, 192, 40, 64)`. That
40-word-wide block provides 80 indexed texels per row; the 4,288 occupied
texels fit within a 78-by-62 bound without resampling or palette conversion.
The complete 256-colour donor palette moves from source row 486 to native row
488. The model's UV, texture-page, and CLUT selectors point to the repacked
pixels and exact palette.

The field-673 graphics remain exactly 102,400 bytes and contain only the four
native uploads:

```text
(0,   480, 256,   9)
(320,   0, 128, 256)
(448,   0,  64, 128)
(512, 192,  40,  64)
```

There is no appended or resized upload. The final graphics SHA-256 is
`395e3907406464ec1746cba8097008a19eebf05babf9e19a34bdef71d9832f50`;
the relocated station model SHA-256 is
`793603ccbe854180cc28a69810696bf3713a394168f06454a83c20693846a015`.

## Exact v107-to-v108 delta

The manifest still contains 166 replacements across 130 jobs. Exactly ten
canonical resources change:

```text
1360/1361  target 377 bundle/graphics
1362/1363  target 378 bundle/graphics
1364/1365  target 379 bundle/graphics
1370/1371  target 382 bundle/graphics
1372/1373  target 383 bundle/graphics
```

The other 156 replacement payloads are byte-identical to v107. No scripts,
dialogue, room backgrounds, warheads, walkmesh, mail, collision, or entry
behavior change.

## Live runtime acceptance

The station was cold-loaded from final v108 media after leaving the resident
room and was visibly correct. The captured state is
`work/runtime_capture/station_v108_lossless_final_live.sav`, SHA-256
`f35efb37bb9011ebfe65b3afb71b5184be9ecd4896934627c62596b7e8a1b088`.

At live VRAM base payload offset `2104792`, all 64 atlas rows matched the
lossless packed payload and the CLUT matched the exact donor palette. The
original user slot was restored after capture; its restored SHA-256 is
`5e5e2332004da7e1f3a52ddf57c9a43579026ed6b93b76ce38972a7fb278900f`.

A resident v107 state restores the allocator-unsafe appended layout and cannot
validate v108. Leave the room and reload it from v108 media, or use a fully
quit cold-boot New Game.

## Packaged v108 identities

- BIN: 696,558,912 bytes, 296,156 raw sectors, SHA-256
  `d081ce3f132f20b3ec44263eb7263848dd15a54e6d0aebfeb11764d542d1ceaa`.
- CUE: 107 bytes, SHA-256
  `e2b76438b59a9cba37413becc8c37ba87d174b5d5a051e078f3c9f9a7b96b2df`.
- Manifest: 208,967 bytes, SHA-256
  `30dce614c21064ba74f311061d934ec566af04cb378306a9f2322e2b393de6bd`.
- Declared replacements: 166 across 130 jobs, totaling 11,502,980 bytes;
  canonical-ID-order aggregate SHA-256
  `8f02ab6ce01784766a37e23ee5a1aca8aed637bcb03ce820d9a33694b5ed39eb`.
- Regression suite: 220 tests and 2,822 subtests passed with no failures,
  errors, or skips.

The superseded v107 artifact identities and appended-upload audit remain
preserved in [the v107 release notes](history/mass-driver/mass-driver-dungeon-2.84.md).
