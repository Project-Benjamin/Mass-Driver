# Mass Driver Dungeon 2.38 - v60 Narrative and Runtime Completion

Version 60 completes the missing playable journey through the Mass Driver
facility and connects it to the sequence already shown in the released game.
The new dungeon remains a canon-conscious reconstruction, not recovered Square
content: it supplies the route that Elly describes, then hands the story back
to Xenogears's authentic Mass Driver launch event when Taura's nanomachine
capsule is fired.

## Dialogue and plot continuity

All 31 dialogue specifications used by the active dungeon fields were revised
as one continuous script. The acclaimed opening exchange with Citan in the
Defense Archive remains textually unchanged. The rest now follows the same
dramatic line:

1. The party discovers that the Mass Driver began as a civilian
   surface-to-space freight system.
2. Zeboim records show its conversion into a strategic launch network, the
   genetic crisis, and the civilization's nuclear destruction.
3. Kim's molecular-machine work provides the historical link to Taura's
   nanomachines without treating the two technologies as the same invention.
4. Citan explains why the facility, the three Gears, and the old authorization
   system are still relevant to the present mission.
5. The containment-vault text builds toward the moral weight of walking
   through preserved weapons rather than repeating disconnected terminal lore.
6. Central Control identifies the payload as Taura's nanomachine capsule and
   leads directly into the released game's launch sequence.

Elly carries the reflective and moral observations, Emeralda asks direct
questions grounded in her connection to Kim's era, and Citan supplies measured
technical context without knowing more than the surviving evidence permits.
Every page still passes the game's manually checked 58-by-5 dialogue-window
contract. The completed-launch report moved to its own repeat-interaction block
so it can no longer appear before the capsule is fired.

## Five-stage authorization and Citan handoff

The Defense Archive's native wall console now treats the directive and four
authority points as five independent entries:

```text
Directive 0320
A-2
B-5
C-8
D-4
```

The authorization bit is written only after all five comparisons succeed.
Entering the first correct letter or point cannot skip the remaining prompts,
and every wrong answer returns to a safe retry. The two archive records are
useful clues, not invisible prerequisite flags: if one was missed, the console
names its location and still permits manual entry.

Elly and Emeralda retain their natural arrival at field 376's east threshold.
Citan is already standing beside the console, and his briefing begins only
when the player approaches, faces him, and presses X / Cross. Before
authorization he is a stationary, solid talk actor with a deliberate collision
radius, so the player cannot walk through him. Once the full code is accepted,
his talk collision is cleared and the native party-follow update resumes. He
then merges into the moving party as a non-solid follower for the Guardian
battle and the vault route.

## Paired Defense Archive bulkhead

The west exit is now a recognizable, PS1-era paired bulkhead rather than a
flat panel:

- model 14 is the screen-left moving leaf;
- model 15 is the screen-right moving leaf;
- model 16 is the fixed jamb, lintel, reveal, rail, and threshold assembly.

The two leaves divide field 394 model 8's weathered native wall texture at the
centre UV. Low-poly edge caps, rails, and split lock plates add depth while the
dark olive frame stays attached to the room. The palette and texture source
therefore remain part of the Defense Archive instead of introducing a modern,
high-contrast door.

Each leaf uses an unrolled 24-frame `OP19` world-position sequence. They move
two world-Z units per frame in opposite directions, with retail `WAIT 0`
yielding between positions. The routines are finite and asynchronous; they do
not apply the primitive-buffer `FE1B` mutation that stalled on the detailed
multi-polygon leaves in the first v60 candidate. The controller then walks the
party through the visibly open aperture before loading vault 1.

| Bulkhead asset | Size | SHA-256 |
| --- | ---: | --- |
| left leaf | 1,100 bytes | `0e80a900c655241f7560f4156493e06a04531d2facffe214c4ab0d8c01f2d10e` |
| right leaf | 1,100 bytes | `06f431a8186d22231a143446bdbba67bc723ff563a5da19b37533657a160de33` |
| stationary frame | 2,084 bytes | `926579beb306cb33fa4dbd2417848ece59c7604a066c98245624953d80098a6e` |
| 17-entry model archive | 56,452 bytes | `54052a05ac8c74e106dd18c443eff9a5e2bd12ee9c0156c737bcb2e878716315` |
| 32-record field header | 912 bytes | `357a8a96a967739d0b7ee2d2991dc94b4874093b63b11434ef6d1cf42aa8aa56` |

