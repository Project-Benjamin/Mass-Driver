# Mass Driver Dungeon 3.09 - Central Control finale restoration

V148 is the current frozen package. The route now ends in Mass Driver Central
Control, target 728, immediately after the five nuclear reserve magazines. The
red service tunnel at target 388 and both Krelian-room presentations at target
507 are absent from the active route and package. No Krelian laboratory asset
is used by the V148 finale.

## Finale contract

Central Control entity 13 remains the main-computer interaction at `(-54,94)`
on walkmesh triangle 16. Its no-facing operand `0x08` gives 32-unit effective
reach and includes the accepted stance near `(-27,84)` without overlapping the
east archive reader or native return door.

The first X interaction is Elly's subjective Zeboim-era memory. Only Elly
perceives Miang, the adult Launch Director, and the helmeted Systems Officer;
Emeralda sees an empty room and Elly reacting to people who are not there. The
memory ends in Central Control without launching. On the second X interaction,
Citan enters through the native east door, follows the checked Central Control
route, joins the conversation, and assists with the complete local capsule
launch. The guarded retail Mass Driver world-map sequence then removes
temporary Citan and returns Elly and Emeralda outside.

The apparition rendering defect came from importing actor banks and VRAM pages
without their native component-04 sprite archives. V148 appends the exact donor
component-04 entries as well as their actors. Miang is 22,028 bytes with
SHA-256 `8f0167062e8183f6a82feeab1b3af7b5ff8a40e49d7cd68e4a9e35e75e6862b7`;
the Systems Officer is 18,444 bytes with SHA-256
`b7786a12937e97d3f8c2248cb1cb62bd992a3480bb1c37cc6ca9c1456a3f1441`;
and the Launch Director is 16,524 bytes with SHA-256
`c0bc9d791b259ac9a71b5940188b5c2b79f4098118e295e60444900fa787c2c3`.
Their header mappings are `(320,256,0,0)`, `(384,256,0,0)`, and
`(448,256,0,0)`. The actors therefore use their complete retail sprite
definitions instead of collapsing into pixel-sized dots. No bitmap artwork was
drawn or regenerated.

## Frozen Central Control identity

Target 728 canonical 2062 is 126,524 bytes with SHA-256
`237d9a0535e4dfc40734fe5995b39546668336b75e7581d24a3d66bf512c9ae3`.
Its prepared 1,088-byte header has SHA-256
`b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31`;
the packed 1,088-byte header has SHA-256
`9512cf649f6834c5cd641684f708bf8d57ae34c48660acaeeb8e57790a082740`.

The 18,640-byte actor component has SHA-256
`2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538`.
The repaired 67,668-byte component-04 sprite archive has SHA-256
`e09e0ca20423abd18fbbbee63c37b47e0d89c8a7a1cb32a61d54d37de452b805`.
The 3,510-byte script has SHA-256
`7e4e3903b5501b9116c924dd78124f99a1d1b6784e0a0abc16650934427fd96e`;
entity 13 script 2 begins at PC `0x03CD`, is 1,038 bytes long, and has SHA-256
`4a2ea37a9cf5868249b9640c73117f32931f67e7f51f606b5c9aab383d379207`.
The 5,044-byte dialogue component has SHA-256
`c5300fd84da598f56215c5561feee6932de3f726524b53704cb56fa762503006`.
Canonical 2063 remains the exact 180,224-byte native Central Control graphics
payload, SHA-256
`4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28`.

The standalone GameState canonical 2595 is 9,048 bytes with SHA-256
`aefb06e0c4e4ef508dab80fbcdc3005449cd2bcf8432fb9f20d7f94d4e2caea3`.
It uses target 728 as the hidden cold-boot gateway. The guarded launch-return
field 617 canonical 1840 remains 71,180 bytes with SHA-256
`d35a13ab5be99c4ebb6e3934bd4ab0c00613839d810c2a4984dae70adbdefb26`.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v148.bin
size: 696,130,848 bytes / 295,974 raw sectors
SHA-256: c4bd92a10318d60bb4d2f2c9194eb049076124fedf9046a8922f6e3201ac80ad

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v148.cue
size: 107 bytes
SHA-256: 52d578682104510a1e36aa1577fbaef93f03e10353253e0e54e5a9ac3396237a

manifest: work/mass_driver_v148_stage/manifest.json
size: 237,088 bytes
SHA-256: 4bce2825fb5400843706c004848bf5108dd46eb232729b1dca56f3fb79457fa1
jobs / replacements / bytes: 136 / 169 / 11,804,612
route fields / directed edges: 33 / 66
replacement aggregate: 521480cc4c833326e0c598d03d49582f85cb3dd63e0904f62ebb9786505bd5a4
framed aggregate: 3363c5f9e03cc2b0d9bf019809cb835cf89b41e12fec8c4aacea1bfe791a92a4
```

## V147-to-V148 delta and validation

The declared stage delta removes canonicals 1382, 1383, 1620, and 1621 and
changes canonicals 2062 and 2595. The exhaustive FAT payload delta is exactly
17, 22, 1382, 1383, 1620, 1621, 2062, and 2595. Canonicals 17 and 22 are
regenerated FAT bookkeeping; 3,715 of 3,723 extractable payloads are
byte-identical.

There are 2,599 changed FAT descriptor tuples. Canonicals 3715 and 3723 remain
unchanged, and no entry kind or directory membership changes. All 169 packaged
replacements re-extracted byte-for-byte, all 5,846 replacement sectors and the
boot sector passed MODE2/Form1 validation, and the exhaustive FAT audit passed.

The authoritative V148 suite passed 262 tests / 2,679 subtests in 19.733
seconds with exit 0. Fresh user-driven visual acceptance of the restored
Central Control memory, full-size apparition actors, second-interaction Citan
arrival, local capsule launch, and guarded return remains pending. The preferred
near-finale state is
`work/runtime_capture/near_final_v148_from_v108_vault1.sav`, 1,701,664 bytes,
SHA-256
`25ae117a723fb80aafd5348806d658aa1082ab7333482c209249e2ded994c3de`.
It has historical V108 field 377 resident, flags `0x0033` (authorization and
Guardian complete; launch, Citan, and memory clear), Elly and Emeralda only,
and no active dialogue or scripts. Walk north so every later vault and Central
Control load fresh from V148. It is focused finale coverage, not cold-boot
whole-release acceptance.

The authorization-console focused
state `work/runtime_capture/guardian_v148_authorization_console_central_finale.sav`
is 1,745,341 bytes with SHA-256
`e2dbea2efb984b714fa92a83fb4253aaba56170a019d1d1f680ccb16cc9e182e`.
It mounts the exact V148 CUE, has the exact resident FAT, contains repaired and
even canonical 29, and has none of targets 728, 388, or 507 resident, so Central
Control will load fresh. Its warm field-376 script is still V143; exit and
reload that room before using the state to validate field-376 changes. This is
focused diagnostic coverage, not cold-boot whole-release acceptance. Ask the
user to navigate and press controls; do not automate emulator input.
