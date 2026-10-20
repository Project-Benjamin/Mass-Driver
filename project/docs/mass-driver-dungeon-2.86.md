# Mass Driver v109 authentic subway Zeboim station

V109 replaces the visible H-10 archive relay inside target 721's stationary
subway train with field 373's authentic model-7 Zeboim freestanding station.
The train's repeatable 6072 archive record remains on the established Cross/X
interaction, and Repair Bot M-07 remains outside the train with both complete
shop menus.

## Static station and retained interaction

The exact retail station model is appended as field-721 model 15 and placed by
static node 30 at `(-1011, 18, 225)`, yaw `0x0E00`. Its controls face east and
its visual centre is `(-1025, -164, 185)`, aligned exactly with the retired
H-10/controller point. Its world bounds are
`(-1065, -986, -240, -88, 146, 224)`, and its base meets the train floor at
`y=-88`. This final placement corrects the donor-pivot occlusion found during
live validation.

Entity 14 no longer initializes or renders H-10. It is now an invisible,
stationary, no-facing controller at `(-1025, 185)` with the same repeatable
action script and no item award or progression write. The authored heading is
now `TRANSIT ARCHIVE TERMINAL`, while the complete launch-team mail remains
available on demand. M-07's separate entity, actor bank, item catalog, and Gear
parts catalog are unchanged.

## Native bank-1 texture and palette reuse

V109 retains field 721's registered local bank-1 upload at `(768, 0)` and uses
it as a static texture carrier. The same lossless 21-island, 80-by-64 atlas used
for the reserve-magazine stations is copied into the first bank-1 image; its
SHA-256 is
`a6ee4c693587c5f68d8777ef60007ca178a744cad66b9d92ea5a85dfe424f129`.
The relocated station selects texture pages `0x008C/0x00AC` and CLUT `0x7A00`.

Field 721's model 14 was the only model using palette row 488 and its associated
32-by-40 indexed texture. V109 moves that texture into unused bank-1 rows
64 through 103 and remaps its 28 colours into unused entries on row 489. The
freed row 488 then holds the station's complete, exact 256-colour retail
palette. Model 14's appearance is preserved, no graphics upload is appended or
resized, and the 319,488-byte MIM keeps its native 37-upload inventory.

The relocated station model is 2,524 bytes with SHA-256
`4b95caefc895985f71f324556d9c5ab08f38f849ad52e7612562e9c9d3af27dc`.
The resulting model archive is 51,964 bytes with SHA-256
`7e73dca3b7fb6ddc047209f4a4a6670ef6dbcd9983b93e916b20501e13f0d3e2`;
the final field-721 graphics SHA-256 is
`d4cf59e33b30df0c03c0c2cd584d942fc6997b7cec2bd79b3d4cbe4fee512aa3`.

## Exact v108-to-v109 delta

The manifest still contains 166 replacements across 130 jobs. Exactly two
canonical resources change from v108:

```text
2048  target 721 field bundle
2049  target 721 graphics
```

Canonical 2048 is 195,716 bytes with SHA-256
`55b8eb437b94cfcf4c3c1da3abfde2916a25e2b66b04e71b0b9b422f8042473a`.
Canonical 2049 remains 319,488 bytes and has the graphics hash above. The other
164 declared replacement payloads are byte-identical to v108. No route,
walkmesh, subway return spawn, M-07 shop, reserve-magazine station, battle, or
finale behavior changes.

## Runtime acceptance

Target 721 must be loaded from v109 media. A resident v108 or earlier field
state retains H-10 and cannot validate the new static station. Cold-boot v109,
or completely leave the subway and re-enter it from v109 media, then confirm:

- the authentic freestanding station is visible inside the train and H-10 is
  not rendered;
- Cross/X at the station opens the complete repeatable archive record and
  awards no item;
- M-07 remains visible outside, and both Item and Gear-parts menus can be
  opened, browsed, canceled, and reopened; and
- returning from target 363 still lands clear of the subway exit trigger.

## Packaged v109 identities

- BIN: 696,561,264 bytes, 296,157 raw sectors, SHA-256
  `f47795904433df064b6eb4d2a48cbc9f324847ad047ca791850643d5f3b7d60d`.
- CUE: 107 bytes, SHA-256
  `74f2ce5120bd1cfdddfa380058d90eeb7ff6331d7281e5e56a2037d9d55dca74`.
- Manifest: 209,705 bytes, SHA-256
  `262259fd5049f2e7157176e5698ae89e8b814a347f313b41e218bb0e4d1c9115`.
- Declared replacements: 166 across 130 jobs, totaling 11,505,848 bytes;
  canonical-ID-order aggregate SHA-256
  `d62d8258cb4f4a1a7fe0d971034d4b8fd98a110dc80682d0b0db602cfc8ec31b`.

V94's now-superseded H-10 transplant remains documented in
[the v94 release notes](mass-driver-dungeon-2.71.md). V108's retained native
reserve-magazine station allocation and packaged identities remain documented
in [the v108 release notes](mass-driver-dungeon-2.85.md).
