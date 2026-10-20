# Mass Driver Dungeon 3.17 - Visible hanging terminal and Citan operation

V156 is the current frozen package. It preserves V155's 33-field, 66-edge
route, widened Central Control wall-console frontage, native transition chime,
subjective two-visible-actor Zeboim memory, automatic post-dialogue-32 handoff,
native east-door entrance, local capsule launch, and guarded field-617 return.
Targets 388 and 507 and every Krelian-laboratory asset remain absent; target
728 remains the active route's final room.

V156 makes Citan's launch station unmistakable and gives the launch engineer a
visible job. It losslessly appends retail field 373's recognizable beige/green
overhead-arm computer to Central Control, moves Citan's final station to its
walkable operating side, lets Citan and Elly face each other for dialogue 35,
then cuts to a held side view while Citan turns back and performs one finite,
sounded keypad sequence before the completion bit and world-map launch.

## Authentic terminal asset and authored placement

The imported geometry is exact retail field 373 node 44/model 7. V156 appends
that model as target model 11 and appends static node 43 at world anchor
`(88,0,168)`, yaw `0x0200`:

```text
node 43: 10 00 00 00 00 02 00 00 58 00 00 00 A8 00 0B 00
model 11: 2,524 bytes
SHA-256: c7791afbe919aece2096c863e0cdff9677b091872e147d10bdbbdc37799d6c1c
```

The model's exact local AABB is X `[-70,14]`, Y `[-258,-106]`, Z
`[-72,12]`; the authored transform produces world AABB X
`[8.0969337259,86.5857864376]`, Y `[-258,-106]`, Z
`[143.2512626585,220.3259018078]`. The room and donor already share byte-exact
180,224-byte graphics, SHA-256
`4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28`,
so no graphics upload or texture remap is added.

The old 43 node records and old 11 model entries remain byte-identical. The
static append adds no actor collision and changes no walkmesh. Prepared-header
node 29/model 5 remains Elly's wall computer bank. Native nodes 26/28 and
models 3/4 remain byte-exact chair-like fixtures; V156 no longer identifies
them as Citan's hanging terminal.

Citan's authored operating station is `(57,63)`, layer 0, triangle 23,
direction 4/raw yaw `0x0A00`. Its relative X/Z displacement from the imported
terminal anchor is `(31,105)`. Field 373 supplies the exact visible asset, not
that station or direction.

## Continuous dialogue, arrival, and terminal operation

The established first interaction remains continuous:

1. Dialogues 12 and 21 play in the present; exact retail save-point sound bytes
   `74 50 80` play once immediately before the first fade.
2. The silent subjective reaction and memory use only dialogues 22-31 and 36,
   visible entities 17/18, hidden Miang anchor 19, and eye
   `(174,-102,-125)`.
3. The party returns under black and dialogue 32 plays under the held present
   camera. Dialogues 33/34 remain authored but unreachable.
4. Without returning control or requiring a second Cross/X press, the camera
   interpolates over 24 frames to whole-room target `(-13,106,-32)`, eye
   `(-27,-767,-544)`. Citan enters through the native east leaf.
5. Citan follows bounded legs `(170,89)/32`, `(100,89)/32`, and `(57,63)/20`,
   ending on triangle 23 in direction 4. Reciprocal `FE 17 03 FF` and
   `FE 17 FF 03` cues make Citan and Elly face each other for dialogue 35.
6. After dialogue 35 closes, the still-held camera interpolates over 12 frames
   to target `(52,140,-116)`, eye `(527,140,-214)`. It does not enter fixed
   mode again. A blocking call runs entity 3 script 23 before completion.
7. Script 23 turns Citan toward the terminal, plays the field-378 keypad
   animation/sound timing, reaches STOP after 84 timed ticks, and only then
   allows the completion write and retail world-map launch.

The operation body is exactly:

```text
5F 04 2C 0A 74 F9 80 26 19 80 74 F9 80 2C 0A 74 F9 80
26 23 80 2C 07 26 18 80 2C FF 00
```

Retail field 378 entity 4 script 4 supplies the exact keypad animation,
three sound-`0xF9` calls, waits `25/35/24`, and STOP sequence. The leading
`5F 04` and target station are authored Central Control mapping. Both launch-
commit paths converge on one static side-camera and blocking operation call.
The interrupted seen/arrived recovery path locks control before dialogue 35;
neither commit path emits `FE 53` before world-map unload.

## Byte-level Central Control identity

Target 728 canonical 2062 is 129,268 bytes with SHA-256
`8f4b0f2672fc61bda95b1a15860b4d4fe5561c3cc438824cbed0003c9671c1c9`.
Its prepared 1,104-byte header has SHA-256
`15830ac6f0b05296f0df613b853732c01429f902906b8c2527d370b4482b182c`;
the final packed header has SHA-256
`a4c56818db08d9d92cf62a5ec3fe82198956226ae01aa6456abcb61d7a13a5a3`.
The 16,032-byte models component has SHA-256
`ac2e4645d3e139115ad4210767a59c88e4cb291a67dc4416fe9ab27baed3a5c1`.

The decoded script is 3,562 bytes with SHA-256
`a27db09bedc55d12bc24ab9dac4360c067a802bd12b1dabe89df7e1bb8369aec`.
Its exact routines are:

```text
e13:s0 initializer  PC 033E  24 bytes  16495b64a4f39fc843abf026726dddeb615e64412394a78b923100d60a7dcd46
e3:s21 stage         PC 039F  15 bytes  9a5aa669a5e137e3039f0e744cf0da4a926869f388d2e4a270a4140da5561cbc
e3:s22 walk          PC 03AE  39 bytes  b8f104f180b394fca01b03444fe9e57f5eef9cbad9f43426f63b884c7b4432b4
e3:s23 operation     PC 03D5  29 bytes  f2ed5e1d3518e963b614fdd381b07d6248a24b136e652d79ae68e23d9e736209
e13:s2 action        PC 03F2 1053 bytes  0d0dda5cf756b4225639789186e53d8a36fd65954656966608df16321cf28d51
```

