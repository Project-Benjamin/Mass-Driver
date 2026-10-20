# Mass Driver standalone dungeon 3.18 (V157)

V157 keeps the 33-field, 66-edge standalone route and the continuous Central
Control finale, but replaces V156's oversized overhead arm with a compact,
recognizable retail standing keypad at the user's captured east-wall marker.
Dialogue, the memory sequence, the whole-room arrival, mutual-facing launch
conversation, blocking terminal operation, native east door, capsule launch,
and guarded field-617 return remain intact.

## Current package

- BIN: `output/Xenogears_PW_CD2_mass_driver_standalone_v157.bin`
  - 696,130,848 bytes / 295,974 raw sectors
  - SHA-256 `38ac9a31f62c172541db6361249f58822a3abccc91569a4bed56498c0518edeb`
- CUE: `output/Xenogears_PW_CD2_mass_driver_standalone_v157.cue`
  - 107 bytes
  - SHA-256 `91d48c195c99d90130d0244de8eb1688d1a3e86b050b01d663cdccf9e5c7ec34`
- Stage manifest: `work/mass_driver_v157_stage/manifest.json`
  - 246,356 bytes
  - SHA-256 `0a8f9e99a471f7af841a42f5ff22a802dfb4282057bcafb80e3e245a34365345`
- Builder: `tools/build_mass_driver_dungeon.py`
  - 1,367,621 bytes
  - SHA-256 `f4daa872b0c8b045b5af4fea3d26ff6a6aa444e0a1360c609d47181cf7acf795`
- Authored Central Control dialogue remains 9,341 bytes, SHA-256
  `e583a26ec7d976b6e31745ff1703ad156dd5eb0766bc4551e0695a320618dab0`.

The manifest contains 136 jobs and 169 replacements totaling 11,804,928
bytes. The route remains 33 fields / 66 directed edges. Canonical-ID-sorted
replacement payload SHA-256 is
`a306ed2adc0bbbaff3538f6c6226b72163ed258ccff9c0d0f37272f8a95726a2`;
the ID-and-length-framed aggregate is
`e478cae23d8f4260dc02eecc8e7be685220ea94fef022fb571f345dcaba14845`.

## Compact standing keypad

The source is exact retail field 361 node 21/model 5. Its unmodified 360-byte
model has SHA-256
`3afa78d55bb7af29dbe842f5f2ac8a4a5db4e6a30a77e5b78a5d4a1aad3e95f4`.
V157 relocates the model's texture state and UVs into proven-unused target
VRAM without redrawing the prop or growing the graphics archive. The installed
360-byte model SHA-256 is
`7177eada7ba59ea9a442661702a6d8dbe32924550d9e2a69ca74fe91f368078b`.
The rebuilt 13,868-byte model component SHA-256 is
`83ae54331684dd8d72f02bd3be1d86742f15caa17f9e6f525b3e101b2aad6203`.

The exact passive-static node-43/model-11 record is:

```text
10 00 00 00 00 08 00 00 BB 00 B7 01 1E 00 0B 00
```

It places the keypad at anchor `(187,439,30)`, yaw `0x0800`. Its world AABB
is X `123..164`, Y `-61..0`, Z `75..112`; the sloped control-face center is
approximately `(143.5,-50.5,84)`, covering the captured `(143,84)` marker.
The old 43 target nodes and old 11 models remain byte-identical. Node 43 uses
static flag `0x0010`, adds no actor collider, and leaves the walkmesh unchanged.

The donor texture word rectangle `(566,84,32,34)` is relocated to
`(432,192,32,34)`. Donor palette row 493 is relocated to unused target row
487. A conservative primitive scan proves target models 0 through 10 do not
sample the destination. The graphics archive remains exactly 180,224 bytes;
its V157 SHA-256 is
`201c89767211545e039422ab8791b48ff5a22f3f5383c4d0b234387a3c25aef7`.

Central Control's optional archive controller, entity 12, moves with the prop
to `(136,53)` on triangle 28. It stays no-facing with OP18 operands `0x01/0x01`:
Noah's raw extent is `2x2`, and the player-radius allowance makes effective
reach `18x18`, inclusive X `[118,154]`, Z `[35,71]`. That leaves an exact
94-coordinate X gap from entity 13's story strip and a one-coordinate X gap
from entity 14's east-door region. Entity 13 remains unchanged at `(-48,97)`,
triangle 16, no-facing OP18 `0x1C/0x02`, effective `72x20`, region
X `[-120,24]`, Z `[77,117]`.

## Finale choreography

One entity-13 interaction still plays present dialogues 12 and 21, exact
save-point chime `74 50 80`, memory dialogues 22-31 and 36, and sole present
response 32. Dialogues 33 and 34 remain authored but unreachable. Only the
Launch Director and Systems Officer render; Miang remains a hidden POV/offscreen
voice. All 18 F5 calls retain flag `0x01`. Dialogue 32 continues automatically,
without returning control or requiring a second Cross/X press.

The held whole-room arrival camera remains target `(-13,106,-32)`, eye
`(-27,-767,-544)`, 24 frames. Citan stages hidden at `(225,104)` behind the
native east leaf and follows this checked route:

1. `(170,45)`, bound 32, triangle 27;
2. `(150,35)`, bound 32, triangle 28;
3. `(136,53)`, bound 20, triangle 28, direction 0.

