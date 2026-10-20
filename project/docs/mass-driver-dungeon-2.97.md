# Mass Driver Dungeon 2.97 - safe arcade atlas and single-base defense

V136 is the frozen package for the Defense Archive arcade correction. It keeps
v135's conservative field-363 station allocation byte-for-byte and changes only
declared canonicals 1358 and 2476 relative to v135.

## Field-376 atlas correction

The malformed Elly sprite reported after leaving the arcade was not caused by
field 363's authentic Zeboim station. The shared 64-by-64 direct-color arcade
atlas was loaded at VRAM `(640,256)`, the same slot used by Elly in the fixed
Defense Archive party. Arcade teardown restored the field display and controls,
but did not reload the overwritten party sprite sheet.

V136 moves canonical 2476 to `(640,384)`. This is the deliberately empty third
party-sprite slot in the enforced Elly/Emeralda route:

- Elly remains at `(640,256)` and Emeralda at `(640,320)`;
- the atlas occupies `x=640..703`, `y=384..447`;
- the compass begins at `y=448`;
- the portrait column begins at `x=704`; and
- dialogue scratch begins at `x=768`.

The atlas pixel payload is byte-identical to v135. Only byte offset 14 in its TIM
header changes, encoding destination Y 256 as Y 384. An old or modified save
with a third active party member cannot validate this allocation; the supported
standalone route keeps party slot 2 empty.

## 2600-style single-base Missile Command

Missile Command now uses the Atari 2600 port's single center launch base and
one fire control. The layout is 2600-style rather than a claim of an exact full
clone: the embedded game retains the existing arcade revision-3 ordinary-missile
quota curve, scoring, bonus-city system, and the current bounded enemy set,
while cruise missiles remain deferred. The maximum 22-missile quota begins at
wave 19 and repeats thereafter; the displayed wave and best-wave record cap at
31.

The center base has 30 ABMs per wave. Ten are loaded and twenty begin in the
underground reserve. Cross fires from the center. Emptying a ten-round set loads
the next set automatically. A direct base hit destroys only the currently loaded
set; any underground reserve survives and supplies the next ten. Six cities and
the center base are the seven enemy targets.

Up to three center-launched ABMs or their fireballs can coexist, along with up
to three attacker-seeded chain explosions. Each moving ABM carries a custom
three-cell hot, bright, and dim contrail. The three-cell presentation is a
project-specific visual treatment, not a documented Atari 2600 rule. Old trail
cells are retired and the live dynamic objects are recomposed so overlapping
player trails, heads, and explosions remain visible. Triangle pauses, Cross
resumes, and Circle exits from pause.

## Frozen v136 package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v136.bin
BIN size: 696,714,144 bytes
BIN raw sectors: 296,222
BIN SHA-256: cfd7be90381a002b05d61139c1b897219712b3d513a185f94ed1e24da46458eb

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v136.cue
CUE size: 107 bytes
CUE SHA-256: ee4ec03e1f8e8eb12f283094e8629ba9dbfad27e204af92b7f568d823e66283e

manifest: work/mass_driver_v136_stage/manifest.json
manifest size: 236,648 bytes
manifest SHA-256: 44b8fb55f2db69637d91c22710dba4d3878493db8b18014272a31a18a53640aa
jobs: 138
unique replacements: 173
replacement bytes: 12,316,668
route fields: 35
directed edges: 70

field 376 canonical 1358 size: 192,612 bytes
field 376 canonical 1358 SHA-256: dd9039414e8fd947e4ed085746961d9042b218117e214abc37a6ddeea0404a8a
field 376 prepared header SHA-256: 2e85b169f0401db16d126d5e14d66efb34fda326a164b33664b8e0a33057724f
field 376 packed header SHA-256: 24b4f0fd507febec98afaf05aba92ff911196b0844304b9cf8c43b1fd8229a90
field 376 script size: 50,860 bytes (48,936-byte bytecode)
field 376 script SHA-256: 718dce46a2d590d4e3e98f0d7315fc03fd2e91f8b27a8015cedd131c2bf166d2
arcade atlas canonical 2476 size: 8,212 bytes
arcade atlas canonical 2476 SHA-256: 3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d
```

All 173 unique declared replacements were extracted directly from the final BIN
through its Xenogears FAT and matched the staged payloads by size, SHA-256, and
bytes. The patched boot sector has the audited standalone hash and valid
MODE2/Form1 EDC/ECC. The complete automated suite passed 257 tests and 3,279
subtests with no failures, errors, or skips.

Fresh v136 emulator acceptance remains pending. Mount the v136 CUE, completely
leave target 376, and re-enter it from v136 media. Ask the player to navigate
and press controls; do not automate emulator navigation. Confirm Elly, Emeralda,
the compass, portraits, dialogue, Start menu, and save/menu overlays remain
correct before and after both arcade games. Then exercise the single-base ammo
reload and base-hit cases, three simultaneous ABMs, three-cell trail cleanup,
chain explosions, scoring, persistence, pause/resume, and return to the field.
