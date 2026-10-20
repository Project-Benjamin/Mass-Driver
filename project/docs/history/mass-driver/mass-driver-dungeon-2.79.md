# Mass Driver v102 adult historical actors and directed staging

V102 corrects the final Miang memory in Central Control. The Launch Director
and Systems Officer are now recognizable adult Zeboim personnel instead of the
small mascot-like sprites inherited from field 369. Miang faces the Director,
and every speaker turns toward the person being addressed before a line begins.
The three figures remain at their assigned console stations; they do not wander,
cross through one another, or teleport while the memory plays.

## Historical-scene contract

- Entity 17 is the adult blonde Launch Director in a white command uniform at
  `(-86, 82)`, actor bank 4, initial direction 1.
- Entity 18 is the adult helmeted Systems Officer at `(-30, 118)`, actor bank
  3, initial direction 5.
- Entity 19 remains Miang at `(14, 58)`, actor bank 2, initial direction 7.
- Before each historical line, all three actors receive direct actor-to-actor
  turn commands. Director/Officer exchanges face entities 17 and 18 toward one
  another while Miang watches the Director. Miang/Director exchanges face the
  Director and Officer toward Miang while Miang faces the Director.
- Dialogue blocks 22 through 31 retain the historical exchange. The former
  shared final block is split so block 31 belongs only to the Director and new
  block 36 gives Miang's closing line its own turn and camera beat.
- Every historical dialogue line has its own stable first-person memory shot,
  targeted at the actual speaker. Actor scripts 1 through 31 remain shared
  `STOP` scripts; all deliberate facing happens in the console cutscene routine.

The scene still shows only Elly's inherited memory. It does not add the
Director or Officer as present-day NPCs and does not change the final capsule
launch trigger.

## Asset provenance and deterministic assembly

The two adult actors come from retail Zeboim field 366, preserving the dungeon's
visual language. The Systems Officer uses donor actor bank 1 and its exact
`(896, 0, 64, 144)` texture page; the Launch Director uses donor actor bank 2
and its exact `(960, 0, 64, 129)` texture page. Miang remains the exact retail
field-364 actor. Target field 728's native banks 0 and 1 are retained so its
existing treasure and room behavior are untouched; Miang, Officer, and Director
are appended as banks 2, 3, and 4.

The field-366 donor component is 12,116 bytes with SHA-256
`8451a0e8dfca1db4a6a5b16417cef9d2ca1e309d44c07676c6a39f307f06564e`.
Its graphics stream is 301,056 bytes with SHA-256
`e35798fd14ec0c2565a6aafb8812b610645a507982e0d138b4bbc02b76aaf0fa`.

## Exact target-728 identities

Only target 728's bundle and graphics replacement are expected to change from
v101. All other declared replacements remain byte-identical.

| Field | Bundle canonical | v102 bundle size | v102 bundle SHA-256 | Graphics canonical | v102 graphics size | v102 graphics SHA-256 |
|---:|---:|---:|---|---:|---:|---|
| 728 | 2062 | 62,276 | `400a6cfb3d4cd184542ac82a04b9c5059de4bbd0b466b734a6fe4a61ed7f372d` | 2063 | 245,760 | `dc60d25ba5c4e73891e498363816abf043fe61a87081f828cd20bb45bd6abf7a` |

The final target-728 field header is 1,088 bytes with SHA-256
`15612fefcd1a4ec8fef6cba81d31370c8a4d8ced8705bd0453e7cb9202fbfd95`.
Its actor component is 18,640 bytes with SHA-256
`2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538`;
its script component is 3,406 bytes with SHA-256
`55814c8deac382dbde2461656e8b244a82f9b64cea4d550350202b9c08b5c9a7`;
and its dialogue component is 5,044 bytes with SHA-256
`c5300fd84da598f56215c5561feee6932de3f726524b53704cb56fa762503006`.

## Packaged v102 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v102.bin`:
  695,815,680 bytes, 295,840 raw sectors, SHA-256
  `795bcd8363d10236b7e0ee19d39eeec0987474dee195736dd2e2571b7947c01d`.
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v102.cue`:
  107 bytes, SHA-256
  `2c4b3a6b3e6d087ba29aa74f4b4c00370739e3af9374f3bd51a697a6e8302bad`.
- Manifest `work/mass_driver_v102_stage/manifest.json`:
  200,295 bytes, SHA-256
  `ef2cb66b43d422fa86f27962dcda38a75ca454bf9a6e76a5ca38feccc46a927a`.
- Declared replacements: 162 across 128 jobs, totaling 10,853,492 bytes,
  canonical-ID-order aggregate SHA-256
  `fb5abb373b0a9c2f467a48d9166ef6b3829b4c403edf49e9104c35c29391d1c1`.
- Regression suite: 208 tests and 2,636 subtests.

## Previous v101 identities

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v101.bin`:
  695,759,232 bytes, 295,816 raw sectors, SHA-256
  `dd9274ef0e3c8047dd56a6bf3a4a3dec3747610945cc89b0d0f96746747676a7`.
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v101.cue`: 107 bytes,
  SHA-256
  `6af2e9c17398b01e35e621802a3ae22c195a43007f87fa9387302bdea9d63d46`.
- Manifest `work/mass_driver_v101_stage/manifest.json`: 200,249 bytes,
  SHA-256
  `97dee560a66aed474c65e45b031eef66abf5db5913154d634df1c0b6f0eaa807`.
- Declared-replacement aggregate: 10,803,828 bytes, SHA-256
  `27a7d66eb09cb7a3631570a22161e44a1b9b2aadce89d1a64abe68e0450be93b`.
- Regression suite: 208 tests and 2,616 subtests.

## Runtime acceptance

Fully quit the emulator, launch the v102 CUE, and choose New Game. Alternatively,
fully leave and re-enter Central Control from v102 media before testing. Do not
judge the change from a save state made while field 728 was resident, because it
can restore v101's old actor and script data.

At the final archive console, confirm that the Director and Systems Officer are
adult Zeboim personnel, Miang visibly faces the Director, and each speaker turns
toward the correct counterpart before speaking. Confirm that no historical
actor wanders or snaps to another station, the final Miang line has its own
camera beat, the camera resets after the memory, and Cross/X on the console still
initiates the final launch sequence normally.
