# Mass Driver v86 Auxiliary-room terminal-role correction

Version 86 corrects the physical-object mapping in target field 361. Both
sections of the floor-mounted control bank now operate the Auxiliary Grid, and
the blue hanging terminal now carries the Guidance Archive mail and Directive
0320.

## Runtime evidence and geometry

The August 1, 2026 08:01 DuckStation capture mounts v84 and contains the same
2,135-byte target-361 script used by v85, SHA-256
`f28d44fc3074db9849713b65b172fec35462ef1f369112c13f120b7fcd19da7a`.
Its open mail window and runtime positions prove that entity 12's controller on
the left floor console fired the archive action. The visible hanging screen had
no independent controller because dormant entity 16 still pointed to `STOP`.

The hanging computer is static header node 27/model 2 at yaw `0x0200`. Its
captured approach point lies in walkmesh triangle 7. The new entity-16
controller is centered at `(-40, 97)`, matching that approach, with no facing
requirement and interaction-bound operand `0x08`. Its effective activation
region has a 4-unit gap from the left floor zone and a 42-unit gap from the
right floor zone, so pressing X at one object cannot invoke another object's
action.

## Corrected interaction contract

- Floor entity 12 at `(-31, 165)` uses no-facing bound `0x08`, sets Auxiliary
  Grid bit 0, plays sound `0x37`, and opens switch/status dialogue 1.
- Floor entity 13 at `(110, 117)` uses no-facing bound `0x1E` and performs the
  same Auxiliary Grid action and dialogue.
- Hanging-terminal entity 16 at `(-40, 97)` uses no-facing bound `0x08`, sets
  Directive-record bit 2, and opens Guidance Archive dialogue 0.

The archive's final Elly page now refers to the “floor controls,” matching both
switch sections. Neither floor action contains mail, and the hanging action
contains no Auxiliary Grid write or status dialogue. Existing room-door and
collision pointers remain unchanged.

## Packaged delta

Only canonical ID 1328 differs from v85. The rebuilt target-361 bundle is
89,856 bytes with SHA-256
`cb11efacf12ac68640d151fe26233cb4aca3a558207ee65fb02585385f104c75`.
Its 2,193-byte script has SHA-256
`ca38838eb8df1178ef47921b36bd8af7fc341cc77aaac47f656eeb626d1c8a44`,
and its 1,387-byte dialogue component has SHA-256
`980551a72dd726363dd8fe6126ce5cf6c74f68c15d53b02e0d9c0ca6849e31ae`.
Every other declared replacement is byte-identical to v85, including the
correct El-Regulus name, the distinct subway computer terminal, Attack-Level
progression, deathblows, battle facing, factory encounter, doors, and final-only
Citan sequence.

The packaged artifacts are:

```text
BIN size: 695,293,536 bytes (295,618 raw sectors)
BIN SHA-256:
cc631aa514de0145439e1fdba1bfce6f75ace672fe0e9b72eefae5b262b4975a

CUE size: 106 bytes
CUE SHA-256:
6a41ffac39105afdb821598e8a7ffbcf76254812a79ec52053222e7f2ba4b3fe

manifest size: 187,059 bytes
manifest SHA-256:
2bd78de9c2522210dfd49f769cd4157e3bcf815367ae133c2f9fe9e5eb17392a
```

The manifest contains 126 jobs and 158 declared replacements totaling
10,392,651 bytes. Their canonical-ID-order aggregate SHA-256 is
`0b055ee1306bd5577fe83f40bf8e7f225a59f4dfd11a8441868ab80c2a49ae41`.

The final automated suite passes 204 tests and 2,341 subtests with no failures,
errors, or skips.

## Runtime acceptance

Fully quit DuckStation and boot
`output/Xenogears_PW_CD2_mass_driver_standalone_v86.cue`. Choose New Game and
do not load an older F1 state or in-game save. In the Auxiliary Grid room:

1. Press X at each floor-console section and confirm both show only the
   Auxiliary Grid switch/status sequence.
2. Press X in front of the blue hanging screen and confirm it opens the
   Guidance Archive mail and Directive 0320.
3. Confirm none of those actions fires while standing at either of the other
   two objects.

An older full-machine state restores its resident v84/v85 field script and the
incorrect floor-mail mapping. At minimum, leave and re-enter target 361 from
v86 media before testing; a cold-boot New Game remains the clean full-release
acceptance path.
