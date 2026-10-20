# Mass Driver Dungeon 3.20 - V159 Defense Archive lift threshold repair

V159 preserves V158's 33-field, 66-edge route, east-wall Central Control
keypad, continuous finale, and all authored progression. It changes only the
already-open north lift in Defense Archive target 376: walking into the visible
opening now has a continuous position-driven transition, and Cross/X remains a
reachable fallback.

## Live V158 failure evidence

The opened leaves and authorization state were correct in the failing V158
session. The live capture recorded Elly at
`(x=3.425583, z=274.982513)` on walkmesh triangle 73, with field variable
`0x03FE=0x0013`; authorization bit 4 was therefore set. The resident field-376
script was the exact V158 script, 48,937 bytes with SHA-256
`f3c08c932d04de87ac6dc8afb0e754193a8899d17ce6aaffd4c2f31479c75257`.

The failure was geometric, not an X-button requirement or missing story flag.
Triangle 73 terminates at the closed `z=279` wall edge, and the player collider
stopped at approximately `z=274.983`. Controller entity 17 remained centered
at `(0,308)` with V158 operand `0x07`, whose 30-unit effective reach did not
begin until `z=278`. Both the assumed passive walk-through contact and the X
selection region were therefore beyond the player's reachable stopping point.

## V159 transition contract

V159 makes entity 0 script 1 a continuous, one-tick-yielding leader-position
worker. This slot was a single STOP in the source field and had no other role.
The worker first checks authorization bit 4, then uses the exact leader query

```text
2D FF F8 07 FA 07 FC 07
```

to place the leader's X, Z, and Y coordinates in field-local variables
`0x07F8`, `0x07FA`, and `0x07FC`. At `z>=274` it invokes entity 17 script 2,
the same checked action used by Cross/X. Otherwise it yields for one VM tick
and retries. The north walkmesh itself narrows the reachable row to the visible
aperture, x=`-44..44`, so geometry supplies the lateral gate and the worker
needs only the signed Z comparison.

This arrangement keeps the transition in one routine. The poll does not copy
the field-change body, write authorization, open dialogue, or replay the leaf
animation. With authorization clear it only retries, so locked feedback remains
exclusive to an intentional Cross/X action.

Entity 17's no-facing interaction operand is now `0x09`, giving 34 units of
effective reach. Its selectable region begins at `z=274`, which includes the
exact V158 blocked capture and provides a reachable X fallback. Script 2 still
shows locked dialogue 9 before authorization and performs the authorized
bounded on-foot transition to field 384 parameter 0 afterward. Controller
script 3 is deliberately STOP: V159 no longer depends on unproven passive
collision dispatch from a model-less static interaction entity.

The authorized action still normalizes both pilot slots to on-foot state,
clears the two Gear-staging bits, and runs the bounded party script 30 crossing
toward `(0,285)` before changing fields. The already-open leaf helpers are not
restarted, so entering the lift cannot visibly close and reopen it.

## Return-spawn safety

Field 384's existing reciprocal parameter-2 return remains `(0,245)` in field
376. It is 29 units south of V159's first automatic row and 63 units from the
controller center, outside the 34-unit X region. An authorized return therefore
cannot immediately bounce back into field 384. The boundary cases explicitly
cover locked `z=279`, authorized `z=273`, first contact `z=274`, both aperture
edges, both just-outside X values, the exact V158 capture, and the return spawn.

## Current package

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v159.bin
size: 696,130,848 bytes (295,974 raw sectors)
SHA-256: 3bb06df72182f72beb2f25ccae2fa244a4a44aa198f9f3224a6262940b080927

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v159.cue
size: 107 bytes
SHA-256: 9b84d3513ae22b6415e005bf286d1b4637ea6d92a142a18056b3010229dbf6db

manifest: work/mass_driver_v159_stage/manifest.json
size: 249,477 bytes
SHA-256: f6aa96575db50a4a90a39036c072e29e777c0d28d00841868d3d4ce762700020
jobs / replacements / bytes: 136 / 169 / 11,804,460
route: 33 fields / 66 directed edges
canonical-order payload SHA-256: 7a543d7ad665f7b987e0f96e9d954a4774bdce5aadc615f91a95ebc3ae2aa00d
canonical-ID/size/payload SHA-256: 2d76bbd95c1d1a64aa7dd783c1fd689de9f55a59057bf13b9d596690dc9049ee

canonical 1358 / target 376 size: 190,444 bytes
canonical 1358 SHA-256: 9696899ce837eee05e727627a2f2f2fd2b8828e90f51ca071dab6ab4fffd6a6f
field 376 script size: 48,930 bytes (47,006-byte bytecode)
field 376 script SHA-256: ab4b7d9454a7fe1b41927fe239dbdde364b1fc692b43293bc15eaeb8856aaa4b
```

The V158-to-V159 staged gameplay delta is canonical 1358 only. Focused
structural and regression tests pass for the exact poll bytes, authorization
guard, one-tick retry loop, script-2 dispatch, widened `0x09` fallback,
script-3 STOP, bounded party crossing, live-capture boundary, return-spawn
exclusion, field bundle, manifest, and deterministic aggregate identities.

All 169 packaged payloads match their staged sources. The exhaustive FAT/raw
audit found only canonical 1358 plus its one-byte primary and embedded FAT size
updates, with no relocation; 95/95 extended field/FAT Mode2 sectors validate
in each image. An independent BIN and manifest rebuild is byte-identical, the
one-file installer passes static and dynamic offline verification, and the
authoritative suite passes 262 tests / 2,702 successful subtests in 20.126
seconds with every failure counter at zero. Fresh user-driven runtime validation
is still pending. For that runtime check, load target 376 from V159 media, enter
the authorized open lift by walking without pressing X, confirm the field-384
transition, return through parameter 2 without a bounce, and separately verify
the reachable locked and authorized X paths. A state captured with target 376
already resident retains its older script even after the CUE changes; leave the
field completely and re-enter it from V159, or use a cold boot.

Historical V158 package and validation facts remain unchanged in
[the V158 solid-console notes](mass-driver-dungeon-3.19.md).
