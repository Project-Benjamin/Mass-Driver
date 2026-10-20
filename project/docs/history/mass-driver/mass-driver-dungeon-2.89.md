# Mass Driver v113 Zeboim station collision repair

V113 makes all seven transplanted field-373 Zeboim freestanding stations
physically solid. Earlier releases installed the authentic static model,
textures, palette, and repeatable Cross/X controller, but the controller was a
script-only field entity. The station therefore looked correct while allowing
the party to walk through it.

The repair covers:

- target 721's archive station inside the stationary subway train;
- target 727's new personnel time-clock station in the three-door operations
  junction; and
- the five reserve-magazine archive stations in targets 377, 378, 379, 382,
  and 383.

## Native collision contract

Each station's existing controller now initializes as an invisible native NPC
contact actor centered on the static model. Opcode `0x18` uses operand `0x1C`,
which the field engine expands to a 56-unit horizontal extent around the
approximately 80-by-80-unit station footprint. Dynamic flag `0x10` makes the
contact actor immovable, and opcode `0x23` hides its carrier sprite without
removing collision. The interaction-disable opcode is deliberately omitted,
so the same actor continues to own the repeatable script-2 Cross/X action.

This keeps art, collision, and interaction tied to one audited location:

| Area | Field(s) | Entity | Collision/controller center | Facing policy |
| --- | --- | ---: | --- | --- |
| Stationary subway | 721 | 14 | `(-1025, 185)` | proximity-only |
| Operations junction | 727 | 18 | `(-147, -42)` | proximity-only |
| Reserve magazines | 377, 378, 379, 382, 383 | 7 | `(500, 0)` | face the controls |

The authentic field-373 model, its static transforms, texture atlases, and the
existing archive mail remain unchanged. The six separate warhead colliders in
each reserve magazine also remain intact.

## Target 727 personnel notice

V113 includes the station added at Elly's captured position in the operations
junction. Its repeatable notice reminds facility personnel to clock in and out
whenever entering or leaving, report suspicious activity to a supervisor, and
stay current with safety protocols. It writes no progression state and does
not overlap any of the junction's three animated doors.

## Packaged release

```text
BIN:
output/Xenogears_PW_CD2_mass_driver_standalone_v113.bin
size: 696,431,904 bytes
SHA-256: 870f65f30c39f977a14dbe5837bb95108d1a7d6989f80259ef3da78f9c1f0aa5

CUE SHA-256:
369746145a816a37642f0478a499afbb198dfc9206407a1150117e1a5868ba04

staging manifest SHA-256:
9f918bd40c7f7744b73eced431334fa3255408b4f650b2519575284d8e7913a1

build inventory: 130 jobs / 166 replacements
packaged payload extraction: 166 / 166 exact
```

Every staged replacement was extracted from the finished disc image and
matched byte-for-byte. After a complete target-727 reload, the user confirmed
that the station blocked movement from its sides and that its personnel notice
still opened. That replay also exposed a narrower issue: because entity 18
owned both the centered collision volume and the X action, the notice could be
selected while standing at a side. V114 supersedes that combined controller
with separate collision and front-only reader entities.
