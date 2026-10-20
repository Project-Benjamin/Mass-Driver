# Mass Driver Dungeon 2.37 - v59 Readable West Bulkhead

Version 59 corrects the closed bulkhead that appeared to be missing on the
west side of the Defense Archive. Version 58 had installed the door as an
exact copy of the original wall quad at the same plane. The action and
transition existed, but the panel had no silhouette, recess, jamb, threshold,
or seam by which a player could recognize it as a door.

## Readable PS1-era construction

The corrected bulkhead separates moving and stationary geometry:

- Model 14 is a 220-byte recessed moving leaf. It keeps field 394's native
  weathered texture, UVs, TPAGE, and CLUT, and adds a dark centre seam.
- Model 15 is a 796-byte stationary frame containing dark olive jambs, a
  lintel, recessed reveals, and a threshold.
- Only the leaf and centre seam slide. The frame remains attached to the room,
  so the open doorway still reads as an architectural opening.

The muted olive-gray values and native wall texture match the Defense
Archive's Zeboim palette. The door does not use the rejected bright
blue-and-orange treatment, modern hazard stripes, or high-contrast materials
that would sit outside the surrounding PlayStation artwork.

The checked model hashes are:

```text
moving leaf:
d6a94032e224a191c17e91d070047e1bf5a1baee37eb3173fcf651350f1a4d16

stationary frame:
a09917ce4136c63d5207afcf5880bf94da81da97d388579febce146d87d87318

16-entry field-376 model archive:
2f95cd1adea3e4eda9c3b8fd13dd9b892294426c24e3fc115317fc93380ed0dc
```

The 896-byte field header has 31 records and SHA-256
`2e234796d3d718ea52790bc9da2e2f9c85daae450841f1cfbdb568c7532ee516`.
Its final static node places model 15 at the audited west-wall pivot:

```text
10 00 00 00 00 00 00 00 C3 FD 00 00 D4 FF 0F 00
```

## Interaction and continuity

The entity-14 action is no longer gated by the engine's narrow facing cone.
Its horizontal half-width is `0x30`, giving a 96-unit activation span across
the full visible aperture instead of the former 60-unit strip. The player can
approach any visible part of the door, press X / Cross, watch the leaf slide,
and see the party walk through before field 377 loads.

This visual and interaction repair does not alter the progression contract:

1. Restore auxiliary power and accelerator-rail power.
2. Enter Directive `0320`.
3. Enter authority points `A-2`, `B-5`, `C-8`, and `D-4` separately.
4. Defeat the mechanical Guardian.
5. Use the dark-framed bulkhead centered between the two console banks.
6. Cross the five containment vaults by walking to each north or south
   boundary; no button is required at those internal transitions.

Entering only `A-2` cannot authorize the launch. Citan still waits beside the
console and speaks only when approached and addressed. The wall terminal
remains usable independently, and the route into field 377 retains the
bounded party walk before the destination is loaded.

## Runtime acceptance

An isolated DuckStation instance loaded field 376 afresh from the final v59
disc. The closed door rendered with its recessed leaf, dark frame, threshold,
and centre seam. A real X / Cross action opened the leaf while leaving the
frame stationary, walked the party through, and loaded a visible field 377.
DuckStation remained responsive.

The supplied continuation begins beside this corrected door. Run:

```text
output/CONTINUE_MASS_DRIVER_V59.cmd
```

Walk to the dark-framed doorway between the two console banks and press K
(the portable keyboard binding for Cross).

## Release artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v59.bin` | 694,825,488 bytes | `e3ce6e7af370aad51d8c1b39a031c2ae5686e221fa36cee1c622b5dcf86013a0` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v59.cue` | 106 bytes | `a1e6acf8d5fd024385d2909657be7b09ad27f9e46d74271c9b8bfe951eb42f18` |
| `output/MASS_DRIVER_V59_CONTINUE.sav` | 1,988,587 bytes | `990d9a5a1bb84fbd29bda6d944f7d4ed46390bc6eaf741dde19b2124926f0056` |

The stage contains 153 replacement payloads totaling 9,715,803 bytes. All
153 payloads re-extract byte-exactly, and 4,827 affected Mode2/Form1
replacement, FAT, executable-header, and boot sectors regenerate with exact
EDC/ECC. The replacement aggregate SHA-256 is
`ffb23f19c6f1c6b5c4441fa466378fbc616570154d4213934bb01baba1ae964c`;
the stage manifest SHA-256 is
`ac86bbfc3f59957eae41169697cfbdceea220af72e24b9fd595b549628be7cdf`.
