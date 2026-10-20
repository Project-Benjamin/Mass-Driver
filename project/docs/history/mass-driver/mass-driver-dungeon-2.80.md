# Mass Driver v103 smooth Citan entrance

V103 smooths Citan's entrance during the final Central Control sequence. The
camera now establishes the doorway before he enters, stays on the same shot
while the door opens and he walks into the room, and then eases into the
conversation framing. Citan follows a verified walkmesh route to Elly instead
of disappearing from the doorway and snapping to her position.

## V102 defect

The final camera used immediately before the entrance placed its eye east of
the doorway, behind Citan as he walked west. This produced an abrupt angle
change followed by several seconds dominated by the back of his head.

The entrance also issued one direct `4B` walk from the doorway to
`(-30, 118)`. That line crossed the unwalkable notch around the console, and
the requested endpoint itself was outside the room's walkmesh. The failed walk
therefore fell through to an `OP19` position change, which was visible as Citan
teleporting from the door to Elly.

## V103 entrance contract

- The arrival shot targets `(87, 97, -72)` from an eye at
  `(87, -380, -170)` over 24 frames.
- That shot remains active continuously while the door opens and Citan walks;
  the sequence does not cut to the old rear angle or restart camera mode.
- Citan follows three verified walkmesh legs across four checked points:
  `(204, 89)` on triangle 32 to `(65, 85)` on triangle 31 with boundary 240;
  then to `(15, 85)` on triangle 21 with boundary 120; and finally to
  `(-30, 105)` on triangle 16 with boundary 120. Every segment remains inside
  traversable geometry and clears the console notch.
- After the full walk completes, one imperceptible endpoint correction seats
  Citan precisely for the dialogue. There is no failed long walk followed by a
  visible teleport.
- Citan and the current party leader receive mutual direct `FE 17`
  actor-to-actor turns, so they face each other before speaking regardless of
  which valid leader is present.
- The conversation settles into a final shot targeting `(-57, 115, -72)` from
  an eye at `(-57, -362, -170)` over 18 frames. This transition does not
  re-enter camera mode, preserving visual continuity from the entrance shot.

The historical Miang memory, adult Director and Systems Officer actors,
console interaction, and capsule-launch sequence are otherwise unchanged from
v102.

## Exact target-728 identities

Only canonical replacement 2062, target field 728's bundle, is expected to
change from v102. Canonical 2063, its graphics stream, remains byte-identical.

| Canonical | Resource | v102 size | v102 SHA-256 | Prepared v103 size | Prepared v103 SHA-256 |
|---:|---|---:|---|---:|---|
| 2062 | target-728 field bundle | 62,276 | `400a6cfb3d4cd184542ac82a04b9c5059de4bbd0b466b734a6fe4a61ed7f372d` | 62,340 | `cfeaad35cf9d5abdd96f1be414f82a4c6d7a07d677a8472b1014e77dc6f386b2` |
| 2063 | target-728 graphics | 245,760 | `dc60d25ba5c4e73891e498363816abf043fe61a87081f828cd20bb45bd6abf7a` | 245,760 | `dc60d25ba5c4e73891e498363816abf043fe61a87081f828cd20bb45bd6abf7a` |

The prepared v103 script component is 3,462 bytes with SHA-256
`836e41d197db9534f10362f6e3d8d7f7a7c06e85ed34c004916562ecf5a9c1fd`.
The following target-728 components remain identical to v102:

- Header: 1,088 bytes, SHA-256
  `15612fefcd1a4ec8fef6cba81d31370c8a4d8ced8705bd0453e7cb9202fbfd95`.
- Actors: 18,640 bytes, SHA-256
  `2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538`.
- Dialogue: 5,044 bytes, SHA-256
  `c5300fd84da598f56215c5561feee6932de3f726524b53704cb56fa762503006`.
- Graphics: 245,760 bytes, SHA-256
  `dc60d25ba5c4e73891e498363816abf043fe61a87081f828cd20bb45bd6abf7a`.

## Packaged v103 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v103.bin`:
  695,815,680 bytes, 295,840 raw sectors, SHA-256
  `03b83464e2fbac6c3551453ee671be2ab305ebe96147411a46d904088ae04212`.
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v103.cue`:
  107 bytes, SHA-256
  `d5d1529fb57c3a9b32b82df9049b6ead320ffc9af067423a072ac42d05748703`.
- Manifest `work/mass_driver_v103_stage/manifest.json`:
  200,496 bytes, SHA-256
  `a71b8c5f935e4342918acae679a12774f08cc64c6ca38a87adb842c1a81b0856`.
- Declared replacements: 162 across 128 jobs, totaling 10,853,556 bytes;
  canonical-ID-order aggregate SHA-256
  `b54340dfad3aa98fb1ee8fcd56d270bfc26623bda0ce008513ba3fce34e5d3e3`.
- Regression suite: 208 tests and 2,652 subtests passed.

## Previous v102 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v102.bin`:
  695,815,680 bytes, 295,840 raw sectors, SHA-256
  `795bcd8363d10236b7e0ee19d39eeec0987474dee195736dd2e2571b7947c01d`.
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v102.cue`:
  107 bytes, SHA-256
  `2c4b3a6b3e6d087ba29aa74f4b4c00370739e3af9374f3bd51a697a6e8302bad`.
- Manifest `work/mass_driver_v102_stage/manifest.json`:
  200,295 bytes, SHA-256
  `ef2cb66b43d422fa86f27962dcda38a75ca454bf9a6e76a5ca38feccc46a927a`.
- Declared replacements: 162 across 128 jobs, totaling 10,853,492 bytes;
  canonical-ID-order aggregate SHA-256
  `fb5abb373b0a9c2f467a48d9166ef6b3829b4c403edf49e9104c35c29391d1c1`.
- Regression suite: 208 tests and 2,636 subtests.

## Runtime acceptance

Fully quit the emulator and launch the v103 CUE before testing. Alternatively,
leave Central Control completely and re-enter it from v103 media. Do not load a
save state made while field 728 was resident, because it can restore v102's
camera and script data.

At the final console, confirm that the camera establishes the doorway before
Citan appears, holds the same readable angle through the door opening and his
entire walk, and never lingers immediately behind his head. Confirm that Citan
walks around the console notch without snapping to Elly, that Citan and the
current leader face each other before speaking, and that the final 18-frame
conversation shot settles smoothly without a second camera-mode cut. The Miang
memory and the subsequent launch interaction should continue normally.
