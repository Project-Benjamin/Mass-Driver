# Mass Driver Dungeon 2.91 — Defense Archive video disk

The Defense Archive now contains a small, optional environmental sequence:
Elly can recover a video disk beside the room's native center film apparatus,
carry it to the computer on the right, and play six surviving Zeboim news
frames. The event uses the room's existing props and the retail Lighthouse
video system, so it reads as part of the old facility rather than as a new
terminal placed over the background art.

This change also realigns every dialogue controller in target field 376 to the
operator side of its visible console. The old invisible-space activations are
retired. A player must stand at the controls and face the corresponding bank.

## Player flow

Before the disk is collected, the southeast computer reports:

```text
ARCHIVE VIDEO CONSOLE
NO MEDIA DETECTED

INSERT VIDEO DISK
TO CONTINUE
```

The disk pickup is entity 26 at `(-75, -162)`. Its checked approach is
`(-75, -167)` on walkmesh triangle 157, matching the captured Elly stance
beside the center apparatus. Dialogue 22 identifies the disk and points the
player toward the computer on the right. The pickup then sets persistent
variable `0x03FA`, bit 3 (`0x0008`), and deletes its controller. This is a
field key-item flag rather than a normal inventory-table item, so it cannot be
sold, equipped, or lost to an inventory-capacity check.

The southeast computer is entity 21 at `(264, -165)`, approached from
`(264, -175)` on triangle 146. Once the flag is set, dialogue 24 identifies the
media as a Zeboim public archive and starts playback. The player may replay the
recording after that, including after leaving and re-entering the room; the
disk pickup itself remains absent.

Entity 21's former dialogue-17 procurement-mail role is deliberately retired.
The five remaining historical readers retain dialogues 16 and 18 through 21,
including entity 23's existing dual role as the strategic-outcome reader and
west-bulkhead control.

## Six-frame narrative

The captions are framed as late-Zeboim public news rather than omniscient
history. They establish a recognizable downward progression while preserving
Xenogears' existing account of hereditary damage, Miang's political influence,
and the civilization-ending nuclear exchange.

| Clip | Dialogue | Subject |
| --- | ---: | --- |
| 1 | 25 | Markets, services, and social order fail while wealthy families buy shelters, aircraft, and places on orbital projects in the belief that they can escape. |
| 2 | 26 | Births remain below replacement, infertility and hereditary illness rise, and officials fear civilization will not survive another generation. |
| 3 | 27 | Foreign and civil wars displace millions, abandon farms, sever transport, produce famine, and fill food lines in nearly every major city. |
| 4 | 28 | Riots continue under indefinite curfew while police and military units struggle to hold government districts, food depots, and power stations. |
| 5 | 29 | The public condemns Miang, identified consistently as the Prime Minister's adviser, and suspects that she manipulates the leader by filtering every report and available choice. |
| 6 | 30 | The last verified broadcast records one nuclear launch, retaliation by other nuclear-armed states, and the destruction of most Zeboim civilization. |

The sequence does not assert that Miang signed the orders. That remains
consistent with dialogue 21 elsewhere in the room: her influence lies in the
decisions and information routed to the official who does sign.

## Console frontage contract

Target 376 has seven physical desk-console banks. Entity 13 remains the
functional authorization station; entities 20 through 25 own the other six
banks. All seven dialogue controllers now use the native facing gate and bound
operand `0x04`, which gives 24 units of effective reach. The controller and
approach pairs are:

| Entity | Function | Controller | Checked approach | Triangle |
| ---: | --- | --- | --- | ---: |
| 13 | Directive 0320 / ABCD authorization | `(175, 123)` | `(172, 105)` | 213 |
| 20 | National-security record, dialogue 16 | `(350, 175)` | `(332, 175)` | 68 |
| 21 | Archive-video player | `(264, -165)` | `(264, -175)` | 146 |
| 22 | Public-information record, dialogue 18 | `(-230, -160)` | `(-230, -170)` | 166 |
| 23 | Outcome record and west-bulkhead panel, dialogue 19 | `(-465, -161)` | `(-465, -175)` | 177 |
| 24 | Directive revision record, dialogue 20 | `(-445, 145)` | `(-445, 125)` | 72 |
| 25 | Miang routing audit, dialogue 21 | `(-220, 66)` | `(-218, 55)` | 197 |

The disk controller uses the same facing-gated `0x04` reach at
`(-75, -162)`. The build validates every controller and checked approach
against connected walkmesh. It also proves the console zones, disk pickup,
authorization terminal, west door, and north lift are pairwise separated.
The north lift itself remains entity 17 at `(0, 245)` with its existing
no-facing `0x18` controller and checked approach near `(7, 255)` on triangle
73.

## Native still-video contract

