# HD dialogue portrait mapping

All 91 supplied asset IDs now have verified native portrait-bank identities.
The generated texture pack is a candidate for emulator testing, not a claim
that HD portraits have already been seen working in the game.

The supplied `assets/definitive/portraits/metadata.json` names `portrait-0` through
`portrait-90`. The site's asset module explicitly maps `portrait-N` to the
original `headN.png`. Each of those 91 original 64x64 images was fetched and
compared pixel-for-pixel with the corresponding retail TIM decoded to RGBA.
All 91 comparisons matched using rounded BGR555 expansion
`(component5 * 255 + 15) // 31`, with transparent alpha only for palette word
zero. All 91 TIMs also matched byte-for-byte across both retail discs.
[Site asset mapping](https://xenoverse.world/assets/xenogearsAssets-Beid9jBB.js),
[example original Fei image](https://xenoverse.world/asset-images/head0.png).

These checks establish the following mapping, without guessing from character
names or treating native portrait selectors as image IDs:

| Identity | Mapping |
| --- | --- |
| Pack ID | `portrait-N`, where N is 0 through 90 |
| Website original | `/asset-images/headN.png` |
| Canonical native TIM resource | `492 + N` |
| Disc 1 physical FAT resource | `492 + N` |
| Disc 2 physical FAT resource | `487 + N` |
| Native TIM size | 4,640 bytes |
| Palette | 256 little-endian BGR555 words at bytes 20 through 531 |
| Indexed image | 4,096 8-bit indices at bytes 544 through 4,639 |
| Image upload size | 32x64 VRAM words, giving 64x64 texels |

The detailed evidence is pinned in
`modules/definitive/content/portrait_sources.json`: each record includes the
original URL, original-file hash, original RGBA hash, native TIM hash, native
selectors, and computed index/palette hashes. This registry contains metadata
and hashes rather than original game image data.

The local Noah implementation at
`work/noah-decomp/NoahLib/field/fieldScriptSupport.cpp` has a 90-entry
`portraitMapping` table. For example, selector 1 maps to bank 6 (Elly), selector
5 maps to bank 23 (Rico), selector 3 loads separate Bart banks 19 and 20 for the
two facing directions, and selector 27 similarly loads Sigurd banks 50 and 51.
The loader reads directory-local file `0x46 + bank`; the shared directory
resolver confirms canonical `492 + bank`. The loader uses three cached VRAM
slots at y=0x100/0x140/0x180, with x=0x2C0/0x2E0 for opposite sides. The CLUT
rows are 0xE0 through 0xE5. These historical sources supplied audit evidence;
the active exporter does not import historical code.

The configured DuckStation executable reports version 0.1.11515. Its matching
upstream tag points to commit `f1e08937459c463f586bdb9cd9c1c9ad55aeb262`.
The exporter follows that version's XXH3 hashing of the indexed upload and
the full 512-byte palette, with this full-upload candidate name:

```text
texupload-P8-INDEXHASH-PALETTEHASH-32x64-0-0-64x64-P0-255
```

For native Fei bank 0, the candidate is
`texupload-P8-9B4F48508CD98C87-E6EE9AB7B8BBFAFA-32x64-0-0-64x64-P0-255`.
Source width is measured in VRAM words; the subtexture width is expanded to
texels. Full-palette matching is explicitly supported by the versioned
implementation. No palette contents or VRAM coordinates are guessed from
the HD image. [Versioned texture-cache implementation](https://github.com/stenzek/duckstation/blob/f1e08937459c463f586bdb9cd9c1c9ad55aeb262/src/core/gpu_hw_texture_cache.cpp).

`modules.definitive.portrait_pack.export_pack(path, output, read_disc)` creates
a standalone sidecar with both serial directories (`SLUS-00664` and
`SLUS-00669`), their replacement PNG files, alias configuration candidates,
instructions, and a manifest hashing every emitted payload file. Its
`read_disc` callback accepts canonical file IDs from either checked retail
disc. Source pack and output directories cannot overlap. Existing output
files are not overwritten, and every native hash and source image is checked
before export starts.

The conversion keeps decoded RGBA bytes and dimensions identical; no image
is resized or edited. The actual pack generated 91 PNGs per serial and 89
unique aliases per serial. An identical native texture with identical HD
pixels shares an alias. Different HD pixels for one native texture cause a
hard error instead of silently choosing one. Transparent bank 90 is retained
as a PNG but does not receive an alias.

The successful standalone audit export is at
`builds/definitive-audit/texture-pack`. Seven exporter tests cover exact RGBA
preservation, full-upload hashing, native identity rejection, pack IDs and
path validation, output isolation, dimensions, transparency, and duplicate
conflicts. The exporter uses the pinned dependency `xxhash==4.0.1`.

Emulator validation must still confirm that portrait uploads remain tracked
as the full expected writes in the tested scenes. Draw cropping, the two
asymmetric portrait pairs, cache-slot reuse, palette changes, and Disc 2
transitions need actual display evidence. Menu/battle portraits use separate
resources and are outside this dialogue pack. DuckStation documents a dump
and visual verification workflow and supports configuration aliases for
replacement images. The generated pack has not changed the user's emulator
configuration or installed itself. [DuckStation Texture Replacement guide](https://github.com/stenzek/duckstation/wiki/Texture-Replacement).
