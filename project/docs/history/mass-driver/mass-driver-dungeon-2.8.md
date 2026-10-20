# Mass Driver Dungeon 2.8 - Rejected v29 El-Regulus Candidate

**Status: superseded and runtime-rejected. Do not use this image as the
current test build. Version 30 replaces it.**

The v29 image passed its automated binary checks but failed manual runtime
acceptance:

- Ether Beam produced no audible firing effect;
- DoubleImpact's first `0x43` clip appeared as an unrelated ducking motion;
- Level-2 and Level-3 deathblows were reported inaccessible.

The candidate expanded canonical 2960's primary SEDS and moved its main root
from v28's `0x7FE8` to `0x805C`, crossing the runtime-sensitive `0x8000`
boundary. Version 30 restores a byte-identical primary model/sound container,
keeps the main root below that boundary, repeats only the proper `0x40`
DoubleImpact motion, and moves Guided Shot's complete SEDS into El-Regulus's
already-preloaded auxiliary resource 3368. See
[the v30 notes](mass-driver-dungeon-2.9.md).

Version 29 changes only the requested El-Regulus battle behavior on top of
the accepted v28 dungeon:

- `DoubleImpact` now performs two distinct El-Regulus motions;
- `Ether Beam` uses all three finite firing layers from Fei's retail Guided
  Shot;
- every original El-Regulus sound ID remains intact.

## DoubleImpact

Level-1 program 35 now uses:

1. the target-facing player-Gear header and camera envelope;
2. native El-Regulus clip `0x43`;
3. a ten-tick pause;
4. native El-Regulus clip `0x40`;
5. one damage dispatch after the second motion;
6. native recovery and completion.

The single damage marker is deliberate. The two motions provide the visible
double attack without applying the deathblow's full damage coefficient twice.

```text
program 35 size: 128 bytes
program 35 SHA-256:
d0ca46443866a390e69b28e890a0c7a24893d0ffd2f6452af1a963bca68dc2cb
```

## Ether Beam audio

The initial bank-2 candidate was rejected during audit. El-Regulus's retail
secondary resource is an empty sound container, so starting another Gear's
bank-2 IDs could have produced silence or an invalid pointer.

The rejected implementation attempted to be self-contained. Canonical 3425,
Fei's Guided Shot resource, supplies the six channel streams for firing
effects 4, 5, and 6. The builder appends those exact streams to El-Regulus's
own selector-1 SEDS as new effects 17, 18, and 19. Existing IDs 0-16 and
their stream bytes are preserved.

```text
canonical 3425 SHA-256:
5fd34033355b1f36c1831d1dee6b1d2f9cd1259a8ddf2e85e151df274f128869

Guided Shot SEDS SHA-256:
49e590c50162034281e1327e64f3629bf459c8fdb5d0a72f17232c0e272ef505

copied firing streams: 193 bytes
copied firing-stream SHA-256:
61ed2fb55599a9c54aff73f95ef38092eff05d0acd0d7c408b0d5e28b0155461
```

The type-5 event wrapper starts IDs 17 and 18 together, then ID 19, at tick
four:

```text
63 02 14 00
04 00 05 11 00 01 12 00
04 00 05 13 00 01 00 00
```

All six firing streams terminate naturally. No unverified stop command or
secondary sound resource is needed. A four-tick guard allows the audio event
to dispatch before program 36 arms El-Regulus's native blue-beam event.

```text
program 36 size: 176 bytes
program 36 SHA-256:
8ce6412b1c954197ace0b548bece06f16bdb74fdad0f377cd5b036bf105d5416
```

The SEDS rebuild increases the ID count from 17 to 20, moves the data table
from `0x64` to `0x70`, updates every nonzero stream pointer, recalculates the
retail additive checksum, and relocates the enclosing archive.

```text
source SEDS size: 812 bytes
source SEDS SHA-256:
b67baaa48bb1f0dc868c4b4ab63ca5cdf3891b95a47ab22187dc9d6c21f98505

v29 SEDS size: 1,020 bytes
v29 SEDS SHA-256:
0fab45ef6287bde8d9db8b1f5d93c44dc6705802ff78661b21d88872cafd5c77

v29 additive checksum: 0
```

## Canonical 2960

```text
source SHA-256:
8ccee45222b6245fdcb4556ce15f69746bf5e2ebd88ec76aa77ec4381ab07d6d

v29 size: 33,912 bytes
v29 SHA-256:
b1a5d65de0512867d619cfa5cef369418875a202f841cd2709b7fe12eb5504d3

v29 roots:
0x0010, 0x805C, 0x8478
```

## Automated validation of the rejected candidate

```text
BIN size: 690,377,856 bytes
BIN SHA-256:
3d28c69e45c1dc719a6b3b55f8a54409b291368897942fba21b1eac1de3ace42

automated tests: 132
post-build replacement comparison: 121/121
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid
```

## Manual runtime result

The required emulator test rejected v29: Ether Beam remained silent,
DoubleImpact began with the wrong ducking motion, and Level-2/Level-3 access
regressed. The hashes above document that failed candidate for comparison;
they are not release-acceptance evidence.
