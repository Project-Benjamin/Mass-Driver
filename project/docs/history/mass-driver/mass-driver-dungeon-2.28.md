# Mass Driver Dungeon 2.28 - v49 Annex Rail Console

Version 49 replaces the misleading Magnetic Conduit rail panel seen in the
July 26 screenshots and makes the separate launch-authorization objective
discoverable.

This remains an original, canon-conscious fan reconstruction. It is not
recovered or official cut-content data.

## Screenshot and save-state diagnosis

The latest v48 Magnetic Conduit frame showed that the added "terminal" was a
reused door plane. It looked like part of a doorway and was difficult to
identify as an interactive control.

The latest central-gate state contained persistent objective word `0x0003`:

- bit 0: auxiliary power restored
- bit 1: accelerator rail restored
- bit 2: Directive 0320 not yet recovered
- bit 3: authority record not yet recovered
- bit 4: launch authorization not yet accepted

The auxiliary and rail switches therefore worked. The gate remained locked
because launch authorization is a separate records-and-console objective that
the old gate message did not explain.

## Rail-control correction

Archive Annex 368 already contains a proper native Zeboim console:

```text
target field: 368
source field: 378
controller entity: 13
native position: (45, -42)
native entry pointers: 02CD / 02E5 / 02E6 / 030E
```

Version 49 assigns the accelerator-rail bypass to that console. Its action
sets persistent variable `0x03FE`, bit 1, then plays sound `0x50` and reports
that launch-track power is restored.

The console's original scenery is preserved. Its two layered native models
remain byte exact:

```text
model 13 SHA-256:
e1ac9cf7e068e0f599f540a68cbe744aef8d28520937acda71d0c3f9cc47996e

model 14 SHA-256:
be8202aa8223397dc634793f391dd070de42008520dc2238e3539c48bbbe07d7
```

The Annex 368 return door remains a distinct native sliding door. Its route
is still reciprocal:

```text
726 entity 21 -> 368 parameter 0
368 entity 22 -> 726 parameter 5
```

## Magnetic Conduit correction

The v48-only fake panel entity, actor, and model are removed. Disc-extracted
target 725 now has the native inventory again:

```text
ATEL entities: 17
header actors: 28
models: 13
```

Entity 16 remains the reachable memory cube at `(10, -27, 0)`. Its retail
Save action is exact:

```text
FE 99 00 FE 55 FE 87 00
```

There is no entity 17 and no accelerator-rail setter in target 725.

## Launch-authorization route

The Central Gate now names the remaining steps instead of only reporting
that authorization was not accepted:

1. From the launch-support hall, use the far door and cross the sealed stair
   connector to the four-door service hub.
2. Enter the Research Annex and read the Guidance Archive. This recovers
   `Directive 0320`.
3. Return to the service hub and enter Materials Storage.
4. Read the Maintenance Authority Copy. It gives
   `A-2 / B-5 / C-8 / D-4`.
5. Use the nearby authorization console. Select `0320`, then
   `A-2 / B-5 / C-8 / D-4`.
6. Return through the stair connector. With auxiliary power, rail power, and
   launch authorization all set, the Central Gate opens and begins the
   El-Regulus boss sequence.

The service directory also now identifies Archive Annex 368 as the
accelerator-rail control location.

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v49.bin

BIN size: 693,263,760 bytes
raw sectors: 294,755
BIN SHA-256:
f1223d3dddaa20ef04bd1dee095573de921620148ee334b89960991a9ca19072

CUE SHA-256:
66405f9edc167e2a40659b43f4acf84c734c1124719e55fd9012fe3b1d2090f2

packed staged replacement comparison:
140/140 exact, totaling 8,152,758 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 152 passed, 1,892 subtests passed
```

Only canonical field bundles `1342`, `1350`, `2056`, and `2058` differ from
v48. Every other staged replacement is byte exact to v48.

Independent extraction from the completed disc confirmed:

- target 368 entity 13 begins with the exact rail-bit and sound prefix
  `3A FE 03 01 00 40 74 50 80`;
- target 368 keeps the native console placement and static model hashes;
- target 725 has 17 entities and the exact entity-16 retail Save action;
- all 140 canonical replacements match the staged files byte for byte.

## Focused manual acceptance

Cold boot the v49 CUE and choose New Game. Do not load an F1/F2 state made
with v48 because save states retain the older mounted disc and field code.

1. Confirm the Magnetic Conduit room contains its gold memory cube but no
   added door-shaped rail panel.
2. Press X at the memory cube and confirm the normal Save menu opens.
3. Enter Archive Annex 368, use its existing console, and confirm the
   accelerator-rail message appears.
4. At the Central Gate, confirm missing authorization now points to the
   Research Annex and Materials Storage.
5. Recover both records, enter both codes at the Materials Storage console,
   and confirm the gate opens.
