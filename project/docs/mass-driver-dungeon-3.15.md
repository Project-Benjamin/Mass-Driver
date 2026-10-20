# Mass Driver Dungeon 3.15 - Native transition chime and present response

V154 is the current frozen package. It preserves V153's 33-field, 66-edge
route, widened Central Control terminal, subjective two-visible-actor Zeboim
memory, native-east-door Citan entrance, held arrival camera, local capsule
launch, and guarded field-617 return. It changes only Central Control canonical
2062 and the generated FAT mirrors that describe its new size. Targets 388 and
507 and every Krelian-laboratory asset remain absent; target 728 remains the
active route's final room.

V154 adds the retail save-point entry chime immediately after Emeralda's
present-day dialogue 21 closes and immediately before the first memory fade.
After the memory, it restores one concise present-day exchange in dialogue 32.
Dialogues 33 and 34 remain authored but are unreachable. All 18 entity-13 F5
dialogue calls retain control flag `0x01`.

The stable V151 failure copy is
`work/runtime_capture/v151_hidden_controller_dialogue_abort.sav`, 1,752,967
bytes, SHA-256
`8bc81de760fda0ba5522c01b439a4aa152082bd8c48182e560c62f8747419717`.
At block 21, hidden owner entity 13 used F5 flag `0x00`; WAIT_DIALOG followed
OP_STOP, terminating the action with the camera and actors stranded and memory
bit 12 clear. V154 retains flag `0x01` on all 18 reachable entity-13 calls.

## Native transition sound

The transition uses exact bytes `74 50 80`: opcode `0x74`, the native field
sound-effect operation, with literal sound ID `0x50`. The strongest retail
donor is Disc 1 field 385, canonical/bundle 1376,
`work/reference_fields/cd1_zeboim/1376.bin`, 49,280 bytes, SHA-256
`62cc98b0914b2206506fc83fe99b627f49a4da4448320c97ce51cd9b90ab8c52`.
Its script component is 1,688 bytes with SHA-256
`a4ab4bd30b8f842b3a8d91f8acef04ac7a9f780f1bc12e2b2580527a7bb0d0fd`.

The donor is entity 16's ordinary save-point collision routine. Its pointers
are init `0x0172`, update `0x01B1`, action `0x01B8`, and collision `0x01C0`.
The semantic collision bytes through STOP are:

```text
FE 99 00 02 0E 04 00 00 40 D1 01 74 50 80 36 0E 04 00
```

The donor plays the chime at PC `0x01CB`, sets its transient latch, and stops
at `0x01D1`. The trailing `E0 00` bytes are unreachable padding and are not
copied. Opcode `0x74` neither blocks nor waits. V154 emits the three-byte sound
at PC `0x045C`, after dialogue 21's WAIT_DIALOG at `0x045B` and before the
first fade at `0x045F`. The sound and fade therefore begin in the same VM slice;
the existing 16-frame fade wait supplies the transition timing.

## Interaction and memory choreography

Entity 13 remains at `(-48,97)` on triangle 16. It is no-facing and uses the
rectangular OP18 X/Z operands `0x1C/0x02`, giving effective reach `72x20` and
inclusive region X `[-120,24]`, Z `[77,117]`. It accepts the captured
`(-113,113)`/triangle-15 stance, the earlier `(-15,113)`/triangle-20 stance,
and both F2 readings `(-4,114)` and rounded `(-4,115)` on triangle 19. The
archive entity-12 region starts at X `25`, leaving a one-unit coordinate gap;
entity 14's east-door region is also disjoint.

The first interaction now runs in this order:

1. Dialogues 12 and 21 play in the present.
2. The native `74 50 80` chime plays once, without an added wait.
3. The field fades, hides the party, and stages the silent subjective reaction.
4. The memory plays dialogues 22 through 31 and 36. Entities 17 and 18 are
   visible; entity 19 remains Miang's hidden point-of-view anchor.
5. Under black, the action hides the memory actors and clears the memory grade.
6. A concise present camera is established, the party is shown, and the field
   fades in. Dialogue 32 then plays as the sole present response.