The facing-independent action has a 48-unit half-width, covering the full
96-unit visible aperture.

## Five Cloning Chamber containment vaults

Fields 377, 378, 379, 382, and 383 reuse retail field 673's Cloning Chamber
architecture. Its six glass vats, retail cast, dialogue, triggers, and cutscene
director are removed from every copy. Each vault instead places six new
vertical nuclear warheads, giving the route 30 visible warheads.

The texture-free, flat-shaded model was built for the native field renderer.
Its 185 vertices and 280 triangles form a stepped casing, recessed panels,
seams, a floor-contact plinth, and four support feet. Its bounds are
`(-70, -660, -70)` through `(70, 0, 70)`, so the feet meet the audited floor
plane rather than leaving the body floating.

```text
warhead model size: 4,916 bytes
warhead model SHA-256:
c4395859e42c495b474db857ddb560be89ea012c60fcf71dc553268948c87c2d

patched model archive SHA-256:
26a636bdab842d2eb08deb04514f86c630b0131be855235e3eb9f973d1c088c3
```

Six fixed NPC collision actors occupy the same anchors as the six static
models. Each has a 72-unit radius and the field engine's immovable-contact
flag. They remain stationary under sustained player input and prevent the
party from walking into or through the warheads.

The north and south boundaries poll the controlled party leader every frame.
Crossing Z `-760` or `+760` loads the adjacent vault automatically; X / Cross
is not required. The complete reciprocal route is:

```text
376 <-> 377 <-> 378 <-> 379 <-> 382 <-> 383 <-> 728
```

## Authentic Mass Driver launch event

Central Control's successful action sets the standalone completion flag and
the retail Mass Driver return flag, then invokes the released game's exact
world-map sequence at position `0x0FFF`, mode `17`. This is a field-triggered
world-map event, not an MDEC movie.

Retail mode 17 returns through field 617, parameter 2. Canonical bundle 1840
therefore has a narrow guard around entity 9 script 1:

- the standalone completion path clears the retail return flag and sends the
  intact Elly, Emeralda, and Citan party to playable world-map position 21;
- every ordinary retail parameter and save jumps to the unchanged retail
  director path at script PC `0x0572`;
- the mod does not call retail entity 32 script 4, which would remove the
  current party and restore only Elly.

The patched canonical 1840 bundle is 71,172 bytes with SHA-256
`08b2bb684843f10b1d24bee557ae691897d1fb8e2da29118d37bc4d69ade3f49`.
Its script component is 15,544 bytes with SHA-256
`a13e2bbdb71812901b834cace779ee5fa7802f57ca5b1e8c2d389eb1ed0a85bb`.
Automated bytecode tests verify the exact mode-17 call, the guarded field-617
branch, preservation of the ordinary retail path, and the one-time launch
flag.

Hands-on launch-sequence status: passed end to end on the exact frozen v60
image. Central Control committed the capsule, retail mode 17 began normally,
the released nanomachine aurora and atmospheric-dispersal views appeared, and
playable world-map control returned with the Elly, Emeralda, and Citan party
unchanged. Runtime evidence includes
[the committed launch](../../../work/v60_launch_cutscene_validation_ds/screenshots/Xenogears%20(Disc%202)%202026-07-29-17-50-14.png),
[mode 17 beginning](../../../work/v60_launch_cutscene_validation_ds/screenshots/Xenogears%20(Disc%202)%202026-07-29-17-51-43.png),
[the visible dispersal](../../../work/v60_launch_cutscene_validation_ds/screenshots/Xenogears%20(Disc%202)%202026-07-29-17-52-14.png),
and [the playable return](../../../work/v60_launch_cutscene_validation_ds/screenshots/Xenogears%20(Disc%202)%202026-07-29-17-53-48.png).

## DuckStation runtime acceptance

