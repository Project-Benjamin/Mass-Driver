# Mass Driver Dungeon 2.27 - v48 Save Point and Rail Panel

Version 48 repairs the Magnetic Conduit room shown in the four July 26
screenshots. It restores the room's retail save point and adds a separate,
visible accelerator-rail control. Every accepted v47 route, door repair,
combat change, and story objective remains unchanged.

## Screenshot identification

The four states identify this route:

```text
target 368 archive annex
  -> target 726 launch-support hall
  -> target 725 Magnetic Conduit
```

The bright gold object in target 725 is not a terminal. Its actor and sprite
banks are byte-identical to the retail memory cube used in the Zeboim save
room. Its native entity-16 scripts are:

```text
init:       0x0172
update:     0x01B1
X action:   0x01B8
collision:  0x01C0

X action bytes:
FE 99 00 FE 55 FE 87 00
```

`FE 55` is the retail normal-menu/save-menu operation and `FE 87` waits for
that menu. The earlier standalone build repointed entity 16's X action to
the rail-interlock routine, so pressing X could set the rail bit but could
never open Save. It also placed the cube at `(100,-100)` on the lowered
triangle-55 surface rather than on the connected main floor.

There was no second rail terminal elsewhere in the room. The user's report
was therefore a structural defect, not a missed route or hidden switch.

## Restored memory cube

Entity 16 remains the original retail actor/sprite:

```text
actor bank 1 SHA-256:
42d88ff3385229ef53fdcf468b13ab61b6413a9ee47d756ece61756c246b8c52

sprite bank 1 SHA-256:
69060c5d8f1f25c3a3a4c438baaaabb18551f250abf66364b60cbbc28ac468d0
```

Only its initializer is made deterministic. It now uses bank 1 at
`(10,-27)`, walkmesh 0, on connected main-floor triangle 6. Its update,
native Save action, and collision pointers remain exactly `0x01B1`,
`0x01B8`, and `0x01C0`.

## Separate rail control

The rail bypass now belongs to new ATEL entity 17 at `(55,70)`, walkmesh 0.
It is X-only, has its own modest interaction box, and does not require the
player to face an offset invisible pivot. Its action begins:

```text
3A FE 03 01 00 40   set persistent rail-interlock bit 1
74 50 80            play control-confirmation sound 0x50
```

A separate stationary field-model actor 18 at `(72,70)` makes the control
visible. It is a recentered copy of the room's own checked Zeboim model 0,
not a Solaris prop and not a transplanted humanoid sprite:

```text
source model SHA-256:
34ea70c33b08f62b0b534ec3c02d31e8743878b58afd76e980705817b3f2e497

panel model SHA-256:
c148fb4dbf4a880640f5f04eebda236cd801f950290ac6df3832f605f5a9a5f5
```

This keeps both actor/sprite bundles, every VRAM mapping, and canonical 2057's
field-graphics upload byte-identical to v47.

## Structural checks

Target 725 changes are deliberately separated:

```text
ATEL entities:       17 -> 18
header actors:       28 -> 30
header bytes:        848 -> 880
field models:        13 -> 14
```

Header records 0 through 16 remain unchanged. The new entity-17 controller
and static actor-18 panel are inserted before the donor's static records;
old records 17 through 27 shift byte-for-byte to records 19 through 29.
The panel is stationary and therefore does not consume a second new ATEL
entity.

The installed packed field has:

```text
canonical file: 2056
size:           98,312 bytes
SHA-256:
75507169a4c3a17f1fc2577905938eabb3b8149088c96f832ead1c227c6fd30d
```

Canonical 2056 is the only staged replacement that differs from v47.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v48.bin

BIN size: 693,266,112 bytes
raw sectors: 294,756
BIN SHA-256:
49e8ea0c348e6a3c399d5ff8d572e2a0a0ee389bb748edffed37fed6aae6b8da

CUE SHA-256:
aecbd0cef799e35154da917c185b200bd48cd04f27e5bcb5378985cd74f327a7

packed staged replacement comparison:
140/140 exact, totaling 8,152,926 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 151 passed, 1,890 subtests passed
```

The disc-extracted target 725 was reparsed independently. It contains 18
ATEL entities, 30 header actors, 14 models, the exact native entity-16 Save
action, and the entity-17 rail-bit/sound prefix shown above.

## Focused manual acceptance

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and confirm the title says
   v48.
3. Choose New Game. Do not load a v47 F1/F2 state; it restores the v47
   mounted disc and already-loaded v47 field code.
4. Reach Archive Annex 368, leave it, then take the nearby left-hand sliding
   door used in the screenshots.
5. In Magnetic Conduit, approach the gold memory cube and press X. Confirm
   the normal Save menu opens and can be closed normally.
6. Approach the separate upright Zeboim wall panel beside the cube and press
   X. Confirm the accelerator-rail interlock response appears.
7. Continue to the final interlocked door and confirm it no longer reports
   the rail line as the missing condition.
8. If either object fails, press F2 immediately before X, press X once, then
   press F2 again while the result is visible. Preserve both state
   generations and the screenshot.
