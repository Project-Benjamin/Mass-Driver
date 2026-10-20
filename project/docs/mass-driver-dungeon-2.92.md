# Mass Driver Dungeon 2.92 - Inventory Video Disk and stable captions

V116 promotes the Defense Archive's optional recording from a field-only flag
to a real ordinary inventory item. Elly can recover the disk from the native
film apparatus, carry it to the southeast computer, choose whether to insert
it, and play six refreshed stills without the image disappearing behind its
caption.

The broadcast is deliberately authored fiction within the mod. `ZBC` and
anchor `Celia Ren` provide a plausible late-Zeboim news frame, but neither is
presented as a canonically named Xenogears broadcaster or person. The report's
events are written to agree with the setting without claiming that this exact
program exists in the original game.

## Ordinary-item contract

The recovered media occupies ordinary item slot 109 (`0x6D`):

```text
name: Video Disk
description: Zeboim archive video disk
```

The apparatus remains entity 26 at `(-75, -162)`, with the checked operator
stance at `(-75, -167)` on walkmesh triangle 157. Its compact `0x04`,
front-facing controller keeps side and rear approaches from triggering the
event.

On the first valid interaction, the field uses ordinary-item award opcode
`0x8C` for item `0x6D`. It verifies the item with the inventory-presence opcode
before committing the persistent event bit. A successful award plays sound
`0x37`, displays the explicit `Received Video Disk` receipt, and then runs the
short Elly/Emeralda pickup exchange.

If the ordinary-item inventory is full, Elly instead says that there is no
room to carry the Video Disk. The success bit is not written, the apparatus
remains available, and the player can make room and retry. This also upgrades
a v115 save whose old field-only disk bit was already set: if item 109 is
absent, the apparatus offers the real award.

After the item is present, the apparatus remains interactive and Elly says:

```text
The other disks are too damaged to read.
```

The disk is not removed by playback. Its actual inventory presence, rather
than the historical field-only flag, gates the computer.

## Computer flow

The southeast computer remains entity 21 at `(264, -165)`, approached from
`(264, -175)` on walkmesh triangle 146. Without item 109 it reports:

```text
ZBC ARCHIVE CONSOLE
NO MEDIA DETECTED

INSERT VIDEO DISK
TO CONTINUE
```

With the disk in inventory, it presents an explicit choice:

```text
INSERT VIDEO DISK?
     Insert disk
     Cancel
```

`Insert disk` starts the recording. `Cancel` closes the choice, releases the
field-input lock, and restores Elly's control without entering playback. The
same choice appears on later visits because the disk remains a carried item
and the recording is replayable.

## Authored ZBC report

All six supplied `screenshotz/1.png` through `screenshotz/6.png` images were
refreshed for v116. Celia Ren anchors the through-line while the desk label and
date advance with the collapse:

| Clip | Caption | Requested subject |
| ---: | --- | --- |
| 1 | `ZBC EVENING REPORT / 6081` | Markets and public services are failing while wealthy families buy private shelters and orbital seats, believing they can escape society's downfall. |
| 2 | `ZBC HEALTH DESK / 6081` | Births have remained below replacement for twelve years; infertility and hereditary illness fuel panic that civilization will not survive another generation. |
| 3 | `ZBC WORLD DESK / 6082` | Foreign and civil wars cause mass displacement, abandoned farms, broken transport, famine, and food lines in virtually every major city. |
| 4 | `ZBC CAPITAL LIVE / 6082` | Riots continue under indefinite curfew while police and military units struggle to hold government districts, food depots, and power stations. |
| 5 | `ZBC POLITICAL DESK / 6082` | The public's anger focuses on Miang, the Prime Minister's adviser, amid allegations that she filters reports and manipulates the choices reaching the leader. Her office denies it. |
| 6 | `ZBC EMERGENCY / 6083` | A confirmed nuclear launch triggers retaliation by other nuclear-armed countries; command links fail, no later broadcast survives, and most of Zeboim civilization ends. |

The sixth report identifies the initiating launch and the retaliatory exchange,
but does not invent a claim that Miang personally signed the order.

## Native still and caption timing

Each source image is center-cropped without stretching, resized to `320x224`,
and encoded as a 143,380-byte PlayStation 16-bit direct-color TIM. The field
continues to address the images through the Lighthouse player's native file
selectors:

| Clip | Source | Field file | Canonical resource |
| ---: | --- | ---: | ---: |
| 1 | `screenshotz/1.png` | `0x03` | 2468 |
| 2 | `screenshotz/2.png` | `0x04` | 2469 |
| 3 | `screenshotz/3.png` | `0x05` | 2470 |
| 4 | `screenshotz/4.png` | `0x06` | 2471 |
| 5 | `screenshotz/5.png` | `0x07` | 2472 |
| 6 | `screenshotz/6.png` | `0x08` | 2473 |

For every clip, `FE9D` commits the still before the mode-3 modal caption opens.
The caption's wait remains inside that image transaction, so the still stays
visible beneath the text for as long as the player is reading it. Only after
the player advances and the dialogue wait returns does `FE9C` fade the current
still. This ordering replaces the earlier flash-then-black behavior and is
repeated independently for all six pages.

