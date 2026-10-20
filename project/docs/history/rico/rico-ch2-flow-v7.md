# Chapter 2 room flow and sprite-grounded portraits

This revision addresses the user's room playtest: Hammer's ascent did not
match the invitation, stationary NPCs obstructed the stairs, walking out did
not transition, Hammer repeated an unexplained coupling exchange, and the
requested room music was inaudible.

The source correction restores the native field218 stair trigger and routes
it to the anthology's D Block commons after the opening flags commit. The
existing reciprocal entries are outside that trigger. Hammer's call and
Rico's invitation precede his awaited climb; NPC parking and collision flags
keep the stairs usable. Repeat dialogue follows the Baptism state and later
story events rather than claiming an unseen parts errand.

The original field scripts identify track47 as The Champ and track71 as
normal Nortune. Main room/bedroom use47; D Block/intake use71; sewers retain13.
The same selection applies after a battle. DuckStation's actual Audio output
volume was0 despite OutputMuted=false. With the emulator closed, only
OutputVolume was changed to50; the exact settings-byte change was audited.

Seven portrait sources were corrected from actor/palette evidence: guard,
Suzarn, infirmary attendant, worker, prisoner, generic battler and clerk.
Worker/prisoner/generic battler share the same native sprite identity and now
share its blue hair/brow-band portrait. Named Leonardo retains his own art.
Suzarn keeps the approved helmet, goggles and bomb collar with an uncovered
nose, mouth and chin. The guard uses blue clothing and pale goggles. The
female doctor's pale head covering and contrasting outfit follow her native
palette; the receptionist uses its teal variant.

The visible D Block clerk previously used Hammer's native actor. A checked
local replacement supplies the actual anonymous arena receptionist in that
existing bank and external texture cell. Gramps' native green tint and squat
scale are restored so his sprite agrees with his already-correct portrait.
Offscreen arena announcements retain their existing artwork.

The larger Chapter 2 point-of-view/story restructuring remains a separate
proposal. Fei's approved bedside staging, guard placement, native bed animation,
Rico's level24 starting profile and protected Mass Driver/Miang content are
outside this revision's changes.

Reference, prompt, source-hash, native-TIM and validation evidence is saved in
`work/rico_npc_portrait_audit_v7`. The final standalone release
`rico-ch2-flow-v7` was built and activated on September 6, 2026. The full
profile suite passed 1,052 tests in 501.964 seconds with seven skipped.
Both discs passed the frozen-source/native-media audit: exactly 21 authorized
resource changes per disc, all other native resources and 29 XA movies exact
against v6. All seven reviewed portraits match their emitted TIM bytes.

The default launcher check passed and the exact v7 playlist opened in
DuckStation. The user stopped Computer Use with physical Escape before the
live scene check could proceed. Runtime gameplay status therefore remains
untested. The isolated QA emulator was closed and pre-QA settings restored
byte-for-byte, preserving the requested output-volume50 correction. User
controller bindings, normal memory cards and existing save states were kept.