7. The camera is released and control returns. Dialogues 33 and 34 are absent
   from the action and runtime-unreachable. Dialogue 35 remains the later
   capsule-launch commit.

Dialogue 32 is exactly:

```text
<Emeralda>
"Elly..."<New><Elly>
(Why does this feel so
familiar?)<New><Emeralda>
"Elly?"<New><Elly>
"I'm okay. This room feels...
familiar."<New><Elly>
"But no matter, we have a
job to do."<Close>
```

It has width 58, height 5, a 151-byte payload, and SHA-256
`6922f9e4253779a9a9bf774e33b1fbc65676a42d1f00afe9256224ea9aa26581`.
Dialogues 33 and 34 remain byte-identical in the authored archive, with payload
SHA-256 values `bc7abd1ae635a19b65eb8e11986b2724fd7899feec210da433a2e5674fb5af78`
and `b166485d27d7d2129805d2e8ef3d65ed4b9aa1d119fe7a1327de79debbba7514`.

The entity-13 action owns exactly 18 F5 calls, all with control flag `0x01`.
Their dialogue IDs, in bytecode order, are:

```text
20, 35, 12, 21, 22, 23, 24, 25, 26,
27, 28, 29, 30, 31, 36, 32, 35, 11
```

The memory eye remains the stable Miang-aligned ATEL `(x,z,y)` position
`(174,-102,-125)`. All historical targets, hidden entity-19 anchor/facing,
Citan staging and movement, east-door behavior, held arrival camera, launch,
and field-617 return remain unchanged.

## Byte-level Central Control identity

Target 728 canonical 2062 is 126,308 bytes with SHA-256
`70b617b9d9b08c1a40a4b936598992a1a3cea92d648370d1790862af465bcd2c`.
Its decoded script is 3,472 bytes with SHA-256
`a421fed38b3baeebc176cf664470073aa7606449bbdfc61ef3cfb1b4d643f30b`.
Entity-13 action script 2 at PC `0x03DD` is 984 bytes with SHA-256
`dd4b1e686aa36c1f8c8c174d169feec12890d65de4da0b8ceab352bfa9421bbd`.

The 24-byte entity-13 initializer at PC `0x033E` remains SHA-256
`16495b64a4f39fc843abf026726dddeb615e64412394a78b923100d60a7dcd46`
with exact bytes:

```text
BC 19 D0 FF 61 00 C0 F8 00 00 20 F8 07 04 00 18 1C 02 64 00 20 01 80 00
```

The prepared 1,088-byte header remains SHA-256
`b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31`;
the packed header is SHA-256
`ea951f6144c95d5eb07675bd639f3cf17064d717f8e08da7ce48490dc1adc58b`.
The decoded components are:

```text
images:       4 bytes / df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119
walkmesh: 2,540 bytes / 6a1f335cd2cf00bcec7a5412b8ab7392fcff378912fd2857880d69f2186e6a14
models:  13,504 bytes / 9bb9ef16cb1f85b0c2a4052d79a710cb91224ea78be7f7b72c246ac6183ab24e
actors:  18,640 bytes / 2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538
sprites: 67,668 bytes / e09e0ca20423abd18fbbbee63c37b47e0d89c8a7a1cb32a61d54d37de452b805
script:   3,472 bytes / a421fed38b3baeebc176cf664470073aa7606449bbdfc61ef3cfb1b4d643f30b
encounters: 528 bytes / e88b412320050425ae87abad80b51749da8171b023e943604cf47a370535ab38
dialogue: 4,892 bytes / d95b3e83575abeb12b79724e032d68a171dfc5fc99895cfd9a6d37c3f5b7e4c0
triggers:     0 bytes / e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Citan's stage and walk scripts remain byte-identical, with SHA-256 values
`9a5aa669a5e137e3039f0e744cf0da4a926869f388d2e4a270a4140da5561cbc`
and `00b90ce55c17beb780b028d81a1f61e40b2c955ce58887eba7b9b43f5d58728f`.
The east-door action and helper remain SHA-256
`2a8de19318b0ce8cce4b6a6e98385a1e3f9c34ea536fb11e668f56f9e31e139b`
and `fe73b10afa9601df5273f8d4c43610bef41ca28e59e928d102e4dedd1eb77c4e`.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v154.bin
size: 696,130,848 bytes / 295,974 raw sectors
SHA-256: 5db4cbbf892338360f24cda664dc841b5a67f4b183819c205005635bc990fdc3

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v154.cue
size: 107 bytes
SHA-256: e77c607981d6d7b935be42eab90443169cfda1e0caa4bfb6bb71628ff3c8d6f2

manifest: work/mass_driver_v154_stage/manifest.json
size: 239,448 bytes
SHA-256: e0423870efc38045b98356d088fce6633cd918369554af17011e2f26e6e566d5
jobs / replacements / bytes: 136 / 169 / 11,804,396
route fields / directed edges: 33 / 66
replacement aggregate: 1d37789cf911ac49a37eef9d9dfae31e2cd74c17d31ebc97d3e6409e9d95fe90
framed aggregate: 8b9ec311d83f50592c7169877ff3cf7abb0a6664fbca7dabe4cde25aea754022
```

