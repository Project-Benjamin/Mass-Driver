# Mass Driver Dungeon 3.16 - Automatic terminal handoff and whole-room finale

V155 is the current frozen package. It preserves V154's 33-field, 66-edge
route, widened Central Control console, native transition chime, subjective
two-visible-actor Zeboim memory, local capsule launch, and guarded field-617
return. It changes only Central Control canonical 2062 and the generated FAT
mirrors that describe its new size. Targets 388 and 507 and every
Krelian-laboratory asset remain absent; target 728 remains the active route's
final room.

V155 removes the second Cross/X requirement from the finale. After dialogue 32
closes, entity 13 keeps control and automatically interpolates from the held
present camera to one whole-room view. Citan then enters through the native
east leaf, crosses the connected floor, and stops at the authentic right
hanging terminal. The same camera remains held through dialogue 35, capsule
launch, and world-map unload.

## Central Control terminal roles

The room retains its exact native terminal assets. Prepared-header nodes 26 and
28 use model entries 3 and 4 for the two-pass right hanging terminal, at world
anchor `(38,-28,139)` with Y rotation `0x0200`. Citan's walkable operating
station is `(60,84)` on walkmesh triangle 23, layer 0, direction 7. Prepared
header node 29/model 5 remains Elly's visible wall computer bank.

Entity 13 remains the only launch controller. It stays at `(-48,97)` on
triangle 16 with no-facing OP18 X/Z operands `0x1C/0x02`, effective reach
`72x20`, and inclusive region X `[-120,24]`, Z `[77,117]`. That one shallow
frontage accepts the captured `(-113,113)`/triangle-15 stance, the earlier
`(-15,113)`/triangle-20 stance, and both F2 readings. No second activation
controller is added. Entity 12 begins at X 25 for a one-unit gap, and entity
14's native east-door region remains disjoint.

The terminal records are byte-exact:

```text
node 26: 10 00 00 00 00 02 00 00 26 00 E4 FF 8B 00 03 00
node 28: 00 80 00 00 00 02 00 00 26 00 E4 FF 8B 00 04 00
node 29: 10 00 00 00 00 00 00 00 00 00 00 00 00 00 05 00

model 3: 860 bytes / 82d8a3a95cdc482094eac44e58ff2de7819beec86d44674a637f6c9acada3328
model 4: 736 bytes / 8e0458a7ec92e52f1d8223e20cfd704960b9d97396cfd8b881e5e1cfa78d7a90
model 5: 2,604 bytes / c868720307d9ceef36efca6e3ee97aed111f39edf02b674f49ec84b911999c85
```

## One continuous memory-to-launch action

The active path is now:

1. Dialogues 12 and 21 play in the present.
2. Exact retail save-point sound bytes `74 50 80` play once, without an added
   wait, immediately before the first fade.
3. A silent reaction leads into memory dialogues 22 through 31 and 36. Only
   entities 17 and 18 are visible; hidden entity 19 remains Miang's point-of-
   view anchor at `(14,58)`. Every memory eye remains `(174,-102,-125)`.
4. Under black, the memory actors and grade clear. The party returns and
   dialogue 32 plays under the established present camera.
5. Dialogue 32 does not restore control. Without a second Cross/X press, the
   action stages Citan and eases over 24 frames to target `(-13,106,-32)` from
   eye `(-27,-767,-544)`.
6. Citan is shown before sound `0x77` and native entity-15 script 4 open the
   east leaf. He walks through `(170,89)/32`, `(100,89)/32`, and `(60,84)/20`,
   then remains direction 7 at the right hanging terminal.
7. Only the leader turns toward Citan. Citan does not turn back toward Elly.
   Dialogue 35 and the launch continue under the same held whole-room camera.

The fresh path reuses the fixed-camera mode already held by dialogue 32; it
does not emit a second `99/9B` prefix. The interrupted compatibility path for
seen bit 12 set and arrival bit 7 clear enters fixed-camera mode explicitly.
Both paths share one reveal/door/walk/arrival-bit suffix. There is no duplicate
static door helper or walking sequence, no conversation retarget, and no
camera release before world-map unload. Completed and authorization-locked
branches remain repeatable and finite.

Dialogue 32 is exactly:

```text
<Emeralda>
"Elly..."<New><Elly>
(Why does this feel so
familiar?)<New><Emeralda>
"Elly?"<New><Elly>
(I remember that...from a
dream?)<New><Elly>
"But no matter, we have a
job to do."<Close>
```

It has width 58, height 5, a 144-byte payload, and SHA-256
`f088d8abd20ac75781cc4e4854edae2831c9881f9a0f9874fe7774facaa5245a`.
Dialogues 33 and 34 remain authored and byte-identical to V154, but no F5 call
can reach either one.

## Byte-level Central Control identity

Target 728 canonical 2062 is 126,316 bytes with SHA-256
`6d7a84c43d702a79cb0481507fc9d4876a3e74b85b68ee236c0597b4e767a07c`.
Its decoded script is 3,488 bytes with SHA-256
`01e2d0ff14babd2d59b51163c2d01d3a6f1eee2617238f1bc4aa0b1cb0c067f4`;
its 4,885-byte dialogue component has SHA-256
`318a95da8d619dd0e9d9a734c2ae0d60b0b1edbcdeed04da56bf465bdf3e455d`.
Entity-13 action script 2 at PC `0x03D5` is 1,008 bytes with SHA-256
`3ccc58171011b9df0e34eb6be2f434845a1fef18753388d030b8bdd5da2e7932`.

