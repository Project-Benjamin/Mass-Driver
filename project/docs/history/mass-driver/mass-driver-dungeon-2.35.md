# Mass Driver Dungeon 2.35 - v56 Containment Vault Route

> Superseded by [v58](mass-driver-dungeon-2.36.md). This page preserves the
> historical v56 build record; its synthetic bulkhead and initial vault
> reveal/proximity implementation are not the current release.

Version 56 replaces the superseded three-gallery tail with five containment
vaults and carries the playable route from the Defense Archive to Central
Control:

```text
726 <-> 376 <-> 377 <-> 378 <-> 379 <-> 382 <-> 383 <-> 728
        Defense      five containment vaults              Central
        Archive                                            Control
```

The complete standalone build now contains 31 target fields.

This remains an original, canon-conscious fan reconstruction. The five new
rooms deliberately adapt retail field 673's Cloning Chamber architecture.
They are not recovered Square scenes, official cut-content rooms, or evidence
that the retail Cloning Chamber canonically belonged to the Mass Driver.

## Defense Archive continuity

Target 726 still opens normally into target 376 through field 394's east
service-stair threshold. Elly and Emeralda retain the inward-facing receiving
position. No automatic conversation moves them to the center of the room.

Citan loads during the fade and waits beside the genuine wall console, clear
of its activation area and Emeralda's follower path. His briefing starts only
when the player faces him and presses X/Cross. The wall console remains
independently usable before or after that conversation.

The authorization terminal now expresses its actual five-step contract:

1. select Directive `0320`;
2. select authority point `A-2`;
3. select authority point `B-5`;
4. select authority point `C-8`;
5. select authority point `D-4`.

Each authority point has its own choice window. The terminal writes the launch
authorization bit only after all five selections match. A wrong selection
reaches the retryable rejection path and cannot grant partial authorization.
The two archive flags remain optional knowledge flags: if one was missed, the
terminal identifies its location and still permits manual entry.

The accepted sequence deploys the expired Zeboim custodian. Elly in
El-Regulus, Emeralda in Crescens, and Citan in Fenrir fight the retained
36,000-HP Guardian. Victory returns the complete party to target 376 and sets
the bit that unlocks its west bulkhead.

## Detailed west bulkhead

The west aperture no longer relies on field 394's single baked textured door
quad. Version 56 replaces it with a deterministic, texture-free PS1 field
model that exactly fills the opening.

The replacement has recessed paired leaves, a central seam, raised edge
rails, and restrained orange bands. It adds no texture, CLUT, TPAGE, sprite,
or VRAM dependency. The checked door helper supplies the bounded sliding
animation and the reciprocal transition between target 376 and the first
vault, target 377.

The bulkhead remains sealed while the custodian defense is active. It unlocks
after Guardian victory; the authorization sequence by itself does not bypass
the fight.

## Field-673 architectural adaptation

Targets 377, 378, 379, 382, and 383 are five independent builds from retail
field 673's Cloning Chamber geometry. The conversion removes:

- the retail story cast;
- the retail story director and event scripts;
- the three obsolete raw scene-transition signatures;
- all six glass-vat placements from each room.

The installer preserves only safe room infrastructure such as lighting,
music, party handling, and the audited geometry needed by the new route.

Each vault receives six original, texture-free, flat-shaded vertical
warheads on audited static anchors. That gives the five-room sequence 30
visible warheads:

| Target | Vault | Vertical warheads |
| ---: | ---: | ---: |
| 377 | 1 of 5 | 6 |
| 378 | 2 of 5 | 6 |
| 379 | 3 of 5 | 6 |
| 382 | 4 of 5 | 6 |
| 383 | 5 of 5 | 6 |
| **Total** |  | **30** |

The visual development reference is
[the Cloning Chamber warhead concept](../../../assets/mass_driver/cloning-chamber-warhead-concept-v1.png).
It documents the intended PS1-era silhouette; it is concept art for this
adaptation, not a retail Xenogears asset.

The recognizable laboratory-like shell is recontextualized as strategic
payload storage. That explanation belongs to this reconstruction's authored
continuity. It must not be presented as a recovered scene involving Kim,
Taura, or a canonical Zeboim military conversion of the retail Cloning
Chamber.

