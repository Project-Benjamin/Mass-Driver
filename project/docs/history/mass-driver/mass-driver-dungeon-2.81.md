# Mass Driver v104 accessible gray archive door

V104 fixes the gray side door shown in the August 2 screenshot. Standing in
front of its visible panel now gives a reliable X interaction, without needing
to hunt for one exact angle or position.

## Runtime identification

The screenshot-era DuckStation backup state was captured at 10:20:59, three
seconds before `Xenogears (Disc 2) 2026-08-02-10-21-02.png`. Its resident field
resources exactly identify target 726, the Zeboim launch-support hall.

The controlled party actor was at `(-605.79303, 495.06880)`, beside the gray
archive-junction door:

- Controller entity 20: `(-605, 474)`.
- Visible sliding panel/helper entity 27: `(-661, 446)`, model 6.
- Destination: target 367, parameter 0.
- Standard encoded interaction half-width: `0x1E`, giving 76 units of
  effective reach after the engine's scaling and player extent.

The player was already only about 21 units from the controller, well inside
that normal interaction region. Proximity was therefore not the problem.

## Root cause and correction

The visible panel is northwest of its invisible controller anchor. V103 still
enabled the engine's narrow facing-cone test for entity 20, so a player facing
the panel artwork could be outside the angle computed toward the hidden anchor.

V104 changes only entity 20's controller flag from facing-gated to
proximity-only. Its controller position, interaction size, native sliding
animation, sound, movement, field transition, artwork, walkmesh, and reciprocal
route are unchanged. The nearby offset-pivot entity-22 door already used this
same reliable proximity-only policy.

At decoded target-726 script offset `0x0ADD`, the sole v103-to-v104 component
change is byte `03 -> 07` in the controller's `F8` flags command.
The packaged v103/v104 BIN comparison changes only raw sector 221,268: 31 raw
bytes including that sector's regenerated error-detection/correction data.

## Exact target-726 identities

Only canonical 2058 changes from v103. Canonical 2059 and every decoded
component except the script remain byte-identical.

| Resource | v103 | v104 |
|---|---|---|
| Target-726 bundle (canonical 2058) | 22,800 bytes, `3035bb283c10ecbcc1d0f3f6ded7e9421770e58f71e2ba4e44d01457a9838aab` | 22,800 bytes, `f83e1bdf710b4db28502ea4e7800b1a4e49ae7423681ed1f583be70334e6291a` |
| Script component | 3,401 bytes, `02274a1cc95f4029c2dedd0b8e4b0713e8f76bb817e4c588687e4611bc4c644f` | 3,401 bytes, `17b7de0e2c60cd18f980d3e96e326be516781f04bbe3523d71c95eb33bd7d60f` |
| Graphics (canonical 2059) | 145,408 bytes, `814172e24014a2ef5050fa8de4e1d4f756a9ff7d060ec29d78ce9504d989e2e3` | unchanged |

The unchanged decoded components are:

- Walkmesh: 2,472 bytes, `6bf746c309116834609fdb52bf6594a36139ee75d356fbce91f219efdb5a6c21`.
- Models: 9,452 bytes, `aa1c67b892f689fd98f5817b511c8262f5430a8edae31bf3f556a535e78e1b97`.
- Actors: 2,872 bytes, `9abdba25445fb9f82e3d1393dedb2fc1fbfe39a649b1845868d5f04e0800cf01`.
- Dialogue: 571 bytes, `4eaad7c53c095d2083a7ad3abafef2c6013ec8d6f36803789f988df3857e56be`.
- Encounters: 528 bytes, `3828516c774346c005fe7255d7b614449458525836d9cc1a233fa8966560b198`.
- Triggers: 24 bytes, `8c56149fb1f11a50e81ef78ced47fea0239b772769309f74f397a06535929065`.

## Packaged v104 identities

- BIN: 695,815,680 bytes, 295,840 raw sectors, SHA-256
  `c58dab43646a63adbe551d6f64b8ad9ddeef631314fc5e58f36f869e066a7812`.
- CUE: 107 bytes, SHA-256
  `bc05a0b2de6caaa2f9c61a782db5d04ecb565acbf8d125277de7145dd33afa4e`.
- Manifest: 200,496 bytes, SHA-256
  `4ef7aac32d7efbd33e6ca6bcd5566f475fc051b6b179a6ee62519e0d5696019a`.
- Declared replacements: 162 across 128 jobs, totaling 10,853,556 bytes;
  canonical-ID-order aggregate SHA-256
  `44a3dc320fbca5eee5c402df030b919524d3a05278ecfc067dd2e52488f95c2d`.
- Regression suite: 209 tests and 2,653 subtests passed.

## Runtime acceptance

V103 is currently resident in the screenshot-era state, so merely changing the
mounted CUE will not replace that loaded field script. Launch v104 and leave
target 726 completely, then re-enter it; a cold boot is also valid.

Walk up to the pictured gray door while facing its visible panel and press X.
It should respond throughout the ordinary area in front of the door, play the
same native sliding animation, and enter the archive junction. Confirm that the
reciprocal door still returns to the same launch-support hallway.