The unchanged 24-byte initializer remains at PC `0x033E`, SHA-256
`16495b64a4f39fc843abf026726dddeb615e64412394a78b923100d60a7dcd46`.
Citan's stage script remains PC `0x039F`, 15 bytes, SHA-256
`9a5aa669a5e137e3039f0e744cf0da4a926869f388d2e4a270a4140da5561cbc`.
His shortened walk script is PC `0x03AE`, 39 bytes, SHA-256
`f3176071b2b04a69dbbc20ab1ba81eec6b8f19582a8886d0c1d62d33f4010d9f`.

The action's fresh 29-byte held-mode camera body occurs once at PC `0x0714`;
the 35-byte interrupted-recovery camera occurs once at `0x074F`; and the
single 27-byte reveal/walk suffix occurs at `0x0772`. Native chime bytes occur
once at `0x0454`; dialogue 32 begins at `0x06FC`; the leader-only turn is at
`0x077D`. No Citan-to-leader turn and no camera-release body are emitted.

All 18 entity-13 F5 calls retain flag `0x01`. Their exact PCs are:

```text
03EE 042C 0447 044F 04CA 04FB 052C 055D 058E
05BF 05F0 0621 0652 0683 06B4 06FC 078D 07BD
```

The prepared 1,088-byte header remains SHA-256
`b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31`;
the packed header is SHA-256
`7938dae10e1d02ab0d17cb8b3f6b0614acae2c40459af1afabccb30294dbaf72`.
Only decoded components 5 and 7, script and dialogue, change from V154. The
walkmesh, models, actors, sprites, encounters, triggers, native east-door
controllers, and historical actor initializers are byte-identical.

## Frozen package identity

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v155.bin
size: 696,130,848 bytes / 295,974 raw sectors
SHA-256: 0bc82870566778313dbdaba48ba8459ee88cc43a3b8834b22d4457ac688cbf11

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v155.cue
size: 107 bytes
SHA-256: 49a611cdda251c2f030adc8610e00ee7d6cab5a2057e30fb0f91d6e273aaa5ac

manifest: work/mass_driver_v155_stage/manifest.json
size: 241,652 bytes
SHA-256: 5eed39c013a4bb792ccc34bc130c67fb1fb45c27369d2d5bad9f0f511080456a
jobs / replacements / bytes: 136 / 169 / 11,804,404
route fields / directed edges: 33 / 66
replacement aggregate: 2a3ab8521aa11c69f1e205749a60d3ed85af88b8802e0910e46a8ab967b9555f
framed aggregate: 1e8912d367f4eb580f08069f64da7d49a5374c880a19115dd088e48cc2b1ed95
```

The frozen builder is 1,320,941 bytes with SHA-256
`2bfaa5f4f88dcd5ffa76e00f7e0a1abf217b11b28bf4a13de08e7f27b42cc53a`.
The authored field-369 dialogue JSON is 9,341 bytes with SHA-256
`e583a26ec7d976b6e31745ff1703ad156dd5eb0766bc4551e0695a320618dab0`.

## V154-to-V155 delta and validation

The declared stage delta is exactly canonical 2062. The exhaustive complete-
FAT payload delta is canonicals 17, 22, and 2062: canonicals 17 and 22 differ
only where their generated FAT mirrors record canonical 2062's size changing
from 126,308 to 126,316 bytes. Exactly one of 4,147 FAT descriptors changes:
canonical 2062/physical 2057 remains at LBA 221314. All 61 directory tables and
3,720 of 3,723 extractable payloads are byte-identical.

Exactly nine raw sectors change: LBAs 31, 172926, 221314, and 221370 through
221375. The exhaustive delta contains 6,718 changed user bytes and 8,144
changed raw bytes after valid MODE2/Form1 regeneration. All 169 packaged
replacements re-extracted byte-for-byte. All 5,849 audited replacement,
changed, and boot sectors passed MODE2/Form1 EDC/ECC validation. A
deterministic second stage and BIN rebuild reproduced every gameplay identity;
after the manifest wording correction, a second full rebuild also reproduced
the final 241,652-byte manifest exactly.

The authoritative V155 structural run passed 262 tests / 2,691 successful
subtests in 20.471 seconds with exit 0 and zero failures, errors, failed
subtests, or skips. Fresh user-driven acceptance of the automatic handoff,
whole-room camera, right-terminal Citan station, launch, and return remains
pending.

## Focused-state guidance

Use `work/runtime_capture/near_final_v155_from_v108_vault1.sav`, 1,701,664
bytes, SHA-256
`572a329ffb0c9f0e1771b253f13db84fda6adc4c54b104328d81e81f80ce824d`.
It mounts the exact V155 CUE once, with no V154 media name retained. Historical
V108 field 377 is resident; target 728 is absent and will cold-load from V155
media. Its resident FAT SHA-256 is
`31413e0b788b3ed4e81ad8ffd23f0d6ed3067e0cc91be9eafd968760f837b847`
at payload offset `0x11A66` / RAM `+0x10004`. Migration changes only FAT byte
`+0x3842` from `64` to `6C`; RAM outside the FAT is byte-exact. Flags are
`0x0033`, with bits 4 and 5 set and bits 6, 7, and 12 clear; party bytes are
`01 06 FF`. Ask the player to navigate and press controls; do not automate
emulator input.

Any V154-or-earlier state with target 728 resident cannot validate V155's
automatic post-dialogue-32 continuation, whole-room camera, shortened Citan
route, terminal-facing endpoint, or leader-only turn. Close DuckStation, mount
the exact V155 CUE, and load the focused state above so target 728 cold-loads
from V155 media.

## Historical V154 boundary

Historical V154 release facts follow unchanged.

V154's frozen native-chime and concise-present-response package, state, and
validation record remains byte-for-byte in
[`mass-driver-dungeon-3.15.md`](mass-driver-dungeon-3.15.md). V155 adds the
automatic terminal handoff and whole-room finale composition; it does not
rewrite that historical release record.