## Automatic vault boundaries

Every vault uses full-width north and south proximity checks. Crossing the
north threshold advances along the route; crossing the south threshold
backtracks. These are reciprocal field transitions:

```text
376 <-> 377
377 <-> 378
378 <-> 379
379 <-> 382
382 <-> 383
383 <-> 728
```

There is no X/Cross prompt, animated door, or narrow interaction hotspot at
an internal vault boundary. The player proceeds by walking to the far end of
the room. The opposite end immediately provides the return path.

The fifth vault enters target 728 Central Control. Its visible return door
leads back to target 383 parameter 1. Central Control's separate entity-13
console still requires accepted launch authorization, releases Taura's
nanomachine capsule once, and reports active dispersal on later use.

## Release artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v56.bin` | 695,366,448 bytes / 295,649 raw sectors | `8a608977f0c1b17b512fb37c84f3336ae0ae7cb05a4692321a83c507b0fad126` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v56.cue` | 106 bytes | `40b2fa23b77f0faf63bdea31fdf7e7d5b27fa729c58fece7be1e8421d870064b` |
| `output/MASS_DRIVER_V56_CONTINUE.sav` | 1,776,480 bytes | `420a95573f28a0b805f7c587c6b7abea5f3e15cabfb2540f61479f8b51952f36` |

The continuation launcher is:

```text
output/CONTINUE_MASS_DRIVER_V56.cmd
```

The launcher defensively omits `-batch`. The canonical continuation was
rebuilt directly from the known-good v54 state. Its type-2 zstd header records:

- data offset: 78,340 bytes;
- compressed size: 1,698,140 bytes;
- uncompressed size: 3,819,074 bytes;
- `data offset + compressed size = 1,776,480`, exactly the file size.

The earlier continuation with SHA-256 beginning `840158e5` is superseded. Its
compressed-size header was stale, so its earlier mount/“began loading”
observation was not sufficient continuation validation.

The v56 stage contains 153 replacement payloads totaling 10,187,371 bytes.
Its manifest SHA-256 is
`02514cb874890be6eb94ad6ce993257a30c83156cf7c8343462efbe2c97ce562`.

## Validation status

Frozen release validation established:

- the full automated suite passed 175 tests and 2,028 subtests;
- 153 of 153 replacement payloads re-extract byte-exactly;
- all 5,040 unique raw replacement and boot sectors regenerate byte-exactly
  with valid MODE2/Form1 EDC/ECC;
- a hidden portable DuckStation run reused the same v56 media, logged
  `System booted in 285.09ms`, and remained running for 15 seconds until the
  diagnostic stop.

The new DuckStation evidence supersedes the earlier mount/“began loading”
claim and verifies that the repaired continuation reaches a stable emulator
boot. It does not prove gameplay traversal. A hands-on full traversal of the
new five-vault sequence remains pending and must not be reported as complete.

## Pending hands-on traversal

1. Enter target 376 normally from target 726. Confirm Elly and Emeralda remain
   at the east threshold, no conversation opens automatically, and Citan
   waits beside but clear of the wall console.
2. Use the wall console before speaking to Citan, then speak to him with
   X/Cross. Confirm both interactions remain independent.
3. Confirm the terminal presents Directive 0320 and authority points A, B, C,
   and D in five separate choice windows. Reject one wrong selection, retry,
   and verify authorization is not set before all five correct entries.
4. Defeat the Guardian, return safely to target 376, and confirm the detailed
   west bulkhead unlocks and slides into target 377.
5. In targets 377, 378, 379, 382, and 383, confirm six vertical warheads per
   room and the absence of retail story actors and glass vats.
6. Cross every north and south boundary without pressing a button. Confirm the
   complete forward route and immediate reciprocal backtracking.
7. Enter target 728 from target 383, use its return door, then re-enter and
   launch Taura's capsule. Confirm later console use reports dispersal instead
   of launching a second payload.

## Historical boundary

[Version 55](mass-driver-dungeon-2.34.md) remains the historical source for
the retained natural Defense Archive arrival and player-triggered Citan
briefing. Its three source-385 missile galleries, 24 missiles, gallery record
scenes, and `376 -> 377 -> 378 -> 379 -> 728` tail no longer describe the
current v56 build.
