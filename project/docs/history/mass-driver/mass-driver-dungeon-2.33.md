# Mass Driver Dungeon 2.33 - v54 Continuity Repair

Version 54 fixes the progression failure captured in the player's July 27
v53 F2 state and rewrites the surrounding objective text as one causal
sequence.

This remains an original, canon-conscious fan reconstruction. The retail
Disc 2 narration establishes the journey on foot, the surviving Zeboim Mass
Driver, the missile galleries, Citan's assistance, Taura's nanomachine
capsule, and the removal of the Limiter. The authorization puzzle and
automated Guardian are additions, not recovered Square cut content.

## Reproduced failure

The newest state was
`work/duckstation/savestates/SLUS-00669_1.sav`, saved in target 376 beside
the Defense Archive wall terminal. Its thumbnail showed:

```text
AUTHORIZATION TERMINAL
GUIDANCE RECORD MISSING
```

Persistent progression word `0x008B` had both mechanical power bits, the
four-point authority clue, and Citan's join bit set. Only the Directive 0320
clue bit was clear. The v53 terminal tested that clue bit and returned before
creating either code menu. Although the east stairs still led back to the
larger facility, nothing at the terminal explained that route clearly, and
the small Guidance Archive interaction could easily be mistaken for inert
scenery.

The Central Gate itself was correct: it tested auxiliary power and
accelerator-rail power only. Moving the clue test onto that gate would have
made the story logic worse, because a terminal cannot remotely know what the
party has read.

## Progression repair

The two record bits now mean knowledge:

- bit 2 records that the Guidance Archive clue, Directive 0320, was read;
- bit 3 records that the Materials Storage clue,
  A-2 / B-5 / C-8 / D-4, was read.

If either bit is clear, the Defense Archive terminal names the clue's
location and says that manual entry remains available. It then continues to
the same two code menus. The correct values are still required, wrong choices
remain retryable, and reading the records remains the intended way to learn
the answers.

This preserves four separate causal roles:

1. Auxiliary and accelerator-rail power open the Central Gate.
2. Directive 0320 and the four-point code authorize the launch at the Defense
   Archive terminal.
3. Defeating the automated custodian opens the west bulkhead.
4. Central Control releases Taura's capsule.

Target 361's Guidance Archive interaction is widened from 20 by 20 to 24 by
24 world units, matching the neighboring auxiliary console. The interaction
remains on the native console and does not overlap the other controller.

Central Control now reads the launch-completed bit before running its launch
sequence. A later interaction reports that the capsule is already released
and atmospheric dispersal is active, then returns to the surface. It cannot
release a duplicate payload.

## Narrative repair

All route text now distinguishes the Guidance Archive, Control and Research,
Materials Storage, Archive Console D, the Central Gate, the Defense Archive,
the missile galleries, and Central Control. Obsolete references to
“Archive Annex 368,” false Gear-life-sign scans, and unused Griffon or
El-Regulus prompts were removed from active dialogue.

The Defense Archive exchange now explains the visible gameplay:

- Citan followed an eastern service route opened by the restored power;
- Taura sent the party's Gears through the freight lift to the defense bay;
- the old system can verify a launch code while separately rejecting the
  request to inhibit its expired emergency defense;
- defeating that defense leaves the authorization active and opens the west
  bulkhead.

The final launch text identifies the payload as Taura's nanomachines, describes
their upper-atmosphere dispersal, and says they remove the genetic Limiter
that has bound humankind. The old Mass Driver is framed first as civil freight
infrastructure, then as a system converted to carry weapons, and finally as a
way to carry a life-saving payload. It does not claim that the party launches
a surviving Zeboim weapon.

## Regression contract

The focused builder suite statically proves the formerly trapped `0x008B`
path: the missing-Directive branch displays its clue message, jumps to the
authority check, and then reaches the Directive menu; a missing-authority
branch likewise reaches manual entry. It also verifies:

- the Central Gate still depends only on power bits 0 and 1;
- the Guidance Archive and auxiliary controls have matching interaction
  widths;
- all active authored pages obey the retail 58-unit by five-line window;
- wrong codes return safely to the terminal;
- accepted codes set authorization and start the isolated battle;
- the completion console tests bit 6 before its only launch path;
- no active dialogue contains the retired room names or false Gear prompts.

The final release is staged in `work/mass_driver_v54_stage` and packed as:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v54.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v54.cue
```

Final post-freeze evidence:

- BIN: 694,799,616 bytes, 295,408 raw sectors, SHA-256
  `2b5b3543378274cda2caf669fe7ff21e7d29b599a98e958a1d7a234f91d600fb`;
- CUE: 106 bytes, SHA-256
  `54f39d12f3ecdc1565b8cb080e61478d17643538bef15cf88dabf21cee3f1f66`;
- manifest: 149 unique replacements totaling 9,688,087 bytes, SHA-256
  `c73fa33c5a3ec4dead2119673987a15497c0e9053e6dcd4016b354a0e25bc768`;
- final-disc re-extraction: 149/149 replacements exact;
- standalone boot context and MODE2/Form1 EDC/ECC: valid;
- automated validation: 165 tests and 1,940 subtests passed.

## Continuing the reported run

An emulator state stores both its mounted-disc path and the field bytecode
already loaded in RAM. Simply pointing an old F2 state at v54 changes the
disc for future field loads, but it does not replace target 376's already
loaded v53 terminal routine.

The safe continuation is:

```text
output/MASS_DRIVER_V54_CONTINUE.sav
```

It preserves the original state and changes its embedded media path from the
v53 CUE to the same-length v54 CUE. It also replaces the 0x8000-byte archive
table that Xenogears loaded from disc sectors 0x18 through 0x27 at boot. That
second change is necessary because the rebuilt target 726 and target 376
resources begin one logical sector later in v54. A media-path-only state would
still seek with v53's resident table and is not safe.

The corrected continuation is 1,776,518 bytes with SHA-256
`42abfb96dc60326c4ca4751df81bdeb1b564078ae544dedc3a1e29ca4b9c230b`.
Its resident table is byte-exact to the final v54 disc, its CD drive is idle,
and no decompressed state bytes outside that table were changed. The source
slot and its backup remain untouched.

An isolated DuckStation v84 process accepted the state, reused the final v54
CUE, reported a successful system boot, and visibly reproduced the saved
authorization-terminal screen. The physical stair traversal, code menus,
battle, galleries, and launch sequence remain the manual end-to-end acceptance
pass; their resources, reciprocal transitions, and prerequisites were
validated independently.

After loading the continuation:

1. finish the currently open missing-clue message;
2. take the east automatic stairs back to target 726;
3. turn around and use the Central Gate to re-enter target 376;
4. use the wall terminal and enter `0320`, then
   `A-2 / B-5 / C-8 / D-4`.

The round trip installs v54's corrected target 376 routine. The existing
`0x008B` progression word is preserved, so the terminal will show the missing
Directive clue and then continue to manual entry. To create a new state
without replacing the source slot, press F4 until DuckStation's overlay shows
empty Slot 4, then press F2.