## V153-to-V154 delta and validation

The declared stage delta is exactly canonical 2062. The exhaustive complete-
FAT payload delta is canonicals 17, 22, and 2062: canonicals 17 and 22 differ
only where their generated FAT mirrors record canonical 2062's size changing
from 126,392 to 126,308 bytes. Exactly one of 4,147 FAT descriptors changes:
canonical 2062/physical 2057 remains at LBA 221314 and changes from
`(221314,126392,file)` to `(221314,126308,file)`. All 61 directory tables and
3,720 of 3,723 extractable payloads are byte-identical.

Exactly nine raw sectors change: LBAs 31, 172926, 221314, and 221370 through
221375. The exhaustive delta contains 5,817 changed user bytes and 7,189
changed raw bytes after valid MODE2/Form1 regeneration. All 169 packaged
replacements re-extracted byte-for-byte. All 5,846 replacement sectors, two
additional changed sectors, and the boot sector passed MODE2/Form1 EDC/ECC
validation: 5,849 of 5,849 audited sectors. A deterministic second stage and
BIN rebuild reproduced every identity above.

The authoritative V154 structural run passed 262 tests / 2,689 successful
subtests in 20.451 seconds with exit 0 and zero failures, errors, failed
subtests, or skips. Fresh user-driven acceptance of the transition chime,
present response, preserved Citan entrance, launch, and return remains pending.

## Focused-state guidance

Use `work/runtime_capture/near_final_v154_from_v108_vault1.sav`, 1,701,664
bytes, SHA-256
`f61675cfc8113a806d2e5d1aef432ac3444cdca2f7aa242bcebac54296146046`.
It mounts the exact V154 CUE. Historical V108 field 377 is resident; target 728
is absent and will cold-load from V154 media. Its resident FAT SHA-256 is
`59298ba90b3b7f9a8dddb2b5a2a21cd3320224bcc804e5b7afaf7f6ae0024ee1`.
The migration changed exactly one FAT byte, `B8` to `64`, and nothing outside
the FAT. Flags are `0x0033`, with bits 4 and 5 set and bits 6, 7, and 12 clear;
party bytes are `01 06 FF`. Ask the player to navigate and press controls; do
not automate emulator input.

Any V153-or-earlier state with target 728 resident cannot validate V154's
changed action and dialogue bytes. Close DuckStation, mount the exact V154 CUE,
and load the focused state above so target 728 cold-loads from V154 media.

## Historical V153 boundary

Historical V153 release facts follow unchanged.

V153's frozen wider-console and coherent-memory package, state, and validation
record remains byte-for-byte in
[`mass-driver-dungeon-3.14.md`](mass-driver-dungeon-3.14.md). V154 adds the
native transition chime and reachable present-day dialogue 32; it does not
rewrite that historical release record.
