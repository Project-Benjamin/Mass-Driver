# Mass Driver Dungeon 2.93 - Defense Archive signal override

V117 adds the supplied `screenshotz/7.png` as the first visible report in the
Defense Archive video. The disk now opens with an unauthorized FZN broadcast
from correspondent Jonas Vale, then resumes the existing six-part ZBC archive
with Celia Ren. The ordinary `Video Disk` item, pickup sound and receipt,
inventory-full retry, insert/cancel prompt, replay behavior, console frontage,
modal still timing, and post-playback cleanup introduced in v116 are retained.

The broadcast is authored fiction within the mod. FZN, Jonas Vale, ZBC, and
Celia Ren are presentation devices rather than canonically named Xenogears
broadcasters or people. Their reports are written to fit late-Zeboim's
political collapse without claiming that this exact recording exists in the
retail game.

## New opening report

The first image transaction uses dialogue block 35:

```text
FZN SIGNAL OVERRIDE / 6081
JONAS VALE, CORRESPONDENT

The government is going to
destroy this country.
Every emergency decree
protects only those in power.

They call our hunger order.
They call our silence peace.
If we wait, there will be
nothing left to save.

It is time for the people
to revolt against the
government.

END UNAUTHORIZED SIGNAL
ZBC ARCHIVE RESUMES
```

The text is explicitly a recorded dissident broadcast, not a present-day party
instruction. After its final page, playback proceeds directly to the unchanged
ZBC sequence: social collapse and wealthy escape plans, falling birth rates,
war-driven displacement and famine, riots, hostility toward Miang, and the
initiating nuclear launch and retaliation.

## Media mapping and playback order

The new source is center-cropped without stretching, resized to `320x224`, and
encoded as a 143,380-byte PlayStation 16-bit direct-color TIM.

| Playback | Report | Source | Field file | Canonical resource |
| ---: | --- | --- | ---: | ---: |
| 1 | FZN signal override / Jonas Vale | `screenshotz/7.png` | `0x09` | 2474 |
| 2 | ZBC Evening Report / Celia Ren | `screenshotz/1.png` | `0x03` | 2468 |
| 3 | ZBC Health Desk / Celia Ren | `screenshotz/2.png` | `0x04` | 2469 |
| 4 | ZBC World Desk / Celia Ren | `screenshotz/3.png` | `0x05` | 2470 |
| 5 | ZBC Capital Live / Celia Ren | `screenshotz/4.png` | `0x06` | 2471 |
| 6 | ZBC Political Desk / Celia Ren | `screenshotz/5.png` | `0x07` | 2472 |
| 7 | ZBC Emergency / Celia Ren | `screenshotz/6.png` | `0x08` | 2473 |

The nonsequential selector order is deliberate: `0x09, 0x03, 0x04, 0x05,
0x06, 0x07, 0x08`. Canonical resources 2468 through 2473 remain byte-identical
to v116, while new canonical 2474 contains only the seventh TIM. This preserves
the established six ZBC resources and inserts the new report through event
ordering rather than renumbering old assets.

The new source and encoded identities are:

```text
screenshotz/7.png
size: 2,479,029 bytes
SHA-256: bbf4b2067f6ddeb5c033a8f38dab39fce35cc1737bac10f90e0692503f6ab0d9

canonical 2474 TIM
size: 143,380 bytes
SHA-256: 48602252cec536677dc251ee9d3e87d132243721939a42373e51bc06a20f0b8f
```

Each of the seven reports keeps the v116 transaction contract: `FE9D` commits
the still, the mode-3 modal caption remains open above it until the player
advances, and only then does `FE9C` fade that image. The retail Lighthouse
projector sound `0xF9` accompanies playback, and donor file `0x48` remains the
cleanup frame before camera, screen, input, and player control are restored.

## Canonical delta from v116

Only two canonical-resource facts distinguish v117 from v116:

| Canonical resource | Change |
| ---: | --- |
| 1358 | Target 376 adds dialogue 35 and schedules the new `0x09` image transaction before the six retained ZBC transactions. |
| 2474 | New 143,380-byte TIM generated from `screenshotz/7.png`. |

Canonicals 2468 through 2473 are byte-identical to v116. All other declared
payloads are also byte-identical. The rebuilt target-376 evidence is:

```text
canonical 1358 bundle
size: 139,404 bytes
SHA-256: d5d29db88dcfdf519a149af9f208d80cd85f7cecbaa97617e7d570442ffe1369

decoded field script
size: 4,974 bytes
SHA-256: 2a1cd29e4dbd8ee098c78214bbbb20d58493449605bb190a5127882b3fbd24d8

decoded dialogue
size: 7,007 bytes
SHA-256: cb2bb6a16ecb38c7db8f96ce16cde3b89711c8ca647b1c9875dc399f96f8149e
```

## Emulator acceptance checklist

A state captured with target 376 resident keeps its old field script. Mount
v117, fully leave the Defense Archive, and re-enter it before testing. A
cold-boot v117 New Game remains the authoritative complete-acceptance path.

1. Confirm that acquiring the disk still awards ordinary item 109, plays sound
   `0x37`, shows `Received Video Disk`, and leaves the damaged-disk repeat line.
2. Confirm that the southeast computer still reports no media when item 109 is
   absent and offers `Insert disk` / `Cancel` when it is present.
3. Choose `Cancel` and verify immediate normal control with no playback side
   effects. Then choose `Insert disk`.
4. Confirm that `screenshotz/7.png` appears first with the FZN / Jonas Vale
   report, including the statement that the government is destroying the
   country and the call for the people to revolt against it.
5. Advance the FZN report and confirm that the six Celia Ren reports follow in
   their existing `1.png` through `6.png` order.
6. Leave each caption open and confirm its image remains visible. Verify that
   advancing fades only the current frame before loading the next one.
7. Advance the final ZBC emergency report and confirm that cleanup returns Elly
   to the room with normal camera and input. Replay the disk once.
8. Check the other six physical console banks and both Defense Archive doors;
   the new media must not alter their aligned frontages or progression roles.

No live-emulator acceptance result is claimed here. The extraction result below
is a structural package audit.

## Packaged v117

```text
BIN:
output/Xenogears_PW_CD2_mass_driver_standalone_v117.bin
size: 696,979,920 bytes
raw sectors: 296,335
SHA-256: 56b0310986d95c7cebe574b34978c1d484c26270bb04181eec69b2e29592fbe2

CUE:
output/Xenogears_PW_CD2_mass_driver_standalone_v117.cue
size: 107 bytes
SHA-256: 09ebbfa5066bb030d93b6177f4762dcf19b36233848b9d026fdc5ccbdf248480

staging manifest:
work/mass_driver_v117_stage/manifest.json
size: 224,079 bytes
SHA-256: 832964147b4e5c8a7aa12c28d29f7ad0576434e2a2aa8707762511213c4b7709

build inventory: 137 jobs / 173 replacements / 12,401,564 bytes
canonical-order aggregate SHA-256:
fb297250c3e13d4117660bb5081d68536b927f6d0068a7a0df963b46686079b5
packaged payload extraction: 173 / 173 exact
audit scope: structural package audit
```
