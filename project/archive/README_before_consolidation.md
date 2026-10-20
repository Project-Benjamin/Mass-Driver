# Xenogears Disc 2: Standalone Mass Driver Facility

The **V168 dialogue candidate** is available through
[PLAY_MASS_DRIVER_V168.cmd](output/PLAY_MASS_DRIVER_V168.cmd). It improves the
opening, Gear/Citan continuity, and two clue terminals while preserving the
Miang flashback and original staff correspondence. The disc and independent
rebuild are verified; fresh in-game acceptance remains pending. See the
[V168 notes](docs/mass-driver-dungeon-3.24.md) and
[before/after dialogue](docs/mass-driver-dialogue-v168-changes.md).

V167 remains the preserved standalone baseline. It corrects the Mass Driver story
continuity by keeping Elly in regular retail Vierge (Gear ID 2) beside
Emeralda's Crescens. The New Game bootstrap, field-376 lift handoff, parked
factory actor, fixed Guardian party, post-victory reload, world-map behavior,
dialogue, and manifest all agree on Vierge. Retail Vierge battle resources
2930/2931 remain untouched.

The completed El-Regulus work is preserved separately for its future story
chapter. `tools/build_el_regulus_archive.py` reproduces an exact eleven-file
archive documented in `content/el_regulus_future/`; none of its eight dedicated
payloads are emitted by V167. Shared canonicals 29 and 2594 contain only the
Video Disk edits, while 2614 is restored to retail normal-combat data.

The V167 package contains 133 jobs / 166 replacements. All 166 payloads were
extracted byte-for-byte from the final BIN and all 5,877 affected raw sectors
passed Mode2/Form1 EDC/ECC validation. The disc is 696,144,960 bytes with
SHA-256 `e5b8a00c5c5889a137035b3bd926e697d91a387adc2b78d7940327f1dc6753ea`.

Earlier release facts follow unchanged.

V160 is the frozen west-panel package. It preserves V159's 33-field,
66-edge route, repaired Defense Archive north lift, solid east-wall Central
Control keypad, and continuous finale while widening the post-Guardian west
bulkhead terminal. The live V159 stance at
`(-474.812835693359,-160.151718140625)`, yaw `0x0C00`, triangle 177 was on the
visible panel but depended on a tiny facing-gated `0x04` square. Entity 23 uses
a no-facing OP18 `0x20/0x04` rectangle, effective `80x24`, covering the
complete walkable bank frontage without reaching the door or another console.
The action, boss flag, dialogue, camera, sound, door animation, and persistent
open bit are unchanged. Focused structural checks, all 169 payload
extractions, the exhaustive FAT/raw audit, all 5,846 replacement-sector
checks, a byte-identical independent rebuild, the authoritative 262-test /
2,707-subtest suite, and static/dynamic one-file-installer verification pass.
Fresh user-driven runtime acceptance remains pending.

Historical V159 release facts follow unchanged.

V159 is the current frozen package. It preserves V158's 33-field, 66-edge
route, solid east-wall Central Control keypad, and continuous finale while
repairing the opened Defense Archive north lift. A live V158 capture stopped
at `(3.425583,274.982513)` on triangle 73, before entity 17's old `0x07`
region began. V159 gives entity 0 script 1 a continuous authorization-gated
leader-Z poll at `z>=274`, widens the reachable X fallback to `0x09`, and
makes entity 17 collision script 3 an explicit STOP. The `(0,245)` return
spawn remains outside both entry paths. Full package, sector, repeat-build,
installer, and 262-test / 2,702-subtest verification pass; fresh user-driven
runtime acceptance remains pending.

Historical V158 release facts follow unchanged.

V158 is the current frozen package. It preserves V157's 33-field, 66-edge
route and continuous Central Control finale while moving the compact retail
field-361 standing keypad to the user's newest captured east-wall marker. The
passive static node remains target node 43/model 11, now at anchor
`(197,439,108)`, yaw `0x0800`, with base centre `(153.5,171.5)`.

Hidden entity 16 supplies an immovable solid-only body at `(154,171)`, triangle
24, while entity 12 owns the repeatable, state-neutral Elly observation from
`(136,131)`, triangle 26. Citan follows `(170,89)/32`, `(160,110)/32`, and
`(136,131)/20`; after dialogue 35, the held 12-frame inside-room camera targets
`(145,160,-45)` from `(170,-80,-135)` for the unchanged blocking keypad
operation. The declared stage delta is 2062; the complete FAT payload delta is
17, 22, and 2062.

Historical V157 release facts follow unchanged.

V157 is the current frozen package. It preserves V156's 33-field, 66-edge
route and continuous Central Control finale while replacing the oversized
overhead arm with a compact, recognizable retail field-361 standing keypad at
the user's captured east-wall marker. The keypad is target node 43/model 11 at
anchor `(187,439,30)`, yaw `0x0800`; its graphics are relocated losslessly
inside existing unused target VRAM with no graphics-file growth.

Optional archive entity 12 and Citan now share the checked operator station
`(136,53)`, triangle 28. Citan follows `(170,45)/32`, `(150,35)/32`, and
`(136,53)/20`, ending direction 0. After mutual-facing dialogue 35, the held
12-frame operation camera targets `(140,70,-45)` from `(300,-150,-135)` and
one blocking entity-3 script-23 call visibly operates the keypad before launch.
The declared stage delta is 2062 and 2063; the complete FAT payload delta is
17, 22, 2062, and 2063.

Historical V156 release facts follow unchanged.

V156 is the current frozen package. It preserves V155's 33-field, 66-edge
route and continuous Central Control finale while adding the recognizable
terminal Citan visibly operates. Exact retail field 373 node 44/model 7 is
appended as target node 43/model 11 at `(88,0,168)`, yaw `0x0200`; the old 43
nodes, old 11 models, graphics, walkmesh, wall bank, and actor collision remain
byte-identical.

Citan now walks the checked route to `(57,63)`, triangle 23, direction 4. He
and Elly face each other for dialogue 35; afterward a 12-frame held-mode side
camera frames the imported terminal and one blocking entity-3 script-23 call
runs the finite field-378 keypad animation, three sound-`0xF9` calls, and
`25/35/24` waits before completion and world-map launch. The declared stage
delta is canonical 2062; the complete FAT payload delta is 17, 22, and 2062.

Historical V155 release facts follow unchanged.

V155 is the current frozen package. It preserves V154's 33-field, 66-edge
route, widened Central Control console, native transition chime, subjective
Zeboim memory, local capsule launch, and guarded field-617 return while making
the memory-to-launch finale one continuous action. After present dialogue 32,
the held camera interpolates automatically to a whole-room view; Citan enters
through the native east leaf and stops direction 7 at its authentic right
hanging terminal. No second Cross/X press is required.

The fresh path reuses the fixed-camera mode already held by dialogue 32. The
interrupted recovery path enters that mode explicitly, and both paths share one
reveal, door, walk, and arrival-bit suffix. Only the leader turns toward Citan;
the whole-room target `(-13,106,-32)` and eye `(-27,-767,-544)` remain held
through dialogue 35, launch, and world-map unload. Entity 13 stays at
`(-48,97)` on triangle 16 with its no-facing `72x20` frontage. The declared
stage delta is canonical 2062; the complete FAT payload delta is 17, 22, and
2062, with one descriptor size change.

Historical V154 release facts follow unchanged.

V154 is the current frozen package. It preserves V153's 33-field, 66-edge
route, widened Central Control console, subjective Zeboim memory, natural Citan
entrance, held arrival camera, local capsule launch, and guarded field-617
return. Immediately after present-day dialogue 21 closes, entity 13 now plays
the retail save-point entry chime with exact bytes `74 50 80`, then begins the
first fade without an added wait. After memory dialogues 22-31 and 36, the
party returns under a concise present camera and dialogue 32 supplies the sole
present response. Dialogues 33 and 34 remain authored but unreachable. All 18
entity-13 F5 calls use control flag `0x01`.

The console remains at `(-48,97)` on triangle 16 with no-facing OP18 X/Z
operands `0x1C/0x02`, effective reach `72x20`, and region X `[-120,24]`,
Z `[77,117]`. The stable `(174,-102,-125)` eye, hidden entity-19 Miang anchor,
visible entities 17/18, Citan route, native east door, held camera, launch, and
return are unchanged. The declared stage delta is canonical 2062; the complete
FAT payload delta is 17, 22, and 2062, with one descriptor size change.

Historical V153 release facts follow unchanged.

V153 is the current frozen package. It preserves V152's 33-field, 66-edge
route while repairing the second captured Central Control console dead zone and
removing the memory's redundant present-day tail. Entity 13 is now at
`(-48,97)` on triangle 16 with a no-facing rectangular OP18 frontage: X/Z
operands `0x1C/0x02`, effective reach `72x20`, and inclusive region
X `[-120,24]`, Z `[77,117]`. It accepts the new user stance `(-113,113)` on
triangle 15, the earlier `(-15,113)` stance, and both F2 readings. Entity 12's
archive begins at X 25, leaving an exact one-unit gap; entity 14 is disjoint.

Dialogue 12 and Emeralda's sole present-day cue, dialogue 21, now precede the
fade, party hide, and POV. A silent reaction shot leads into memory dialogues
22-31 and 36 only; dialogues 32-34 remain in the byte-identical dialogue
archive but are unreachable. All 17 remaining entity-13 F5 calls use flag
`0x01`. The stable `(174,-102,-125)` eye, hidden entity-19 Miang anchor,
authored dialogue, visible entities 17/18, Citan route, native east door, held
arrival camera, launch, and field-617 return are unchanged. The declared stage
delta is canonical 2062; the exhaustive FAT payload delta is 17, 22, and 2062,
with exactly one descriptor size change for canonical 2062.

Historical V152 release facts follow unchanged.

V152 is the current frozen package. It preserves V151's 33-field, 66-edge
route and repaired `28x18` center-console frontage while fixing the subjective
memory's stopped dialogue and extreme close-up. The captured V151 failure state
with SHA-256
`8bc81de760fda0ba5522c01b439a4aa152082bd8c48182e560c62f8747419717`
reached dialogue 21 with hidden entity 13 as owner. Its F5 control flag `0x00`
made native WAIT_DIALOG take OP_STOP, terminating the action with the camera and
actors stranded and bit 12 clear.

All 20 entity-13-owned dialogue calls now use F5 flag `0x01`. Every one of the
12 memory eyes is the stable Miang-aligned `(174,-102,-125)`, about `2.79x` to
`3.25x` the prior target distance. Entity 19 remains hidden at `(14,58)`;
camera targets, authored dialogue, visible entities 17/18, Citan's entrance,
native east door, held arrival camera, launch, and field-617 return are
unchanged. The declared and exhaustive V151-to-V152 payload deltas are both
exactly canonical 2062; all 4,147 FAT descriptors are unchanged.

Historical V151 release facts follow unchanged.

V151 is the current frozen package. It preserves V150's 33-field, 66-edge
route and complete Central Control finale while repairing the live
center-console dead zone. The rejected engine stance `(-15,113)`, triangle 20,
yaw `0x0C00` was already inside V150's 24-by-24 box, but its facing delta 3350
fell just outside the accepted cone. Entity 13 remains at `(-4,118)` on
triangle 19 and prepared header node 29/model 5; it now uses no-facing OP18
operands X `0x06` / Z `0x01`, for effective reach `28x18`.

Entity 12's archive and entity 14's native east-door regions remain disjoint
from the shallow entity-13 frontage. The first interaction still shows only
the Launch Director and Systems Officer while hidden entity 19 supplies
Miang's POV and offscreen `MIANG` voice. Citan's stage, bounded walk, SHOW and
native-door ordering, held camera, complete action routine, launch, and guarded
field-617 return are byte-identical to V150. The declared and exhaustive
V150-to-V151 payload deltas are both exactly canonical 2062; all 4,147 FAT
descriptors are unchanged.

Historical V150 release facts follow unchanged.

V150 is the current frozen package. It preserves V149's 33-field, 66-edge
route, centered entity-13 control-panel frontage at `(-4,118)` on triangle 19,
24-unit facing-gated operand `0x04`, F2 marker `(-3.642,114.571)`, and retired
entity-16 chest whose 32 action slots point to STOP.

The first interaction is now strictly Elly's subjective point of view. Only
entity 17, the Launch Director, and entity 18, the Systems Officer, are visible.
Entity 19 is hidden at `(14,58)` as Miang's point-of-view actor; every memory
eye is `(14,58,-125)`, no camera targets Miang, and her offscreen lines retain
the `MIANG` label. Entities 14 and 15 remain byte-identical to V149.

On the second interaction, Citan is hidden at `(225,104)` behind the native east
leaf. Scoped F8 mask `0x0038` permits only the first bounded leg to `(170,89)`
before clearing; he then walks through `(100,89)/32`, `(60,84)/20`, and
`(20,80)/20`, settling direction 7. One arrival camera remains held while the
field is shown, native entity 15 script 4 opens the leaf, Citan enters, and the
capsule launches. There is no release, second cut, final-camera reprojection,
or closed-leaf reprojection; the leaf stays visually open through world map.

The declared V149-to-V150 stage delta is canonical 2062 only. The exhaustive
FAT payload delta is 17, 22, and 2062; 17 and 22 are regenerated FAT mirrors.
One of 4,147 descriptors changes only canonical 2062's size from 126,524 to
126,444 bytes at unchanged sector 221,314. Entry kinds and directory
memberships are unchanged; 3,720 of 3,723 extractable payloads are identical.

Historical V149 release facts follow unchanged.

V149 is the current frozen package. After the five nuclear reserve magazines,
the route ends directly in Mass Driver Central Control target 728. Targets 388
and 507 remain absent from the active route and package, and the finale uses no
Krelian laboratory assets.

Invisible entity 13 now sits at `(-4,118)` on walkmesh triangle 19, directly on
the centered back-wall control panel carried by prepared header node 29/model 5.
Its native facing gate and operand `0x04` give 24-unit effective reach at the
accepted F2 marker `(-3.642,114.571)`, rounded to `(-4,115)` at yaw `0x0C00`.
The native entity-16 treasure chest is retired: all 32 of its script slots point
to the donor STOP, so only the control panel can initiate the finale.

The first X interaction presents Elly's subjective Zeboim-era memory; Emeralda
sees the empty room. V149 preserves V148's exact native component-04 sprite
archives for Miang, the Systems Officer, and the Launch Director. The second X
interaction opens the native east door and stages Citan at `(170,89)` before a
short material-safe walk through `(100,89)`, `(60,84)`, and `(20,80)`. He settles
facing direction 7 without waiting through the old blocked bounds, then runs the
dialogue, capsule launch, retail Mass Driver cinematic, and guarded
Elly/Emeralda return locally in Central Control.

The declared and exhaustive V148-to-V149 payload deltas are both exactly
canonical 2062. All 4,147 FAT descriptors, entry kinds, and directory
memberships are byte-identical; 3,722 of 3,723 extractable payloads are
unchanged.

Historical V148 release facts follow unchanged.

V148 is the current frozen package. After the five nuclear reserve magazines,
the route ends directly in Mass Driver Central Control target 728. Targets 388
and 507 are absent from the active route and package, and the finale uses no
Krelian laboratory assets.

Entity 13 at `(-54,94)` owns the complete two-interaction finale. The first X
interaction presents Elly's subjective Zeboim-era memory; Emeralda sees the
empty room. V148 imports the exact native component-04 sprite archives for
Miang, the Systems Officer, and the Launch Director, fixing the pixel-sized dot
rendering produced by actor-only imports. The second X interaction brings Citan
through the native east door and runs the dialogue, capsule launch, retail Mass
Driver cinematic, and guarded Elly/Emeralda return locally in Central Control.

The declared V147-to-V148 delta removes canonicals 1382, 1383, 1620, and 1621
and changes canonicals 2062 and 2595. The exhaustive FAT payload delta is
exactly 17, 22, 1382, 1383, 1620, 1621, 2062, and 2595. Of 3,723 extractable
payloads, 3,715 are byte-identical. The 2,599 descriptor changes preserve every
entry kind and directory membership; canonicals 3715 and 3723 remain unchanged.

Historical V147 cloned the exact compact retail Disc 1 field-573 Krelian
computer room into target 507. Its small square shell, walkmesh, six static
nodes, centered baked control-panel bank, entity-7 controller, bounded Citan
route, and finite entity-10 panel beat are preserved in the frozen V147 package
and [its release notes](docs/mass-driver-dungeon-3.08.md). Its declared delta
from V146 was canonicals 1620 and 1621; its complete FAT payload delta was 17,
22, 1620, and 1621.

Historical V146 moved the final sequence into the exact retail field-507
Krelian/Ouroboros laboratory. Its invisible entity-19 frontage was at
`(191,-522)` on walkmesh triangle 1 with 24-unit reach, and its staged delta was
canonicals 1620, 2062, and 2063. Its exhaustive FAT payload delta was 17, 22,
1620, 2062, and 2063.

Historical V145 restored the complete native workstation around the final
launch apparatus. Its invisible entity-19 frontage was at `(187,-250)` on
walkmesh triangle 141 with 48-unit reach, and its declared/staged and complete-
FAT V144-to-V145 delta was exactly canonical 1620. Canonical 1621 and every
other payload were byte-identical, with zero FAT descriptor changes. V145 also
preserved V144's live-camera authorization and automatic north-lift behavior.

Historical V144 changed the complete ABCD authorization so it keeps the live
Defense Archive camera instead of zooming to the already-visible north lift.
The accepted-code tail plays sound `0x77`, opens both native-textured leaves
through helper entities 18 and 19, and waits 32 field frames. Once authorized,
the player walks through the open lift without pressing X; before
authorization, collision is silent and the X fallback retains locked dialogue
9.

Lift controller entity 17 is centered at `(0,308)` with no-facing bound
operand `0x07` and 30-unit effective reach. z=`277` is safe and z=`278` is the
first authorized contact row; x=`-28..28` is covered at the threshold. The
return spawn at `(0,245)` is 63 units from the controller and cannot bounce the
player back into the lift. The declared/staged and exhaustive complete-FAT
V143-to-V144 deltas are both exactly canonical 1358; every other payload and
all FAT descriptors remain byte-identical.

Historical V143 fixed the Guardian-battle command-menu exception by restoring
even alignment in canonical 29 and returned the final capsule launch to the
exact retail Disc 1 field-507 Krelian/Ouroboros laboratory shown in
`lastroom.png`. V144 preserves v142's
Defense Archive controller frontages, v141's distinct interceptor head and
three-cell exhaust, v140's compact five-cell blasts and Missile-specific sound,
v139's bounded incoming tails, safe `(640,384)` arcade atlas, real-time worker
scheduler, single-center-base rules, field-363 station, and complete 35-field
route. V143's declared/staged V142-to-V143 replacement delta is exactly canonical
IDs 29, 1620, and 1621. Generated FAT bookkeeping canonicals 17 and 22 also
change because the rebuilt archive and disc layout move their recorded
locations; they add no gameplay content.

V142's unpadded Video Disk item-name entry shifted the later El-Regulus command
table to odd archive offset `0x51A7`. Opening the Gear command menu could then
raise an address-error exception inside `GetStringEntry`, producing the
observed Guardian-fight freeze. V143 added one zero alignment byte after the
2,469-byte logical entry, moves the command table to even offset `0x51A8`, and
leaves every visible item and command name unchanged.

V137 removed the shoot-triggered simulation pause. The terminal action handles
input and progression with one wait per field frame while finite automatic
script-1 workers on entities 16-20 and 22-27 advance enemies, interceptors,
fireballs, trails, terrain, HUD, and cursor concurrently. Request/acknowledgement
handshakes order setup, active play, pause, resume, wave clear, and teardown.
Every worker stops without an internal wait; the largest unconstrained
compositor path is 871 operations under ATEL's 1,024-opcode guard and
904-cycle soft budget, with maximum call depth three.

V138 makes that real-time renderer background-safe. A player interceptor is now
exactly three grid-aligned 6-by-6 blocks--hot, bright, and dim--with the hot
block serving as the visible shot and no separate off-grid player-head tile.
Enemy owners leave one red 1-by-1 foreground point and the cursor worker draws
one white 1-by-1 head point. Only foreground pixels move off grid, so opaque
6-by-6 CRT-grain tiles can no longer stamp phase-shifted squares into the
playfield. The authored gray CRT board and unchanged atlas remain intact.

V139 bounds each incoming missile's visible history to exactly three red
prior-head points plus its current white head. Before the FIFO advances, the
expired oldest point restores its phase-correct CRT background cell. Hit,
impact, spawn, and wave-reset paths clear retained history, so long red
framebuffer lines cannot survive. Player shots remain the same three
grid-aligned hot, bright, and dim blocks.

V140 makes every interceptor and chain detonation a compact five-cell cross:
the center appears first, expands to center plus four cardinal neighbors,
holds briefly, then contracts to the center before complete cleanup. Missile
Command alone now uses retail field sound `0x51` for explosions. Nuke retains
its distinct `0x77` crash cue, as do the historical door and machinery uses of
that sound.

V141 separates the moving interceptor from its exhaust and later explosion.
The existing grid-aligned `interceptor` tile supplies only seven colored
foreground pixels through two narrow strips, so none of its baked CRT
background is copied. Exactly three prior cells remain as hot, bright, and dim
exhaust; the `explosion` tile appears only after detonation. Canonical 2476 and
its VRAM placement remain unchanged.

V142 aligns the Defense Archive's X regions to their visible operator sides.
Authorization entity 13 and entities 21 through 26 now use the native facing
gate with tight `0x04` bounds; long east-bank reader entity 20 retains its
required `0x24` bound but is facing-gated too. Dialogue-21 reader entity 25 now
centers at `(-260,105)`, matching the accepted live stance
`(-260.214,92.209)`, yaw `0x0C00`, triangle 196. The rejected empty-floor
stance `(-221.548,55.813)`, yaw `0x0800`, triangle 197 selects no console.

Field 363 still uses the authentic field-373 terminal at the captured
south-wall location. Its 192 used atlas indices remain losslessly mapped into
228 free row-485 slots, with native row 488, native door models 0/1, and their
1,118 texture bytes preserved. The original wall panel remains inert, and the
rejected south door and field-365 annex remain absent.

The Defense Archive southeast computer opens a root menu with `Arcade Games`,
`Video Disk`, and `Leave`. `Arcade Games` opens a second menu with `Play NUKE`,
`Missile Command`, and `Back`; `Back` returns to the root menu. The disk branch
remains available whether or not Elly owns the Video Disk, and the root `Leave`
branch restores player control without launching a game, checking inventory,
or starting playback.

The current seven-frame archive reel uses Celia Ren only for its opening ZBC
newsroom frame.  It then shows the existing restaurant overlook, affluent
families buying lavish private fallout shelters, nationwide food lines, a
poorer mob burning a wealthy estate, an empty maternity ward during the
collapse in birth rates, and a live warning of a nuclear-missile launch,
retaliation beginning, failing command links, and the instruction to find
shelter, ending `This is not a drill.`  It does not narrate the exchange's
outcome or its own aftermath.  The former Miang political report is no longer
part of the reel.  The one-time `Received
Video Disk` notice uses the standard compact 40-by-2 item-receipt window
instead of reserving five text rows.

Missile Command now uses an Atari 2600-style single center base and one fire
button. This is not a claim of an exact full 2600 clone: the embedded game keeps
the arcade revision-3 ordinary-missile quotas, scoring curve, bonus cities,
and bounded enemy set, while cruise missiles remain deferred. The maximum
22-missile quota begins at wave 19 and repeats thereafter; the displayed wave
and best-wave record cap at 31. Six cities flank one center base. Cross launches from its 10-round
loaded set; another 20 ABMs begin underground and reload in sets of ten. A base
hit loses only the loaded set, leaving the underground reserve available.

Three center-launched ABMs or their fireballs and three attacker-seeded chain
explosions can coexist. Each moving ABM has a distinct foreground-only head
followed by exactly three hot, bright, and dim exhaust cells; that presentation
is project-specific, not a documented Atari 2600 rule. Triangle pauses, Cross
resumes, and Circle exits from pause.
The x1-through-x6 multiplier, 25-point interceptions, 5-point unused missiles,
100-point surviving cities, 10,000-point bonus cities, three-city per-wave loss
limit, and play-until-the-cities-are-gone structure remain. Score, best wave,
and the shared four-letter pilot remain persistent, including v129/v130 record
migration. V142 changes only Defense Archive controller frontage, not those
rules, V141's player-projectile presentation, V140's compact blasts, or the
Missile-specific explosion sound.

V161 has a 252,161-byte source-stage manifest, SHA-256
`7b3a65389d7b557e52d94c353e717eb951e0afd4b05d4fd591a8e082754e6d8a`,
with 136 jobs, 169 unique replacements, 11,804,464 replacement bytes, 33
fields, and 66 directed edges. Target 384 canonical 1374 remains 162,324
bytes with SHA-256
`3f294aacbf4a5fd1fc535015042364b7ce5a6a925547bc061906aee3edc57ba7`;
its 21,205-byte script has SHA-256
`a0f485a0e7537ff90754baacf1c5dbb62eab5922f84778b51cc3d3575bbae315`.
Canonical 2960 is 33,608 bytes with SHA-256
`78eee071519dc5ee3cbbf5ca0080c69923580b6443b3e48e9759db451b6da46c`.
Direct final-BIN extraction matches all 169 staged payloads, the exhaustive
FAT/raw-sector audit records no relocation, and all 5,846 replacement sectors
pass Mode2/Form1 EDC/ECC. An isolated repeat build matches all 550 stage files,
the manifest, BIN, and CUE byte-for-byte. Static and dynamic V161 installer QA
passes; Play launcher `1.6.1.0` is 446,464 bytes with SHA-256
`7001509183bcc90986fbee68450cb33a8ae171134ecd7a85dde528162910f0c9`.
The authoritative suite passes 262 tests / 2,706 successful subtests in
20.355 seconds with exit 0 and all failure counters zero. Fresh runtime replay
remains pending. See
[the V161 Guardian battle notes](docs/mass-driver-dungeon-3.22.md).

Historical V160 package-summary facts follow unchanged.

V160 has a 251,375-byte source-stage manifest, SHA-256
`c77dd76e5dff304fbb348a71dc9269cc01f87bc3f3b0651d8efb5891d1b46cf3`,
with 136 jobs, 169 unique replacements, 11,804,460 replacement bytes, 33
fields, and 66 directed edges. Target 376 remains 190,444 bytes but now has
SHA-256
`3badf3f1718522e5c798954017a96d104cb75713f4becf4eeeaa932b22350bd9`;
its 48,930-byte script has SHA-256
`bdbcfacf464841df93ba2a415aea03559273f715298e6ad98a189c29cfb3bcbc`.
Focused tests pin the exact live stance, complete visible frontage, shallow
depth, unique selection, two-byte V159 script delta, and unchanged action.
All 169 packaged payloads, the exhaustive FAT/raw audit, all 5,846 replacement
sectors, a byte-identical independent BIN/manifest rebuild, 262 tests / 2,707
successful subtests, and static/dynamic one-file-installer checks pass. Runtime
status is reported in release validation. See
[the V160 west-panel frontage notes](docs/mass-driver-dungeon-3.21.md).

Historical V159 package-summary facts follow unchanged.

V159 has a 249,477-byte source-stage manifest, SHA-256
`f6aa96575db50a4a90a39036c072e29e777c0d28d00841868d3d4ce762700020`,
with 136 jobs, 169 unique replacements, 11,804,460 replacement bytes, 33
fields, and 66 directed edges. The current target-376 bundle is 190,444 bytes
with SHA-256
`9696899ce837eee05e727627a2f2f2fd2b8828e90f51ca071dab6ab4fffd6a6f`.
Focused structural and regression tests pass for the automatic `z>=274` poll,
reachable `0x09` X fallback, inert collision script, and safe `(0,245)` return.
All 169 packaged payloads, the exhaustive FAT/raw-sector audit, 95/95 extended
field/FAT Mode2 sectors per image, a byte-identical repeat build, the static and
dynamic one-file installer checks, and 262 tests / 2,702 successful subtests
pass. Fresh user-driven lift/runtime acceptance remains pending. See
[the V159 Defense Archive lift notes](docs/mass-driver-dungeon-3.20.md).

Historical V158 package-summary facts follow unchanged.

V158 has a clean 249,070-byte source-stage manifest, SHA-256
`c01792fae7de6ab3bdcdf214c2b16e30dca7101ebc31a92e45ad021bb56ffe7f`,
with 136 jobs, 169 unique replacements, 11,804,468 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads extracted directly from the
final BIN match the stage byte-for-byte; all 5,846 replacement sectors, all
nine logical-delta sectors, and the 5,849-sector union including boot pass
MODE2/Form1 EDC/ECC. A second complete stage, manifest, and BIN rebuild is
byte-identical. The authoritative V158 release run passed 262 tests / 2,693
successful subtests in 20.844 seconds with exit 0 and zero failures, errors,
failed subtests, skips, expected failures, or unexpected successes. Fresh
user-driven console, collision, remark,
route, operation, launch, and return acceptance remains pending. See
[the V158 solid-console notes](docs/mass-driver-dungeon-3.19.md).

Historical V157 package-summary facts follow unchanged.

V157 has a clean 246,356-byte source-stage manifest, SHA-256
`0a8f9e99a471f7af841a42f5ff22a802dfb4282057bcafb80e3e245a34365345`,
with 136 jobs, 169 unique replacements, 11,804,928 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads extracted directly from the
final BIN match the stage byte-for-byte; all 5,846 replacement sectors, all
166 logical-delta sectors, and the 5,863-sector union including boot pass
MODE2/Form1 EDC/ECC. A second complete stage, manifest, and BIN rebuild is
byte-identical. The authoritative V157 run passed 262 tests / 2,693 successful
subtests in 21.558 seconds with exit 0 and zero failures, errors, failed
subtests, or skips.
Fresh user-driven compact-keypad, route, operation, launch, and return
acceptance remains pending. See
[the V157 compact-keypad notes](docs/mass-driver-dungeon-3.18.md).

Historical V156 package-summary facts follow unchanged.

V156 has a clean 245,085-byte source-stage manifest, SHA-256
`ab46ece79e120786f8a18a56972623c5eee8e758a77b55776a4d526520fa95dc`,
with 136 jobs, 169 unique replacements, 11,807,356 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads extracted directly from the
final BIN match the stage byte-for-byte; all 5,848 replacement sectors, all 80
logical-delta sectors, and the boot sector pass MODE2/Form1 EDC/ECC. A second
complete stage, manifest, and BIN rebuild is byte-identical. The authoritative
V156 structural run passed 262 tests / 2,693 successful subtests in 21.010
seconds with exit 0 and zero failures, errors, failed subtests, or skips.
Fresh user-driven hanging-terminal, mutual-facing,
operation, launch, and return acceptance remains pending. See
[the v156 terminal-operation notes](docs/mass-driver-dungeon-3.17.md).

Historical V155 package-summary facts follow unchanged.

V155 has a clean 241,652-byte source-stage manifest, SHA-256
`5eed39c013a4bb792ccc34bc130c67fb1fb45c27369d2d5bad9f0f511080456a`,
with 136 jobs, 169 unique replacements, 11,804,404 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads extracted directly from the
final BIN match the stage byte-for-byte; all 5,849 audited changed,
replacement, and boot sectors pass MODE2/Form1 EDC/ECC validation. A second
complete stage, manifest, and BIN rebuild is byte-identical. The authoritative
V155 structural run passed 262 tests / 2,691 successful subtests in 20.471
seconds with exit 0. Fresh user-driven automatic-handoff, whole-room-camera,
right-terminal, launch, and return acceptance remains pending. See
[the v155 automatic-finale notes](docs/mass-driver-dungeon-3.16.md).

Historical V154 release facts follow unchanged.

V154 has a clean 239,448-byte source-stage manifest, SHA-256
`e0423870efc38045b98356d088fce6633cd918369554af17011e2f26e6e566d5`,
with 136 jobs, 169 unique replacements, 11,804,396 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads extracted directly from the
final BIN match the stage byte-for-byte; all 5,849 audited changed,
replacement, and boot sectors pass MODE2/Form1 EDC/ECC validation. A second
complete stage and BIN rebuild is byte-identical. The authoritative V154
structural run passed 262 tests / 2,689 successful subtests in 20.451 seconds
with exit 0. Fresh user-driven chime, present-response, and preserved-finale
acceptance remains pending. See [the v154 transition notes](docs/mass-driver-dungeon-3.15.md).

Historical V153 release facts follow unchanged.

V153 has a clean 238,991-byte source-stage manifest, SHA-256
`5e7ee65fd047484fcb5d378a1991ede34e89f5bdeab2079804df3c980fa8c3e0`,
with 136 jobs, 169 unique replacements, 11,804,480 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads were extracted directly from
the final BIN and matched the stage byte-for-byte; all 5,849 audited changed,
replacement, and boot sectors passed MODE2/Form1 EDC/ECC validation. A second
complete stage and BIN rebuild matched byte-for-byte. The authoritative V153
structural run passed 262 tests / 2,689 subtests in 20.106 seconds with exit 0.
Fresh user-driven widened-console, memory, and preserved-finale acceptance
remains pending. See [the v153 finale notes](docs/mass-driver-dungeon-3.14.md).

Historical V152 release facts follow unchanged.

V152 has a clean 237,913-byte source-stage manifest, SHA-256
`fe7d6b8ecc2bb1af358757090227c2e8d58d7c666c5d88b8e485ec193eff8f41`,
with 136 jobs, 169 unique replacements, 11,804,532 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads were extracted directly from
the final BIN and matched the stage byte-for-byte; all 5,846 replacement
sectors and the boot sector passed MODE2/Form1 EDC/ECC validation. A second
complete stage and BIN rebuild matched byte-for-byte. The authoritative V152
structural run passed 262 tests / 2,682 subtests in 20.391 seconds with exit 0.
Fresh user-driven memory-dialogue, camera, and preserved-finale acceptance
remains pending. See [the v152 memory-dialogue notes](docs/mass-driver-dungeon-3.13.md).

Historical V151 package-summary facts follow unchanged.

V151 has a clean 237,578-byte source-stage manifest, SHA-256
`a62687e0bc871410d6dd461e36ff79776d80a9b3b7ee268cc623dac8206775c0`,
with 136 jobs, 169 unique replacements, 11,804,532 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads were extracted directly from
the final BIN and matched the stage byte-for-byte; all 5,846 replacement
sectors and the boot sector passed MODE2/Form1 EDC/ECC validation. A second
complete stage and BIN rebuild matched byte-for-byte. The authoritative V151
structural run passed 262 tests / 2,682 subtests in 22.641 seconds with exit 0.
Fresh user-driven center-console and preserved-finale visual acceptance remains
pending. See [the v151 center-console notes](docs/mass-driver-dungeon-3.12.md).

Historical V150 package-summary facts follow unchanged.

V150 has a clean 237,297-byte source-stage manifest, SHA-256
`2c3585a1a22ca46049597536e40759d00c7708a40756de591a5ac09e37578328`,
with 136 jobs, 169 unique replacements, 11,804,532 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads were extracted directly from
the final BIN and matched the stage byte-for-byte; all 5,846 replacement
sectors and the boot sector passed MODE2/Form1 EDC/ECC validation. An
independent stage and full BIN rebuild matched byte-for-byte. The authoritative
V150 structural run passed 262 tests / 2,681 subtests in 23.044 seconds with
exit 0. Fresh user-driven Central Control visual acceptance remains pending.
See [the v150 subjective-memory and Citan-entrance notes](docs/mass-driver-dungeon-3.11.md).

Historical V149 package-summary facts follow unchanged.

V149 has a clean 237,200-byte source-stage manifest, SHA-256
`be30b9fd1974050c52992d98989486ddb17eed95a24986cfd130101ad94aeeb5`,
with 136 jobs, 169 unique replacements, 11,804,612 replacement bytes, 33
fields, and 66 directed edges. All 169 payloads were extracted directly from
the final BIN and matched the stage byte-for-byte; all 5,846 replacement
sectors and the boot sector passed MODE2/Form1 validation. The authoritative
V149 full suite passed 262 tests / 2,681 subtests in 20.918 seconds with exit 0.
Fresh user-driven Central Control visual acceptance remains pending. See
[the v149 control-panel and Citan-arrival notes](docs/mass-driver-dungeon-3.10.md),
[the v148 Central Control finale notes](docs/mass-driver-dungeon-3.09.md),
[the v147 compact-final-room notes](docs/mass-driver-dungeon-3.08.md),
[the v146 finale-relocation notes](docs/mass-driver-dungeon-3.07.md),
[the historical v145 workstation-restoration notes](docs/mass-driver-dungeon-3.06.md),
[the historical v144 live-camera and automatic-lift notes](docs/mass-driver-dungeon-3.05.md),
[the historical v143 alignment and final-room notes](docs/mass-driver-dungeon-3.04.md),
[the historical v142 controller-frontage notes](docs/mass-driver-dungeon-3.03.md),
[the historical v141 projectile notes](docs/mass-driver-dungeon-3.02.md),
[the historical v140 compact-blast notes](docs/mass-driver-dungeon-3.01.md),
[the historical v139 bounded-tail notes](docs/mass-driver-dungeon-3.00.md),
[the historical v138 background-safe rendering notes](docs/mass-driver-dungeon-2.99.md),
[the historical v137 real-time worker notes](docs/mass-driver-dungeon-2.98.md),
[the historical v136 arcade correction notes](docs/mass-driver-dungeon-2.97.md),
[the historical v135 station notes](docs/mass-driver-dungeon-2.96.md), and
[the historical v131 Missile Command notes](docs/mass-driver-dungeon-2.94.md).

The national-security record on entity 20 remains attached to its visible
terminal face at controller `(507,175)`, approached from `(435,168)` on
walkmesh triangle 235. Facing-gated operand `0x24` gives an effective reach of
88 units. Shared arcade/video computer entity 21 moves its invisible pivot to
`(264,-148)` and retains facing with `0x0C/0x0C` bounds, giving 40-by-40-unit
effective reach. This includes the captured dead-zone stance
`(274.787613,-165.414902)` and the established `(264,-175)` approach while
remaining disjoint from every other terminal. The video-disk pickup entity 26
likewise moves its invisible point to `(-75,-148)` and uses facing-gated
`0x0C/0x0C` bounds for 40-by-40-unit effective reach. That region includes the
captured dead-zone stance `(-83.166046,-164.725983)` and the established
`(-75,-167)` approach while remaining isolated from neighboring controllers.
Entities 13, 22, 24, and 25 retain facing-gated operand `0x04` with 24-unit
reach. Entity 23 retains its no-facing `0x20/0x04` west-panel frontage. Entity
25 remains at `(-260,105)` so dialogue 21 opens from the user-accepted
visible-console stance `(-260.214,92.209)` rather than the rejected empty-floor
stance `(-221.548,55.813)`.

The playable Nuke game uses `screenshotz/nuke_game.png` as its terminal image
and includes D-pad steering, a jet-fire contrail, targets, levels, sound,
pause/resume, game-over retry, four-letter name entry, and persistent score,
best-level, and initials records. V142 retains its framed 28-by-16 board
with 4-by-6 glyphs on a regular 5-by-7 grid, a two-row `SCORE`/`BEST` and
`LEVEL`/`TARGET x/5` HUD, and centered intro, pause, game-over, and name-entry
panels.

Start is reserved by the field engine before actor bytecode can consume it and
is not a Nuke control. The intro advertises `CROSS` / `LAUNCH/PAUSE`: Cross
launches, pauses and resumes during flight, and retries after game over, while
Circle exits. Name entry displays `CROSS NEXT / SAVE` and `CIRCLE BACK`; Cross
advances and saves on the fourth slot, while Circle moves back.

The current V161 package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v161.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: b010fcb46946e5e1595d7225652bd78f04b91e97a5b6dce0cc8cf0675ed49bf4

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v161.cue
CUE size: 107 bytes
CUE SHA-256: 06149bd106fdd02fe1baacbae6b07b001411bb4ecfb6cc501efd199ea0379561

manifest: work/mass_driver_v161_stage/manifest.json
manifest size: 252,161 bytes
manifest SHA-256: 7b3a65389d7b557e52d94c353e717eb951e0afd4b05d4fd591a8e082754e6d8a
jobs / replacements / bytes: 136 / 169 / 11,804,464
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: 1cebbdb3bbdc7a46ac4c86b7dabbd787bdb20813786eb1e87993145dd1112b7f
canonical-ID/size/payload SHA-256: de4dae7ab4f33a3081595b55ed51783f2728af833b25f3f9ecfb72fa99fb0d86
```

Target 384 canonical 1374 is 162,324 bytes with SHA-256
`3f294aacbf4a5fd1fc535015042364b7ce5a6a925547bc061906aee3edc57ba7`.
Its 21,205-byte script has SHA-256
`a0f485a0e7537ff90754baacf1c5dbb62eab5922f84778b51cc3d3575bbae315`.
Canonical 2960 is 33,608 bytes with SHA-256
`78eee071519dc5ee3cbbf5ca0080c69923580b6443b3e48e9759db451b6da46c`.

Historical V160 package-identity facts follow unchanged.

The frozen V160 package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v160.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: 8f37d9ddf3487abbd599ca2daaef10ed17006ef054107fcd36ab71197709f7d0

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v160.cue
CUE size: 107 bytes
CUE SHA-256: 051d53cc064e25b37dd5497e62f3fda4788d5a2080b0b0092256b2b89d61f6a9

manifest: work/mass_driver_v160_stage/manifest.json
manifest size: 251,375 bytes
manifest SHA-256: c77dd76e5dff304fbb348a71dc9269cc01f87bc3f3b0651d8efb5891d1b46cf3
jobs / replacements / bytes: 136 / 169 / 11,804,460
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: 06ad32f3a4296ae642eb2ce8a597dce3a00385c6a8a87da239d52dc520689e3b
canonical-ID/size/payload SHA-256: dedc1fc799dd7d092b8d2832770b4c185d33915b0084e10a19527b107d483b5b
```

Target 376 canonical 1358 is 190,444 bytes with SHA-256
`3badf3f1718522e5c798954017a96d104cb75713f4becf4eeeaa932b22350bd9`.
Its 48,930-byte script has SHA-256
`bdbcfacf464841df93ba2a415aea03559273f715298e6ad98a189c29cfb3bcbc`.

Historical V159 package-identity facts follow unchanged.

The current V159 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v159.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: 3bb06df72182f72beb2f25ccae2fa244a4a44aa198f9f3224a6262940b080927

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v159.cue
CUE size: 107 bytes
CUE SHA-256: 9b84d3513ae22b6415e005bf286d1b4637ea6d92a142a18056b3010229dbf6db

manifest: work/mass_driver_v159_stage/manifest.json
manifest size: 249,477 bytes
manifest SHA-256: f6aa96575db50a4a90a39036c072e29e777c0d28d00841868d3d4ce762700020
jobs / replacements / bytes: 136 / 169 / 11,804,460
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: 7a543d7ad665f7b987e0f96e9d954a4774bdce5aadc615f91a95ebc3ae2aa00d
canonical-ID/size/payload SHA-256: 2d76bbd95c1d1a64aa7dd783c1fd689de9f55a59057bf13b9d596690dc9049ee
```

Target 376 canonical 1358 is 190,444 bytes with SHA-256
`9696899ce837eee05e727627a2f2f2fd2b8828e90f51ca071dab6ab4fffd6a6f`.
Its 48,930-byte script has SHA-256
`ab4b7d9454a7fe1b41927fe239dbdde364b1fc692b43293bc15eaeb8856aaa4b`.

Historical V158 package-identity facts follow unchanged.

The current V158 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v158.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: 5b2b5aecd15c9aaf4bbcb7a3e555c391a22148f7645fc42fba53d4ad775accd4

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v158.cue
CUE size: 107 bytes
CUE SHA-256: 8f205b83f6e0232a6ea3fdda39027cd4728024b2305cd37a269f3d06b93c2955

manifest: work/mass_driver_v158_stage/manifest.json
manifest size: 249,070 bytes
manifest SHA-256: c01792fae7de6ab3bdcdf214c2b16e30dca7101ebc31a92e45ad021bb56ffe7f
jobs / replacements / bytes: 136 / 169 / 11,804,468
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: ca18e714f9b02f5467ac7bdaf42b2567578088bf987ed84073e31233e2fd7130
canonical-ID/size/payload SHA-256: bed7f0270c73c209920d27eaea389e750b89c878a40a9ce04933af2f0d2b953e
```

Target 728 canonical 2062 is 126,380 bytes with SHA-256
`3ed0527021cc4d09ef8e6297dd335e09f435018dd305299dcf200ae3c8f1210c`;
graphics canonical 2063 remains 180,224 bytes with SHA-256
`201c89767211545e039422ab8791b48ff5a22f3f5383c4d0b234387a3c25aef7`.
Its decoded script is 3,593 bytes with SHA-256
`39f7a1cf08cbe8721ac39fa471a29b69a9e5ca1a944948c88cbd0f6bda73c020`;
entity-13 action PC `0x03F2` is 1,053 bytes with SHA-256
`41e90c56f716d18b670e26e28204a0309be3d811dd4a5e0d651a5bc168cebfdf`.
The appended entity-16 collider at PC `0x0866` is 31 bytes with SHA-256
`5c4d5eb5c599b119653ac90a6746eee799f1dc71a2ff15e5e4f4eafff43e97df`.

Historical V157 package-identity facts follow unchanged.

The current V157 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v157.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: 38ac9a31f62c172541db6361249f58822a3abccc91569a4bed56498c0518edeb

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v157.cue
CUE size: 107 bytes
CUE SHA-256: 91d48c195c99d90130d0244de8eb1688d1a3e86b050b01d663cdccf9e5c7ec34

manifest: work/mass_driver_v157_stage/manifest.json
manifest size: 246,356 bytes
manifest SHA-256: 0a8f9e99a471f7af841a42f5ff22a802dfb4282057bcafb80e3e245a34365345
jobs / replacements / bytes: 136 / 169 / 11,804,928
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: a306ed2adc0bbbaff3538f6c6226b72163ed258ccff9c0d0f37272f8a95726a2
canonical-ID/size/payload SHA-256: e478cae23d8f4260dc02eecc8e7be685220ea94fef022fb571f345dcaba14845
```

Target 728 canonical 2062 is 126,840 bytes with SHA-256
`404c67c39b34f6a62fffde18d20580cab9a60d8ec2f28bbf4880cb056e6c5f46`;
graphics canonical 2063 is 180,224 bytes with SHA-256
`201c89767211545e039422ab8791b48ff5a22f3f5383c4d0b234387a3c25aef7`.
Its decoded script is 3,562 bytes with SHA-256
`889bde3344c78874c8da995a463dc309e97d4bc472a72728516f67cad3535c56`;
entity-13 action PC `0x03F2` is 1,053 bytes with SHA-256
`12cbdceababaaa4bc1ae543eda7860bd2ebf0fd1f2912f17f46a25b45ba1bf19`.
The entity-13 initializer remains 24 bytes with SHA-256
`16495b64a4f39fc843abf026726dddeb615e64412394a78b923100d60a7dcd46`.

Historical V156 package-identity facts follow unchanged.

The current V156 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v156.bin
BIN size: 696,135,552 bytes
BIN raw sectors: 295,976
BIN SHA-256: 9eb4dde57c0ed39ba504d50684b9bb63055812145de2474043e255ff150774a1

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v156.cue
CUE size: 107 bytes
CUE SHA-256: 5a47cbe3465ecdf08a20eaa7ef5deb1029d9581631d145f141bdc4c305d81707

manifest: work/mass_driver_v156_stage/manifest.json
manifest size: 245,085 bytes
manifest SHA-256: ab46ece79e120786f8a18a56972623c5eee8e758a77b55776a4d526520fa95dc
jobs / replacements / bytes: 136 / 169 / 11,807,356
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: d7f8a08343e191a500f8844dfbd4a9b9b950eb1901fcb6bd495ef4b171f666d9
canonical-ID/size/payload SHA-256: 9843b800b8a4039250d8eb0215dd322aede53e27ab0494bcf7ddf5efafd92665
```

Target 728 canonical 2062 is 129,268 bytes with SHA-256
`8f4b0f2672fc61bda95b1a15860b4d4fe5561c3cc438824cbed0003c9671c1c9`.
Its decoded script is 3,562 bytes with SHA-256
`a27db09bedc55d12bc24ab9dac4360c067a802bd12b1dabe89df7e1bb8369aec`;
entity-13 action PC `0x03F2` is 1,053 bytes with SHA-256
`0d0dda5cf756b4225639789186e53d8a36fd65954656966608df16321cf28d51`.
The initializer remains 24 bytes with SHA-256
`16495b64a4f39fc843abf026726dddeb615e64412394a78b923100d60a7dcd46`.

Historical V155 package-identity facts follow unchanged.

The current V155 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v155.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: 0bc82870566778313dbdaba48ba8459ee88cc43a3b8834b22d4457ac688cbf11

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v155.cue
CUE size: 107 bytes
CUE SHA-256: 49a611cdda251c2f030adc8610e00ee7d6cab5a2057e30fb0f91d6e273aaa5ac

manifest: work/mass_driver_v155_stage/manifest.json
manifest size: 241,652 bytes
manifest SHA-256: 5eed39c013a4bb792ccc34bc130c67fb1fb45c27369d2d5bad9f0f511080456a
jobs / replacements / bytes: 136 / 169 / 11,804,404
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: 2a3ab8521aa11c69f1e205749a60d3ed85af88b8802e0910e46a8ab967b9555f
canonical-ID/size/payload SHA-256: 1e8912d367f4eb580f08069f64da7d49a5374c880a19115dd088e48cc2b1ed95
```

Target 728 canonical 2062 is 126,316 bytes with SHA-256
`6d7a84c43d702a79cb0481507fc9d4876a3e74b85b68ee236c0597b4e767a07c`.
Its decoded script is 3,488 bytes with SHA-256
`01e2d0ff14babd2d59b51163c2d01d3a6f1eee2617238f1bc4aa0b1cb0c067f4`;
entity-13 action PC `0x03D5` is 1,008 bytes with SHA-256
`3ccc58171011b9df0e34eb6be2f434845a1fef18753388d030b8bdd5da2e7932`.
The initializer remains 24 bytes with SHA-256
`16495b64a4f39fc843abf026726dddeb615e64412394a78b923100d60a7dcd46`.

Historical V154 release facts follow unchanged.

The current V154 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v154.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: 5db4cbbf892338360f24cda664dc841b5a67f4b183819c205005635bc990fdc3

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v154.cue
CUE size: 107 bytes
CUE SHA-256: e77c607981d6d7b935be42eab90443169cfda1e0caa4bfb6bb71628ff3c8d6f2

manifest: work/mass_driver_v154_stage/manifest.json
manifest size: 239,448 bytes
manifest SHA-256: e0423870efc38045b98356d088fce6633cd918369554af17011e2f26e6e566d5
jobs / replacements / bytes: 136 / 169 / 11,804,396
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: 1d37789cf911ac49a37eef9d9dfae31e2cd74c17d31ebc97d3e6409e9d95fe90
canonical-ID/size/payload SHA-256: 8b9ec311d83f50592c7169877ff3cf7abb0a6664fbca7dabe4cde25aea754022
```

Target 728 canonical 2062 is 126,308 bytes with SHA-256
`70b617b9d9b08c1a40a4b936598992a1a3cea92d648370d1790862af465bcd2c`.
Its decoded script is 3,472 bytes with SHA-256
`a421fed38b3baeebc176cf664470073aa7606449bbdfc61ef3cfb1b4d643f30b`;
entity-13 action PC `0x03DD` is 984 bytes with SHA-256
`dd4b1e686aa36c1f8c8c174d169feec12890d65de4da0b8ceab352bfa9421bbd`.
The initializer remains 24 bytes with SHA-256
`16495b64a4f39fc843abf026726dddeb615e64412394a78b923100d60a7dcd46`.

Historical V153 release facts follow unchanged.

The current V153 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v153.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: d5e50afa2f5288eeab63bf52a55f9d7167bbf48eef7bbead4fb5757dcff52b94

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v153.cue
CUE size: 107 bytes
CUE SHA-256: c01e5dca6c9a3ed6405e7ba7eb3951e973856dbb585c13e0c93397e016070766

manifest: work/mass_driver_v153_stage/manifest.json
manifest size: 238,991 bytes
manifest SHA-256: 5e7ee65fd047484fcb5d378a1991ede34e89f5bdeab2079804df3c980fa8c3e0
jobs / replacements / bytes: 136 / 169 / 11,804,480
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: 479f4359f1f6ff222abf959b176c8dea02ea6be63ba85119c886c71654a4fce5
canonical-ID/size/payload SHA-256: d64931dacb4e7d768d4a2bb3e66f7658cb3eaea4ddf98313eee43367dc9eda0a
```

Target 728 canonical 2062 is 126,392 bytes with SHA-256
`9e5c5be2d6b858fb69375a7019224f2c253b0b7fb6aac955f2cb0d64175bb0c5`.
Its decoded script is 3,435 bytes with SHA-256
`bb34a0a6e652feef3a1f32bc422229a39c518cbef291e1a2eb9a7e8605747a73`;
entity-13 action PC `0x03DD` is 947 bytes with SHA-256
`ac24214ddc755d8e89f92be799a970f943ac2c7b4c1d5bc5bd1d9980e8c58f24`.
The initializer is 24 bytes with SHA-256
`16495b64a4f39fc843abf026726dddeb615e64412394a78b923100d60a7dcd46`.
Authored dialogue, actors, sprites, camera targets, Citan stage/walk, native
door, arrival camera, graphics, and field 617 retain their V152 identities.

Historical V152 release facts follow unchanged.

The current V152 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v152.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: 8dcb5e62607350832af926562a75dbb07b624ece41fd2edb7fee09d8b4b23cf4

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v152.cue
CUE size: 107 bytes
CUE SHA-256: 244144983c6e13c499122cf26eaeed59e62870de92567e0a7b959bd3d3865f65

manifest: work/mass_driver_v152_stage/manifest.json
manifest size: 237,913 bytes
manifest SHA-256: fe7d6b8ecc2bb1af358757090227c2e8d58d7c666c5d88b8e485ec193eff8f41
jobs / replacements / bytes: 136 / 169 / 11,804,532
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: 9542a7978bb3b0793939d305b0e9cc59275b4b81963def02575bc48ebc98683a
canonical-ID/size/payload SHA-256: f1ea7670fa5617d9538e83383c2a0ef9abbdbdfd205c7bc000e8479a57368ea0
```

Target 728 canonical 2062 is 126,444 bytes with SHA-256
`3cb22422077995d06e35097fe943de5e6de9dc658fcbbe15d3c7f94b0e3035f9`.
Its decoded script is 3,482 bytes with SHA-256
`b6e7023c38a03801ae00cd15b326954127330a3da58d5216725e073e142a8eb5`;
entity-13 action PC `0x03DD` is 994 bytes with SHA-256
`3c48e815b5815bdbb6acf1b4afd74b581ed05779a61d538ce4859b54efe1cc23`.
The initializer, stage, walk, dialogue, actors, sprites, targets, Citan route,
native door, arrival camera, graphics, and field-617 payload retain their V151
identities exactly.

Historical V151 package-identity facts follow unchanged.

The current V151 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v151.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: 60cdf6e6ab9292908e7e20e0095da3dd6d34f89ce291d6a185fdbb1f07bf24a7

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v151.cue
CUE size: 107 bytes
CUE SHA-256: 18dd7904fb0b60a40258a1fdf03fa011ed17ad377d7c317d8f728aa060d1e3dc

manifest: work/mass_driver_v151_stage/manifest.json
manifest size: 237,578 bytes
manifest SHA-256: a62687e0bc871410d6dd461e36ff79776d80a9b3b7ee268cc623dac8206775c0
jobs / replacements / bytes: 136 / 169 / 11,804,532
route fields / directed edges: 33 / 66
canonical-order payload SHA-256: 402453c4d884741f653ccaa29620fce59da7ad2bb19c7a7cf9b3db81fbc252c6
canonical-ID/size/payload SHA-256: 4b703993944fc5911a6e41003f714a95ed7ec2a594011b1b2dcf721346854777
```

Target 728 canonical 2062 is 126,444 bytes with SHA-256
`094a504a9b7d51e7f0beefbf83df1729b7f582f8e932589a567ff70bc5fd936d`.
Its decoded script is 3,482 bytes with SHA-256
`f3c72efec276d82deb51dfdf9c18bab27db9207263aeface5cd3c9aeec3e476f`;
entity-13 initializer PC `0x033E` is 24 bytes with SHA-256
`181a80e903ce97b95af8b25c499265262879e1c5c680025446cefef371a92ba1`.
The stage, walk, and finale-action bodies retain their V150 hashes exactly.

Historical V150 package-identity facts follow unchanged.

The current V150 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v150.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: b28288e1a276b1a56dbe07ee9cb610ce85ee45473af1eeae18bb4898afeb915d

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v150.cue
CUE size: 107 bytes
CUE SHA-256: d0c5ecd25396b40d09009bd0b2960e68e9453594fe377b801c096fdc2fd66e4e

manifest: work/mass_driver_v150_stage/manifest.json
manifest size: 237,297 bytes
manifest SHA-256: 2c3585a1a22ca46049597536e40759d00c7708a40756de591a5ac09e37578328
declared replacements: 169 across 136 jobs, totaling 11,804,532 bytes
replacement aggregate SHA-256: 988cd68d882303ceef30d7d8c7d2d45f488424b6fa01dbe6fe702320691afeab
framed aggregate SHA-256: b8d78bb4bc92f1e0e09efe80205712d7d97d96bf0efc5dfb1cbc7263c8a57392

field 728 bundle size: 126,444 bytes
field 728 bundle SHA-256: 74badc327537c6fb5c5ca6c165f87a7c94a15f8de9cad944e402a9312bc65b42
field 728 prepared header: 1,088 bytes / b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31
field 728 packed header: 1,088 bytes / cb5439aaa3b2bd00aa1fb103356f1fd7ff06c1de34c724eea1bed1b4193cd1db
field 728 actors: 18,640 bytes / 2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538
field 728 sprites: 67,668 bytes / e09e0ca20423abd18fbbbee63c37b47e0d89c8a7a1cb32a61d54d37de452b805
field 728 script: 3,482 bytes / 172d20ae35f6d63b247610c245adbdc4f4baa226f746a456f23d748f7099028c
field 728 dialogue: 4,998 bytes / f9b38b8cef89b1b4b212a3eb41fb3d464beea71cdaa35777a33614f2b4f1a948
field 728 entity-13 script-0: PC 033E / 24 bytes / c655d253d88189b3385d8db76d745126ed37b867e90b252a40704526d6979b4a
field 728 entity-13 script-2: PC 03DD / 994 bytes / fb6eae5e3f1645ffe2bf53752215f01370fded4cc44e8b2c953ddd7b2d27a91b
field 728 entity-3 script-21: PC 039F / 15 bytes / 9a5aa669a5e137e3039f0e744cf0da4a926869f388d2e4a270a4140da5561cbc
field 728 entity-3 script-22: PC 03AE / 47 bytes / 00b90ce55c17beb780b028d81a1f61e40b2c955ce58887eba7b9b43f5d58728f
field 728 arrival sequence: 76 bytes / 2462b1808c776a34fce501d091e03bdaeb96f82e46d94a60279693ca3b073427
field 728 arrival camera: 35 bytes / f5d04c00fe5de8f416e95735ff10cd6b211096283983ad66d7809814e5690103
field 728 graphics: 180,224 bytes / 4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28

package acceptance: all 169 replacements re-extracted from the V150 BIN and matched the manifest exactly; 5,846/5,846 replacement sectors and boot passed; declared stage delta is canonical 2062; exhaustive FAT payload delta is 17, 22, and 2062; one descriptor changes only canonical 2062's size; entry kinds and directory memberships are unchanged
full-suite acceptance: authoritative V150 structural run passed 262 tests / 2,681 subtests in 23.044 seconds with exit 0
runtime acceptance: fresh user-driven subjective-memory/native-door/Citan/held-camera/launch replay pending; focused V150 near-finale state available
test launcher: output/TEST_V131_MISSILE.cmd
```

The complete V149 identity block follows as historical evidence and remains
unchanged.

The current V149 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v149.bin
BIN size: 696,130,848 bytes
BIN raw sectors: 295,974
BIN SHA-256: e5125cfcf4b9a876a6b605b0bbac8152ee60476fd989b4824050ca27cb7363de

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v149.cue
CUE size: 107 bytes
CUE SHA-256: 3b8b5e4cbcb0d2ec5e05a83f8ffea424adcd7a740c98b32674c1b8b7d61fb173

manifest: work/mass_driver_v149_stage/manifest.json
manifest size: 237,200 bytes
manifest SHA-256: be30b9fd1974050c52992d98989486ddb17eed95a24986cfd130101ad94aeeb5
declared replacements: 169 across 136 jobs, totaling 11,804,612 bytes
replacement aggregate SHA-256: 86d4d110f86b4d1e6c95f97acd0adc0b9cdb3dcd1ed074035e304f6c007c0768
framed aggregate SHA-256: f7cdc39db4a4cd6b954dee33117995cf29f74df1c0719882bef79a8aaf35162e

field 728 bundle size: 126,524 bytes
field 728 bundle SHA-256: e70ce6317a634b447eb941a87407112306304d3086b89ba8bde0555470f191ea
field 728 prepared header: 1,088 bytes / b459f1b22c429183054fdea438a8c14a423341757efe7849d410a9fa7cc30a31
field 728 packed header: 1,088 bytes / 9512cf649f6834c5cd641684f708bf8d57ae34c48660acaeeb8e57790a082740
field 728 actors: 18,640 bytes / 2bedd56ec86f28662684e72c0ca815ee6b96974d551d0e03e5c543cdf3422538
field 728 sprites: 67,668 bytes / e09e0ca20423abd18fbbbee63c37b47e0d89c8a7a1cb32a61d54d37de452b805
field 728 script: 3,510 bytes / 1aa6dd7fbeb32846a8139e12a57efd3bbc8a5899d2c97c842e8087069f592177
field 728 entity-13 script-0: PC 033E / 24 bytes / c655d253d88189b3385d8db76d745126ed37b867e90b252a40704526d6979b4a
field 728 entity-13 script-2: PC 03CD / 1,038 bytes / c248e21886a1309ba5c3c59d6c9e4d8dfb3b71a8c2827f9470fd041cd9407c86
field 728 entity-3 script-21: PC 039F / 11 bytes / d9358abd4ed27e8dbab0e9b89e7a826b93b648d26acc490d853463595df118f8
field 728 entity-3 script-22: PC 03AA / 35 bytes / 4e9589542aec71a6c446ab3a7c1183ee1cc7ecc55a4dc3616d6bf8fa59cbaa2c
field 728 dialogue: 5,044 bytes / c5300fd84da598f56215c5561feee6932de3f726524b53704cb56fa762503006
field 728 graphics: 180,224 bytes / 4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28

package acceptance: all 169 replacements re-extracted from the V149 BIN and matched the manifest exactly; 5,846/5,846 replacement sectors and boot passed; declared and exhaustive FAT payload delta is exactly canonical 2062; zero FAT descriptors changed
full-suite acceptance: authoritative V149 run passed 262 tests / 2,681 subtests in 20.918 seconds with exit 0
runtime acceptance: fresh user-driven centered-panel/chest-retirement/Citan-arrival replay pending; focused V149 near-finale state available
test launcher: output/TEST_V131_MISSILE.cmd
```

The complete V148 identity block remains frozen in the V148 release-validation
section below.

The historical V147 frozen package has these identities:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v147.bin
BIN size: 696,387,216 bytes
BIN raw sectors: 296,083
BIN SHA-256: 63fd1ceafee04c0346acddb27a9df0724f07e5587de608e6c6dc56cfb4eb0881

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v147.cue
CUE size: 107 bytes
CUE SHA-256: 6e00bd12d06042f3bf3d8a983d6d44b6241763287767c6773ff14ad5aaba4f55

manifest: work/mass_driver_v147_stage/manifest.json
manifest size: 242,543 bytes
manifest SHA-256: 0d6f9cc688916817f267d4fc0c656e6cb0f85583f0af3abf4e2b962370a795b0
declared replacements: 173 across 138 jobs, totaling 12,034,636 bytes
replacement aggregate SHA-256: 92bf2aec3d943a096359f09e88e0ce76e0d96ea0a8a6f7f88fc5b361c6ff7096
framed aggregate SHA-256: 139b1dc35af938680ab4012a620c31bf7e80dbaf010918b9394cec9ab2c8af40

canonical 29 size: 13,596 bytes
canonical 29 SHA-256: b2feb89ac7031b5007aa137e2711ca0ab2f5b48efbe0d55ee040f98f81192816

field 507 donor: retail Disc 1 field 573 / physical files 1752 and 1753
field 507 bundle size: 68,540 bytes
field 507 bundle SHA-256: 5a292fd2df08bff7af3bcb3c243748bb9f92a18ad2e469a4931d64b1b4364c97
field 507 prepared header: 672 bytes / e49f9573e08e6b8d475bf9185dd79e843fad1ba75ef1f9c5e5fa60440846ed9d
field 507 packed header: 672 bytes / 84f3ac2103a741855ce4f6dbc0c35e5c09935e84f0dd32f5196bdb0c9a1b8ec5
field 507 script size: 2,405 bytes
field 507 script bytecode: 1,569 bytes / 11 entities
field 507 script SHA-256: 7e089ce88febe68ffa51709476a9e2eb4f0ab9cbb36baf9e21b6227b569dd51a
field 507 graphics size: 141,312 bytes
field 507 graphics SHA-256: c253c815b126a9527851057d9279b9646fed0ea982fde359d389020178f9d9d6

field 728 bundle size: 46,952 bytes
field 728 bundle SHA-256: 6dc4ae2b720b81ff3afc224e3471bab591235fd269c6f8f505dcebad758926c3
field 728 script size: 2,233 bytes
field 728 script SHA-256: 9d13d94f49bddfcbd4f1ce458737655ea3a1afe9260d52420ff21fadc26d0772
field 728 graphics size: 180,224 bytes
field 728 graphics SHA-256: 4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28

field 363 bundle size: 21,352 bytes
field 363 bundle SHA-256: bc450a6117ebd3e4dc60eb6bc0a39c4175ebac77dbbcf193c384dd9829937c3b
field 363 prepared header SHA-256: c5dd92f8b149eee4e8287b622d0cd70c730c82eb796115dc0642464d2df6a182
field 363 models SHA-256: b756da8c20274bf8a6c3c136eafe63c73a830566b0c9aaefb56c5bf7db4f9d20
field 363 script SHA-256: 1d11ad410628d1d7e1e64a5885144f8529171188cb6e626bafcc2e79af688f30
field 363 graphics SHA-256: 0f90479813717a6aa250691ec85f02b2c3fb009aed9adbab003212a80bda2561

field 376 bundle size: 190,452 bytes
field 376 bundle SHA-256: db9395c7d3e11b73d98014236744ac3bc090d4b82d357a9af289c14cf79ded7f
field 376 prepared header SHA-256: 5a1f9906041cea5aa585088bb3c8517f9033f767adf4bb81f2154dd31f2c31fd
field 376 packed header SHA-256: 8ec2ab8905031e890a34a70f5f204fd474916c33117b2801fbede1278d441738
field 376 script size: 48,937 bytes (47,013-byte bytecode)
field 376 script SHA-256: f3c08c932d04de87ac6dc8afb0e754193a8899d17ce6aaffd4c2f31479c75257
field 376 dialogue size: 7,200 bytes
field 376 dialogue SHA-256: 3eadb9b8fafc2b1fa36c8325a604aac6d8e91e519ad317a2d4bc42988b92289d
shared arcade atlas TIM size: 8,212 bytes
shared arcade atlas TIM SHA-256: 3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d
package acceptance: all 173 replacements re-extracted from the v147 BIN and matched the manifest exactly; 5,959/5,959 replacement sectors and boot passed; the exhaustive FAT payload delta is exactly canonicals 17, 22, 1620, and 1621
full-suite acceptance: authoritative V147 run passed 262 tests / 3,326 subtests in 43.82 seconds with exit 0
runtime acceptance: fresh user-driven v147 compact-room entrance/controller/dialogue/panel-beat/launch/return replay pending; prior runtime evidence is historical
test launcher: output/TEST_V131_MISSILE.cmd
```

Historical V117 adds `screenshotz/7.png` as the first visible report on target 376's
ordinary `Video Disk`. An unauthorized FZN signal from correspondent Jonas Vale
warns that the government is destroying the country and calls for the people to
revolt. The recording then resumes the existing six ZBC reports anchored by
Celia Ren, in their unchanged `screenshotz/1.png` through `screenshotz/6.png`
order. The new playback selector order is `0x09, 0x03` through `0x08`.

V117 retains v116's item-109 award, `0x37` acquisition chime, explicit receipt,
inventory-full retry, damaged-disk repeat line, insert/cancel choice, modal
caption timing, retail Lighthouse projector sound `0xF9`, and cleanup frame
`0x48`. The new 143,380-byte TIM occupies canonical 2474; the six established
TIMs in canonicals 2468 through 2473 remain byte-identical.

The packaged 696,979,920-byte / 296,335-sector v117 BIN has SHA-256
`56b0310986d95c7cebe574b34978c1d484c26270bb04181eec69b2e29592fbe2`.
The structural package audit extracted all 173 declared replacements exactly.
Relative to v116, canonical 1358 changes and canonical 2474 is added; every
other declared payload is byte-identical. A state captured with target 376
resident must fully leave and re-enter the room from v117 media before testing.
See [the v117 signal-override notes](docs/mass-driver-dungeon-2.93.md).

Historical V116 turned the video-disk prop into real ordinary item 109,
refreshed the six ZBC stills, and kept every still visible until its caption was
advanced. Its 696,899,952-byte BIN has SHA-256
`c0c13b0feb157bc90b839bd8eb0c969b552e5a5a627bb3344c07a9c51da3ce0c`;
all 172 packaged replacements extracted exactly. See
[the v116 inventory-video notes](docs/mass-driver-dungeon-2.92.md).

Historical V115 introduced the optional six-frame Defense Archive recording,
aligned its visible console frontages, and added canonical TIM resources 2468
through 2473. Its 696,899,952-byte BIN has SHA-256
`15bf08dcf0bd3ed1b50b310b0af24aa20baf3cbba63a95b0dc1e675fcee1560d`;
all 172 packaged replacements extracted exactly. Its disk was represented only
by persistent field state rather than a normal inventory entry. See
[the v115 video-disk notes](docs/mass-driver-dungeon-2.91.md).

Historical V114 separated target 727's personnel-station collision from its Cross/X
frontage. Invisible entity 18 remains an immovable `0x1C` solid at
`(-147, -42)` but is interaction-disabled; new non-solid entity 19 sits at the
positive-X controls at `(-108, -42)`, requires the player to face them, and
uses compact `0x04` reach for repeatable dialogue 4. The captured intended
stance is `(-88.55, -42.18)`, while side approaches are outside the reader.
The packaged 696,431,904-byte v114 BIN has SHA-256
`b0a8c915256c62a3cdb362ccb4dbbb5557fd9cb442f27b54e7ed64204c325570`;
all 166 packaged replacements extracted exactly, and only canonical 2060
differs from v113. Live front/side acceptance is pending after a target-727
exit and re-entry. See [the v114 frontage notes](docs/mass-driver-dungeon-2.90.md).

V113 gives all seven transplanted field-373 Zeboim computer stations native,
invisible, immovable collision: the subway station in target 721, the new
personnel time-clock in target 727, and the reserve-magazine stations in
targets 377, 378, 379, 382, and 383. Their existing Cross/X interactions remain
repeatable, while target 727's new notice tells personnel to clock in and out,
report suspicious activity, and stay current with safety protocols. The
packaged 696,431,904-byte BIN has SHA-256
`870f65f30c39f977a14dbe5837bb95108d1a7d6989f80259ef3da78f9c1f0aa5`;
all 166 staged replacements extracted from it exactly. A fresh target-727
reload confirmed side collision, while also revealing that its combined
centered actor allowed X interaction from a side; v114 supersedes that narrow
frontage behavior. See [the v113 station-collision notes](docs/mass-driver-dungeon-2.89.md).

Historical V111 replaced the dungeon's former last-room presentation with retail field
595's later playable version of Krelian's private laboratory—the white chamber
with the staircase, circular apparatus, and built-in desk terminal. The route
still crosses target 388's red Zeboim pressure tunnel into logical target 507,
but Elly, Emeralda, and final-only noncombat Citan now enter the transplanted
private lab at `(434, -30)`. Pressing Cross/X in front of the native desk
terminal at `(0, 450)` runs the final dialogue, stages the complete native
two-step apparatus sequence, and launches Taura's capsule. The tunnel performs
the visible door animation; the laboratory's matching east panel is already in
its open wall position and a quiet threshold returns the party for backtracking.

Historical V110, retained by v111, kept Elly and Emeralda as the complete playable party
from the world-map approach through the entire dungeon and Guardian battle.
Citan never mounts Fenrir or participates in an encounter. Central Control
target 728 owns Elly's warm-filtered first-person memory and Citan's final
arrival; the capsule itself is launched only in the laboratory after the red
tunnel.

Historical V110 aligned every interaction in target 376's Defense Archive without moving
any visible console or changing action ownership. Authorization entity 13
remains at `(175, 123)` with its facing gate, while it and record entities
20-25 use operand `0x04`, giving 24-unit effective reach. North-lift entity 17
remains at `(0, 245)` with operand `0x18`, giving 64-unit effective reach. The
retired empty-aisle stance `(-30, 141)` is silent, and a fresh v110 field reload
also produced no dialogue when Cross was pressed near `(-11.93, 127.34)` on
walkmesh triangle 70.

V109, retained by v110, replaces archive relay H-10 inside target 721's stationary subway train
with field 373's authentic model-7 Zeboim freestanding station. The station
keeps entity 14's repeatable Cross/X mail interaction and awards no item, while
Repair Bot M-07 remains outside with its complete Item and Gear-parts shops.
The static model reuses H-10's registered bank-1 texture allocation, and the
full retail palette occupies a freed native MIM row; no graphics upload is
appended or resized. Its final static-node position is `(-1011, 18, 225)` at
yaw `0x0E00`; the visual centre `(-1025, -164, 185)` aligns exactly with the
retired H-10/controller point. Its final world bounds are
`(-1065, -986, -240, -88, 146, 224)`, avoiding the donor-pivot occlusion found
during live validation.

Historical v108 installed the selected option B terminal in every reserve
magazine: field 373's authentic model-7 Zeboim freestanding station. It is
lowered to the floor, turned toward the existing east-side Cross/X controller,
and retains its
exact retail model, sampled texture pixels, full palette, screen, and status
lights. V107 appended otherwise valid texture and palette uploads outside field
673's registered native runtime allocations, so the live allocator did not
retain them. V108 losslessly repacks the station's 21 used 8bpp islands into
the exact native fourth upload at `(512, 192, 40, 64)` and puts the donor's
full palette on native row 488. The graphics stream remains exactly four
uploads and 102,400 bytes; the five rooms' backgrounds, warheads, walkmesh,
mail, and silent-entry behavior remain unchanged.

V106 also introduced both visible Defense Archive progression changes. Accepting
Directive `0320` and all four authority points cuts to the north lift, plays
its native machinery sound, and slides both native-textured leaves open. After
the Guardian battle, the nearby west-bank record/control panel at entity 23 is
the only control that opens the west bulkhead. V106's action used a fixed camera;
the current build removes only that cut, keeping the live field camera while it
plays the same native sound, opens both leaves, and records the open state for
later visits. V160 gives the panel a shallow no-facing `80x24`
selection rectangle across its complete walkable front. Pressing X on the bulkhead itself only traverses it
after that panel operation.

Historical v105 separated Central Control's optional archive reader from its
then-required launch console. Entity 12 keeps the east archive frontage at
`(57, 71)`, while entity 13 moved from its hidden `(-154, 125)` pivot to the
captured console stance at `(-54, 94)`. Both use proximity-only `0x08`
controllers with 32 units of effective reach. Their X regions are disjoint
from one another and from entity 14's native east-door region at `(181, 88)`,
so the archive mail, staged memory/final-route sequence, and door cannot
intercept one another in v106.

V104 corrected the small gray archive panel in target 726. The exact
screenshot-era v103 `.bak` runtime state places Elly at
`(-605.793, 495.069)`, immediately in front of entity 20's controller at
`(-605, 474)` and its visible entity-27 helper at `(-661, 446)`. That route is
`726:e20 -> 367:p0`, not entity 22's separate corridor. Elly was already inside
the existing proximity box, but aiming at the visibly offset panel missed the
hidden controller pivot's facing cone. V104 removed the facing requirement only
from entity 20. Its standard proximity check, native door animation,
destination, and artwork are unchanged.

V103 corrects Citan's final Central Control entrance. V102 cut abruptly to a
rear camera, showed mostly the back of his head, then attempted a direct walk
across an unwalkable console notch to an off-walkmesh endpoint. That failed
route ended in a visible position snap beside Elly. The arrival camera now
holds a readable full-body profile throughout the door animation and three
verified walkmesh legs. Citan reaches the dialogue point without a visible
teleport, faces Elly, and the same fixed-camera mode pans into the conversation
without a second abrupt cut.

V102 corrects the people and staging in Central Control's Zeboim-era memory.
The Launch Director is now an adult blonde officer in a white command uniform,
and the Systems Officer is an adult helmeted bridge operator; both use native
field-366 actors instead of the childlike field-369 mascot actors. Miang keeps
her exact retail field-364 actor. All three apparitions remain at their console
stations, and runtime `FE 17` actor-to-actor turns aim them directly toward the
person involved before every spoken line. Miang faces the Director throughout
their exchange, the Director and
Systems Officer face one another during their exchange, and the camera gives
each historical line its own first-person beat. Miang's final reassurance is
separated from the Director's order so both facing and camera staging remain
clear through the end of the vision.

V101 replaces the five reserve magazines' cross-field Materials Storage
computers with a three-piece lower service pedestal assembled entirely from
each room's own field-673 cloning-apparatus models. The pedestal retains the
room's native render layers, texture pixels, palette, and VRAM layout: no
foreign model, texture page, palette, or additional VRAM upload remains. The
existing entity-7 Cross/X interaction and all five exposition records are
unchanged.

V100 made every physical console bank in the Defense Archive meaningful.
The northeast bank remains the dedicated Directive 0320 and ABCD
authorization station. Each of the other six native desk-console banks now
opens a different optional, repeatable record: Zeboim's national crisis,
military procurement begun before civil review, the public "shared use" cover
story, nuclear outcome models, Directive 0320's release-unless-recalled
revision, and Miang's unsigned influence over executive routing. These are
deliberate X interactions only; none opens on entry or writes progression.

V99 gives mounted El-Regulus distinct non-world-map field motion. Canonical
453 now maps its intact retail controller onto authentic upright idle art,
feet-anchored crouch art, and forward-driving travel/airborne art. The existing
six-phase walk, three-stage jump, and four-phase run cadence now reads visibly
after the Guardian battle instead of sliding the same upright canvas through
every state. The post-battle exchange says that the party will leave both
Gears in the lower bay until after the capsule reaches the upper atmosphere.
The human-sized south lift still dismounts both pilots safely, but no longer
displays the mistaken player instruction about proceeding on foot.

V99 preserves v98's native target-facing restoration and command-menu idle.
V98 preserved v97's native target-facing restoration and fixed the remaining
static opening pose. V97's animation 0 reached the correct direction, selected
El-Regulus's default keyframe 1, cleared the delayed loader-completion flag, and
then terminated. The Gear therefore faced correctly but did not begin moving
until its first attack returned through a separate recovery path. V98 extends
that tail from `10 FF 21 00 6D 00 00 00` to
`10 FF 21 00 6D 00 11 FF 00 01 00 00`: the retained `10 FF` selects the
default keyframe, `21 00 6D 00` preserves the delayed completion handshake,
and the added `11 FF 00 01` arms the same native 30-tick keyframe-1 idle loop
used by animation 1 and post-attack recovery. At the initial command menu,
El-Regulus now both faces its slot-center target and idles before any attack.
Only canonical 2960 animation 0 changed from v97 to v98; battle overlay 38, the
model and sound container, attacks, deathblows, Crescens, and enemies remain
unchanged in v99.

### Historical v97 native-facing restoration

V97 restored El-Regulus's native battle-entry facing sequence. The v96-only
aligned `62 20 00 00 00 00 00 F8 00 00` packet applied a blanket signed
`-0x0800` turn to Gear 10. A fresh state from the nearby Dragon encounter proves
that packet executed but rotated the opening pose from formation yaw `0x0000`
to `0x0800`, while both the slot-center target and Dragon were due west at the
correct yaw `0x0400`. Attacking then restored normal target-facing. V97 returned
animation 0 to retail `60 00 43 00`: opcode `60` obtains the formation's native
slot-center target and opcode `43` faces it. All 17 retail playable Gears use
that same entry behavior. Canonical battle overlay 38 remains exact retail;
Crescens, enemies, El-Regulus's model, attacks, and deathblows are unchanged.

### Historical v96 opening-facing regression

V96 was a Guardian-specific workaround, not a general facing correction. The
preserved Guardian evidence had El-Regulus at yaw `0x0C00` with its slot-center
target coincident with its root, so native `43 00` received a zero vector. The
replacement relative half-turn mapped that one captured yaw to `0x0400`, but
it ignored formation-dependent starting yaw. The exact captured v96 state,
SHA-256
`3db10c4b78708120964806ed18a46a29c5f99da74dd21a7be283c5a9ae7e4de6`,
mounts the v96 CUE and shows the regression in a new Dragon battle: El-Regulus
is at `(4020, 0, 3640)`, its slot-center target is `(3580, 0, 3640)`, the Dragon
is at `(3140, 0, 3640)`, and the executed packet leaves root yaw `0x0800`
instead of due-west `0x0400`. V96 must not be used to validate opening facing.

Historical v94 replaced the visually mismatched handmade train terminal with
archive relay H-10, a compact native Harquebus mechanical actor from the retail
Goliath Factory. H-10 has its own actor and sprite bank, is visibly distinct
from Repair Bot M-07, and preserves the same repeatable 6072 space-program mail
without awarding an item. The retail subway header and model archive are
restored exactly: no added static terminal model or header node remains. V109
supersedes that presentation with the authentic static Zeboim station while
retaining the record and M-07 vendor interaction.

V93's retained correction fixes the subway return loop. The service-junction
stairs still return to target 721 parameter 1, but that receiving point is now
`(-1250, -218)` on the
same connected subway platform walkmesh. The former `(-1334, -218)` point was
inside entity 13's expanded automatic-exit volume and immediately sent the
party back upstairs. The new point is 61 units beyond that exit edge, so the
party remains in the subway and can walk away normally.

V85 also corrects El-Regulus's fixed-cell initial-GameState name. The old
record stored `0x13` as its third glyph; the loader remapped that value to the
runtime digit `3`, producing `El3Regulus` in the Repair Bot's Gear-items
screen. The record now stores the retail fixed-cell hyphen `0x1A`, which the
loader maps to the runtime hyphen and displays as `El-Regulus`.

V77 repaired the actual root of El-Regulus's Attack Level 1 cap, and v110
preserves that exact working state. Elly's battle
command loadout is `m56 = 1`, so the engine derives her Gear Attack-Level
maximum from the third ability halfword at initial GameState offset `0x16E4`.
V76 left that word at `0x1808`, which genuinely capped El-Regulus at Level 1;
the adjacent `0x16E0 = 0xFC00` word belongs to the on-foot ability set and does
not control this loadout. The build writes `0x1FF8`: Level-1/2/3 masks `0x1C00`,
`0x0380`, and `0x0070`, plus Infinity bit `0x0008`. The correct retail
Attack-Level-Max accessories `0x60/0x61/0x62` remain equipped.

V76 corrected El-Regulus's remaining offensive-motion mistakes, and v110
retains those changes byte-for-byte. Beat Storm
now chains the confirmed `0x40` and `0x41` attacks before its single damage
event. Every Level-2, Level-3, and Infinity physical prelude is restricted to
confirmed offensive clips `0x40` through `0x42`; none invokes `0x45`, the
observed collapse/defeat motion. Clip `0x43` is the separate ducking/down
motion and is likewise absent from those preludes. Clip `0x44` is a valid
beam charge/firing pose, so it remains deliberately present inside native
beam finishers.

The DuckStation state captured at 14:50 on July 31, 2026 cannot test this
release. Its state header mounts the historical v73 CUE, and its saved Gear 10
record still contains the retired `5A 5B 5C` Frame HP loadout. Loading an F1
state restores its old mounted media and resident gameplay RAM. Ordinary
in-game saves also preserve the old `0x16E4` ability word. Selecting a newer
CUE first does not upgrade either one. Fully quit DuckStation, cold-boot the
v117 CUE, choose New Game, and do not load any older F1 state or in-game save.

The newer DuckStation state captured at 07:23 on August 1 mounts v83 and shows
Elly at the unintended south floor point with the Guidance Archive mail open.
It documents the oversized v83 interaction bound, but loading it restores the
resident v83 field script. It cannot validate v84's corrected bound until the
room is left and re-entered from v84, and it cannot validate v117's current
field scripts, GameState name, train-terminal presentation, or Central Control
cutscene. A fully quit v117 cold boot and New Game
remains the clean acceptance path.

The 08:01 August 1 capture directly confirms the object-role bug: it mounts
v84, opens Guidance Archive mail from entity 12 at the left floor console, and
leaves hanging-screen entity 16 dormant. Its resident target-361 script is
byte-identical to v85, so this is not a stale-state explanation for the v85
behavior. It is, however, too old to validate v117; leave and re-enter the room
from v117 media or use the full cold-boot path.

The latest Auxiliary-room capture mounts v86 and proves why its intended remap
was still unusable: entity 16 at `(-40, 97)` activates in an empty aisle rather
than at the visible hanging computer. That resident v86 field script cannot
validate v117. Reload target 361 from v117 media, or use the clean cold-boot New
Game path, before testing the corrected hotspot retained from v87.

The currently open exact snapshot mounts v87 with target 368 resident. Elly is
at `(-124.075394, -24.551453)` on walkmesh triangle 16, directly beneath the
visible beige/orange overhead-arm computer, but X opens nothing because v87's
entity 14 remains at `(-89, 90)`, a z delta of `114.551453`. That resident v87
field script cannot validate v117. Cold-boot v117 or reload the room from v117
media before testing any corrected source-378 hanging terminal.

V74 corrected one contributor to El-Regulus's reported Attack Level 1 cap but
did not complete the runtime repair. The bootstrap had
mistakenly equipped item IDs `0x5A/0x5B/0x5C`, which retail data identifies as
Frame HP10/30/50. It now equips the actual `Atk Lv1/2/3 Max` accessories at
`0x60/0x61/0x62`; however, v76 still left the loadout-selected ability word at
`0x1808`, so accessories alone did not lift the Level-1 cap. The retained `0x1FF8`
word completes that repair. All three Infinity attacks
combine model-local melee motions with El-Regulus's native blue ether beam at
the common retail Omnigear `50/55/60` power and `10/20/30` fuel curve.

V75 repairs both created doors in the Defense Archive. The north lower-access
lift now replaces the exact donor wall panel with matching native texture,
opens sideways over a dark behind-wall reveal, and uses a bounded 24-frame
animation. The west bulkhead likewise uses the donor aperture's own weathered
surface instead of conspicuous added trim, and its paired leaves now animate
reliably before the party crosses.

V89 removed the shared-overlay cause of El-Regulus's backwards combat
presentation. The live v88 battle capture shows El-Regulus in player slot 0
with root yaw `0x0C00` while its Guardian target is due west, whose native
target-derived yaw is `0x0400`. The v78-v88 slot-zero branch added the erroneous
`0x0800` half-turn. V89 removes that override and restores canonical battle
overlay 38 to the exact retail packed and decoded bytes, so all combatants
retain the engine's native target-facing calculation. Crescens, the Guardian,
every other combatant, and canonical 2960's models, animations, and deathblows
were unchanged by that historical correction. V99 retains the retail overlay
and v97's restoration of El-Regulus's model-local animation 0 to the native
`60 00 43 00` slot-center facing sequence after v96's invalid relative-turn
experiment. It then keeps animation 0 alive with the native keyframe-1 idle
loop described above. The
field-scale Gear slot still uses the authentic field-657 El-Regulus art, so
the parked and mounted Gear in the factory hall is not Vierge.

V80 consolidates the factory encounter shown in the July 31 save-state
thumbnail. El-Regulus and Crescens move from a 732-unit spread to safe,
connected walkmesh anchors at `(-200,-2035)` and `(200,-2035)`. Crossing the
centered `z=-2100` approach line now runs one automatic sequence: both pilots
board, the Guardian warning plays, and combat starts immediately. After
victory, one checked same-field rebuild restores both mounted field actors for
the return to the human-sized lift.

The authorization terminal remains separate from the Guardian encounter.
Entering Directive `0320` and authority points `A-2`, `B-5`, `C-8`, and `D-4`
ends at the console and unlocks the north lift. It leads directly to target
384, a large Goliath Factory hall cloned from retail field 260. Elly and
Emeralda arrive on foot beside El-Regulus and Crescens, now parked together on
the central aisle. Walking up to the adjacent Gears starts one scene that
has Elly recognize, `So... Citan left our Gears here for us.` Citan remains
offscreen and is not created as an actor or battle slot. The scene then boards
both pilots, identifies the surviving defense robot, and immediately starts
the two-Gear battle. Victory rebuilds the same hall with both pilots
visibly mounted. The far factory door remains
visible but reports that its bulkhead is offline. Backtracking to the
human-sized south lift dismounts both pilots and returns them to target 376 on
foot, where the west bulkhead continues the dungeon.

The current build replaces the isolated room behind the formerly dead hub
panel with a native source-377 Zeboim operations junction at target 367. Entry
parameter 0 places the party at `[0, 134, 0, 4, 4]`. Entity 12 and native door
helper 15 return to target 726 parameter 4; entities 13 and 14, with native
helpers 16 and 17, open two optional branches into targets 385 and 386. Both
branches are dead-end source-374 Materials Storage rooms, so their architecture
and props match the surrounding Zeboim technology. Each contains repeatable
archive mail on its native computer and a separate native animated chest that
awards one Omegasol. The chests persist independently on bits 0 and 1 of
`0x03FA`; neither terminal changes story progression.

V88 preserves v69's split Archive Console D roles while correcting the visible
computer's interaction geometry. Entity 13 remains the main rail desk at
`(45, -42)`, with no-facing bound `0x1E` and 76-unit reach: it presents only
accelerator-interlock dialogue 0 and remains the sole writer of the rail-power
bit that satisfies the Central Gate condition. Entity 14 now controls the
actual beige/orange overhead-arm computer at `(-124, -25)`, beneath the donor
room's header node 25/model 4 at yaw `0x0600`. Its tight no-facing bound `0x08`
provides 32-unit reach, presents only dialogue 1 containing Aron's saved 6081
mail to Lena, and never restores the rail or writes a progression bit. The
desk and hanging interaction zones retain a 61-unit x gap.

V87 corrects the auxiliary-room interaction geometry demonstrated by the
latest August 1 runtime capture. In target 361, entities 12 at `(-31, 165)`
and 13 at `(110, 117)` remain on the left and right sections of the
floor-mounted Auxiliary Grid bank. Either section operates the same switch,
plays the same feedback sound, and displays only bypass/status dialogue 1.
Entity 16 alone presents Guidance Archive dialogue 0, including Directive
0320 and the room's maintenance and political mail. Its no-facing `0x08`
controller is now at `(-31, -105)` on walkmesh triangle 26, directly below the
beige, green-lit overhead-arm computer identified as header node 44/model 7 at
yaw `0x0200`. The captured approach at `(-30.75, -104.82)` lies strictly
inside that triangle and within the 32-unit interaction reach. The archive
zone remains separate from both floor switches: its gap from the left zone is
206 units on z, and its gaps from the right zone are 33 units on x and 114 on
z. V86 had correctly separated the switch and archive scripts but mistakenly
identified node 27/model 2 and placed entity 16 at `(-40, 97)`, in an empty
aisle; v81-v85 had instead put the archive interaction on the left floor
console.

All six active source-378 layouts at targets 366, 368, 369, 370, 371, and 724
use the same actual beige/orange overhead-arm computer: header node 25/model 4
at yaw `0x0600`. V88 moves each hanging entity 14 from v87's invisible
`(-89, 90)` hotspot to `(-124, -25)` and tightens it from no-facing bound
`0x1E`/76-unit reach to bound `0x08`/32-unit reach. In the five lore-only
annexes, the desk station remains entity 13 at `(45, -42)` with dialogue 1,
while hanging entity 14 presents separate dialogue 0; neither writes a
progression bit. Target 368 uses the Railway-specific dialogue roles described
above. Every desk stays at `(45, -42)` with bound `0x1E` and 76-unit reach, and
each desk/hanging pair has a 61-unit x gap. The new target-367 junction carries
no exposition prop of its own; its mail remains on the visible native computers
inside targets 385 and 386.

The Railway and Auxiliary rooms are deliberate switch exceptions. In target
368, the desk station operates the accelerator rail while its hanging rear
computer carries Archive Mail Terminal D. In target 361, both floor-console
sections operate the Auxiliary Grid while the beige, green-lit overhead-arm
computer carries Directive 0320 and the room's mail. Targets 385 and 386 each
have one native archive computer and a separate Omegasol chest; target 722 has
the same clear terminal/chest role separation; target 376's wall console
contains authorization and status only; and Central Control entity 12 carries
only Elly's repeatable, state-neutral observation that the relocated console
looks out of place among the other computer terminals, separately from entity
13's required continuous finale. Entity
13 owns Elly's subjective memory on the single X press, then automatically
continues into Citan's arrival, all finale dialogue, and the local capsule
launch.

In each paired lore annex, the desk and hanging-terminal controllers are both
positioned in reachable player space. Target 722's combined Materials Storage
computer, its native one-time Omegasol chest, the two additional native annex
chests, and the sole gold memory-cube Save point retain distinct roles; no chest
carries exposition.

Version 73 moves Reserve Magazine 02's expanded record off the automatic
entry path and onto a distinct archive console midway along the east side of
the room. Entering or crossing target 378 is now silent. Facing the console
and pressing X presents the complete record, which can be reread without a
progression flag: the existing 6083 launch log first, then six archived 6079
mail pages about civil funding cuts, Strategic Command's demand for the
accelerator and every payload, the Prime Minister's Adviser's `shared use`
language, and Mara's explicit nuclear-warhead manifest.

V90 applied that opt-in presentation consistently to all five reserve
magazines. V91 replaced the superseded texture-free prop with the exact
two-part retail field-374 Materials Storage hooded facility computer. Its
original model geometry and native textures appeared in every magazine through
v100. V101 removes that cross-field transplant and instead reassembles the
three-piece lower service pedestal from each room's own field-673 cloning
apparatus. Its native models, render-layer flags, textures, palette, and VRAM
layout already belong to the room, so no foreign texture or palette upload can
clash with the silo background. Targets 377, 378, 379, 382, and 383 remain
silent from either direction.
Entity 7's controller remains at `(420, 0)`; its facing-required `0x28`
half-width accepts Cross/X and presents the room's existing dialogue block 0
repeatably without writing a progression flag. Automatic north/south passage
boundaries, every warhead, their supports and collision, and all five
exposition records remain unchanged.

It also preserves v64's maintenance-robot text-window repair and Elly's
one-time observation that M-07 is still operational. It otherwise retains
v63's natural, character-specific script from the entrance through the retail
launch handoff. Dated mail follows guidance engineer Lena, her daughter Mira,
systems engineer Aron, and payload-safety officer Mara from hopeful survey
launches, through Miang's political pressure and military conversion, to
Zeboim's nuclear destruction. The same facility is finally used to carry
Taura's nanomachines into the upper atmosphere.

The Defense Archive retains a paired recessed bulkhead whose two native wall
halves slide apart over a dark reveal. The leaves use bounded world-position
animation, avoiding the primitive-buffer stall seen in the first v60 candidate.

The natural arrival from the Central Gate into the Defense Archive remains
preserved. Elly and Emeralda cross field 394's east service-stair
threshold and remain at its inward-facing receiving point; no automatic scene
moves them into a mid-room tableau. No Citan actor or party slot is initialized
there. The genuine wall terminal supplies all authorization context needed by
the two-character party. It asks for Directive `0320` first, then
for `A-2`, `B-5`, `C-8`, and `D-4` one at a time. It sets launch authorization
only after all five entries are correct. Wrong answers remain retryable.

The accepted code keeps the live Defense Archive camera, plays the north-wall
lift's native sound, and visibly opens both leaves rather than starting combat
at the terminal. The authorization bit keeps those leaves open on later
room loads. The lift enters target 384's genuine Goliath
Factory access hall with Elly and Emeralda on foot and both Gears visibly
parked side by side. Walking up the central aisle starts one combined boarding
and defense scene; El-Regulus and Crescens then fight one mechanical
Guardian. Citan and Fenrir are absent from the scene, formation, and
post-battle party. A single visual rebuild keeps both pilots mounted in target
384. The north door is an offline dead end; the south personnel lift dismounts
the party and returns them to target 376. Victory enables the nearby entity-23
record/control panel, not the bulkhead itself. Using that panel shows the west
door under a fixed camera, plays its native sound, opens both leaves, and saves
their open state. The door then becomes the passage into route
`377 <-> 378 <-> 379 <-> 382 <-> 383 <-> 728`. The five intervening
reserve magazines adapt retail field 673's Cloning Chamber geometry after
removing its story actors, story scripts, and six glass-vat placements from
each room. Each magazine instead carries six original, detailed PS1-style
vertical warheads, for 30 visible warheads total. Every warhead rests on a
floor-contact plinth and four support feet and has an immovable 72-unit
collision volume. The full-width north and south boundaries activate
automatically on proximity; internal boundaries do not require X or another
button. All five rooms enter silently in both directions. Each one places its
existing exposition on the authentic field-373 model-7 Zeboim freestanding
station along the east side. The station is lowered to the floor and faces the
retained controller; face its controls and press Cross/X to read or reread
dialogue block 0.
No terminal writes story state, and target 378's established interaction
behavior is unchanged.

Central Control is the active route's final room. Entity 13 requires the
established authorization bit and owns the complete continuous finale at
`(-48,97)` on walkmesh triangle 16. Its no-facing OP18 X/Z operands `0x1C/0x02`
give an effective `72x20` shallow strip covering X `[-120,24]`, Z `[77,117]`.
It accepts the captured engine stance `(-113,113)`, triangle 15, the older
`(-15,113)` stance, and both F2 readings. Entity 12's optional Elly-only
observation controller now shares the compact standing keypad at `(136,131)`,
triangle 26. Its no-facing
OP18 `0x01/0x01` gives raw extent 2 and effective `18x18` reach over X
`[118,154]`, Z `[113,149]`, leaving a 94-unit X gap from entity 13 and a one-unit
X gap from entity 14's east-door region.
Prepared header node 29/model 5 is the visible control-panel bank; all 32 native
entity-16 treasure scripts remain retired. Its appended script 0 is instead an
immovable, interaction-disabled solid body at `(154,171)`, triangle 24.

The Cross/X interaction presents Elly's subjective Zeboim-era memory and then
continues automatically into the launch finale.
Dialogue 12 and Emeralda's one cue, dialogue 21, play in the present before the
fade and party hide. When dialogue 21 closes, exact retail save-point sound
bytes `74 50 80` play once; the first fade begins immediately afterward with
no added blocking wait. A silent reaction shot then leads into memory dialogues
22-31 and 36 only. Only the adult Launch Director and helmeted Systems Officer
are visible; hidden entity 19 remains Miang's point-of-view anchor at `(14,58)`
and supplies her offscreen `MIANG` voice. Every memory eye is the stable
Miang-aligned `(174,-102,-125)`, and no camera targets Miang. Under black, the
action hides the memory actors and clears the grade; it then establishes a
concise present camera, shows the party, and fades in. Dialogue 32 is the sole
present response. Instead of releasing the camera or returning control, the
action automatically stages Citan behind the native east leaf at `(225,104)`
and interpolates over 24 frames to a whole-room target `(-13,106,-32)` from eye
`(-27,-767,-544)`. Dialogues 33 and 34 remain authored but unreachable. All 18
entity-13 F5 calls use flag `0x01`; no second Cross/X press is required.

Scoped F8 mask `0x0038` applies only to Citan's first bounded leg to
`(170,89)`. It then clears as he walks through `(160,110)` to `(136,131)`, where
he settles on triangle 26 in direction 0 at the compact retail field-361
standing keypad, target node 43/model 11. Its losslessly relocated model and
texture remain passive static scenery at `(197,439,108)`, yaw `0x0800`, with a
floor-aligned world AABB X `133..174`, Y `-61..0`, Z `153..190`. Entity 12's
single Elly page calls the console out as unlike the other computer terminals
and writes no state. The field is shown before
native entity 15 script 4 opens the leaf. Reciprocal facing cues turn Citan and
the leader toward each other for dialogue 35. After its wait, a 12-frame
held-mode inside-room camera, target `(145,160,-45)` from eye `(170,-80,-135)`,
frames the terminal and a blocking entity-3 script-23
call performs the finite keypad animation and three sound-`0xF9` calls before
completion and world-map unload. Entity 13 sets completion bit 6 and invokes the released game's Mass
Driver world-map event at position `0x0FFF`, mode `17`. The guarded field-617
return removes Citan's temporary slot and restores Elly and Emeralda outside.
Targets 388 and 507 and all Krelian-laboratory assets are absent from V158's
active route and package.

This is an original architectural adaptation for the standalone dungeon, not
recovered Square script, an official deleted Mass Driver route, or evidence
that the retail Cloning Chamber canonically belonged to the facility.

Historical release note: v72 superseded v71 and established the current
two-character dungeon contract. Elly and Emeralda alone traverse the dungeon
and fight the Defense Bay Guardian; Citan appears only at the final launch
console as a noncombat trajectory assistant and is removed on the guarded
field-617 return.

Historical release note: v71 superseded v70 at the time. It changed target 376's
authored script and packed field bundle, added target 384's field bundle and
graphics, and moved the Guardian encounter into that new room. The
authorization terminal wrote only its accepted-code state; the new lift,
one-time bay scene, battle, reciprocal return, and post-victory west gate used
separate checked state transitions.

Historical release note: v70 superseded v69 and repaired target 376's
first-entry Citan staging without restaging Elly or Emeralda. That staging is
retired in v72; it does not describe the current route.

Version 69 superseded v68. It changed only target 368's
authored dialogue, script, and packed field bundle. The main console retains
rail control, while a separate reachable rear console presents the new email
exposition without sharing the rail bit.

Version 68 superseded v67. It changed only target 722's authored dialogue,
script, field header, and packed bundle. Its original north computer combines
both records, while the elevated duplicate computer is replaced by the donor
room's native one-time Omegasol chest.

Version 67 superseded v66. It expanded the original north computer's political
archive while retaining v66's two-computer geometry and sole-Save contract.

Version 66 superseded v65. Its field-content change was the target-722
two-computer presentation described above.

Version 65 superseded v64. It changed only Reserve Magazine 02's authored
dialogue and packed field-378 bundle, adding the 6079 mail while preserving the
room's existing 6083 opening and character reactions.

Version 64 superseded v63. It changed only M-07's undersized prompt/closing
windows, added Elly's one-time first-interaction response, and added regression
coverage for the retail font-unit bounds and persistent event-script branch.

Version 63 superseded v62. It keeps v62's corrected
space-program-to-missile arc, confirmed nuclear release, five forward-entry
magazine scenes, and retail launch handoff, but replaces its over-explained
dialogue with a connected employee story and shorter character reactions.
It also corrects Kim's record to a 6077 expulsion, 6081 Miang sponsorship,
and 6083 military assault; keeps Mara in one job; seeds Citan's Gear-bay route;
and lets Elly identify Miang only after the ambiguous afterimage.

Version 62 replaced the obsolete freight interpretation and no-launch ending
with the canon-consistent space-program-to-missile arc, chronological staff
correspondence, Lawine and Kim-era context, Miang's political manipulation,
confirmed nuclear release, five forward-entry magazine scenes, and a unified
present-day ending. Its first dialogue pass is superseded by v63.

Version 61 introduced the guarded historical afterimage, exact retail Miang
presentation, distinct translucent officers, and Elly's
destruction-to-healing answer. Its refusal-and-fuse version of the apparition
is superseded by v62.

Version 60 superseded v59's single-leaf bulkhead. It added opposed sliding
leaves, detailed grounded and solid warheads, Citan's solid-to-follower state
handoff, a five-stage code gate that cannot accept only its first letter,
rewritten dungeon dialogue, and the authentic retail nanomachine launch
sequence.

Version 59 superseded v58's visually indistinguishable west-door panel. It
added a recessed, stationary frame and full-aperture interaction while
retaining the native-textured moving leaf and v58's corrected vault
reveal/proximity handoff.

Version 56 introduced the five-vault route. Version 58 superseded its
synthetic bulkhead and incomplete vault reveal/proximity handoff while
retaining the cleaned Cloning Chamber shells and PS1-style warheads.

Version 55 remains a historical staging milestone: it introduced the retained
natural Defense Archive arrival and player-triggered Citan briefing. Its
three-gallery, 24-missile route is superseded by v56.

Version 53 first replaced the placeholder archive records with a comprehensive
terminal script. Version 63 corrects that script: the optional records now
trace the Mass Driver from launching materials and instruments toward space,
through military conversion, the Zeboim genetic crisis, Lawine's destruction
of the central power station, Kim's separate molecular-machine research, and
nuclear collapse, to Taura's present use of the surviving launcher. Every
authored lore page is
manually wrapped and build-validated against the retail 58-by-5 window:
29 standard two-unit Latin glyphs per line, no more than five rendered lines
per page, and explicit player-advanced page breaks. Validation measures the
encoded retail font units, including its wider asterisk glyph.

No treasure chest presents exposition in the current release. Historical v94
replaced target 721's visually mismatched handmade terminal with archive relay
H-10, a compact native Harquebus mechanical actor from the retail Goliath
Factory. V109 retires H-10's visible initializer and places the authentic
field-373 Zeboim freestanding station inside the train. Entity 14 remains as an
invisible, repeatable Cross/X controller for the same mail, while the platform's
M-07 shop unit and both vendor catalogs remain separate and unchanged.
Target 361's dormant control now gives the beige/green-lit overhead-arm
hanging computer its own archive interaction, while both floor-console
sections operate the Auxiliary Grid switch. In
target 722, entity 14 invisibly controls the original north
computer at `(40, 150)` and presents both the expanded payload-handling mail
and the four-point authority record in dialogue 8. Entity 15 is field 374's
genuine native animated chest at `(220, 43, 66)`, using actor 2 and sprite 1
to award one Omegasol. Target 725 remains the only room with an active gold
memory-cube Save point.

The accelerator-rail interlock belongs only to target 368's main Archive Console
D, entity 13 at `(45, -42)`. The second computer in the back is entity 14 at
`(-124, -25)`, beneath header node 25/model 4, and presents Aron's 6081 email
to Lena without changing the rail condition. Both use native room scenery;
the reciprocal sliding return door remains unchanged.

Version 49 removed the misleading door-plane rail panel introduced in v48.
The Magnetic Conduit room again contains only its native assets and the
restored retail Zeboim memory cube/save point (target 725 entity 16), which
remains the dungeon's only gold memory-cube Save point.

Version 48 first restored the Magnetic Conduit memory cube's exact retail
Save action and collision wrapper, but its attempted separate rail panel
looked like a door and was difficult to identify. Version 49 supersedes that
panel while preserving the save-point repair.

Version 47 repairs the small gray panel shown in the earlier July 26
screenshot. The matching v46 F2 state identifies it as target 726 entity 22,
whose distinct reciprocal route is `726:e22 -> 369:p0 -> 726:p6`. The room
and transition code were already present, but the panel's invisible
controller pivot lies outside the facing cone aimed at its visible model.
The engine therefore selected collision script 3 instead of X action script
2.

That one controller now explicitly clears its facing-only flag while
retaining its checked X action. Pressing X inside its existing interaction
box plays the native sound and slide, performs the bounded party crossing,
and enters the existing Zeboim archive room D.
Every other door controller and route is byte-policy unchanged.

Version 46 fixes the
black-and-white striped corruption after the save point and Magnetic
Conduit at its script-control-flow source. When v35 expanded target 726's
field-entry table, the relocator copied the retail entity-0 initializer but
left its `IF_GAMEPROGRESS_EQUAL` alternate target at old PC `0x002B`.
Standalone game progress takes that branch, so execution entered parameter
6's coordinate data. Bytes at PC `0x002C` accidentally decoded as opcode
`FE DF`; its `FD 00` operand resolved to mode 0, selecting the engine's
640-pixel field mode. That framebuffer overwrote the Zeboim texture pages
stored from x=320 through x=575 and produced the apparent door crash.

The conditional now targets its relocated alternate path at PC `0x0349`,
and an automated regression rejects any pointer or audited branch into the
expanded entry records. A repaired runtime state remained in normal
320-pixel mode for more than 75 seconds with every field-graphics upload
rectangle byte-exact. Version 45's inward-facing parameter-0 actor and
camera directions remain unchanged; camera placement was not the cause of
the striped geometry.

Version 44's accepted repair for the north door immediately after the
auxiliary-power room remains unchanged. Fresh v43 before/after states proved
that target 372 entity 22 was not entering a stairwell at all: it jumped
directly to target 726 parameter 2. Version 44 installs a second complete
source-375 sealed stairwell in the allocated,
previously dummy target 375. The route is now
`372:e22 -> 375:p0 -> 726:p2`, with both reverse doors reciprocal. The
accepted archive-F stairwell remains independently hosted in target 723.

The same v43 states proved that the striped post-door frame was not a hung
field loader. Target 726 had loaded successfully, but camera octant 4 placed
the eye beyond its closed north wall and rendered through the geometry.
Parameter 2 now keeps Elly facing into the room in actor octant 4 while the
camera uses the unobstructed octant 0. Version 43 repaired the
paired same-room passages after the auxiliary-power annex. Their v38-v42
stability code moved every active party actor to the far side in one frame
and started both door panels concurrently, which could look like a geometry
glitch. The existing allocation-safe party update wrapper now performs a
48-step bounded walk and exact safe landing. The owner allows 52 frames for
that movement, opens both checked native panels serially, restores control,
and only then starts their closing routines.

Version 42 repairs the
striped geometry reproduced while opening target 726's archive door beyond
the golden save point. The earlier count-only suppression left an invalid
64-byte gap between the mesh and display list, retained all eight obsolete
GPU records, and retained their render-buffer allocation. Version 42 removes
the eight baked-panel index records and eight matching display records,
relocates the display list, and shrinks the instance buffer consistently.
The v41 archive-stair route itself is unchanged.

Version 41 changes the
archive-F route shown in the July 26 screenshots: target 371's only door now
enters the complete source-375 sealed stairwell in target 723, and the other
end of that stairwell enters target 726's existing save-point hall. The route
is fully reciprocal. The two displaced visible doors are preserved as a
direct target-372/target-726 pair, while the unrelated target-727/target-372
connection remains direct. Version 44 supersedes only that displaced direct
pair with target 375's independent staircase.

Version 40 makes the
bounded walk through every external mechanical doorway visible. The party
task is now allocated immediately before cinematic control is disabled,
waits for the native panels to open, and completes its finite animated walk
before the unchanged field transition. This retains the anti-freeze timeout
without allowing the owner to reach the next room while no walk is running.
Version 40 also removes field 726's eight replaced baked wall-panel
primitives from the submitted mesh tail. Their vertices, indices, and display
list remain byte-stable, but the audited primitive counts exclude them, so
the PlayStation renderer cannot expand degenerate hidden quads into the
white-and-black striped polygons seen at the archive door beyond the save
point.

Version 39 repairs the
east storage-annex transition that completed its native door animation and
then hard-froze while loading field 722. The destination's record actor now
runs its required `INIT_ENTITY_NPC` opcode before setting its position. A
checked unconditional branch skips only the obsolete donor story/delete
condition and rejoins the original safe continuation.

Version 38 repairs the
four same-field service-hub passages after v37's blocking party-leader
handoff froze with the panels open. Each native panel now starts while
controls are still live; a field-local request lets every already-running
party update snap its own actor to the audited far-side endpoint. The owner
uses only finite waits while controls are disabled, restores controls, and
then queues both native closing animations. No helper or party-script
allocation can block the cinematic interval.

Version 37's attempted serialized repair is retained only as a forensic
record; runtime testing rejected it because the panels opened but party
crossing and control restoration never completed.

Version 36 replaces the
v35 service-panel hinge with each donor field's retail Zeboim sliding-door
routine and correctly oriented native model art. It moves all eight archive
annex returns beyond their controller collision volumes, preserving a
forward-facing arrival with the used door behind the party. Its attempted
accelerator-rail control reused what v48 later proved was the retail memory
cube/save-point sprite; v48 restored the save point, and v49 places the rail
control on Annex 368's proper native console.

Version 35 converted the eight remaining decorative service panels into
accessible doors: one in target 363 and seven in target 726. Every annex
retains its reciprocal native animated return door. Seven consoles remain
replaceable archive records; Annex 368's console now controls the rail.

Version 34 repairs the
service hub's east storage-annex door, which could finish its native opening
animation and then wait forever at the threshold instead of loading the
annex. The same sound and model animation remain, but the party leader now
uses a bounded 120-update walk followed by an exact safe-position snap before
the unchanged field transition. Version 33 repairs the
second internal service-hub passage that could leave Elly through the open
door, Emeralda queued behind it, and cinematic control locked forever. All
four same-field passage endpoints now sit in connected outbound walkmesh
pockets for every possible party leader, and their unbounded follower waits
are finite 24-frame synchronization windows. The native sounds, paired model
animations, camera staging, state writes, and forward movement remain.
Version 32 moves all 20
external-door walk-through waypoints away from closed walkmesh edges. This
fixes the service-hub door that could finish opening and leave Elly frozen at
the threshold before the auxiliary-power annex, and hardens the other paired
Zeboim doors against the same blocking-movement failure. Door sounds,
animations, X activation, movement direction, destinations, and receiving
entries are unchanged. Version 31 changed only Ether Beam's sound event from
v30: it plays the exact two-layer energy
cue authored for Xenogears's `Raimai` attack. The cue is appended as isolated
effects 7 and 8 in El-Regulus's already-preloaded auxiliary sound resource.
`DoubleImpact`, `Beat Storm`, and Ether Beam's animation/timing/damage retain
their accepted v30 bytecode. V74 revises the higher-tier programs as described
below. Version 28's repaired cold-boot names for Elly and Emeralda and its
complete El-Regulus deathblow menu remain intact. Level 1 displays `DoubleImpact`,
`Ether Beam`, and `Beat Storm`.
Ether Beam has a longer native blue-beam sequence, dynamic camera framing,
and an authentic retail beam sound. V74 equips the checked retail
`Atk Lv1 Max`, `Atk Lv2 Max`, and `Atk Lv3 Max` accessories for standalone
testing. Version 26's distinct native-style Triangle, Square,
and X standard attacks and balanced `6/12/24` power coefficients remain
unchanged.
Version 25's removal of Perfect Works Story Mode remains intact, so enemies
retain normal HP, attack, and defense. It starts on the playable world map
outside the
**Mass Driver complex that
already exists in Xenogears' late-game retail map**. It does not load a save,
play through the Disc 2 story, or depend on a story flag. Elly leads and
Emeralda follows.

Double-click:

```text
output/PLAY_MASS_DRIVER_STANDALONE.cmd
```

Approach the nearby facility until **Mass Driver** appears, then press
**X** (Cross) to enter. The portable keyboard profile maps X to `K`. The
checked field and world-map handlers use Cross alone for interaction. Circle
remains dedicated to dash/cancel and cannot activate a nearby action.

## Route

The active target-field graph is:

```text
world map -> 729 <-> 364 <-> 360 <-> 720 <-> 721
                                                |
                                                v
                    363 vestibule <-> 362 airlock <-> 727

operations junction:
  727 <-> 362
  727 <-> 372
  727 <-> 387

four-boundary service hub:
  372 <-> 361  Directive 0320 record; auxiliary interlock
  372 <-> 722  combined archive computer; optional Omegasol chest
  372 <-> 375 <-> 726
          sealed post-auxiliary stairwell

launch works:
  727 <-> 387 <-> 725 <-> 726

post-gate defense and reserve magazines:
  726 <-> 376  unique archive-control chamber; authorization and lower-access lift
          | \
          |  +-> 384
          |      Goliath Factory staging hall and Guardian battle
          |
          +-> 377 <-> 378 <-> 379 <-> 382 <-> 383 <-> 728
               five proximity-linked reserve magazines       Central Control
                                                              memory, Citan arrival,
                                                              local capsule launch,
                                                              then Elly/Emeralda return

archive annexes:
  726 <-> 366
  726 <-> 367  native Zeboim three-door operations junction
          +-> 385  dead-end storage archive; native terminal and Omegasol chest
          +-> 386  dead-end storage archive; native terminal and Omegasol chest
  726 <-> 368  main rail interlock; separate rear archive mail
  726 <-> 369
  726 <-> 370
  726 <-> 723 <-> 371
          sealed stairwell
  726 <-> 724
```

The exact 33-target build order is `729, 364, 360, 720, 721, 363, 362,
727, 372, 361, 722, 723, 375, 387, 725, 726, 366, 367, 385, 386, 368,
369, 370, 371, 724, 376, 384, 377, 378, 379, 382, 383, 728`.

The retail donor mapping is:

```text
729 <- 361   inclined surface lift
364 <- 362   inclined-lift continuation and lower landing
360 <- 398   curved Lighthouse tunnel
720 <- 399   Lighthouse utility tunnel
721 <- 397   abandoned employee subway/platform
363 <- 363   open subway-side service vestibule
362 <- 376   Zeboim personnel pressure-transfer airlock
727 <- 377   three-door operations junction
372 <- 372   four-boundary/eight-control service hub
361 <- 373   control/research annex
722 <- 374   materials-storage annex
723 <- 375   sealed stair connector
375 <- 375   independent post-auxiliary sealed stair connector
387 <- 387   stacked two-level connector
725 <- 385   magnetic conduit hall
726 <- 384   launch-support hall and final gate
366 <- 378   launch-support archive annex A
367 <- 377   native three-door Zeboim operations junction
385 <- 374   civil-payload storage archive and optional Omegasol chest
386 <- 374   strategic-payload storage archive and optional Omegasol chest
368 <- 378   launch-support archive annex C
369 <- 378   launch-support archive annex D
370 <- 378   launch-support archive annex E
371 <- 378   launch-support archive annex F
724 <- 378   launch-support archive annex G
376 <- 394   autonomous-defense archive/control chamber
384 <- 260   Goliath Factory Gear-staging and Guardian hall
377 <- 673   adapted reserve magazine 1
378 <- 673   adapted reserve magazine 2
379 <- 673   adapted reserve magazine 3
382 <- 673   adapted reserve magazine 4
383 <- 673   adapted reserve magazine 5
728 <- 369   Central Control/archive and complete local finale
```

The native landmark enters target 729 at the upper end of source field 361's
inclined lift. The released mechanism is a paired-field sequence, not one
artificially extended room. Operating its visible control retains the donor's
motor, cinematic state, and original 30-step upper-half descent before its
native transition to target 364. Target 364 clones source field 362 and
continues the same descent for the donor's remaining 15 movement steps. It
then performs the released lower-landing SFX and platform-velocity cleanup
before returning control to the player at the actual bottom of the shaft.

The far threshold in target 364 leads into target 360. Backtracking from
target 360 enters target 364 with parameter 1; the retained lower control runs
the native ascent into target 729 with parameter 1, where the upper half
completes. Target 729 suppresses its entrance dialogue on that return trip.
Target 360 retains a one-frame SFX fail-safe, but it runs after the proper
landing and is not used to cut the lift off midway. Source field 386's
vertical/deep elevator is not used.

Fields 360 and 720 are exactly two connected Lighthouse underground tunnel
screens. They lead to field 721's abandoned employee subway terminus; there
is no train ride. One surviving maintenance robot, M-07, stands outside the
stationary train and opens the native Item and Gear-parts menus. Field 373's
authentic Zeboim freestanding station inside the train replaces the former
platform chest and later H-10 relay; its repeatable controller carries the
first 6072 staff mail about an instrument probe and the Mass Driver's original
space-development purpose.

The Lighthouse/subway soundscape is retail music sequence `0x1A` with wave
bank `0x18`; its sparse distant-machinery and water-drop sounds are intentional.
Both assets remain byte-identical in the standalone and combined images. If the
ambience seems absent while runtime state still reports `0x1A`, check the
DuckStation per-game output level: a very low emulator volume can hide this
quiet cue before louder interface sounds.

V166 standalone and V236 combined repair the station graphic after M-07's
vendor menu. The old layout placed the passive station atlas at VRAM x768,
which is also the room's live dialogue-glyph scratch page. V236 repacks the
same sampled texels into the audited menu-safe x832 image, rows 0 through 48;
canonical field resource 2048 is the only disc payload changed from V235.
Launch the combined revision with `output/PLAY_SURFACE_SOYLENT_V236.cmd`.

M-07's prompt and closing response use full-width windows, and Elly comments
once after their first completed interaction. The archive awards no item.
Crossing the far platform threshold loads target 363 at its open-side arrival
automatically; there is no subway exit prompt and no need to press X at that
clear passage.

Target 363 is source 363's service vestibule. Its open entity-14 side returns
to the matching open subway threshold at target 721 parameter 1. Its visible
entity-13 mechanical door enters target 362 parameter 0. Target 362 is source
376's two-door Zeboim personnel pressure-transfer airlock, not another lift
landing. Its clean animated north door returns to target 363 parameter 1,
while its south door enters target 727 parameter 2. Target 727's entity-14
door supplies the animated reverse route into the airlock at parameter 1.
Target 363's remaining baked service panel is inert. The exact existing
target-727 Zeboim terminal stands in front of it at the user's marked
south-wall position, with a solid body and separate tight front reader. It
opens repeatable dialogue only; there is no target-365 room or transition.

The junction's western door reaches target 372, source 372's large service
hub. Its four external mechanical boundaries lead back to target 727, into
the source-373 control/research annex, into the source-374 storage annex, and
directly into target 726's launch-support hall. Four additional
X actions operate two paired local passages inside the same hub. The
junction's other branch runs through target 387's stacked two-level connector
and target 725 before reaching a different side of target 726.

Target 387 preserves the donor's two doorways at the same horizontal position
on separate walkmesh layers. Its lower door connects to target 727 and its
upper door connects to target 725. Target 726 adds a checked parameter-2
arrival at `(43, 602)` on walkmesh 0, beside entity 15, so targets 372 and
726 use matching visible doors in both directions. Six of its remaining
service panels lead directly to targets 366-370 and 724. The target-726 door
beside the Magnetic Conduit arrival leads into target 723's complete sealed
stairwell, whose other end reaches target 371's archive annex. No two panels
share a substitute room.

The complete objective chain is:

1. Read target 361 entity 16's beige/green-lit overhead-arm Guidance Archive
   terminal for the **Directive 0320** clue and optional
   maintenance/political mail.
2. Activate either target 361 floor-console section: entity 12 on the left or
   entity 13 on the right. Both set the same Auxiliary Grid interlock and their
   switch/status dialogue contains no exposition.
3. In target 722, use entity 14's original north computer to read the combined
   payload-handling and authority archive and recover the
   **A-2 / B-5 / C-8 / D-4** clue. Entity 15's separate native chest holds an
   optional Omegasol.
4. In target 368, use the main Archive Console D to restore the accelerator
   rail. The separate terminal in the back contains Aron's optional 6081 mail
   to Lena and does not operate the interlock.
5. With both power interlocks active, open target 726's Central Gate and enter
   the Defense Archive in target 376 through its east service stairs. Elly and
   Emeralda keep the natural threshold arrival. Citan is absent.
6. Walk inward to target 376's built-in wall console, entity 13, press X, and
   select Directive `0320`, followed by four separate prompts for `A-2`,
   `B-5`, `C-8`, and `D-4`. Authorization is written only after all five
   selections match. If a clue was skipped, the terminal identifies its
   archive but still permits manual entry. Wrong choices are rejected without
   consuming anything. This is the room's genuine native console, not a Save
   point or treasure chest.
7. Accepting the complete code keeps the live room camera, plays the north-wall
   lift's native machinery sound, and visibly slides both recessed leaves
   apart without a zoom. Authorization keeps those leaves at their open
   endpoints after a room reload. Walk through the revealed lift to enter target 384's actual Goliath
   Factory hall on foot, then run up the central aisle to Vierge and
   Crescens, which are parked together with a safe gap between them.
8. Crossing the centered approach line starts one scene automatically: Elly
   and Emeralda board both Gears, identify the expired emergency custodian,
   and immediately fight the mechanical Guardian. Citan and Fenrir do not
   appear. Victory keeps both pilots mounted
   in target 384. The far door reports that its bulkhead is offline. Backtrack
   to the south personnel lift, which dismounts both pilots and returns the
   party upstairs on foot.
9. Back upstairs, use the nearby west-bank record/control panel at entity 23.
    It retains its strategic-outcome archive, but only this panel can release
    the Guardian-gated west bulkhead. Its V160 `80x24` no-facing region covers
    the complete visible operator front, so precise aiming at one point is not
    required. The current field camera remains unchanged while the weathered
    leaves play their native sound and slide apart. The open state
    persists after leaving and returning. Walk to the now-open bulkhead, press
    X to traverse it, and pass through reserve magazines 377, 378, 379, 382,
    and 383. Each contains
    six vertical warheads, for 30 total. Walk to either far boundary to
    continue or backtrack; the full-width proximity transitions are automatic
    and require no button. Room entry is silent. To read a magazine's optional
    exposition, approach the field-373 Zeboim freestanding station on the east
    side, face its controls, and press Cross/X.
10. Use target 728's entity-13 central console. Only Elly sees the
    Zeboim-era memory; Emeralda sees an empty room. Confirm only the adult
    Launch Director and helmeted Systems Officer appear, both as complete people
    rather than pixel-sized dots. Miang must remain an offscreen `MIANG` voice;
    after Emeralda's present-day cue, confirm the native save-point chime plays
    once before the fade. The sole present response must be dialogue 32;
    dialogues 33 and 34 must not appear. Do not press Cross/X again: after
    dialogue 32 the held present camera must ease automatically to the
    whole-room view, and Citan must first appear through the native east door.
    Confirm the leaf occludes him before it opens and he walks the checked
    direct three-leg route to the visible compact standing keypad without
    walking in place. Citan stops at `(136,131)`, triangle 26, direction 0, and
    both characters face each other for dialogue 35. Afterward, confirm the
    held camera, target `(145,160,-45)` from eye `(170,-80,-135)`, frames the
    terminal and Citan performs the complete sounded
    keypad sequence before launch.
11. Confirm that continuous entity-13 action launches Taura's nanomachine capsule into
    the upper atmosphere, invokes the retail Mass Driver world-map sequence,
    and returns Elly and Emeralda outside with temporary noncombat Citan
    removed. Targets 388 and 507 are not part of the V158 route.

Target 726's central mechanical door checks the auxiliary and rail interlocks
separately. If one is missing, the door reports that specific
power condition. Launch authorization does not operate this mechanical gate;
it is entered later at the separate archive-control console. The gate remains on
the visible door itself, not on the operations junction. The accelerator-rail
warning is an objective lock, not a failed doorway: use target 726's Archive
Console D door, operate the existing rail terminal, and return.

Elly owns regular Vierge (Gear ID 2) from New Game. V167 keeps the complete
retail Vierge field, world-map, menu, model, animation, command, and balance
paths active. Gear ID 10 remains unused in this chapter. The completed custom
El-Regulus resources are reproducible through
`tools/build_el_regulus_archive.py`, but are deliberately absent from the
Mass Driver replacement set. The party still starts on foot.

At target 376, Elly and Emeralda retain field 394's natural east
service-stair arrival instead of being repositioned by a checkpoint scene.
Citan's party resources are not loaded, no Citan actor is staged beside the
console, and no follower handoff occurs after authorization. The built-in wall
terminal gives the complete briefing and code-entry context directly to Elly
and Emeralda.

The Defense Archive is source field 394's Zeboim-era archive/news chamber
from the Lighthouse underground area, not another field-385 industrial hall.
The authorization action remains on source 394's real console entity 13 while
its original visual controller and interaction collision stay intact.
It remains reachable and usable without a separate NPC interaction.

The correct code is accepted, but the Zeboim custodian's expired emergency
protocol classifies every living visitor as an intruder. The code unlocks the
north lift into target 384's source-260 Goliath Factory hall. A parameter-zero
entry clears stale mounted state and presents Elly and Emeralda on foot beside
Vierge and Crescens, parked symmetrically at `(-200,-2035)` and
`(200,-2035)`. A centered `z=-2100` director trigger plays both boarding beats
and the defense warning, mounts both pilots, and immediately starts the
isolated 36,000-HP Guardian battle. Citan and Fenrir are never
loaded into the formation, and Escape is disabled. Victory preserves the
mounted party through one post-victory field-actor rebuild. The north door is an intentionally nonfunctional factory
bulkhead; using the south personnel lift dismounts both pilots before the
return to target 376. The completed battle then unlocks the west bulkhead into
the first containment vault. Elly's Gear remains Vierge; El-Regulus is neither
found nor introduced inside the facility.

The installer removes field 394 model 8's exact west-aperture `POLY_FT4` and
model 13's exact lower north-wall panel. Models 14/15 and 17/18 replace those
surfaces with paired one-primitive leaves that preserve each donor polygon's
UVs, TPAGE, CLUT, texture, and centre seam. Models 16 and 19 contain only dim
behind-wall reveals; no bright rails, locks, or foreground trim are placed
over neighbouring art. Each pair uses a bounded 24-frame world-position
animation. The west action then performs its bounded party crossing into
target 377; the north action enters target 384.

Targets 377, 378, 379, 382, and 383 each adapt retail field 673's Cloning
Chamber architecture. The build strips the complete retail scene cast and
scripts and removes all six glass-vat placements from every clone. Six
original detailed flat-shaded vertical warheads occupy audited static anchors
in each room, for 30 visible warheads. Floor-contact plinths and support feet
keep them grounded, and matching immovable colliders prevent the party from
walking through them. The concept study is
[the Cloning Chamber warhead adaptation](assets/mass_driver/cloning-chamber-warhead-concept-v1.png).
This reuse is intentionally visible and explicitly non-canonical: it is an
architectural adaptation for the reconstruction, not recovered cut content.

Each vault has full-width automatic proximity boundaries at its north and
south ends. Walking to the far end advances to the next vault; walking back
returns to the previous room. No X press, door interaction, or narrow hidden
trigger is required at an internal vault boundary. A one-shot entity-6 update
releases the donor's full subtractive-black layer and restores player control.
After an unmet edge condition, each boundary script yields one frame and
jumps back to its position poll instead of stopping. `GET_ACTOR_POSITION
2D FF` intentionally resolves through the engine's party mapping to the
current controlled leader; signed Z checks at `+760` and `-760` then issue
the reciprocal transition without a confirm press.

Mechanical doors elsewhere remain X-activated and use the Zeboim donor
pattern. External doors allocate their bounded party walk first, then apply
the cinematic lock, door sound, model-helper animation, finite movement, and
reciprocal field transition. Paired local openings serialize their native
panels and use each party actor's existing update slot for a bounded animated
walk and exact safe landing. Their collision callbacks remain STOP, so
touching a closed mechanical door cannot silently teleport the party.

Every declared directed room link, plus the world-map entrance, uses a
checked receiving parameter with explicit actor and camera directions. On
arrival, the party faces away from the doorway and into the new room; the
camera normally looks the same way from behind the party. Target 726
parameter 2 uses an explicit opposite camera octant because its north wall
would otherwise stand between the camera and party. No active arrival
inherits the previous room's heading. Stacked doors retain their separate
walkmesh layers, and the first curved tunnel uses its diagonal inward axis.

The active objective route uses a full optional archive sequence and
restrained party dialogue. Employee mail establishes the Mass Driver's
space-development purpose and magnetic engineering, its military conversion,
Miang's manipulation through a head-of-state aide and emergency law, the human
cost of Zeboim's decline, Lawine, Kim's separate molecular-machine research,
the 6083 strategic release, and counterstrikes. Elly supplies the moral
throughline, Emeralda recognizes the human history surrounding Kim's work, and
their reactions keep evidence distinct from inference without adding Citan to
the dungeon party.
Central Control reuses that infrastructure to launch Taura's nanomachine
capsule, not a nuclear weapon, and fulfills the retail goal of breaking the
Limiter seal.

Cold boot uses field 728 as the hidden black bootstrap gateway into the
playable world map. Central Control is kept black through the loader reveal
window, so it does not flash onscreen before the exterior appears. The normal
route enters target 728 from target 383 after the fifth reserve magazine. Its
visible west door animates back to target 383 parameter 1. Elly and Emeralda
reach Central Control alone.

Entity 13 owns Elly's subjective memory and the exact native
component-04 sprite fix. Only the Director and Systems Officer are visible;
hidden Miang supplies the POV and offscreen voice. After dialogue 32, Citan
stages automatically behind the native east leaf, enters under the held
whole-room camera after the leaf opens, follows the verified direct route to the
relocated compact retail field-361 standing keypad, faces Elly for dialogue,
then operates that terminal under the held inside-room camera for the complete
local capsule launch. Hidden entity 16 supplies the keypad's solid-only body;
entity 12 supplies only Elly's repeatable out-of-place-console remark. The
guarded return removes the temporary Citan slot before restoring
Elly and Emeralda outside. Targets 388 and 507 and all Krelian-laboratory
assets are absent from V158's active route and package.

The world-map patch preserves the retail Mass Driver complex (model records
59-62, blocks 48-51) and makes its dormant landmark reachable and
interactive. It does not create a Lighthouse tower or replace Taura/Torah's
House. The house's field-614 destination and `Torah's House` label remain
intact.

Most facility interiors use Zeboim/Ethos Dig Site resources. Lighthouse
environment assets are limited to the two approach tunnels, abandoned
employee platform, and field 394 archive chamber. Version 56 deliberately
adds the five cleaned field-673 Cloning Chamber shells described above, while
removing their retail story actors, scripts, and vats. That donor choice
contributes architecture only and does not import its original scene or claim
a canonical link to the Mass Driver. Version 58 retains those shells while
restoring their reveal/control startup and continuous automatic boundaries.
The fixed boss uses an isolated copy of
the retail mechanical Pedestal model and AI, renamed Guardian and placed in
unused enemy set `0x10`; the retail Pedestal remains unchanged. The future
El-Regulus archive remains separate from the Mass Driver's technology and
active resources. This is a canon-conscious
fan reconstruction, not recovered Square cut-content data.

The platform merchant uses the retail Aveh mountain Repair Bot's
self-contained NPC graphics as one surviving Zeboim depot maintenance robot.
No Aveh room, architecture, or story state is imported with it; within this
reconstruction the unit is strictly Zeboim-era industrial hardware. The train
archive instead uses field 373's authentic Zeboim freestanding station. Its
static retail model and lossless indexed texture atlas do not duplicate M-07,
and its invisible controller preserves the repeatable 6072 record.

The corrected layout leaves bank 1's x768 first image to the field-dialogue
glyph renderer and packs the station's sampled 8bpp texels, plus model 14's
relocated texture, into the registered x832 second image for exactly 49 rows.
Live VRAM comparison after closing M-07's vendor menu proves x768 is overwritten
while x832 rows 0..48 and M-07's x896/x960 bank remain byte-identical. The
static station therefore no longer samples menu scratch and survives shop
return without requiring a room reload.
Entity 14 controls only the static station interaction; entity 11 initializes
only M-07.

The merchant now uses isolated, previously unused catalog IDs rather than
altering a retail merchant: normal shop 36 contains 29 item entries, and Gear
shop 20 contains 58 Gear-part entries across the five native categories.
Those merchant catalogs do not add Solaris or Krelian equipment, and every
original retail shop remains unchanged for later story integration. V158 also
uses no Krelian laboratory asset in its active Central Control finale.

The v17 correction for the v16 black-screen shop hang is unchanged. The
PlayStation shop decoder always executes all eight commands in an LZSS
control group; the builder completes each final group with declared zero
padding and validates it using the retail decoder's exact termination rule.

Retail-story integration remains out of scope for this standalone version.

The current package is V167. Its audited build identity is
recorded in the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v167.cue
```

A cold-boot New Game remains the complete V167 acceptance path. For a focused
Guardian retest, enter target 384 from field 376 on V167 media so the lift can
normalize any older save to Vierge. Confirm that Vierge and Crescens are
parked together, that the normal battle theme starts, that Vierge uses its
retail battle presentation, and that the hall ambience returns after victory.
Ask the player to navigate and press controls; do not automate emulator input.

Historical V161 acceptance facts are preserved in
`docs/mass-driver-dungeon-3.22.md`.

Historical V160 acceptance facts follow unchanged.

The frozen package is V160. Its exact packaged identity is recorded in the
release-validation section. A cold-boot New Game remains the complete V160
acceptance path. For the focused
west-panel retest, the user's V159 in-game save may continue, but target 376
must be completely left and re-entered from V160 media; changing the mounted
CUE does not replace resident field code. After the Guardian victory, Cross/X
should work across the visible front of entity 23's west-bank panel. Ask the
player to navigate and press controls; do not automate emulator input.

Historical V159 acceptance facts follow unchanged.

The current frozen package is V159. Its exact packaged identity is recorded in
the release-validation section, and the historical launcher mounted:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v159.cue
```

A cold-boot New Game remains the complete V159 acceptance path. In particular,
an F1 state captured with target 376 already resident retains V158's
unreachable north-lift trigger even after mounting the V159 CUE. Completely
leave target 376 and re-enter it from V159 media, or cold-boot V159, before
validating the automatic walk-through or the widened X fallback.

Historical V158 acceptance facts follow unchanged.

The current frozen package is V158. Its exact packaged identity is recorded in
the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v158.cue
```

A cold-boot New Game remains the complete V158 acceptance path. Any V157-or-
earlier state with target 728 resident retains the older terminal position,
non-solid carrier, archive dialogue, Citan route, and operation-camera bytes.
Completely leave target 728 and re-enter it from V158 media, or cold-boot V158.

The preferred focused V158 finale state is
`near_final_v158_from_v108_vault1.sav`, 1,701,664 bytes with SHA-256
`5be101fd30f7f6c1bcec66b363ca82e5f7cf5cccb7dbac232801648dfdd6f301`.
It mounts the exact V158 CUE and has historical V108 field 377 resident. Its
resident FAT SHA-256 is
`5a8bbb4ca9333f427b0674c18e7f1ebde55ac7c4d76c332acd968c8657459af6`;
target 728 is absent and will cold-load from V158. Flags are `0x0033`, bits
0/1/4/5 set and 6/7/12 clear, with party bytes `01 06 FF`. Walk north so every
later vault and Central Control load fresh from V158. This is focused finale
coverage, not cold-boot whole-release acceptance. Ask the player to navigate
and press controls; do not automate emulator input.

Historical V157 acceptance facts follow unchanged.

The current frozen package is V157. Its exact packaged identity is recorded in
the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v157.cue
```

A cold-boot New Game remains the complete V157 acceptance path. Any V156-or-
earlier state with target 728 resident retains the older terminal asset,
controller, Citan route, direction, and operation-camera bytes. Completely
leave target 728 and re-enter it from V157 media, or cold-boot V157.

The preferred focused V157 finale state is
`near_final_v157_from_v108_vault1.sav`, 1,701,664 bytes with SHA-256
`267dbe35a584cdd9733c46285e51f78b99392d3ff9a500f4c2e6f1aa516105f8`.
It mounts the exact V157 CUE and has historical V108 field 377 resident. Its
resident FAT SHA-256 is
`da14b400a03ecff0c71786a32db046bdeded595a27b93349d6cf4771c195a53d`;
target 728 is absent and will cold-load from V157. Flags are `0x0033`, bits
0/1/4/5 set and 6/7/12 clear, with party bytes `01 06 FF`. Walk north so every
later vault and Central Control load fresh from V157. This is focused finale
coverage, not cold-boot whole-release acceptance. Ask the player to navigate
and press controls; do not automate emulator input.

Historical V156 acceptance facts follow unchanged.

The current frozen package is V156. Its exact packaged identity is recorded in
the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v156.cue
```

A cold-boot New Game remains the complete V156 acceptance path. Any V155-or-
earlier state with target 728 resident retains older header, model, route,
facing, camera, and operation bytes. Completely leave target 728 and re-enter
it from V156 media, or cold-boot V156.

The preferred focused V156 finale state is
`near_final_v156_from_v108_vault1.sav`, 1,701,685 bytes with SHA-256
`6eac212f38e4ee14ce73665fb8b90fc7971293034f7233646098fa85f7704681`.
It mounts the exact V156 CUE and has historical V108 field 377 resident. Its
resident FAT SHA-256 is
`f2aa2741a124de00ba8b3e87b6ff70b883278c217a9044e2b968c088cd3efe6a`;
target 728 is absent and will cold-load from V156. Flags are `0x0033`, bits
0/1/4/5 set and 6/7/12 clear, with party bytes `01 06 FF`. Walk north so every
later vault and Central Control load fresh from V156. This is focused finale
coverage, not cold-boot whole-release acceptance. Ask the player to navigate
and press controls; do not automate emulator input.

Historical V155 acceptance facts follow unchanged.

The current frozen package is V155. Its exact packaged identity is recorded in
the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v155.cue
```

A cold-boot New Game remains the complete V155 acceptance path. Any V154-or-
earlier state with target 728 resident retains older finale code and cannot
validate the automatic post-dialogue-32 handoff. Completely leave target 728
and re-enter it from V155 media, or cold-boot V155.

The preferred focused V155 finale state is
`near_final_v155_from_v108_vault1.sav`, 1,701,664 bytes with SHA-256
`572a329ffb0c9f0e1771b253f13db84fda6adc4c54b104328d81e81f80ce824d`.
It mounts the exact V155 CUE and has historical V108 field 377 resident. Its
resident FAT SHA-256 is
`31413e0b788b3ed4e81ad8ffd23f0d6ed3067e0cc91be9eafd968760f837b847`;
target 728 is absent and will cold-load from V155. Flags are `0x0033`, bits 4/5
set and 6/7/12 clear, with party bytes `01 06 FF`. Walk north so every later
vault and Central Control load fresh from V155. This is focused finale
coverage, not cold-boot whole-release acceptance. Ask the player to navigate
and press controls; do not automate emulator input.

Historical V154 release facts follow unchanged.

The current frozen package is V154. Its exact packaged identity is recorded in
the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v154.cue
```

A cold-boot New Game remains the complete V154 acceptance path. Any V153-or-
earlier state with target 728 resident retains the old entity-13 action and
dialogue bytes; changing discs cannot replace resident field code. Completely
leave target 728 and re-enter it from V154 media, or cold-boot V154.

The preferred focused V154 finale state is
`near_final_v154_from_v108_vault1.sav`, 1,701,664 bytes with SHA-256
`f61675cfc8113a806d2e5d1aef432ac3444cdca2f7aa242bcebac54296146046`.
It mounts the exact V154 CUE and has historical V108 field 377 resident. Its
resident FAT SHA-256 is
`59298ba90b3b7f9a8dddb2b5a2a21cd3320224bcc804e5b7afaf7f6ae0024ee1`.
Flags are `0x0033`, with bits 4 and 5 set and bits 6, 7, and 12 clear; party
bytes are `01 06 FF`. Target 728 is absent and will cold-load. Walk north so
every later vault and Central Control load fresh from V154. This is focused
finale coverage, not cold-boot whole-release acceptance. Ask the player to
navigate and press controls; do not automate emulator input.

Historical V153 release facts follow unchanged.

The current frozen package is V153. Its exact packaged identity is recorded in
the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v153.cue
```

A cold-boot New Game remains the complete V153 acceptance path. Any V152-or-
earlier state with target 728 resident retains old controller geometry and
memory choreography; changing discs cannot replace resident field code.
Completely leave target 728 and re-enter it from V153 media, or cold-boot V153.

The preferred focused V153 finale state is
`near_final_v153_from_v108_vault1.sav`, 1,701,665 bytes with SHA-256
`f0277210b6cb45786bf4d7466740c17239647f21f645fd9b0080dd57d8032dac`.
It mounts the exact V153 CUE and has historical V108 field 377 resident. Its
resident FAT SHA-256 is
`d03a2a9168dbff1a76a3a939162c1784810763628cb374b6a5451ecc89155e07`
at payload offset `0x11A66` / RAM `+0x10004`. Flags are `0x0033`, with bits 4
and 5 set and bits 6, 7, and 12 clear; party bytes are `01 06 FF`. Target 728
is absent and will cold-load. Walk north so every later vault and Central
Control load fresh from V153. This is focused finale coverage, not cold-boot
whole-release acceptance. Ask the player to navigate and press controls; do
not automate emulator input.

Historical V152 release facts follow unchanged.

The current frozen package is V152. Its exact packaged identity is recorded in
the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v152.cue
```

A cold-boot New Game remains the complete V152 acceptance path. Any V151-or-
earlier state with target 728 resident retains old memory-eye operands and
entity-13 F5 controls; changing discs cannot replace resident field code.
Completely leave target 728 and re-enter it from V152 media, or cold-boot V152.

The preferred focused V152 finale state is
`near_final_v152_from_v108_vault1.sav`, 1,701,665 bytes with SHA-256
`882a1fa4090b5607b0574a08f64349d454a84edd3d04346b52e8c52278d55444`.
It mounts the exact V152 CUE and has historical V108 field 377 resident. Its
resident FAT SHA-256 is
`d03a2a9168dbff1a76a3a939162c1784810763628cb374b6a5451ecc89155e07`
at payload offset `0x11A66` / RAM `+0x10004`. Flags are `0x0033`, with bits 4
and 5 set and bits 6, 7, and 12 clear; party bytes are `01 06 FF`. Target 728
is absent and will cold-load. Walk north so every later vault and Central
Control load fresh from V152. This is focused finale coverage, not cold-boot
whole-release acceptance. Ask the player to navigate and press controls; do
not automate emulator input.

Historical V151 acceptance guidance follows unchanged.

The current frozen package is V151. Its exact packaged identity is recorded in
the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v151.cue
```

A cold-boot New Game remains the complete V151 acceptance path. Any V150-or-
earlier state with target 728 resident retains old entity-13 interaction code;
changing discs cannot replace resident field code. Completely leave target
728 and re-enter it from V151 media, or cold-boot V151.

The preferred focused V151 finale state is
`near_final_v151_from_v108_vault1.sav`, 1,701,665 bytes with SHA-256
`c0a105bddcc3d2b28cc32ab3a710d07c84f411cd3f5f69fb8bf3aed7661619de`.
It mounts the exact V151 CUE and has historical V108 field 377 resident. Its
resident FAT SHA-256 is
`d03a2a9168dbff1a76a3a939162c1784810763628cb374b6a5451ecc89155e07`
at payload offset `0x11A66` / RAM `+0x10004`; its decompressed gameplay payload
and payload outside the FAT are byte-identical to the V150 state. Flags are
`0x0033` with authorization and Guardian bits 4 and 5 set, bits 6, 7, and 12
clear, and party bytes `01 06 FF`. Target 728 is absent and will cold-load.
Walk north so every later vault and Central Control load fresh from V151. This
is focused finale coverage, not cold-boot whole-release acceptance. Ask the
player to navigate and press controls; do not automate emulator input.

Historical V150 acceptance guidance follows unchanged.

The current frozen package is V150. Its exact packaged identity is recorded in
the release-validation section, and the main launcher mounts:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v150.cue
```

A cold-boot New Game remains the complete V150 acceptance path. A state with
target 728 resident from V149 or earlier retains the old three-visible-actor
memory, Citan staging, door, and camera behavior; changing discs cannot replace
resident field code. Completely leave target 728 and re-enter it from V150
media, or cold-boot V150.

The preferred focused V150 finale state is
`near_final_v150_from_v108_vault1.sav`, 1,701,665 bytes with SHA-256
`9704f618da1834db9e0ab9ea3223348006456bb762cc4401ada94075b06b6808`.
It mounts the exact V150 CUE and has historical V108 field 377 resident. Its
resident FAT SHA-256 is
`d03a2a9168dbff1a76a3a939162c1784810763628cb374b6a5451ecc89155e07`
at payload offset `0x11A66` / RAM `+0x10004`; payload outside the FAT is
unchanged. Flags are `0x0033` with authorization and Guardian bits 4 and 5 set,
bits 6, 7, and 12 clear, and party bytes `01 06 FF`. Target 728 is absent and
will cold-load. Walk north so every later vault and Central Control load fresh
from V150. This is focused finale coverage, not cold-boot whole-release
acceptance. Ask the player to navigate and press controls; do not automate
emulator input.

Historical V149 acceptance guidance follows unchanged.

The current frozen package is v149. Its exact packaged identity is recorded
in the release-validation section:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v149.cue
```

A cold-boot New Game remains the complete v149 acceptance path. A clean
v114-or-later in-game save can continue, but a state or save made with target
376 resident must completely leave the room and re-enter it after v149 media is
mounted. A migrated V143 state still has V143 field 376 resident and cannot
validate V144's live-camera authorization or automatic lift until the room is
completely left and re-entered. Resident v141 and earlier code cannot hot-load the facing-gated,
tightened controller frontages or entity 25's live-captured placement. Resident
v140 and earlier code cannot hot-load the foreground-only
interceptor head or its three-cell exhaust contract. Resident v139 and earlier
code cannot hot-load the compact five-cell blast renderer or Missile-specific
`0x51` explosion cue. Resident v138 and
earlier code cannot hot-load the bounded three-point
incoming-tail renderer; resident v137 and earlier code cannot hot-load the background-safe
renderer; resident v136 and earlier code also cannot hot-load the real-time worker
scripts; resident pre-v131 code also cannot load the rewritten Missile Command,
the root and arcade menus, entity 20's visible-terminal frontage, or the
revised NUKE UI. A resident v135 target-376 state also retains the old y256
atlas placement and cannot validate v136's y384 empty-party-slot correction.

A state made with target 363 resident must likewise leave that room completely
and re-enter it from v149 media. The fresh load is required to install the
conservative row-485 station palette mapping while preserving row 488 and the
native door assets. Ask the player to perform this navigation; do not automate
emulator movement or interaction.

Any battle entered with V142's canonical 29 resident retains its odd command-
table address and cannot validate the Guardian-menu fix. End that battle and
enter a new one after mounting V149, or cold-boot V149. Any V148 state with
target 728 resident retains V148's old finale controller, active treasure, and
blocked Citan route. It cannot validate V149's centered panel, retired chest,
or bounded natural entrance. Completely leave the resident field and enter
target 728 from V149 media.

The preferred focused V149 finale state is
`near_final_v149_from_v108_vault1.sav`, 1,701,664 bytes with SHA-256
`b044a007a583fc47e376571784dea534fa34f1cc5265b5cd5fdc75f06cefa6d5`.
It starts in historical V108 field 377 with flags `0x0033`, Elly and Emeralda
only, and no active dialogue or scripts. Walk north so every later vault and
Central Control load fresh from V149. It is focused finale coverage, not
cold-boot whole-release acceptance.

The historical focused V148 diagnostic state remains available for comparison:
`guardian_v148_authorization_console_central_finale.sav` is 1,745,341 bytes
with SHA-256
`e2dbea2efb984b714fa92a83fb4253aaba56170a019d1d1f680ccb16cc9e182e`.
It has exact V148 media and resident FAT, repaired/even canonical 29, and none
of targets 728, 388, or 507 resident, so Central Control loads fresh. Its warm
field-376 script is V143 and must be exited and reloaded before validating
field-376 changes. It is not cold-boot whole-release acceptance. No legacy
continuation state is recommended for complete v149 acceptance. The
historical `MASS_DRIVER_V71_CONTINUE.sav` already contains the old early-Citan
party and begins with field 376 resident after the Guardian; it cannot validate
v149's two-character dungeon, aligned Defense Archive interactions, seven
console banks, disk pickup, seven-frame native video, source-377 archive junction,
and source-374 storage dead ends, adjacent-Gear encounter, Citan's final-only
arrival, restored Central Control memory and local launch, corrected
El-Regulus ability word and name, the train archive's authentic Zeboim station,
the corrected subway return arrival, the animation-0 battle-entry idle loop,
the distinct mounted-field Gear poses, the five authentic field-373 Zeboim
stations, canonical-29 alignment, or the native component-04 apparition fix. Run
`output/PLAY_MASS_DRIVER_STANDALONE.cmd`, choose New Game after a cold boot,
and enter the facility normally. In particular, do not load the July 31 14:50
F1 state: it explicitly remounts v73 and restores the obsolete Frame HP
accessories. No pre-v115 F1 state or in-game save can validate v149 completely:
DuckStation
states restore their mounted disc and resident RAM, while in-game saves retain
older GameState ability words and fixed-cell names. Fully quit DuckStation,
boot v149, and choose New Game. Make a fresh F2 state or in-game save only after
that New Game has completed.

A v103 F1 state saved with target 726 resident cannot validate the v104 panel
fix retained in v110 because it restores v103's resident entity-20 action
script. Leave target 726 and re-enter it from v149 media before testing the
small gray archive panel, or use the clean cold-boot v149 New Game path.

A V148 state saved with target 728 resident retains the previous off-panel
controller, active native chest, and long blocked Citan bounds. Cold-boot V149,
or explicitly mount V149 media, completely leave the resident field, and enter
target 728 before testing the centered control panel, silent chest, natural
Citan arrival, restored memory, or local capsule launch.

Version 31 retains v30's accepted deathblow animations, v28's complete
deathblow suite, v27's damage repair, v26's standard attacks, v25's normal
combat set, and v24's encounter and battle-entry corrections. Canonical
system resource 29 now gives El-Regulus all twelve Vierge-style command
labels. The blue-beam Level-1 slot is deliberately renamed from `Hard Smash`
to `Ether Beam`; the other labels retain their retail English text.

DoubleImpact program 35 now performs El-Regulus's proper native `0x40`
motion twice, with a ten-tick pause between the two attacks, and resolves
its single damage event only after the repeated motion completes. It does
not use the unrelated `0x43` ducking motion seen in the rejected v29
candidate.

Ether Beam program 36 is expanded from the short retail fragment into a
168-byte player-Gear sequence. It faces the target, uses the Square camera
envelope, plays El-Regulus's native firing pose and blue beam, holds the
charge and beam long enough to read, and now dispatches the two-layer retail
energy cue from Xenogears's `Raimai`. The provenance chain is canonical 2594
Gear 15 record 9 -> animation 41 -> local clip/program 65 -> simultaneous
sound IDs 7 and 8 with retail visual effect `0x19`.

El-Regulus's retail animation 29 already preloads canonical 3368 as sound
selector 2. Version 31 retains the checked Guided Shot SEDS used by v30,
extends its pointer table from seven to nine effects, and appends only
Raimai's exact 86 bytes of channel bytecode as new effects 7 and 8. The
existing Guided Shot effects remain byte-for-byte unchanged. Ether Beam's
retail-sized 12-byte sound event selects the new effects, and v74 also uses
that cue for the two upper Infinity finishers. Its four-tick dispatch guard lets
the sound start before the unchanged native visual event arms the shared
asynchronous event slot. Raimai uses battle-global WDS banks 0 and 1; every
required bank/sample pair is already referenced by El-Regulus's retail SEDS.

Canonical 2960's primary model/sound container is byte-identical to retail.
Its relocated main root ends at `0x7FF8`, below the runtime-sensitive
`0x8000` boundary crossed by the rejected v29 candidate.

The nine retail four-byte stubs for Attack Levels 2, 3, and Infinity are now
complete model-local programs with multi-motion combinations or beam
variants, one damage dispatch, recovery, and completion. V76 introduced, and
v99 retains, the restriction of every physical prelude to confirmed offensive
clips `0x40`, `0x41`, and `0x42`.
Clip `0x43` is the ducking/down motion, and `0x45` is the observed
collapse/defeat motion; neither is used by these physical combinations.
Clip `0x44` is not a collapse animation: it is El-Regulus's valid beam
charge/firing pose and remains inside the native beam finishers. Infinity
programs 68-70 each perform two ordered offensive motions and then fire the
native blue ether beam, escalating their camera, charge, hold, and retail
energy cue.

The standalone GameState starts Elly at level 70 with battle-command loadout
`m56 = 1`. That loadout makes retail battle code read the third ability
halfword at `0x16E4`, not the adjacent on-foot word at `0x16E0`. V76 left
`0x16E4 = 0x1808`, so its runtime maximum was genuinely Level 1 despite the
correct retail Attack-Level-Max accessories `0x60`, `0x61`, and `0x62`.
V77 writes exact word `0x1FF8`, combining Level-1/2/3 unlock masks `0x1C00`,
`0x0380`, and `0x0070` with Infinity bit `0x0008`. Canonical 2594 verifies the
accessories' effect selectors as `06/07/08`; the retired
`0x5A/0x5B/0x5C` items are Frame HP10/30/50. During battle the entity stores
current and maximum Gear Attack Level at `+0x148` and `+0x149`; ordinary Gear
attacks can now advance Attack Level 0 -> 1 -> 2 -> 3. Using any deathblow resets Attack Level, so
keep choosing ordinary attacks until the desired Level-2 or Level-3 menu is
reached. Infinity remains subject to the native Hyper roll once Level 3 is
reached.

Canonical 2595's 31 fixed-width name records are also rebuilt in their actual
little-endian glyph-cell format. This restores the main-menu names `Elly` and
`Emeralda` while retaining `El-Regulus` in its Gear slot.

El-Regulus's minimal
44-byte standard attacks are now complete player-Gear sequences: each keeps
its own native `0x40`, `0x41`, or `0x42` motion clip and single damage event,
while gaining a distinct retail camera-framing and synchronization envelope.
Their power curve remains proportional at `6/12/24`, with the
original `10/20/30` fuel costs, accuracy, elements, and status data.

At the Mass Driver start area,
table 12, scenario row 2, formation slot 0 now selects its native Gear-scale
Dragon instead of Tusk-Tusk. The Dragon has 18,000 normal HP and retains the
Mass Driver battle backdrop. Mounting El-Regulus before the encounter
produces the normal Gear command HUD, attacks, enemy turns, victory flow, and
mounted return to the saved world-map position. Outside this area, each
world-map region still supplies its native slot-0 formation.

The historical v117 Defense Archive signal override, seven-frame playback, package
identity, terminal frontages, and reload guidance are recorded in
[the v117 release notes](docs/mass-driver-dungeon-2.93.md). The historical v116
inventory-video event and package identity remain recorded in
[the v116 release notes](docs/mass-driver-dungeon-2.92.md). The historical v115
field-flag video event and package identity remain recorded in
[the v115 release notes](docs/mass-driver-dungeon-2.91.md). The historical v114
personnel-station frontage remains recorded in
[the v114 release notes](docs/mass-driver-dungeon-2.90.md). The retained v111
private-laboratory transplant is documented in
[the v111 release notes](docs/mass-driver-dungeon-2.88.md). The retained v110
Defense Archive alignment is documented in
[the v110 release notes](docs/mass-driver-dungeon-2.87.md).
The retained historical v109 subway-station transplant is recorded in
[the v109 release notes](docs/mass-driver-dungeon-2.86.md).
The retained historical v108 reserve-magazine native-allocation transplant is
recorded in [the v108 release notes](docs/mass-driver-dungeon-2.85.md).
The allocator-unsafe historical v107 appended-upload transplant is retained in
[the v107 release notes](docs/mass-driver-dungeon-2.84.md).
The retained historical v106 final-route expansion and Defense Archive control
presentation are recorded in
[the v106 release notes](docs/mass-driver-dungeon-2.83.md).
The retained historical v105 Central Control terminal correction and artifact
identities are recorded in
[the v105 release notes](docs/mass-driver-dungeon-2.82.md).
The retained historical v104 launch-support panel correction, artifact
identities, and reload guidance are recorded in
[the v104 release notes](docs/mass-driver-dungeon-2.81.md).
The retained historical v103 smooth Citan entrance, artifact identities, and
cold-boot guidance are recorded in
[the v103 release notes](docs/mass-driver-dungeon-2.80.md).
The retained historical v102 Central Control adult-actor and line-by-line
facing correction, artifact identities, and cold-boot guidance are recorded in
[the v102 release notes](docs/mass-driver-dungeon-2.79.md).
The retained historical v101 native reserve-magazine service-pedestal
replacement, artifact identities, and cold-boot guidance are recorded in
[the v101 release notes](docs/mass-driver-dungeon-2.78.md).
The retained historical v100 Defense Archive terminal expansion, artifact
identities, and cold-boot guidance are recorded in
[the v100 release notes](docs/mass-driver-dungeon-2.77.md).
The retained v99 mounted-field El-Regulus animation and quiet post-battle
handoff are recorded in [the v99 release notes](docs/mass-driver-dungeon-2.76.md).
The retained v98 native El-Regulus command-menu idle fix and historical
artifact identities are recorded in
[the v98 release notes](docs/mass-driver-dungeon-2.75.md).
The retained v97 native-facing restoration and its historical artifact
identities remain recorded in
[the v97 release notes](docs/mass-driver-dungeon-2.74.md).
The superseded v96 formation-specific facing experiment, regression evidence,
and historical artifact identities remain recorded in
[the v96 release notes](docs/mass-driver-dungeon-2.73.md).
The retained v95 Zeboim archive branch and subjective Central Control finale
are recorded in [the v95 release notes](docs/mass-driver-dungeon-2.72.md).
The superseded historical v94 native subway archive robot is recorded in
[the v94 release notes](docs/mass-driver-dungeon-2.71.md).
The retained v93 subway return correction is recorded in
[the v93 release notes](docs/mass-driver-dungeon-2.70.md).
The retained v92 Elly-only Central Control vision and native camera staging
are recorded in [the v92 release notes](docs/mass-driver-dungeon-2.69.md).
The superseded v91 retail reserve-magazine terminal visual and historical
artifact identities are recorded in
[the v91 release notes](docs/mass-driver-dungeon-2.68.md).
The superseded v90 texture-free reserve-magazine terminal conversion and its
artifact identities are recorded in
[the v90 release notes](docs/mass-driver-dungeon-2.67.md).
The retained v89 Gear-bay dialogue and native battle-facing correction,
artifact identities, and live v88 failure evidence are recorded in
[the v89 release notes](docs/mass-driver-dungeon-2.66.md).
The retained v88 source-378 hanging-terminal geometry correction and its
historical packaged evidence are recorded in
[the v88 hanging-terminal notes](docs/mass-driver-dungeon-2.65.md).
The retained v87 Auxiliary-room geometry correction and historical packaged
evidence are recorded in
[the v87 hanging-terminal notes](docs/mass-driver-dungeon-2.64.md).
The superseded v86 terminal-role remap and historical packaged evidence are
recorded in [the v86 terminal-role notes](docs/mass-driver-dungeon-2.63.md).
The retained v85 El-Regulus name and subway-terminal corrections are recorded
in [the v85 name and train-terminal notes](docs/mass-driver-dungeon-2.62.md).
The superseded v84 Guidance Archive interaction-bound correction and
historical packaged evidence are recorded in
[the v84 terminal-bound notes](docs/mass-driver-dungeon-2.61.md).
The superseded v83 terminal-controller alignment, no-facing interaction repair,
and historical packaged evidence are recorded in
[the v83 terminal-access notes](docs/mass-driver-dungeon-2.60.md).
The superseded v82 Zeboim service-archive replacement, paired-terminal mail
expansion, and historical packaged evidence are recorded in
[the v82 room and terminal notes](docs/mass-driver-dungeon-2.59.md).
The superseded v81 auxiliary-room controller correction and historical
packaged evidence are recorded in
[the v81 terminal-mapping notes](docs/mass-driver-dungeon-2.58.md).
The retained v80 adjacent-Gear staging, approach trigger, mounted return rebuild, and
packaged evidence are recorded in
[the v80 Gear-encounter notes](docs/mass-driver-dungeon-2.57.md).
The retained control-panel/archive-terminal separation is recorded in
[the v79 terminal-role notes](docs/mass-driver-dungeon-2.56.md).
The retained v78 staging-hall and battle-facing evidence is recorded in
[the v78 Gear-staging and facing notes](docs/mass-driver-dungeon-2.55.md).
The v77 loadout-selected ability-word repair, exact unlock masks, old-save
restriction, retained motion sequences, and packaged evidence are recorded in
[the v77 El-Regulus Attack-Level notes](docs/mass-driver-dungeon-2.54.md).
The inherited v76 offensive-motion correction and exact clip sequences remain
recorded in [the v76 El-Regulus motion notes](docs/mass-driver-dungeon-2.53.md).
The rebuilt Defense Archive doors and superseded two-room Goliath Factory route,
the now-superseded source-380 materials lab, and historical v75 release evidence are recorded in
[the v75 door and lower-route notes](docs/mass-driver-dungeon-2.52.md).
The v74 accessory correction and mixed melee/ether Infinity programs remain
recorded in [the v74 El-Regulus notes](docs/mass-driver-dungeon-2.51.md); its
claim that accessories alone repaired the cap is superseded by v77.
The Reserve Magazine 02 archive console and historical v73 release evidence
remain recorded in
[the v73 archive-terminal notes](docs/mass-driver-dungeon-2.50.md).
The two-character dungeon continuity and historical v72 release evidence are
recorded in
[the v72 final-only Citan notes](docs/mass-driver-dungeon-2.49.md).
The separated Defense Bay progression and historical v71 release evidence are recorded in
[the v71 Defense Bay notes](docs/mass-driver-dungeon-2.48.md).
The Defense Archive first-entry repair and historical v70 release evidence are recorded in
[the v70 Citan-staging notes](docs/mass-driver-dungeon-2.47.md).
The split Archive Console D controls and historical v69 release evidence remain
recorded in
[the v69 rail-and-mail terminal notes](docs/mass-driver-dungeon-2.46.md).
The consolidated Materials Storage computer, native Omegasol chest, and
historical v68 release evidence remain recorded in
[the v68 storage-object notes](docs/mass-driver-dungeon-2.45.md).
The expanded Materials Storage political archive and v67 release evidence
remain recorded in
[the v67 north-computer notes](docs/mass-driver-dungeon-2.44.md).
The Materials Storage computer presentation, global sole-Save contract, and
v66 release evidence are recorded in
[the v66 terminal-presentation notes](docs/mass-driver-dungeon-2.43.md).
The Reserve Magazine 02 political mail and v65 release evidence are recorded in
[the v65 reserve-mail notes](docs/mass-driver-dungeon-2.42.md).
The M-07 window correction and one-time Elly response remain documented in
[the v64 robot-dialogue notes](docs/mass-driver-dungeon-2.41.md).
The v63 dialogue audit, connected employee-mail arc, corrected chronology,
revised historical afterimage, authentic launch handoff, and release evidence
are recorded in
[the v63 natural-dialogue notes](docs/mass-driver-dungeon-2.40.md).
The v62 canon audit and first story-closure pass remain as historical context
in [the v62 canon notes](docs/mass-driver-dungeon-2.39.md).
The v60 paired bulkhead, grounded solid warheads, Citan handoff, dialogue
revision, and authentic launch sequence remain as historical context in
[the v60 completion notes](docs/mass-driver-dungeon-2.38.md).
The v59 recessed bulkhead, full-width interaction, and runtime traversal
remain as historical context in
[the v59 readable-bulkhead notes](docs/mass-driver-dungeon-2.37.md).
The v58 native-textured panel, visible vault startup, and continuous proximity
transitions remain as historical context in
[the v58 door and vault-continuity notes](docs/mass-driver-dungeon-2.36.md).
The initial v56 five-vault architectural adaptation remains historical context
in [the v56 containment-vault notes](docs/mass-driver-dungeon-2.35.md).
The superseded v55 three-gallery route and the retained natural Defense
Archive arrival/player-triggered Citan briefing remain as historical context
in [the v55 Defense Archive arrival notes](docs/mass-driver-dungeon-2.34.md).
The retained v54 progression repair, narrative continuity pass, and one-time
launch guard are recorded in
[the v54 continuity notes](docs/mass-driver-dungeon-2.33.md).
The retained v53 terminal script, page-layout contract, and removal of exposition
chests are recorded in
[the v53 terminal-archive notes](docs/mass-driver-dungeon-2.32.md).
The retained v52 unique archive-control chamber, genuine field-394 console,
and west sliding bulkhead are recorded in
[the v52 archive-control notes](docs/mass-driver-dungeon-2.31.md).
The superseded v51 field-385 defense checkpoint, missile galleries, and
historical three-Gear Guardian battle are recorded in
[the v51 post-gate notes](docs/mass-driver-dungeon-2.30.md).
The retained v50 two-condition Central Gate and authorization baseline is
recorded in
[the v50 progression notes](docs/mass-driver-dungeon-2.29.md).
The retained Annex 368 rail-control implementation is recorded in
[the v49 Annex 368 and authorization notes](docs/mass-driver-dungeon-2.28.md).
The superseded v48 Magnetic Conduit panel attempt is recorded in
[the v48 Magnetic Conduit notes](docs/mass-driver-dungeon-2.27.md).
The retained gray-panel activation repair is recorded in
[the v47 gray-panel door notes](docs/mass-driver-dungeon-2.26.md).
The retained field-entry branch repair is recorded in
[the v46 renderer-corruption repair notes](docs/mass-driver-dungeon-2.25.md).
The retained v45 parameter-0 arrival orientation is recorded in
[the v45 post-save-point arrival notes](docs/mass-driver-dungeon-2.24.md).
The retained dedicated post-auxiliary staircase and its independently
wall-safe receiving camera are recorded in
[the v44 post-auxiliary stair notes](docs/mass-driver-dungeon-2.23.md).
The retained v43 same-room passage repair is recorded in
[the v43 service-hub passage notes](docs/mass-driver-dungeon-2.22.md).
The retained complete obsolete-panel removal and boot validation are recorded in
[the v42 archive-door geometry notes](docs/mass-driver-dungeon-2.21.md).
The retained archive-stair route is recorded in
[the v41 archive-stair route notes](docs/mass-driver-dungeon-2.20.md).
The retained pre-cinematic walking repair is recorded in
[the v40 external-door walking notes](docs/mass-driver-dungeon-2.19.md).
The retained storage-annex initialization repair is recorded in
[the v39 storage-annex initialization notes](docs/mass-driver-dungeon-2.18.md).
The retained deterministic same-field passage repair is recorded in
[the v38 service-hub passage notes](docs/mass-driver-dungeon-2.17.md).
The runtime-rejected v37 serialization remains documented in
[the superseded v37 notes](docs/mass-driver-dungeon-2.16.md).
The retained rail-terminal placement, sliding-door repair,
return-collision audit, and v36 validation are recorded in
[the v36 door/interlock notes](docs/mass-driver-dungeon-2.15.md).
The original archive-annex implementation remains recorded in
[the v35 archive-annex notes](docs/mass-driver-dungeon-2.14.md).
The retained v34 storage-annex door repair and railway-gate distinction are
recorded in
[the v34 storage-annex door notes](docs/mass-driver-dungeon-2.13.md).
The retained local-passage audit is recorded in
[the v33 internal-passage notes](docs/mass-driver-dungeon-2.12.md).
The retained external-door waypoint audit is recorded in
[the v32 door-transition notes](docs/mass-driver-dungeon-2.11.md).
The retained Ether Beam implementation is documented in
[the v31 El-Regulus beam-audio notes](docs/mass-driver-dungeon-2.10.md).
The accepted v30 animation repair remains documented in
[the v30 El-Regulus attack/audio notes](docs/mass-driver-dungeon-2.9.md).
The runtime-rejected v29 attempt is retained only as a forensic record in
[the superseded v29 notes](docs/mass-driver-dungeon-2.8.md).
The superseded complete-suite implementation is recorded in
[the v28 El-Regulus deathblow notes](docs/mass-driver-dungeon-2.7.md).
The superseded Level-1-only repair is recorded in
[the v27 El-Regulus deathblow notes](docs/mass-driver-dungeon-2.6.md).
The standard attacks remain documented in
[the v26 El-Regulus attack notes](docs/mass-driver-dungeon-2.5.md). The
[v25 normal-combat notes](docs/mass-driver-dungeon-2.4.md) and
[v24 combat-test notes](docs/mass-driver-dungeon-2.3.md) remain as historical
evidence for the normal-combat correction and superseded Story-mode build.

Version 23 supplied the complete retail-style world-map Gear behavior:
five authentic upright direction frames while idle, five separate
forward-driving direction frames while moving, and the original
`0, -2, -4, -6, -4, -2` movement bob applied to those travel poses. Its full
contract is recorded in
[the v23 El-Regulus forward-pose notes](docs/mass-driver-dungeon-2.2.md).
The superseded v22 bob-only implementation is documented, with a correction
notice, in
[the v22 El-Regulus movement notes](docs/mass-driver-dungeon-2.1.md).
The superseded static v21 presentation is documented in
[the v21 PS1-safe El-Regulus sprite notes](docs/mass-driver-dungeon-2.0.md).
The superseded v20 conversion is documented, with a correction notice, in
[the v20 authentic El-Regulus sprite notes](docs/mass-driver-dungeon-1.9.md).
The superseded v19 presentation attempt is documented, with a correction
notice, in
[the v19 El-Regulus presentation notes](docs/mass-driver-dungeon-1.8.md).
The v18 ownership work remains documented in
[the v18 El-Regulus notes](docs/mass-driver-dungeon-1.7.md). The accepted v17
shop build remains documented in
[the v17 shop-loader correction](docs/mass-driver-dungeon-1.6.md), and the
accepted v14 objective baseline remains documented in
[the v14 build notes](docs/mass-driver-dungeon-1.3.md).

The sprite and expanded-inventory work is documented in
[the v16 Repair Bot shop notes](docs/mass-driver-dungeon-1.5.md).

## Build

The user supplies legally obtained US Disc 1 and Disc 2 images. Original disc
images are never modified in place.

For a newly prepared workspace, extract the fourteen retained retail Disc 2
resources used by the presentation, shop, and El-Regulus battle work:

```powershell
$sourceDisc = "C:/path/to/Xenogears_PW_CD2.bin"
python tools/xgdisc.py extract $sourceDisc work/_audit_el_regulus_field657 `
  --canonical-disc2 1920 1921 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_el_regulus_worldmap `
  --canonical-disc2 3949 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_shop_models `
  --canonical-disc2 2260 2261 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_regulus `
  --canonical-disc2 2998 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_el_regulus_battle `
  --canonical-disc2 2931 2960 3084 3368 3425 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_el_regulus_damage `
  --canonical-disc2 2594 --force
python tools/xgdisc.py extract $sourceDisc work/_audit_system_data `
  --canonical-disc2 29 --force
python tools/xgdisc.py extract $sourceDisc work/shop_menu_data `
  --canonical-disc2 2602 --force
python tools/xgdisc.py extract $sourceDisc work/guardian_resources `
  --canonical-disc2 2749 --force
```

Prepare the matching Perfect Works 0.10.2 normal-combat set:

```powershell
python tools/prepare_mass_driver_normal_combat.py `
  --perfect-works-gamefiles C:/path/to/Perfect_Works_Build/gamefiles `
  --output work/normal_combat_resources `
  --force
```

The helper selects `script2/<id>` when the translated normal resource exists
and otherwise selects `og_monsters/<id>`. It deliberately does not use
`monsters_script`, which belongs to the separate optional enemy rebalance.

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v161_stage `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v161.bin
```

Run automated validation with:

```powershell
python -m unittest discover -s tests
```

Treat any automated-test failure, error, or skip as release-blocking.

## V161 release validation

The current standalone image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v161.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v161.cue
```

The BIN is 696,130,848 bytes / 295,974 sectors with SHA-256
`b010fcb46946e5e1595d7225652bd78f04b91e97a5b6dce0cc8cf0675ed49bf4`.
The 107-byte CUE has SHA-256
`06149bd106fdd02fe1baacbae6b07b001411bb4ecfb6cc501efd199ea0379561`.
The 252,161-byte manifest at `work/mass_driver_v161_stage/manifest.json` has
SHA-256
`7b3a65389d7b557e52d94c353e717eb951e0afd4b05d4fd591a8e082754e6d8a`,
136 jobs, 169 replacements, 11,804,464 replacement bytes, 33 fields, and 66
directed edges. Its canonical-ID-sorted payload and framed aggregate hashes are
`1cebbdb3bbdc7a46ac4c86b7dabbd787bdb20813786eb1e87993145dd1112b7f`
and `de4dae7ab4f33a3081595b55ed51783f2728af833b25f3f9ecfb72fa99fb0d86`.

The declared V160-to-V161 gameplay delta is canonicals 1374 and 2960. Direct
final-BIN extraction matches all 169 staged replacements. The exhaustive
payload delta is canonicals 17, 22, 1374, and 2960; canonicals 17 and 22 reflect
canonical 2960's four-byte descriptor-size change. Canonical 2960 is the only
changed FAT descriptor, from 33,604 to 33,608 bytes. All start sectors, kinds,
directory memberships, and allocations remain unchanged. All 61 directory
tables match.

Ten raw sectors change at LBA 34, 172929, 197074, 197140-197141, 197152,
244670, and 244684-244686. They differ by 4,867 raw bytes and 3,414 user-data
bytes; the other 295,964 sectors are exact. All 5,846 replacement sectors and
the 5,849-sector union containing every changed sector and boot pass
Mode2/Form1 EDC/ECC validation.

Target 384 canonical 1374 remains 162,324 bytes with SHA-256
`3f294aacbf4a5fd1fc535015042364b7ce5a6a925547bc061906aee3edc57ba7`.
Its script grows to 21,205 bytes / 19,281 bytecode bytes with SHA-256
`a0f485a0e7537ff90754baacf1c5dbb62eab5922f84778b51cc3d3575bbae315`.
Exact bytes `75 14 80` now precede `FE 84 0F 80`, selecting normal battle
music ID `0x14`. Canonical 2960 grows to 33,608 bytes with roots
`(2,0x10,0x7FFC,0x8348)` and SHA-256
`78eee071519dc5ee3cbbf5ca0080c69923580b6443b3e48e9759db451b6da46c`.
Animation 4 contains exactly one `4A FD 60 00 43 00 5B 02` post-return
formation-target handoff.

The builder is 1,399,262 bytes with SHA-256
`2a2559bdb602e437d163d9e97f2c838fb64cc29cc04120ddcb200d9264069077`.
An isolated repeat build matches all 550 stage files, the manifest, BIN, and
CUE byte-for-byte; a short staging path was required by the legacy path limit.
Static and dynamic V161 installer verification passes. The Play launcher is
version `1.6.1.0`, 446,464 bytes, with SHA-256
`7001509183bcc90986fbee68450cb33a8ae171134ecd7a85dde528162910f0c9`.
The installer EXE identity remains deliberately unpinned because rebuilding
documentation resources changes that container without changing the tested
payload contract. The authoritative instrumented suite passes 262 tests and
2,706 successful subtests in 20.355 seconds with exit 0. Failed subtests,
failures, errors, skips, expected failures, and unexpected successes are all
zero. Fresh user-driven runtime acceptance remains pending and is not
represented as a pass. The captured V160 in-battle state cannot
validate V161 because it restores old media and resident resources. Enter a
new Guardian battle from V161 media; confirm battle music, El-Regulus's facing
after each action, and ambient-music restoration after victory.

See [the V161 Guardian battle notes](docs/mass-driver-dungeon-3.22.md).

Historical V160 release facts follow unchanged.

## V160 release validation

The frozen V160 standalone image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v160.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v160.cue
```

The BIN is 696,130,848 bytes / 295,974 sectors with SHA-256
`8f37d9ddf3487abbd599ca2daaef10ed17006ef054107fcd36ab71197709f7d0`.
The 107-byte CUE has SHA-256
`051d53cc064e25b37dd5497e62f3fda4788d5a2080b0b0092256b2b89d61f6a9`.
The 251,375-byte manifest at `work/mass_driver_v160_stage/manifest.json` has
SHA-256
`c77dd76e5dff304fbb348a71dc9269cc01f87bc3f3b0651d8efb5891d1b46cf3`,
136 jobs, 169 replacements, 11,804,460 replacement bytes, 33 fields, and 66
directed edges. Its canonical-ID-sorted payload and framed aggregate hashes are
`06ad32f3a4296ae642eb2ce8a597dce3a00385c6a8a87da239d52dc520689e3b`
and `dedc1fc799dd7d092b8d2832770b4c185d33915b0084e10a19527b107d483b5b`.

The V159-to-V160 staged and exhaustive gameplay delta is canonical 1358 only.
All 169 packaged replacements extract exactly. All 4,147 FAT descriptors and
all 61 directory tables are unchanged, no payload relocates, and only canonical
1358 differs among 3,723 extractable files. Exactly one raw sector, LBA 196167,
changes by two user bytes / 46 raw bytes; the other 295,973 sectors are exact.
All 5,846 replacement sectors pass Mode2/Form1 EDC/ECC validation. An
independent build reproduces the BIN and manifest byte-for-byte. Target 376
remains 190,444 bytes and has SHA-256
`3badf3f1718522e5c798954017a96d104cb75713f4becf4eeeaa932b22350bd9`;
its 48,930-byte script has SHA-256
`bdbcfacf464841df93ba2a415aea03559273f715298e6ad98a189c29cfb3bcbc`.
Entity 23 stays at `(-465,-161)`, but its initializer is now no-facing with
OP18 X/Z operands `0x20/0x04`, effective reach `80x24`. This includes the live
stance `(-474.812835693359,-160.151718140625)`, yaw `0x0C00`, triangle 177,
and covers the complete audited walkable bank frontage X `[-485,-425]`.
Entity 23's action is byte-identical to V159.

Focused structural tests pass for the live stance, complete frontage, shallow
depth, unique selection, exact two-byte script delta, and unchanged action.
The authoritative suite passes 262 tests / 2,707 successful subtests in
22.097 seconds with every failure, error, skip, expected-failure, and
unexpected-success counter at zero. Static verification passes the PE,
manifest, import, embedded-resource, hash, and path-leak audits; the installer
is intentionally unsigned. Dynamic offline verification passes exact patching,
launcher creation and recovery, existing-build reuse, wrong-size/hash and
output-collision refusal, corrupt-patch rejection, source/sentinel preservation,
and cleanup. The emitted version-`1.6.0.0` Play launcher is 446,464 bytes with
SHA-256
`1cb8141cef86662157e1fc76e78370b8fab99bed45d2f89a88455e63a5004df0`.
Fresh user-driven runtime acceptance remains pending. Mount
V160, completely leave target 376, and re-enter it before testing; a state with
that field already resident retains the V159 initializer. After the Guardian
victory, press Cross/X across the visible panel front and confirm dialogue 19,
camera, sound, both sliding leaves, field-377 traversal, and persistent reload
state. Verify the pre-victory locked response and nearby independent controls.

See [the V160 west-panel frontage notes](docs/mass-driver-dungeon-3.21.md).

Historical V159 release facts follow unchanged.

## V159 release validation

The current standalone image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v159.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v159.cue
```

The BIN is 696,130,848 bytes / 295,974 sectors with SHA-256
`3bb06df72182f72beb2f25ccae2fa244a4a44aa198f9f3224a6262940b080927`.
The 107-byte CUE has SHA-256
`9b84d3513ae22b6415e005bf286d1b4637ea6d92a142a18056b3010229dbf6db`.
The 249,477-byte manifest at `work/mass_driver_v159_stage/manifest.json` has
SHA-256
`f6aa96575db50a4a90a39036c072e29e777c0d28d00841868d3d4ce762700020`,
136 jobs, 169 replacements, 11,804,460 replacement bytes, 33 fields, and 66
directed edges. Its canonical-ID-sorted payload and framed aggregate hashes are
`7a543d7ad665f7b987e0f96e9d954a4774bdce5aadc615f91a95ebc3ae2aa00d`
and `2d76bbd95c1d1a64aa7dd783c1fd689de9f55a59057bf13b9d596690dc9049ee`.

The V158-to-V159 prepared replacement delta is canonical 1358 only. Target 376
is 190,444 bytes with SHA-256
`9696899ce837eee05e727627a2f2f2fd2b8828e90f51ca071dab6ab4fffd6a6f`;
its 48,930-byte script has SHA-256
`ab4b7d9454a7fe1b41927fe239dbdde364b1fc692b43293bc15eaeb8856aaa4b`.
The script continuously polls the authorized leader from entity 0 script 1,
dispatches the shared entity-17 script-2 action at `z>=274`, uses interaction
operand `0x09` for the X fallback, and leaves entity 17 script 3 at STOP. The
existing field-384 return remains `(0,245)`, outside both entry paths.

Focused structural and regression tests pass for the exact worker bytes,
authorization guard, boundary cases including the live V158 stop point,
bounded on-foot transition, return-spawn exclusion, and deterministic field
and stage identities. All 169 packaged payloads match, the exhaustive FAT/raw
audit and 95/95 extended Mode2 sectors per image pass, the independent BIN and
manifest rebuild is byte-identical, the installer passes static and dynamic
offline verification, and the authoritative suite passes 262 tests / 2,702
successful subtests in 20.126 seconds with every failure counter at zero.

Fresh user-driven V159 runtime acceptance also remains pending. Load target 376
fresh from V159 media, authorize and open the north lift, then walk into it
without pressing X and confirm field 384 parameter 0 loads. Return through the
south personnel lift and confirm `(0,245)` does not bounce. Separately verify
locked dialogue 9 and the authorized transition through the reachable X
fallback. A state with target 376 already resident must leave and reload the
field, because changing the mounted CUE does not replace resident field code.

See [the V159 Defense Archive lift notes](docs/mass-driver-dungeon-3.20.md).

Historical V158 release facts follow unchanged.

## V158 release validation

The frozen standalone image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v158.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v158.cue
```

The BIN is 696,130,848 bytes / 295,974 sectors with SHA-256
`5b2b5aecd15c9aaf4bbcb7a3e555c391a22148f7645fc42fba53d4ad775accd4`.
The 107-byte CUE has SHA-256
`8f205b83f6e0232a6ea3fdda39027cd4728024b2305cd37a269f3d06b93c2955`.
The 249,070-byte manifest at `work/mass_driver_v158_stage/manifest.json` has
SHA-256
`c01792fae7de6ab3bdcdf214c2b16e30dca7101ebc31a92e45ad021bb56ffe7f`,
136 jobs, 169 replacements, 11,804,468 replacement bytes, 33 fields, and 66
directed edges. Its canonical-ID-sorted payload and framed aggregate hashes are
`ca18e714f9b02f5467ac7bdaf42b2567578088bf987ed84073e31233e2fd7130`
and `bed7f0270c73c209920d27eaea389e750b89c878a40a9ce04933af2f0d2b953e`.

The declared V157-to-V158 stage delta is canonical 2062. The exhaustive FAT
payload delta is 17, 22, and 2062. Exactly one of 4,147 descriptors changes:
canonical 2062/physical 2057 stays at LBA 221314 and changes size from
126,840 to 126,380 bytes. No descriptor relocates, all 61 directory tables are
unchanged, and exactly 3,720 of 3,723 extractable payloads are byte-identical.
Canonical 3722 and 3723 remain descriptor- and payload-identical. The FAT
changes by exactly two bytes, from SHA-256
`da14b400a03ecff0c71786a32db046bdeded595a27b93349d6cf4771c195a53d`
to `5a8bbb4ca9333f427b0674c18e7f1ebde55ac7c4d76c332acd968c8657459af6`.

The image keeps the same sector count and every later LBA. Exhaustive
same-LBA comparison changes only nine raw sectors: 31, 172926, 221314, and
221370-221375. All 169 replacements extracted exactly; all 5,846 replacement
sectors and the 5,849-sector audited union including logical delta and boot
passed MODE2/Form1 EDC/ECC. A second complete build was byte-identical.

Canonical 2062 is 126,380 bytes with SHA-256
`3ed0527021cc4d09ef8e6297dd335e09f435018dd305299dcf200ae3c8f1210c`.
Canonical 2063 remains 180,224 bytes with SHA-256
`201c89767211545e039422ab8791b48ff5a22f3f5383c4d0b234387a3c25aef7`.
The prepared and packed headers are 1,104 bytes with SHA-256 values
`9a2f2fb373a52b3d64e865db3356b67bbaa3fa977129aa5703d32ab646f80c52`
and `fb7dd25da1ff29aedaae013a1aaa057d3efccb816dbde46cb8dafd819ae8d6e9`.
The 13,868-byte models component remains SHA-256
`83ae54331684dd8d72f02bd3be1d86742f15caa17f9e6f525b3e101b2aad6203`;
the 3,593-byte script has SHA-256
`39f7a1cf08cbe8721ac39fa471a29b69a9e5ca1a944948c88cbd0f6bda73c020`;
the 4,448-byte dialogue component has SHA-256
`131de29fa2c10c2f3ffd927e2900cd892e7352987a08e3835d186688816a19f0`.

Static node 43 is now at `(197,439,108)`, yaw `0x0800`, with base centre
`(153.5,171.5)` and AABB X `133..174`, Y `-61..0`, Z `153..190`. Hidden
entity 16 adds a solid-only body at `(154,171)`, triangle 24; its `0x0B`
operand gives raw radius 22 and effective player contact 38. Entity 12 at
`(136,131)`, triangle 26, retains no-facing OP18 `0x01/0x01`, raw extent 2,
effective `18x18` reach, and supplies only Elly's repeatable one-page remark
that the console looks out of place among the other computer terminals.

Citan walks `(170,89)/32`, `(160,110)/32`, and `(136,131)/20`, ends direction
0, faces Elly for dialogue 35, then operates the same console under the held
inside-room 12-frame camera target `(145,160,-45)`, eye `(170,-80,-135)`.
The broad entity-13 story frontage, memory, chime, native door, all 18 flag-01
F5 waits, finite blocking operation, and guarded return remain intact.

The authoritative V158 validation run passed 262 tests / 2,693 successful
subtests in 20.844 seconds with exit 0 and zero failures, errors, failed
subtests, skips, expected failures, or unexpected successes. Fresh user-driven V158
console, collision, remark, route, operation, launch, and return acceptance
remains pending.

The preferred focused state is
`work/runtime_capture/near_final_v158_from_v108_vault1.sav`, 1,701,664 bytes,
SHA-256
`5be101fd30f7f6c1bcec66b363ca82e5f7cf5cccb7dbac232801648dfdd6f301`.
It mounts the exact V158 CUE once, has historical V108 field 377 resident, and
has target 728 absent for a cold load. Its resident FAT SHA-256 is
`5a8bbb4ca9333f427b0674c18e7f1ebde55ac7c4d76c332acd968c8657459af6`;
migration changes exactly two FAT bytes and nothing outside the FAT. Flags are
`0x0033`, bits 0/1/4/5 set and 6/7/12 clear; party is `01 06 FF`. Ask the player
to navigate and press controls; do not automate emulator input.

Historical V157 release facts follow unchanged.

## V157 release validation

The frozen standalone image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v157.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v157.cue
```

The BIN is 696,130,848 bytes / 295,974 sectors with SHA-256
`38ac9a31f62c172541db6361249f58822a3abccc91569a4bed56498c0518edeb`.
The 107-byte CUE has SHA-256
`91d48c195c99d90130d0244de8eb1688d1a3e86b050b01d663cdccf9e5c7ec34`.
The 246,356-byte manifest at `work/mass_driver_v157_stage/manifest.json` has
SHA-256
`0a8f9e99a471f7af841a42f5ff22a802dfb4282057bcafb80e3e245a34365345`,
136 jobs, 169 replacements, 11,804,928 replacement bytes, 33 fields, and 66
directed edges. Its canonical-ID-sorted payload and framed aggregate hashes are
`a306ed2adc0bbbaff3538f6c6226b72163ed258ccff9c0d0f37272f8a95726a2`
and `e478cae23d8f4260dc02eecc8e7be685220ea94fef022fb571f345dcaba14845`.

The declared V156-to-V157 stage delta is canonicals 2062 and 2063. The
exhaustive FAT payload delta is 17, 22, 2062, and 2063. Of 4,147 descriptors,
1,919 change: canonical 2062/physical 2057 shrinks from
`(221314,129268,file)` to `(221314,126840,file)`, and 1,918 later descriptors
relocate by two sectors. The other 2,228 tuples, every entry kind, and all 61
directory tables remain unchanged. Exactly 3,719 of 3,723 extractable payloads
are byte-identical.

The image shrinks by two sectors. The exhaustive same-LBA raw comparison has
60,328 changed and 235,646 unchanged common sectors, two removed sectors, and
none appended. Logical changes are confined to LBAs 31-38, 172926-172933, and
221314-221463. The 74,510-sector user-data tail at old LBA 221466 matches the
new tail at LBA 221464 exactly. All 169 replacements extracted exactly; all
5,846 replacement sectors and the patched boot sector passed MODE2/Form1
EDC/ECC. A second complete build was byte-identical.

Canonical 2062 is 126,840 bytes with SHA-256
`404c67c39b34f6a62fffde18d20580cab9a60d8ec2f28bbf4880cb056e6c5f46`.
Canonical 2063 is 180,224 bytes with SHA-256
`201c89767211545e039422ab8791b48ff5a22f3f5383c4d0b234387a3c25aef7`.
The prepared and packed headers are 1,104 bytes with SHA-256 values
`d947f233c17232e0b2c88e141295247e69f4fbf6482a41109104d56f69cfd719`
and `260c95291043fb71770d5beda5f9753da895c7b58813612f862209ede193c227`.
The 13,868-byte models component has SHA-256
`83ae54331684dd8d72f02bd3be1d86742f15caa17f9e6f525b3e101b2aad6203`;
the 3,562-byte script has SHA-256
`889bde3344c78874c8da995a463dc309e97d4bc472a72728516f67cad3535c56`.

V157 replaces V156's large overhead-arm prop with field 361 model 5, relocated
losslessly as compact standing keypad model 11. Static node 43 is at
`(187,439,30)`, yaw `0x0800`; the model's world AABB is X `123..164`, Y
`-61..0`, Z `75..112`, and its control-face centre is `(143.5,-50.5,84)`.
Optional archive entity 12 and Citan use `(136,53)`, triangle 28; entity 12's
no-facing OP18 `0x01/0x01` yields raw extent 2 and effective `18x18` reach.
Citan walks `(170,45)/32`, `(150,35)/32`, `(136,53)/20`, ends direction 0,
faces Elly for dialogue 35, then operates the same keypad under the held
12-frame camera target `(140,70,-45)`, eye `(300,-150,-135)`. The wall-console
story controller, dialogue, memory, chime, native door, all 18 flag-01 F5
calls, blocking operation, and guarded return remain intact.

The authoritative V157 structural run passed 262 tests / 2,693 successful
subtests in 21.558 seconds with exit 0 and zero failures, errors, failed
subtests, or skips. Fresh user-driven V157 terminal,
route, operation, launch, and return acceptance remains pending.

The preferred focused state is
`work/runtime_capture/near_final_v157_from_v108_vault1.sav`, 1,701,664 bytes,
SHA-256
`267dbe35a584cdd9733c46285e51f78b99392d3ff9a500f4c2e6f1aa516105f8`.
It mounts the exact V157 CUE, has historical V108 field 377 resident, and has
target 728 absent for a cold load. Its resident FAT SHA-256 is
`da14b400a03ecff0c71786a32db046bdeded595a27b93349d6cf4771c195a53d`;
migration changes exactly 1,933 FAT bytes and nothing outside the FAT. Flags
are `0x0033`, bits 0/1/4/5 set and 6/7/12 clear; party is `01 06 FF`. Ask the
player to navigate and press controls; do not automate emulator input.

Historical V156 release facts follow unchanged.

## V156 release validation

The frozen standalone image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v156.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v156.cue
```

The BIN is 696,135,552 bytes / 295,976 sectors with SHA-256
`9eb4dde57c0ed39ba504d50684b9bb63055812145de2474043e255ff150774a1`.
The 107-byte CUE has SHA-256
`5a47cbe3465ecdf08a20eaa7ef5deb1029d9581631d145f141bdc4c305d81707`.
The 245,085-byte manifest at `work/mass_driver_v156_stage/manifest.json` has
SHA-256
`ab46ece79e120786f8a18a56972623c5eee8e758a77b55776a4d526520fa95dc`,
136 jobs, 169 replacements, 11,807,356 replacement bytes, 33 fields, and 66
directed edges. Its payload and framed aggregate hashes are
`d7f8a08343e191a500f8844dfbd4a9b9b950eb1901fcb6bd495ef4b171f666d9`
and `9843b800b8a4039250d8eb0215dd322aede53e27ab0494bcf7ddf5efafd92665`.

The declared V155-to-V156 stage delta is canonical 2062. The exhaustive FAT
payload delta is 17, 22, and 2062 because canonicals 17 and 22 mirror the new
canonical-2062 size. Of 4,147 descriptors, 1,919 change: canonical
2062/physical 2057 grows from `(221314,126316,file)` to
`(221314,129268,file)`, and 1,918 later descriptors relocate by two sectors.
The other 2,228 tuples, all entry kinds, and all 61 directory tables remain
unchanged. Exactly 3,720 of 3,723 extractable payloads are byte-identical.

The image grows by two sectors. The exhaustive same-LBA raw comparison contains
60,335 changed common sectors, two appended sectors, and 235,639 unchanged
common sectors. Logically changed/new user data is confined to LBAs 31-38,
172926-172933, and 221314-221377; all 74,598 old tail user-data sectors match
at new LBA `+2`. All 169 final-BIN replacements extracted exactly; all 5,848
replacement sectors, all 80 logical-delta sectors, and the patched boot sector
passed MODE2/Form1 EDC/ECC. A second complete stage, final manifest, and BIN
rebuild matched byte-for-byte.

Canonical 2062 is 129,268 bytes with SHA-256
`8f4b0f2672fc61bda95b1a15860b4d4fe5561c3cc438824cbed0003c9671c1c9`.
Its prepared/packed headers are 1,104 bytes with SHA-256 values
`15830ac6f0b05296f0df613b853732c01429f902906b8c2527d370b4482b182c`
and `a4c56818db08d9d92cf62a5ec3fe82198956226ae01aa6456abcb61d7a13a5a3`.
Its 16,032-byte models component has SHA-256
`ac2e4645d3e139115ad4210767a59c88e4cb291a67dc4416fe9ab27baed3a5c1`;
its 3,562-byte script has SHA-256
`a27db09bedc55d12bc24ab9dac4360c067a802bd12b1dabe89df7e1bb8369aec`.

Exact field-373 model 7 is appended as model 11 and node 43 at `(88,0,168)`.
Citan walks through `(170,89)/32`, `(100,89)/32`, and `(57,63)/20`, stopping
on triangle 23 in direction 4. Reciprocal facing cues precede both dialogue-35
paths. After each dialogue wait, the paths converge at one 12-frame side
camera, target `(52,140,-116)`, eye `(527,140,-214)`, and one blocking call to
the 29-byte finite entity-3 script 23. Completion and world-map launch occur
only after its field-378 keypad animation, three sounds, waits, and STOP. All
18 entity-13 F5 calls retain flag `0x01`; memory, dialogue, chime, wall bank,
native door, and guarded return remain intact.

The authoritative V156 structural run passed 262 tests / 2,693 successful
subtests in 21.010 seconds with exit 0 and zero failures, errors, failed
subtests, or skips. Fresh user-driven V156 hanging-terminal visual,
mutual-facing dialogue, keypad operation, launch, and return acceptance remains
pending.

The preferred focused state is
`work/runtime_capture/near_final_v156_from_v108_vault1.sav`, 1,701,685 bytes,
SHA-256
`6eac212f38e4ee14ce73665fb8b90fc7971293034f7233646098fa85f7704681`.
It mounts the exact V156 CUE, has historical V108 field 377 resident, and has
target 728 absent for a cold load. Its resident FAT SHA-256 is
`f2aa2741a124de00ba8b3e87b6ff70b883278c217a9044e2b968c088cd3efe6a`;
migration changes exactly 1,933 FAT bytes and nothing outside the FAT. Flags
are `0x0033`, bits 0/1/4/5 set and 6/7/12 clear; party is `01 06 FF`. Ask the
player to navigate and press controls; do not automate emulator input.

Historical V155 release facts follow unchanged.

## V155 release validation

The frozen standalone image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v155.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v155.cue
```

The BIN is 696,130,848 bytes / 295,974 sectors with SHA-256
`0bc82870566778313dbdaba48ba8459ee88cc43a3b8834b22d4457ac688cbf11`.
The 107-byte CUE has SHA-256
`49a611cdda251c2f030adc8610e00ee7d6cab5a2057e30fb0f91d6e273aaa5ac`.
The 241,652-byte manifest at `work/mass_driver_v155_stage/manifest.json` has
SHA-256
`5eed39c013a4bb792ccc34bc130c67fb1fb45c27369d2d5bad9f0f511080456a`,
136 jobs, 169 replacements, 11,804,404 replacement bytes, 33 fields, and 66
directed edges. Its payload and framed aggregate hashes are
`2a3ab8521aa11c69f1e205749a60d3ed85af88b8802e0910e46a8ab967b9555f`
and `1e8912d367f4eb580f08069f64da7d49a5374c880a19115dd088e48cc2b1ed95`.

The declared V154-to-V155 stage delta is canonical 2062. The exhaustive FAT
payload delta is 17, 22, and 2062 because canonicals 17 and 22 mirror the new
canonical-2062 size. Exactly one of 4,147 descriptors changes, canonical
2062/physical 2057 from `(221314,126308,file)` to `(221314,126316,file)`;
entry kinds and all 61 directory tables remain unchanged. Exactly nine raw
LBAs change: 31, 172926, 221314, and 221370-221375, totaling 6,718 changed user
bytes and 8,144 changed raw bytes. All 169 final-BIN replacements extracted
exactly; all 5,849 audited replacement, changed, and boot sectors passed
MODE2/Form1 EDC/ECC validation. A second complete stage, final manifest, and
BIN rebuild matched byte-for-byte.

Canonical 2062 is 126,316 bytes with SHA-256
`6d7a84c43d702a79cb0481507fc9d4876a3e74b85b68ee236c0597b4e767a07c`.
Its 3,488-byte script has SHA-256
`01e2d0ff14babd2d59b51163c2d01d3a6f1eee2617238f1bc4aa0b1cb0c067f4`.
Entity 13 remains at `(-48,97)` on triangle 16, no-facing, with OP18 X/Z
operands `0x1C/0x02`, effective reach `72x20`, and region X `[-120,24]`,
Z `[77,117]`.

Dialogues 12 and 21 precede exact native chime bytes `74 50 80` at PC
`0x0454`, followed immediately by the memory fade. Memory dialogues 22-31 and
36 retain their subjective cameras. Under black the memory actors and grade
clear; the party returns under the held present camera and dialogue 32 supplies
the sole present response. The action then continues automatically, without a
second X press, to one whole-room target `(-13,106,-32)`, eye
`(-27,-767,-544)`, over 24 frames. Citan walks three bounded legs and remains
direction 7 at `(60,84)` beside native nodes 26/28 and models 3/4. Only the
leader turns toward him. The camera and east leaf remain held through dialogue
35, launch, and world-map unload. Dialogues 33 and 34 are authored but
unreachable; all 18 entity-13 F5 calls use flag `0x01`.

The authoritative V155 structural run passed 262 tests / 2,691 successful
subtests in 20.471 seconds with exit 0 and zero failures, errors, failed
subtests, or skips. Fresh user-driven V155 automatic-handoff, whole-room-camera,
right-terminal, launch, and return acceptance remains pending.

The preferred focused state is
`work/runtime_capture/near_final_v155_from_v108_vault1.sav`, 1,701,664 bytes,
SHA-256
`572a329ffb0c9f0e1771b253f13db84fda6adc4c54b104328d81e81f80ce824d`.
It mounts the exact V155 CUE, has historical V108 field 377 resident, and has
target 728 absent for a cold load. Its resident FAT SHA-256 is
`31413e0b788b3ed4e81ad8ffd23f0d6ed3067e0cc91be9eafd968760f837b847`;
migration changes only FAT byte `+0x3842` from `64` to `6C` and nothing outside
the FAT. Flags are `0x0033`, bits 4/5 set and 6/7/12 clear; party is `01 06 FF`.
Ask the player to navigate and press controls; do not automate emulator input.

Historical V154 release facts follow unchanged.

## V154 release validation

The frozen standalone image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v154.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v154.cue
```

The BIN is 696,130,848 bytes / 295,974 sectors with SHA-256
`5db4cbbf892338360f24cda664dc841b5a67f4b183819c205005635bc990fdc3`.
The 107-byte CUE has SHA-256
`e77c607981d6d7b935be42eab90443169cfda1e0caa4bfb6bb71628ff3c8d6f2`.
The 239,448-byte manifest at `work/mass_driver_v154_stage/manifest.json` has
SHA-256
`e0423870efc38045b98356d088fce6633cd918369554af17011e2f26e6e566d5`,
136 jobs, 169 replacements, 11,804,396 replacement bytes, 33 fields, and 66
directed edges. Its payload and framed aggregate hashes are
`1d37789cf911ac49a37eef9d9dfae31e2cd74c17d31ebc97d3e6409e9d95fe90`
and `8b9ec311d83f50592c7169877ff3cf7abb0a6664fbca7dabe4cde25aea754022`.

The declared V153-to-V154 stage delta is canonical 2062. The exhaustive FAT
payload delta is 17, 22, and 2062 because canonicals 17 and 22 mirror the new
canonical-2062 size. Exactly one of 4,147 descriptors changes, canonical
2062/physical 2057 from `(221314,126392,file)` to `(221314,126308,file)`;
entry kinds and all 61 directory tables remain unchanged. Exactly nine raw
LBAs change: 31, 172926, 221314, and 221370-221375, totaling 5,817 changed user
bytes and 7,189 changed raw bytes. All 169 final-BIN replacements extracted
exactly; all 5,849 audited replacement, changed, and boot sectors passed
MODE2/Form1 EDC/ECC validation. A second complete rebuild matched byte-for-byte.

Canonical 2062 is 126,308 bytes with SHA-256
`70b617b9d9b08c1a40a4b936598992a1a3cea92d648370d1790862af465bcd2c`.
Its 3,472-byte script has SHA-256
`a421fed38b3baeebc176cf664470073aa7606449bbdfc61ef3cfb1b4d643f30b`.
Entity 13 remains at `(-48,97)` on triangle 16, no-facing, with OP18 X/Z
operands `0x1C/0x02`, effective reach `72x20`, and region X `[-120,24]`,
Z `[77,117]`.

Dialogues 12 and 21 precede exact native chime bytes `74 50 80` at PC
`0x045C`, followed immediately by the memory fade. Memory dialogues 22-31 and
36 retain their subjective cameras. Under black the memory actors and grade
clear, a concise present camera restores the party, and dialogue 32 supplies
the sole present response. Dialogues 33 and 34 are authored but unreachable.
All 18 entity-13 F5 calls use flag `0x01`. Citan's route, native east door,
held arrival camera, launch, and field-617 return remain byte-identical.

The authoritative V154 structural run passed 262 tests / 2,689 successful
subtests in 20.451 seconds with exit 0 and zero failures, errors, failed
subtests, or skips. Fresh user-driven V154 chime, response, Citan, launch, and
return acceptance remains pending.

The preferred focused state is
`work/runtime_capture/near_final_v154_from_v108_vault1.sav`, 1,701,664 bytes,
SHA-256
`f61675cfc8113a806d2e5d1aef432ac3444cdca2f7aa242bcebac54296146046`.
It mounts the exact V154 CUE, has historical V108 field 377 resident, and has
target 728 absent for a cold load. Its resident FAT SHA-256 is
`59298ba90b3b7f9a8dddb2b5a2a21cd3320224bcc804e5b7afaf7f6ae0024ee1`;
the migration changes exactly one FAT byte `B8` to `64` and nothing outside
the FAT. Flags are `0x0033`, bits 4/5 set and 6/7/12 clear; party is `01 06 FF`.
Ask the player to navigate and press controls; do not automate emulator input.

Historical V153 release facts follow unchanged.

## V153 release validation

The frozen standalone image is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v153.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v153.cue
```

The BIN is 696,130,848 bytes / 295,974 sectors with SHA-256
`d5e50afa2f5288eeab63bf52a55f9d7167bbf48eef7bbead4fb5757dcff52b94`.
The 107-byte CUE has SHA-256
`c01e5dca6c9a3ed6405e7ba7eb3951e973856dbb585c13e0c93397e016070766`.
The 238,991-byte manifest at `work/mass_driver_v153_stage/manifest.json` has
SHA-256
`5e7ee65fd047484fcb5d378a1991ede34e89f5bdeab2079804df3c980fa8c3e0`,
136 jobs, 169 replacements, 11,804,480 replacement bytes, 33 fields, and 66
directed edges. Its payload and framed aggregate hashes are
`479f4359f1f6ff222abf959b176c8dea02ea6be63ba85119c886c71654a4fce5`
and `d64931dacb4e7d768d4a2bb3e66f7658cb3eaea4ddf98313eee43367dc9eda0a`.

The declared V152-to-V153 stage delta is canonical 2062. The exhaustive FAT
payload delta is 17, 22, and 2062 because canonicals 17 and 22 mirror the new
canonical-2062 size. Exactly one of 4,147 descriptors changes, canonical
2062/physical 2057 from `(221314,126444,file)` to `(221314,126392,file)`;
entry kinds and all directory memberships remain unchanged. Exactly nine raw
LBAs change: 31, 172926, 221314, and 221370-221375, totaling 6,759 changed user
bytes and 8,183 changed raw bytes. All 169 final-BIN replacements extracted
exactly; all 5,849 audited replacement, changed, and boot sectors passed
MODE2/Form1 EDC/ECC validation. A second complete rebuild matched byte-for-byte.

Canonical 2062 is 126,392 bytes with SHA-256
`9e5c5be2d6b858fb69375a7019224f2c253b0b7fb6aac955f2cb0d64175bb0c5`.
Its 3,435-byte script has SHA-256
`bb34a0a6e652feef3a1f32bc422229a39c518cbef291e1a2eb9a7e8605747a73`.
Entity 13 is at `(-48,97)` on triangle 16, no-facing, with OP18 X/Z operands
`0x1C/0x02`, effective reach `72x20`, and region X `[-120,24]`, Z `[77,117]`.
It accepts the captured `(-113,113)`/triangle-15 stance, the earlier
`(-15,113)`/triangle-20 stance, and both F2 positions; entity 12 begins one
coordinate beyond its east edge, and entity 14 remains disjoint.

The first interaction presents dialogues 12 and 21 before the fade and party
hide, uses a silent subjective reaction, and plays memory dialogues 22-31 and
36 only. Dialogues 32-34 remain byte-identical in the authored archive but are
unreachable. After dialogue 36, grade and camera cleanup happen under black
before the party is shown and control returns. All 17 remaining e13 F5 calls
use flag `0x01`; all 12 `(174,-102,-125)` eyes, hidden entity 19, visible
entities 17/18, authored dialogue, Citan route, native door, held camera,
launch, and return retain their V152 contracts.

The authoritative V153 structural run passed 262 tests / 2,689 subtests in
20.106 seconds with exit 0 and zero failures, errors, subtest failures, or
skips. Fresh user-driven V153 widened-console, coherent-memory, Citan, launch,
and return acceptance remains pending.

The preferred focused state is
`work/runtime_capture/near_final_v153_from_v108_vault1.sav`, 1,701,665 bytes,
SHA-256
`f0277210b6cb45786bf4d7466740c17239647f21f645fd9b0080dd57d8032dac`.
It mounts the exact V153 CUE, has historical V108 field 377 resident, and has
target 728 absent for a cold load. The captured console evidence is
`work/runtime_capture/user_v152_console_second_position.sav`, 1,884,059 bytes,
SHA-256
`d247400bb8a06745c834e9e760fe1a9c7994e8c51c5b1e5635cd07c41b420b1b`.
Its screenshot is
`work/duckstation/screenshots/Xenogears (Disc 2) 2026-08-10-20-12-47.png`,
2,028,365 bytes, SHA-256
`fae1ea2895c685ceb779a35ee80b7de5442ff088aa4da802166ca67a5f2b6ae7`.
The stable V151 failure copy remains
`work/runtime_capture/v151_hidden_controller_dialogue_abort.sav`, 1,752,967
bytes, SHA-256
`8bc81de760fda0ba5522c01b439a4aa152082bd8c48182e560c62f8747419717`,
as historical evidence only.
Ask the player to navigate and press controls; do not automate emulator input.

Historical V152 release facts follow unchanged.

## V152 release validation

The current frozen package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v152.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v152.cue
```

The BIN is 696,130,848 bytes / 295,974 raw sectors with SHA-256
`8dcb5e62607350832af926562a75dbb07b624ece41fd2edb7fee09d8b4b23cf4`.
The 107-byte CUE has SHA-256
`244144983c6e13c499122cf26eaeed59e62870de92567e0a7b959bd3d3865f65`.
The 237,913-byte manifest at `work/mass_driver_v152_stage/manifest.json` has
SHA-256
`fe7d6b8ecc2bb1af358757090227c2e8d58d7c666c5d88b8e485ec193eff8f41`.
It declares 169 unique replacements across 136 jobs totaling 11,804,532 bytes,
33 fields, and 66 directed edges. Its canonical-order payload SHA-256 is
`9542a7978bb3b0793939d305b0e9cc59275b4b81963def02575bc48ebc98683a`;
the framed aggregate is
`f1ea7670fa5617d9538e83383c2a0ef9abbdbdfd205c7bc000e8479a57368ea0`.
Direct FAT extraction matched all 169 staged payloads byte-for-byte. All 5,846
replacement sectors and the boot sector passed MODE2/Form1 EDC/ECC validation.

The declared/staged and exhaustive complete-FAT V151-to-V152 payload deltas
are both exactly canonical 2062. All 4,147 descriptor tuples, entry kinds, and
directory memberships are identical; 3,722 of 3,723 extractable payloads
remain byte-identical. Exactly one raw sector changes, LBA 221,372, within
canonical 2062's unchanged allocation. It contains 56 changed user bytes and
250 changed raw bytes after valid EDC/ECC regeneration. A second complete stage
and disc rebuild matched byte-for-byte.

Target 728's bundle is 126,444 bytes with SHA-256
`3cb22422077995d06e35097fe943de5e6de9dc658fcbbe15d3c7f94b0e3035f9`.
Its 3,482-byte decoded script has SHA-256
`b6e7023c38a03801ae00cd15b326954127330a3da58d5216725e073e142a8eb5`.
The 56-byte decoded script delta consists only of 20 F5 control bytes changing
from `0x00` to `0x01` and 36 operand bytes for 12 eyes changing from
`(14,58,-125)` to `(174,-102,-125)`. Entity 19 remains hidden at `(14,58)`;
all targets, authored dialogue, visible actors, entity-13 initializer, Citan
stage and walk, native door, arrival camera, graphics, and field-617 handoff
remain byte-identical to V151.

The captured V151 failure state
`work/duckstation/savestates/SLUS-00669_1.sav` is 1,752,967 bytes with SHA-256
`8bc81de760fda0ba5522c01b439a4aa152082bd8c48182e560c62f8747419717`.
At dialogue 21, hidden-owner F5 flag `0x00` caused WAIT_DIALOG to take OP_STOP,
leaving the camera and actors staged with bit 12 clear. V152's 20 flag-`0x01`
calls bypass that hidden-owner stop condition.

The authoritative V152 structural run passed 262 tests / 2,682 subtests in
20.391 seconds with exit 0. Fresh user-driven memory-dialogue, stable-camera,
native-door, Citan, held-arrival-camera, local-launch, and guarded-return replay
remains pending. Use
`work/runtime_capture/near_final_v152_from_v108_vault1.sav` for the focused
replay; it is 1,701,665 bytes with SHA-256
`882a1fa4090b5607b0574a08f64349d454a84edd3d04346b52e8c52278d55444`.
It mounts the exact V152 CUE, has historical V108 field 377 resident, and has
no target-728 payload resident; walk north so Central Control cold-loads from
V152. Ask the player to navigate and press controls; do not automate emulator
input.

The following V151 release-validation block is preserved as historical
evidence and remains unchanged.

## V151 release validation

The current frozen package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v151.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v151.cue
```

The BIN is 696,130,848 bytes / 295,974 raw sectors with SHA-256
`60cdf6e6ab9292908e7e20e0095da3dd6d34f89ce291d6a185fdbb1f07bf24a7`.
The 107-byte CUE has SHA-256
`18dd7904fb0b60a40258a1fdf03fa011ed17ad377d7c317d8f728aa060d1e3dc`.
The 237,578-byte manifest at `work/mass_driver_v151_stage/manifest.json` has
SHA-256
`a62687e0bc871410d6dd461e36ff79776d80a9b3b7ee268cc623dac8206775c0`.
It declares 169 unique replacements across 136 jobs totaling 11,804,532 bytes,
33 fields, and 66 directed edges. Its canonical-order payload SHA-256 is
`402453c4d884741f653ccaa29620fce59da7ad2bb19c7a7cf9b3db81fbc252c6`;
the framed aggregate is
`4b703993944fc5911a6e41003f714a95ed7ec2a594011b1b2dcf721346854777`.
Direct FAT extraction matched all 169 staged payloads byte-for-byte. All 5,846
replacement sectors and the boot sector passed MODE2/Form1 EDC/ECC validation.

The declared/staged and exhaustive complete-FAT V150-to-V151 payload deltas
are both exactly canonical 2062. All 4,147 descriptor tuples, entry kinds, and
directory memberships are identical; 3,722 of 3,723 extractable payloads
remain byte-identical. Exactly one raw sector changes, LBA 221,372, within
canonical 2062's unchanged allocation. A second complete stage and disc
rebuild matched byte-for-byte.

Target 728's bundle is 126,444 bytes with SHA-256
`094a504a9b7d51e7f0beefbf83df1729b7f582f8e932589a567ff70bc5fd936d`.
Its 3,482-byte decoded script has SHA-256
`f3c72efec276d82deb51dfdf9c18bab27db9207263aeface5cd3c9aeec3e476f`.
Only offsets `0x08CE`, `0x08D2`, and `0x08D3` change from V150, installing
entity 13's no-facing X/Z `0x06/0x01` rectangle. The Citan stage, walk, complete
finale action, arrival sequence, held camera, memory, actor/sprite payloads,
graphics, and field-617 handoff remain byte-identical.

The authoritative V151 structural run passed 262 tests / 2,682 subtests in
22.641 seconds with exit 0. Fresh user-driven center-console, memory,
native-door, Citan, held-camera, local-launch, and guarded-return replay remains
pending. Use
`work/runtime_capture/near_final_v151_from_v108_vault1.sav` for the focused
replay; it is 1,701,665 bytes with SHA-256
`c0a105bddcc3d2b28cc32ab3a710d07c84f411cd3f5f69fb8bf3aed7661619de`.
It mounts the exact V151 CUE, has historical V108 field 377 resident, and has
no target-728 payload resident; walk north so Central Control cold-loads from
V151. Ask the player to navigate and press controls; do not automate emulator
input.

The following V150 release-validation block is preserved as historical
evidence and remains unchanged.

## V150 release validation

The current frozen package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v150.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v150.cue
```

The BIN is 696,130,848 bytes / 295,974 raw sectors with SHA-256
`b28288e1a276b1a56dbe07ee9cb610ce85ee45473af1eeae18bb4898afeb915d`.
The 107-byte CUE has SHA-256
`d0c5ecd25396b40d09009bd0b2960e68e9453594fe377b801c096fdc2fd66e4e`.
The 237,297-byte manifest at `work/mass_driver_v150_stage/manifest.json` has
SHA-256
`2c3585a1a22ca46049597536e40759d00c7708a40756de591a5ac09e37578328`.
It declares 169 unique replacements across 136 jobs totaling 11,804,532 bytes,
33 fields, and 66 directed edges. Its canonical-order payload SHA-256 is
`988cd68d882303ceef30d7d8c7d2d45f488424b6fa01dbe6fe702320691afeab`;
the framed aggregate is
`b8d78bb4bc92f1e0e09efe80205712d7d97d96bf0efc5dfb1cbc7263c8a57392`.
Direct FAT extraction matched all 169 staged payloads byte-for-byte. All 5,846
replacement sectors and the boot sector passed MODE2/Form1 EDC/ECC validation.

The declared/staged V149-to-V150 delta is canonical 2062 only. The exhaustive
FAT payload delta is canonicals 17, 22, and 2062. One of 4,147 descriptor tuples
changes: canonical 2062 remains at sector 221,314 and shrinks from 126,524 to
126,444 bytes. Entry kinds and directory memberships are identical; 3,720 of
3,723 extractable payloads remain byte-identical. A second complete stage and
disc rebuild matched byte-for-byte.

Target 728's bundle is 126,444 bytes with SHA-256
`74badc327537c6fb5c5ca6c165f87a7c94a15f8de9cad944e402a9312bc65b42`.
Only the Launch Director and Systems Officer are visible in the memory; hidden
Miang supplies the POV and offscreen `MIANG` voice. Citan stages hidden behind
the east leaf at `(225,104)`, uses scoped F8 `0x0038` only through the first leg
to `(170,89)`, then follows `(100,89)/32`, `(60,84)/20`, and `(20,80)/20`.
The single arrival camera is held while native entity 15 script 4 opens the
leaf and through the dialogue, capsule launch, and world-map handoff.

The authoritative V150 structural run passed 262 tests / 2,681 subtests in
23.044 seconds with exit 0. Fresh user-driven subjective-memory, native-door,
Citan, held-camera, local-launch, and guarded-return replay remains pending.
Use `work/runtime_capture/near_final_v150_from_v108_vault1.sav` for the focused
replay; it is 1,701,665 bytes with SHA-256
`9704f618da1834db9e0ab9ea3223348006456bb762cc4401ada94075b06b6808`.
It mounts the exact V150 CUE, has historical V108 field 377 resident, and has no
target-728 payload resident; walk north so Central Control cold-loads from
V150. Ask the player to navigate and press controls; do not automate emulator
input.

The following V149 release-validation block is preserved as historical
evidence and remains unchanged.

## V149 release validation

The current frozen package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v149.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v149.cue
```

The BIN is 696,130,848 bytes / 295,974 raw sectors with SHA-256
`e5125cfcf4b9a876a6b605b0bbac8152ee60476fd989b4824050ca27cb7363de`.
The 107-byte CUE has SHA-256
`3b8b5e4cbcb0d2ec5e05a83f8ffea424adcd7a740c98b32674c1b8b7d61fb173`.
The 237,200-byte manifest at `work/mass_driver_v149_stage/manifest.json` has
SHA-256
`be30b9fd1974050c52992d98989486ddb17eed95a24986cfd130101ad94aeeb5`.
It declares 169 unique replacements across 136 jobs totaling 11,804,612 bytes,
33 fields, and 66 directed edges. Its canonical-order payload SHA-256 is
`86d4d110f86b4d1e6c95f97acd0adc0b9cdb3dcd1ed074035e304f6c007c0768`;
the framed aggregate is
`f7cdc39db4a4cd6b954dee33117995cf29f74df1c0719882bef79a8aaf35162e`.
Direct Xenogears-FAT extraction matched all 169 staged payloads byte-for-byte.
All 5,846 raw sectors occupied by replacements and the boot sector passed
MODE2/Form1 validation.

The declared/staged and exhaustive complete-FAT V148-to-V149 payload deltas are
both exactly canonical 2062. All 4,147 FAT descriptors, entry kinds, and
directory memberships are identical; 3,722 of 3,723 extractable payloads remain
byte-identical. A second complete stage and disc rebuild matched byte-for-byte.

Target 728's bundle is 126,524 bytes with SHA-256
`e70ce6317a634b447eb941a87407112306304d3086b89ba8bde0555470f191ea`.
Entity 13's facing-gated controller is at `(-4,118)` on triangle 19 with operand
`0x04` and 24-unit reach, aligned to header node 29/model 5 and the accepted F2
marker. Every entity-16 script slot points to STOP. Citan stages at `(170,89)`,
walks bounded legs through `(100,89)`, `(60,84)`, and `(20,80)`, and settles at
direction 7 before the updated final camera and dialogue.

The authoritative V149 full suite passed 262 tests / 2,681 subtests in 20.918
seconds with exit 0. Fresh user-driven centered-panel, silent-chest, natural
Citan entrance, local capsule launch, and guarded return replay remains pending.
Use `work/runtime_capture/near_final_v149_from_v108_vault1.sav` for the focused
replay; it is 1,701,664 bytes with SHA-256
`b044a007a583fc47e376571784dea534fa34f1cc5265b5cd5fdc75f06cefa6d5`.
Ask the player to navigate and press controls; do not automate emulator input.

The following V148 release-validation block is preserved as historical
evidence.

## V148 release validation

The current frozen package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v148.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v148.cue
```

The BIN is 696,130,848 bytes / 295,974 raw sectors with SHA-256
`c4bd92a10318d60bb4d2f2c9194eb049076124fedf9046a8922f6e3201ac80ad`.
The 107-byte CUE has SHA-256
`52d578682104510a1e36aa1577fbaef93f03e10353253e0e54e5a9ac3396237a`.
The 237,088-byte manifest at `work/mass_driver_v148_stage/manifest.json` has
SHA-256
`4bce2825fb5400843706c004848bf5108dd46eb232729b1dca56f3fb79457fa1`.
It declares 169 unique replacements across 136 jobs totaling 11,804,612 bytes,
33 fields, and 66 directed edges. Direct Xenogears-FAT extraction matched all
169 staged payloads byte-for-byte. All 5,846 raw sectors occupied by
replacements and the boot sector passed MODE2/Form1 validation.

The declared V147-to-V148 stage delta removes canonicals 1382, 1383, 1620, and
1621 and changes canonicals 2062 and 2595. The complete FAT payload delta is
17, 22, 1382, 1383, 1620, 1621, 2062, and 2595. All 4,147 entries preserve
their kinds and directory membership. Canonicals 3715 and 3723 are unchanged;
all 2,599 descriptor changes are accounted for. Of 3,723 extractable payloads,
3,715 remain byte-identical.

The authoritative V148 full suite passed 262 tests / 2,679 subtests in 19.733
seconds with exit 0. Fresh user-driven Central Control memory, full-size
apparition actor, Citan arrival, local capsule launch, and guarded return replay
remains pending. Ask the player to navigate and press controls; do not automate
emulator navigation.

The following V147 release-validation block is preserved as historical
evidence.

## V147 release validation

The current frozen package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v147.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v147.cue
```

The BIN is 696,387,216 bytes / 296,083 raw sectors with SHA-256
`63fd1ceafee04c0346acddb27a9df0724f07e5587de608e6c6dc56cfb4eb0881`.
The 107-byte CUE has SHA-256
`6e00bd12d06042f3bf3d8a983d6d44b6241763287767c6773ff14ad5aaba4f55`.
The 242,543-byte manifest at `work/mass_driver_v147_stage/manifest.json` has
SHA-256
`0d6f9cc688916817f267d4fc0c656e6cb0f85583f0af3abf4e2b962370a795b0`.
It declares 173 unique replacements across 138 jobs totaling 12,034,636 bytes,
35 fields, and 70 directed edges. Direct Xenogears-FAT extraction matched all
173 staged payloads byte-for-byte. All 5,959 raw sectors occupied by
replacements and the boot sector passed MODE2/Form1 validation.

The declared V146-to-V147 stage delta is exactly canonicals 1620 and 1621. The
complete FAT payload delta is canonicals 17, 22, 1620, and 1621; 17 and 22 are
regenerated FAT bookkeeping. All 4,147 entries preserve their kinds and
directory membership. Canonical 1620 resizes, canonical 1621 moves and resizes,
and 2,328 later files plus 31 metadata aliases shift backward 162 sectors,
accounting for all 2,361 descriptor changes. Of 3,723 extractable payloads,
3,719 remain byte-identical.

The authoritative V147 full suite passed 262 tests / 3,326 subtests in 43.82
seconds with exit 0. Fresh user-driven compact-room entrance, console, Citan
route, dialogue, panel beat, launch, and return replay remains pending. Ask the
player to navigate and press controls; do not automate emulator navigation.

The following V146 release-validation block is preserved as historical
evidence.

## V146 release validation

The current frozen package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v146.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v146.cue
```

The BIN is 696,768,240 bytes / 296,245 raw sectors with SHA-256
`47d4ef0586189e4489f4ef2a7b0e6f870024c4b050b87a8ccf1e44b5d9f1fb71`.
The 107-byte CUE has SHA-256
`4e6f116b42c848d39d2513e7c4fcac76f4cc03b605a712771c5e7d050ed88192`.
The 242,367-byte manifest at `work/mass_driver_v146_stage/manifest.json` has
SHA-256
`f3de56cf394ebe39505a9c80afde7ef9713bd280c1363d4d048b55cda5355712`.
It declares 173 unique replacements across 138 jobs totaling 12,365,936 bytes,
35 fields, and 70 directed edges. Direct Xenogears-FAT extraction matched all
173 staged payloads byte-for-byte. All 6,121 raw sectors occupied by
replacements and the boot sector passed MODE2/Form1 validation.

The declared V145-to-V146 stage delta is exactly canonicals 1620, 2062, and
2063. The complete FAT payload delta is canonicals 17, 22, 1620, 2062, and
2063; 17 and 22 are regenerated FAT bookkeeping. All 4,147 entries preserve
their kinds and directory membership. The three resized gameplay descriptors
and 1,917 later nonempty sector-shift descriptors account for all 1,920 changed
descriptor tuples; 3,718 of 3,723 extractable payloads remain byte-identical.

The authoritative V146 full suite passed 263 tests / 3,375 subtests in 49.10
seconds with exit 0.
Fresh user-driven Central-Control handoff and complete field-507 finale replay
also remain pending. Ask the player to navigate and press controls; do not
automate emulator navigation.

The following V143 release-validation block is preserved as historical
evidence.

## V143 release validation

The current frozen package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v143.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v143.cue
```

The BIN is 696,862,320 bytes / 296,285 raw sectors with SHA-256
`085be8ee0efef9c4b18385c861f52985a3d7ae6bf456c02b97d23a377eb0b320`.
The 107-byte CUE has SHA-256
`ddf8b7d073163e1546ed2bcedf26514e30e43336e2e4d2491a921b6347dfe3a6`.
The 241,523-byte manifest at `work/mass_driver_v143_stage/manifest.json`
has SHA-256
`73984157c2d66e6fe1c8385c3bebc5fbfecde6af69a2fdc32bc8aceaa94c4241`.
It declares 173 unique replacements across 138 jobs totaling 12,446,596
bytes, 35 fields, and 70 directed edges. Direct Xenogears-FAT extraction
matched all 173 staged payloads byte-for-byte. All 6,161 raw sectors occupied
by replacements passed MODE2/Form1 EDC/ECC checks.

The declared/staged V142-to-V143 replacement delta is exactly canonical IDs
29, 1620, and 1621. Generated FAT bookkeeping canonicals 17 and 22 also change
because archive and disc-layout relocation changes their recorded locations;
they add no gameplay content. Canonical 29 is 13,596 bytes with SHA-256
`b2feb89ac7031b5007aa137e2711ca0ab2f5b48efbe0d55ee040f98f81192816`.
Its aligned item-name entry is 2,470 bytes and the El-Regulus command-name
entry begins at even offset `0x51A8`.

Target 507 canonical 1620 is 166,096 bytes with SHA-256
`8714fe87a28273c42167bd30c89a71a87e21dab0f2579f680e2e9e798297812b`.
Its 5,499-byte script has SHA-256
`2dca3f1da9115bede0010fd480ec88fe8de8e3207da143856d3123faa84bea68`.
Canonical 1621 is 374,784 bytes with SHA-256
`f4b06ecad813330a5085afb4fa85d491c9b3e6ddd295e9ac6c410e891182f900`.

The authoritative V143 full suite passed 258 tests / 3,322 subtests in 44.29
seconds without failures, errors, skips, or expected failures. Fresh user-driven
V143 Guardian-menu and target-507 runtime acceptance remains pending. Mount
V143, enter a new Guardian battle, and confirm the command menu
opens, cancels, reopens, and continues through an attack. Then completely
reload target 507 and confirm the exact field-507 Krelian/Ouroboros laboratory,
native reciprocal east door, entity-7 apparatus interaction, entity-10
mechanism, one capsule launch, and repeat dispersal response. Ask the player to
navigate and press controls; do not automate emulator navigation.

## Historical V142 release validation

The historical V142 package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v142.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v142.cue
```

The BIN is 696,709,440 bytes / 296,220 raw sectors with SHA-256
`1e16bffd110c048c6c40085a176536cab5cb4b76541dd7f42974c582a3adfbdd`.
The 107-byte CUE has SHA-256
`0fb2e62fe4030d12d78db45969b28b0417d294493553284a7c48edd9a17edb8a`.
The 241,290-byte manifest at `work/mass_driver_v142_stage/manifest.json`
has SHA-256
`cc66f4fc59e7f86bb3c1e422c246710a158a05e165e33d0bf6fb3a00f088ce42`.
It declares 173 unique replacements across 138 jobs totaling 12,314,508
bytes, 35 fields, and 70 directed edges. Direct Xenogears-FAT extraction
matched all 173 staged payloads byte-for-byte. All 6,096 raw sectors occupied
by replacements passed MODE2/Form1 EDC/ECC checks; the separately audited
patched boot sector at raw LBA 172938 passed as well.

The complete V141-to-V142 FAT delta is exactly canonical 1358; no descriptor or
other extractable payload changes. Target 376 remains 190,452 bytes and now has
SHA-256
`5e2996b1c7f9d2bce2b8e3e30d3b2e1ff8f6116125dbbe3f29b2bb0b9a849514`.
Its 1,104-byte, 44-record prepared header is
`62e0fd0d2b4512971a0ee1d81e06547adc0bba55fc29249dc33210de10bd4daf`;
the packed header is
`f1d54532db4bdcbcda53ee2583fbe4a0e95de684bd012a2aca02cdb79a2f0897`.
The 48,943-byte script contains 47,019 bytes of bytecode, 28 entities, and has
SHA-256
`daee4fdd6ee9cf7e127d28a6c6e613aea4100190b3c269ef9cc5491c155927da`.
Canonical 1359 remains 239,616 bytes with SHA-256
`969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd`;
canonical 2476 remains 8,212 bytes with SHA-256
`3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d`.

The native facing-gate bytes are `F8 03 04 00`. Authorization entity 13 and
entities 21 through 26 use bound operand `0x04`, giving 24-unit effective
reach; entity 20 remains `0x24`, giving 88-unit reach. Entity 25 now centers at
`(-260,105)`. Its accepted live stance is `(-260.214,92.209)`, yaw `0x0C00`,
triangle 196; the rejected empty-floor stance `(-221.548,55.813)`, yaw
`0x0800`, triangle 197 lies outside every interaction region.

Models, field graphics, dialogue, video/background resources, the shared arcade
atlas, Missile worker bodies and PCs, and the shared entity-21 arcade action are
byte-identical to V141. The authoritative V142 full suite passed 257 tests /
3,280 subtests in 41.10 seconds. Fresh user-driven v142 runtime replay remains pending. Mount v142,
completely leave target 376, and re-enter it before validating every console
from its visible operator side, including the rejected and accepted entity-25
stances. Then replay both arcade games and verify all V141 projectile, cleanup,
overlay, party-sprite, and field-return behavior. Ask the player to navigate and
press controls; do not automate emulator navigation.

## Historical V141 release validation

The current package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v141.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v141.cue
```

The BIN is 696,709,440 bytes / 296,220 raw sectors with SHA-256
`65e10899e8bda43b423ad31c0266cb8839dd247c47cfe6498f699f3a6c387aba`.
The 107-byte CUE has SHA-256
`217a705a47d680ddeb147b744561330e21408be84c22c62c74edbae7aea7e6e3`.
The 240,275-byte manifest at `work/mass_driver_v141_stage/manifest.json`
has SHA-256
`d4f755d3b594facda6bb240244db1e75d772db90d6b81f2b944e328ca7a44c0d`.
It declares 173 unique replacements across 138 jobs totaling 12,314,508
bytes, 35 fields, and 70 directed edges. Direct Xenogears-FAT extraction
matched all 173 staged payloads byte-for-byte. All 6,096 raw sectors occupied
by replacements passed MODE2/Form1 EDC/ECC checks; the separately audited
patched boot sector at raw LBA 172938 passed as well.

Relative to v140, the staged/declared delta is canonical 1358 only. Target
376's 190,452-byte bundle has SHA-256
`4e183eb7ccb93fb17708fa09fdc7b31934b14e0f4f71d5d1fea07308c2b62d0a`.
Its 1,104-byte, 44-record prepared header remains
`2e85b169f0401db16d126d5e14d66efb34fda326a164b33664b8e0a33057724f`;
the packed header is
`45ea04268fa4f554c24ca1693f1b8883cc479d27f865141f87ed1551c7cfed64`.
The 48,943-byte script contains 47,019 bytes of bytecode, 28 entities, and has
SHA-256
`56b46a504df09c7dabbf007810ec37e0f80746ccdaf8be63046514f745d2ef49`.
Canonical 1359 remains 239,616 bytes with SHA-256
`969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd`;
canonical 2476 remains 8,212 bytes with SHA-256
`3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d`.

V141 draws the existing `interceptor` head with two foreground-only strips,
retains exactly three hot, bright, and dim exhaust cells, and uses the
`explosion` tile only after detonation. Twenty-eight cycle boosters provide a
904-cycle soft budget. The largest reachable worker maximum is 441 operations;
e24's deliberately unconstrained compositor contract reaches 871, still below
the budget, and maximum call depth remains three.

The final full-suite result is 257 automated tests / 3,286 subtests without
failures, errors, skips, or expected failures.

Fresh user-driven v141 runtime replay remains pending. Mount v141, completely
leave target 376, and re-enter it before checking the distinct player head,
exactly three exhaust cells, explosion graphics only after detonation, three
retained red prior-head points plus each white enemy head, smooth concurrent
motion, and zero residue after cleanup. Then verify pause/resume, wave clear,
clean exit, both arcade games, party sprites, compass, portraits, menus,
dialogue, and field return. Ask the player to navigate and press controls; do
not automate emulator navigation.

## Historical V140 release validation

The current package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v140.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v140.cue
```

The BIN is 696,709,440 bytes / 296,220 raw sectors with SHA-256
`fdcdf41773183801c1d73fa9bab2f4e19bf713c280b1aabe7d052856cf73ef8c`.
The 107-byte CUE has SHA-256
`ac0ae9f780974a5e8f71d21c44ba963928f9ce4424838e0b4ca0ecf62507d763`.
The 239,797-byte manifest at `work/mass_driver_v140_stage/manifest.json`
has SHA-256
`9868e6b95ee11c48808c15b30d73ac60768d2488176541b8856fb73fa13aa31d`.
It declares 173 unique replacements across 138 jobs totaling 12,314,212
bytes, 35 fields, and 70 directed edges. Direct Xenogears-FAT extraction
matched all 173 staged payloads byte-for-byte. All 6,096 raw sectors occupied
by replacements passed MODE2/Form1 EDC/ECC checks; the separately audited
patched boot sector at raw LBA 172938 passed as well.

Relative to v139, the staged/declared delta is canonical 1358 only. Target
376's 190,156-byte bundle has SHA-256
`9a9ace17e9113d6a64000b71fcaed1c1d4207ec5f2e871f7f77a26927c9ca558`.
Its 1,104-byte, 44-record prepared header remains
`2e85b169f0401db16d126d5e14d66efb34fda326a164b33664b8e0a33057724f`;
the packed header is
`eaa4229e1da964747c228532d883df39ef5ace214edb56fa62cbb84e49b0622e`.
The 48,679-byte script contains 46,755 bytes of bytecode, 28 entities, and has
SHA-256
`1f68fcad46f1619aec237f17fc1ec5d5cc126effd0a128e2cbc9b80c1c93dd22`.
Canonical 1359 remains 239,616 bytes with SHA-256
`969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd`;
canonical 2476 remains 8,212 bytes with SHA-256
`3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d`.

The v139 bounded-tail and v138 background-safe worker renderer remain. V140
uses compact five-cell cross-shaped blasts: center, center plus four cardinal
neighbors, hold, then center-only contraction and complete cleanup. Missile
Command uses retail explosion cue `0x51`; Nuke retains crash cue `0x77`.
The largest audited worker path is 432 operations under the 1,024-opcode
guard; the worker soft budget is 648 and maximum call depth is three.

The final full-suite result is 257 automated tests / 3,278 subtests
without failures, errors, skips, or expected failures. Fresh user-driven v140
runtime replay remains pending. Mount v140, completely leave target 376, and
re-enter it before checking compact five-cell explosions, Missile cue `0x51`,
exactly three player blocks, three retained red prior-head points plus each
white enemy head, smooth concurrent motion, and zero residue after cleanup.
Then verify pause/resume, wave clear, clean exit, both arcade games, party
sprites, compass, portraits, menus, dialogue, and field return. Ask the player
to navigate and press controls; do not automate emulator navigation.

## Historical V139 release validation

V139 is preserved in
[its frozen bounded-tail note](docs/mass-driver-dungeon-3.00.md) and the
`v139_release_delta` metadata block. Its package identities, bounded-tail
contract, and pending runtime status remain historical and unchanged.

## Historical V138 release validation

V138 is preserved in
[its frozen background-safe rendering note](docs/mass-driver-dungeon-2.99.md)
and the `v138_release_delta` metadata block. Its package identities and
canonical-1358-only delta remain historical and unchanged.

## Historical V137 release validation

The superseded v137 package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v137.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v137.cue
```

The BIN is 696,709,440 bytes / 296,220 raw sectors with SHA-256
`4900748c648dd61d6b966d403a3606fccc50d5ae1051cb3573ba4939a98f0ba1`.
The 107-byte CUE has SHA-256
`4d4e68176b3a5acc1acb5e33552866e81ed75d2af053343269c8a2b8e7a582b7`.
The 238,773-byte manifest at `work/mass_driver_v137_stage/manifest.json`
has SHA-256
`a2487e9a452c397d22952096f9f343a62f70ca12cd360a4bf224d6b18988b42d`.
It declares 173 unique replacements across 138 jobs totaling 12,314,004
bytes, 35 fields, and 70 directed edges. Direct Xenogears-FAT extraction
matched all 173 staged payloads byte-for-byte. All 6,096 raw sectors occupied
by replacements and the patched boot sector passed MODE2/Form1 EDC/ECC checks.

Relative to v136, only declared canonical 1358 changes. Target 376's
189,948-byte bundle has SHA-256
`1677755fa9440200b6179e621cfd302e3c3dd63a447e48187fb5f5fb8935e158`.
Its 1,104-byte prepared header remains
`2e85b169f0401db16d126d5e14d66efb34fda326a164b33664b8e0a33057724f`;
the packed header is
`fe657022b5fea258271e984038ea1824290613a049c4fcdda6df02499ffde777`.
The 48,494-byte script contains 46,570 bytes of bytecode, 28 entities, and has
SHA-256
`d64bfbd2e84aa93f46c7b46af875912c72e5663db1fa636edee703cea1d3537b`.
Canonical 1359 remains 239,616 bytes with SHA-256
`969408b6df78197c0b3c6565cd6d0e654e7c801ad4df46b6e4ef214b03c1f6dd`;
canonical 2476 remains 8,212 bytes with SHA-256
`3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d`.

Finite script-1 workers on entities 16-20 and 22-27 now simulate and render one
complete Missile Command frame while the entity-21 terminal action handles
input with one outer wait. Firing adds no extra wait. Lifecycle requests and
acknowledgements order setup, pause, resume, wave clear, and teardown. The
largest audited worker path is 820 operations under the 1,024-opcode guard;
the worker soft budget is 904 and maximum call depth is three. The v136
single-base ammo, trail, scoring, quota, persistence, safe y384 atlas, and
field-363 contracts remain unchanged.

All 257 automated tests / 3,204 subtests passed without failures, errors, skips,
or expected failures. Fresh user-driven v137 runtime replay remains pending.
Mount v137, completely leave target 376, and re-enter it before checking firing
smoothness, concurrent motion, worker pause/resume and teardown, both arcade
games, Elly, compass, portraits, menus, dialogue, and field return. Ask the
player to navigate and press controls; do not automate emulator navigation.

## Historical V136 release validation

The superseded v136 package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v136.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v136.cue
```

The BIN is 696,714,144 bytes / 296,222 raw sectors with SHA-256
`cfd7be90381a002b05d61139c1b897219712b3d513a185f94ed1e24da46458eb`.
The 107-byte CUE has SHA-256
`ee4ec03e1f8e8eb12f283094e8629ba9dbfad27e204af92b7f568d823e66283e`.
The 236,648-byte manifest at `work/mass_driver_v136_stage/manifest.json`
has SHA-256
`44b8fb55f2db69637d91c22710dba4d3878493db8b18014272a31a18a53640aa`.
It declares 173 unique replacements across 138 jobs totaling 12,316,668
bytes, 35 fields, and 70 directed edges. All 173 payloads were extracted
directly from the finished BIN and matched the manifest byte-for-byte. The
patched cold-boot sector passed its MODE2/Form1 EDC/ECC audit.

Relative to v135, only declared canonicals 1358 and 2476 changed. Target 376's
192,612-byte bundle has SHA-256
`dd9039414e8fd947e4ed085746961d9042b218117e214abc37a6ddeea0404a8a`.
Its 1,104-byte prepared header has SHA-256
`2e85b169f0401db16d126d5e14d66efb34fda326a164b33664b8e0a33057724f`;
the packed header has SHA-256
`24b4f0fd507febec98afaf05aba92ff911196b0844304b9cf8c43b1fd8229a90`.
The 50,860-byte script contains 48,936 bytes of bytecode and has SHA-256
`718dce46a2d590d4e3e98f0d7315fc03fd2e91f8b27a8015cedd131c2bf166d2`.
The 8,212-byte atlas has SHA-256
`3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d`.

The atlas now loads at `x=640..703`, `y=384..447`, the enforced empty third
party slot. This corrects v135's overwrite of Elly at y256 while staying below
Emeralda at y320, above the compass at y448, and left of portrait and dialogue
scratch space. The pixel payload is unchanged from v135; only the TIM load y
changed. Target 363 is byte-identical to v135 and retains the accepted authentic
station, native row-488 door assets, inert wall panel, and no field-365 route.

Missile Command now uses a 2600-style single center base, not an exact full
clone: Cross fires a 10-round loaded set backed by 20 underground ABMs, and a
base hit loses only the loaded set. Up to three center shots and three chain
fireballs can coexist. The hot/bright/dim three-cell trail is project-specific.
The maximum 22-missile quota begins at wave 19 and repeats thereafter; the
displayed wave and best-wave record cap at 31. Arcade scoring and bonus cities
remain.

All 257 automated tests / 3,279 subtests passed without failures, errors, or
skips. Fresh user-driven v136 runtime replay remains pending. Mount v136,
completely leave target 376, and re-enter it before checking the arcade, Elly,
compass, portraits, menus, dialogue teardown, and transitions. Ask the player
to navigate and press controls; do not automate emulator navigation.

## Historical v135 release validation

The superseded v135 package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v135.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v135.cue
```

The BIN is 696,711,792 bytes / 296,221 raw sectors with SHA-256
`f124100fc5fec53d9d82ed7e9efb5cedca919a161ae437099f44e6b846d4491b`.
The 107-byte CUE has SHA-256
`d66eca6a83ec53c9d32243b098d8a56b591dd658244c1d0f0692677083b6c70a`.
The 236,056-byte manifest at `work/mass_driver_v135_stage/manifest.json`
has SHA-256
`f841abf690eb47557ab003931c256c69544b03503ebc48faa1816619f02b6afb`.
It declares 173 unique replacements across 138 jobs totaling 12,316,324
bytes. All 173 were extracted directly from the finished BIN and matched the
staged payloads byte-for-byte.

Target 363's 21,352-byte bundle has SHA-256
`bc450a6117ebd3e4dc60eb6bc0a39c4175ebac77dbbcf193c384dd9829937c3b`.
Its 832-byte prepared header remains
`c5dd92f8b149eee4e8287b622d0cd70c730c82eb796115dc0642464d2df6a182`;
the 9,904-byte model archive is
`b756da8c20274bf8a6c3c136eafe63c73a830566b0c9aaefb56c5bf7db4f9d20`;
the 1,995-byte script remains
`1d11ad410628d1d7e1e64a5885144f8529171188cb6e626bafcc2e79af688f30`;
and the 106,496-byte graphics component is
`0f90479813717a6aa250691ec85f02b2c3fb009aed9adbab003212a80bda2561`.

Relative to v134, only declared canonicals 1332 and 1333 changed. The v135
station keeps identical geometry, triangle order, and sampled 16-bit colors
through a lossless index remap into row 485. Native row 488, native models 0
and 1, and their 1,118-byte door texture footprint remain byte-identical. No
complete standalone station-palette row is installed.

Structural and package checks pass. Fresh v135 emulator replay remains
pending. Mount v135, fully leave field 363, and walk back in yourself before
judging the terminal or transition. Verify the authentic station, front Cross
dialogue, solid collision, inert wall panel, and absence of a field-365 route.
Then fully reload target 376 before checking the inherited arcade and video
terminal. Ask the player to navigate and press controls; do not automate
emulator navigation or interaction.

## Historical v134 release validation

The superseded v134 package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v134.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v134.cue
```

The BIN is 696,711,792 bytes / 296,221 raw sectors with SHA-256
`3e57ed1f5656820115cf5fe843e0869e2671ce9840c301ca378a578f122490fe`.
The 107-byte CUE has SHA-256
`bc4906c0eee984d2f225658538707f9a0f6ee66d1f2776840b5cb97b836947ac`.
The 236,040-byte manifest at `work/mass_driver_v134_stage/manifest.json`
has SHA-256
`0e5e7525bd09e18d5e7b6f276088b24961421c6f3dc0e053c4214243d937b188`.
It declares 173 replacements across 138 jobs totaling 12,316,324 bytes.

Target 363's 21,352-byte bundle has SHA-256
`1eeccea9de3a5636db2c4cfebf74a474ff5bc5f511b2ac1c1d19f66b158b87b9`.
Its 832-byte prepared header has SHA-256
`c5dd92f8b149eee4e8287b622d0cd70c730c82eb796115dc0642464d2df6a182`.
The 9,904-byte model archive has SHA-256
`55a292f2a6a174e50cb2a2487bc827ff4a9d98070a095534d000b8325e8d5509`.
The 1,995-byte script has SHA-256
`1d11ad410628d1d7e1e64a5885144f8529171188cb6e626bafcc2e79af688f30`.
The 106,496-byte graphics component has SHA-256
`c6a3f288c071c211bcbef4b0b32ca2f4e082eaa0a73d92275dc615bb8292adfc`.

The station is the existing target-727 Zeboim computer asset, not a newly
modeled substitute. In this frozen v134 package its 5,120-byte atlas and
512-byte palette were copied byte-for-byte, while native door indices and
colors were remapped. V135 supersedes that allocation:
it preserves native row 488, models 0/1, and their texture bytes exactly while
retaining identical station geometry, triangle order, and sampled 16-bit
colors through a lossless station-index remap. Target 365 is absent from the
active route and replacement set in both revisions.

Relative to the rejected v133 package, only declared canonicals 1332 and 1333
change: field 363 grows from 20,316 bytes / `1ecd5abe...aa356b` to 21,352 bytes /
`1eeccea9...8b87b9`, while its 106,496-byte graphics changes from
`0d561e48...1965` to `c6a3f288...2adfc`. The 138 jobs, 173 replacements,
35 route fields, and 70 directed edges are otherwise unchanged.

Target 376's 192,268-byte bundle has SHA-256
`3b2f65ba5d177e8bf751078781d34808454c742ffde85ec8047e011bd8fdb9fd`.
Its 1,104-byte prepared header has SHA-256
`2e85b169f0401db16d126d5e14d66efb34fda326a164b33664b8e0a33057724f`.
The 50,560-byte script bundle contains 48,636 bytes of bytecode and has
SHA-256
`4a0adcc2e7330cfbe320febd806acec003ce4a83c9d24b37e576669176022d81`.
The 7,200-byte dialogue block has SHA-256
`3eadb9b8fafc2b1fa36c8325a604aac6d8e91e519ad317a2d4bc42988b92289d`.
The 8,212-byte shared arcade atlas has SHA-256
`9c3516b554d6494ce70e75b2059a3114c3c30bfbd84284c8cd279eb473d0b4c2`.

All 173 declared replacements were extracted back out of the finished BIN and
matched the manifest size and SHA-256 exactly. The raw BIN length is divisible
by 2,352 and its patched cold-boot sector has the audited SHA-256
`79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc`.

Use a cold boot, or fully leave target 376 and re-enter it from v134 media.
Cross at the southeast computer must open exactly `Arcade Games`,
`Video Disk`, and `Leave`. `Arcade Games` must open exactly `Play NUKE`,
`Missile Command`, and `Back`; `Back` must restore the root prompt. Missile
Command must display Square/Cross/Circle battery fire and Triangle pause, three
10-missile stocks, overlapping fireballs and chain reactions, attackable and
rearming batteries, the rev-3 quota curve, arcade multiplier and bonuses,
banked bonus cities, and endurance past wave 10. The v129/v130 record migration
must preserve NUKE score/level and the four-letter pilot without writing story
progression.

Structural tests, all 257 automated tests, and package extraction pass. A
user-driven v134 reload of field 363 confirmed the authentic station visual,
its front Cross dialogue, and no door transition. Collider coverage, the inert
wall panel, and absence of field 365 remain structurally verified.
The complete v130 terminal loop and v129 NUKE/video runs remain historical
evidence, not validation of the rewritten Missile Command gameplay loop.

`output/TEST_V131_MISSILE.cmd` remains the frozen historical v131 Missile
Command launcher. The main launcher mounts the current V161 CUE.

## Historical v129 release validation

The combined v129 package is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v129.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v129.cue
```

The BIN is 697,001,088 bytes / 296,344 raw sectors with SHA-256
`55b42becc2b1ab87805b7f318531704dd879000df0251f50e2b933c9c22d7062`.
The 107-byte CUE has SHA-256
`8fdb017ed4dfe61349a9dab7ba3339978bd508ed8e5f42cda94f64253e25c48b`.

Use a cold boot, or fully leave target 376 and re-enter it from v129 media
before testing. At the southeast computer, Cross must open exactly `Play NUKE`,
`Video Disk`, and `Leave`; selecting `Leave` must close the menu and restore
control without launching Nuke, checking inventory, or playing video. At the
visible national-security terminal, Cross from approximately `(435,168)` must
open record dialogue 16, while the retired `(350,175)` floor hotspot remains
silent. Nuke must show its framed board, regular compact font, two-row HUD, and
centered intro, pause, game-over, and four-letter name-entry panels. Start must
not be advertised or required: Cross launches, pauses/resumes during flight,
retries, advances name slots, and saves; Circle backs up or exits. Confirm the
onscreen labels `LAUNCH/PAUSE`, `CROSS RETRY`, `CROSS NEXT / SAVE`, and
`CIRCLE BACK`.

Live v129 acceptance completed on 2026-08-05. The three-choice console menu,
its `Leave` branch, the relocated visible-terminal action, all record-computer
and disk X targets, disk `Take`/`Leave`, media `Insert`/`Cancel`, and the full
seven-still playback return all passed. Every video caption stayed readable
over its still. Nuke's intro, two-row HUD, gameplay, pause/resume, game-over,
retry, and Circle exit paths passed live; the four-letter name-entry layout and
save/back routing passed the release tests.

`output/TEST_V129_NUKE.cmd` launches the v129 CUE and uses a future dedicated
control-room state automatically if one is present; otherwise it boots the disc
normally and prints the same focused checks.

## Historical v117 release validation

The current route must be validated from a cold-boot New Game on:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v117.bin
output/Xenogears_PW_CD2_mass_driver_standalone_v117.cue
```

Use a cold-boot New Game for complete v117 acceptance. A v116 in-game save is
compatible. A v116 F1 state is suitable for the narrow seven-frame video test
only after v117 media is mounted and target 376 has been fully left and
re-entered;
F1 snapshots restore their mounted disc and resident gameplay RAM, so a state
captured in that room initially retains its v116 script.
V76 is genuinely broken for this test because its loadout-selected `0x16E4`
word is `0x1808`, which caps El-Regulus at Level 1. Completely exit
DuckStation, launch the v117 CUE, choose New Game, and load no older state or save.
Create a new F2 state or in-game save only after that New Game has started.
An F1 state taken inside an older battle also retains canonical 2960's resident
animation 0. The native idle-loop fix therefore requires a battle newly entered
from v117 media. Resuming a v97 battle retains its static animation-0 tail;
resuming a v96 battle additionally retains its invalid relative turn. Neither
can validate v117. A field state made on v98 likewise retains the flattened
canonical-453 art and target-384 script, so it cannot validate the mounted-field
motion or quiet south-lift handoff.

Any v99 state saved inside target 376 also retains its resident six inert
console banks. Leave and re-enter the Defense Archive from v117 media before
testing the new records.

Any v100 state saved inside target 377, 378, 379, 382, or 383 retains the
resident field-374 Materials Storage computer. V101 through v106 resident
states retain later superseded pedestal visuals. A resident v107 state contains
the allocator-unsafe appended-upload station and cannot validate v108's native
repack retained by v117. Leave and re-enter every tested reserve magazine from
v117 media before judging the Zeboim station.

A state saved with target 721 resident on v108 or earlier retains archive relay
H-10 and cannot validate v117's authentic static subway station. Cold-boot v117,
or completely leave the subway and re-enter target 721 from v117 media, before
judging the station, its archive record, or the adjacent M-07 shop.

Any v101 state saved inside Central Control target 728 retains its resident
childlike officer actors and earlier historical-scene choreography. Cold-boot
v117, or leave Central Control and re-enter it from v117 media, before judging
the adult actors, line-by-line facing, or camera beats.

Any v102 state saved while Central Control target 728 was resident retains the
old direct Citan route, off-walkmesh endpoint, and rear entrance camera. It
cannot validate v117's retained continuous three-leg walk or camera transition.
Fully leave and re-enter Central Control from v117 media, or use the cold-boot
path.

A v103 state saved with target 726 resident retains the old entity-20 facing
gate even after v117 media is selected. It cannot validate this release's small
gray archive panel. Leave target 726 and re-enter it from v117 media, or use a
cold boot, before testing `726:e20 -> 367:p0`.

A v104 state saved with target 728 resident retains the old Central Control
controller geometry even after v117 media is selected. It cannot validate the
two local console frontages. Cold-boot v117, or explicitly mount v117 media,
completely leave Central Control, and re-enter target 728 before testing entity
12's archive mail and entity 13's final-route sequence.

Any v105 state saved with target 376 resident retains the earlier code-success
and west-bulkhead actions. It cannot validate the north-lift camera/sound
reveal, entity 23's exclusive bulkhead control, or either door's persistent
open state. Reload target 376 from v117 media or use the cold-boot path.

A v109 state saved with target 376 resident retains the broader authorization,
record-reader, and north-lift interaction regions. Completely leave the room
and re-enter it from v117 media before testing the aligned regions or retired
empty-aisle stances.

Any v105 state saved with target 728 resident retains the old direct launch
action and has no playable target-388/target-507 handoff. Completely leave
Central Control and re-enter it from v117 media, or cold-boot v117, before
testing the red tunnel and Ouroboros laboratory.

V104 left entity 12 at `(57, 71)` with a facing gate and native `0x82` by
`0x82` operands, producing 276 units of effective reach on each axis after the
player extent. Entity 13 still used the behind-console pivot `(-154, 125)` and
a `0x46` by `0x14` rectangle, producing 156 by 56 units of effective reach.
V110 retains v105's archive entity 12 at `(57, 71)` on walkmesh triangle 23 and
entity 13 at `(-54, 94)` on triangle 16, removes both facing requirements, and
gives both encoded half-width `0x08`, or 32 units of effective reach. Their
centers differ by 111 units on x, so the two 32-unit regions cannot overlap.
Entity 14's unchanged east-door controller remains at `(181, 88)` with a 26 by
76 effective rectangle and is disjoint from both. The rounded captured
story-console stance `(-27, 84)` selects entity 13 alone.

Target 376 authorization entity 13 remains at `(175, 123)`. The six other
console controllers are aligned to their visible fronts at `(507,175)`,
`(264,-165)`, `(-230,-160)`, `(-465,-161)`, `(-445,145)`, and `(-220,66)`.
Entity 20 is approached near `(435,168)` on walkmesh triangle 235 and uses
proximity-only operand `0x24`, producing 88-unit effective reach; its retired
`(350,175)` empty-floor hotspot is silent. Entities 13 and 21 through 25 use
proximity-only operand `0x08`, producing 32-unit effective reach. Entity 26
provides the one-time proximity-only disk pickup at `(-75,-162)`;
Entity 26 owns the persistent, inventory-aware disk-apparatus interaction;
entity 21 is the shared arcade/video computer and always offers `Arcade Games`,
`Video Disk`, or `Leave` before checking disk ownership. `Arcade Games` offers
`Play NUKE`, `Missile Command`, or `Back`. On the PS field-input mapping,
Cross/confirm is mask `0x0020` and Circle/cancel is mask `0x0040`; this
correction makes Cross launch Nuke instead of taking its exit path. Its hidden
screen rig is isolated at world position `(8000,80,8000)` and uses ATEL target
`(8000,8000,-144)` and
eye `(8000,6464,-144)`. Even after retail's look-at helper triples every camera
component, all values remain inside signed-16 range. North-lift entity 17
remains at `(0,245)` with its separate no-facing `0x18` controller. The complete checked
approach and walkmesh table is in the v117 release notes.

The historical v117 package identities are:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v117.bin
BIN size: 696,979,920 bytes
BIN raw sectors: 296,335
BIN SHA-256: 56b0310986d95c7cebe574b34978c1d484c26270bb04181eec69b2e29592fbe2

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v117.cue
CUE size: 107 bytes
CUE SHA-256: 09ebbfa5066bb030d93b6177f4762dcf19b36233848b9d026fdc5ccbdf248480

manifest: work/mass_driver_v117_stage/manifest.json
manifest size: 224,079 bytes
manifest SHA-256: 832964147b4e5c8a7aa12c28d29f7ad0576434e2a2aa8707762511213c4b7709
declared replacements: 173 across 137 jobs, totaling 12,401,564 bytes
replacement aggregate SHA-256: fb297250c3e13d4117660bb5081d68536b927f6d0068a7a0df963b46686079b5
packaged payload extraction: 173 / 173 exact (structural package audit)
```

Relative to v116, canonical 1358 changes and canonical 2474 is added. Canonical
1358 inserts the FZN / Jonas Vale dialogue and `0x09` image transaction before
the retained ZBC sequence. Canonical 2474 is the new TIM generated from
`screenshotz/7.png`. Canonicals 2468 through 2473 and every other declared
payload remain byte-identical to v116.

Details are in [the v117 release notes](docs/mass-driver-dungeon-2.93.md).

### Historical v116 inventory-video package

V116 first promoted the disk to ordinary item 109, refreshed the six ZBC
frames, and held each still beneath its modal caption until advance:

```text
BIN: output/Xenogears_PW_CD2_mass_driver_standalone_v116.bin
BIN size: 696,899,952 bytes
BIN raw sectors: 296,301
BIN SHA-256: c0c13b0feb157bc90b839bd8eb0c969b552e5a5a627bb3344c07a9c51da3ce0c

CUE: output/Xenogears_PW_CD2_mass_driver_standalone_v116.cue
CUE size: 107 bytes
CUE SHA-256: b28c537eb5080bf2388ca599f50bcb07c3ddbab85585a74be488ec5eff232986

manifest: work/mass_driver_v116_stage/manifest.json
manifest size: 222,465 bytes
manifest SHA-256: bb797e261cdcaf068bbd17aaf3702bf5d9942ded387be5bdb181c4b72867dc0f
declared replacements: 172 across 136 jobs, totaling 12,257,716 bytes
replacement aggregate SHA-256: 8f81e624ccab14e8ef8a00de86453dadb9bf8037af2d5d9fc3b520d344214c77
packaged payload extraction: 172 / 172 exact (structural package audit)
```

See [the v116 release notes](docs/mass-driver-dungeon-2.92.md).

### Historical v115 Defense Archive video package

The v115 field-flag video event, package identity, six-frame native-video
contract, and console-frontage table remain preserved in
[the v115 release notes](docs/mass-driver-dungeon-2.91.md).

### Historical v114 personnel-station frontage package

The v114 package identity and its target-727 front/side validation status are
preserved in [the v114 release notes](docs/mass-driver-dungeon-2.90.md).

### Historical v110 Defense Archive alignment package

The retained v110 interaction-alignment proof and package identities are in
[the v110 release notes](docs/mass-driver-dungeon-2.87.md).

### Historical v109 subway-station package

The final v109 package identities were:

```text
BIN size: 696,561,264 bytes
BIN raw sectors: 296,157
BIN SHA-256: f47795904433df064b6eb4d2a48cbc9f324847ad047ca791850643d5f3b7d60d

CUE size: 107 bytes
CUE SHA-256: 74f2ce5120bd1cfdddfa380058d90eeb7ff6331d7281e5e56a2037d9d55dca74

manifest size: 209,705 bytes
manifest SHA-256: 262259fd5049f2e7157176e5698ae89e8b814a347f313b41e218bb0e4d1c9115
declared replacements: 166 across 130 jobs, totaling 11,505,848 bytes
replacement aggregate SHA-256: d62d8258cb4f4a1a7fe0d971034d4b8fd98a110dc80682d0b0db602cfc8ec31b
```

Exactly canonical IDs `2048` and `2049`, target 721's field bundle and
graphics, differ from v108; the other 164 replacements are byte-identical.
Canonical 2048 is 195,716 bytes with SHA-256
`55b8eb437b94cfcf4c3c1da3abfde2916a25e2b66b04e71b0b9b422f8042473a`;
canonical 2049 is 319,488 bytes with SHA-256
`d4cf59e33b30df0c03c0c2cd584d942fc6997b7cec2bd79b3d4cbe4fee512aa3`.

Details remain in [the v109 release notes](docs/mass-driver-dungeon-2.86.md).

### Historical v108 native-allocation package

The final v108 package identities were:

```text
BIN size: 696,558,912 bytes
BIN raw sectors: 296,156
BIN SHA-256: d081ce3f132f20b3ec44263eb7263848dd15a54e6d0aebfeb11764d542d1ceaa

CUE size: 107 bytes
CUE SHA-256: e2b76438b59a9cba37413becc8c37ba87d174b5d5a051e078f3c9f9a7b96b2df

manifest size: 208,967 bytes
manifest SHA-256: 30dce614c21064ba74f311061d934ec566af04cb378306a9f2322e2b393de6bd
declared replacements: 166 across 130 jobs, totaling 11,502,980 bytes
replacement aggregate SHA-256: 8f02ab6ce01784766a37e23ee5a1aca8aed637bcb03ce820d9a33694b5ed39eb
regression result: 220 tests and 2,822 subtests passed; no failures, errors, or skips
```

Live acceptance cold-loaded the station from final v108 media after leaving
the resident room, and the station was visibly correct. The resulting state is
`work/runtime_capture/station_v108_lossless_final_live.sav` (SHA-256
`f35efb37bb9011ebfe65b3afb71b5184be9ecd4896934627c62596b7e8a1b088`).
At live VRAM base payload offset `2104792`, all 64 atlas rows and the exact
CLUT matched. The original user slot was restored afterward with SHA-256
`5e5e2332004da7e1f3a52ddf57c9a43579026ed6b93b76ce38972a7fb278900f`.
Details are in [the v108 release notes](docs/mass-driver-dungeon-2.85.md).

### Historical v107 appended-upload package

The final v107 package identities were:

```text
BIN size: 696,652,992 bytes
BIN raw sectors: 296,196
BIN SHA-256: 147697121f12360986031e1f17b7eadac7e1c8c3495e6c8f5c47427c04c1e936

CUE size: 107 bytes
CUE SHA-256: f74b944bcd30df14257faa9fc68215ffa5ebd3d7eb9a4b4d38640f06c841d96e

manifest size: 208,284 bytes
manifest SHA-256: 1930c564f21f8e2e19938e102dc7c016e056b1fba12eac5b617a2f372a922d77
declared replacements: 166 across 130 jobs, totaling 11,584,900 bytes
replacement aggregate SHA-256: a1609a31c97af0235a320a198a420f00e0ce89d16927e51f2b57594dc904d733
regression result: 220 tests and 2,789 subtests passed; no failures, errors, or skips
```

V107's appended texture and palette uploads replayed correctly offline but
were outside field 673's registered native runtime allocations, so the live
field/actor VRAM allocator did not retain them. The package and its audit remain
available for historical comparison in
[the v107 release notes](docs/mass-driver-dungeon-2.84.md).

### Historical v106 packaged image and delta from v105

The final v106 package identities were:

```text
BIN size: 696,547,152 bytes
BIN raw sectors: 296,151
BIN SHA-256: bfb7dbbe6c3cd1f9162b89cd990a9a2c2d898189f712a3d1f95c9edd52c192a9

CUE size: 107 bytes
CUE SHA-256: e1efb24054e787c80db28c89abea3dda8fd500a231cf3699e7fe00f9c1f81204

manifest size: 206,831 bytes
manifest SHA-256: 050181b0304b0e154d27d1544fc58a64b5a99fb9e7a768152160c30edf925dc6
declared replacements: 166 across 130 jobs, totaling 11,494,440 bytes
replacement aggregate SHA-256: 42221214703826686729b170acf9fb2f5010acec01b3026dcb986d2d930a4247
regression result: 217 tests and 2,704 subtests passed; no failures, errors, or skips
```

The historical route, control, and final-room changes are documented in
[the v106 release notes](docs/mass-driver-dungeon-2.83.md).

### Historical v105 packaged image and delta from v104

The superseded v105 package was:

```text
BIN size: 695,815,680 bytes
BIN raw sectors: 295,840
BIN SHA-256: e495adefc0d01a1c284b23bb82f18f5f96bc7e058b2641ebe6cffa3c54e12be9

CUE size: 107 bytes
CUE SHA-256: 1e09351beed59f6d0521d2af179216bd9377de9f25ba1b142ffd64a887293b41

manifest size: 200,496 bytes
manifest SHA-256: ded64e33d94fc9e76487d83771bad0d50a770e486de096f446779bcda3de5f8f
```

The v105 manifest has 128 jobs and 162 declared replacements totaling
10,853,608 replacement bytes. Its canonical-ID-order aggregate SHA-256 is
`8b8f1fbccf6ddd35f3754de3dd4ae23092698462f307fad742ee9e2a0dd4e626`.

Relative to v104, this is a script-only canonical-2062 delta. Target 728's
script replaces the oversized or offset native controllers with distinct local
X regions for entity 12's archive reader and entity 13's launch console. Every
other decoded component, canonical 2063 graphics, and every other declared
replacement are byte-identical to v104. Exact per-ID identities are in
[the v105 release notes](docs/mass-driver-dungeon-2.82.md).

### Historical v104 packaged image and delta from v103

The superseded v104 release was:

```text
BIN size: 695,815,680 bytes
BIN raw sectors: 295,840
BIN SHA-256: c58dab43646a63adbe551d6f64b8ad9ddeef631314fc5e58f36f869e066a7812

CUE size: 107 bytes
CUE SHA-256: bc05a0b2de6caaa2f9c61a782db5d04ecb565acbf8d125277de7145dd33afa4e

manifest size: 200,496 bytes
manifest SHA-256: 4ef7aac32d7efbd33e6ca6bcd5566f475fc051b6b179a6ee62519e0d5696019a
```

The v104 manifest has 128 jobs and 162 declared replacements totaling
10,853,556 replacement bytes. Its canonical-ID-order aggregate SHA-256 is
`44a3dc320fbca5eee5c402df030b919524d3a05278ecfc067dd2e52488f95c2d`.

Relative to v103, exactly canonical 2058 changed. Target 726's field bundle
removed the facing requirement only from entity 20's checked action. Its
standard proximity box, visible entity-27 helper, native opening animation,
destination `367:p0`, and artwork remained unchanged. Every other declared
replacement was byte-identical to v103. Exact per-ID identities remain in
[the v104 release notes](docs/mass-driver-dungeon-2.81.md).

### Historical v103 packaged image and delta from v102

The superseded v103 release was:

```text
BIN size: 695,815,680 bytes
BIN raw sectors: 295,840
BIN SHA-256: 03b83464e2fbac6c3551453ee671be2ab305ebe96147411a46d904088ae04212

CUE size: 107 bytes
CUE SHA-256: d5d1529fb57c3a9b32b82df9049b6ead320ffc9af067423a072ac42d05748703

manifest size: 200,496 bytes
manifest SHA-256: a71b8c5f935e4342918acae679a12774f08cc64c6ca38a87adb842c1a81b0856
```

The v103 manifest has 128 jobs and 162 declared replacements totaling
10,853,556 replacement bytes. Its canonical-ID-order aggregate SHA-256 is
`b54340dfad3aa98fb1ee8fcd56d270bfc26623bda0ce008513ba3fce34e5d3e3`.

Relative to v102, exactly canonical 2062 changes. Central Control's field
bundle replaces the invalid direct Citan route and rear entrance camera with
three verified walkmesh legs, one side-on arrival shot held through the door
and walk, mutual Citan/leader facing, and a same-mode conversation pan. There
is no visible position snap. Canonical 2063's graphics and every other declared
replacement are byte-identical to v102. Exact per-ID identities are in
[the v103 release notes](docs/mass-driver-dungeon-2.80.md).

### Historical v102 packaged image and delta from v101

The superseded v102 release was:

```text
BIN size: 695,815,680 bytes
BIN raw sectors: 295,840
BIN SHA-256: 795bcd8363d10236b7e0ee19d39eeec0987474dee195736dd2e2571b7947c01d

CUE size: 107 bytes
CUE SHA-256: 2c4b3a6b3e6d087ba29aa74f4b4c00370739e3af9374f3bd51a697a6e8302bad

manifest size: 200,295 bytes
manifest SHA-256: ef2cb66b43d422fa86f27962dcda38a75ca454bf9a6e76a5ca38feccc46a927a
```

The v102 manifest had 128 jobs and 162 declared replacements totaling
10,853,492 replacement bytes. Its canonical-ID-order aggregate SHA-256 was
`fb5abb373b0a9c2f467a48d9166ef6b3829b4c403edf49e9104c35c29391d1c1`.
Its automated suite passed 208 tests and 2,636 subtests.

Relative to v101, exactly canonicals 2062/2063 changed: Central Control's field
bundle added the adult Director and Systems Officer actors, stationary `FE 17`
actor-to-actor facing before every historical line, and an individual camera
beat for each line, while its graphics resource carried those native adult
actor textures. Every other declared replacement was byte-identical to v101.
Exact per-ID identities remain in
[the v102 release notes](docs/mass-driver-dungeon-2.79.md).

### Historical v101 packaged image and delta from v100

The superseded v101 release was:

```text
BIN size: 695,759,232 bytes
BIN raw sectors: 295,816
BIN SHA-256: dd9274ef0e3c8047dd56a6bf3a4a3dec3747610945cc89b0d0f96746747676a7

CUE size: 107 bytes
CUE SHA-256: 6af2e9c17398b01e35e621802a3ae22c195a43007f87fa9387302bdea9d63d46

manifest size: 200,249 bytes
manifest SHA-256: 97dee560a66aed474c65e45b031eef66abf5db5913154d634df1c0b6f0eaa807
```

The v101 manifest had 128 jobs and 162 declared replacements totaling
10,803,828 replacement bytes. Its canonical-ID-order aggregate SHA-256 was
`27a7d66eb09cb7a3631570a22161e44a1b9b2aadce89d1a64abe68e0450be93b`.

Relative to v100, exactly canonicals 1360/1361, 1362/1363, 1364/1365,
1370/1371, and 1372/1373 changed: the five reserve-magazine bundles replaced
the cross-field computer with native service-pedestal nodes, and all five
graphics resources returned to field 673's exact 102,400-byte native stream.
Every other declared replacement was byte-identical to v100. Exact per-ID
identities remain in
[the v101 release notes](docs/mass-driver-dungeon-2.78.md).

### Historical v100 packaged image and delta from v99

V100's package identities, 208-test/2,600-subtest validation result, and sole
canonical-1358 Defense Archive delta remain recorded in
[the v100 release notes](docs/mass-driver-dungeon-2.77.md).

### Historical v99 packaged image and delta from v98

V99's package identities and its canonical-453/1374 delta are recorded in
[the v99 release notes](docs/mass-driver-dungeon-2.76.md).

### Historical v98 packaged image and delta from v97

The superseded v98 release was:

```text
BIN size: 695,834,496 bytes (295,848 raw sectors)
BIN SHA-256:
68ea0467edd054bbbe90cde57fe921ae5b7bd2bfa6ff88d82de04735bf8852ed

CUE size: 106 bytes
CUE SHA-256:
9797eb2009f06d69c2d6facec7908185174aa8e208c766ebfa990fefc40e1d67

manifest size: 197,378 bytes
manifest SHA-256:
51630346126a178e4ee36a2a6ee4dcf6e887a81d41b052427fe4aab55252f119
```

Its manifest had 128 jobs and 162 declared replacements totaling 10,870,888
replacement bytes, with canonical-ID-order aggregate SHA-256
`bbc99d82d5198ea5f5c278c2d9ae24ec617352cf02fc7945783b40840f81a5e5`.

Relative to v97, only declared canonical 2960 changed. The
source-level result is 33,604 bytes with outer roots
`(2, 0x10, 0x7FF8, 0x8344)` and SHA-256
`589a0d3c8c9481a0f1c336513ce727e5e88701dad311bda12239c7f93a0f3252`.
Its 36-byte animation 0 retains native `60 00 43 00` target-facing and ends
`10 FF 21 00 6D 00 11 FF 00 01 00 00`, adding the native keyframe-1 loop only
after the delayed completion handshake. Animation 1 shifts intact to
`0x71E0..0x71F4`; later program pointers move by four bytes. All standard
attacks, deathblows, the 844-byte model/sound container, and retail battle
overlay 38 remain unchanged.

### Historical v97 packaged image and delta from v96

The superseded v97 release was:

```text
BIN size: 695,834,496 bytes (295,848 raw sectors)
BIN SHA-256:
64816abe1a2b26eee020b2f5416f0384df69277329a0feb486215380844e3166

CUE size: 106 bytes
CUE SHA-256:
e44b987e6975e9c7462a7d5f1c20c2b64db2cd0482e392451fa9d4b3a599090b

manifest size: 197,378 bytes
manifest SHA-256:
cc283a215d79f2b30d011bfbf5537925f40df6d08490a9d898f01fed9ea7d56e
```

The v97 manifest has 128 jobs and 162 declared replacements totaling
10,870,884 bytes; their canonical-ID-order aggregate SHA-256 is
`52611121fef39fc1c7748b9d25973fa50f0616ce34781832bb36f82a216c7d9a`.

Relative to v96, only declared canonical 2960 changes. V97 restores its exact
v95 33,600-byte resource with SHA-256
`627b332e5b2c15ca7e99d7d44e76fa8f72291634dbbfc32aae1ab19ef511c8c6`
and outer roots `(2, 0x10, 0x7FF4, 0x8340)`. Animation 0 again ends its native
entry setup with `60 00 43 00`: obtain the formation slot-center target, then
face it. The v96-only 33,608-byte resource, SHA-256
`86807cb3d54acb40649b174e384f31aa82a167274976faa2e7ed283c2b62ec0a`,
and its relative `-0x0800` packet are retired. Canonical 38 remains exact
retail. The complete v97 replacement set and BIN are byte-identical to v95;
only release metadata and the CUE filename distinguish the packaged releases.

### Historical v95 packaged image and delta from v94

The superseded v95 release was:

```text
BIN size: 695,834,496 bytes (295,848 raw sectors)
BIN SHA-256:
64816abe1a2b26eee020b2f5416f0384df69277329a0feb486215380844e3166

CUE size: 106 bytes
CUE SHA-256:
4bf160b1a1d1aa6ad0112f7c0c31ea822feeda717772c069b66758cad6344cad

manifest size: 196,759 bytes
manifest SHA-256:
649b4b81553cb1e8178eb7ffe680460397032d2ddd196f8fadbee319ad8111fb
```

Its manifest had 128 jobs and 162 declared replacements totaling 10,870,884
bytes, with canonical-ID-order aggregate SHA-256
`52611121fef39fc1c7748b9d25973fa50f0616ce34781832bb36f82a216c7d9a`.
Its complete automated suite passed 207 tests and 2,420 subtests with no
failures, errors, or skips.

Relative to v94, v95 changes or adds exactly seven declared canonical
resources:

| Canonical | Target | Resource | Size and SHA-256 |
| ---: | ---: | --- | --- |
| 1340 | 367 | Field bundle | 23,932; `166a09660df3e9598b3e45386f5892d6546a3a677a1cbd72337e5736cd9d458a` |
| 1341 | 367 | Graphics | 116,736; `db54a274c151c4a2602e10b24e7781e99aed220916b64429b6d1d9bb476b8259` |
| 1376 | 385 | Field bundle | 55,748; `c724afdbe719899069924850f4aa7e79537708c565b8a7f7a80b9ee04d3df78e` |
| 1377 | 385 | Graphics | 165,888; `d38d2ae9a2136b497403b917d04a052ecfd0b476f7f2799c10bfb86a8c235596` |
| 1378 | 386 | Field bundle | 55,516; `4b2ae09b34690892d6ad6624f1c0460cc88a01432c9e0774bd1c5a480de44977` |
| 1379 | 386 | Graphics | 165,888; `d38d2ae9a2136b497403b917d04a052ecfd0b476f7f2799c10bfb86a8c235596` |
| 2062 | 728 | Field bundle | 53,572; `0d81fbded88cd76e622a0e2880091c7d6617daa469778695e91e8f6513e40857` |

Target 367's 1,758-byte script has SHA-256
`5d75339bfbe28488b191a3921f246660d24255736814ac2cc50a9ae25d2392b0`;
its 105-byte dialogue has SHA-256
`e35f3e204abe8727e9282786951493065b4a8b0ed11344695db0f99ec0a665df`.
Targets 385 and 386 each have a 1,803-byte script, with respective SHA-256
values `41a99d6d2a5278e1860a79e94a207de37560eea60e6354bff1a2f43edea6df49`
and `4a98568d2130be090e58d36b819c72deedbf7a82375771535b76c6b1fcecca87`.
Their dialogue payloads are respectively 790 and 577 bytes, with SHA-256
`b8fbffffe7882c974d08c1708eb2f5b66b7e6e275123973b70dc7548c6042d1e`
and `f3ed00a4584c2ef9b352d2e16ca9bf9be857d00acf2a90fe4725517d5ebbef92`.
Target 728's 3,083-byte script has SHA-256
`def9d997333c91c69bb287fe5d790f5f399906ced69f34cf729e0b49c8342b95`;
its 5,040-byte dialogue has SHA-256
`6012b671b036c8869d626ad545fa7e2d1b8b0ef3887cebac7cd3dd5006620e8b`.

Every other declared replacement is byte-identical to v94. This preserves the
native subway archive robot and return correction, retail reserve-magazine
computers, native El-Regulus battle yaw, complete deathblows and Attack-Level
progression, hanging-terminal corrections, Auxiliary and Railway switch
roles, Goliath Factory encounter, and all five warhead layouts.

### Historical v76 packaged image

The superseded v76 release was:

```text
BIN size: 696,112,032 bytes (295,966 raw sectors)
BIN SHA-256:
2335f0cf46a1bab32d54aeb221ca418af4cf417b879ce9141c9efc8da23c6c47

CUE size: 106 bytes
CUE SHA-256:
e25563d81464f96edc1f613d9c917db5616ced5513e6230951fcadd6fd2d1c28

manifest size: 180,984 bytes
manifest SHA-256:
c19e255b216f8db7385f27946e8ecbfb0fe392d2faa6628fe3d95cab111f9b55
```

The final v76 automated suite passed 197 tests and 2,242 subtests. Its
manifest has 125 jobs and 158 declared replacements totaling 10,912,047
bytes; their canonical-ID-order aggregate SHA-256 is
`cd1df6976415128f68eb4392b854131bace4b987e0fd1a7b142c0582194f056f`.
V76 retained the corrected offensive motions, routes, doors, and animations,
but was genuinely capped at Attack Level 1 because Elly's `m56 = 1` loadout
read `0x16E4 = 0x1808`.

### Historical v75 packaged image

The superseded v75 release was:

```text
BIN size: 696,112,032 bytes (295,966 raw sectors)
BIN SHA-256:
31bb91d6bb9d781ce39693c1eb5d77dc211717ea2c27d2381c6147db83845df4

CUE size: 106 bytes
CUE SHA-256:
0eb635968ac69772a7772f4d9f2735daff322cde72b4713ac2780e4d3daaa952

manifest size: 180,849 bytes
manifest SHA-256:
de960f5289a9c5a16893d1578177c3daec6cacde66178cd5406dbc047c5b33e1
```

The final v75 automated suite passed 197 tests and 2,240 subtests. Its manifest
contains 125 jobs and declares 158 replacements totaling 10,912,031 bytes;
their canonical-ID-order aggregate SHA-256 is
`457dd88ac50a2a79472489e212afc9d275724416bc184aff273fae73813d9750`.
The final image rebuild completed successfully, its patched boot sector passed
the builder's MODE2/Form1 EDC/ECC check, and the BIN/CUE/manifest hashes above
were recomputed after that rebuild.

### Historical v71 release evidence

The superseded v71 release image was:

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v71.bin

BIN size: 695,538,144 bytes
raw sectors: 295,722
BIN SHA-256:
09a91f50211a8f1106a6a341e69dd225a64e31c89a3939f10997a93baceef90b

CUE:
output/Xenogears_PW_CD2_mass_driver_standalone_v71.cue
CUE size: 106 bytes
CUE SHA-256:
d672bea94a499da2fc8696e86d3fc950a721da9778466faf19ce41ff804dfcc5
```

The final automated suite passes 187 tests and 2,095 subtests.

The stage contains 156 replacements totaling 10,407,043 bytes, with
canonical-ID-order aggregate SHA-256
`448c45c5df4c83a4511fe87481c27425732fa8a80a797fec7bb8f56fa948e314`.
The final stage manifest is 175,490 bytes with SHA-256
`ff593f5249b71a759b9dfbf0f89be5484e99ac22f7d3ac5541e6facb6c5d9fb7`.

Re-extraction confirms all 156 replacement payloads, totaling 10,407,043
bytes, byte-exact. The 5,149 unique replacement sectors plus the standalone
boot sector, 5,150 sectors in all, regenerate exactly as MODE2/Form1;
including the FAT and archive header expands the audited set to 5,167 sectors.
Comparing the retail source with v71 finds 108,801 changed common sectors plus
3,011 output-only sectors. All 111,812 regenerate with valid EDC/ECC and zero
invalid sectors or mismatches.

All 3,565 ordinary undeclared FAT files, totaling 624,830,534 bytes, remain
byte-identical. Their aggregate SHA-256 is
`ab116c665120d6699bee74ddce86f2d76532f41636c531636050c091c23dae43`.
Canonical 22 is the patched system executable; canonical 17 is the overlapping
umbrella entry spanning that executable and the rebuilt archive region, so
neither is counted as untouched.

The retired historical continuation is
`output/MASS_DRIVER_V71_CONTINUE.sav`, 1,745,813 bytes, with SHA-256
`cc8d4582df72ceaf2e7dd6d07177f62ab731f8dff19c0da058bed0ab7346545a`.
It begins in the migrated post-Guardian field 376 beside the paired bulkhead,
with the final image mounted and its resident archive table matched to v71
(SHA-256
`b6e4bbf5c843942691e8fcd9fcb94643c399af0cec33e5ecdfb5dc8cd047d85c`).
The deterministic v70-to-v71 migration retains frame format 2 at payload
offset 98,422, recompresses the 3,817,114-byte gameplay payload to 1,647,391
bytes, and changes 5,231 decompressed payload bytes in the resident archive
table. Because field 376 is already resident after the Guardian, it cannot
validate the new lift, target 384, its scene and battle, the return upstairs,
or Citan's corrected first-entry staging. It also begins after target 368 and
Materials Storage, so it cannot validate the split main rail and rear email
terminals or target 722's objects. More importantly, it embeds v71's early
Citan party and must not be used or recommended for any v74 party, narrative,
or battle acceptance. It also retains the earlier Gear accessory inventory and
ability word, so it cannot validate v77's repaired attack-level progression.
Use a fully quit, cold-boot v110 New Game instead.

Comparing v70 and v71 shows exactly three changed or new replacements:
canonical 1358 for target 376 and canonicals 1374/1375 for target 384. The
target-376 bundle is 135,460 bytes with SHA-256
`9d1950f6486df612919aae53671ab7c94464468ab22ca670c7d7a7648d18a5e8`;
its 3,152-byte script has SHA-256
`31b6a6733f744c5a30686c713ce32d9634108917429bc3a6c201eb47b3053000`.
The new target-384 bundle is 133,640 bytes with SHA-256
`d00829ca635d0f4cc33b1d14272a21057cee7427d0217b16a9a55412d87d8416`;
its 19,839-byte script has SHA-256
`d27aed0a413711250689c4d791ba48c3f77d01a6439bb16d9779f838630f0e3a`.
Target 384's 440,320-byte graphics are the byte-exact source-403 asset with
SHA-256
`cb3cdcd7b61326e7d4aa3e54e7570abed2bcc3af295f4fd3cdbb288cb2896000`.
The complete v70 and v71 images differ across 84,628 common sectors plus 279
v71-only sectors, 84,907 sectors total.

Isolated DuckStation acceptance on the exact frozen image showed the recessed
native-textured paired leaves inside their fixed dark olive frame. The widened,
facing-independent entity-14 action opened both leaves, walked the party
through the full visible aperture, and reached a visible, stable field 377
without a script stall. Automatic north and south transitions passed without a
button. Sustained movement into a field-378 warhead left the player stopped
outside its 72-unit immovable collider. The warhead models, collision, and
proximity mechanics retain that accepted implementation; v63 changes only
the narration and other active dialogue in those rooms.
Historical hands-on launch-sequence status: the exact frozen v60 image passed
end to end. Central Control committed the capsule, the released mode-17
nanomachine-dispersal sequence played visibly, and playable world-map control
returned with the then-current Elly/Emeralda/Citan party. That result does not
validate the current final-only Citan appearance, the Elly/Emeralda return
party, or v77's repaired attack-level progression.

### Frozen V161 El-Regulus validation contract (historical)

Everything in this subsection is frozen V161 evidence for the former
Mass Driver El-Regulus implementation. It is retained to preserve the exact
reconstruction and audit history; it is not an active V167 contract. V167
uses retail Vierge for Elly, and the custom El-Regulus payloads described
below are available only through the separate future-resource archive.

The frozen V161 build strengthens target-376's entity-0 script-1 worker. It
retains the exact `2D FF F8 07 FA 07 FC 07` leader-position read and
authorization guard, but now also encodes signed X guards before the
`z>=274` boundary: X below `-44` or at least `45` retries instead of calling
the boss-hangar lift. The shared entity-17 script-2 dispatch, one-tick yield,
and retry jump remain. Entity 17 retains no-facing operand `0x09`, reachable
locked and authorized X behavior, and a single-STOP script 3. Validation pins
the V158 north-lift point `(3.425583,274.982513)` on triangle 73 inside the
entry contract, the reciprocal `(0,245)` spawn outside it, and the captured
east return stair `(694.87,97.21)` on triangle 110 outside it. That far-east
corridor must reach field 726 parameter 1 rather than being stolen by field
384's boss-hangar transition.

The frozen V161 build also requires Defense Archive entity 23 at
`(-465,-161)` use
a no-facing rectangular initializer with X/Z operands `0x20/0x04` and
effective reach `80x24`. The live V159 stance
`(-474.812835693359,-160.151718140625)`, yaw `0x0C00`, triangle 177 and the
complete walkable front X `[-485,-425]` must select entity 23 alone. Its action
must retain the boss-victory guard, locked dialogue, dialogue 19, sound,
helpers, and persistent open-state write while replacing only the retired
fixed-camera entry/release spans. Opening the bulkhead must leave the live
field camera unchanged.

The frozen V161 build also moves Defense Archive video-disk pickup entity 26 from
`(-75,-162)` to `(-75,-148)`, exactly 16 units in front of the center apparatus,
and expands its facing-gated bounds from `0x04/0x04` to `0x0C/0x0C`. Effective
reach is therefore 40 units per axis over `X[-115,-35]`, `Z[-188,-108]`. The
captured stance `(-83.166046,-164.725983)`, yaw `0x0C00`, triangle 157 and the
established `(-75,-167)` approach must both activate the pickup, while its
region remains disjoint from every neighboring console.

V161 additionally requires target 384's Guardian routine to contain exact
`75 14 80 FE 84 0F 80` bytes after its 15-tick wait. Music ID `0x14` is the
retail-proven normal battle sequence used immediately before fixed battles in
fields 388 and 627; `0x1D` is not accepted as an alias. The existing
post-victory target-384 parameter-0 reload must remain responsible for
restoring field-music ID `0x18`.

Automated validation checks the world-map control overlay's two isolated
decoded-byte edits: one encounter slot at `0x5780` and deterministic formation
slot 0 at `0x6584`. It also verifies that the landmark interaction instruction
at `0x210A4` uses the executable layer's Cross-only mask `0x0020`. Separately,
canonical 4052
changes only the Mass Driver formation's first Gear enemy selector at decoded
offset `0x30F60`, from Tusk-Tusk `0x80` to Dragon `0x81`; its checked packed
SHA-256 is
`68d0b5f60acc5c5a7b7a55a1fba85438115dbe025b75434d25e17f7bbcefbf2d`.
The Mass Driver arena and every unrelated formation remain unchanged.

Validation also requires all 78 normal combat resources (441,537 bytes) with
aggregate SHA-256
`831d6a8c4514e9c0ae9acd45fd7a920563e397922d722c1e474e986b25b6fbe5`.
That set contains 76 enemy resources with aggregate
`781a39824b10c4724c8b27e009b7ed9db5259e985b9f3a2fe8ef2d5afa3a068f`
plus support resources 47 and 2614. The builder explicitly rejects the Story
Mode aggregate
`2496389c6b107aa2e69d7e7af5462ec5750835ffe058d106d5ae3ad7f8640ba6`.

It also checks canonical 2960's exact native animation-0 facing sequence,
delayed completion handshake, and keyframe-1 idle-loop handoff, all three
standard-attack source and patched hashes, their `112/120/112`-byte program
sizes, native clips, and single damage markers. Level-1 programs 35, 36, and
37 are checked independently for exact hashes and one damage dispatch each.
DoubleImpact must contain two instances of native motion `0x40`, separated
by ten ticks, with its damage marker after both. Ether Beam additionally
requires its full target-facing header, camera envelope, 30-tick charge,
exact retail-sized selector-2 sound event, four-tick event guard, native
visual packet, and 60-tick beam hold. Beat Storm must use `0x40` followed by
`0x41`, dispatch damage after both, complete normally, and contain none of
the `0x43`, `0x44`, or `0x45` non-combo motions.

V161 canonical 2960 must be exactly 33,608 bytes with outer roots
`(2, 0x10, 0x7FFC, 0x8348)` and SHA-256
`78eee071519dc5ee3cbbf5ca0080c69923580b6443b3e48e9759db451b6da46c`.
Its animation 4 must grow from V160's 84-byte
`f1d1dadf381cb19dd32e7f456f74c325952d3797461f394af785e787e6b6e50d`
body to an 88-byte body with SHA-256
`420fb39fa55df38c3a123ad61a04c35ecc27836e2de9d3961774f00d76bdf518`.
The exact handoff `4A FD 60 00 43 00 5B 02` must occur once: native opcodes
`0x60` and `0x43` reacquire and face the formation target after returning
home. V160's frozen canonical was 33,604 bytes with roots
`(2,0x10,0x7FF8,0x8344)` and SHA-256
`589a0d3c8c9481a0f1c336513ce727e5e88701dad311bda12239c7f93a0f3252`.
Its 36-byte animation 0 must have SHA-256
`f6cd4d7520356d3a25b4396a04d5a87d18811b2bb516912fa1320c394fe46939`
and exact bytes:

```text
0A 00 0C 00 10 00 48 00 4A FD 61 00 0A 00 5A 08
32 00 06 00 60 00 43 00 10 FF 21 00 6D 00 11 FF
00 01 00 00
```

Native `60 00 43 00` sets the slot-center target and faces it. `10 FF` selects
the model's default keyframe 1; `21 00 6D 00` preserves v24's delayed
loader-completion behavior; and `11 FF 00 01` arms that keyframe as a repeating
30-tick idle instead of terminating on a static pose. Animation 1 must remain
byte-identical while shifting intact from `0x71DC..0x71F0` to
`0x71E0..0x71F4`; every later animation pointer must shift by four bytes.
Validation rejects both the v97 static tail `10 FF 21 00 6D 00 00 00` and the
v96-only `62 20 00 00 00 00 00 F8 00 00` relative-turn packet, and verifies
that all 17 retail playable Gears use the same native `60`/`43` entry pattern.
Its primary model/sound container must remain byte-identical to the retail
source. Canonical 3425 supplies Guided Shot's complete checked SEDS;
canonical 2981 supplies Xenogears/Raimai's exact effects 7 and 8. Validation
builds a nine-effect, checksum-zero composite SEDS without changing any of
Guided Shot's channel bytecode. The patched canonical 3368 must be exactly
8,844 bytes with roots `(2, 0x10, 0x207C, 0x228C)` and SHA-256
`ecbd52b38f9ccff189626d0cc9f752331db1d3eb203f14acb0d76e953e6cd1d7`.
Its nested bank has count 6 and pointer sequence
`0x20, 0x20, 0x210, 0x210, 0x210, 0x210, 0x210`.
The composite SEDS is 496 bytes, has SHA-256
`d922c9c85dae0dae5e4206fb3c30811d854c50dbce915362d7cae4d350a9ef7c`,
and retains a valid additive checksum.
The donor's complete `0x55E0`-byte WDS is also proven byte-identical to
canonical 3084 (SHA-256
`ec6ae588d85e342f973ebf1ca1e87073c1721f37dbf06d521ccbcd70a6f65262`),
the common Gear WDS loaded by the retail battle path.

Canonical battle overlay 38 is separately decoded from the 343,948-byte retail
source with SHA-256
`ad4586923095715288377caea89f2cd15d70a2f80ef53394e2faec22b2e0b825`.
The weight restoration scales only on-foot party physical Attack by
`floor(Attack * (weight_hundredths_lb + 27280) / 44000)` and adds
`trunc((floor(weight_hundredths_lb / 220) - 76) / 2)` ticks to ATB. Fei's
initial 167.20 lbs is neutral; Attack changes about 0.2273% per pound and ATB
changes one tick per 4.40 lbs.
Enemies, Gears, and Ether remain on their retail paths. Validation retains the
native 20-byte target-yaw block at decoded offset `0x3D240` and rejects the
v78-v88 fixed-slot-0 half-turn block. The patched decoded overlay has SHA-256
`0b1b6a530abc4f7faacd0743a9d31214d4c81f4f1d464caeece7b35ab9bed580`;
its exact complete-group LZSS replacement is 164,732 bytes with SHA-256
`6bd4fb2d0b6b92a28f8379d051f775e23342b2df11fa18efb402feb0cefbbbec`.
Canonical 38 remains wholly responsible for shared target-derived yaw. V97
historically restored canonical 2960 animation 0
to v95's native facing bytes. V98 extended only that animation's tail with the
native keyframe-1 loop. V161 changes only shared post-action animation 4 after
the complete V160 animation suite; Attack-Level progression, model data,
standard attacks, Level-1 programs, and all higher deathblows remain
byte-identical to V160.

Canonical 453 replaces Gear 10's global field-scale Vierge alias. Its retail
16-animation controller remains byte-exact, including animation 3's physical
jump, apex, and landing hooks. V99 maps the 65 frames onto five authentic
field-657 idle directions, five feet-anchored crouch derivatives, and five
forward travel/airborne directions. Walk retains its six-phase hover cadence,
jump reads upright -> crouch -> airborne, and run retains its four-phase
cadence. The rebuilt resource is 13,844 bytes with SHA-256
`2035ee09d4c11e1497f4f25491c5cc0ce9dd80d06c06131fdc2bda4f46333f1b`;
its decoded SHA-256 is
`4a504751d5bcb94528b5e95936d6535ffc954b03c421c9fffe0c8fcfd1563014`.

Programs 38-43 and 68-70 must no longer equal their retail four-byte stubs.
Each is hash-checked for an aligned model-local program, one damage dispatch,
one completion, and audited El-Regulus motion clips. Their physical-prelude
sequences are respectively `40-41`, `41`, `42-40`, `40-41-40`, `41-41`,
`42-40-42`, `40-41`, `41-42`, and `42-40`. Thus every physical segment uses
only confirmed offensive clips `0x40-0x42`, and no higher-tier program invokes
collapse/defeat clip `0x45`. Beam variants retain the valid `0x44` firing pose
inside their native beam event. Each Infinity program must place two ordered
offensive clips before its native beam packet, with powers `50/55/60` and fuel
costs `10/20/30`. The relocator checks every nested
pointer, outer root, null/alias entry, unchanged program, the
byte-identical primary model/sound container, and the separate checked
auxiliary sound resource.

Canonical 29 is decoded with the retail complete-group LZSS rule; validation
proves that only El-Regulus name-table entry 38 changes, all twelve command
labels and dimensions fit their audited slots, and every other entry is
identical. Canonical 2595 validation rebuilds all 31 fixed-width name records
and checks Elly, Emeralda, and El-Regulus explicitly. V85 introduced, and v99
retains, the requirement that El-Regulus's third stored glyph be fixed-cell
`0x1A`; validation verifies that it maps
to the runtime hyphen, and rejects the old `0x13` value that displayed as the
digit `3`. It also checks Elly's
level 70 test state, `m56 = 1` battle-command loadout, and exact
`Atk Lv1/2/3 Max` accessories `60/61/62`. For that loadout the engine selects
the third ability halfword at initial GameState offset `0x16E4`; v99 retains
exact value `0x1FF8`, composed of Level-1/2/3 masks `0x1C00`, `0x0380`, and
`0x0070` plus Infinity bit `0x0008`. The adjacent `0x16E0 = 0xFC00` word is
the on-foot ability word and cannot satisfy this Gear path. Battle runtime
stores current and maximum Gear Attack Level at entity offsets `+0x148` and
`+0x149`, incrementing the current value and clamping it to that derived
maximum. Canonical 2594 validation decodes accessory archive
entry 19 and proves those IDs use effect selectors `06/07/08`, rather than the
Frame HP selectors carried by `5A/5B/5C`. It also decodes Gear 10's entry,
changes only the three standard-attack power bytes, preserves the `10/20/30`
fuel values, and proves that every other archive entry is byte-identical.
Existing validation
checks field 657 actor 7
and its external graphics, exact PSX VRAM
reconstruction, the five authentic directional idle canvases, the five
Vierge-derived forward-driving canvases, the self-contained world-map bundle,
retail five-animation/35-frame program, distinct idle and movement pixel
pointers, halfword-aligned two-subsprite records, pose-specific direction
bounds, uploads no larger than the retail 32-word by 64-row Gear cell, and
the retail `0, -2, -4, -6, -4, -2` movement cycle, the source-361/source-362
paired lift, its 30-step upper motion and 15-step lower continuation, the
native lower-landing cleanup, both ascent directions, exactly two tunnels,
Gear ID 10's authentic five-direction world-map sprite, its dormant Gear-shop
model selector, neutral pose selector, and the separate equipment-preview
pointer,
the platform Repair Bot's transplanted actor/sprite banks, retail-proven VRAM
placements, native shop opcodes, isolated shop IDs 36 and 20, and exact
29-item/58-Gear-part catalog counts, complete native LZSS command groups with
exact heap-decoder termination, the collision-driven subway exit, the
open target-363 vestibule, its authentic reused south-wall terminal, the
source-376 personnel airlock, all 33 target fields, target 372's four external
and four local door actions, all four bounded local transfer branches shared
by the eleven possible party actors, all 44 party-actor copies of their deeper
outbound waypoints, all four finite transfer waits and exact local state
writes, the storage-annex door's shared bounded script-31 movement for all
eleven possible party leaders, target 722's sole facility-computer controller
at `(40, 150)`, its combined dialogue-8 action and required authority-record
bit, entity 15's native actor-2/sprite-1 treasure presentation and persistent
one-time Omegasol flow at `(220, 43, 66)`, target 387's stacked connector,
target 726's
parameter-2 arrival, both objective annexes, six source-378 archive rooms,
the native source-377 target-367 three-door junction, its reciprocal links to
target 726 and both source-374 storage dead ends, the target-385/386 native
computer and chest presentations, and their independent `0x03FA` opened bits,
target 368's main entity-13 rail action and independent entity-14
rear-mail action, the fact that only entity 13 writes the rail bit, the native
header-node-25/model-4 overhead-arm presentation at yaw `0x0600`, the
two interlocks, the reciprocal post-gate containment-vault route, and every
declared receiving orientation. The terminal-role verifier separately proves
that target 361 floor entities 12 and 13 are the only Auxiliary Grid writers
with switch/status dialogue 1, while hanging-terminal entity 16 is the sole
Directive writer with archive dialogue 0. It requires entity 16 at
`(-31, -105)` on walkmesh triangle 26, with no-facing bound `0x08`, beneath
the beige/green-lit overhead-arm prop at header node 44/model 7 and yaw
`0x0200`. The checked 32-unit archive reach remains 206 z-units from the left
floor-switch zone and at least 33 x-units and 114 z-units from the right one.
It rejects mail, staff names, or party commentary in the Auxiliary console's
authored status text. Across targets 366, 368, 369, 370, 371, and 724, it
requires every hanging terminal entity 14 at `(-124, -25)` with no-facing bound
`0x08`/32-unit reach beneath the beige/orange node-25/model-4 prop at yaw
`0x0600`. Every desk entity 13 stays at `(45, -42)` with bound `0x1E`/76-unit
reach, leaving a 61-unit x gap between interaction zones. In targets 366, 369,
370, 371, and 724, desk dialogue 1 and hanging dialogue 0 must both repeat
without writing progression. Target 368 remains the checked large-rail/small-
mail exemplar: desk dialogue 0 alone writes the rail bit, while hanging
dialogue 1 presents Aron's mail without a write. Central Control entity 12 must
remain a separate, repeatable, state-neutral Elly observation that the relocated
console looks out of place among the other computer terminals, rather than part
of its entity-13 finale console. Entity
13 must own the distinct historical memory and automatic post-memory Citan
arrival, local dialogue, capsule launch, repeat status, and guarded return.
Only entities 17 and 18 may be visible in the memory, and
their exact native component-04 sprite entries must render complete people
rather than pixel-sized dots. Entity 19 must remain hidden as Miang's point of
view and offscreen `MIANG` voice.

Validation also checks the Directive and address records, the two-condition power gate, fixed
no-escape formation 15, the isolated 36,000-HP Guardian resource pair,
the El-Regulus/Crescens two-Gear setup with no Fenrir or Citan battle slot,
the preserved field-376 threshold arrival, Citan's absence from target 376,
the authorization-to-lift handoff, target 384's safe adjacent Gear placement,
single automatic approach/boarding trigger, Elly's offscreen-Citan line,
immediate one-time defense-robot
scene and battle, post-victory mounted-actor rebuild, offline north
bulkhead, dismounting south return to target 376, persistent Gear
ownership, Elly/Emeralda on-foot restoration, all 30 grounded vertical warhead models across
five cleaned field-673 rooms, their six immovable colliders per room, removal
of the retail story cast/scripts and glass vats, and automatic full-width
north/south boundaries. Both checked target-376 doors consist of two opposed
moving leaves cut from the exact donor wall-panel textures, with only a dark
reveal behind each wall plane. Finite 24-frame `OP19` world-position routines
move each pair outward. Code acceptance must preserve the live room camera
while owning the north pair's sound, animation, and persistent authorized-open
presentation. Entity 23 at `(-465,-161)` must use no-facing OP18 X/Z
`0x20/0x04`, effective `80x24`, preserve the current field camera, and own the
west pair's post-Guardian sound, animation, and separate
persistent open bit; entity 14 may only traverse the already-open door. All five
vaults include the one-shot reveal/control handoff plus
ten `2D FF` controlled-leader polls with reciprocal destinations and yielded
per-frame retry loops. It also checks source field 394's unique archive
geometry, its unchanged entity-13 native console initialization and collision,
the absence of a Citan actor or party load there, the absence of the save-menu
opcode from that console, its five sequential authorization choices, the east
service-stair entry, reserve-magazine routing, the paired west bulkhead, the
boss-completion flag, and the entity-23 bulkhead release. The Central Control
check requires entity 13 at `(-48,97)` on triangle 16 with no-facing OP18
operands X `0x1C` / Z `0x02`, effective `72x20` reach, and inclusive region
X `[-120,24]`, Z `[77,117]`. The new live engine stance `(-113,113)`, triangle
15, the older `(-15,113)`/triangle-20 stance, and F2 `(-4,114)` or rounded
`(-4,115)`/triangle-19 stances must select entity 13. Entity 12's archive must
use `(136,131)`, triangle 26, with no-facing OP18 operands `0x01/0x01`, raw
extent `2x2`, and effective `18x18` reach over X `[118,154]`, Z `[113,149]`. It
must retain a 94-unit X gap from entity 13 and a one-unit X gap from entity 14's
east-door region. Dialogue 1 must be one repeatable, state-neutral Elly page
identifying the console as out of place among the other computer terminals.
Entity 13's action must gate on authorization bit 4, play dialogues 12 and 21
in the present before fade or party hide, then emit the exact retail
save-point entry chime `74 50 80` once at PC `0x047A`. The chime must be
nonblocking and immediately precede the first fade. The action then presents
Elly's subjective memory with only entities 17 and 18 visible. Entity 19 remains hidden as the
`(14,58)` Miang POV; the silent reaction and historical shots use the stable
eye `(174,-102,-125)` without targeting Miang. Exactly 18 entity-13 F5 calls
must use flag `0x01`, and no flag `0x00` F5 may remain. The V151 failure SHA-256
`8bc81de760fda0ba5522c01b439a4aa152082bd8c48182e560c62f8747419717`
must remain recorded as evidence that hidden-owner dialogue 21 otherwise takes
OP_STOP and strands camera/actors with bit 12 clear. The memory flow must call
only dialogues 22-31 and 36. After dialogue 36, the action fades to black,
hides the memory actors, clears the grade, establishes one concise present
camera, shows the party, and fades in. Dialogue 32 must be the sole present
response. Dialogues 33 and 34 remain authored but runtime-unreachable. After
dialogue 32, the held fixed camera must interpolate for 24 frames to the
whole-room target `(-13,106,-32)` and eye `(-27,-767,-544)` without releasing
control, returning to STOP, or requiring a second Cross/X press. The fresh path
must enter that shot without a second camera-mode prefix; the interrupted
seen-but-not-arrived recovery path must enter fixed mode before the same shot.
Both paths must converge on one shared reveal/walk suffix. Citan must stage
hidden at `(225,104)` behind the native east leaf, set scoped F8 mask `0x0038`,
follow bounded waypoints `(170,89)/32`, `(160,110)/32`, and `(136,131)/20`, and
clear the mask immediately after the first leg before settling on triangle 26
in direction 0. SHOW must precede sound `0x77` and native entity-15 script 4.
Prepared header node 43/model 11 must be the relocated field-361 node-21/model-5
compact standing keypad at `(197,439,108)`, yaw `0x0800`, flags `0x0010`. Its
world AABB must be X `133..174`, Y `-61..0`, Z `153..190`; the no-growth texture
relocation must preserve all native models 0..10 and leave walkmesh and
node-29/model-5 wall bank byte-identical. Entity 16 script 0 at PC `0x0866`
must be the appended interaction-disabled, state-neutral solid body at
`(154,171)`, triangle 24, with raw collision radius 22 and effective player
contact 38; all remaining entity-16 scripts must STOP.
Reciprocal Citan-to-leader and leader-to-Citan facing cues plus WAIT 4 must
precede both dialogue-35 paths. After the dialogue wait, one 12-frame held-mode
operation camera must target `(145,160,-45)` from eye `(170,-80,-135)`, then
make one blocking call to entity 3 script 23. That 29-byte routine must turn
direction 0,
run the exact field-378 keypad animations, three `0xF9` sound calls, waits
`25/35/24`, and STOP. No `FE 53` may unlock either launch-commit path before
world-map unload. The bit-7 compatibility write, Citan addition, dialogue 35,
terminal operation, completion bit,
exact retail world-map position `0x0FFF` in mode `17`, and guarded field-617
return must remain ordered in that one local target-728 action. Each mechanical receiving entry is checked
against the forced outbound waypoint of the door behind it.

### Active V167 runtime acceptance

Runtime acceptance should confirm that target 729 completes the upper descent
before target 364 continues to the real lower landing; the lift motor stops
and its velocity is cleared there; target 364's far threshold enters target
360; returning through target 360 enters target 364 with parameter 1 and the
native ascent reaches target 729 with parameter 1 without replaying its
introduction; the two tunnel screens precede the stationary subway; M-07 is
visible outside the train, faces the platform lane, and opens working Item
and Gear-parts shops without blocking the train archive station or the route;
field 373's authentic Zeboim freestanding station is visible inside the train,
H-10 is not rendered, and the station displays the 6072 space-program mail
without awarding an item; both expanded lists can be browsed and
canceled repeatedly; Vierge remains Elly's retail Gear in the menu; and returning from
either menu leaves M-07 and the static station presentation intact; the
subway exit crosses into target 363 parameter 0; its open side returns to
target 721 parameter 1 at `(-1250, -218)` and leaves the party in the subway
without retriggering the exit or bouncing back upstairs; its mechanical door
enters target 362 parameter 0;
the airlock's north door returns to target 363 parameter 1 and its south door
enters target 727 parameter 2; every declared mechanical door control responds
only to X, plays sound and animation, and never transitions on contact; every external
door must visibly carry Elly and Emeralda through its threshold before the
next field appears; target 371's archive door must enter target 723's
staircase; crossing the complete staircase must exit into target 726 at its
Magnetic Conduit-side door without striped polygons, a freeze, or lost
movement; the reverse route must return through the same staircase;
both objective annexes, all eight archive rooms, the new three-door archive
junction, and both paths to field 726 can be
backtracked; after returning from the
auxiliary annex, both internal service-hub passages must open their paired
panels serially, visibly carry Elly and Emeralda fully through in both
directions, close normally, restore the
compass, and return movement control; target 372's north external door enters
target 375's complete staircase, whose far door reaches target 726 parameter
2 beside entity 15 with an unclipped interior camera; the reverse entity-15
door returns through that same staircase; target 728's west door returns to
target 383 parameter 1, and its native east door remains independent from
entity 13's continuous finale. Target 728 is the route's final room; no
target-388 or target-507 handoff exists in the active package. Before
entering the landmark, mounting Vierge and moving nearby must naturally start
a one-Dragon battle, show Vierge's retail Gear command HUD, and allow command-
menu entry and cancellation. The Dragon must survive the weakest attack,
normal enemy actions and damage must remain possible, and victory or Escape
must return to the saved exterior position with Elly still mounted. Vierge's
retail attacks and AERODs option must execute and return control normally; no
El-Regulus-specific command names, animations, balance, or model may appear.
The following objective sequence must also work:

1. At the beige/green-lit overhead-arm terminal in target 361, press X from
   the captured approach near `(-30.75, -104.82)` and confirm entity 16 reveals
   Directive 0320. Either floor-console entity 12 or 13 must set the Auxiliary
   Grid interlock with feedback; neither floor section displays mail, and the
   archive text must not open from v86's old empty-aisle hotspot at `(-40, 97)`.
2. Target 722 presents one genuine facility computer and one genuine treasure
   chest rather than two gold memory cubes. Entity 14 at `(40, 150)` combines
   the payload-handling mail, authority record, directions, and
   A-2 / B-5 / C-8 / D-4 clue in dialogue 8 and records the clue bit. Entity
   15 at `(220, 43, 66)` awards one Omegasol if inventory capacity permits,
   plays the native opening animation, and does not respawn after collection.
3. In target 368, use the main terminal at `(45, -42)` and confirm it supplies
   only rail-activation feedback and satisfies the rail condition. Then use the
   beige/orange overhead-arm terminal at `(-124, -25)` and confirm it presents
   Aron's saved 6081 email to Lena, is repeatable, and neither repeats the
   interlock feedback nor changes progression. The old v87 hotspot at
   `(-89, 90)` must open nothing.
4. In targets 366, 369, 370, 371, and 724, interact with both the desk
   station at `(45, -42)` and the beige/orange overhead-arm terminal at
   `(-124, -25)`. Confirm that each presents its own relevant, repeatable mail,
   neither changes progression, and no archive text opens from `(-89, 90)`.
5. Target 726 names whichever of the two power interlocks is still missing;
   it never requires launch authorization to open. Use the formerly dead side
   panel and confirm it opens target 367's native source-377 three-door Zeboim
   junction at entry `[0, 134, 0, 4, 4]`. Its return door must reach target 726
   parameter 4, while the other two doors reach targets 385 and 386 and return
   through parameters 1 and 2. In both source-374 dead ends, confirm that the
   native computer at `(40, 150)` presents repeatable room-specific mail and
   writes no progression bit. Confirm that the separate native chest at
   `(220, 43, 66)` awards one Omegasol, remains open after leaving and
   returning, and does not affect the other annex's chest.
6. With both power interlocks active, target 726 opens through the east
   service stairs into target 376. Confirm this source-394 archive-control
   chamber is visually different from the earlier Zeboim service rooms. Elly
   and Emeralda must remain at the inward-facing threshold, no dialogue may
   open automatically, and no Citan actor or follower may appear.
7. Walk to the built-in wall console and press X. Confirm entity 13 remains
   accessible, does not open the Save menu or behave like a treasure chest,
   and supplies the authorization context without a separate NPC interaction.
   A wrong entry must return safely.
8. With either clue bit unset, confirm the console names the missing record's
   location and then continues to manual entry. It must prompt separately for
   Directive 0320, A-2, B-5, C-8, and D-4 regardless of whether the optional
   clues were read, and it must not set authorization before all five match.
   Once accepted, the terminal must keep the live room camera, play the native
   `0x77` machinery sound, start both finite leaf animations together, and
   return player control without a zoom, combat, or field change. Leaving and
   re-entering target 376 must initialize both
   leaves at their open endpoints while authorization remains set.
9. Enter the lift and confirm target 384 loads as an actual Goliath Factory
   hall rather than the Zeboim ruins, with Elly and Emeralda on foot and
   retail Vierge and Crescens field sprites visibly parked near the
   entrance. The already-open archive lift must look like two halves of the
   original north-wall panel separated over a dim recess; walking through it
   must perform the bounded on-foot crossing automatically without replaying an
   unrelated scene or requiring X.
10. Confirm Vierge and Crescens stand together across the central aisle.
   Walking to them must automatically play one sequence that boards Elly and
   Emeralda. Before boarding, Elly must say `So... Citan left our Gears here
   for us.` without Citan appearing. The sequence then presents the short
   defense-robot exchange and immediately starts
   a no-Escape battle in the enclosed
   factory arena: Elly/Vierge and Emeralda/Crescens face one 36,000-HP
   mechanical Guardian. Citan and Fenrir must not appear.
11. Start this as a new battle loaded from V167 media; do not resume an older
    in-battle F1 state. Vierge must use its untouched retail model, animation,
    command names, attacks, and AERODs behavior; no Gear-10 presentation or
    El-Regulus-specific command may appear. Victory must return
    control in target 384 without a crash or stray battle state and keep both
    pilots mounted. The exchange must say the Gears will remain until after the
    capsule reaches the upper atmosphere. Walk, run, and jump as Vierge;
    confirm its retail field presentation follows the intact cadence. The north factory door must report that its
    bulkhead is offline without animating or transitioning. Backtrack to the
    south human-sized lift; it must dismount both pilots and return them on foot
    to target 376 without displaying an instruction to proceed on foot.
    Re-entering the hall must remain safe and backtrackable. Separately, enter
    target 376 from field 726 parameter 0 and immediately walk back up the far
    east service stair: it must return to field 726 parameter 1 and must never
    trigger field 384. The actual north lift at X `[-44,44]`, z `>=274` must
    still enter field 384 automatically after authorization.
12. The completed battle enables entity 23, the nearby west-bank record/control
    panel at `(-465,-161)`. Its no-facing `0x20/0x04` rectangle must accept the
    full walkable frontage and the captured `(-474.813,-160.152)` stance.
    Pressing X there must still present its strategic
    outcome record, keep the player's current field camera unchanged, play
    native sound `0x77`, and slide both weathered leaves outward. Those leaves must
    match the donor wall aperture, divide its existing texture at the center,
    and reveal only a dark opening; they must not resemble added bright rails,
    locks, or a flat blue/orange slab. The panel writes the persistent open
    state, so revisiting target 376 must show the leaves already open. Entity
    14 at the doorway must never open the door itself: before the panel release
    it reports the lock, and afterward its X action only walks Elly and Emeralda
    through the open aperture before changing fields.
13. Targets 377, 378, 379, 382, and 383 must each enter silently from both
    directions and display six detailed, grounded vertical warheads, with no
    retail cloning vats or story actors visible. Each room must also show the
    exact field-373 node-44/model-7 Zeboim station in target node 22/model 0,
    flags `0x0010`, at `(486, 106, -41)` with yaw `0x0600`. Its exact retail
    21 used 8bpp texture islands must be copied without resampling into the
    exact native fourth upload at `(512, 192, 40, 64)`, and its complete
    256-colour donor palette must occupy native row 488. The graphics stream
    must remain exactly four uploads and 102,400 bytes, with no appended or
    resized upload. Approach its
    unchanged entity-7 controller at `(420, 0)`, face the station controls, and
    press Cross/X; the
    facing-required `0x28` zone must present that room's complete dialogue
    block 0 on every use without setting a flag.
    No exposition may open automatically on entry or at either passage.
    Sustained movement into every reachable warhead side must stop outside its
    geometry. Cross every north and south boundary without pressing a button
    and confirm its automatic transition. Backtracking across the opposite
    boundary must return through the complete reciprocal sequence without
    triggering narration. Target 378's terminal must retain its complete
    6083/6079 record and its v89 interaction behavior.
14. Elly and Emeralda must enter target 728 Central Control alone. From the new
    captured engine stance `(-113,113)`, triangle 15, press Cross/X and confirm
    entity 13 responds without point-target facing or selecting entity 12 or the
    east door. Repeat from the older `(-15,113)`/triangle-20 and F2 positions.
    Dialogue 12 and Emeralda's single cue, dialogue 21, must finish in the
    present before any fade or hide. Confirm the ordinary save-point chime
    plays exactly once after dialogue 21 and before the fade, without delaying
    the fade. Confirm a silent reaction shot then leads
    into Elly's memory. Only the Launch Director and Systems Officer render as
    complete native actors; Miang remains hidden at `(14,58)` as the POV and
    offscreen `MIANG` voice. Every memory eye is `(174,-102,-125)` and no camera
    targets her. Dialogues 22-31 and 36 must advance. After dialogue 36 the
    memory must clean up under black, restore the party under one concise
    present camera, and show only dialogue 32. Dialogues 33 and 34 must not
    appear. All 18 entity-13 F5 calls use flag `0x01`. Do not press Cross/X
    again: the sequence must continue automatically without returning control.
15. Immediately after dialogue 32, the held camera must interpolate for 24
    frames to target `(-13,106,-32)` and eye `(-27,-767,-544)`. Citan must
    appear through Central Control's native east door after being occluded at
    `(225,104)` behind its leaf. Scoped F8 `0x0038` must cover only the first
    bounded leg to `(170,89)` and then clear. SHOW must precede the native door
    helper, and the whole-room camera must remain held while Citan walks through
    `(160,110)` to the compact standing keypad at `(136,131)`, triangle 26,
    direction 0. Confirm the terminal is visibly present and both Citan and Elly
    face each other for dialogue 35. Afterward, a 12-frame camera at target
    `(145,160,-45)`, eye `(170,-80,-135)`, must frame the terminal while Citan
    performs the finite sounded keypad sequence;
    completion must not occur until its blocking script reaches STOP. The leaf
    must remain visually open through unload. The local action must
    launch Taura's capsule, invoke the released game's Mass Driver world-map
    event, and return Elly and Emeralda outside with Citan removed. Targets 388
    and 507 and every Krelian-laboratory asset must remain absent from the active
    route and package. Before triggering the finale, confirm the relocated
    console is solid at `(154,171)` and that entity 12 opens only Elly's
    out-of-place-console remark, without an Emeralda line or state change.
16. A normal save and reload retain Elly's Vierge assignment and retail menu
    name. Loading an older memory-card save and taking the field-376 north lift
    must also restore Gear ID 2 before target 384 loads.
17. On the world map and in fields, mounted and parked Vierge use the untouched
    retail Vierge presentation. Turning, stopping, dismounting, and remounting
    retain valid direction frames and palettes.

## Surface Soylent campaign

The cut Disc 2 Surface Soylent sequence is also reconstructed as a cohesive
eighteen-room dungeon with 20 reciprocal door-pair foundations, 40 physical
X-button endpoints, specialist medical and Solaris annexes, ordered molecular-sorting and
M-Project puzzles, Meld containment, a save point, and the retained Sufal Mass
confrontation. Every room uses the native Krelian Lab corridor cue (music ID
`0x3D`), and the field-623 north
threshold now has a matching
paired blue bulkhead whose opposite-wall instance is correctly front-facing,
with sound and a finite opening animation. V233 retains V232's dialogue-grid
discipline, including V215's font-grid-safe field-593 keycard choice, and
validates the four repurposed field-550 patient-record blocks; 49 earlier blocks
have explicit word-boundary repairs, and the field-621 intake boy still says
exactly `I like turtles!`.

V232 retains V231's saved lower-east Intake route within the
Soylent facility. Security-keycard-gated field-621 entity 26 now enters logical
field 594, a bright, self-contained Treatment Preparation Room built from the
verified Disc 1 field-352 Ethos clinic source (canonicals 1315/1316) in checked
Disc 2 dummy targets 1794/1795. Its examination bed, illuminated workstation,
disabled encounters, and native animated exit are retained. The repeatable
read-only terminal now loads the T-594-03 fin-armed patient's vitals, hydration,
metabolic response, injection uptake, and improving prognosis without changing
any credential or progression flag. The repeatable read-only terminals in
fields 591, 592, and 594 drain the closing X press before restoring control, so
dismissing a readout cannot immediately reopen it. Field-594 e17 returns only
to `621/p5`; the
superseded field-565 e7/p3 handoff is sealed and dormant for future laboratory
content, so this door does not expose Krelian's Lab.

V228 populated private treatment rooms 591--594. V233 retains V232's rooms,
with one doctor administering aid beside the bed and one distinct native
Soylent demihuman patient in each.
Both characters are talkable. Each doctor uses a different warning that the
procedure is private and directs Fei back to the waiting area; each patient has
a different hopeful line about the treatment. Field 567 deliberately remains
the one NPC-empty examination room, while field 550's story doctor office is
unchanged. Field 567's visible side workstation now repeatably reports
`PATIENT RECORD / No patient is loaded / for this room.` and does nothing else.

V233 is the current packaged release. Every occupied treatment room in fields
591--594 now binds its record to the actual model-3 side computer bank rather
than an oversized aisle trigger. Three narrow, invisible X carriers at
`(80,-167)`, `(116,-167)`, and `(152,-167)` span the visible workstation and
require Fei to face it. Their encoded `0x01/0x0F` bounds produce an effective
`18 x 46` reach. The exact field-593 Save 1 aisle position
`(75.007858,-77.750687)` is outside all three carriers. All 1,201 reachable
bank-front points are covered while facing the workstation, and none accepts
the bed-facing heading. Each room retains its distinct two-page patient record;
field 593 also retains the visible Quarantine keycard and Accept/Leave flow.
Field 567 uses retired entities 4--6 to provide the same narrow, facing-gated
coverage on its existing workstation, without adding a model or collision
actor. Its no-patient readout is repeatable and read-only: there is no item,
state write, NPC, combat, gate, or progression effect, and the bed and open
aisle remain silent.

V232 retains V230's Classification Archive return-door correction in logical
field 549 without changing its deliberate-X action. The action-disabled e16
physical seal remains at `(-244,248)`, four units west and eight units north of
the e6 action center, deeper in the aperture. Its 16-world-unit physical radius
and 32-unit effective player contact radius are unchanged and remain wholly
inside e6's effective `36 x 40` X envelope. The exact V229 round-trip southwest
walking line clears the effective disk by 5.639 world units. The visible leaf,
native helper, and X target remain at `(-240,240)`. Holding Forward alone still
cannot open the leaf, and the complete closed-door cut across walkmesh triangles
6, 10, 11, 12, and 13 remains blocked.

V232 otherwise retains V230's X-only clinical return-door contract. Logical
fields 550, 567, 591, 592, 593, and 594 retain the aperture-aligned thin
rectangular collision seal, but do not use its proximity forward poll.
Approaching a leaf or holding Forward does not open it or invoke doctor-office
dialogue; one fresh, deliberate X press on the existing broad carrier is
required. A centered Fei can approach the seal's inner `z=250` contact plane
naturally, the previously reported off-center stance remains inside the X
target, and all six retail field-352 walkmeshes are unchanged.

V231 replaced field 593's historical Fei readout with the current A-593-12
shelled-patient record: pulse, blood pressure, temperature, respiration, shell
density, mineral balance, treatment response, and clearance. This diagnostic
path does not repeat the one-time item sound, acquisition receipt, or card
award.

V232 retains V231's three added field-621 examination doors in true apertures
carved into the white Intake walls. Their short far-side threshold pathways use
one whole-width textured FT4 apiece, so independently sorted lateral halves can
no longer cover the closed leaves at oblique camera angles. Field 593's terminal asks
`Accept it` or `Leave it` before awarding the visible Quarantine keycard. Leave
is repeatable and produces no state change or sound; Accept plays the item
sound, shows the acquisition receipt, and awards the card.

V232 retains V231's field-550 patient record, which is bound to
every reachable section of the actual side computer bank to Fei's left, static
node 27/model 3, through invisible entities 4, 5, and 6 at `(80,-167)`,
`(116,-167)`, and `(152,-167)`. Each uses encoded X/Z bounds `0x01/0x0F` and a
native facing gate. All 1,201 audited bank-front walkmesh points work when Fei
faces the terminal, while none work at the saved bed-facing heading. The bed
itself cannot invoke the record. The terminal reads
the registered cover name, Fei's mutable Status weight, clinical vitals, and a
`100% / PERFECT FIT` Biological Compatibility Index without changing clinic
state. V213 remains the historical first patient-record release; V214 is the
historical release that corrected its interaction geometry, and V232 retains
that correction. V232 also retains V230's private field-local
exit-gate scratch word across Xenogears' eight-opcode scheduler
slices, so the doctor update can no longer overwrite `OFFICE_ACTIVE` and
accidentally run the native exit before security is defeated. At the exact
saved field-620 east threshold, entity 24 still displays `This is the end for
now.` followed by
`The rest is coming soon...`. It plays no sound, does not animate or open the
leaf, does not transition or write state, drains both relevant Cross presses,
and leaves west entity 23 usable as the Intake return. The three independent
examination-room leaves remain flush with the rendered walls, and the
straight-wall pair remains in the separate `z=840` and `z=396` architectural
bays. Their dark opened-door view now comes from recessed jamb/lintel/sill
returns around carved apertures rather than backing plates. Field 593 alone
supplies the Quarantine keycard through its explicit, font-grid-safe Accept/Leave
prompt. The field-549 check-in terminal still opens and closes all
six original panels, but its repeat menu is only Fei, Elly, Citan, and Exit.
The unrelated retail binary unlock-code branch is no longer reachable.

The clinic security keycard starts the authored dungeon foundation by opening
field-621 e24 into field 565, e26 into the independent field-594 Treatment
Preparation Room, and all three Intake examination rooms. Field-589 e9
plays and records only the authentic five-tone clue; field-565 e12 requires
`Up, Down, Up, Left, Right` at its native service input panel. V208 installs the
exact bright Disc 1 field-550 diagnostic-scanner donor: source canonicals
1711/1712 fill logical field-588 targets 1782/1783. Its obvious entity-4 scanner
arms only the bio-interface cutoff; the distinct Quarantine keycard comes from
field 593. Intake e22 and field-565 e10 both accept that credential for
Quarantine. The planned production route proceeds in the fixed order
`590 -> 624 -> 626 -> 625 -> 622`. Sorter
and core receipts, a fuller
Meld response, and a reload-safe Sufal pending/epilogue/secured sequence make
each persistent transition visible. The completed outcome secures this local
node and leaves the emergency return explorable; it does not force the party to
an external field, world map, or title screen. V205 had selected natural field 588 by numeric identity even
though it is an unrelated Dark Armor treasure room; the appended credential
interaction was consequently a model-less hotspot. V206 uses exact Disc 1
field-573 canonicals 1757/1758. The compact room's workstation is baked into
static nodes 11 and 15, entity 7 supplies the aligned X interaction, unrelated
donor entities 6, 8, 9, and 10 are retired, and the native e4/e5 animated door returns
to `621/p5`. V207 preserves that release as history, moves the five-tone check
to e26's compound entrance gate, and replaces the room with the bright
field-550 diagnostic-scanner donor. V207's fresh-New-Game canonical 2595 grants every native on-foot
deathblow across all character and form records; Chu-Chu and Maria correctly
retain no native deathblows. Levels and stats remain unchanged because the
retained Perfect Works canonical 2607 already uses level-1 learning gates. V207
retains V205's independent topology, V203's post-sign-in receptionist response,
V202's deeper-access puzzle, and V201's
recovered Clinical Stabilization Ward as logical field 590, activates the
formerly empty field-565 staff-door action, and places the four-clearance
production threshold before the existing `624 -> 626 -> 625 -> 622` back half.
Field-565 e4-e10 use
wider X targets around unchanged narrow physical seals, with bounce-safe
reciprocal arrivals.

V233 retains V232's field-620 e24 as the only current-content boundary.
Its former relay-completion transition to `565/p6` and the later back-half
progression remain frozen as future foundations rather than being removed.

Version 180 widens the field-549 Classification Archive return-door action target so
the exact formerly failing straight-on stance is accepted without enlarging
the door's physical seal. Version 182 moves the Step-2 crowded biological
Quarantine room (field 620) to the live-audited field-621 west side-corridor
door, entity 22, and moves the Classification Archive (field 549) to the
north double door, entity 21. Their returns lead back to field 621 parameters
2 and 0, respectively. The field-565 patient-manifold route remains on its
native parameter-1 Intake return. Version 183 makes the desk receptionist
identified by the user's saved field-621 stance interactive as entity 13. She
retains her visible sprite while using a non-blocking rectangular X target that
covers the exact across-counter stance. She directs the party through rear door
entity 21 to field 549, where the terminal
offers one-time registration as `Aron Voss`, `Noel Ardan`, or `Kiro Dalen`. Registration
persists, unlocking repeatable Fei, Elly, and Citan patient records. Their
weights come from the mutable live Status records through retail opcode `EX69`,
not hard-coded profile masses; a clean campaign reports 167.20, 92.40, and
158.40 lbs, respectively. V209 keeps the native six-panel terminal animation
but removes `Archive records` from the repeat menu, so its unrelated unlock-code,
input-process, code-schema, and binary-value screens are unreachable. Version 184 persists the chosen alias
and starts a 60-second appointment timer when the party leaves the records
room. The physician then walks out of the marked east examination-room door,
waits beside reception, and calls that exact alias. Speaking to him sends him
back through the door while Fei remains under player control. Version 192
changes that instruction to `Follow me into the examination room.` and leaves
the lobby leaf visibly open after he disappears inside. Following through uses
the already-open doorway without a close/reopen animation; a genuine lobby
reload still falls back to the native opener. The player can then enter a
transplanted Disc 1 Ethos infirmary, now the Intake
Examination Office, for the one-time bloodwork and injection briefing. V183
savestates receive one explicit alias-confirmation menu because those states
recorded check-in completion but not the selected name. Version 185 moves the
doctor's reception endpoint off the sloped desk-edge walkmesh and onto open,
flat lobby floor, with the route and captured party clearances enforced by the
build. Version 186 keeps Fei controllable during the full timer and every
physician walk, and uses the exact office physician actor/sprite for the lobby
doctor. In the office, trying to leave makes the doctor insist on bloodwork;
two separate refusal conversations call a fixed no-Escape team of two Solaris
Guards and two Security Cubes. Version 187 makes that response visible: the
office leaf opens, all four responders use exact overworld Guard and Security
Cube assets, and the leaf closes before combat. That version froze
edge-connected routes but did not yet account for the exterior strip's
non-walkable material; V200 makes those crossings complete naturally. Clearance
is awarded only after victory. Version 196 makes that award a visible
`SECURITY KEYCARD`:
item-retrieval sound `0x37` plays, a receipt announces `SECURITY KEYCARD
ACQUIRED` and authorizes `FREIGHT / SERVICE`, and only then is persistent
operand `0x021A` bit 0 set. Defeat cannot award the credential. The doctor
then follows a connected route to the leaf and remains under a player-controlled
escape sequence. V200 completes that intended behavior: he opens the leaf at
the threshold, walks fully outside without stalling, remains visible while it
closes behind him, and only then disappears.
Version 188 historically fenced all nine ambient survivors away from the north
Archive doorway while retaining native random walking. Its one shared rectangle
later proved wider than the actual waiting-room walkmesh, so V198 supersedes
that shared-zone portion while preserving the door clearance.
Version 189 gives all eight adult waiting-room NPCs hopeful pre-revelation
dialogue: they believe the staff, tests, and treatment will help them and do
not yet know what the Soylent system is using people for. The little boy's line
remains exactly `I like turtles!`.
Version 190 makes the examination-room exit first report that it is locked and
then has the doctor insist that the procedure continue. The four security
responders now hidden-snap to the exterior threshold, cross on short staggered
16-step-bounded routes, and dynamically turn toward Fei instead of sharing a
downward cardinal pose. Their fixed no-Escape fight uses retail-proven bright
silver-white technological arena `0x30` in place of dark arena `0x3B`.
Held-X release drains keep the automatic call, both refusals, and exit denials
from collapsing into unintended repeat interactions. A lobby dialogue mutex
also makes the automatic call wait for any survivor or receptionist window to
close. Version 191 restores the archive terminal's original six-panel startup
before every first-use and repeat-use check-in menu. Registration, vitals,
Cancel, and Exit launch the panels' native close scripts; Archive records enters
the already-open retail menu directly, so its unlock-code workflow remains
intact without opening the screens twice. All terminal, migration, and doctor
dialogue now uses the selected two-part cover identity while preserving the
original three alias codes for existing saves.
Version 209 supersedes only that historical Archive-record handoff: it removes
the choice and every executable jump to the retail binary menu while preserving
the panel opening and native closes. It also changes lobby e22 from the V197
relay-completion shortcut into a direct Quarantine-keycard entrance and aligns
the three newer examination-room panels flush with their rendered wall bays.
Version 192 changes the physician's handoff to `Follow me into the examination
room.` and leaves the lobby office leaf visibly open after he enters. The live
open doorway transitions directly without a close/reopen cycle, while a true
field reload resets the local visual-state flag and safely uses the native
opening action. Version 193 identifies the newest Slot-1 marker as field 621
entity 22, the west side-corridor door to field 620. That historical release
held it closed while preserving its original open-and-enter action. V197 gives
that preserved path a concrete state transition: the party first reaches field
620 through field-565 e10 using the clinic keycard, and completing the biological
relays sets `quarantine_complete` and unlocks lobby e22 as the return shortcut.

Version 194 identifies the newer Save State 1 marker as Fei/e3 at
`(69.98291015625,396)`, triangle 14, yaw `0`, directly facing field-621 staff
door e25 at `(88,396)`. That door now enters the new field-567 Clinical
Stabilization Ward instead of dropping directly into field 565. The ward is
inserted between reception and the Service Distribution Manifold's staff route:
its first native paired door returns to field 621/p4, its second continues to
field 565/p2, and the manifold's staff door returns to field 567/p1. The room
retains its native paired-door animations and native Krelian Lab music
`0x3D`; its third door remains sealed as a restricted-procedure threshold.
For V194 testing, Save State 1 embeds the older field-621 script already loaded
in memory. Leave reception through another door and re-enter it before trying
the marked e25 door, or the embedded pre-V194 action will still use its old
destination.

Version 195 supersedes that ward topology while preserving V194 as history.
Field 621/p4 staff-door controller e25 still enters logical field 567/p0, but
field 567 is now an empty, one-door medical examination room transplanted from
Disc 1 field 352. Its exact static examination bed and surrounding environment
remain intact. It has no doctor, NPC, reachable dialogue, automatic story event,
scripted battle, or random encounter. Its sole exit, field-567 controller e17,
returns to field 621/p4. The former field-565 e6/p2 staff route is both physically
and action sealed. The complete V194 Clinical Stabilization Ward donor remains
reserved for a future room in
`content/surface_soylent_v1/reserved_room_donors.json` and
`tools/surface_soylent_campaign_donor567.py`.

V233 keeps that V195 room NPC-empty but activates its existing model-3 side
workstation. A deliberate X press from the narrow, facing-gated frontage shows
`PATIENT RECORD / No patient is loaded / for this room.` The action is
repeatable and read-only and adds no item, state write, NPC, battle, gate, or
progression effect.

Version 196 identifies the current Slot-1-marked door as field-621 freight
controller e26 at `(1645,396)`, not e22. Its reciprocal route remains
`621/p5 -> 565/p3`, but e26 now reports that the door is locked and requires a
security keycard until the field-550 security victory. Before that award it
plays no door sound, does not move the leaf, and cannot transition; afterward
it releases the preserved native open-and-enter action. The keycard also
replaces the former scanner-approval requirement at the production bulkhead.
In V197 this expands into the full service threshold: e24 and e26 both require
the credential, field-565 e12 becomes the keycard service passage, and e10 uses
it for the service-side route into Quarantine. Field-589's retained five-tone
clue then grants a resonance receipt; Quarantine releases e22 after its relays
are complete.

The V197 back half is deliberately ordered. Field 624 completes all
three feed diversions and displays a sorting receipt before field 626; field 626
confirms its safe-state calibration with a core receipt before field 625; and
field 625 expands the Meld reveal into a response from Fei, Elly, and Citan
before field 622. The Sufal conclusion records post-battle pending state, resumes
the epilogue after a reload if necessary, and commits the secured state only
after that epilogue. The secured node opens the 622-to-623 emergency return and
remains explorable. It concludes this local node without forcing an external
handoff.

Version 198 fixes the current Slot-1 waiting-room pileup without changing any
dialogue. The captured V197 state shows e9, e12, and e15 converged at the real
east wall near `(1190,1592)`, with e8 pressed beside them; west-side patients
were also walking into the opposite wall. V197's shared OP17 rectangle extended
to X500/X1250 even though the room ends near X541/X1190. V198 gives each of all
nine patients a distinct clockwise roaming zone with a completely on-mesh
24-unit halo and at least 50 units of separation. They retain native random
walking but can no longer converge, enter the walls, block the central aisle,
or obstruct the physician route. Their interactions remain unchanged, and the
little boy still says exactly `I like turtles!`.

Version 199 fixes the newest Slot-1 physician pass-through. The field-621 lobby
doctor had a valid radius-16 body, but the collision-ghost flag used to cross his
still-solid doorway seal remained set after he arrived at `(1200,1400)`. The
lobby and office versions of the physician now use a normal 32-unit rectangular,
solid, immovable body whenever visibly waiting. They remain ghosted only while
hidden or following a scripted doorway route, and the ghost transition occurs
before player control resumes for those walks. This preserves the earlier
no-stall door behavior while preventing Fei from running through either doctor.

Version 200 fixes the remaining office-door entrance and escape defect. The
newest Slot-1 capture proves that field 550's exterior triangles 34 and 35 use
material 0 with runtime flags `0x00800000`, so ordinary NPC movement rejects the
strip even though its geometry joins the interior. The four security actors
were spending their bounded walks outside and then being endpoint-corrected
inside; the doctor was spending three much longer bounds against the same strip
before being corrected and hidden. V200 gives only each scripted crossing actor
the native scoped `F8 02 38 00` traversal permission and clears it with
`F8 06 38 00` once safely across. Fei's solid e19 doorway seal and the global
walkmesh remain unchanged. Security now walks continuously from the exterior
reveal through `(0,200)` before fanning out and facing Fei. The doctor opens the
leaf, crosses on three 16-update legs, stays visible while the reverse-close
finishes, hides behind the closed leaf, and then clears the override.

Version 201 recovers the preserved Clinical Stabilization Ward at logical field
590, connects two reciprocal field-565 routes to it, places the four-clearance
production threshold at its third door, and widens field-565 exterior X targets
without widening their physical seals.

Version 202 restores field-565 entity 12's complete native directional-input
action. Field-589 entity 9 is now clue-only: it plays `Up, Down, Up, Left,
Right`, records clue-seen state at `0x021E` bit 8, and does not authorize the
passage. Repeating that sequence at entity 12 sets `0x021E` bit 9 and releases
both its native carrier and physical seal. Beyond it, field-588 entity 9 arms
the bio-interface cutoff and awards a distinct Quarantine keycard at `0x021A`
bit 8 with one item sound and receipt. Field-565 entity 10 requires that new
credential for `565/p6 -> 620/p1`; the original clinic security keycard at
`0x021A` bit 0 continues to gate only the two Intake-to-Service routes and to
contribute to final production clearance.

Version 203 changes only receptionist entity 13's completed-registration branch:
`I see you have signed in. Please wait here until your name is called.` The
pre-registration terminal direction, alias persistence, appointment timer, and
all V202 dungeon behavior remain unchanged.

Version 204 transforms the initial GameState in canonical 2595 so every native
on-foot deathblow is learned for Fei, Elly, both Citan forms, Bart, Billy, Rico,
and both Emeralda forms. Chu-Chu and Maria have no native on-foot deathblows and
receive no invented commands. The transformation does not alter character
levels, stats, or unrelated ability data; the checked Perfect Works canonical
2607 tables already make every native learning requirement level 1.

Version 205 makes the saved lower-east Intake freight door, field-621 entity 26,
the sole outside entrance to field 588. That room retains its tone-gated,
one-time Quarantine-keycard terminal and returns directly to `621/p5`. The two
displaced Service-Manifold thresholds now pair `565/p3 <-> 565/p5`, preserving
all 14 rooms, 17 reciprocal door pairs, and 34 physical endpoints without a
duplicate hallway route.

Version 206 corrects the room behind that route without changing its topology or
progression flags. V205's natural field-588 donor is an unrelated Dark Armor
treasure room, and its added credential action had no terminal model behind it,
so the player encountered a model-less hotspot. V206 replaces it with exact
Disc 1 field-573 canonicals 1757/1758: a compact blue Solaris computer room with
the center workstation baked into static nodes 11 and 15. Entity 7 is the
workstation's X carrier. Unrelated donor entities 6, 8, 9, and 10, including
retail story and loot behavior, are retired. The native animated door returns to
`621/p5`; the workstation still requires the five-tone authorization and gives
the Quarantine-key item sound, receipt, and persistent award only once.

Version 207 replaces V206's compact blue room with the exact bright Disc 1
field-550 diagnostic-scanner donor. Source canonicals 1711/1712 fill logical
field-588 targets 1782/1783. The native e17/e18 door returns to `621/p5`, while
the obvious e4 scanner owns the credential interaction. Field-621 e26 now
requires both the Security keycard and five-tone authorization; once the party
passes that compound gate, the scanner does not repeat the tone check and
save-safely awards both the bio-interface cutoff and Quarantine keycard.

A fresh V207 New Game loads that canonical-2595 grant. Existing savestates embed
their own GameState flags and mounted-media/FAT metadata, so loading one or using
Change Disc alone cannot apply the grant. Upgrade an existing state through the
fail-closed deathblow transformation and generic guarded disc-state migration,
write the result separately, preserve the source as a backup, and fully close
DuckStation before installing the migrated copy.

The current Slot 1 is safely migrated to V209 media while preserving its saved
field-621 position and gameplay state. It still has V208's Intake field resident,
so leave through any working door and return before validating the adjusted
panel geometry or direct e22 Quarantine-keycard gate. The exact V208 source is
preserved as `emulator_data/SLUS-00669_1.pre_v209_ef67aa91_20260824T172455.sav`.

Historically, the V207 Slot 1 still had V206's compact blue
field-588 room resident. Mounting V207 cannot replace that active room's bundle,
script, models, or graphics. Leave through the existing return to Intake at
`621/p5`, then re-enter the same door. That round trip is required before
judging V207's bright clinical scanner room; the still-resident V206 room is
not V207 validation. The installed 1,650,255-byte state has SHA-256
`e198990d0bf6ac3f976805cda5d853d3f09245ed2c434aa8433eaf0cecfe4b0c`.
The exact 1,858,882-byte source is backed up as
`emulator_data/SLUS-00669_1.pre_v207_cd47b5d8_20260823T221553.sav`, SHA-256
`cd47b5d8c6a5f82244f0ec08500c42fdd479865264919d764b31ff3c35eaa7d9`.

Historically, the guarded V205-to-V206 migration changed only the recorded CUE
and resident archive table; GameState, actors, Fei's position, and all bytes
outside that table remained exact.
The installed 1,745,647-byte state has SHA-256
`e1be06cf08d209a88808377cc74a6305444987c0f260c783b4af8a6d2ba36b7f`.
The exact source is backed up as
`emulator_data/SLUS-00669_1.pre_v206_75207402_20260823T210834.sav`, SHA-256
`7520740280e8a65a79dcb5f47a00741db3bfd3bdefe3c055188281cc0e474a1b`.
That migration likewise could not replace its then-active V205 room and required
an exit and re-entry before historical V206 validation.

The V205 Slot 1 is a pinned migration of the saved field-621/e26 stance.
It updates the CUE, FAT, and resident field script while preserving GameState and
runtime actor data, allowing an immediate X-button test without a room reload.
Its SHA-256 is
`31f0c570935b1f31f5c3aa58fb83227a76a48dfcd5967d6d6b41db36b4f53485`;
the exact pre-V205 source remains in `emulator_data` as a separate backup.

The V203 receptionist-validation Save State 1 is resident in field 621 under
V202, paused in the old
post-check-in dialogue ID 12 with `Aron Voss` registered and the appointment
armed. Fei is at approximately `(870.00,1431.09)`, directly facing receptionist
entity 13 at `(870,1302)`. The state is 1,711,245 bytes with SHA-256
`3f6dd8311e0761c21a88aef0d7d8eb67746da987193aad51d3e10f6fde3a6797`.
After launching and loading the state, use DuckStation's Change Disc command to
select the V203 CUE because the state restores its recorded V202 media. Then
close the embedded V202 line, enter the records room, return to reception, and
speak to her again. Player movement and emulator input remain user-controlled.

The previous Save State 1 is resident in field 565 under V201, with Fei at
approximately `(3553.43,-1107.49)` facing entity 12 at `(3500,-1060)`. Because
the state embeds V201's already-loaded field script, mounting V202 cannot update
that resident action. After launching V202, leave field 565 through an existing
door and re-enter it, then return to the marked controller and press a fresh X.
Enter `Up, Down, Up, Left, Right`; player movement and all emulator input remain
user-controlled.

The earlier V201 marker was resident in field 565 under V200, with Fei near
`(4250.66,-2999.62)` facing entity 6. That resident STOP action likewise needs a
field round trip before the V201 staff route can be tested.

An older Save State 1 can test V195 immediately. Its resident field-621
script is already V194's script, whose e25 destination is field 567/p0; press a
fresh X at the marked door without leaving and re-entering reception. Field 567
then loads from the mounted V195 disc.

For historical V199 testing, its captured Save State 1 must not be used to judge collision
immediately: it embeds V198's resident field-621 script and its already-created,
ghosted e35 doctor. Load the state on V199, make a safe round trip through a
nearby room, and re-enter reception from the V199 disc. The reload recreates the
called-phase doctor as solid, retains all nine separated V198 patient zones, and
loads that release's e22/e24/e26 gates.

Start with
[`docs/surface-soylent-campaign.md`](docs/surface-soylent-campaign.md); the
executable builder is `tools/build_surface_soylent_campaign.py` and the frozen
machine-readable layout is `content/surface_soylent_v1/dungeon_plan.json`.
The current image is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v233.cue`, launched by
`output/PLAY_SURFACE_SOYLENT_V233.cmd`. Its BIN is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v233.bin`,
698,816,832 bytes with SHA-256
`f50fa064e8d466bde46e0946a4c1ea7dc556a6a94d85f4632de201934318a72b`;
the 112-byte CUE has SHA-256
`106149772cdd6b12a460be98858e59d268fb1e01008d12b81f3eda80dd04ca28`;
and the 1,244-byte launcher has SHA-256
`83d3a23fa26c757f92437f773b3fbac6f5a5a482427ac414a92de2b281b11016`.
The 136,361-byte primary manifest at
`work/surface_soylent_campaign_v233_stage/manifest.json` and repeat manifest at
`work/v233r_stage/manifest.json` both have SHA-256
`b79d7a866ba29ad9a5f488bf6e004310f5a5a2c32ed73aaf676eee3154ac4d1a`.
The isolated primary and repeat V233 BINs and manifests match byte-for-byte.

The exact current Slot 1 upgrade is the fail-closed 75,617-byte
`tools/migrate_surface_soylent_v232_slot1_to_v233.py` helper, SHA-256
`3c7fe81b7657213c97090b8ba0a96d7551ea2a22dbb66cbc7fc5a65b484ea13f`.
It converts only the preserved 1,607,991-byte V232 field-567 state (SHA-256
`3f09a8cea70ce09c87b2bc0892ad8e427cc90d7fcf1759b8677413927c20b022`)
into the 1,457,268-byte V233 candidate at
`work/save_candidates/SLUS-00669_1_v233_from_3f09a8ce_field567_empty_terminal_native_init.sav`,
SHA-256
`b9b41cbc756300f6567a7c1cdc6b304e44bc57e025f1a4a51ff74aae84742acf`.
Exactly 456 decompressed bytes change: archive table 1, fixed-size resident
ATEL 127, relocated no-patient dialogue 307, and retired e4/e5/e6 scheduler 21.
All three exact native initializer bodies are queued from a verified 87-byte
cavity, and the action replaces a control-flow-dead former e16:s4 span; every
saved current/slot PC is scanned before either span is changed.
Fei's saved stance, party, GameState, field variables, camera, dialogue
windows, resident header/heap layout, and every unrelated actor byte remain
exact. Native allocator and callback proofs pin sprite recreation to the same
addresses without offline sprite edits. DuckStation must be fully closed
before the candidate replaces Slot 1; the immutable source backup must be
retained.

The guarded historical V231 state migration uses the 51,172-byte helper
`tools/migrate_surface_soylent_v230_slot1_to_v231.py`, SHA-256
`af84b5f52105315f7f27cd6d41350cd9b39ae023cc3deaf4a27e157c9ed4c295`.
It accepts only
`work/save_candidates/SLUS-00669_1_v230_patient_terminal_1eb8b434.sav`
(1,845,278 bytes; SHA-256
`1eb8b43472bece86bb46a0e50120d3ea31baa5c19b11418eb2818ce00245e2f3`)
and emits
`work/save_candidates/SLUS-00669_1_v231_from_1eb8b434_field592_patient_record.sav`
(1,670,155 bytes; SHA-256
`b8fd8b566aed92e68133739ea2eb1911a7f6742c923e467e63cde2c6986a214f`).
Its 2,504-byte report has SHA-256
`27b1faffa7c5b7151ab07eb667a165397ed9b70929a372909c025fe0f2fa6252`.
The migration changes only the four affected off-resident archive entries, one
resident terminal operand, retired ID45's unreachable dialogue cavity, and the
already-open window's two source pointers. It preserves component sizes, heap
neighbors, Fei, party, GameState, field variables, camera, every actor, and the
rest of every window. The captured old glyphs remain visible until one X closes
the preserved window; the next terminal interaction renders the new record. A
cold field reload uses ordinary V231 dialogue ID53.
The final repository discovery suite passes all 616 tests; the dedicated
V230-to-V231 migration suite passes all 11 tests.

The guarded historical V230 state migration uses the 50,554-byte helper
`tools/migrate_surface_soylent_v229_slot1_to_v230.py`, SHA-256
`92ae98a2811ec79c15c04dddd9f6eea9fe8153e5405a1f5e47b6a41f17c9c049`.
It accepts only
`work/save_candidates/SLUS-00669_1_v229_roundtrip_stuck_09d68876.sav`
(1,615,526 bytes; SHA-256
`09d68876b0c2ebf50f2b130d97f26bc6b8bd242aa84c154e96f8ef9e7ae17e5c`)
and emits
`work/save_candidates/SLUS-00669_1_v230_from_09d68876_field549_shifted_seal.sav`
(1,466,492 bytes; SHA-256
`36e5bbaf509f9cdeb4c86a3555175c5dd880002d9964eb73cf7cf69f4bfc070e`).
The matching 2,496-byte JSON report,
`work/save_candidates/SLUS-00669_1_v230_from_09d68876_field549_shifted_seal.json`,
has SHA-256
`ca74e80180a9c7dfcebbe45b8105d95b40cd59e3b0d70442bec023e094520504`.
Its 3,819,109-byte decompressed payload has SHA-256
`7cd05bcf4fc79c7d204812a9c6c42c6371da5cdf5f17033bdfae824318a1dc6c`;
the 1,419,163-byte compressed frame has SHA-256
`e3e765712039941a0e484c40f90590bb7b8be91c7355d7af625591e90a789ca8`.
Exactly seven decompressed payload bytes change at offsets `0x148DE`,
`0x10C73A`, `0x10C73C`, `0x112180`, `0x112188`, `0x1EF676`, and
`0x1EF67A`: one archive-table byte, two resident-ATEL position bytes, two
runtime-e16 position bytes, and two cached-header position bytes. The resident
cached header retains V229's component offsets with SHA-256
`f842bd2febf7f2c21d5ea63cefeafe065a19e063ae8665fa400ef907cac84698`,
while the prepared V230 media header has SHA-256
`27432b47d36a1d08438aa843146bfeccbae0efbd0370167ccbf00871a9914a21`.
The migration rebuilds the resident archive table for V230, preserves its
volatile tail, and keeps Fei, party, GameState, field variables, camera,
dialogue windows, e16's collision volume, and every unrelated actor byte
unchanged. It verifies the compressed round trip and never writes live Slot 1.

V229 remains available as the historical first archive-return collision
release. Its 698,814,480-byte BIN at
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v229.bin` has SHA-256
`436ecb3a053df1c6860aaedc356fa6db55d2749a27f51b4812166b117500ddc4`;
its 112-byte CUE at
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v229.cue` has SHA-256
`73812b56b1cb84b57cd8a8b1f9ecd5f67c1b983c475777dabee9d3f042c1083d`;
its 1,318-byte `output/PLAY_SURFACE_SOYLENT_V229.cmd` launcher has SHA-256
`c1c3a5343b4934aee225374223ec4db0ff73f2a26071c24289443aacda147bdf`;
and its 129,207-byte primary manifest at
`work/surface_soylent_campaign_v229_stage/manifest.json` and repeat manifest at
`work/v229r_stage/manifest.json` have SHA-256
`2dfba5b96913771b7cf97827d11d08c67336db190c9ebf208609dccf2d7749bf`.
The isolated primary and repeat V229 BINs and manifests match byte-for-byte.

The guarded historical V229 state migration uses
`tools/migrate_surface_soylent_v228_slot1_to_v229.py` (46,948 bytes; SHA-256
`c83112decd4d25013156ffe45a73ce42233a479aa4d41a0910a01039794861a9`).
It accepts only
`work/save_candidates/SLUS-00669_1_v228_source_cd84f8b5_field549.sav`
(1,632,883 bytes; SHA-256
`cd84f8b59d80398f81dc10f153633f4105be152f2c4f79b2fa73a33174debfa8`)
and emits
`work/save_candidates/SLUS-00669_1_v229_from_cd84f8b5_field549_seal.sav`
(1,485,222 bytes; SHA-256
`13ae2d667d8edd24ef60c1465f3e1771363823bcc4fd78c09064564a90eba21c`).
The matching 2,030-byte JSON report has SHA-256
`8927c34eb57f296b4804953d65a88c22920f2fd5865ff6e334ddf6807a6ba181`.
Its 3,819,109-byte decompressed payload and 1,438,158-byte compressed form have
SHA-256
`6c05487dfbf434f01ecf2c7a11fa6a9784c4d74df0be6e1947365788e06c698e`
and `0f3a002be787eafc2595fd5599cac9a0e7ccf1cd75c709c0d6b7d3ed16ca051f`.
Exactly two payload bytes change: field-549 ATEL offset `0x10C74D` changes
`0x0E -> 0x08`, and runtime e16 collision-radius offset `0x11217C` changes
`0x1C -> 0x10`. The V228/V229 archive tables remain byte-identical after the
V229 rebuild, including the volatile tail. Fei, party, GameState, field state,
camera, dialogue windows, actor records, and unrelated ActorData remain exact;
the helper verifies its compressed round trip and never writes live Slot 1.

V228 remains available as the historical private-clinic population release.
Its 698,814,480-byte BIN has SHA-256
`7bdb5fd17970abb15fc36f32a0907aafd132f80eae818e79ba21473380621deb`;
its 112-byte CUE has SHA-256
`0c3e3672f69969a0e1ced0e04d8dfc2f2298e706acf42b1c58292b4689c714fb`;
its 1,306-byte launcher has SHA-256
`471ec8019acb6057b152bad979ce5cbcdcf1e9b6a09516c6d989e12eb706f43d`;
and its 128,038-byte primary and repeat manifests have SHA-256
`39e5b82647ecece73fb61784eae7b3cdcf490e411887765b72a58ea8ed592244`.

The guarded historical V228 state migration,
`tools/migrate_surface_soylent_v227_slot1_to_v228.py`, accepts only the exact
1,735,278-byte V227 state with SHA-256
`23221b3468b77096fb9a8e07a11a32203fbd51e4c92d0b7fd203b036e30c1950`.
It emits
`work/save_candidates/SLUS-00669_1_v228_from_23221b34_clinic_aid.sav`
(1,735,287 bytes; SHA-256
`a991c4f8779bf0ce877fd6ef90806c757e08cde97abc2b2d05c692972164df64`)
and the 1,804-byte matching JSON report with SHA-256
`05d28f4752bc365e54539dc50a9a762f01a724d5787ae8910f8a5c172fc5c8b0`.
It changes exactly 2,464 serialized Disc 2 archive-table bytes for the four
newly populated room bundles. Field 621's resident script, header, actors,
runtime PCs, route, gameplay state, camera, dialogue, and walkmesh remain
byte-identical; the helper never writes DuckStation's live Slot 1.

V227 remains available as the historical Treatment Preparation release. Its
698,885,040-byte BIN has SHA-256
`108c753b964831ae6be61ca05fb8cbcd47240d27c0d4f376135828b4945596ed`;
its 112-byte CUE has SHA-256
`df061663cd9053e195513221997f4042d37c8d23fba9268e9d10bdafa577c134`.
The 122,987-byte primary and repeat manifests have SHA-256
`3a56b3ac97ce837c9356207df6a14d488a26cc0a63524472ba903bbae557fb67`.

The guarded historical V227 state migration,
`tools/migrate_surface_soylent_v226_slot1_to_v227.py`, accepts only
`work/save_backups/SLUS-00669_1_v226_intake_door_room_change_9436ef84.sav`
(1,910,685 bytes; SHA-256
`9436ef847164e1c850828da3c6f90a28ba1ea931763a3b691c6117e376333c82`).
It emits
`work/save_candidates/SLUS-00669_1_v227_from_9436ef84_treatment_preparation.sav`
(1,735,278 bytes; SHA-256
`23221b3468b77096fb9a8e07a11a32203fbd51e4c92d0b7fd203b036e30c1950`)
and the 1,809-byte JSON report
`work/save_candidates/SLUS-00669_1_v227_from_9436ef84_treatment_preparation.json`,
SHA-256
`ee5e4952da80a7eef27af2e39f88b824675c80a5ff1571b9816d7f44fcf003e4`.
Its exact 3,033-byte decompressed whitelist contains 3,031 archive-table bytes
and two resident route bytes, changing only `field 565/p3 -> field 594/p0`.
ActorData and runtime-PC bytes remain untouched; Fei, party, GameState, field
variables, camera, windows, loaded header, dialogue, and walkmesh are preserved
byte-for-byte.

The guarded historical V226 state migration accepts only the preserved
1,855,939-byte field-592 V225 state at
`work/save_backups/SLUS-00669_1_v225_auto_open_408a5dc9.sav`, SHA-256
`408a5dc96f5a2633079f8a41b09eefe669400b71a455bd5312fa9e0fc6cb22b9`.
It emits
`work/save_candidates/SLUS-00669_1_v226_from_408a5dc9_field592_x_only.sav`
(1,680,239 bytes; SHA-256
`a3aa3752e1b4b035b1f05f7cc0495bc4d4acd61f988923401e3ee8e30876e7bb`)
and a 1,629-byte matching JSON report with SHA-256
`bde8fc1e9c71a7036372ee26223914d549b4c0ffc811501b7849d279b5552b45`.
Its exact 70-byte decompressed whitelist contains four archive-table bytes,
62 equal-size resident field-592 ATEL bytes, and four entity-0 runtime-PC
bytes. It restores shared STOP `0x068C` and the retired poll cavity while
preserving the native e17:s2 X action at `0x0735`, Fei, every non-controller
actor, GameState, party, field variables, loaded header, walkmesh, collision
carriers, closed leaf, camera, and windows byte-for-byte.
The 3,819,109-byte decompressed payload has SHA-256
`3a256a7d4632d79fedd13488d1e7b95fecb038490f1cd1496e7db4abe25602cb`;
the 1,635,031-byte compressed frame has SHA-256
`d8e3cadf0ac9bbb80026c306c41212b8151147b4773127862ed5e8769000ef6f`;
finished RAM has SHA-256
`4a52a6df97f29cb9eb7a4aadbb48c86962bb08d0600853b9f81186f2fbf903bf`;
and the resident archive table has SHA-256
`3ee67d330d7a2c4b2bbdd8188dfa38a4a0152bea3950be3276d40a6ce8862a47`.

V225 is historical. Its image is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v225.cue`, launched by
`output/PLAY_SURFACE_SOYLENT_V225.cmd`; its BIN is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v225.bin`. Its BIN and CUE
hashes are
`539e2e33266d71337666c84d9d3a153dfd7555d8db933efadc49376483e6e1ff`
and `6a289550cec7003e9742d75f862db41d37214afe499d0dcddab1892839f6b8fd`;
its 119,944-byte repeat manifest at `work/v225r_stage/manifest.json` has
SHA-256
`2f6d433e9c257455e70fbc028a07335ec5b84790c646d7ff397f544a8ca1bb99`.
It remains the superseded automatic field-352 doorway-correction release.

The historical V217 migration candidate is
`work/save_candidates/SLUS-00669_1_v217_from_1114bf36_door_clearance.sav`
(1,679,396 bytes; SHA-256
`577668ae2ffd55b3132b68f5fa7d19a9f813e6f5769b8427f4362e47b63d8596`).
Its exact 60-byte decompressed-payload whitelist contains three archive-table
bytes, 46 allocator-safe resident-ATEL bytes, and 11 bytes confined to field
593's e20 runtime seal. Fei's exact position, the party, camera, GameState and
keycard, dialogue/windows, closed leaf, native Cross action, and retail
walkmesh remain byte-identical.

V216 is superseded but remains the historical post-keycard medical-diagnostics
release, launchable through `output/PLAY_SURFACE_SOYLENT_V216.cmd`. Its BIN is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v216.bin`, 698,642,784
bytes with SHA-256
`3764d6584fce3f590298cdc4e752432f4da1ec7770aa3416141296e6a79b4498`;
the 112-byte CUE has SHA-256
`5019b53f2c2ffa5e7b3a52cd194da14b2f36ba8207b5dd2c9210d7d77afce722`.
Its 117,430-byte manifest at
`work/surface_soylent_campaign_v216_stage/manifest.json` has SHA-256
`86725b90e4ac9f8b24d72111a8ce8090d5fc21af15ae9e80c4adea2bd3b66640`.
Its isolated repeat stage matched all 220 staged files byte-for-byte with zero
mismatches, all 32 replacement payloads read back exactly, and its complete
repository suite passed 518 tests and 6,212 subtests.

The exact post-keycard V215 Slot 1 was migrated to
`work/save_candidates/SLUS-00669_1_v216_from_ca850361_terminal_diagnostics.sav`
(1,685,638 bytes; SHA-256
`544c4c32c84412e52ddbfa8b85bfe4d79be2ae8eae9da44137584fbdfd562b40`).
That historical migration changes exactly 85 decompressed bytes: one V216
archive-table size byte and 84 bytes confined to resident dialogue ID 55. The
accepted-card flag, exact field position, party, camera, actor PCs, and
closed-window state remain byte-identical.

V215 is superseded but remains the historical carved-aperture and explicit
keycard-choice release, launchable through
`output/PLAY_SURFACE_SOYLENT_V215.cmd`. Its BIN is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v215.bin`, 698,642,784
bytes with SHA-256
`2ebd33059188333895db4ec2a2fbe80568d9707cfb7a464ebe49c4fa8d6af1c3`;
its 112-byte CUE has SHA-256
`fbce922f0018ae7ac6698e6c49b5d0e782659f4f2b9bcb87b23b99622157c275`.
Its 117,411-byte manifest at
`work/surface_soylent_campaign_v215_stage/manifest.json` has SHA-256
`537d03493d30503e315d9c273379bc50463dd95c04ff1c2476900441049ee176`.
Its isolated repeat stage matched all 220 staged files byte-for-byte with zero
mismatches, and all 32 replacement payloads read back exactly from the completed
BIN. The complete V215 repository suite passed all 508 discovered tests and
6,212 subtests with no failures, errors, or skips.

The allocator-safe migration of the captured V214 Slot 1 is
`work/save_candidates/SLUS-00669_1_v215_from_dcd01f7a_allocator_safe.sav`.
It is 1,674,270 bytes with SHA-256
`509b97a21526b1fb86ed0e19ac2be5743462a669d404a6dac01740d06871d195`.
The migration preserves the active field-593 window, actor PCs, GameState,
party, camera, heap headers, and trigger allocation while installing the
non-clipping text and explicit choice through retired resident script/dialogue
space.

V214 is superseded but remains the historical full-computer-bank patient-record
release, launchable through `output/PLAY_SURFACE_SOYLENT_V214.cmd`. Its BIN is
698,642,784 bytes with SHA-256
`b3bdc04631d89e44353e5f6d02f672a8237111189015675a4efcaab41f54ace8`;
its 112-byte CUE has SHA-256
`b6a0d53c65e5205a9e8f3505091e8f6c2e91d3a0330642a15031e5293cdf7f2c`.
Its isolated repeat stage matched all 220 staged files byte-for-byte with zero
mismatches, and all 32 replacement payloads read back exactly from the completed
BIN. Its 117,259-byte manifest at
`work/surface_soylent_campaign_v214_stage/manifest.json` has SHA-256
`c8dc22e80ec1cf95f54c272e3082de54bd2304a34b32dd2000b6d915e76cb9ea`.
The complete V214 repository suite passed all 497 discovered tests with no
failures, errors, or skips. The installed V213-to-V214 Slot 1 migration is
1,433,243 bytes with SHA-256
`d4617725cfb7c46c71f0555805632827c056f48aa4935e88d96c2092cad2a047`;
it changes only 81 audited payload bytes while preserving GameState, the open
medical record, the active script wait, and all three carrier sprites.

V213 is superseded but remains the historical first patient-record release,
launchable through `output/PLAY_SURFACE_SOYLENT_V213.cmd`. Its BIN had SHA-256
`9a2d781630e265af0f51ca01a801372d2766018f79a0bb5637818298c2b7e684`;
its CUE had SHA-256
`03c0ec7f3647ba91801dec48841ff9b1685cf23be2e5ca833f83a454e849dd71`;
and its 116,038-byte manifest had SHA-256
`8e1ce33f2fbb086a715be5070c119e10663a2a6c6d99823c6e4ce066e2a56a8b`.
Its final repository suite passed all 489 discovered tests with no failures,
errors, or skips.

V206 is superseded but remains available through
`output/PLAY_SURFACE_SOYLENT_V206.cmd`. Its 697,868,976-byte BIN had SHA-256
`de2413dcd94a976623168f5894ae13eb0afc81b6a6d8ab3bebd2d8e925211833`;
its 112-byte CUE had SHA-256
`b5eade571299297bdba56aae1dae07ee18638394afd24a435c6b9445ae4d5289`;
and its 96,523-byte manifest had SHA-256
`42ef530ce0014b572b68ea315d6291c390f86bc9e203e4f2159b2c59f2ac3284`.
Its isolated repeat preparation matched all 181 staged files, and its complete
repository suite passed 450 tests / 5,531 subtests.

V205 is superseded but remains available through
`output/PLAY_SURFACE_SOYLENT_V205.cmd`. Its 697,960,704-byte BIN had SHA-256
`d3a2ccd661eae4cd987393cecefe1232f9e76f003152e1dd1dfab1521cd3017f`;
its 112-byte CUE had SHA-256
`cef99704474501354888739bc89afbebebd710de0c567233a321494b993e050c`;
and its 95,691-byte manifest had SHA-256
`6c32ce00d63e33e6c03f53bf1ab726179c142d1fee6814bca27b9d3885cac50e`.
Its isolated repeat preparation matched all 181 staged files. Only the
route-owning replacement payloads for fields 565, 588, and 621 differed from
V204; the other 23 replacements remained byte-identical. The complete V205
repository regression suite passed all 447 tests.

V204 is superseded but remains available through
`output/PLAY_SURFACE_SOYLENT_V204.cmd`. Its BIN had SHA-256
`79b59e10776da09b1175691d717a51f9642b5016056e91c316d964c7c9631255`.

V203 is superseded but remains available through
`output/PLAY_SURFACE_SOYLENT_V203.cmd`. Its BIN had SHA-256
`09ab185c6c9f0d7742b3c84d8b6eacc1ef0135b6e309c799e9b38989a8321ee4`,
its CUE had SHA-256
`1a93580d5774fa138fe8c73a6bfa854462f92b62908e027553a63348136bb5ca`,
and its 90,061-byte manifest had SHA-256
`72da61a5db1bae02bd4586f25ac614a4c0279ea1622d4212c64ce58de100cfc8`.

V202 is superseded but remains available through
`output/PLAY_SURFACE_SOYLENT_V202.cmd`. Its BIN had SHA-256
`1acd87f65b4f986b74dcf0dff906b4eb48fde04013e1405b506b58791892eec0`.

V201 is superseded but remains available through
`output/PLAY_SURFACE_SOYLENT_V201.cmd`. Its BIN had SHA-256
`85f9deeda68d1ad5915c39011541e75a2f7867cc440208854669265bc1001b32`.

The superseded V199 package remains the historical phase-safe
physician-collision release with the clinic exterior-material defect. Its
launcher is `output/PLAY_SURFACE_SOYLENT_V199.cmd`; its BIN had SHA-256
`8049c25141251191c049bedfae484acfa9beb1f3ef04b19b8b7d593094f52659`,
its CUE had SHA-256
`75a60bab9a376c0a2ed7384b652f82cc7d10708812b02d313c4ad3a34a1a7d1f`,
and its 81,053-byte manifest had SHA-256
`03569ea1cfc03251d48b83fc95031cff7c8bfa6f97ec7eee32be0a84238ad0a3`.

The superseded V198 package remains the historical collision-safe patient-roaming
release with permanently ghosted physicians. Its launcher is
`output/PLAY_SURFACE_SOYLENT_V198.cmd`; its BIN had SHA-256
`fe1536e84d424e23363b0f5b20a0a253fae8355ab9b4824bd7dbf193bf70ff7e`.

The superseded V197 package remains the historical complete-dungeon release
with the shared Intake roaming rectangle. Its launcher is
`output/PLAY_SURFACE_SOYLENT_V197.cmd`; its BIN had SHA-256
`c1de9e3149ff9877d563c65ccabaaebdbaa86037b8499bab0373105423f9b92f`.

The superseded V196 package remains the historical one-door keycard release.
Its launcher is `output/PLAY_SURFACE_SOYLENT_V196.cmd`; its BIN had SHA-256
`956a76023d2f6665a74e6c4ed7373fa9b912d5a74bddbff86251a269aa14a950`.

The superseded V195 package remains the historical empty-medical-annex release.
Its launcher is `output/PLAY_SURFACE_SOYLENT_V195.cmd`; its BIN had SHA-256
`82cceca8dfb5814a94ebb5bf89787e4f4fdfb062593de604937a4d70f0e1c0fd`.

The superseded V194 package remains documented above as the historical Clinical
Stabilization Ward release. Its launcher was
`output/PLAY_SURFACE_SOYLENT_V194.cmd`; its 697,716,096-byte BIN had SHA-256
`e229febcfc5dff84dc5292e18256ed5899f3ff996573759e7fac92902773dd7e`.
