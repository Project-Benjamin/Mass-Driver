# Mass Driver v73: Optional Reserve Magazine 02 archive terminal

Version 73 moves Reserve Magazine 02's long historical record out of the
room-entry path and onto a visible archive terminal. Target 378 now enters
silently, so crossing the room no longer forces the 6083 launch log and 6079
mail thread to replay. Players who want the exposition can approach the
terminal, press X / Cross, and reread the complete record at any time.

This is a targeted delivery change. The automatic north and south boundaries
remain active, and Reserve Magazines 01, 03, 04, and 05 (targets 377, 379,
382, and 383) retain their short automatic observations. The v72 two-character
dungeon, Guardian battle, final Citan handoff, launch, and world-map return
contracts are otherwise unchanged.

## Archive-terminal implementation

The console is a distinct, texture-free field object rather than another
save-point-like memory terminal. It reuses previously parked static model 0
and static node 22, placing the visible console at `(500, 0, 0)`. The flat
shading and compact industrial silhouette identify it as local archive
hardware without adding a texture or VRAM dependency.

Retired entity 7 now owns the interaction controller at `(420, 0)`. Its
X / Cross action presents dialogue block 0, which contains the 6083 launch
log followed by the complete archived 6079 political and military-pressure
mail thread. The action is repeatable, does not set a progression flag, and
does not control either room boundary. Walking through target 378 therefore
requires no terminal interaction.

The target-378 contract is:

```text
enter from Reserve Magazine 01 or 03
    -> no automatic dialogue
walk to the archive console and press X / Cross
    -> read the complete launch log and political mail
    -> terminal remains available for another reading
continue through either room edge
    -> existing automatic reciprocal transition
```

## Packed v73 target-378 resources

The v73 manifest records these target-378 replacements:

| Component | Canonical ID | Size | SHA-256 |
| --- | ---: | ---: | --- |
| Reserve Magazine 02 field bundle | 1362 | 93,824 | `40c16f67d39a075718ba612013b22374ce2bb80dd3f0004aa5da9a8abd4aca58` |
| Reserve Magazine 02 graphics | 1363 | 102,400 | `e58a4c0f5aacffbf500c31879e0795238af402d3bfb8d83dfca46df454dca2ed` |

The corresponding embedded authored payloads are:

| Payload | Size | SHA-256 |
| --- | ---: | --- |
| target-378 script | 3,494 | `e1e36173bf5bf9cf7073b2588e58e7f62d1f8aefa1a35d18ec269a00ed427ca6` |
| target-378 dialogue | 736 | `fd19f01c182c3f034d90b2ae27a50656599575f1e3037e52debade0b30aa2270` |

## v73 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v73.bin` | 695,531,088 | `8f816b2e8569d73657350221ed26ec3336b02ed6a031d3aaf5f0f07453225992` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v73.cue` | 106 | `85646fbbd0c57ca5e0729313fd3459a74bc3e98f82f3822cdd2b31525174630a` |
| `work/mass_driver_v73_stage/manifest.json` | 177,480 | `09ba8d2c210930821bd2c220af82b280eaaa6d07e4cd88b3748229949d30721c` |

The image contains 295,719 raw sectors.

## Validation and cold-boot requirement

The final automated suite passes **192 tests and 2,226 subtests**. All 156
declared replacements re-extract byte-exact from the disc, totaling
10,403,575 bytes; their canonical-ID-order aggregate SHA-256 is
`1180b9589f5273bebdbdb4c1c35be40a6b3929926b841354f4ad52f8b35ea9c5`.

The 5,146 unique replacement sectors, standalone boot sector, FAT sectors,
and executable-header sector all regenerate byte-exactly as MODE2/Form1 with
valid EDC/ECC. The complete retail comparison finds 108,759 changed common
sectors and 3,008 output-only sectors; all 111,767 regenerate exactly, with
zero invalid sectors and zero mismatches. All 3,565 ordinary undeclared FAT
files remain byte-identical, totaling 624,830,534 bytes.

Focused runtime visual acceptance is also pending. In particular, validation
must begin from a cold boot of
`output/Xenogears_PW_CD2_mass_driver_standalone_v73.cue`. A save state made
while target 378 is resident contains the earlier room script and asset state
in gameplay RAM; changing the mounted image cannot replace that resident
state. Do not use such a state to judge the silent entry or new console.

Cold-boot acceptance must confirm:

1. Entering target 378 from either adjacent magazine does not open dialogue.
2. The archive console is clearly visible and visually distinct from a save
   point.
3. X / Cross at the console presents the complete 6083 launch log and 6079
   mail thread.
4. Closing the record and pressing X / Cross again rereads it without a
   progression-state dependency.
5. Both automatic room-edge transitions still work without interacting with
   the console.
6. Targets 377, 379, 382, and 383 retain their short automatic observations.