Playback retains the retail Lighthouse/Zeboim projector sound `0xF9`: three
startup beats plus one sound for each of the six still transactions and the
native cleanup transaction. Donor file `0x48` remains the final cleanup frame;
the routine then resets the screen state and restores ordinary field input.

## Console frontage contract

V116 retains v115's visual-frontage alignment for every desk-console dialogue
or function in target 376. The compact, facing-gated regions remain centered
on the visible operator side rather than in invisible floor space:

| Entity | Function | Controller | Checked approach | Triangle |
| ---: | --- | --- | --- | ---: |
| 13 | Directive 0320 / ABCD authorization | `(175, 123)` | `(172, 105)` | 213 |
| 20 | National-security record | `(350, 175)` | `(332, 175)` | 68 |
| 21 | Inventory-gated archive-video player | `(264, -165)` | `(264, -175)` | 146 |
| 22 | Public-information record | `(-230, -160)` | `(-230, -170)` | 166 |
| 23 | Outcome record and west-bulkhead control | `(-465, -161)` | `(-465, -175)` | 177 |
| 24 | Directive revision record | `(-445, 145)` | `(-445, 125)` | 72 |
| 25 | Miang routing audit | `(-220, 66)` | `(-218, 55)` | 197 |

All seven console banks use facing-gated operand `0x04`, producing 24 units of
effective reach. Entity 26 uses the same compact contract for the apparatus.
North-lift entity 17 remains separate at `(0, 245)` with its no-facing `0x18`
controller.

## Canonical delta from v115

V116 changes these existing canonical resources:

| Canonical resource | Change |
| ---: | --- |
| 29 | Adds the `Video Disk` ordinary-item name. |
| 1358 | Adds the inventory award/full-retry path, persistent apparatus line, insert/cancel choice, and corrected six-still timing in target 376. |
| 2468-2473 | Replaces all six native TIMs with the refreshed `screenshotz/1-6` frames. |
| 2594 | Adds the `Zeboim archive video disk` item description. |

No canonical resource IDs are added or removed. Every other canonical payload
is byte-identical to v115.

## Emulator acceptance checklist

A state captured while target 376 was resident on v115 retains the old field
script even after v116 media is selected. Fully leave the Defense Archive and
re-enter it from the v116 CUE before testing. A cold-boot v116 New Game remains
the authoritative complete-acceptance path.

1. With item 109 absent, use the southeast computer from its checked frontage.
   Confirm the `NO MEDIA DETECTED` / `INSERT VIDEO DISK TO CONTINUE` prompt and
   that no playback begins.
2. Face the native center apparatus from its checked stance and collect the
   disk. Confirm sound `0x37`, the explicit receipt, and the ordinary inventory
   entry `Video Disk` with description `Zeboim archive video disk`.
3. If an inventory-full setup is available, confirm the full message, retained
   apparatus, and successful retry after one ordinary-item slot is freed.
4. Use the apparatus again after acquisition. Confirm the line about the other
   damaged disks; the controller must not disappear.
5. Use the southeast computer, select `Cancel`, and confirm immediate field
   control with no projector sound, still, black screen, or input lock.
6. Select `Insert disk`. Confirm the startup message, the familiar `0xF9`
   cadence, and clips 1 through 6 in order with their matching subjects.
7. On every clip, leave its caption open and verify that the corresponding
   image remains visible beneath it. Advance once and verify that the current
   image fades only then, before the next image transaction.
8. Advance the sixth caption and confirm that cleanup returns Elly to the room
   with normal camera and input. Use the computer again to confirm replay.
9. Leave and re-enter target 376. Confirm that the real Video Disk remains in
   inventory and both the repeat apparatus line and computer choice still work.
10. Check every controller in the frontage table from its visible console.
    Former invisible offsets must not open dialogue, and the authorization,
    west-bulkhead, and north-lift progression paths must remain intact.

No live-emulator acceptance result is claimed here. This checklist is the
runtime handoff; the extraction result below is a structural package audit.

## Packaged v116

```text
BIN:
output/Xenogears_PW_CD2_mass_driver_standalone_v116.bin
size: 696,899,952 bytes
raw sectors: 296,301
SHA-256: c0c13b0feb157bc90b839bd8eb0c969b552e5a5a627bb3344c07a9c51da3ce0c

CUE:
output/Xenogears_PW_CD2_mass_driver_standalone_v116.cue
size: 107 bytes
SHA-256: b28c537eb5080bf2388ca599f50bcb07c3ddbab85585a74be488ec5eff232986

staging manifest:
work/mass_driver_v116_stage/manifest.json
size: 222,465 bytes
SHA-256: bb797e261cdcaf068bbd17aaf3702bf5d9942ded387be5bdb181c4b72867dc0f

build inventory: 136 jobs / 172 replacements / 12,257,716 bytes
canonical-order aggregate SHA-256:
8f81e624ccab14e8ef8a00de86453dadb9bf8037af2d5d9fc3b520d344214c77
packaged payload extraction: 172 / 172 exact
audit scope: structural package audit
```
