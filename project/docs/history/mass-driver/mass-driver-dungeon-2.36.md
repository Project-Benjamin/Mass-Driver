# Mass Driver Dungeon 2.36 - v58 Door and Vault Continuity

> Historical release note: v59 supersedes v58's visually indistinguishable
> closed door with a recessed leaf and stationary dark frame. See
> [the v59 readable-bulkhead notes](mass-driver-dungeon-2.37.md).

Version 58 supersedes the v56 release candidate. It addresses the reported
flat blue/orange bulkhead and the apparent crash after opening it, then closes
the remaining automatic-boundary gap found during sustained runtime testing.

## Native-textured Defense Archive bulkhead

The contrasting synthetic gate is removed. The installer extracts field 394
model 8's original west-aperture `POLY_FT4`, removes that primitive from the
baked wall, and installs an independently movable copy at the same pivot. The
copy retains the retail quad's vertices, UV coordinates, TPAGE, CLUT, and
weathered wall texture, so the closed bulkhead reads as part of the room.

The 136-byte movable model has SHA-256
`7f07b832b0f509cb54cd48e50178d928d44b561f51a08a514073ec493272efde`.
The rebuilt model archive has SHA-256
`f6d4b541628fbf741374e4bde514206f5d9923e8b496900e0c4e26e907f98574`.
The checked entity-14 action still slides the bulkhead, performs the bounded
party walk through its opening, and only then changes to field 377.

## Why the destination looked like a crash

Field 673's retail Cloning Chamber begins under a full subtractive-black
screen layer. Its original cutscene director later lowers that layer. The
cleaned containment-vault clones had parked the director without reproducing
its visual handoff, so the field continued running at Game 30 / Video 60 while
remaining black.

Each of fields 377, 378, 379, 382, and 383 now preserves the donor's safe
initializers and gives entity 6 one startup update. That update changes the
black layer to the donor's visible tint, restores player control, and retires.
No retail story actor, dialogue, cloning vat, or cutscene trigger is restored.

## Continuous automatic boundaries

Each vault has one south and one north boundary script. Both use
`GET_ACTOR_POSITION 2D FF`; operand `FF` resolves through
`partyToFieldEntityArrayMapping[0]` to the current controlled party leader.
This remains correct when party order changes.

The signed Z thresholds are `+760` south and `-760` north. When a threshold is
not met, the script yields one frame with opcode `5A` and jumps back to the
position poll. It no longer reaches `STOP` after checking only once. Successful
checks issue the reciprocal field transition without requiring X:

```text
376 <-> 377 <-> 378 <-> 379 <-> 382 <-> 383 <-> 728
```

## Authorization and prose

The authorization terminal still requires all five correct selections before
setting its progression bit:

```text
Directive 0320
A-2
B-5
C-8
D-4
```

Entering only A cannot authorize the launch or start the Guardian battle.
Wrong answers remain retryable.

Citan's briefing and console directions were also tightened for clarity.
He now says that he followed “another service route” rather than referring
ambiguously to an eastern route, explicitly describes authority points A
through D as separate entries, identifies the later spaces as former research
chambers, and explains the makers' failure to imagine their own disappearance.
All changed pages still pass the retail 59-font-unit by five-line layout
contract.

## Continuation launcher

`output/CONTINUE_MASS_DRIVER_V58.cmd` loads the separate post-Guardian state
immediately before the ordinary bulkhead action. Walk to the weathered west
bulkhead and press K/X. Internal vault boundaries need no button.

The launcher invokes DuckStation in the foreground without `-batch`, keeps
the command window open, and prints DuckStation's exit code when the emulator
closes. This makes an unexpected exit visible instead of allowing the command
window to disappear with it.

## Release artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v58.bin` | 694,823,136 bytes | `c52cc6d60743f52638562a8539f3686605b0d7a92d4cfbc0f22e643cc7f2d37c` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v58.cue` | 106 bytes | `8efd3dc1e574500d1dd306f49b93dd9e92e2655df5edc2df2bdf61dcbfc20f05` |
| `output/MASS_DRIVER_V58_CONTINUE.sav` | 1,807,450 bytes | `aaa8dd812e818cf014ff8796e22681d834d30d1f66ec7c720285e54efea08b5c` |

The stage has 153 unique replacement payloads totaling 9,714,791 bytes. Every
manifest hash and canonical FAT allocation matches. All 4,826 affected
Mode2/Form1 replacement, FAT, executable-header, and boot sectors regenerate
their EDC/ECC exactly. The manifest SHA-256 is
`a19fa386cec1b2781d8ae9c1088fd4efe6580243f2115bcccf787ffc6e0ebd2a`.

The automated suite passes 176 tests and 2,028 subtests.

## Runtime acceptance

The exact v58 image and corrected continuation were tested in DuckStation:

- the packaged state loaded field 376 and remained responsive;
- fresh field 376 showed the integrated native wall/bulkhead, with no
  blue/orange slab;
- the real entity-14 action reached visible field 377 without a crash;
- field 377 remained visible and responsive for more than 56 seconds;
- the valid south-side `+600 -> +800` crossing returned to field 376;
- a real parameter-1 north arrival at `-600`, followed by the adjacent
  `-800` crossing, loaded field 378; and
- field 378's active reciprocal scripts targeted field 377 parameter 1 and
  field 379 parameter 0.

An earlier diagnostic that teleported directly from the south entry at
`+600` to `-800` was rejected: its stale walkmesh state correctly restored the
actor to `+600`. It was not a north-comparator failure and is not counted as
acceptance evidence.
