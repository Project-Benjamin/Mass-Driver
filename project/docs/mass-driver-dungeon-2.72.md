# Mass Driver v95 Zeboim archive branch and subjective finale

V95 replaces target 367's isolated vertical-lift archive with a native
source-377 Zeboim service junction. Its two side passages lead to targets 385
and 386, separate source-374 Materials Storage annexes that match the
facility's established technology and palette. Both rooms are optional dead
ends with repeatable exposition on native computers and a separate one-time
Omegasol chest. Neither room writes launch progression.

V95 also divides Central Control into two deliberate console activations. The
first presents Elly's recovered memory and returns full control without
launching the capsule. The player must press Cross/X again to begin the final
scene, during which Citan opens the room's native east door, walks to the
console, and speaks only after reaching Elly.

## Native Zeboim archive branch

The optional branch is:

```text
726 <-> 367
          +-> 385
          +-> 386
```

Target 367 uses source field 377's native three-door Zeboim junction. Targets
385 and 386 each use source field 374's Materials Storage architecture,
computer, and treasure presentation. Every passage is reciprocal. Each
annex's mail can be reread, while its chest awards one Omegasol only once and
retains its opened state. No custom or thematically unrelated room prop is
introduced.

## Elly-only memory staging

The first launch-console activation is a memory scene only:

1. The camera assumes Elly's first-person viewpoint and hides every present-day
   party actor.
2. A warm native `F1` color grade distinguishes Miang's memory from the current
   room.
3. The Director manifests with corrected semitransparency mode 1 and receives
   dedicated camera shots so that his apparition remains clearly visible.
4. The officers and the exact retail Miang actor play the historical exchange
   entirely within Elly's perception.
5. The apparitions are hidden, the warm grade is cleared, the party is
   restored, and the fixed camera is released back to normal gameplay.
6. The historical-seen state is recorded, but Citan is not loaded and the
   capsule is not launched.

Emeralda remains confused because she saw only Elly reacting to an empty room;
Elly then explains the memory she experienced.

## Separate final launch scene

A second Cross/X interaction begins the final scene. Citan is staged beyond
the native east doorway rather than appearing beside the console. The native
door opens, he walks through it to Elly, and only then does his trajectory
dialogue begin. He assists with Taura's capsule launch without becoming
available for exploration or combat.

The authentic Mass Driver world-map launch sequence and guarded
Elly/Emeralda return remain unchanged. Later console use reports active
atmospheric dispersal and cannot launch another payload.

## Static coverage

Validation checks the complete 34-field route, the reciprocal `726 <-> 367`,
`367 <-> 385`, and `367 <-> 386` links, all three native donor layouts, both
repeatable archive interactions, and two independent persistent Omegasol
chests.

Central Control coverage verifies that the first console press cannot launch
or initialize Citan; all live party actors are hidden during the POV memory;
the warm `F1` grade is both applied and cleared; the Director's mode-1
apparition and dedicated shots occur in order; every ghost is removed; and the
gameplay camera is restored before control returns. The second press must open
the native east door, walk Citan into position before dialogue, and only then
commit the capsule and invoke the retail launch.

## Packaged delta from v94

Exactly seven changed or new declared canonical resources differ from v94:

| Canonical | Target | Resource | Size and SHA-256 |
| ---: | ---: | --- | --- |
| 1340 | 367 | Field bundle | 23,932; `166a09660df3e9598b3e45386f5892d6546a3a677a1cbd72337e5736cd9d458a` |
| 1341 | 367 | Graphics | 116,736; `db54a274c151c4a2602e10b24e7781e99aed220916b64429b6d1d9bb476b8259` |
| 1376 | 385 | Field bundle | 55,748; `c724afdbe719899069924850f4aa7e79537708c565b8a7f7a80b9ee04d3df78e` |
| 1377 | 385 | Graphics | 165,888; `d38d2ae9a2136b497403b917d04a052ecfd0b476f7f2799c10bfb86a8c235596` |
| 1378 | 386 | Field bundle | 55,516; `4b2ae09b34690892d6ad6624f1c0460cc88a01432c9e0774bd1c5a480de44977` |
| 1379 | 386 | Graphics | 165,888; `d38d2ae9a2136b497403b917d04a052ecfd0b476f7f2799c10bfb86a8c235596` |
| 2062 | 728 | Field bundle | 53,572; `0d81fbded88cd76e622a0e2880091c7d6617daa469778695e91e8f6513e40857` |

Target 367's 1,758-byte script has SHA-256
`5d75339bfbe28488b191a3921f246660d24255736814ac2cc50a9ae25d2392b0`;
its 105-byte dialogue has SHA-256
`e35f3e204abe8727e9282786951493065b4a8b0ed11344695db0f99ec0a665df`.
Targets 385 and 386 each have a 1,803-byte script, with respective SHA-256
values `41a99d6d2a5278e1860a79e94a207de37560eea60e6354bff1a2f43edea6df49`
and `4a98568d2130be090e58d36b819c72deedbf7a82375771535b76c6b1fcecca87`.
Their dialogue payloads are respectively 790 and 577 bytes, with SHA-256
`b8fbffffe7882c974d08c1708eb2f5b66b7e6e275123973b70dc7548c6042d1e`
and `f3ed00a4584c2ef9b352d2e16ca9bf9be857d00acf2a90fe4725517d5ebbef92`.
Target 728's 3,083-byte script has SHA-256
`def9d997333c91c69bb287fe5d790f5f399906ced69f34cf729e0b49c8342b95`;
its 5,040-byte dialogue has SHA-256
`6012b671b036c8869d626ad545fa7e2d1b8b0ef3887cebac7cd3dd5006620e8b`.
Every other declared replacement is byte-identical to v94.

## Packaged v95 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v95.bin`: 695,834,496
  bytes / 295,848 raw sectors, SHA-256
  `64816abe1a2b26eee020b2f5416f0384df69277329a0feb486215380844e3166`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v95.cue`: 106 bytes,
  SHA-256
  `4bf160b1a1d1aa6ad0112f7c0c31ea822feeda717772c069b66758cad6344cad`
- Manifest `work/mass_driver_v95_stage/manifest.json`: 196,759 bytes,
  SHA-256
  `649b4b81553cb1e8178eb7ffe680460397032d2ddd196f8fadbee319ad8111fb`
- Replacement aggregate: 128 jobs, 162 declared replacements, 10,870,884
  bytes, SHA-256
  `52611121fef39fc1c7748b9d25973fa50f0616ce34781832bb36f82a216c7d9a`
- Complete automated suite: 207 tests and 2,420 subtests, with no failures,
  errors, or skips

## Runtime acceptance

Fully quit DuckStation, cold-boot
`output/Xenogears_PW_CD2_mass_driver_standalone_v95.cue`, choose New Game, and
load no older F1 state or in-game save.

Enter target 367 from the formerly dead hallway door. Confirm that it is a
native Zeboim junction, that both side passages reach visually compatible but
separate dead-end storage annexes, and that both return to the junction. In
each annex, confirm that the native computer presents repeatable exposition and
the native chest awards one Omegasol only once.

In Central Control, press Cross/X once. Confirm that the warm first-person
memory contains no visible present-day party member, that the Director is
clearly manifested in his dedicated shots, and that only Elly perceives the
scene. Confirm that the grade, ghosts, and fixed camera are fully cleared and
normal player control returns without Citan or a launch.

Press Cross/X on the console a second time. Confirm that the native east door
opens, Citan visibly walks through it, and dialogue begins only after he reaches
Elly. Complete the launch, verify the Elly/Emeralda return, and confirm that
another console use reports dispersal without launching again.
