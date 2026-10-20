# Chapter 2 native route and Suzarn portrait correction

The v7 stair exit sent Rico directly from the Champion's room (retail field
218) to an interior copied from field 211. It skipped the downstairs bar and
the D Block street. This release restores the original geographic connection
with isolated copies of the native bar and street, retaining the existing
Chapter 2 progress state.

## Original game evidence

Retail field 218 entity 3 UPDATE at 0x02A4 uses native trigger 0 and travels to
field 217, entry 1. Field 217 entity 3 UPDATE returns to field 218, entry 1.
The bar's street door connects to field 196, entry 5.

Both native street doors of the field 211 interior are restored as well:
field 196 entities 29/34 enter its opposite ends, and field 211 entities 4/5
return to the matching street entries. Directional arrivals use the original
entry tables instead of forcing Rico to one fixed coordinate.

Physical door traversal retains native OP47 without removing/reloading the
live party beforehand. The engine's party removal can clear the controlled
actor, and reloading a PC can copy the position of a different controlled
actor; either can disrupt OP47's walk from Rico's current position. During
field load, the engine runs INITs in ascending entity order and uses its
buffer-only party setup path, so director entity 0 prepares the party before
the appended PC actors initialize. Generic staircase transitions retain their
existing concealed party setup. This distinction has a regression check.

The original dialogue calls field 217 Latina's Bar. Field 217 dialogue 30
places the Wildcat in the civilian part of the city, and field 196 dialogue
129 advertises Latina's Bar in D Block. The user correctly identified the
missing downstairs bar; these native scripts distinguish the two bar names.

## Suzarn

Suzarn's portrait now depicts an adult woman with an uncovered face, the
approved olive-gold ribbed helmet and goggles, and a separate dark bomb
collar with spaced rectangular lights. Direct native field 218 bank 0,
palette 0 torso crops show an open charcoal jacket, exposed tan upper chest,
and a horizontal cream/beige inner garment. The portrait interprets this as
a tube top, preserving enough chest in the crop to read at 64x64.

The built-in image generation edit and its exact inspected inputs are saved
in `work/rico_suzarn_v8/final_generation.json`. The final source SHA-256 is
`5c8f845efba0cc768ebbe407264ddb6f8e4750d0510abc183f9821335905792a`;
the 4,640-byte native TIM SHA-256 is
`676d51befe9785f3a7a1922f4de4ce108e8551c00ce07ce89fe9cd66594c7096`.
All other portrait source PNGs and provenance entries are unchanged from v7.

## Verification status

Forty-seven focused route/resource/progression/integration/music checks,
eight independent native geography checks, four portrait checks, and three
presentation checks pass. The source and decoded native 64x64 portrait have
been visually inspected against the sprite. Ten mutation checks exercise the
release auditor's rejection of out-of-scope changes.

The initial packaging attempt exposed missing OP1B metadata in the dialogue
processor. Noah's OP_1B explicitly advances seven bytes; adding that verified
instruction length lets the untouched native street resident INITs pass the
processor. A ninth geography regression now runs all four route fields
through final dialogue presentation and checks that ambient bar/street
bundles remain byte-identical. All 22 geography/compiler/presentation checks
pass together. The superseded full test run was stopped before restarting
against these final sources.

`work/rico_suzarn_v8/route_fixed_approved_sources.json` records the final
source freeze. The candidate is `rico-ch2-route-v8-fixed`; the failed initial
`rico-ch2-route-v8` record remains unactivated. The corrected two-disc build
and native audit passed. The full profile suite passed 1,061 tests in
323.261 seconds, with seven skipped (`full_tests_fixed.log`). The corrected
release is explicitly active, and the default `project.py play rico
--check-only` passes with fresh sources and verified media. Runtime status
remains `untested`; no emulator playthrough is claimed. User saves, controls,
and emulator settings were not changed during this update.

The final audit at `work/rico_suzarn_v8/route_fixed_audit_report.json` reports
3,720 unchanged resources on Disc 1 and 3,715 on Disc 2, with eight authorized
changes on each: verified executable FAT, Suzarn portrait 499, commons 744,
new bar/street resources 762–765, and the Champion room bundle. All 90 other
portraits, existing dialogue, visual resources, battles, level-24 state,
infirmary bed/guard, Clerk graphics, and protected Miang content match v7.
All 17 Disc 1 and 12 Disc 2 movies are unchanged. The restored maps preserve
their exact native actors, graphics and other visual components.

Disc 1: 719,333,328 bytes, SHA-256
`8a5b3601ca02a9bd7c747a8359bd2c2f66b27589ac3f4e1125f7781bd5ccb95c`.
Disc 2: 697,930,128 bytes, SHA-256
`bfb0286781711b8598d28f682ca08c5b3165988f7ac299741ec140c369ae59ec`.
