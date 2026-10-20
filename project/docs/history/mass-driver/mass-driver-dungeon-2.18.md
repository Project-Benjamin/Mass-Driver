# Mass Driver Dungeon 2.18 - v39 Storage Annex Initialization Repair

Version 39 repairs the reproducible hard freeze after field 372's east
storage-annex door finishes opening. The door action, sound, bounded party
movement, and transition were completing successfully. The crash occurred
on the first update of destination field 722.

## F2-state diagnosis

The pre-door state places the party at field-372 door entity 23. The
post-freeze state proves that field 722 had already loaded, then entered a
recursive address-error exception loop:

```text
PC/NPC: 0x80000080 / 0x80000084
k0:     0x0000002B
CAUSE:  0x00000410
EPC:    0x80000088
```

Field 722's record actor is entity 15 at position `(220, 43, 66)`. The v38
clone had repointed its script 0 from bytecode PC `0x019D` to `0x01AB`.
That skipped the required `INIT_ENTITY_NPC` instruction and began with
`SET_ACTOR_POSITION_2D`. Because the actor's sprite structure was still
null, the position update wrote into low RAM. Its Y coordinate, decimal 43
or `0x002B`, replaced the immediate in the PlayStation exception-vector
instruction at `0x80000084`:

```text
before: 0x275A0C80
after:  0x275A002B
```

The next exception therefore jumped to the unaligned address `0x2B` and
could never return to the field engine. This is why the last visible frame
looked like a door-transition stall even though the destination field was
responsible.

## Repair

Entity 15 now retains its original script-0 pointer at `0x019D`, so the
native NPC initialization always runs. At bytecode PC `0x01A0`, the obsolete
donor story/delete condition is replaced with an unconditional jump to its
existing safe continuation at `0x01AB`:

```text
field 722 / 05_scripts.bin

entity 15 script-0 pointer, file 0x0444:
v38: AB 01
v39: 9D 01

initialization and branch, file 0x0621:
v38: 0B 14 04 02 20 04
v39: 0B 14 04 01 AB 01
     INIT_NPC  JUMP 0x01AB
```

The field-372 source door is unchanged from v38. It still plays the native
Zeboim door sound and animation, uses bounded party movement, and enters
field 722 through the same receiving parameter.

The builder now rejects field 722 unless all of these invariants hold:

- entity 15 script 0 starts at `0x019D`;
- `INIT_ENTITY_NPC` executes before any actor-position opcode;
- the checked branch lands at the original `0x01AB` continuation;
- mutation back to the v38 `0x01AB` entry pointer fails validation.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v39.bin

BIN size: 692,852,160 bytes
raw sectors: 294,580
BIN SHA-256:
267f7d3e1fbcbb3f4c8412222d8981c6544cafbd2c7076521e037c47a6c8de98

packed staged replacement comparison:
138/138 exact, totaling 7,792,342 bytes

only replacement changed from v38:
2050_field_722.bin
size: 55,776 bytes
SHA-256:
b76d7acd49c760922503f55c7efc3ce705aa3a10c7160f9221d00e733637ad96

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 144 passed, 1,854 subtests passed
```

The other 137 packed replacements are byte-identical to v38. Runtime
acceptance is not claimed until the repaired route passes manually.

## Manual acceptance

Do not load an F2 state made with v38. DuckStation states retain the mounted
image and the already-loaded field program.

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and cold-boot v39.
3. Restore auxiliary power and return to field 372.
4. Approach the east storage-annex door next to the auxiliary route and
   press X.
5. Confirm the native sound and sliding animation finish and field 722
   appears.
6. Wait several seconds. Confirm the compass appears, the party separates
   normally, and Elly can move.
7. Inspect the record actor, then leave through field-722 door entity 12.
8. Confirm the party returns to field 372 facing away from the door, with
   movement still enabled.

If any step freezes, press F2 while the frozen frame remains visible before
closing DuckStation.
