# Mass Driver Dungeon 2.1 - v22 El-Regulus World-Map Movement

> **Superseded and corrected by v23:** v22's six-phase bob is valid, but its
> retail-art conclusion below is incomplete. Retail Gear bundles use separate
> five-direction idle and forward-driving pixel banks. Version 23 adds the
> missing El-Regulus travel poses; see
> [the v23 forward-pose notes](mass-driver-dungeon-2.2.md).

Version 22 preserves the complete standalone dungeon and v21's PS1-safe,
authentic El-Regulus world-map sprite. It adds the movement animation that
v21's first stable conversion was missing.

## Retail animation audit

All ten audited Disc 2 world-map Gear resources use the same 128-byte
animation section. Their movement is not an articulated leg-and-arm cycle.
Each direction reuses the same pixels while the entire Gear rises and falls.

Animation ID 1 plays this six-pose loop:

```text
phase:         0 -> 1 -> 2 -> 3 -> 2 -> 1
vertical y:    0   -2   -4   -6   -4   -2 source pixels
frame hold:    6    6    6    6    6    6 ticks
loop length:   36 ticks / approximately 0.6 seconds
```

World-map Gears render at 2x sprite scale, making the motion clearly visible
without introducing new artwork. The five directional groups are:

```text
rear:                 frames 16-19
rear three-quarter:   frames 20-23
side:                 frames 24-27
front three-quarter:  frames 28-31
front:                frames 32-35
```

The animation VM reverses through phases 2 and 1 after phase 3, so the Gear
returns smoothly to its base position.

## El-Regulus implementation

Version 21 already supplied all 35 expected frame IDs, but each four-frame
movement group had identical geometry. Version 22 keeps every validated v21
texture, pointer, tile placement, palette entry, root offset, and animation
byte. It changes only the movement-frame geometry:

- both 48x36 sprite halves move upward by two pixels per phase;
- frame width bounds increase by one per phase;
- frame height bounds increase by two per phase;
- idle/action frames 1-15 remain static;
- movement frames 16-35 follow the retail four-phase contract.

Exactly 60 bytes differ between the v21 and v22 canonical `3949` resources.
No new texture memory, disc allocation, or loader behavior is required.

The animated sprite contract is:

```text
canonical ID:       3949
size:               10,960 bytes
SHA-256:            23ceabff1b79209d2066712d5f3ff83d392483021364a48933cb5b4f59d0a40f
root offsets:       0x14, 0x94, 0x2A8C, 0x2AD0
animation entries:  5
frame header:       0x1423 (35 frames, retail allocation maximum 10)
actual subsprites:  2 per frame
upload envelope:    24 VRAM words x 36 rows
movement offsets:   0, -2, -4, -6, -4, -2
```

Creating 20 additional independent full-canvas textures would expand the
resource to more than 44 KiB and require unverified loader and allocation
changes. Texture sharing with geometry phases is both the original game's
method and the safer implementation.

## Build

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v22_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v22.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v22.cue
```

The rebuilt BIN is 690,368,448 bytes with SHA-256:

```text
80e4c9a326fbde312def6949ae50afd02be52c47ff01941b26686413a45cd4e0
```

It passed 119 automated tests, 134 subtests, and an exact post-build
comparison of all 40 injected disc resources.

## Runtime acceptance

A mounted-state DuckStation probe instantiated the v22 sprite and moved it
continuously across the world map. Multiple directions rendered without a
freeze, seam, palette change, or stopped audio.

Read-only live-RAM sampling at sprite frame field `0x8015819C` recorded:

```text
16 -> 17 -> 18 -> 19 -> 18 -> 17 -> 16
```

Each pose lasted approximately 100 milliseconds, matching the retail six-tick
timing. Releasing movement returned El-Regulus to animation ID 0 and its
directional idle frame.

For manual acceptance:

1. Start New Game and open the world-map Gear menu.
2. Tell Elly to get into El-Regulus.
3. Hold a direction and observe the smooth rising-and-falling motion.
4. Turn through all five source directions and their mirrored opposites.
5. Stop, move again, dismount, and remount.

This is the same movement style used by the original world-map Gears. Their
sprites also bob as a complete unit rather than using independently drawn
limb animation.