The paired door passed on the exact frozen BIN in an isolated portable
DuckStation profile. The sequence is recorded
[closed beside the party](../../../work/v60_runtime_validation_ds/screenshots/35_finalfinal_field376_closed_beside.png),
[with an early centre gap](../../../work/v60_runtime_validation_ds/screenshots/36_finalfinal_bulkhead_early_open.png),
[with both leaves fully outward](../../../work/v60_runtime_validation_ds/screenshots/37_finalfinal_bulkhead_late_open.png),
and [after the unattended field-377 transition](../../../work/v60_runtime_validation_ds/screenshots/38_finalfinal_bulkhead_transition_complete.png).
Game FPS remained at 30, both leaves moved outward, and field 377 loaded
without the former script stall.

The automatic route passed in both directions:
[north from 377 to 378](../../../work/v60_runtime_validation_ds/screenshots/27_final_auto_north_into_vault2.png)
and [south from 378 to 377](../../../work/v60_runtime_validation_ds/screenshots/31_final_auto_south_into_vault1.png).
No transition required a button.

Sustained movement into a field-378 warhead produced identical stopped player
positions in the
[first hold](../../../work/v60_runtime_validation_ds/screenshots/28_final_warhead_collision_first_hold.png)
and [extended hold](../../../work/v60_runtime_validation_ds/screenshots/29_final_warhead_collision_extended_hold.png);
the [clean follow-up frame](../../../work/v60_runtime_validation_ds/screenshots/30_final_warhead_collision_stopped_clean.png)
shows the player outside the model. Runtime RAM placed the player at X
`569.941` and the warhead at X `661`, a 91.06-unit separation against combined
16- and 72-unit radii. All six collider actors retained their authored
positions, zero movement step, radius 72, immovable flag, and enabled update
state.

The vault, boundary, and collision pass used the immediately preceding v60
image; those five vault resources are byte-identical in the frozen build. The
paired-door recheck used the frozen BIN SHA-256
`678737b934d898a13dbcc94d6a9f715980af4625e1f6d502c4319e992b606825`
directly.

## Frozen release integrity

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v60.bin` | 694,844,304 bytes | `678737b934d898a13dbcc94d6a9f715980af4625e1f6d502c4319e992b606825` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v60.cue` | 106 bytes | `ab4a76905170aa3a03921818f1464aeaa663a0b678647651da5b30b697048423` |
| `work/mass_driver_v60_stage/manifest.json` | 169,512 bytes | `4da2aba924e1b5ee07626b58216168564fd7dd19e55b08ad08564e81dd11e6c1` |
| `output/MASS_DRIVER_V60_CONTINUE.sav` | 1,975,307 bytes | `fa9880cdab354ddf2b4d17ce3dce951c78a09dace1d6ece70135824bf005e200` |

The BIN contains 295,427 raw sectors. The stage contains 154 replacement
payloads totaling 9,799,687 bytes; their aggregate SHA-256 is
`f952fe3dd7469829c7922e03f75069ea3652a9e184f583e8165e659513eec3c2`.
All 154 payloads re-extract byte-exactly from the frozen image. The 4,852
unique replacement sectors, plus the boot sector, regenerate byte-exactly
with valid MODE2/Form1 EDC/ECC.

The complete automated suite passes 181 tests and 2,043 subtests. It covers
the five independent authorization comparisons, Citan's solid-to-follower
state transition, paired finite door helpers, detailed warhead geometry and
collision scripts, ten yielded controlled-leader boundary loops, all 31
active dialogue specifications and their window layout, the retail mode-17
call and guarded party-safe return, replacement re-extraction, and raw-sector
integrity.

Run the fresh continuation with:

```text
output/CONTINUE_MASS_DRIVER_V60.cmd
```

The continuation was saved from a freshly loaded field 376 on the frozen
image. Its sole resident archive table has SHA-256
`a8c0727abb76a125f24ccab0c1d665f626705a2f104b652f4758689efc97f952`.
At capture, the party and closed bulkhead were at their audited positions:
the player at `(-539.983, 0, 0)`, controller entity 14 at `(-530, 0, 0)`, and
both shut leaves at `(-573, 0, -44)`.

The launcher keeps DuckStation in the foreground, omits `-batch`, leaves its
console open if the emulator exits, and reports the process exit code.
