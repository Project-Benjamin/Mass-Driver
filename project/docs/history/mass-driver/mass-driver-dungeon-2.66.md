# Mass Driver v89 Gear-bay dialogue and native battle-facing correction

V89 makes two isolated corrections to the Goliath Factory Gear encounter. Elly
now recognizes that Citan left El-Regulus and Crescens in the bay, matching his
offscreen support role established earlier in the dungeon. The battle overlay
also returns to Xenogears's native target-derived yaw after live evidence proved
that the v78-v88 slot-zero half-turn made El-Regulus face backward.

## Gear-bay dialogue

Target 384 dialogue block 3 now begins:

```text
Elly
So... Citan left our Gears
here for us.
```

This replaces Elly's claim that the machine is surprisingly still operational.
Citan remains offscreen: no Citan field actor, follower, playable slot, Fenrir,
or battle participant is added. The existing Emeralda/Custodian explanation,
two-Gear boarding sequence, Guardian formation, post-battle mounted rebuild,
and human-scale dismount return are unchanged.

The rebuilt canonical 1374 field bundle is 162,424 bytes with SHA-256
`059a4a881c5428a21dbc37dc4f0fac2cb6c6b5d26c70c966a2524cdca330dd5e`.
Its script remains exactly 21,207 bytes with SHA-256
`ca016611e19974493f7b8e32d8451ed64bde18ba0953476864e216664f259b3a`.
Only its dialogue payload changes, to 1,112 bytes with SHA-256
`bc981e1f36278ffc9757afb4c8fc638640d8b20562f19e2a28d1a64861a808c9`.
The v88 bundle was 162,460 bytes with SHA-256
`31fbb31fa4768873196c7095515c4248a9d4a23c2f5207abc8b047ccba918f2d`;
its 1,143-byte dialogue payload had SHA-256
`edbc866c9f7708224a70e25cf65d196ae18c35a8c6156dd9ce0017a996f66db5`.

## Live v88 facing evidence

The preserved battle state is
`work/runtime_capture/el_regulus_v88_facing_audit/SLUS-00669_1.v88-battle-live.sav`.
It is 2,009,672 bytes with SHA-256
`dd8b8696b90e8286138907cfe7b415dee4563d4c7c02591068edfa594ee9d58d`
and mounts the exact v88 CUE. Its extracted 256-by-192 thumbnail is
`work/runtime_capture/el_regulus_v88_facing_audit/el_regulus_backwards.png`,
91,388 bytes with SHA-256
`de223784ee1d3a6cf0e2ae8905ac77fb6ed460d58fcc682d01de436261126728`.
It visibly shows El-Regulus presenting its rear to the Guardian while Crescens
faces correctly.

The resident battle data identifies Elly as visual entity 0, player slot 0,
Gear ID 10 at x/z `(1720, 1640)`. The Guardian is visual entity 3 at
`(1040, 1640)`, exactly 680 units due west. The native target-derived yaw for
that vector is `0x0400`, but El-Regulus's root yaw at RAM `0x801522C6` is
`0x0C00`. The difference is exactly the `0x0800` half-turn added by the
v78-v88 slot-zero override resident at `0x800ACD30`. This isolates the fault to
the overlay patch rather than El-Regulus's model, animations, formation, or
target selection.

The state is immutable failure evidence only. Loading it restores v88's
mounted media and resident half-turn code, so it cannot validate v89.

## Native target-yaw restoration

V89 stages canonical 38 as
`work/mass_driver_v89_stage/replacements/38_battle_native_target_yaw.bin`.
It is the exact audited retail packed source: 166,665 bytes with SHA-256
`93a4179fe3b31a4fffb9fe723f63511f15de5177bbfcbca2529124a4108ffbb1`.
It decodes to 343,948 bytes with retail SHA-256
`ad4586923095715288377caea89f2cd15d70a2f80ef53394e2faec22b2e0b825`.

At decoded offset `0x3D240`, v89 restores the native block:

```text
00 3C 15 00 03 3C 07 00 00 14 02 00 30 01 A4 8F 03 14 02 00
```

The retired v78-v88 replacement block was:

```text
20 00 83 92 02 00 60 14 21 38 A0 02 00 08 42 24 30 01 A4 8F
```

That retired packed resource is 164,608 bytes with SHA-256
`32bc80f7ebec84f2c7f24b88a3d9a4fa09ac98dc7fb2fbcf9a7aac95b0b1ebc8`;
its decoded SHA-256 is
`9409b10bdff27fb46f54df47f4b3ecab876d9aac95492c117e4d556b34007db3`.
V89 removes the fixed player-slot exception instead of applying a different
manual rotation. Crescens, the Guardian, all other enemies and player Gears,
canonical 2960's models and deathblow animations, and formation data remain
unchanged.

## Packaged delta and identities

Only canonical IDs 38 and 1374 differ from v88. Every other declared
replacement is byte-identical, including the v88 source-378 hanging-terminal
geometry, the v87 Auxiliary-room terminal correction, El-Regulus's Attack
Level and complete deathblow programs, its fixed-cell name, and both Gear-bay
graphics resources.

The packaged v89 artifacts are:

- BIN `output/Xenogears_PW_CD2_mass_driver_standalone_v89.bin`: 695,295,888 bytes / 295,619 raw sectors, SHA-256 `28d1a5f3ffea7e33eaccc790a194d6e55eeb51458a74f5689b56d4487e0fef15`
- CUE `output/Xenogears_PW_CD2_mass_driver_standalone_v89.cue`: 106 bytes, SHA-256 `413f0dc2b36aabaa90534d8deb7df4731140ede430bce75812737dcc3007f440`
- Manifest `work/mass_driver_v89_stage/manifest.json`: 187,692 bytes, SHA-256 `f54834780b76235a51cf7d9e6982718d2cb065abe958008635244725dc184d2b`
- Replacement aggregate: 126 jobs, 158 declared replacements, 10,394,672 bytes, SHA-256 `387171f1ee3613598a6b93fb58b274a20a552f894c7e98c21cc43f4c3d53bdac`

The complete automated suite passes 204 tests and 2,345 subtests with no
failures, errors, or skips.

## Runtime acceptance

Fully quit DuckStation, boot
`Xenogears_PW_CD2_mass_driver_standalone_v89.cue`, choose New Game, and load
no older F1 state or in-game save. Enter Directive `0320` and authority points
`A-2`, `B-5`, `C-8`, and `D-4`, then take the north lift into target 384.

Walk up to the adjacent El-Regulus and Crescens. Confirm that Elly says Citan
left the Gears there, while Citan and Fenrir remain absent. The same sequence
must board Elly and Emeralda and begin the no-Escape Guardian battle. Confirm
that El-Regulus's front faces the Guardian; the captured due-west formation
must use native yaw `0x0400`, not the rejected v88 `0x0C00` rear view.
Crescens and the Guardian must retain their existing orientation and behavior.
After victory, confirm the mounted rebuild, offline north bulkhead, south-lift
dismount, and return to the Defense Archive still work normally.
