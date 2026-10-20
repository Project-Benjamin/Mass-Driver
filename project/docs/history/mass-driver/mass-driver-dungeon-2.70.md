# Mass Driver v93 subway return correction

V93 fixes the immediate return loop between the abandoned subway and the
service-junction stairs. The stairs in target 363 still return through their
open side to subway target 721 parameter 1, but the receiving point is now
`(-1250, -218)` on the same connected platform walkmesh.

## Root cause and repair

Target 721's automatic subway exit is centered at x `-1391`. Its encoded
horizontal bound expands to 64 units at runtime, and Elly's 16-unit collision
width makes its effective reach 80 units, through x `-1311`. The former
parameter-1 arrival at `(-1334, -218)` was therefore 23 units inside that
active volume. As soon as target 721 loaded, entity 13 fired again and returned
the party to target 363.

The new x coordinate, `-1250`, lies 61 units beyond the expanded exit edge and
remains on connected layer-0 walkmesh triangle 71. Its z coordinate,
walkmesh layer, actor facing, and camera direction remain unchanged. The
subway-side exit volume is also unchanged, so it remains easy to use when the
player intentionally walks upstairs.

The build-time scene-continuity verifier now derives the automatic exit's
effective bounds from entity 13's actual initializer and rejects a return
arrival with less than 32 units of horizontal clearance while its z coordinate
overlaps the exit. Automated coverage also proves that the former `-1334`
coordinate is inside the volume and that the emitted `-1250` coordinate clears
it.

## Packaged delta from v92

Exactly one declared canonical resource differs from v92: 2048, the subway
target-721 field bundle. Its size remains 150,260 bytes and its SHA-256 is
`99b349d8ef99aa05d9cbfd385e7d8035b69e86cf04776ee6718b771a2dc3c2e6`.
The 1,692-byte script has SHA-256
`2b7baada95f5b45599007e7a95ea8a96441589f10eacb6c9ba627224c4e16f36`.
The 802-byte dialogue remains byte-identical to v92 with SHA-256
`9ac63fd3538e58788dd188dafaa17dcfa948e46a77d04d7acad0acacef15573c`.
Canonical 2049 subway graphics and every other declared replacement are also
byte-identical to v92.

## Packaged v93 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v93.bin`: 695,338,224
  bytes / 295,637 raw sectors, SHA-256
  `0d3b3833067d183772fea212eb30ba712b218a9360402302e2e77d521aaffeda`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v93.cue`: 106 bytes,
  SHA-256
  `e97f611b81f69079ac08491d0d52ec317d558bdeb19a39589a05a77d003745d7`
- Manifest `work/mass_driver_v93_stage/manifest.json`: 190,187 bytes, SHA-256
  `043b50aec3488dedfb446f19c928e1361d0003ccab9d0f886fbc723c3c20361e`
- Replacement aggregate: 126 jobs, 158 declared replacements, 10,433,356
  bytes, SHA-256
  `625918d7bc03933bfe07471e7b2822bfdf595c375ec0b3c48f67b0706ffe112e`
- Complete automated suite: 205 tests and 2,374 subtests, with no failures,
  errors, or skips

## Runtime acceptance

Fully quit DuckStation and boot
`output/Xenogears_PW_CD2_mass_driver_standalone_v93.cue`. Use a cold-boot New
Game or leave and re-enter the subway after mounting v93 media. A full-machine
state with the older target-721 field already resident restores that old field
script and cannot validate this correction.

From the subway, use the normal exit to enter target 363 parameter 0. Turn
around and walk through the service-junction opening. Confirm that the party
returns to target 721 parameter 1 farther inside the subway platform, remains
there without an automatic transition, and can walk away from the stairs. Then
walk back to the subway exit deliberately and confirm that it still returns to
target 363 normally.
