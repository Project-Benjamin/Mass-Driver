# Mass Driver Dungeon 2.9 - v30 El-Regulus Runtime-Safe Repair

Version 30 replaces the runtime-rejected v29 candidate while preserving the
accepted v28 dungeon and complete El-Regulus deathblow suite.

The repair has three focused changes:

- `DoubleImpact` repeats El-Regulus's proper native `0x40` attack motion
  twice, with a ten-tick pause between the motions;
- Ether Beam dispatches Guided Shot's firing layers through El-Regulus's
  already-preloaded auxiliary sound resource 3368;
- canonical 2960's primary model/sound container remains byte-identical and
  its main root stays below the runtime-sensitive `0x8000` boundary.

The rejected v29 build used clip `0x43` before `0x40`, expanded canonical
2960's primary SEDS, and moved its main root to `0x805C`. Runtime testing
found a ducking first motion, no audible beam effect, and inaccessible
Level-2/Level-3 deathblows. Those results are preserved in
[the superseded v29 notes](mass-driver-dungeon-2.8.md).

## DoubleImpact

Level-1 program 35 now performs:

1. the target-facing player-Gear setup;
2. native El-Regulus motion `0x40`;
3. a ten-tick pause;
4. the same native motion `0x40` again;
5. one damage dispatch after the second motion;
6. native recovery and completion.

The single damage marker is deliberate. Repeating the proper visible motion
does not apply the deathblow's full damage coefficient twice.

```text
program 35 size: 64 bytes
program 35 SHA-256:
5872e46bab1cd9e76e4846a3a1b9a0bde0e64d514f8e2eb78211e4ebbc4756ee
```

## Ether Beam auxiliary audio

El-Regulus's retail animation 29 already preloads canonical 3368 as sound
selector 2. Its trailing sound container has six entries but is empty in the
retail resource. Version 30 preserves its existing first entry and inserts
Fei's complete, checksum-valid Guided Shot SEDS as the next entry. The
remaining entries stay empty.

Canonical 3425 supplies the donor SEDS:

```text
canonical 3425 SHA-256:
5fd34033355b1f36c1831d1dee6b1d2f9cd1259a8ddf2e85e151df274f128869

Guided Shot SEDS bounds: 0x02F4..0x0488
Guided Shot SEDS size: 404 bytes
Guided Shot SEDS SHA-256:
49e590c50162034281e1327e64f3629bf459c8fdb5d0a72f17232c0e272ef505
```

Canonical 3425's `0x0488..0x5A68` WDS is a complete `0x100`-byte
header plus `0x54E0` bytes of PS1 ADPCM. It is byte-identical to canonical
3084, the common Gear WDS loaded before player-Gear animations:

```text
common Gear WDS size: 0x55E0 / 21,984 bytes
common Gear WDS SHA-256:
ec6ae588d85e342f973ebf1ca1e87073c1721f37dbf06d521ccbcd70a6f65262
```

Both the donor SEDS and El-Regulus's retail SEDS select the common/default
sample-bank path, so no separate WDS or waveform transplant is required.

The type-5 event remains the retail 12-byte size. At tick zero it starts
Guided Shot effects 4 and 5 through selector 2:

```text
63 01 0C 00 00 00 05 04 00 02 05 00
```

Both finite streams terminate naturally. A four-tick guard allows the sound
event to dispatch before program 36 arms El-Regulus's native visual event.

```text
program 36 size: 168 bytes
program 36 SHA-256:
3e41bd6309bc875dfb7389dd52da326156a00f1be17b14c6ef4fc77db4b17150
```

### Canonical 3368

```text
source size: 0x209C / 8,348 bytes
source SHA-256:
088175c1ae15e0a76020edf992ed970d4c8398a29d32f4a1bb9997c28058e7ff
source outer roots:
(2, 0x0010, 0x207C, 0x209C)

v30 size: 0x2230 / 8,752 bytes
v30 SHA-256:
ac19c5e2308fff8f1c957a845b09727e71e6cd200835dc14592ab5cf13b7ff17
v30 outer roots:
(2, 0x0010, 0x207C, 0x2230)
```

The nested auxiliary bank grows from `0x20` to `0x1B4` bytes. It retains
count 6 and has seven entry-boundary pointers:

```text
0x20, 0x20, 0x1B4, 0x1B4, 0x1B4, 0x1B4, 0x1B4

v30 nested-bank SHA-256:
0f44f9f6a4509f0a4ad58dcf5523fa661752ac2dada76c0f0b63ae327406fc99
```

## Canonical 2960

The compact repeated motion and retail-sized sound event leave the main root
at `0x7FFC`. The model and primary sound container are byte-identical to the
retail source; Guided Shot audio is not appended to this resource.

```text
source SHA-256:
8ccee45222b6245fdcb4556ce15f69746bf5e2ebd88ec76aa77ec4381ab07d6d

v30 size: 0x8348 / 33,608 bytes
v30 SHA-256:
627c356a4289c2e1a2989b295137cbb1fae8fe997808c8083f11f6a8f12c55a9
v30 outer roots:
(2, 0x0010, 0x7FFC, 0x8348)
```

Programs 38-43 and 68-70 retain the complete Level-2, Level-3, and Infinity
implementations from v28. Ordinary Gear attacks raise Attack Level
`0 -> 1 -> 2 -> 3`; using any deathblow resets Attack Level. To test a
Level-2 or Level-3 deathblow, keep selecting ordinary attacks without using a
lower-level deathblow until the desired menu appears. Infinity still depends
on the native Hyper roll after reaching Level 3.

## Release validation

The final v30 image was rebuilt and every staged replacement was extracted
from the finished BIN before recording these release results:

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v30.bin

BIN size: 690,377,856 bytes
BIN SHA-256:
17917ed9d116c72af6c9da37bfba5a0213674f6be61ee20216f4221990162fc5
automated tests: 132 passed, 317 subtests passed
post-build replacement comparison: 122/122 exact
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid
```

Known resource-level validation for this candidate:

```text
canonical 2960:
33,608 bytes
627c356a4289c2e1a2989b295137cbb1fae8fe997808c8083f11f6a8f12c55a9

canonical 3368:
8,752 bytes
ac19c5e2308fff8f1c957a845b09727e71e6cd200835dc14592ab5cf13b7ff17
```

## Manual runtime test

1. Launch v30, mount El-Regulus on the world map, and keep moving near the
   Mass Driver until the native Dragon encounter starts.
2. Build Attack Level 1 with an ordinary attack, then use `DoubleImpact`.
   Confirm the proper attack motion occurs twice with a readable pause, no
   ducking motion appears, and damage displays after the second attack.
3. Build Attack Level 1 again and use `Ether Beam`. Confirm an audible
   beam-like firing effect accompanies the native blue beam, damage is
   nonzero, the sound ends, and the command menu returns normally.
4. Use only ordinary attacks to build through Attack Level 2 and then Level
   3. Confirm both menus appear and their deathblows execute. Remember that
   choosing any deathblow resets Attack Level and requires rebuilding it.

Binary validation proves the resource layout and event bytes. Audible sound,
perceptual synchronization, and Level-2/Level-3 runtime access still require
this emulator acceptance test.