The supplied `screenshotz/1.png` through `screenshotz/6.png` files are
center-cropped without stretching and resized with Lanczos filtering. Each is
encoded as a `320x224` PlayStation 16-bit direct-color TIM: RGB555 pixels,
little-endian words, and the STP bit clear. Every generated TIM is 143,380
bytes and uses the retail full-screen image rectangle at VRAM `(640, 0)`.

Field 376 addresses the six frames through the Lighthouse player's native
`FE77` file selectors:

| Clip | Field file | Canonical resource |
| ---: | ---: | ---: |
| 1 | `0x03` | 2468 |
| 2 | `0x04` | 2469 |
| 3 | `0x05` | 2470 |
| 4 | `0x06` | 2471 |
| 5 | `0x07` | 2472 |
| 6 | `0x08` | 2473 |

Playback retains the retail projector sound `0xF9`, including its three-beat
startup cadence. Each image transaction also uses that sound. Captions 25
through 30 are normal dialogue rendered in the retail video's full-screen
mode-3 overlay. After the sixth frame, one final `FE77` transaction loads the
donor's unchanged cleanup file `0x48`; the routine then clears the screen
state, exits cinematic mode, and restores field input. In total, the action
contains seven image transactions—six supplied frames plus cleanup—and ten
`0xF9` sound calls—three at startup plus one per transaction.

The target-376 header contract is now 43 records / 1,088 bytes, with SHA-256
`4315a2225c8564ec9713240a26d7b99abda5d1b075dc43b950181d11459c11b1`.
Its ATEL script has 27 entities / 4,831 bytes, with SHA-256
`7f43ecb026fb089b617537c1fa099680f1b589f45eeeafe9f7856476c655e273`.
Entity 26 is inserted before the retained static nodes, so no native room
model is replaced or shifted out of the renderer's table.

## Emulator acceptance checklist

A DuckStation state saved while field 376 was already resident contains the
old room resources. After changing discs or migrating the state, first leave
the Defense Archive completely and re-enter it from the new media before
judging this event.

1. Before collecting the disk, approach entity 21 from `(264, -175)`, face
   the visible southeast computer, and press Cross/X. Dialogue 23 must request
   a video disk. The retired procurement mail must not appear.
2. Approach the center film apparatus from `(-75, -167)`, face it, and press
   Cross/X. Dialogue 22 must play once and the disk interaction must disappear.
   Pressing Cross/X beside or behind the prop must not collect it.
3. Return to entity 21. Confirm dialogue 24, hear the familiar Lighthouse
   projector cadence, and view images 1 through 6 in order with dialogues 25
   through 30. Check every page for intact final words and five-line layout.
4. Close the sixth caption. The game must return to the ordinary room view
   with Elly controllable; no white frame, black screen, stuck camera, or input
   lock may remain.
5. Use entity 21 again. The video must replay without another pickup prompt.
6. Leave and re-enter target 376. Entity 26 must remain absent and entity 21
   must still play the recording, proving `0x03FA` bit 3 persisted.
7. Visit each console from the checked approach in the frontage table. Its
   correct dialogue or function must open only while facing the visible
   controls. The former offsets `(115,-94)`, `(-132,-40)`, `(-406,-94)`, and
   `(-406,225)` must not activate invisible dialogue.
8. Confirm the authorization station still accepts the five-step code, the
   north lift still reports or performs its proper state, and entity 23 still
   opens the west bulkhead after the Guardian condition. The optional video
   flag must not alter any of those progression paths.

No live-emulator acceptance result is claimed by this document; the checklist
is the handoff contract for testing the packaged build.

## Packaged v115

```text
BIN:
output/Xenogears_PW_CD2_mass_driver_standalone_v115.bin
size: 696,899,952 bytes
raw sectors: 296,301
SHA-256: 15bf08dcf0bd3ed1b50b310b0af24aa20baf3cbba63a95b0dc1e675fcee1560d

CUE:
output/Xenogears_PW_CD2_mass_driver_standalone_v115.cue
size: 107 bytes
SHA-256: ae6142b0aa3158ec4e5275e8deceaf7184a2c4cd86d10ad4af52d0ffe346748d

staging manifest:
work/mass_driver_v115_stage/manifest.json
size: 221,536 bytes
SHA-256: 36108de1388c631e5f792bb8b9b27e43981b77d33ca0267c4c2fb1ba3230f964

build inventory: 136 jobs / 172 replacements / 12,257,144 bytes
canonical-order aggregate SHA-256:
4031590c5f72a838f081c05dff36fd37564cd56021a7ff9f974384ab1424d815
packaged payload extraction: 172 / 172 exact
```

Relative to v114, canonical 1358 changes for target 376 and canonical
resources 2468 through 2473 are added for the six video frames. A v114 save is
compatible with v115. If the save or emulator state was captured while field
376 was resident, mount the v115 CUE, fully leave the Defense Archive, and
re-enter it before testing; resident v114 room resources are not replaced in
place.
