# Mass Driver v96 El-Regulus battle-entry facing correction

V96 completes the El-Regulus combat-facing repair while retaining the entire
v95 dungeon, archive branch, Central Control finale, party, encounters, and
item progression. The change is isolated to Gear 10's model-local battle-entry
animation in canonical 2960. The shared battle overlay remains exact retail.

## Root cause and rendered evidence

The preserved battle capture places El-Regulus at root yaw `0x0C00` with the
Guardian due west. In this model, `0x0C00` presents El-Regulus's back, while
`0x0400` presents its front toward the Guardian.

Canonical 2960 animation 0 contained source command `43 00`, which asks the
model to face its own root. That self-target produces a zero vector, so the
command is a no-op and leaves the enemy-side formation yaw visible. Restoring
canonical battle overlay 38 in v89 correctly removed the earlier shared
slot-zero override, but it could not change this separate model-local no-op.

A yaw-only A/B probe from the same preserved v88 battle establishes the visual
target directly; it does not stand in for the pending cold-boot v96 run:

- Root yaw `0x0C00` produces the rear view.
- Root yaw `0x0400` produces the front toward the due-west Guardian.

The interpreter audit below establishes that v96's signed relative packet
maps the first yaw to the second.

## Isolated animation-0 patch

V96 replaces animation 0's two-byte self-target command with this aligned
root-0 relative-rotation packet:

```text
source:  43 00
v96:     62 20 00 00 00 00 00 F8 00 00
```

The packet's signed yaw operand is `-0x0800`. Applied to the captured
`0x0C00` rear yaw, it yields `0x0400` modulo the engine's `0x1000` turn. Because
the turn is relative, the same half-turn correction remains formation-relative
rather than hard-coding a single absolute direction.

The insertion adds eight bytes and relocates only subsequent animation
pointers. Animation 0 retains its checked completion tail. El-Regulus's model,
all standard attacks, Level-1 programs, Level-2/3 and Infinity deathblows, and
every other animation remain byte-identical to v95. Crescens and all enemies
are untouched.

Canonical 2960 changes as follows:

| Build | Size | Outer roots | SHA-256 |
| --- | ---: | --- | --- |
| v95 | 33,600 | `(2, 0x10, 0x7FF4, 0x8340)` | `627b332e5b2c15ca7e99d7d44e76fa8f72291634dbbfc32aae1ab19ef511c8c6` |
| v96 | 33,608 | `(2, 0x10, 0x7FFC, 0x8348)` | `86807cb3d54acb40649b174e384f31aa82a167274976faa2e7ed283c2b62ec0a` |

Canonical battle overlay 38 remains the exact retail 166,665-byte packed
resource with SHA-256
`93a4179fe3b31a4fffb9fe723f63511f15de5177bbfcbca2529124a4108ffbb1`.
Its decoded 343,948-byte payload remains SHA-256
`ad4586923095715288377caea89f2cd15d70a2f80ef53394e2faec22b2e0b825`.

## Packaged v96 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v96.bin`: 695,834,496
  bytes / 295,848 raw sectors, SHA-256
  `3036603c64a90c5d9aa85d3f151ff5dc09b9acde38fb5fce1170e1c2d32321c3`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v96.cue`: 106 bytes,
  SHA-256
  `1f01684d7b2362225a14afcf006d2583ed64c12cd5ce109cc941810d46c857f1`
- Manifest `work/mass_driver_v96_stage/manifest.json`: 197,551 bytes,
  SHA-256
  `2d40573a371e47e4690df12186155793affe13c7e7cb27ed5d5273bde3195366`
- Replacement aggregate: 128 jobs, 162 declared replacements, 10,870,892
  bytes, SHA-256
  `10115658aedc15b3f91e3394df776858d625e652866e0c656003bd87dcd74327`

Only canonical 2960 differs from v95. Every other declared replacement is
byte-identical.

## Runtime acceptance

Fully quit DuckStation and cold-boot
`output/Xenogears_PW_CD2_mass_driver_standalone_v96.cue`. Choose New Game and
load no older F1 state or in-game save.

The facing packet is loaded as part of canonical 2960 when a battle starts. An
F1 state saved inside an older battle restores the old mounted disc and the old
resident animation, so resuming it cannot validate v96. Enter a completely new
battle from v96 media.

In the factory Guardian encounter, confirm that El-Regulus presents its front
toward the due-west Guardian from the opening pose through command selection.
Confirm that Crescens and the Guardian retain their normal orientation, all
three standard attacks and every deathblow still complete, Attack Level still
advances normally, victory returns both pilots to the factory hall, and the
human-sized lift still dismounts them for the return to the Defense Archive.
