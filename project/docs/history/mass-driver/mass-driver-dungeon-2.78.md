# Mass Driver v101 native reserve-magazine service pedestals

V101 replaces the visually incompatible reserve-magazine computer with an
object built entirely from the room that contains it. Targets 377, 378, 379,
382, and 383 now reassemble the exact three-piece lower service pedestal from
retail field 673's own cloning apparatus. The former field-374 Materials
Storage model transplant, copied texture rectangle, copied palette, and two
additional VRAM uploads are gone.

The replacement uses native field-673 models 2, 4, and 6 in static nodes 22,
23, and 24 with their original render flags `0x0000`, `0x0010`, and `0x8000`.
Its placement anchor is `(1161, 0, 396)`, producing the audited aisle-side
visual center `(500, 0, 0)`. Field 673's 102,400-byte graphics stream is now
preserved exactly. Retired upper-vat model slots 0 and 1 are compacted with
harmless copies of native model 6; no active room geometry is discarded and no
synthetic or cross-field visual asset is introduced.

## Five-room design and interaction contract

The five-room route remains
`376 <-> 377 <-> 378 <-> 379 <-> 382 <-> 383 <-> 728`.

Every reserve magazine keeps the same gameplay contract:

- Six detailed grounded warheads, their support geometry, 72-unit solid
  collision, and every walkable aisle remain unchanged.
- North and south passage boundaries remain automatic and reciprocal. Entry
  from either direction is silent.
- Retired script entity 7 remains the invisible archive-reader controller at
  `(420, 0)`. Its facing-required `0x28` interaction zone accepts Cross/X.
- Cross/X presents that room's existing dialogue block 0 on every use. It
  writes no progression flag, changes no field, and never opens automatically.
- The visible object is the native three-piece service pedestal. It introduces
  no foreign model, texture page, palette, or VRAM upload.

## Exact canonical-ID delta from v100

Exactly ten declared replacements change. Every other declared replacement is
byte-identical to v100.

| Field | Bundle canonical | v101 bundle size | v101 bundle SHA-256 | Graphics canonical | v101 graphics size | v101 graphics SHA-256 |
|---:|---:|---:|---|---:|---:|---|
| 377 | 1360 | 88,604 | `be490adb3d87cd579c1fb37cf2304c2f2bc2c471689b6cd15203ef3c5bb4f2ff` | 1361 | 102,400 | `e58a4c0f5aacffbf500c31879e0795238af402d3bfb8d83dfca46df454dca2ed` |
| 378 | 1362 | 89,072 | `7a7346a753bcd3edc0b9c1940f524831aa421fd15405812f1a258dffa2a130da` | 1363 | 102,400 | `e58a4c0f5aacffbf500c31879e0795238af402d3bfb8d83dfca46df454dca2ed` |
| 379 | 1364 | 88,612 | `cadda1e8657a715bbc4f899e03148cf04ab16d7487dbbdd0e3e55d656cc6ad8f` | 1365 | 102,400 | `e58a4c0f5aacffbf500c31879e0795238af402d3bfb8d83dfca46df454dca2ed` |
| 382 | 1370 | 88,560 | `00544fa5ed0a8f12544a49c133ca044e15462f74d14fbe6242c071cb5be68e90` | 1371 | 102,400 | `e58a4c0f5aacffbf500c31879e0795238af402d3bfb8d83dfca46df454dca2ed` |
| 383 | 1372 | 88,600 | `7dbc50ec8e9fb546220f9e8e1c82c0954e6f2cae8c54b02995965b13cb4763f7` | 1373 | 102,400 | `e58a4c0f5aacffbf500c31879e0795238af402d3bfb8d83dfca46df454dca2ed` |

The manifest still contains 128 jobs and 162 declared replacements. Their
combined size is 10,803,828 bytes and their canonical-ID-order aggregate
SHA-256 is
`27a7d66eb09cb7a3631570a22161e44a1b9b2aadce89d1a64abe68e0450be93b`.

## Packaged v101 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v101.bin`:
  695,759,232 bytes, 295,816 raw sectors, SHA-256
  `dd9274ef0e3c8047dd56a6bf3a4a3dec3747610945cc89b0d0f96746747676a7`.
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v101.cue`: 107 bytes,
  SHA-256
  `6af2e9c17398b01e35e621802a3ae22c195a43007f87fa9387302bdea9d63d46`.
- Manifest `work/mass_driver_v101_stage/manifest.json`: 200,249 bytes,
  SHA-256
  `97dee560a66aed474c65e45b031eef66abf5db5913154d634df1c0b6f0eaa807`.

## Previous v100 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v100.bin`:
  695,841,552 bytes, 295,851 raw sectors, SHA-256
  `11bd8e140b272dee22bf5da6a6349069341bd81bb1c5d00e3b8558877906e43f`.
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v100.cue`: 107 bytes,
  SHA-256
  `2303521cea39b6e7b6c82338779e7dd82a4f260033d787e003e9f5b52040feb3`.
- Manifest `work/mass_driver_v100_stage/manifest.json`: 199,944 bytes,
  SHA-256
  `e32dccc8c0872796586b45cfcccd93327f0edc41bba6aa72ab8de2fa16ba97bc`.
- Declared-replacement aggregate: 10,878,648 bytes, SHA-256
  `bf72649459017c3292d7326f5953f4307042b569e66ea651adffe673d69007dd`.

## Runtime acceptance

Fully quit DuckStation, launch the v101 CUE, and choose New Game. A v100 F1
state made inside targets 377, 378, 379, 382, or 383 restores the old resident
field-374 computer and cannot validate this correction. Reload each magazine
from v101 media before checking the pedestal. Confirm silent entry from both
directions, repeatable Cross/X dialogue at the visible pedestal, automatic
reciprocal boundaries, and unchanged warhead collision.
