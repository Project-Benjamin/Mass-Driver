# Xenogears Mass Driver V161.3 - one-app packaging revision

V161 is an unofficial fan-made playtest build for the reconstructed Mass
Driver dungeon. It is not affiliated with or endorsed by Square Enix.

## V161 changes

- The Guardian encounter starts the normal battle theme instead of continuing
  the room ambience.
- El-Regulus turns back toward Guardian after returning from an attack or
  deathblow, so Elly's Gear does not remain backward for the rest of the fight.
- V160's wider post-Guardian west-panel interaction area remains included.
- V159's automatic Defense Archive north-lift transition remains included.

Start a completely fresh Guardian battle from the V161 CUE when testing these
changes. An in-battle save state made with an older build restores the old
resident battle code and cannot validate V161.

## Portable packaging change

This release replaces the former multi-file root with one clear app. Extract
the ZIP and open `Xenogears_Mass_Driver.exe`. The ZIP root contains only that
app and its `MassDriverData` support folder. The same app builds the game,
finds or asks for an emulator, and starts the game. Its integrated xdelta3
decoder applies the patch without unpacking or starting a helper executable.

The package contains no original game disc image, emulator, or BIOS. It
requires the user's unmodified USA Disc 2 BIN and their own emulator and BIOS.

## Verified input and output

```text
Input BIN size:    688,700,880 bytes
Input BIN SHA-256: 5eab85c683d4d7087d345b587472db9c44df29b35ce66553c2626d26018b947e

Output BIN size:    696,130,848 bytes
Output BIN SHA-256: b010fcb46946e5e1595d7225652bd78f04b91e97a5b6dce0cc8cf0675ed49bf4

Output CUE size:    107 bytes
Output CUE SHA-256: 06149bd106fdd02fe1baacbae6b07b001411bb4ecfb6cc501efd199ea0379561
```

Fresh user-driven gameplay confirmation remains the purpose of this
prerelease.
