# Mass Driver v114 operations-junction station frontage

V114 keeps target 727's personnel station solid on every side while limiting
its Cross/X notice to the visible controls on the front. V113 correctly made
the transplanted station physical, but one centered entity owned both the
collision volume and the interaction. A player standing at either side could
therefore face the center and satisfy the same proximity action.

The captured live stance places Elly at `(-88.55, -42.18)`, directly east of
the station and facing its controls. The static model remains centered at
`(-147, -42)` with yaw `0x0E00`, so this is its positive-X frontage.

## Split native entities

V114 separates physical collision from the reader without changing the
station model, textures, palette, notice, or surrounding doors:

- Entity 18 remains centered at `(-147, -42)`. It is an invisible,
  immovable native NPC contact actor with collision operand `0x1C`, giving a
  56-unit runtime extent. Its carrier sprite is hidden, its interaction is
  explicitly disabled, and every non-initialization script is STOP. It blocks
  movement from the front, sides, and rear but cannot consume Cross/X.
- Entity 19 is a non-solid script controller at `(-108, -42)`, aligned to the
  model's positive-X front face. Its native facing gate requires Elly to aim at
  the controls. Bound operand `0x04` gives 24 units of effective reach, enough
  for the captured stance while excluding both side approaches. Its only
  active action is the repeatable dialogue-4 personnel notice.

Target 727's header now contains 23 records and is 768 bytes. Entity 19 is
inserted before the retained static nodes, and the Zeboim station becomes
static node 22 while remaining model 5 at its unchanged transform.

```text
target-727 raw header:
size: 768 bytes
SHA-256: 1154bd7a0d3941bf9f2240e889ce5ed94b463f2d2888684df3b3e6d9135a81a0

target-727 script component:
size: 1,967 bytes
SHA-256: 260532677b880496a34d8cf4e8270b4a19df6a2dd6d75df5d301c6b01d656800

canonical 2060 field bundle:
size: 43,936 bytes
SHA-256: eae00cd55d1eef87f3d9e028b6c82bff18857c774f9438a946753e079659f809
```

## Packaged release

```text
BIN:
output/Xenogears_PW_CD2_mass_driver_standalone_v114.bin
size: 696,431,904 bytes
raw sectors: 296,102
SHA-256: b0a8c915256c62a3cdb362ccb4dbbb5557fd9cb442f27b54e7ed64204c325570

CUE:
size: 107 bytes
SHA-256: 49868d80c10a226ea1a774a66ec1d64c6b7c14dcc5d7e400ca4e060954a721eb

staging manifest:
size: 213,694 bytes
SHA-256: a5bfe2cd95ab1f48c7f0309ded766afc6977b9f839dc27b55c7c2a76fcba6057

build inventory: 130 jobs / 166 replacements / 11,393,752 bytes
canonical-order aggregate SHA-256:
d138b3fb199ae96ab3768f4a745b651cfae5c402dd093fc51e554ef93796c067
packaged payload extraction: 166 / 166 exact
```

Exactly canonical replacement 2060 differs between v113 and v114. The other
165 staged payloads are byte-identical, including all six other transplanted
Zeboim stations and target 727's graphics file 2061.

Live front/side acceptance remains pending. Leave target 727 and re-enter it
from v114 media before testing: movement must stop against every station side,
Cross/X from the captured front stance must open dialogue 4, and Cross/X while
facing the station from either side must remain silent.