Dialogue-35 WAITs occur at PCs `0454` and `07B7`. The one side camera begins at
`07BC`, the blocking `09 03 37` operation call is at `07D9`, the completion
write is at `07DC`, and the world-map call is at `07EB`. All 18 entity-13 F5
calls use control flag `0x01`; their PCs are:

```text
040B 0454 046D 0475 04F0 0521 0552 0583 05B4
05E5 0616 0647 0678 06A9 06DA 0722 07B7 0807
```

The images, walkmesh, actors, sprites, encounters, dialogue, triggers, native
east-door controllers, memory staging, wall bank, chime, and authored dialogue
archive are byte-identical to V155. Entity 16's 32 slots remain on STOP.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v156.bin
size: 696,135,552 bytes / 295,976 raw sectors
SHA-256: 9eb4dde57c0ed39ba504d50684b9bb63055812145de2474043e255ff150774a1

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v156.cue
size: 107 bytes
SHA-256: 5a47cbe3465ecdf08a20eaa7ef5deb1029d9581631d145f141bdc4c305d81707

manifest: work/mass_driver_v156_stage/manifest.json
size: 245,085 bytes
SHA-256: ab46ece79e120786f8a18a56972623c5eee8e758a77b55776a4d526520fa95dc
jobs / replacements / bytes: 136 / 169 / 11,807,356
route fields / directed edges: 33 / 66
replacement aggregate: d7f8a08343e191a500f8844dfbd4a9b9b950eb1901fcb6bd495ef4b171f666d9
framed aggregate: 9843b800b8a4039250d8eb0215dd322aede53e27ab0494bcf7ddf5efafd92665
```

The frozen builder is 1,346,370 bytes with SHA-256
`56952d297fa144b0e62d72e5261c7270f522578573a4b873aa3cd19d7c7782a9`.
The authored field-369 dialogue JSON remains byte-exact at 9,341 bytes,
SHA-256
`e583a26ec7d976b6e31745ff1703ad156dd5eb0766bc4551e0695a320618dab0`.

## V155-to-V156 delta and validation

The declared stage delta is exactly canonical 2062. The exhaustive complete-
FAT payload delta is canonicals 17, 22, and 2062; 3,720 of 3,723 extractable
payloads are byte-identical. The FAT grows canonical 2062 from 126,316 to
129,268 bytes at unchanged LBA 221314. Of 4,147 descriptors, 1,919 change:
one size tuple and 1,918 sector relocations by `+2`; 2,228 tuples, all entry
kinds, and all directory memberships remain unchanged. FAT SHA-256 changes
from `31413e0b788b3ed4e81ad8ffd23f0d6ed3067e0cc91be9eafd968760f837b847`
to `f2aa2741a124de00ba8b3e87b6ff70b883278c217a9044e2b968c088cd3efe6a`.

The image grows by two raw sectors. An exhaustive same-LBA comparison finds
60,335 changed common raw sectors plus two appended sectors and 235,639
unchanged common raw sectors. Logically, only FAT sectors 31-38, mirrored FAT
sectors 172926-172933, and target-2062 sectors 221314-221377 carry changed or
new user data. Every one of the 74,598 old tail sectors at 221376-295973 has
byte-identical user data at new LBA `+2` (221378-295975). All 169 packaged
replacements re-extracted byte-for-byte. All 5,848 replacement sectors, all 80
logical-delta sectors, and the boot sector passed MODE2/Form1 EDC/ECC; the
union contains 5,865 sectors. The patched boot remains exact at LBA 172938,
SHA-256
`79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc`.
A deterministic second build reproduced all 550 staged files, the manifest,
and the complete BIN byte-for-byte.

The authoritative V156 structural run passed 262 tests / 2,693 successful
subtests in 21.010 seconds with exit 0 and zero failures, errors, failed
subtests, or skips. Fresh user-driven
acceptance of the imported terminal visual, mutual-facing dialogue, side
camera, keypad operation, launch, and return remains pending.

## Focused-state guidance

Use `work/runtime_capture/near_final_v156_from_v108_vault1.sav`, 1,701,685
bytes, SHA-256
`6eac212f38e4ee14ce73665fb8b90fc7971293034f7233646098fa85f7704681`.
It mounts the exact V156 CUE once with no V155 media name retained. Historical
V108 field 377 is resident; target 728 is absent and will cold-load from V156
media. The resident FAT at payload offset `0x11A66` / RAM `+0x10004` has
SHA-256
`f2aa2741a124de00ba8b3e87b6ff70b883278c217a9044e2b968c088cd3efe6a`.
Migration changes exactly 1,933 FAT bytes and zero payload bytes outside the
FAT. Flags are `0x0033`, with bits 0, 1, 4, and 5 set and bits 6, 7, and 12
clear; party bytes are `01 06 FF`. Ask the player to navigate and press
controls; do not automate emulator input.

Any V155-or-earlier state with target 728 resident cannot validate V156's
imported model/header bytes, revised Citan route/facing, side camera, or
terminal-operation script. Close DuckStation, mount the exact V156 CUE, and
load the focused state above so target 728 cold-loads from V156 media.

## Historical V155 boundary

Historical V155 release facts follow unchanged.

V155's frozen automatic-handoff and whole-room-finale package, state, and
validation record remains byte-for-byte in
[`mass-driver-dungeon-3.16.md`](mass-driver-dungeon-3.16.md). V156 appends the
recognizable terminal and operation choreography; it does not rewrite that
historical release record.