The route clears the compact prop by more than the 16-unit actor radius and
keeps scoped F8 `0x0038` limited to the first leg. The field is shown before
sound `0x77` and native entity-15 script 4 open the leaf. Reciprocal facing
cues make Elly and Citan face each other for dialogue 35.

After dialogue 35, the held-mode operation camera moves over 12 frames to
target `(140,70,-45)` from eye `(300,-150,-135)`. It frames both Citan and the
keypad with no front-facing static blocker. One blocking entity-3 script-23
call then turns Citan direction 0 and runs the finite field-378-derived keypad
sequence with three sound-`0xF9` events and waits `25/35/24` before STOP.
Completion bit 6 and the retail Mass Driver world-map launch occur only after
that operation. The east leaf and camera remain held through unload.

## Exact target 728 identities

- Canonical 2062: 126,840 bytes, SHA-256
  `404c67c39b34f6a62fffde18d20580cab9a60d8ec2f28bbf4880cb056e6c5f46`
- Canonical 2063: 180,224 bytes, SHA-256
  `201c89767211545e039422ab8791b48ff5a22f3f5383c4d0b234387a3c25aef7`
- Prepared header: 1,104 bytes,
  `d947f233c17232e0b2c88e141295247e69f4fbf6482a41109104d56f69cfd719`
- Packed header: 1,104 bytes,
  `260c95291043fb71770d5beda5f9753da895c7b58813612f862209ede193c227`
- Script: 3,562 bytes,
  `889bde3344c78874c8da995a463dc309e97d4bc472a72728516f67cad3535c56`
- Entity-12 initializer PC `0x02F8`: 24 bytes,
  `9255a0edd7d5b7d7e1c9ad9f14a60f0a4ada215f715342182917ea63ac3f0117`
- Citan stage PC `0x039F`: 15 bytes,
  `9a5aa669a5e137e3039f0e744cf0da4a926869f388d2e4a270a4140da5561cbc`
- Citan walk PC `0x03AE`: 39 bytes,
  `f5ef8a4e675a1ba157ca8d8f9eb206c7e1d2928ec13becd530e281b5942fda38`
- Terminal operation PC `0x03D5`: 29 bytes,
  `e88f1ffb09b42ec8c4d878983cb6cac2e065f686955a5521e7f0fe9f963f1c7e`
- Entity-13 action PC `0x03F2`: 1,053 bytes,
  `12cbdceababaaa4bc1ae543eda7860bd2ebf0fd1f2912f17f46a25b45ba1bf19`
- Operation camera at PC `0x07BC`: 29 bytes,
  `5c0314952501b852986687aa766d5cee8b8aa75df49afa0ffec56bc3c05f4326`
- Blocking call at PC `0x07D9`: `09 03 37`.

Images, walkmesh, actors, sprites, encounters, dialogue, and triggers are
byte-identical to V156. The dialogue component remains 4,885 bytes, SHA-256
`318a95da8d619dd0e9d9a734c2ae0d60b0b1edbcdeed04da56bf465bdf3e455d`.

## Package audit

The declared V156-to-V157 stage delta is exactly canonicals 2062 and 2063.
The complete FAT payload delta is exactly 17, 22, 2062, and 2063; 3,719 of
3,723 extractable payloads are unchanged. Of 4,147 FAT descriptors, 1,919
change: canonical 2062 has the sole size change and 1,918 later descriptors
relocate two sectors earlier. All entry kinds, 61 directory records, and
canonical payloads 3722 and 3723 remain unchanged. FAT SHA-256 changes from
`f2aa2741a124de00ba8b3e87b6ff70b883278c217a9044e2b968c088cd3efe6a`
to `da14b400a03ecff0c71786a32db046bdeded595a27b93349d6cf4771c195a53d`.

Direct final-BIN extraction passed 169/169. MODE2/Form1 EDC/ECC validation
passed 5,846/5,846 replacement sectors, 166/166 logical-delta sectors, and
5,863/5,863 sectors in their union with boot LBA 172938. The patched boot
sector SHA-256 remains
`79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc`.
The deterministic second full build produced the same BIN, manifest, and all
169 staged payloads. The relocated user-data tail is byte-identical across
74,510 sectors from old LBAs 221466-295975 to new LBAs 221464-295973.

## Focused replay and validation status

The preferred state is
`work/runtime_capture/near_final_v157_from_v108_vault1.sav`, 1,701,664 bytes,
SHA-256
`267dbe35a584cdd9733c46285e51f78b99392d3ff9a500f4c2e6f1aa516105f8`.
It mounts the exact V157 CUE and has historical V108 field 377 resident.
Target 728 is absent, so walking north cold-loads the V157 room. Resident FAT
SHA-256 is
`da14b400a03ecff0c71786a32db046bdeded595a27b93349d6cf4771c195a53d`;
payload bytes outside the FAT are unchanged. Flags are `0x0033`, party bytes
are `01 06 FF`, and the active VM/dialogue state is idle.

The authoritative V157 structural run passed 262 tests / 2,693 successful
subtests in 21.558 seconds with exit 0 and zero failures, errors, failed
subtests, or skips. Fresh user-driven visual and gameplay
acceptance of the compact keypad, Citan route, operation, launch, and return
remains pending.

Historical V156 documentation remains frozen in
[`mass-driver-dungeon-3.17.md`](mass-driver-dungeon-3.17.md). The complete V157
authored-dialogue ledger is
[`mass-driver-dialogue-v157.md`](mass-driver-dialogue-v157.md).
