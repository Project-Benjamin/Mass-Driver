# Surface Soylent Campaign

This implementation reconstructs the cut Disc 2 Surface Soylent sequence as a
complete eighteen-room dungeon. It is the Ignas surface installation seen
during the narration, not the Disc 1 Etrenank facility.

V233 is the current playable release. It retains V232's occupied private
treatment-room records in fields 591--594 on the actual model-3 side
computer bank rather than an oversized aisle trigger. Three narrow,
facing-gated X carriers at `(80,-167)`, `(116,-167)`, and `(152,-167)` span the
visible workstation with effective `18 x 46` world-unit reach. The exact
field-593 Save 1 aisle position `(75.007858,-77.750687)` is outside all three.
All 1,201 reachable bank-front points work while Fei faces the workstation, and
none accepts the bed-facing heading. The distinct two-page patient records and
field-593 Quarantine-keycard Accept/Leave flow are unchanged.

V233 also activates that visible side workstation in field 567, the one
unassigned examination room with no doctor or patient. Retired entities 4, 5,
and 6 provide the same narrow, facing-gated coverage without adding a model or
collision actor. Pressing X while facing the workstation repeatably displays
`PATIENT RECORD / No patient is loaded for this room.` The bed and open aisle
remain silent, and the action awards no item and writes no progression state.

V232 retains V230's Classification Archive return-door correction in logical
field 549 without changing its deliberate-X action. The action-disabled e16
physical seal remains at `(-244,248)`, four units west and eight units north of
the e6 action center, deeper inside the aperture. Script radius `0x08` (16 world
units) and Fei's effective first-contact radius of 32 remain unchanged inside
e6's effective `36 x 40` world-unit X envelope. The exact V229 round-trip
southwest walking line clears the disk by 5.639 world units. The visible leaf,
native helper, and action carrier remain at `(-240,240)`. Holding Forward alone
still cannot open the door, and the complete closed-door cut through walkmesh
triangles 6, 10, 11, 12, and 13 remains blocked.

V232 also retains V230's X-only return-door contract in logical fields 550,
567, 591, 592, 593, and 594: approaching or holding Forward does not invoke the
action. All six clinical rooms use the same thin aperture-aligned rectangular
seal, and each leaf opens only after a fresh, deliberate X press on its existing
broad carrier. The seal's inner plane at `z=250` lets a centered Fei approach
the rendered leaf naturally, while the carrier still reaches the previously
reported off-center field-550 stance at approximately `(43.354,228.711)`. The
retail field-352 walkmesh remains exact in every room.

V228 populated private treatment rooms 591--594. V233 retains V232's rooms;
each keeps its examination bed and workstation while adding a doctor
administering aid to a different native Soylent demihuman patient. Both
characters are talkable. The four doctors use
distinct warnings that the procedure is private and direct Fei back to the
waiting area; the four patients remain hopeful about their care. Field 567 is
deliberately the one NPC-empty examination room, with only its no-patient
terminal readout, and field 550 remains the unchanged story doctor office.

V232 retains V231's lower-east Intake route inside this
facility. Security-keycard-gated entity 26 now enters logical field 594, a
bright, self-contained Treatment Preparation Room cloned from the same verified
field-352 Ethos clinic donor. Its examination bed and illuminated Solaris
workstation remain intact. The workstation's repeatable read-only display is
now its fin-armed patient's record:

```text
PATIENT RECORD: T-594-03
Type: fin-armed demihuman
Pulse 76 bpm / BP 108/68
Temp 37.0 C / Resp. 18/min

Hydration: NOMINAL
Metabolic response: 91%
Injection uptake: STABLE
Prognosis: IMPROVING.
```

The terminal writes no credential or progression flag. Like the repeatable
read-only terminals in fields 591 and 592, it drains the closing X press before
restoring control, so dismissing the readout cannot immediately reopen it. The
room's native e17 door returns only to `621/p5`. The superseded field-565 e7/p3
threshold is sealed and dormant as a future laboratory handoff, so Intake e26
does not expose the Service Manifold or Krelian's Lab.

V224's rendering correction retains V223's aperture-coplanar field-621 Intake
leaves, far-side-only threshold pathways, and `V=0x8D` cyan-shadow-row clamp,
then eliminates the persistent bottom-left wedge by replacing model 20's two
independently sorted lateral `POLY_FT4` halves with one whole-width
`POLY_FT4`. Its display packet is
`00 00 00 2D 97 89 97 8D B6 89 B6 8D`, with indices `(0,1,4,5)`.
The apron footprint, vertices, UV extent, leaf origins, static-node transforms,
interaction, collision, and camera data remain V223-identical. The pathways do
not overlap the accessible hall floor and are not rear plates, black boxes,
jambs, or vestibule walls.

The retail source proof is exact. Entity 24's 172-byte leaf is model 4
(SHA-256
`1c585299d3b1e67826303f5b668ed7cc04eede7f02b65174a4134c4ba0ae6e25`)
on plane `x=1645`, `z=793..882`. Its visible pathway is instead FT4 ordinal 4
in separate 560-byte model 19 (SHA-256
`7d2aab285a01c5561182f1a3db7f6f5eaefc1e806c22ecec256413315109a502`),
referenced by retail static-header entry 38 and retained as shifted entry 59 in
the expanded archive. Model 19 has 34 vertices, ten `POLY_FT4` records, one
mesh group, offsets `0x48/0x48/0x158/0x1AC`, and GPU-packet arena `0x190`.
The apron vertices are `(1601,0,793)`, `(1601,0,882)`, `(1645,0,882)`, and
`(1645,0,793)`, with indices `1,2,0,3`: exactly 89 units wide and 44 units
deep. Its texture states are `A8 00 00 C4` and `00 79 00 C8`; its packet is
`00 00 00 2D B6 95 B6 89 97 95 97 89`.

The ordering-table proof comes from the closed doors in V223 Save State 1,
preserved at
`work/save_backups/SLUS-00669_1_v223_persistent_bottom_left_clip_b9624646.sav`,
SHA-256
`b962464676e5c2b9a59918a5b9247d5d747276ab6ec0fc4a36c1f5f48ae96d24`.
Door helpers e47/e48 remain at their closed origin `(1733,0,0)`.
Door B's leaf packet at `0x1227CC` has projected XY
`[(140,90),(141,128),(115,106),(116,145)]`; model-20 lower half q0 at
`0x13B4B4` projects inside its lower-left area as
`[(116,145),(105,137),(129,137),(117,128)]`. The exact OT chain is
`0xB29F4 -> 0x1255E0 -> 0x125590 -> 0x1227CC -> 0xB29F0 -> 0x13B4B4 -> 0xB29EC`,
so q0 draws after and over the closed leaf. The other half, q1, is in bucket
`0xB2A08`, five buckets above the leaf, and draws first behind it. Door C proves
the same split with
`0xB2AC0 -> 0x1259F0 -> 0x125770 -> 0x122A58 -> 0xB2ABC -> 0x13B768 -> 0xB2AB8`,
while q1 is five buckets above at `0xB2AD4`. Aligned V222-to-V223 crops retain
the same triangular silhouette--924 changed pixels at `x=70..112,y=112..152`
far and 2,397 at `x=50..109,y=113..178` near--showing that V223's UV clamp
recolored the overdraw but could not correct its primitive depth split. Native
straight-door aprons use one FT4, including model-19 ordinals 0 and 5.

V224 keeps model 20 in its existing 396-byte allocation and keeps static nodes
60--62 and their pointers unchanged. One normalized copy of the retail
89-by-44 apron is now the single whole-width `POLY_FT4`; the other fourteen
records are degenerate `POLY_F3`. The model has 15 vertices, 15 primitives,
two mesh groups, offsets `0x48/0x48/0xC0/0x140`, GPU-packet arena `0x140`, and
SHA-256
`8ef50d3f377c7b8caf2fdcfa0fcaecebe3d25ce5a51a90dfa0f14a734fdf3b52`.
Its local bounds are `x=0..89`, `y=0`, `z=0..44`; there is no local negative-Z
or vertical geometry that could become a hall-side slab, rear plate, or
camera-near black ribbon. V224 retains V223's nodes 60--62 on the far side at
`[512,1645,0,1307]`, `[1024,1821,0,882]`, and
`[1024,1821,0,441]` respectively.

V224 preserves V220's model-2 camera cleanup byte-for-byte. Only native model
2's flat-black mesh groups 0 and 2 remain disabled in place: four `POLY_F3`
corner caps and 134 `POLY_F4` ceiling/fascia polygons have degenerate vertex
indices. The 4,836-byte native model has SHA-256
`b093460d49974a083f191442a2aaafb75983da7ed5ad78201b3d46f5b4b2bdd3`;
the retained V220--V224 model has SHA-256
`2d0b40fb67720162fe93bb3fa522d33c3cf3db8333865f3f8d7c897688fad5d3`.
Textured groups 1 and 3, all packet counts and offsets, and the allocation remain
intact. The complete V224 model archive remains 39,292 bytes with SHA-256
`b06e38c58fcd5e1ce5033e1135f0ae7c7d745b9ef37575f44b0cba4c936c52aa`;
the field-621 bundle is 135,648 bytes with SHA-256
`011be9593a2c565e6c3bb5f325ef64ac47811592794945ce529fcb3b6eb36677`.
Its 10,895-byte script has SHA-256
`a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c25fca52f202845ea7`,
and its 1,408-byte header has SHA-256
`bd8be9feef57bff074c81c885d66b329ed20456e42d3a11c6b8e03b18550598f`.

This remains allocation-neutral for model 20: one `0x28`-byte FT4 packet plus
fourteen `0x14`-byte F3 packets still requires exactly the `0x140`-byte GPU
arena. Relative to V223, V224 changes only the apron primitive topology and
associated model tables. A single coherent centroid depth now sorts the whole
apron behind a closed leaf, so no nearer lateral half can enter a later OT
bucket and cover the leaf. It does not change interaction volumes,
walkmesh/collision, model allocation, vertex geometry, static placements,
camera scripts, or camera data. An open leaf exposes the continuous short
native-style far-side apron, then the field's native black clear.

V226 removes the field-352 forward poll from its five logical rooms. Entity
0 script 1 again resolves to the shared STOP, and the verified retired
`0x044E..0x04A5` cavity has no active entry point. The aperture-aligned thin
rectangular collision seal remains centered at `(0,266)`, with physical contact
planes at `z=250/282`; the unchanged e17:s2 carrier is now the only way to open
the leaf. In fields 567 and 591--593 X selects the retained native return
action. In the doctor office it selects the unchanged bloodwork exit gate, whose
successful branch retains the native leaf action. Every retail field-352
walkmesh remains unchanged.

Field 594 inherits that same X-only doorway contract in V228, keeping the
shared field-352 clinical-room set to six rooms without
changing the donor walkmesh.

Historical V225 extended the field-352 doorway correction to logical fields
550, 567, 591, 592, and 593. It paired the same rectangular seal with a 63-byte
in-place forward poll at integer `z=228`; a post-action disarm loop prevented a
denied office exit from reopening its dialogue every scheduler cycle. V226
retires that automatic path in favor of deliberate X-only interaction.

V231 supersedes V216's historical post-keycard Fei readout in field 593. After
the Quarantine keycard has been accepted, every later interaction displays the
loaded A-593-12 record for the shelled patient beside that room's bed: pulse,
blood pressure, temperature, respiration, shell density, mineral balance,
treatment response, and clearance. The diagnostic path does not repeat the
one-time keycard award.

V224 retains V215's true apertures carved into the white Intake walls and
V220's removal of every finite black reveal used by V210 and V217--V219. The
full leaves remain visible at oblique camera angles because model 20 contains
only its top-facing far-side floor and model 2's disabled flat-black groups
cannot cross the camera near plane.

V224 retains V214's field-550 repeatable patient-record interaction on every
reachable section of the actual side computer bank to Fei's left: static node
27/model 3, with invisible entities 4, 5, and 6 anchored at `(80,-167)`,
`(116,-167)`, and `(152,-167)`. Each uses encoded X/Z bounds `0x01/0x0F`,
producing three overlapping effective regions with 18-unit X and 46-unit Z
reach. Facing is required: all 1,201 audited walkmesh points along the bank
accept terminal-facing use, while none accept the saved bed-facing heading.
The bed itself is never an interaction target.

The record reads the alias selected at Intake, Fei's mutable Status weight,
pulse, blood pressure, temperature, respiration, and neural observation, then
reports a `100% / PERFECT FIT` Biological Compatibility Index. The euphemistic
result foreshadows Fei's suitability for Sufal Mass integration without
exposing that purpose in the on-screen record. Missing or legacy registration
data fails closed with no active-patient response, and the readout never changes
clinic progression. V213 remains the historical first patient-record release;
V214 is the historical release that corrected which room fixture can invoke
that record, and V224 retains the correction unchanged.

V224 retains V212's fix for the doctor-office exit race
captured in Slot 1: field scripts run in eight-opcode slices, and the exit gate
previously yielded after saving `OFFICE_ACTIVE` in field-local word `0x07C6`.
The lower-ID doctor update then replaced that word with refusal stage 2 before
the gate resumed, causing the native exit to release its solid seal. The gate
now owns private field-local word `0x07D0`, so the locked notice remains active
until the security sequence genuinely reaches `RESOLVED / COMPLETE`.

V224 retains V211's current-content boundary. The saved field-620 stance is on
triangle 182 directly in front of the east continuation controller, entity 24.
Every fresh X press there now displays exactly `This is the end for now.` and
`The rest is coming soon...`. It plays no door sound, does not animate or open
the leaf, does not change fields or write progression state, and drains the
closing press before restoring control. The west entity-23 return to Intake
remains usable, so the notice cannot trap the party.

V224 retains V222's restoration of all three V209 examination-room leaves to exact aperture
co-planarity, and the two straight-wall doors remain in separate native bays
444 world units apart. Once a leaf opens, its native-style threshold apron
extends away from the hall on the far side of the aperture. It shares only the
leaf-plane edge with model 1's hall floor, leaving no overlapping slab, rear
plate, black border, ceiling slab, or camera-facing triangle. Field 593's terminal visibly holds the
Quarantine keycard and asks `Accept it` or `Leave it`. Leaving is repeatable
and produces no state
change or sound. Accepting plays the item sound, shows the acquisition receipt,
and awards the card that directly opens both the marked Intake e22 Quarantine
door and Service e10. In V231, subsequent interactions show the current
shelled patient's diagnostic record instead of an already-removed notice or
Fei's unrelated office record.

The check-in terminal still performs its original six-panel opening and closing
animations. Its repeat menu is now only Fei, Elly, Citan, and Exit. The
unrelated retail `Unlock codes` / `Input process` / `Code schema` branch and its
binary values are unreachable.

The clinic security victory unlocks Intake entities 24, 26, 43, 44, and 45.
Entity 24 remains the patient-service route into field 565. Entity 26 instead
enters the independent Treatment Preparation Room at `594/p0`; its field-594 e17
return lands only at `621/p5`. Service entity 9 enters the bright field-588
scanner annex, whose return lands at `565/p5`. That scanner arms only the
bio-interface cutoff. It does not issue a credential. Logical field 593 is the
sole Quarantine-keycard source, and field-565 e7 remains sealed for a future
laboratory handoff.

A fresh New Game grants every native on-foot deathblow across all eleven
character and form records. Chu-Chu and Maria have no native on-foot
deathblows, so no commands are invented for them. Character levels and stats
remain unchanged because the retained Perfect Works canonical 2607 already
sets the native deathblow learning gates to level 1.

The campaign is built by
[`tools/build_surface_soylent_campaign.py`](../build.py)
on top of the frozen v173 reciprocal-door conversion. Its data model is
[`tools/surface_soylent_campaign_blueprint.py`](../tools/surface_soylent_campaign_blueprint.py),
and the machine-readable design contract is
[`content/surface_soylent_v1/dungeon_plan.json`](../content/dungeon_plan.json).

## V233 boundary and current topology

The authored reciprocal graph remains the planned foundation. V233 retains
V232's field-620 e24 as the dialogue-only current-content boundary:

```text
                                      [549 Classification Archive]
                                                |
[623 Tissue Transfer] <-> [621 Intake / Triage] <-> [620 Quarantine] --e24--> [CURRENT END NOTICE]
                                  |  |  |  |  |  |
                [550 Story Office] [567 Empty Exam] [594 Private Aid / Preparation]
                       [591 Private Aid A] [592 Private Aid B] [593 Private Aid C + Keycard]
                                  |
                    [565 Service Distribution Manifold]
                         |       |       |       |
                    [588 Scanner] [589 Resonance] [590 Clinical Ward]
                                                     |
                       [623] <- [622 Sufal] <-> [625 Meld]
                                      |                |
                                 [624 Sorting] <-> [626 M-Core]
```

The field-594 spoke is reciprocal only with Intake p5. The downward Service
spoke is the separate `621/p1 <-> 565/p0` patient route; field-565 e7/p3 has no
active graph edge in V233.

The intended clearance sequence is:

1. Defeat the clinic security team in field 550 to receive the Security
   keycard (`0x021A`, bit 0).
2. Use Intake e26 to explore the self-contained field-594 Treatment Preparation
   Room, whose read-only terminal reports the fin-armed patient's vitals and
   treatment response and whose e17 exit returns to Intake p5. The sealed
   field-565 e7 threshold is not an endpoint.
3. Explore the three new Intake examination rooms. Field 593's terminal has the
   inserted Quarantine keycard (`0x021A`, bit 8) and explicitly asks whether to
   `Accept it` or `Leave it`. Leaving is repeatable, silent, and state-neutral.
   Accepting plays the item sound and receipt once and awards the card. Every
   subsequent interaction reports the shelled patient's vitals, shell density,
   mineral balance, treatment response, and clearance instead of an empty-slot
   notice or Fei's office record.
4. Present the Quarantine keycard directly at Intake e22 or Service e10 to enter
   field 620. At the saved east-side e24 threshold, X displays the retained two-line
   current-content notice instead of running the former relay-gated transition.
   Use west e23 to return to Intake.
5. The former e24 relay-completion gate, its `565/p6` destination, and the
   authored production back half remain frozen as dormant future foundations;
   V233 does not activate them from this endpoint.

All three new Intake doors use forgiving rectangular interaction volumes. The
retained outer walkmesh wall is their closed collision barrier, so no invisible
seal overlaps the hallway. Each leaf occupies a true carved wall aperture. A
396-byte allocation-preserved model 20 remains attached to static nodes 60--62.
Its one whole-width `POLY_FT4` reconstructs one retail model-19 apron at each
door; fourteen degenerate `POLY_F3` records preserve the allocation. Each
apron occupies only local `z=0..44` on the far side; local negative-Z is the
accessible hall and remains empty. Both far-depth vertices stop at `V=0x8D`,
retaining V223's exclusion of the source texture's near-black `0x8E..0x95`
tail without changing the apron footprint. The whole apron now receives one
centroid depth and one OT position, eliminating the lateral-half sort split.
Model 20 and model 1 share only the
aperture edge, never positive floor area. Native black clear begins beyond the apron
through an aperture exposed by an open leaf. Native model 2's
disabled flat-black groups 0 and 2 cannot sweep a ceiling slab or diagonal band
across the view; textured groups 1 and 3 remain intact. Each room's native
animated exit returns to Intake parameters 7, 8, or 9 at a point outside the
corresponding held-X volume.

## Historical V207 physical layout

Every line below is a reciprocal X-button-door topology. The clinic security
keycard remains the boundary between public Intake and the restricted network.
Patient-transfer e24 (`621/p1 -> 565/p0`) enters the Service Manifold after
operand `0x021A` bit 0 is set. Freight e26 (`621/p5 -> 588/p0`) enters only the
independent Clinical Quarantine Credential Laboratory and uses the compound
V207 gate: the same Security keycard plus tone authorization at `0x021E` bit 9.
The field-588 return goes directly to `621/p5`. The displaced field-565 p3 and
p5 thresholds now form an internal
reciprocal bypass instead of duplicating either external route. V202 separates
the deeper gates. Field-565 e12 retains its native input action and opens only
after `Up, Down, Up, Left, Right`; its success sets tone authorization at
`0x021E` bit 9 and releases both the native carrier and the added physical seal.
After that compound door admits the party, field-588 e4 is aligned with the
bright clinical room's obvious diagnostic scanner. It performs no second tone
check, arms the bio-interface cutoff, and issues a distinct Quarantine keycard
at `0x021A` bit 8. Field-565 e10 accepts that later credential and admits
the party to Quarantine Diagnostics from the service side. The field-620 relay
consensus then sets `quarantine_complete` and unlocks lobby e22 as the reciprocal
return to Intake. This orders the puzzle, passage, credential, and Quarantine
threshold without opening Quarantine early. V195's e25 staff threshold remains
the one-door medical exploration annex at logical field
567. V201 separately recovers the preserved Clinical Stabilization Ward at
logical field 590. Field 565 has two distinct reciprocal thresholds into that
ward: `565/p1 <-> 590/p0` and `565/p2 <-> 590/p1`. The ward's third paired door
owns the four-clearance production gate at `590/p2 <-> 624/p0`.

```text
                                      [549 Classification Archive]
                                                ⇅
[623 Tissue Transfer] ⇄ [621 Intake / Triage] ⇄ [620 Quarantine Diagnostics]
          ⇅                  ⇅  ⇅  ⇅                        ⇅
          │             [550] [567] [588 Credential Lab]  │
          │                  ⇅ patient-service             │
          │        [565 Service Distribution Manifold] ────╯
          │                  ⇅               ⇅⇅
          │             [589 Resonance] [590 Clinical Ward]
          │                                   ⇅ production clearance
          ╰──── finale [622 Sufal Generation] ⇄ [625 Meld] ⇄ [626 M-Core] ⇄ [624 Sorting]
                 shortcut

[550] = Intake Examination Office
[567] = Unassigned Medical Examination Room
[588] = Clinical Quarantine Credential Laboratory
```

The doubled `⇅⇅` marks the two independent Service-Manifold/Ward door pairs; it
does not represent an automatic transition or a shared destination parameter.

The apparent loop on the lower line is intentional. Once the security keycard
admits the party to the Service Manifold, the resonance clue, native service
input, visible diagnostic scanner, Quarantine relays, and remaining authorization
work open production. The ward is the recovered clinical bridge into the
existing cut-Surface back half, which follows one explicit order:
`590 -> 624 -> 626 -> 625 -> 622`. Securing the local node opens the emergency
`622 -> 623` return and leaves the completed dungeon explorable as one
navigable circuit. V197 does not force a world-map, title-screen, or other
external handoff after the Sufal epilogue.

The north transfer threshold in field 623 now uses the same native blue paired
bulkhead leaves seen on the field-621 side. Both leaves open for 32 frames with
the retail door sound before the room transition. The implementation reuses
field 623's existing model 10/11 assets and textures; it adds no imported door
art. Because the leaves originated at the opposite-facing south threshold,
their north-door instances use a 180-degree Y rotation so their rendered front
faces, not their culled backs, face the arriving party.

## Historical V207 progression

V207 retains the connected post-clinic dungeon and makes the deeper access
sequence explicit:

1. The field-550 security victory awards the security keycard at `0x021A` bit 0.
   Lobby e24 then enters field 565. Lobby e26 recognizes the card but remains
   sealed until the five-tone authorization is also present.
2. Field 589 plays the authentic five tones and records only that the clue was
   seen at `0x021E` bit 8. It does not grant access. The sequence is
   `Up, Down, Up, Left, Right`.
3. Repeating that sequence at field-565 e12 runs its complete native password
   action. Either native success path sets tone authorization at `0x021E` bit 9
   and releases the sliding passage; wrong input retains the native failure
   behavior and leaves the passage sealed.
4. Return to Intake and use e26 to enter the independent field-588 Clinical
   Quarantine Credential Laboratory. The door checks the Security keycard and
   tone authorization together. Inside, entity 4 is aligned to the obvious
   diagnostic scanner; it does not recheck tone authorization, but arms the
   bio-interface cutoff and awards the distinct Quarantine keycard at `0x021A`
   bit 8. Its
   item sound and receipt occur once, and independent commits let a torn save
   recover whichever of the two awards is missing.
5. Field-565 e10 accepts only the Quarantine keycard and enters field 620 from
   the service side. Completing the biological relays records
   `quarantine_complete`, unlocks the service return, and releases lobby e22 as
   a convenient Intake shortcut.
6. Field-565 p1 and p2 lead through separate reciprocal doors to field-590 p0
   and p1. The preserved room provides the missing Clinical Stabilization Ward
   without restoring its retired surgery event.
7. With the security keycard, tone authorization, Quarantine completion, and
   bio-interface authorization, the ward's production bulkhead at field-590 p2
   opens into field-624 p0.
8. Field 624 diverts living tissue, nanomachine medium, and unstable Meld away
   from production. A completion receipt confirms that all three feeds are
   isolated before the route to field 626 opens.
9. Field 626 disables fusion and pattern alignment while retaining containment.
   Its completion receipt confirms the safe-state calibration before field 625
   becomes available.
10. Field 625 expands the Meld reveal into a party response: Fei, Elly, and Citan
   acknowledge the people within the amalgamation and commit to stopping the
   line before the route to Generation opens.
11. Field 622 retains the save console and native Sufal battle configuration,
   but its conclusion uses a recoverable phase sequence. The native post-battle
   sync records a pending victory, the epilogue completes the local shutdown,
   and only then does the secured phase open the emergency return. Reloading or
   re-entering during the pending phase resumes the epilogue instead of
   replaying the battle or silently skipping the shutdown dialogue.

Defeat cannot mark the node complete, and a secured node cannot be fought
again. The outcome is deliberately local: this Ignas node is complete while
other Surface systems remain, and the party retains control to save, backtrack,
or use the explorable emergency-return loop.

### Intake registration and patient records

Version 183 makes the actual desk receptionist identified by the user's saved
field-621 stance interactive. This is entity 13, not the nearby survivor who
already has a separate conversation. Her retail 64-unit circular interaction
range could not cross the counter to the saved 131.61-unit straight-on stance,
so her visible actor now owns a non-blocking, no-facing rectangular X target
with effective half-extents 80 by 144 units. Before registration she directs
the party through the rear north double door, entity 21, directly behind that
stance. The door enters the Classification Systems Archive in field 549.

The archive terminal offers a one-time intake choice among the full cover
identities `Aron Voss`, `Noel Ardan`, and `Kiro Dalen`; Fei's real name is not
offered, and canceling creates no record. Accepting an alias sets the persistent
intake-registration flag. The original first-name order and packed alias codes
remain unchanged, so an existing appointment save retains its selected
identity. Later visits expose repeatable Fei, Elly, and Citan patient records,
and the receptionist recognizes that registration has already been completed.
V203 makes that post-check-in response explicit: “I see you have signed in.
Please wait here until your name is called.”

Version 191 also restores the terminal's original presentation around the
custom check-in workflow. Every first-use and repeat-use interaction runs the
retained field-549 player-use beat, terminal sounds, and staggered scale-up of
all six native screen panels before showing the custom menu. Cancel,
registration, patient-vitals, and Exit paths launch those panels' matching
native scale-down scripts before returning control.

Patient weight is not a hard-coded biography value. Each terminal action uses
retail extended field opcode `EX69` to read the character's mutable live Status
weight, applies the game's `x2.20` conversion, and splits the result across two
dialogue parameters for a decimal pounds readout. A clean Surface start reports
Fei at 167.20 lbs, Elly at 92.40 lbs, and Citan at 158.40 lbs; food or other
retail weight changes are therefore reflected on later reads. Height remains
fixed profile data, while pulse, blood pressure, temperature, respiration, and
clinical observations are authored facility readouts rather than retail
character statistics.

V209 removes `Archive records` from the repeat menu because its binary
unlock-code material is unrelated to registration or Quarantine access. The
terminal still opens all six original panels before the custom menu and closes
them through their native scripts on every registration, vitals, Cancel, and
Exit path.

Version 189 restores the intended pre-revelation tone of the Intake waiting
area. All eight adult patients sincerely expect the staff, screening, and
treatment to help them; none speaks as though they already know the Soylent
system's purpose or the fate of people sent deeper inside. Their dialogue is
hopeful without changing the darker discoveries in Quarantine, Meld, or Sufal
Generation. The little boy remains entity 11, dialogue 7, and still says
`I like turtles!` exactly.

### Timed clinic appointment

Version 184 persists the selected alias and starts a 60-second play-time timer
only when the party leaves field 549 after registration. On returning to the
Intake hall, a physician emerges through the saved-position east office door,
walks to reception, and automatically calls `Aron Voss`, `Noel Ardan`, or
`Kiro Dalen` to match the terminal choice. Version 186 gives that lobby actor the exact actor and
sprite bank used by the physician inside field 550, so he is the same person on
both sides of the door. Fei remains controllable throughout the timer and every
physician walk; only dialogue and combat lock input. Every survivor,
receptionist, and office-denial window in the lobby publishes a field-local
mutex, so the automatic alias call waits for an existing conversation to close
instead of overlapping it.

Closing the automatic call cannot count as talking to the physician. A fresh X
press makes him say `Follow me into the examination room.`, after which he
opens the leaf and walks through while Fei remains controllable. Version 192
leaves that lobby leaf visibly open when the physician disappears inside, and
the entered-phase door action takes Fei directly into the office without
closing or replaying the opening. A field-local open flag distinguishes that
live handoff from a genuine field reload; if the persistent entered phase is
restored in a newly loaded lobby with a closed leaf, the native opening action
runs normally instead of transitioning through a closed-looking panel. Logical
field 550 uses Disc 1 field 352's intact Ethos infirmary room, including its
examination bed and native animated exit. On entry the physician begins the
requested bloodwork and injection briefing.

Trying to leave before the procedure first reports `The door is locked.`, then
has the doctor insist that the procedure continue. Two distinct conversations
with the physician advance Fei's refusal and the doctor's final warning; held
Cross is drained after each window so one press cannot collapse the interactions
together. Version 190 opens the retained office leaf, hidden-snaps the two exact
Solaris Guards and two Security Cubes to the last exterior threshold point, and
reveals them on 0/6/12/18-frame staggers. Their visible doorway legs are bounded
to 16 movement steps instead of 180, and each finishes with the engine's dynamic
actor-to-party-leader turn, so they cross promptly and face Fei from four
different endpoints. The leaf closes before their fixed, no-Escape on-foot
battle. That fight now uses retail arena `0x30`, whose bright silver-white
technological walls match the examination office far better than dark arena
`0x3B`. Version 196 makes victory award a visible credential rather than an
abstract scanner approval: item sound `0x37` plays, then a receipt reports
`SECURITY KEYCARD ACQUIRED` and authorizes `FREIGHT / SERVICE`. Only after that
receipt closes is operand `0x021A` bit 0 set, so defeat cannot silently unlock a
door. In V197 the keycard remains one of the four production-bulkhead
requirements and opens both genuine Intake-to-service thresholds: e24 from
`621/p1` to `565/p0` and e26 from `621/p5` to `565/p3`. It also authorizes the
field-565 e12 service passage and e10's service-side entry into Quarantine. The
doctor then panics and follows a connected walkmesh route to the door, opens the
leaf, crosses the threshold, disappears outside, and closes it behind him while
Fei remains controllable. The office exit enables only after that departure
completes.

Version 188 fixes the north Archive threshold observed in the user's live
field-621 Slot-1 state. The room's nine retail survivors still run their native
random-walk actions, but each initializer now installs the engine's native
four-corner movement bound. Its clockwise rectangle spans X 500 through 1250
and Z 1350 through 1680, ending 152 world units inside the closed entity-21
Archive leaf at `(867,1832)`. The two retail starts already inside that margin
move from `(726,1799)` to `(650,1650)` and from `(882,1732)` to `(950,1650)`.
All nine resulting starts are distinct and belong to exactly one walkmesh
triangle, so the survivors continue roaming without entering, overlapping, or
passing through the closed door.

V183 savestates recorded completion but not the chosen alias. On the first
V184 Intake load, those states receive one explicit alias-confirmation menu;
legacy Slot-1 states follow that migration path. New registrations persist the
alias directly and do not need confirmation.

## Lore boundaries

- The facility belongs to the worldwide Surface Soylent network and remains
  distinct from Etrenank.
- The Verus crisis follows the limiter's collapse and Krelian's virus, before
  the Gaetia Key.
- Solaris classification language is presented as dehumanizing administration,
  not an objective account of who remains human.
- The Gazel Ministry's M Project overlaps Krelian's plans but is not treated as
  identical to them.
- Meld is made from multiple people; it is not described as one former person.
- Securing this node does not end the wider crisis. Other surface installations
  remain, preserving the canonical Disc 2 scope.

## Technical guarantees

- 18 rooms, 20 reciprocal door pairs, and 40 physical X-button endpoints.
- No reachable coordinate-triggered field changes.
- Every arrival point is inside an audited walkmesh triangle and outside the
  matching door's held-X retrigger volume.
- Thirty-seven reciprocal endpoints separate their broad X-button target from
  an action-disabled, immovable physical seal. The three new Intake-side panels
  instead sit directly on the retained outer-wall walkmesh boundary, which is
  already an authoritative closed barrier. Axis-aligned Surface panels use a
  thin seal on the panel plane; diagonal donor thresholds use a circular seal.
  This prevents corner snags without making a closed door walk-through or
  letting collision consume X.
- Donor seals are released only after their authentic leaf animation succeeds
  and before the scripted party walk. Denied or incomplete gate checks keep
  the corresponding seal closed.
- Authentic panel animations are retained or promoted to finite 32-frame
  helpers before transitions.
- All eighteen rooms initialize the native Krelian Lab corridor cue heard in retail
  fields 565 and 567, music ID `0x3D`. This intentionally excludes ID `0x3C`,
  the Kislev/Nortune infiltration cue also used at two lab thresholds. Disc 2 already
  contains the exact `0x8D` wave bank and `0x8E` sequence. The field engine's
  same-ID check preserves the playing sequence across ordinary room
  transitions instead of restarting it.
- The original 66 Surface-authored dialogue blocks are checked against the
  retail font grid. Version 179 repairs 77 overwide lines in 45 blocks with
  explicit word-boundary line/page breaks. Version 183 adds 11 explicitly
  sized receptionist and check-in blocks, Version 184 adds nine explicitly
  sized appointment/clinic blocks, and Version 186 adds six refusal, security,
  and escape blocks. Version 189 rewrites only the eight adult field-621
  waiting-room blocks as hopeful, pre-revelation patient dialogue; retained
  retail dialogue remains byte-exact, and the intake boy still says
  `I like turtles!` exactly.
- Version 180 widens only the field-549 Classification Archive return door's
  ghost action target along its approach axis, from `0x0A` to `0x0C`. The exact
  formerly failing Slot-1 stance at `(-212.4679108, 201.5092010)` is covered;
  the separate action-disabled circular physical seal remains unchanged at
  radius `0x0E`.
- Version 182 swaps the rooms behind the two Intake thresholds identified in
  the user's live three-step audit. Field 621 entity 22 at `(88,840)` now
  enters the Step-2 crowded biological room in field 620, while the north
  double-door entity 21 at `(867,1832)` now enters the field-549 Classification
  Archive. Their field-620 and field-549 return actions lead to field 621
  parameters 2 and 0, respectively, so both routes remain reciprocal. The
  field-565 patient-manifold route remains on its native parameter-1 Intake
  return. Only four checked
  `CHANGE_FIELD` operands change; physical leaves, animations, collision seals,
  entries, graphics, models, and walkmeshes remain attached to their doors.
- Version 183 repoints the STOP-only action slot and initializer of field 621's
  saved-stance receptionist, entity 13. Her original sprite and position remain;
  the initializer adds a ghosted, no-facing `0x20/0x40` rectangular X target
  whose effective 80/144-unit half-extents cover the exact saved desk stance
  without adding collision. Her directions identify rear door entity 21 and
  the field-549 check-in terminal. One-time alias registration persists,
  patient records remain repeatable, `EX69` supplies live Status weight for a
  decimal pounds conversion, and the retained retail Archive records branch
  remains available.
- Version 184 adds the alias-backed 60-second appointment, a nonblocking doctor
  actor and finite lobby walk, a state-gated office door, and the automatic
  bloodwork/injection briefing. Appointment state is isolated from field 620's
  relay-selection word, and the title reset clears the packed alias/timestamp.
- Version 185 moves the physician's lobby endpoint from `(1080,1375)`, where
  runtime resolved him onto sloped triangle 191 at `y=-20`, to `(1200,1400)`
  on flat triangle 36 at `y=0`. The revised route clears the captured Fei,
  Elly, and Citan positions by approximately 98, 139, and 184 units.
- Version 186 leaves Fei controllable during the appointment timer and all
  physician walks, replaces field 621 actor/sprite bank 6 with the exact
  field-352 physician bank used inside the office, and moves bank 6's previous
  civilian user to the existing civilian bank 3. Its office state machine adds
  an exit insistence, two input-separated refusals, a fixed no-Escape Solaris
  security fight, a victory-only clearance state repurposed as the security
  keycard in V196, and a physician escape
  during which Fei stays controllable. Persistent substages safely resume the
  sequence after a field reload or savestate without duplicating a completed
  battle.
- Version 187 gives the called security team a complete overworld entrance:
  exact Disc 1 Solaris Guard and Security Cube actor/sprite banks replace two
  unused office banks, four new field actors stage outside, the retained leaf
  opens, and all four responders walk inside before it closes and combat begins.
  The physician now approaches the leaf over a strictly edge-connected walkmesh
  route and opens it only at the threshold. That release froze the intended
  routes but checked only triangle geometry: it missed the exterior strip's
  non-walkable material, so bounded walks could still expire and fall through to
  their endpoint correction. V200 supplies the missing actor-local traversal
  permission. Reload-safe entrance and battle-pending substages prevent an
  interrupted entrance from skipping or duplicating combat.
- Version 188 preserves slot-1 `WALK_RANDOM_DIRECTION` for all nine native
  field-621 survivor actors while their initializers install exact 18-byte
  `OP17` clockwise movement bounds. The shared X 500..1250, Z 1350..1680
  rectangle keeps a 152-unit interior margin from the north entity-21 Archive
  leaf; entities 9 and 10 receive distinct on-mesh starts inside the bound.
  This historical fix prevented entry into the north threshold, but a later
  runtime save proved that its shared rectangle still crossed the real west and
  east waiting-room walls. V198 supersedes the shared-zone portion.
- Version 189 changes only final field-621 dialogue blocks 2-6 and 8-10 for
  adult waiting-room actors 6-10, 12, 14, and 15. Exact-text and font-grid
  checks keep every line inside its 58-by-4 window, enforce the patients'
  hopeful pre-revelation knowledge boundary, and freeze entity 11/block 7 as
  `I like turtles!<Close>`.
- Version 190 changes field-550 dialogue ID 54 to a two-page locked-door notice
  and physician response. It also freezes the exterior `(8,261)` reveal,
  interior `(-1,237)` crossing, 0/6/12/18-frame stagger, 16-step per-leg bound,
  and `FE 17 actor FF` dynamic Fei-facing command for all four responders.
- Version 191 restores field 549's exact native six-panel opening body before
  every custom registration and records menu. Custom branches launch the exact
  native close scripts; `Archive records` releases control and enters the
  already-open retail menu at `0x010F`, preventing both recursion and a second
  opening. The three stable alias codes now display the full cover identities
  `Aron Voss`, `Noel Ardan`, and `Kiro Dalen` everywhere the terminal,
  receptionist migration menu, and physician use them.
- Version 192 replaces the lobby physician's `I will go first` instruction with
  `Follow me into the examination room.` After his return walk, field 621's
  entity-31 leaf remains at its fully open 64-unit endpoint; the physician hides
  and commits the entered phase without calling its close script. A field-local
  open-state word lets the next X action transition directly to field 550
  without snapping or replaying the leaf, while initialization clears that word
  so a genuine lobby reload safely uses the retained native opening action.
- Version 193 decoded the Slot-1 capture (SHA-256
  `a2e28eee8da9b4db14477bc8251e6c83b22bc840a0bfd2d091818eebe08fe62d`)
  as field 621, Fei/e3 at `(69.98291015625,840)`, triangle 18, yaw `0`, facing
  side-corridor controller e22 at `(88,840)`. That historical release held e22
  closed while preserving its exact field-620/p0 opening action. V197 gives the
  preserved action its final purpose: it remains locked on initial Intake
  exploration, then `quarantine_complete` releases it after the party enters
  field 620 through service-side e10 and solves the biological relays.
- Version 194 decodes the newer Save State 1 marker as field 621, Fei/e3 at
  `(69.98291015625,396)`, triangle 14, yaw `0`, directly facing staff-door
  controller e25 at `(88,396)`. Its former field-565/p2 destination now enters
  field 567/p0. The Clinical Stabilization Ward is inserted into the staff route:
  its first native paired door returns to field 621/p4, its second paired door
  continues to field 565/p2, and field 565's staff-side door returns to field
  567/p1. Field 567 retains its retail paired-leaf animations and native music
  selector `0x3D`; its third door is a sealed restricted-procedure threshold.
  The southwest and restricted thresholds use independently audited `0x1C`
  circular seals (72 world units at player contact), because their native
  paired leaves are visual helpers rather than physical colliders. The service
  threshold retains the standard `0x0E` seal. All three closed doorway chords
  are disconnected without placing either playable arrival inside a seal.
- Version 195 supersedes that staff-route topology while preserving V194 as
  historical evidence. Field 621/p4 controller e25 still enters logical field
  567/p0, but logical field 567 now transplants Disc 1 field 352 as an empty,
  one-door medical examination room. Its exact static examination bed and full
  surrounding environment remain intact. It exposes no doctor, NPC, dialogue,
  automatic story event, scripted battle, or random encounter. Its sole exit,
  field-567 controller e17, returns to field 621/p4. The former field-565 e6/p2
  staff route is physically and action sealed. The complete V194 Clinical
  Stabilization Ward donor remains preserved in
  `content/surface_soylent_v1/reserved_room_donors.json` and reproducible through
  `tools/surface_soylent_campaign_donor567.py`; it stays outside the active
  topology from V195 through V200 before V201 recovers it at a new logical field.
- Version 196 repurposes retail's former scanner-approval allocation at operand
  `0x021A` bit 0 as the persistent security keycard. A field-550 security victory
  plays item-retrieval sound `0x37`, shows the `SECURITY KEYCARD ACQUIRED`
  receipt, and sets the bit only after that receipt closes. Field 621 controller
  e26 is the exact Slot-1-marked freight door at `(1645,396)`; before the award,
  its new gate reports that the door is locked and requires a security keycard
  without playing the door sound, moving its leaf, or changing fields. After the
  award, it releases the byte-preserved action for `621/p5 -> 565/p3`, whose
  reciprocal endpoint returns to `621/p5`. V197 extends this same credential to
  e24, e12, and service-side Quarantine e10 rather than leaving e26 as an
  isolated alternate entrance.
- Version 197 connects the entire post-keycard route. Field-621 e24 and e26 are
  the public threshold; field-565 e12 is the keycard service passage; field-589
  retains the five-tone clue and adds a persistent resonance receipt; and e10
  admits the party to field 620. Solving Quarantine releases lobby e22 and
  contributes its clearance to the production bulkhead. The ordered route
  `624 -> 626 -> 625 -> 622` adds explicit sorter and core completion receipts,
  a fuller Fei/Elly/Citan response to Meld, and a recoverable Sufal
  pending/epilogue/secured sequence. Securing the node opens the explorable
  emergency return; it does not force an external field, world-map, or title
  handoff.
- Version 198 uses the current Slot-1 runtime evidence to correct all nine
  field-621 waiting-room patients. In the captured V197 state, e9, e12, and e15
  had converged within five units of one another at the real east edge near
  `(1190,1592)`, while e8 pressed immediately beside them; west-side patients
  showed the same wall-seeking behavior. Their one shared OP17 rectangle had
  extended to X500/X1250 even though the main room ends near X541/X1190.
  Each actor now keeps native `59 00` random walking inside a distinct
  clockwise microzone. Every zone has a fully on-mesh 24-unit halo, every pair
  remains at least 50 units apart, and the layout leaves both the central player
  aisle and physician route clear. All dialogue and interaction actions remain
  unchanged, including `I like turtles!`.
- Version 199 uses the newest Slot-1 runtime evidence (field 621, physician e35
  at `(1200,1400)`) to correct a leaked doorway-transit flag. His valid radius-16
  body was present, but `20 01 80` left collision flag `0x80` set after arrival,
  so Fei could occupy the same point. Both physician actors now remain ghosted
  only while hidden or following scripted doorway routes. Their visible waiting
  states use `20 0C 80`, restoring the ordinary solid/immovable NPC class, and a
  32-unit rectangular body that preserves a forgiving, no-facing X target
  without creating an oversized invisible wall. Called-phase lobby reloads and
  every unresolved office phase reconstruct the solid state; both return walks
  restore the ghost state before player control resumes, preserving the earlier
  no-stall door behavior.
- Version 200 uses the newest Slot-1 office capture to identify the remaining
  doorway defect precisely. Field 550's exterior triangles 34/35 use material 0,
  whose runtime flags are `0x00800000`; ordinary layer-0 NPC movement rejects
  that strip even though triangle 34 shares a real edge with interior triangle
  3. Security therefore exhausted its 16-update `OP4B` walks outside before the
  old endpoint correction snapped each actor to formation. The doctor exhausted
  three 180-update threshold walks before the same correction placed and hid him
  outside. V200 leaves the global walkmesh and Fei's solid e19 seal untouched.
  Instead, each crossing actor receives native scoped `F8 02 38 00` permission.
  Security keeps it from the hidden exterior reveal through deep interior
  `(0,200)`, clears it with `F8 06 38 00`, and then fans out normally. The doctor
  receives it only after the blocking leaf-open helper, crosses with three
  proven 16-update bounds, remains visible while the blocking reverse-close runs,
  hides behind the closed leaf, and only then clears the override. Every route
  leg has at least eight settling updates beyond its eight-unit movement budget,
  so the deterministic endpoint correction is limited to the normal nine-unit
  arrival tolerance rather than a visible cross-room teleport.
- Version 201 recovers the preserved Disc 1 field-567 Clinical Stabilization
  Ward into logical field 590, whose Disc 2 canonical targets are the checked
  dummy pair 1786/1787. It does not overwrite logical field 567's empty Ethos
  examination annex. Field-565 p1 now pairs with field-590 p0 through
  `service_stabilization_production`; the formerly STOP-only field-565 p2 staff
  threshold pairs with field-590 p1 through `service_stabilization_staff`; and
  the ward's third native paired door at p2 owns `production_clearance` through
  `stabilization_sorting` to field-624 p0. All three ward entries are walkmesh
  audited, all six native paired-leaf helpers remain, the retail surgery event
  remains neutralized, and the existing ordered cut-Surface chain continues as
  `624 -> 626 -> 625 -> 622`. Field-565 e4-e10 now use `0x18` rectangular
  ghost action targets around unchanged narrow physical seals. All seven
  reciprocal arrivals move farther into their original audited triangles so a
  held X press cannot bounce the party back. Field 590 applies the same design
  with `0x24` action targets and bounce-safe p0/p1/p2 arrivals.
- Version 202 restores the current Slot-1-marked field-565 entity-12 controller
  to its complete retail action at PC `0x03AC`. The native directional password
  is `Up, Down, Up, Left, Right`; only either native success exit sets
  `tone_authorized` (`0x021E` bit 9) and releases both leaf-helper entity 21 and
  physical-seal entity 30. Field-589 entity 9 remains the audiovisual clue: it
  plays the same five tones, records only clue-seen bit 8, and reminds the player
  to repeat them at the service input panel. It never authorizes the passage.
  Beyond that passage, field-588 entity 9 requires tone authorization, retains
  its bio-interface cutoff work, and adds a one-time item sound `0x37` plus
  `QUARANTINE KEYCARD ACQUIRED` receipt before setting the distinct credential at
  `0x021A` bit 8. Field-565 entity 10 now gates `565/p6 -> 620/p1` on this new
  credential, while the Intake-to-Service door and independent Intake-to-key-room
  door continue to use the original clinic security keycard at `0x021A` bit 0.
  The two field-588 commits are
  independent so an interrupted save can resume only the missing award.
- Version 206 corrects V205's visually irrelevant natural field-588 donor. The
  natural donor is a Dark Armor treasure room, and V205's custom credential
  interaction had no backing terminal model, leaving a model-less hotspot.
  V206 installs exact Disc 1 field-573 canonicals 1757/1758 instead: the compact
  blue Solaris computer-room shell, its baked center workstation on static
  nodes 11 and 15, and its native animated door. Entity 7 owns the workstation
  X interaction; unrelated donor entities 6, 8, 9, and 10, including the old
  story/loot behavior, are retired. The door returns to `621/p5`, and the
  workstation still requires the five-tone authorization before its one-time
  Quarantine-key item sound, receipt, and persistent award.
- Version 208 supersedes the independent Intake credential-lab route. It adds
  bright examination rooms 591, 592, and 593 behind three existing Solaris
  panels on Intake's eastern outer wall. Each exact field-352 clinic clone keeps
  its bed, illuminated workstation, native animated exit, and disabled random
  encounters. Field 593's terminal is the only Quarantine-keycard writer.
  Intake e26 again enters Service at `565/p3`; Service e7 returns to `621/p5`,
  e9 enters field 588, and field 588 returns to `565/p5` while awarding only the
  bio-interface cutoff. The diagonal first panel is half-turned and re-anchored
  so its rendered face points toward the user's saved hallway stance.
- Version 209 aligns the first examination panel with the rendered diagonal
  wall plane and moves the other two from the inset walkmesh edge to the true
  east wall at `x=1821`. Doors B and C occupy the native `z=840` and `z=396`
  bays, preventing protrusion and increasing their center spacing to 444 units.
  The field-549 repeat menu drops its unrelated retail binary-code handoff while
  retaining the six-panel presentation. The Quarantine keycard at `0x021A` bit
  8 now directly gates both Intake e22 and Service e10; `quarantine_complete`
  remains a later production-clearance condition rather than an entrance key.
- Version 227 reroutes Security-keycard-gated Intake e26 from the superseded
  `565/p3` freight handoff to the independent `594/p0` Treatment Preparation
  Room. Logical field 594 uses verified Disc 1 field-352 source canonicals
  1315/1316 in checked Disc 2 dummy targets 1794/1795. It retains the bright
  clinic shell, examination bed, illuminated workstation, disabled encounters,
  and native e17/e18 animated exit returning to `621/p5`. Its entity-19 terminal
  repeatably reports metabolic conditioning, nutrient balance, and injection
  readiness without writing a credential or progression flag. Field-565 e7/p3
  is sealed and dormant for a future laboratory handoff and is not an active
  transition endpoint.
- Version 226 removes the automatic field-352 forward poll from logical fields
  550, 567, 591, 592, and 593. Entity 0 script 1 returns to the shared STOP and
  the verified 87-byte retired cavity has no active entry point. Forward alone
  cannot open a leaf or call the doctor-office denial; a fresh X press remains
  the sole trigger for the unchanged e17:s2 action. The V225 rectangular seal
  remains at `(0,266)` with script half-extents `(24,8)` and physical contact
  planes `z=250/282`, and all five 1,948-byte retail walkmeshes remain
  byte-identical.
- Version 225 extends the thin field-352 examination-door seal and e17:s2
  forward poll to fields 550 and 567, and corrects the shared trigger in all
  five rooms from unreachable integer `z=230` to `z=228`. The exact reported
  field-550 state has Fei at `(43.353989,228.710999)`, yaw `0x0800` on triangle
  15, only 5.289 units from the unconnected `z=234` walkmesh edge. A 63-byte
  in-place worker in the verified 87-byte retired cavity calls the unchanged
  e17:s2 action, then waits for Fei to back below `z=228` before rearming. This
  lets the resolved office exit open naturally without turning a pre-procedure
  denial into a repeating dialogue loop. All five 1,948-byte retail walkmeshes
  remain byte-identical with SHA-256
  `abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df`.
- Version 224 eliminates the persistent bottom-left wedge by correcting its
  proven ordering-table cause. In closed-door V223 state
  `b962464676e5c2b9a59918a5b9247d5d747276ab6ec0fc4a36c1f5f48ae96d24`,
  Door B lower apron half q0 at `0x13B4B4` is linked after leaf `0x1227CC`,
  while q1 is five OT buckets above at `0xB2A08`; Door C repeats the split with
  q0 `0x13B768` after leaf `0x122A58` and q1 five buckets above at `0xB2AD4`.
  Aligned V222/V223 crops preserve the same triangular silhouette, proving the
  V223 UV clamp changed its color but not the later-sorted overdraw. V224
  replaces the two lateral FT4 halves with the native-style one whole-width FT4
  packet `00 00 00 2D 97 89 97 8D B6 89 B6 8D` and fourteen degenerate F3
  records. Model 20 remains 396 bytes with counts `15/15/2`, offsets
  `0x48/0x48/0xC0/0x140`, GPU arena `0x140`, unchanged bounds, vertices, UV
  clamp, and placements, and SHA-256
  `8ef50d3f377c7b8caf2fdcfa0fcaecebe3d25ce5a51a90dfa0f14a734fdf3b52`.
  The 39,292-byte model archive, 135,648-byte field-621 bundle, unchanged
  10,895-byte script, and 1,408-byte header have SHA-256
  `b06e38c58fcd5e1ce5033e1135f0ae7c7d745b9ef37575f44b0cba4c936c52aa`,
  `011be9593a2c565e6c3bb5f325ef64ac47811592794945ce529fcb3b6eb36677`,
  `a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c25fca52f202845ea7`,
  and `bd8be9feef57bff074c81c885d66b329ed20456e42d3a11c6b8e03b18550598f`
  respectively. The focused release suite passes all 62 tests, and the
  complete repository suite passes all 567 discovered tests with no failures,
  errors, or skips.
- Version 223 clamps the near-black texture tail on all three added Intake
  doors without changing V222's geometry or placements. In model 20's two FT4
  display packets, exactly four duplicated far-depth V endpoints change from
  `0x95` to cyan-shadow row `0x8D`: the packets are now
  `97 89 97 8D A6 89 A6 8D` and `A6 89 A6 8D B6 89 B6 8D`. This excludes
  the source atlas's near-black `0x8E..0x95` tail while preserving the complete
  89-by-44 apron, its winding, U span, texture page, CLUT, allocation, leaf
  origins, and static-node transforms. Model 20, the 39,292-byte model archive,
  135,652-byte field-621 bundle, unchanged 10,895-byte script, and 1,408-byte
  header have SHA-256
  `524f3d90eb72bb674cba3428a7d55b40f580e4064aaf3270b54d8f331320c98a`,
  `abd08ad9f355179df8281ecd7c297c4e34b45982aa3bcf39f604374c116688d4`,
  `d96a1dad2085ab1b0099c62ab7180ece7e52c93862faaa199b6ae7f3119a4c3f`,
  `a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c25fca52f202845ea7`,
  and `bc016d4404b7cd5f31a4eb7aac91315b594152ca17ea640104bc6f8fdc4790df`
  respectively.
- Version 222 removes V221's wall-side black border at the three added Intake
  doors. It restores V209's leaf origins: Door A moves from `(3086,1461)` to
  `(3088,1463)`, while Doors B/C move from `x=1731` to `x=1733`, making every
  closed leaf coplanar with its carved aperture. Static nodes 60--62 reverse to
  `[512,1645,0,1307]`, `[1024,1821,0,882]`, and
  `[1024,1821,0,441]`, so model 20 begins at the leaf plane and extends only
  onto the far side. Its local negative-Z hall side remains empty, and each
  apron shares only one boundary edge with model 1's retained hall floor. The
  model archive and model-20 identity remain unchanged. The resulting
  field-621 bundle, script, and header have SHA-256
  `acf5c09f99d67ee157c4049c31fe1f48026819e6a39e041284bd1912e6e4a039`,
  `a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c25fca52f202845ea7`,
  and `a673a4079dddfd4d908f63f8fedee227e9c23f033c6652b8aace86de08900887`.
- Version 221 adds the same short hall-side threshold apron visible at retail
  field-621 entity 24 to Doors A, B, and C. The source is model-19 `POLY_FT4`
  ordinal 4, not entity 24's model-4 leaf: its four source vertices define an
  exact 89-by-44 top-facing floor. Model 20 remains exactly 396 bytes at nodes
  60--62 and their existing placements, but now contains two texture-continuous
  FT4 halves plus twelve degenerate F3 records. It has counts `15/14/2`, offsets
  `0x48/0x48/0xC0/0x138`, GPU arena `0x140`, local bounds
  `x=0..89,y=0,z=0..44`, and SHA-256
  `0ce78d9edc020706c22ac4b4027149c53ac28be99ef4b71bedb80a25bbf7744f`.
  It has no local negative-Z or vertical geometry. V220's model-2 camera cleanup
  remains byte-identical. The resulting model archive and field-621 bundle have
  SHA-256 `9fec53653008970b00bc06b4e151f5c093c08e9e49d2620600600f75042e2d7a`
  and `693c507955696d8a3c75b07acb1be7ad13c50ed4791b95a48b558661c279aae4`.
- Historical Version 220 superseded the finite black reveal geometry. Model 20 keeps its
  396-byte allocation, static nodes 60--62, placements, counts, offsets, and
  pointers, but all 16 `POLY_F3` index records are degenerate; its SHA-256 is
  `501971ffbbfa09a28c8f3be10f546630cb9ab6cf52b31c3b28882679388cbb39`.
  Native 4,836-byte model 2 changes from SHA-256
  `b093460d49974a083f191442a2aaafb75983da7ed5ad78201b3d46f5b4b2bdd3`
  to `2d0b40fb67720162fe93bb3fa522d33c3cf3db8333865f3f8d7c897688fad5d3`:
  group 0's four flat-black `POLY_F3` corner caps and group 2's 134 flat-black
  `POLY_F4` ceiling/fascia records are degenerate, while textured groups 1 and 3
  and all model-layout invariants remain. The carved openings now expose the
  native field clear only while their leaves are open. No ATEL/script,
  interaction, entity placement, walkmesh/collision, or camera data changes.
- Historical Version 219 replaced V218's double-sided tiled plate with a
  hallway-facing one-sided `POLY_F3` plate at local `z=-32`. Same-delay runtime
  A/B testing later showed that disabling this plate removed the small black
  triangular tears at Door A but not the large diagonal band, identifying a
  second independent occluder in native model 2.
- Historical Version 218 replaced field 621's visible dark doorway outline with
  a shared 396-byte tiled, double-sided opaque-black rear-plate model at local
  `z=-32`. It removed the thin varying-depth jamb, lintel, and sill border and
  was superseded first by V219's one-sided plate and then by V220's inert model.
- Version 217 corrects field 593's player-side exam-room doctor-office doorway.
  Its collision seal is now a thin rectangle aligned to the physical aperture,
  and a narrow forward-movement poll invokes the unchanged native animated-door
  action. A fresh X press remains valid, and the retail field-352 walkmesh is
  byte-identical.
- Version 216 replaces field 593's post-keycard already-removed response with a
  repeatable medical-diagnostics panel for Fei: pulse 64, blood pressure
  118/72, temperature 36.8 C, respiration 14, and elevated neural activity.
  The one-time Accept branch, item sound, acquisition receipt, and credential
  write remain unchanged and cannot repeat through the diagnostic path.
- Version 215 replaces the three field-621 examination doors' independent black
  backing plates with true openings carved into the Intake wall geometry. Each
  opening uses plate-free, recessed black jamb, lintel, and sill returns, so no
  separately sorted triangle can diagonally cover a door at an oblique camera
  angle. Field 593's Quarantine-keycard text is rebuilt on safe font-grid
  boundaries and now presents explicit `Accept it` / `Leave it` choices. Leave
  is repeatable, silent, and state-neutral; Accept alone plays the item sound,
  shows the acquisition receipt, and writes the credential.
- Version 214 expands field 550's patient-record interaction across the entire
  reachable side-computer frontage with three facing-gated invisible carriers.
  It excludes the saved bed-facing heading and preserves the record as a
  read-only view of the chosen alias, live weight, vitals, and compatibility.
- Version 213 activates field 550's static node-29/model-5 workstation through
  retired entity 4. Its hidden, ghosted target is centered on the saved
  `(70,-143)` operator stance with a compact depth that ends one world unit
  before the physician's X volume. The action branches directly on the three
  persistent alias codes, reads Fei's live weight once with `FE 69`, and shows
  alias-specific vitals plus `100% / PERFECT FIT`. Dormant dialogue IDs 2, 10,
  33, and 45 carry the records; dormant ID 50 absorbs unreachable padding so
  the script and dialogue remain exactly 5,414 and 6,056 bytes for safe resident
  migration.
- Version 212 isolates the field-550 exit gate's scheduler-spanning snapshot in
  `0x07D0`. The doctor/security state machine remains on `0x07C6`; all thirteen
  gate operand references change without moving any script pointer or changing
  ATEL size. A regression reproduces the exact eight-opcode yield, doctor write,
  and gate resume from the user's `0x03FA=0x00E0` / `0x03EE=0x4002` state. It
  must show dialogue 54 with no field change, while `RESOLVED / COMPLETE` still
  reaches the intended post-victory exit and seal release.
- Version 211 decodes Slot 1 SHA-256
  `9b5839c678df0b81b1bb8148af41486df968b76ed12843b7d8eb3298b1942cf3`
  as resident field 620 with Fei at `(332.129791,-1.275818)`, triangle 182,
  facing east controller e24 at `(352,0)`. That action now displays the exact
  two-line current-content notice without sound, helper calls, leaf animation,
  field transition, or state writes. Separate release loops drain both the
  opening press and the press that closes the window. The dormant native gate
  stays byte-preserved, while west e23 remains the usable return to Intake.
- Version 210 gives all three added Intake examination doors the same dark
  opened-door presentation as the native facility thresholds. Field 621
  appends one 132-byte, texture-free opaque-black model and instances it as
  collisionless static header nodes 60--62. Each leaf remains visually flush:
  the leaf sits two world units inside its continuous white wall, with its
  fixed black recess on the intervening one-unit depth plane. Opening the leaf
  now reveals black instead of the wall, while the interaction volumes,
  walkmesh barrier, slide vectors, destinations, and reciprocal entries remain
  unchanged.
- Version 207 replaces V206's compact blue field-573 room with the exact bright
  Disc 1 field-550 diagnostic-scanner donor. Source canonicals 1711/1712 fill
  logical field-588 targets 1782/1783. The baked clinical shell and obvious
  scanner remain visible; e4 carries the credential interaction, and native
  e17/e18 provide the reciprocal animated return to `621/p5`. Field-621 e26 now
  requires both the Security keycard and five-tone authorization. Because that
  compound gate authenticates the party before entry, e4 does not repeat the
  tone test; it save-safely arms the bio-interface cutoff and awards the
  Quarantine keycard.
- Retail graphics, models, and walkmeshes remain byte-identical within each
  retained source unless explicitly described. Field 550 uses field 352's
  infirmary bundle/graphics pair, replaces its unused actor/sprite banks 1 and 2
  with exact Security Cube and Solaris Guard banks, and zeros all 16 encounter
  weights. V195 field 567 independently reuses field 352's exact static room,
  bed, models, and graphics while making its retail characters and events
  unreachable. Fields 591--594 fill the retired local clinic actor/sprite bank
  with four exact, distinct demihuman patient donors while preserving the
  physician bank. Field 590 reuses the preserved field-567 Krelian Lab ward
  graphics unchanged. Field 621's bank-6 physician replacement, V215's carved
  apertures, V224's one-FT4 UV-clamped native-style model-20 threshold apron,
  and V220's retained disabled model-2 groups 0 and 2 are the other explicit
  asset exceptions. The superseded border and rear plates are absent; textured
  model-2 groups and unrelated model entries remain byte-identical.
- V233 activates only field 567's visible model-3 side workstation through
  retired entities 4--6. Its narrow, facing-gated readout reports that no patient
  is loaded; it adds no model, collision actor, NPC, combat, gate, item, or
  progression write.
- Random encounters remain disabled. Field 550 replaces only disabled
  configuration 15 with field 551's checked two-Cube/two-Guard formation and
  sets its no-Escape flag. It keeps normalized Disc 2 resource set `0x21` but
  selects bright technological arena `0x30`; field 551's retail configuration
  15 independently proves that exact resource-set, no-Escape, arena, and
  Security Cube combination. Canonicals 2871/2872 are verified by size and
  SHA-256 and reused without transplant. Field 622 still invokes its retained
  Sufal battle configuration. V195 field 567 instead keeps all field-352 battle
  formations unreachable and zeros every encounter weight. Field 590 likewise
  keeps the retired surgery event unreachable and random encounters disabled.
- Fields 567, 588, and 590 use unused Disc 2 field pairs. V195 field 567 retains the
  exact static field-352 bed/environment and only its e17 return to field 621;
  V233 additionally gives its existing model-3 workstation a repeatable,
  read-only no-patient record action without changing that route;
  logical field 588 now uses exact Disc 1 field-550 source canonicals 1711/1712
  in targets 1782/1783, keeps the bright clinical room's native animated door,
  and returns independently to field 621/p5; field
  590 uses dummy target IDs 1786/1787 for the recovered three-door ward.
- The Surface title bootstrap clears only Surface-owned state and installs Fei,
  Elly, and Citan. Canonical 2595 also grants every native on-foot deathblow to
  every character and form record. The grant leaves character levels and stats
  byte-identical; canonical 2607's checked Perfect Works tables already use
  level-1 learning gates. Chu-Chu and Maria correctly retain empty native
  deathblow sets.

## Build

V233 is the current source release. Its reproduction command is:

```powershell
python tools/build_surface_soylent_campaign.py `
  --source-disc output/Xenogears_PW_CD2_mass_driver_standalone_v163.bin `
  --donor-disc C:/path/to/Xenogears_PW_CD1.bin `
  --output work/surface_soylent_campaign_v233_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --disc-output output/Xenogears_PW_CD2_mass_driver_surface_soylent_v233.bin
```

The current playable image is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v233.cue`, launched by
`output/PLAY_SURFACE_SOYLENT_V233.cmd`. Its 698,816,832-byte BIN has SHA-256
`f50fa064e8d466bde46e0946a4c1ea7dc556a6a94d85f4632de201934318a72b`;
its 112-byte CUE has SHA-256
`106149772cdd6b12a460be98858e59d268fb1e01008d12b81f3eda80dd04ca28`.
The 1,244-byte launcher has SHA-256
`83d3a23fa26c757f92437f773b3fbac6f5a5a482427ac414a92de2b281b11016`.
The 136,361-byte primary manifest at
`work/surface_soylent_campaign_v233_stage/manifest.json` and repeat-stage
manifest at `work/v233r_stage/manifest.json` both have SHA-256
`b79d7a866ba29ad9a5f488bf6e004310f5a5a2c32ed73aaf676eee3154ac4d1a`.
The isolated primary and repeat V233 BINs and manifests match byte-for-byte.

The guarded V232-to-V233 Slot 1 migration uses the 75,617-byte helper
`tools/migrate_surface_soylent_v232_slot1_to_v233.py`, SHA-256
`3c7fe81b7657213c97090b8ba0a96d7551ea2a22dbb66cbc7fc5a65b484ea13f`.
It accepts only the preserved 1,607,991-byte field-567 state at
`work/save_backups/SLUS-00669_1_v232_field567_empty_terminal_3f09a8ce.sav`,
SHA-256
`3f09a8cea70ce09c87b2bc0892ad8e427cc90d7fcf1759b8677413927c20b022`,
and emits
`work/save_candidates/SLUS-00669_1_v233_from_3f09a8ce_field567_empty_terminal_native_init.sav`
(1,457,268 bytes; SHA-256
`b9b41cbc756300f6567a7c1cdc6b304e44bc57e025f1a4a51ff74aae84742acf`).
Its matching 6,393-byte JSON report has SHA-256
`c870d9f441933eb0170fb0ce5accf0ca78013acef1cab66095870533da22575a`.

The migration changes exactly 456 decompressed payload bytes: one resident
archive-table byte, 127 fixed-size ATEL bytes, 307 bytes in unreachable retail
dialogue ID 45, and 21 scheduler bytes across retired entities 4, 5, and 6.
The exact native V233 initializer bodies occupy `0x044E..0x04A4`; their
read-only action occupies proven-dead former e16:s4 span `0x05BD..0x05E3` and
overwrites the old raw ID45 reference. All 180 runtime current/slot PCs and the
complete live control-flow graph are checked before either span is replaced.
It preserves the resident header and heap layout, Fei's exact saved
position and facing, party, GameState, field variables, camera, dialogue
windows, every unrelated actor byte, and all offline sprite bytes. Native MIPS
and heap-header checks prove serial sprite recreation reuses the same pointers
without advancing an unrelated callback. The compatibility action calls the
relocated no-patient record from the already-loaded V232-sized field; a cold
field reload uses ordinary V233 dialogue ID 53. Install the candidate only
while DuckStation is fully closed and retain the preserved source as backup.

The guarded historical V231 state migration uses the 51,172-byte helper
`tools/migrate_surface_soylent_v230_slot1_to_v231.py`, SHA-256
`af84b5f52105315f7f27cd6d41350cd9b39ae023cc3deaf4a27e157c9ed4c295`.
It accepts only the exact field-592 terminal capture at
`work/save_candidates/SLUS-00669_1_v230_patient_terminal_1eb8b434.sav`
(1,845,278 bytes; SHA-256
`1eb8b43472bece86bb46a0e50120d3ea31baa5c19b11418eb2818ce00245e2f3`)
and emits
`work/save_candidates/SLUS-00669_1_v231_from_1eb8b434_field592_patient_record.sav`
(1,670,155 bytes; SHA-256
`b8fd8b566aed92e68133739ea2eb1911a7f6742c923e467e63cde2c6986a214f`).
The matching 2,504-byte JSON report has SHA-256
`27b1faffa7c5b7151ab07eb667a165397ed9b70929a372909c025fe0f2fa6252`.

The migration changes exactly 2,505 decompressed payload bytes: 2,201 in the
resident archive table, one terminal-dialogue operand, 299 bytes in a retired
dialogue cavity and its width field, and four bytes across the active window's
two source pointers. The new 203-byte record cannot fit field 592's old
110-byte ID53 allocation, so the resident-only migration uses unreachable
retail ID45's verified 307-byte cavity, pads its remaining 104 bytes with Close,
and remaps only terminal e19 from ID53 to ID45. The already-open window's source
pointers target the relocated record and its authored Close byte, but its
captured glyph primitives remain visibly old until one X closes it; the next
terminal interaction freshly renders the new record. Component sizes, both heap
gaps, walkmesh, Fei, party, GameState, field variables, camera, every actor, the
terminal VM PC, and the remainder of all dialogue windows stay exact. A cold
room reload discards that compatibility layout and uses ordinary V231 ID53.

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
`73812b56b1cb84b57cd8a8b1f9ecd5f67c1b983c475777dabee9d3f042c1083d`.
The 1,318-byte `output/PLAY_SURFACE_SOYLENT_V229.cmd` launcher has SHA-256
`c1c3a5343b4934aee225374223ec4db0ff73f2a26071c24289443aacda147bdf`.
The 129,207-byte primary manifest at
`work/surface_soylent_campaign_v229_stage/manifest.json` and repeat manifest at
`work/v229r_stage/manifest.json` both have SHA-256
`2dfba5b96913771b7cf97827d11d08c67336db190c9ebf208609dccf2d7749bf`.
The isolated primary and repeat V229 BINs and manifests match byte-for-byte.

The guarded historical V229 state migration uses the 46,948-byte helper
`tools/migrate_surface_soylent_v228_slot1_to_v229.py`, SHA-256
`c83112decd4d25013156ffe45a73ce42233a479aa4d41a0910a01039794861a9`.
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
The 3,819,109-byte decompressed payload has SHA-256
`6c05487dfbf434f01ecf2c7a11fa6a9784c4d74df0be6e1947365788e06c698e`;
its 1,438,158-byte compressed form has SHA-256
`0f3a002be787eafc2595fd5599cac9a0e7ccf1cd75c709c0d6b7d3ed16ca051f`.
Exactly two decompressed payload bytes change: resident field-549 ATEL offset
`0x10C74D` changes `0x0E -> 0x08`, and runtime e16 ActorData radius offset
`0x11217C` changes `0x1C -> 0x10` (little-endian word `0x001C -> 0x0010`).
The V228 and V229 media archive tables are identical; the helper nevertheless
rebuilds and validates the resident table against V229 while preserving its
volatile `0xE0` tail byte, so zero table bytes change. Fei, party, GameState,
field variables and backup, camera, dialogue windows, actor records, and all
unrelated ActorData remain byte-identical. The compressed payload round trip is
verified, and the candidate is always written separately from live Slot 1.

V228 remains available as the historical private-clinic population release.
Its 698,814,480-byte BIN has SHA-256
`7bdb5fd17970abb15fc36f32a0907aafd132f80eae818e79ba21473380621deb`;
its 112-byte CUE has SHA-256
`0c3e3672f69969a0e1ced0e04d8dfc2f2298e706acf42b1c58292b4689c714fb`;
and its 1,306-byte launcher has SHA-256
`471ec8019acb6057b152bad979ce5cbcdcf1e9b6a09516c6d989e12eb706f43d`.
The 128,038-byte primary and repeat manifests have SHA-256
`39e5b82647ecece73fb61784eae7b3cdcf490e411887765b72a58ea8ed592244`.

The guarded historical V228 state migration uses
`tools/migrate_surface_soylent_v227_slot1_to_v228.py` and accepts only the exact
1,735,278-byte V227 state at
`work/save_candidates/SLUS-00669_1_v227_from_9436ef84_treatment_preparation.sav`,
SHA-256
`23221b3468b77096fb9a8e07a11a32203fbd51e4c92d0b7fd203b036e30c1950`.
It emits
`work/save_candidates/SLUS-00669_1_v228_from_23221b34_clinic_aid.sav`
(1,735,287 bytes; SHA-256
`a991c4f8779bf0ce877fd6ef90806c757e08cde97abc2b2d05c692972164df64`)
and the 1,804-byte matching JSON report with SHA-256
`05d28f4752bc365e54539dc50a9a762f01a724d5787ae8910f8a5c172fc5c8b0`.
Exactly 2,464 decompressed payload bytes change, all within the serialized Disc
2 archive table for field resources 1788, 1790, 1792, and 1794. The resident
field-621 script, hybrid header, actors, runtime PCs, route, GameState, party,
camera, windows, dialogue, and walkmesh remain byte-identical. The helper
updates the equal-length embedded CUE name, verifies the compressed round trip,
and never writes DuckStation's live Slot 1.

V227 remains available as the historical Treatment Preparation release. Its
698,885,040-byte BIN has SHA-256
`108c753b964831ae6be61ca05fb8cbcd47240d27c0d4f376135828b4945596ed`;
its 112-byte CUE has SHA-256
`df061663cd9053e195513221997f4042d37c8d23fba9268e9d10bdafa577c134`.
The 122,987-byte primary and repeat manifests have SHA-256
`3a56b3ac97ce837c9356207df6a14d488a26cc0a63524472ba903bbae557fb67`.

The guarded historical V227 state migration uses
`tools/migrate_surface_soylent_v226_slot1_to_v227.py` and accepts only the exact
1,910,685-byte V226 backup at
`work/save_backups/SLUS-00669_1_v226_intake_door_room_change_9436ef84.sav`,
SHA-256
`9436ef847164e1c850828da3c6f90a28ba1ea931763a3b691c6117e376333c82`.
It emits the 1,735,278-byte candidate
`work/save_candidates/SLUS-00669_1_v227_from_9436ef84_treatment_preparation.sav`,
SHA-256
`23221b3468b77096fb9a8e07a11a32203fbd51e4c92d0b7fd203b036e30c1950`,
and the 1,809-byte report
`work/save_candidates/SLUS-00669_1_v227_from_9436ef84_treatment_preparation.json`,
SHA-256
`ee5e4952da80a7eef27af2e39f88b824675c80a5ff1571b9816d7f44fcf003e4`.
Exactly 3,033 decompressed payload bytes change: 3,031 archive-table bytes and
the two resident route operands that change `field 565/p3` to `field 594/p0`.
ActorData and runtime-PC bytes do not change. Fei, the party, GameState, field
variables, camera, windows, loaded header, dialogue, walkmesh, and neighboring
components remain byte-identical; the helper never overwrites DuckStation's
live Slot 1.

The historical guarded V226 migration accepts only the exact 1,855,939-byte
V225 Slot 1
captured while field 592's retired automatic poll was active at PC `0x048A`,
SHA-256
`408a5dc96f5a2633079f8a41b09eefe669400b71a455bd5312fa9e0fc6cb22b9`.
Its preserved source is
`work/save_backups/SLUS-00669_1_v225_auto_open_408a5dc9.sav`. The exact
candidate is
`work/save_candidates/SLUS-00669_1_v226_from_408a5dc9_field592_x_only.sav`
(1,680,239 bytes; SHA-256
`a3aa3752e1b4b035b1f05f7cc0495bc4d4acd61f988923401e3ee8e30876e7bb`).
The 1,629-byte report at the matching `.json` path has SHA-256
`bde8fc1e9c71a7036372ee26223914d549b4c0ffc811501b7849d279b5552b45`.

Exactly 70 decompressed payload bytes change: four V225-to-V226 archive-table
bytes, 62 bytes in the equal-size resident field-592 ATEL, and the two-byte PC
in each of entity 0's active-slot and current-PC records. Entity 0 script 1 now
points to shared STOP `0x068C`, the complete retired `0x044E..0x04A5` cavity
is restored, and native e17:s2 at `0x0735` remains the only door action. The
3,819,109-byte payload has SHA-256
`3a256a7d4632d79fedd13488d1e7b95fecb038490f1cd1496e7db4abe25602cb`;
finished RAM has SHA-256
`4a52a6df97f29cb9eb7a4aadbb48c86962bb08d0600853b9f81186f2fbf903bf`.
The resident archive table has SHA-256
`3ee67d330d7a2c4b2bbdd8188dfa38a4a0152bea3950be3276d40a6ce8862a47`.
The 1,635,031-byte compressed frame has SHA-256
`d8e3cadf0ac9bbb80026c306c41212b8151147b4773127862ed5e8769000ef6f`.
The loaded header, walkmesh, all non-controller actors, Fei's stance, party,
GameState, field variables, closed leaf, e17 carrier, e20 rectangle, camera,
and windows remain byte-identical. The exact compressed round trip is verified.
For that V226 migration, every other state must cold-load an affected field
from V226 media.

Historical V225 remains the automatic field-352 doorway-correction release. Its
image is `output/Xenogears_PW_CD2_mass_driver_surface_soylent_v225.cue`, its
launcher is `output/PLAY_SURFACE_SOYLENT_V225.cmd`, and its 698,642,784-byte BIN
is `output/Xenogears_PW_CD2_mass_driver_surface_soylent_v225.bin` with SHA-256
`539e2e33266d71337666c84d9d3a153dfd7555d8db933efadc49376483e6e1ff`;
its 112-byte CUE has SHA-256
`6a289550cec7003e9742d75f862db41d37214afe499d0dcddab1892839f6b8fd`.
Its 119,944-byte repeat manifest at `work/v225r_stage/manifest.json` has
SHA-256
`2f6d433e9c257455e70fbc028a07335ec5b84790c646d7ff397f544a8ca1bb99`,
and its isolated primary and repeat builds match byte-for-byte.

Its guarded migration accepts only the exact 1,851,504-byte V224 Slot 1
captured at the field-550 blocked doorway, SHA-256
`6df7129d144f7b9efe785f24749ca68512f10dda04ca8d4022cadf757c9b5dae`.
Its preserved source is
`work/save_backups/SLUS-00669_1_v224_field550_door_clip_6df7129d.sav`.
The exact candidate is
`work/save_candidates/SLUS-00669_1_v225_from_6df7129d_field550_clearance.sav`
(1,672,710 bytes; SHA-256
`b8638edcf76e2c19a829711b57cc7c0beded7a89c60871e2cc8aaac60616f9eb`).
The 1,810-byte report at the matching `.json` path has SHA-256
`4d5c253f890f2840d2ad343c8740ab86362f9999c82998ac4836d310df142bcb`.

Exactly 87 decompressed payload bytes change: five V224-to-V225 archive-table
entries plus field 621's nonvolatile FAT-size catch-up, 68 bytes in the
equal-size resident field-550 ATEL, two bytes in the loaded e19 header record,
and eleven bytes that convert live e19 from its circle at `z=250` to the
rectangle at `z=266`. The 3,819,109-byte payload has
SHA-256
`f27cebfc3eb00498cbb76d339d78ee98779c2b2c8868559254f474969f0243ed`;
finished RAM has SHA-256
`60d52d04106554e57b1f444a53f3a6e5a77fbc88a5092429f5c441c4edaea2e1`.
The 1,628,725-byte compressed frame has SHA-256
`a1d542be06f0b474b5c2c4d9703b92aec62b7cbed79221d990e3522f36a1c9fd`.
The migration normalizes field 621's nonvolatile resident FAT byte at
`0x3268` from `E8` to V225's `E0` and preserves only the volatile
`0x7FFF=E0` tail; its resulting table has
SHA-256
`337607d4873dcc0f5c2eee5cd69f7d61f130badb074b3441e09a60cd0e801eb9`.
Fei’s fixed-point stance, triangle, yaw, party, GameState, field variables,
doctor/security runtime, closed leaf, camera, dialogue windows, dialogue,
walkmesh, and native X action remain unchanged. The exact compressed round
trip and five migration tests pass. Every other state must cold-load an
affected field from V225 media.

Historical V224 remains the whole-width Intake-threshold rendering release.
Its 698,642,784-byte BIN has SHA-256
`6d0854e878f677eee7e8c57fd5084d0f28b9cc776b758934925ef353da30022d`;
its 112-byte CUE has SHA-256
`4cd7c8be1096148c00d619f776754e6e15cf55dffcc9a3cc97b8887af333944d`.
The 119,788-byte repeat manifest has SHA-256
`9296f347064f271df10370feb5c433baa49093b717c58fa374a0bca1cb2fae91`.

Its guarded V224 migration accepts only the 1,672,493-byte V223 Slot 1 used for
the closed-door OT proof, SHA-256
`b962464676e5c2b9a59918a5b9247d5d747276ab6ec0fc4a36c1f5f48ae96d24`.
Its preserved source is
`work/save_backups/SLUS-00669_1_v223_persistent_bottom_left_clip_b9624646.sav`.
The exact candidate is
`work/save_candidates/SLUS-00669_1_v224_from_b9624646_single_threshold_quad.sav`
(1,513,683 bytes; SHA-256
`fab19182ff32d0ec0e25f8ef334f1e3604ee407dea29fcf180c3cd2dd14156bb`).
The 1,655-byte report at
`work/save_candidates/SLUS-00669_1_v224_from_b9624646_single_threshold_quad.json`
has SHA-256
`06d409e29b2f2dd6aba2b761b0c39e721a1eb16bbe82e007b9d674e1eb858317`.

Exactly 418 decompressed RAM/payload bytes change: 38 in resident model 20 and
380 across the six double-buffered GPU packet arenas, with per-arena counts
`67/65/62/62/62/62`. The 3,819,109-byte decompressed payload has SHA-256
`b74fea8bf8be9d12394afe99afb9ed0c21f6451b273c8c6d94cdff4a412971b3`;
finished RAM has SHA-256
`b2a4cd510c004f7b6ed4b9934f2f8098d56f58bc87768ef179854e9793662a53`.
The resident model 20, each reinitialized packet arena, and the six-arena set
have SHA-256
`af389e6da468c4a5875d2bd4271574654a34fcd2ca6f62e235771fddfc03c03d`,
`3c03f04c72c2424d4a5faa272ef4d8e855dd647360b00e210bcbe02f6e0bd508`,
and `5574ecb24ef25954a3ecb136ea9def40b82e94d4de4927f9c1e552d2bab13680`.
The resident archive table remains byte-identical with SHA-256
`3eacc1ac53db105f07c987a3eeb20cfbbca9df9fefe21a8c7a4c4750e14dfba0`.
Model and packet-arena allocations, field header, scripts, actors, collision,
player, camera, and gameplay state are preserved; the arenas are deliberately
reinitialized for the topology change. The compressed encode/decode round trip
is exact. Migration tests pass `7/7`, and the chained release tests pass
`26/26`. Every other state must cold-load field 621 from V224 media.

Historical V223 remains the superseded UV-clamp release. Its reproduction
command was:

```powershell
python tools/build_surface_soylent_campaign.py `
  --source-disc output/Xenogears_PW_CD2_mass_driver_standalone_v163.bin `
  --donor-disc C:/path/to/Xenogears_PW_CD1.bin `
  --output work/surface_soylent_campaign_v223_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --disc-output output/Xenogears_PW_CD2_mass_driver_surface_soylent_v223.bin
```

That historical playable image is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v223.cue`, launched by
`output/PLAY_SURFACE_SOYLENT_V223.cmd`. Its 698,642,784-byte BIN has SHA-256
`4cd47686c8a7cc2b5be331f03b73f3e58bfd5e5e23b850ad7547abac917dc7e8`;
its 112-byte CUE has SHA-256
`bbc6dce43108fe5afc233d91acf6e0e11107833824c2216560abcc663c0e2e4a`.
The 119,807-byte repeat-stage manifest at `work/v223r_stage/manifest.json` has
SHA-256
`4d09092cfa36149cf7823c4d72fc9786233200bbd447f8d8bcfb05141b7e01e4`.
Two isolated V223 builds matched byte-for-byte.

The guarded V223 migration accepts only the 1,677,622-byte V222 Slot 1 captured
at the bottom-left threshold regression angle, SHA-256
`a714c8e830ee539157288d9407a22fc38ff670149a276acf9c02c3c69acba9e8`.
Its preserved source is
`work/save_backups/SLUS-00669_1_v222_bottom_left_clip_a714c8e8.sav`. The exact
candidate is
`work/save_candidates/SLUS-00669_1_v223_from_a714c8e8_threshold_uv.sav`
(1,519,504 bytes; SHA-256
`075b239d04e3781464f0a3e739ea8e65f8ba5086492eab0b9cdd87f71c797872`).
The 1,374-byte report beside it has SHA-256
`6ebf15ab51cf2a6d1158a789fd464ef557e6b78edfb8f17e11b4f326e44963b3`.
Exactly 28 decompressed RAM/payload bytes change, all from `0x95` to `0x8D`:
four display-list UV bytes in resident model 20 and the corresponding four UV
bytes in each of its six double-buffered GPU packet arenas. The decompressed
payload has SHA-256
`7012e08113286a05bd613a3b789b583d70c17343a28bbb302aa89ed7c9da6c3e`;
the finished RAM, resident model 20, and six-arena set have SHA-256
`065b299d971001cafbbedfa2ba172a76e9769a94f68e3b2557973a23ed23d893`,
`6f477079b5f55bedfbd2b438883b4a15026bdee4924b28aca242c5daedf5e9fa`,
and `92e6cec844d9f5a318e4dd9210efd5ae5db2d54386aec27329db7a20dcfa3ec1`.
Model topology and allocation, packet-arena allocation, field header, scripts,
actors, collision, player, camera, GameState, dialogue, walkmesh, and the
resident archive table are preserved. Every other state must cold-load field
621 from V223 media.

Historical V222 remains the superseded aperture-coplanarity release. Its
reproduction command was:

```powershell
python tools/build_surface_soylent_campaign.py `
  --source-disc output/Xenogears_PW_CD2_mass_driver_standalone_v163.bin `
  --donor-disc C:/path/to/Xenogears_PW_CD1.bin `
  --output work/surface_soylent_campaign_v222_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --disc-output output/Xenogears_PW_CD2_mass_driver_surface_soylent_v222.bin
```

That historical playable image is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v222.cue`, launched by
`output/PLAY_SURFACE_SOYLENT_V222.cmd`. Its 698,642,784-byte BIN has SHA-256
`4d386649f85a873003235ec8fc3082eb3e036aa5dbbc306c8cabdf84c8c80d03`;
its 112-byte CUE has SHA-256
`a2ab49791fbd65b34964361d8603e85e6cea5fb79430e852440af6e582f3220e`.
The 119,703-byte repeat-stage manifest at `work/v222r_stage/manifest.json` has
SHA-256
`d317d62ddb4ccaeb8cbcd12e80db38e0a65dbb25cd95f44e52cf1336d1b352dc`.
Two isolated V222 BIN builds matched byte-for-byte.

The guarded V222 migration accepts only the 1,521,337-byte V221 state with
SHA-256
`27710b20903e4eb6be1c818b3e3aaf8bf4050c7cc709575a73f5c2fb7f9d3581`.
Its exact candidate is
`work/save_candidates/SLUS-00669_1_v222_from_27710b20_flush_doors.sav`
(1,521,338 bytes; SHA-256
`66bbf32915c4181aefc7518b8d73c57979a132b24d3c5b6098d0951a6c104427`).
The 2,132-byte report beside it has SHA-256
`3cf42861256efd701ec1c1a298a55c2ded6d44d5d9cfdf82bd28e0b274606fe6`.
Exactly 204 resident payload bytes change: 14 header bytes, 129 script bytes,
49 actor bytes, eight ActorData bytes, and four sprite bytes. The archive table
changes by zero bytes. Models, camera, GameState, dialogue, walkmesh, collision,
unrelated actors, packet arenas, and the archive table are preserved. Every
other state must cold-load field 621 from V222 media.

Historical V221 remains the superseded hall-side-apron release. Its
reproduction command was:

```powershell
python tools/build_surface_soylent_campaign.py `
  --source-disc output/Xenogears_PW_CD2_mass_driver_standalone_v163.bin `
  --donor-disc C:/path/to/Xenogears_PW_CD1.bin `
  --output work/surface_soylent_campaign_v221_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --disc-output output/Xenogears_PW_CD2_mass_driver_surface_soylent_v221.bin
```

That historical playable image is
`output/Xenogears_PW_CD2_mass_driver_surface_soylent_v221.cue`, launched by
`output/PLAY_SURFACE_SOYLENT_V221.cmd`. Its 698,642,784-byte BIN has SHA-256
`577519db3fb4228c17f0555466866b271c265587a5fdc01515d9ff3f78f6827a`;
its 112-byte CUE has SHA-256
`a4134fcf3f5bee22530aa90aed6cd691a29983483eb8438828af5caa30ba1163`.
The 119,665-byte repeat-stage manifest at `work/v221r_stage/manifest.json` has
SHA-256
`ff8acf4b520034bc401dd8c88d7d051a5c90f4169b38d20648e0efea780e25b1`.
Two isolated V221 BIN builds matched byte-for-byte.

The verified V221 migration source is the 1,679,306-byte state with SHA-256
`e4aea385a822c19b74040bb442c1766ad122be1a95009a24d9bec51429198c54`.
Its exact candidate is
`work/save_candidates/SLUS-00669_1_v221_from_e4aea385_native_threshold_aprons.sav`
(1,521,337 bytes; SHA-256
`27710b20903e4eb6be1c818b3e3aaf8bf4050c7cc709575a73f5c2fb7f9d3581`).
The round-trip-verified 3,819,109-byte decompressed payload has SHA-256
`88525715b23bc3c13c1c39b1e25d9d06cb7772cd02560a9234d0ca722e97a816`
and changes exactly 1,025 bytes: one archive-table byte, 113 model-20 bytes,
and 911 bytes across six renderer packet arenas. The latter 1,024 bytes are the
complete resident-render change.

The migration preserves the actor/header layout, gameplay state, camera,
scripts, collision, resident model 2, model-20 allocation, all six packet-arena
allocations, and the volatile archive-table byte. It reinitializes the six
arenas only for the new model-20 topology and round-trips exactly. The verified
resident hashes are
`3eacc1ac53db105f07c987a3eeb20cfbbca9df9fefe21a8c7a4c4750e14dfba0`
for the archive table,
`749800fc048b59c2e89028b558846f375f9009ff01e0c2a0cc2bcf2b07857ba8`
for model 2,
`81b45178684dbd87fcaf71c4cba3f43bccb2932106aa2245fa2048303f0cb8bb`
for resident model 20, and
`8225f199051718510efad5f75e8a69ecc58a8a283f043eafa16b2c3235553d7e`
for the six packet arenas together. Apply this migration only to the exact
source identity; every other state must cold-load field 621 from V221 media.

Historical V220 remains the superseded inert-model release. Its
698,642,784-byte BIN has SHA-256
`b4f91cad8d7c819e4908d0e1c8369ff3fe3c432405a39ff4cb8d7bd9e961c63d`;
its 112-byte CUE has SHA-256
`4a07ef2954e665340ed6f00912777a1cac162b4d8bb3206c41e5a8e653d85ab7`.
The 119,623-byte manifest at
`work/surface_soylent_campaign_v220_stage/manifest.json` has SHA-256
`d7007838c4aae5198720fd055d6c226228093b40632188dfe066a51d7d53ffe0`.
Two isolated V220 builds matched exactly, all 220 staged files matched
byte-for-byte, and every replacement payload read back from the completed BIN.

The historical verified V220 migration candidate is
`work/save_candidates/SLUS-00669_1_v220_from_3081ee5d_camera_occluder_fix.sav`
(1,506,786 bytes; SHA-256
`d5acab444832d1e773a2bc66c58c0074cf2a54f901ebd689549acac34b3a017b`).
It is specific to source-state SHA-256
`3081ee5db0b0a5bf4a73a11970cb6341bebc1dca8d14415f0925d0fc0dc88053`.
Its round-trip-verified payload changes 548 bytes: two resident archive-table
bytes and 546 model-2 index bytes. Resident model 20 was already inert and is
preserved byte-for-byte. Actor/header state, gameplay state, camera, scripts,
collision, the volatile archive-table byte, and runtime pointers remain
unchanged. A state with any other identity must cold-load field 621 from the
historical V220 image instead of receiving an inferred resident-memory patch.

Historical V219 is the superseded one-sided-rear-plate release. Its
698,642,784-byte BIN has SHA-256
`6d00d1c9246aa5b61a23949d4f52b55a7ab87a787244143740980cd1e31d837f`;
its 112-byte CUE has SHA-256
`8403365f8a5010224604956d9b521594be603ae7408b426da4145c378b5aa7d6`;
and its 119,108-byte manifest has SHA-256
`421042c3f7162842761911621fb3a79e1858d08e1398cd3873b90f5a7811b560`.

Historical V218 is the superseded double-sided tiled-rear-plate release. Its
698,642,784-byte BIN has SHA-256
`1660e1a4ff0a90f416a428428e92fadfb05410cbb17d5be6c0b132ec39bc248a`;
its 112-byte CUE has SHA-256
`ae8410db00d89f864f42cb0bc880c708f59e36972f8da95da944e7aebfd31524`;
and its 119,048-byte manifest has SHA-256
`e3655f1e52dd1ed7aa74b4b094580d31a9a4c182059b49b991ff247218467e35`.
Its isolated repeat stage matched all 220 staged files byte-for-byte, all 32
replacement payloads read back exactly, and its repository suite passed 530
tests.

The historical safe V218 migration candidate is
`work/save_candidates/SLUS-00669_1_v218_from_e8bcc431_outline_fix_safe.sav`
(1,468,317 bytes; SHA-256
`ebffa2fb49f4486f6f57feec0ec67935c87ae19f6672091622a67cdc54db777d`).
It changes only 42 decompressed resident-geometry bytes while preserving the
live script pointers for static entities 60, 61, and 62. The failed migration
experiment established the hard safety rule: never null e60-e62; preserve
those pointers because the live field scheduler can still dereference them
even though those historical entities carried only the rear plates. V220 obeys
the same pointer-safety rule while making their model inert.

V217 is superseded but remains the historical aperture-aligned doorway release,
launchable through `output/PLAY_SURFACE_SOYLENT_V217.cmd`. Its 698,642,784-byte
BIN has SHA-256
`b672e95c592efe2978cd46a10ee3cde3b86d6af89a1db69a02646fbb0789184a`;
its 112-byte CUE has SHA-256
`2f921abda6c2b87ed5ab71896e1148965e59f464be0657b42bcbf9107d09d297`.
Its 119,029-byte manifest at
`work/surface_soylent_campaign_v217_stage/manifest.json` has SHA-256
`d36a6e37488e58a3b71c6db465287e6109d27aad106af27a1218bff61f3f39ba`.
Its isolated repeat stage matched all 220 staged files byte-for-byte with zero
mismatches, all 32 replacement payloads read back exactly from the completed
BIN, and its final repository suite passed 525 tests and 6,218 subtests.

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
release, launchable through `output/PLAY_SURFACE_SOYLENT_V216.cmd`. Its
698,642,784-byte BIN has SHA-256
`3764d6584fce3f590298cdc4e752432f4da1ec7770aa3416141296e6a79b4498`;
its 112-byte CUE has SHA-256
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
`output/PLAY_SURFACE_SOYLENT_V215.cmd`. Its 698,642,784-byte BIN has SHA-256
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

The captured V214 Slot 1 has an allocator-safe V215 migration candidate at
`work/save_candidates/SLUS-00669_1_v215_from_dcd01f7a_allocator_safe.sav`.
Its size is 1,674,270 bytes and its SHA-256 is
`509b97a21526b1fb86ed0e19ac2be5743462a669d404a6dac01740d06871d195`.
It leaves the live field-593 script and dialogue allocations at their V214
sizes, resumes the choice through retired entity-14 bytecode and dialogue ID
52, and preserves the open window, actor PCs, GameState, party, camera, heap
headers, and trigger-zone allocation.

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
failures, errors, or skips.

V213 is superseded but remains the historical first patient-record release,
launchable through `output/PLAY_SURFACE_SOYLENT_V213.cmd`. Its BIN had SHA-256
`9a2d781630e265af0f51ca01a801372d2766018f79a0bb5637818298c2b7e684`;
its CUE had SHA-256
`03c0ec7f3647ba91801dec48841ff9b1685cf23be2e5ca833f83a454e849dd71`;
and its 116,038-byte manifest had SHA-256
`8e1ce33f2fbb086a715be5070c119e10663a2a6c6d99823c6e4ce066e2a56a8b`.
Its final repository suite passed all 489 discovered tests with no failures,
errors, or skips.

V212 is superseded but remains the historical doctor-office exit-lock release.
Its BIN had SHA-256
`d98297809775b908ab8b4f6012ebdb102f18e7bdfd11157fcb69ab138a890d0d`;
its CUE had SHA-256
`e8976110516b392d5bfdc5b178ecb142c8dbe66204ef28d5f3f5002254a363b7`.

V211 is superseded but remains the historical current-boundary release. It is
launched by `output/PLAY_SURFACE_SOYLENT_V211.cmd`. Its BIN had SHA-256
`0b23ae64ccc0aececbd3cbb84b8c5486b8878884e048d341d4ab36662d0f5369`;
its CUE had SHA-256
`7b0c3f39c3d817da0f0b661f0627e893c74fb36625aac615326d2d0224aff3c6`.

V210 is superseded but remains the historical black-door-recess release. It is
launched by `output/PLAY_SURFACE_SOYLENT_V210.cmd`. Its BIN is 698,642,784 bytes
with SHA-256
`3ed26765a336d3ac0db79bcea03d1cc3a6b4501898391358289c55d687ce6068`;
the 112-byte CUE has SHA-256
`9ace108af58cfcb9c18c8453d2c5d4d491f6ab5b1dfc03173a6a260ce2c31534`.

V209 is superseded but remains the historical flush-door/direct-keycard
release. It is launched by `output/PLAY_SURFACE_SOYLENT_V209.cmd`. Its BIN is
698,642,784 bytes with SHA-256
`448c7feb4b95bb3470574ce28dc89cd7cddb198ba991fc45b82c01c10b97f590`;
the 112-byte CUE has SHA-256
`bb3200e86a2f3c1cb6585f531070ee191acbc6e925d2f1d0a430e8a456c87191`.

V208 is superseded but remains the historical three-examination-room release.
It is launched by `output/PLAY_SURFACE_SOYLENT_V208.cmd`. Its BIN is 698,642,784
bytes with SHA-256
`c81dd07af1c6790fe141bd7c2dfeb3ad5aa1ed4c8c69f0bbbbaa0714b827feee`;
its 112-byte CUE has SHA-256
`4b903adfd8b2c4900e8ef6cdd7b16cfb02fbc2465f70e0fdbec920efceb84d87`.

V207 is superseded but remains the historical bright-scanner credential-room
release. It is launched by `output/PLAY_SURFACE_SOYLENT_V207.cmd`. Its BIN is
697,916,016 bytes with SHA-256
`9667ae693a3692f6fef9cb2fa3b7eb1c43ed24d1caf7467008cac95fa8601548`;
its 112-byte CUE has SHA-256
`708299f7cc52ab24f3540023c5b56b6a4dc979309a96785dd8a9c621d135267c`.

V206 is superseded but remains the historical compact-blue credential-room
release, launched by `output/PLAY_SURFACE_SOYLENT_V206.cmd`. Its 697,868,976-byte
BIN had SHA-256
`de2413dcd94a976623168f5894ae13eb0afc81b6a6d8ab3bebd2d8e925211833`;
its 112-byte CUE had SHA-256
`b5eade571299297bdba56aae1dae07ee18638394afd24a435c6b9445ae4d5289`;
and its 96,523-byte manifest had SHA-256
`42ef530ce0014b572b68ea315d6291c390f86bc9e203e4f2159b2c59f2ac3284`.
Its isolated repeat preparation matched all 181 staged files byte-for-byte, and
its complete repository suite passed 450 tests / 5,531 subtests.

V205 is superseded. It remains the historical independent-key-room topology
release, launched by `output/PLAY_SURFACE_SOYLENT_V205.cmd`. Its 697,960,704-byte BIN had
SHA-256
`d3a2ccd661eae4cd987393cecefe1232f9e76f003152e1dd1dfab1521cd3017f`;
its 112-byte CUE had SHA-256
`cef99704474501354888739bc89afbebebd710de0c567233a321494b993e050c`;
and its 95,691-byte manifest had SHA-256
`6c32ce00d63e33e6c03f53bf1ab726179c142d1fee6814bca27b9d3885cac50e`.
Its isolated repeat preparation matched all 181 staged files. The V204-to-V205
comparison changed only the three route-owning replacement payloads: canonical
1736 (field 565), 1782 (field 588), and 1848 (field 621). Every other staged
replacement remained byte-identical.

V204 is the superseded complete-deathblow release. Its launcher remains
`output/PLAY_SURFACE_SOYLENT_V204.cmd`; its BIN had SHA-256
`79b59e10776da09b1175691d717a51f9642b5016056e91c316d964c7c9631255`,
and its CUE had SHA-256
`7681951f45e1db030fca4ec5e41f81d11633faf73aa31bdc5436d9519c71184e`.

V203 is the superseded receptionist-response release. Its launcher remains
`output/PLAY_SURFACE_SOYLENT_V203.cmd`; its BIN had SHA-256
`09ab185c6c9f0d7742b3c84d8b6eacc1ef0135b6e309c799e9b38989a8321ee4`,
its CUE had SHA-256
`1a93580d5774fa138fe8c73a6bfa854462f92b62908e027553a63348136bb5ca`,
and its 90,061-byte manifest had SHA-256
`72da61a5db1bae02bd4586f25ac614a4c0279ea1622d4212c64ce58de100cfc8`.

V202 is the superseded native-service-puzzle and Quarantine-keycard release.
Its launcher remains `output/PLAY_SURFACE_SOYLENT_V202.cmd`; its BIN had
SHA-256
`1acd87f65b4f986b74dcf0dff906b4eb48fde04013e1405b506b58791892eec0`.

V201 is the superseded recovered-ward and wide-service-target release. Its
launcher remains `output/PLAY_SURFACE_SOYLENT_V201.cmd`; its BIN had SHA-256
`85f9deeda68d1ad5915c39011541e75a2f7867cc440208854669265bc1001b32`.

V200 remains the superseded clinic-doorway-traversal release. Its launcher is
`output/PLAY_SURFACE_SOYLENT_V200.cmd`; its BIN had SHA-256
`0b567b4900987719e047b7144f6b238974dbca81b710c9e53fafbd0b1c9fa764`.

The superseded V199 release remains the historical phase-safe physician-collision
release with the clinic exterior-material defect. Its launcher is
`output/PLAY_SURFACE_SOYLENT_V199.cmd`; its BIN had SHA-256
`8049c25141251191c049bedfae484acfa9beb1f3ef04b19b8b7d593094f52659`,
its CUE had SHA-256
`75a60bab9a376c0a2ed7384b652f82cc7d10708812b02d313c4ad3a34a1a7d1f`,
and its 81,053-byte manifest had SHA-256
`03569ea1cfc03251d48b83fc95031cff7c8bfa6f97ec7eee32be0a84238ad0a3`.

The superseded V198 release remains the historical collision-safe patient-roaming
release with permanently ghosted physicians. Its launcher is
`output/PLAY_SURFACE_SOYLENT_V198.cmd`; its BIN had SHA-256
`fe1536e84d424e23363b0f5b20a0a253fae8355ab9b4824bd7dbf193bf70ff7e`.

The superseded V197 release remains the historical complete-dungeon release
with the shared Intake roaming rectangle. Its launcher is
`output/PLAY_SURFACE_SOYLENT_V197.cmd`; its BIN had SHA-256
`c1de9e3149ff9877d563c65ccabaaebdbaa86037b8499bab0373105423f9b92f`.

The superseded V196 release remains the historical one-door keycard release.
Its launcher is `output/PLAY_SURFACE_SOYLENT_V196.cmd`; its 697,673,760-byte BIN
had SHA-256
`956a76023d2f6665a74e6c4ed7373fa9b912d5a74bddbff86251a269aa14a950`.

The superseded V195 release remains frozen as the empty-medical-annex release.
Its launcher is `output/PLAY_SURFACE_SOYLENT_V195.cmd`; its 697,673,760-byte BIN
had SHA-256
`82cceca8dfb5814a94ebb5bf89787e4f4fdfb062593de604937a4d70f0e1c0fd`,
and its CUE had SHA-256
`dd483156d4d699e5658199225215392680f4717a9d0cb1208bb1bc9a3babeb2d`.

The superseded V194 release remains frozen as historical evidence. Its launcher
was `output/PLAY_SURFACE_SOYLENT_V194.cmd`; its 697,716,096-byte BIN had SHA-256
`e229febcfc5dff84dc5292e18256ed5899f3ff996573759e7fac92902773dd7e`,
and its CUE had SHA-256
`d033ae28bcabdf9cdd02b5c5eaabaa6131a5e98147daf12c95ba39ea4ef3e4da`.
All 23 V194 replacement resources read back byte-for-byte, all 1,157 unique
occupied sectors passed MODE2/Form1 EDC/ECC regeneration, and the isolated
repeat matched all 167 staged files and the BIN/CUE track layout. A direct V193-to-V194
replacement comparison found two new payloads, canonicals 1740/1741 for field
567, and two changed payloads, canonical 1736 for field 565's reciprocal return
and canonical 1848 for field 621's new destination. The other 19 replacement
payloads remain byte-identical.

Ordinarily, a field savestate embeds its GameState, mounted-media/FAT metadata,
resident scripts, dialogue, and headers. A fresh V207 New Game receives the
deathblow grant from canonical 2595, but an existing state does not: loading the
state or using Change Disc alone cannot replace its embedded deathblow flags.
Upgrade an existing state only with the fail-closed
`tools/grant_all_deathblows_duckstation_state.py` transformation followed by
`tools/migrate_duckstation_disc_state.py` for the current image. Both results must
be written separately from the source state, with its exact hash and expected
field checked. Keep the source as a backup, and fully close DuckStation before
installing the migrated copy.

The historical V214 Slot 1 upgrade was installed through the pinned
`tools/migrate_surface_soylent_v213_slot1_to_v214.py` helper. Its validated
1,433,243-byte candidate has SHA-256
`d4617725cfb7c46c71f0555805632827c056f48aa4935e88d96c2092cad2a047`.
The exact migration changes only 81 decompressed payload bytes: one audited
archive-table byte, 56 equal-length ATEL bytes, and 24 terminal-runtime bytes.
It patches the already-active entity-4 carrier in place, queues entity 5 at
`0x05F1` and entity 6 at `0x060E`, and preserves the open dialogue, entity 4's
active `0x05CF` wait, GameState, all three sprite spans, and the resident
archive table's volatile tail. The exact V213 source remains at
`work/save_backups/SLUS-00669_1_v213_3c2e76d5.sav`, 1,567,694 bytes with
SHA-256
`3c2e76d52ec7bfffa613766e98ce2ce6a84f8991722bd9b2c65839926723197e`.

Historical V213 was installed through the pinned
`tools/migrate_surface_soylent_v212_slot1_to_v213.py` helper. Its validated
1,453,925-byte candidate has SHA-256
`86b337dd0b63b321e12c31949247ccbcce719d58c80cd40137c595c7c270b7b6`.
It preserves GameState and every unrelated runtime byte while changing exactly
4,867 payload bytes: two resident archive-table bytes, 235 equal-length ATEL
bytes, 4,623 equal-length dialogue bytes, and seven entity-4 scheduler bytes.
The latter queue the normal terminal initializer for the next field tick, so
the already-loaded room gains the same hidden position, bounds, and flags as a
fresh V213 load without relocating heap data or moving Fei. The exact V212
source remains at `work/save_backups/SLUS-00669_1_v212_3493bff3.sav`, 1,606,184
bytes with SHA-256
`3493bff36abf088a0d80f7e71087854f7fe99262b5f25ed647ddfd9ed0257b49`.

V212 was installed through the pinned
`tools/migrate_surface_soylent_v211_slot1_to_v212.py` helper. Its validated
1,435,487-byte candidate has SHA-256
`e0e5dc547be87ef615a3b7a78ba7df16f5743cb18030c110609b29feeeb01d4e`.
It changes only two resident archive-table bytes (including the source table's
volatile tail) and thirteen `0x07C6 -> 0x07D0` gate operand bytes. GameState,
all ActorData, Fei's exact `(0,205)` saved stance, appointment values, and the
solid e19 radius remain byte-identical. The exact V211 source is preserved at
`work/save_backups/SLUS-00669_1_v211_a2bd6b8b.sav`, 1,578,436 bytes with
SHA-256
`a2bd6b8bff5d88be81549f876db5b40bb6da5217d84ea4e162f7f16c8028ff2f`.
The live Slot 1 may naturally acquire a new hash after the player saves again.

Historically, the V209 Slot 1 was a guarded V208-to-V209 media migration. Its
1,480,634-byte state has SHA-256
`d0f33fb409623c7bd3aa4912a9e0170812309b41a6f672af40c94c0eacb56039`
and mounts the V209 CUE. The migration changed four resident archive-table bytes
while preserving gameplay state. It remains resident in V208 field 621 at Fei
position `(1623.63,1222.92)`, triangle 76, facing `0x0E00`; changing media cannot
replace that already-loaded header, script, or door placement. Leave Intake
through any working door and return before judging V209's flush panels or e22
keycard gate. The exact V208 source is preserved at
`emulator_data/SLUS-00669_1.pre_v209_ef67aa91_20260824T172455.sav`, 1,621,486
bytes with SHA-256
`ef67aa917cbbf9de02b6337737bc5ad3f7ba434824691e4b0d91217df55e2684`.
Player movement and emulator input remain user-controlled.

Historically, the V207 Slot 1 was a guarded V206-to-V207 media migration, but it still had
V206's compact blue field-588 room resident. Changing the mounted image cannot
replace that active room's bundle, script, models, or graphics. Leave through
its existing return to Intake at `621/p5`, then re-enter the same door. Only
that round trip loads V207's bright clinical diagnostic-scanner room; the
still-resident V206 room is not V207 validation. The installed 1,650,255-byte
state has SHA-256
`e198990d0bf6ac3f976805cda5d853d3f09245ed2c434aa8433eaf0cecfe4b0c`.
Its exact 1,858,882-byte V206 source remains at
`emulator_data/SLUS-00669_1.pre_v207_cd47b5d8_20260823T221553.sav`, SHA-256
`cd47b5d8c6a5f82244f0ec08500c42fdd479865264919d764b31ff3c35eaa7d9`.

Historically, the state was deterministically migrated from V205 to V206's CUE
and resident archive table while preserving GameState, all actors, Fei's
position, and every byte outside that table. The installed 1,745,647-byte state has SHA-256
`e1be06cf08d209a88808377cc74a6305444987c0f260c783b4af8a6d2ba36b7f`;
its exact V205 source is preserved as
`emulator_data/SLUS-00669_1.pre_v206_75207402_20260823T210834.sav`, SHA-256
`7520740280e8a65a79dcb5f47a00741db3bfd3bdefe3c055188281cc0e474a1b`.
That V206 migration intentionally left the then-active V205 room resident,
because a media migration cannot replace an active field; its historical V206
validation likewise required an exit and re-entry.

The V205 Save State 1 was migrated with the pinned
`tools/migrate_surface_soylent_v204_slot1_to_v205.py` helper. It updates the
mounted CUE, resident archive table, and equal-length resident field-621 script,
so the saved e26 interaction can be tested immediately without moving Fei or
reloading Intake. The installed 1,670,052-byte state has SHA-256
`31f0c570935b1f31f5c3aa58fb83227a76a48dfcd5967d6d6b41db36b4f53485`.
Only one archive-table byte and the two audited destination bytes changed in
the decompressed payload; GameState and runtime actor state remain byte-identical.
The exact V204 source is preserved as
`emulator_data/SLUS-00669_1.pre_v205_20a7487b_20260823T193318.sav`.

The following state notes are retained as historical room-specific validation
records. V195's Save State 1 is an exact, useful exception to the normal resident
field-script rule: it is already resident in field 621 with V194's script, whose
e25 action targets field 567/p0. Load it and press a fresh X at the marked door
immediately; no reception reload is needed. Logical field 567 then loads from
the mounted V195 disc and therefore exercises the new empty examination room.

The V203 receptionist-validation Save State 1 is resident in field 621 under
V202 and is paused in receptionist entity 13's post-check-in dialogue ID 12.
Fei is at approximately
`(870.00,1431.09)` on triangle 28, directly facing the receptionist at
`(870,1302)`. Check-in bit `0x03FA/7` is set, the appointment is armed, and the
registered alias is `Aron Voss`. The 1,711,245-byte state has SHA-256
`3f6dd8311e0761c21a88aef0d7d8eb67746da987193aad51d3e10f6fde3a6797`.
Because it embeds V202's resident field-621 dialogue and mounted-media path,
loading it restores the V202 CUE even if V203 was selected before the load.
After loading, use DuckStation's Change Disc command to select the V203 CUE,
close the old line, enter the records room, return to reception so field 621
reloads from V203, and speak to the receptionist again.
She must say, `I see you have signed in. Please wait here until your name is
called.` Player movement and emulator input remain user-controlled.

The previous Save State 1 is resident in field 565 under V201. Fei is at
approximately `(3553.43,-1107.49)` on triangle 30, facing field-565 entity 12 at
`(3500,-1060)` on triangle 32. Its saved resident script is V201's action, so
mounting V202 cannot replace that already-loaded copy. Leave field 565 through
an existing route and re-enter it from the V202 image before testing the marked
controller. On the reloaded field, a fresh X opens the native input interaction;
enter `Up, Down, Up, Left, Right` to authorize and release the passage. Player
movement and all emulator input remain user-controlled.

That 1,857,740-byte state has SHA-256
`480abc4561d47a2ef09b9563a69b3f8ce410ea8b0d5003811d386d49c3ae9dff`.
Its persistent banks already have security-keycard bit `0x021A/0` set, while the
new Quarantine-keycard bit `0x021A/8`, clue bit `0x021E/8`, and tone-authorization
bit `0x021E/9` are clear. It therefore exercises the intended V202 sequence
without replaying the clinic fight, once field 565 has been reloaded from disc.

The earlier V201 Save State 1 marker was resident in field 565 under V200, with
Fei at approximately `(4250.66,-2999.62)` facing entity 6. Its resident action
was exactly STOP; it likewise requires a field-565 round trip before testing
V201's recovered `service_stabilization_staff` route.

The earlier Save State 1 used for V200 is 1,546,265 bytes with SHA-256
`9d54f0070d0e40dbc9103e3e865177082221ae7df3e9bef0f9a2ebb132e49ced`.
It is already resident in field 550 at `BATTLE_PENDING`: all four security entry
scripts have finished, their completion mask is `0x000F`, and the security
arrival dialogue is open. It also embeds V199's old field-550 script. Loading it
on V200 therefore cannot replay either corrected doorway crossing; mounting a
new BIN does not replace a resident field script in RAM. For acceptance, start
from a state before entering the examination office (or replay the appointment),
enter field 550 from V200, and save before the second refusal/security call.

The older Save State 1 used for V199 embeds V198's resident field-621 script and
live e35 physician with collision flag `0x80` still set. After loading it on
V199, a safe round trip through a nearby room and re-entry to reception recreates
the called-phase physician with V199's solid state. Loading it without that room
reload cannot test the collision fix because the actor flags and script remain
embedded in the savestate.

Historically, the Save State 1 used to validate V193 contains V192's field-621
action table and dialogue. After loading it with V193, leave the reception hall
through another door and re-enter it before testing entity 22; otherwise the
embedded V192 action will still open the door. Once reloaded, a fresh X press at
that saved stance must show the lock notice with no sound, leaf animation, or
transition.

The newer Save State 1 used for V194 marks field-621 entity 25, but at that time it
embeds the older field-621 script already resident in memory. Leave reception
through another door and re-enter it from the rebuilt image before trying the
marked staff door. Without that reload, the embedded pre-V194 action can still
send the party directly to field 565 instead of the new field-567 ward.

V231 manual acceptance may use the exact migrated current-state candidate at
`work/save_candidates/SLUS-00669_1_v231_from_1eb8b434_field592_patient_record.sav`,
or cold-boot the V231 CUE and load each affected room from current media. The
migrated state opens in field 592 with terminal e19's old window already fully
rendered in captured GPU state. Press X once to close that preserved placeholder
and, without moving Fei, press X again to invoke the migrated terminal action.
Verify the fresh window begins `PATIENT RECORD: N-592-07`, advances to the
joint-inflammation and nanomachine-response page, and closes normally without
changing any other room state. Historical guarded candidates remain useful only
for their own inherited regressions. Run the Intake rendering checks from a
cold load of field 621:

1. Open the original east entity-24 leaf first. Inspect the retail model-19
   apron from the complete reachable camera orbit: it must be a short textured
   pathway beyond the leaf before the native black clear, not a rear wall or a
   full vestibule.
2. At each of Doors A, B, and C, inspect the closed and open leaf across the
   complete reachable camera orbit and pause at every camera limit so
   interpolation can settle. Each model-20 apron must match the original e24
   apron's visible depth and U continuity. Its one deliberate texture difference
   is the far-depth clamp at `V=0x8D`; no added-door packet may retain a
   `V=0x95` far endpoint. Each closed leaf must be coplanar with its aperture,
   and each apron must begin on that plane and extend only to the far side. The
   full leaf must remain visible with no black outline, bottom-left near-black
   wedge, triangular tear, diagonal band, hall-side slab, or hole in the
   surrounding white shell.
3. Open and close each added leaf while continuing the camera orbit. With the
   leaf closed, no lower-left portion of the apron may sort in front of it. With
   the leaf open, the one whole-width FT4 must appear as a continuous pathway
   with no lateral midpoint seam, crack, flicker, or texture discontinuity.
   Model 20 may share the aperture edge with model 1 but must never overlap
   positive area on the accessible hall floor. Black may begin only beyond the
   44-unit far-side floor; no vertical/rear model-20 face or model-2
   ceiling/fascia polygon may cross the near plane, leaf, or party.
4. Traverse every examination door in both directions and repeat the orbit
   after returning to Intake. Confirm the existing X targets, leaf timing and
   sound, destinations, bounce-safe returns, closed walkmesh barrier, and camera
   behavior are unchanged.
5. Leave field 621, reload it from V231 media, and repeat the regression
   angle plus one complete open/close cycle at the original e24 and all three
   added doors. Confirm stable 30 FPS and the same clean result after the second
   field load.

Then test the shared field-352 return doorway:

6. Cold-load fields 550, 567, 591, 592, 593, and 594. In each room, approach e17 from
   every reachable lateral offset and hold Forward without pressing X. The leaf
   must remain closed and no action or dialogue may begin. The thin rectangular
   seal must cover only the aperture, centered at `(0,266)` with script
   half-extents `(24,8)`, physical half-extents `(48,16)`, and contact planes
   `z=250/282`. A centered Fei must reach the seal naturally. One fresh X press
   must select the unchanged e17:s2 action, and all six retail 1,948-byte
   walkmeshes must remain unchanged.
7. In field 550, reproduce the reported stance at fixed-point
   `(2841247,14988804)/65536`, approximately `(43.353989,228.710999)`, yaw
   `0x0800` on triangle 15. Before security victory, Forward alone must neither
   open the leaf nor show the locked-door response. One fresh X press must show
   the locked-door/continue-procedure response exactly once.
8. Keep holding Forward through multiple scheduler cycles and confirm no
   automatic action occurs. Use a separate fresh X press and confirm the
   bloodwork gate responds once without treating the closing press as another
   interaction. Repeat the one-shot X check during `RESOLVED / FLEE_PENDING`
   and confirm it uses only the escape-in-progress response.
9. At `RESOLVED / COMPLETE`, approach the same field-550 threshold from the
   saved off-center stance. Confirm sound `0x77`, the blocking e18:s4 leaf-open
   helper, e19:s4 seal release, and the field-621/p3 transition occur in that
   order. No seal release may occur on a denied or fleeing path.
10. In fields 567 and 591--594, confirm Forward alone never opens the leaf, then
     use a distinct fresh X press and verify the retained native leaf animation,
     destination, return, and byte-identical walkmesh. Also test one simultaneous
     Forward+X approach per room and confirm it runs the action only once. In
     field 567, face each reachable section of the visible model-3 side
     workstation and confirm the narrow carriers display exactly
     `PATIENT RECORD / No patient is loaded / for this room.` The readout must be
     repeatable and read-only; the open aisle and bed-facing heading must remain
     silent, with no item, state write, NPC, combat, gate, or progression event.
11. In field 594, press X at the saved center-aisle position and verify nothing
    opens. Then stand directly in front of and face each reachable section of
    the model-3 side computer bank. Its three narrow carriers must provide the
    T-594-03 record across the full frontage while reporting the fin-armed
    patient's vitals, hydration, metabolic response, injection uptake, and
    improving prognosis without writing a credential or progression flag.
    Facing the bed must not invoke the record. Confirm e17 returns only to
    `621/p5` and field-565 e7/p3 remains sealed and dormant.
12. Visit fields 591--594 and confirm that each room contains its own doctor and
    visibly different demihuman patient beside the examination bed. Speak to
    both characters in every room: each doctor must use a different private-area
    warning and direct Fei to the waiting area, while each patient must retain a
    distinct hopeful treatment line. Use the actual side computer bank in every
    occupied room and confirm fields 591--594 show, respectively, the H-591-04, N-592-07,
    A-593-12, and T-594-03 records for those patients. Each record must have two
    explicit pages, fit its window, and contain no empty-queue placeholder or
    Fei office data. Confirm field 567 remains NPC-empty and its workstation
    shows only the no-patient record described above; field 550's story doctor
    office remains unchanged.
13. Cold-load field 549. Reproduce the exact V229 round-trip stance at fixed
    position `(-13485612,0,15269605)/65536`, approximately
    `(-205.774109,0,232.995682)`, yaw `0x0600` on triangle 10. Hold Forward
    southwest: that infinite travel line must clear e16's shifted effective
    disk at `(-244,248)` by 5.639 world units without snagging. The visible
    leaf, native helper, and e6 action carrier remain at `(-240,240)`. Then
    deliberately approach the closed leaf. Holding Forward alone must not open
    it; one fresh X press inside the retained effective `36 x 40` envelope must
    invoke unchanged e6:s2 exactly once. Without that action, the 32-unit disk
    must keep the complete walkmesh cut across triangles 6, 10, 11, 12, and 13
    impassable. Repeat the deliberate-X check from the older audited stance at
    `(-193.825134,244.253677)`.

## Automated coverage

V233 focused coverage pins field 567's NPC-empty population, three retired
entity carriers, exact narrow/facing-gated workstation frontage, and exact
`PATIENT RECORD / No patient is loaded / for this room.` text. It proves the
interaction is repeatable and read-only, preserves the native exit and exact
field-352 walkmesh, and cannot award an item, write state, start combat, open a
gate, or advance progression.

V231 coverage retains V230's field-549 proof, separately pinning e6's action
center at `(-240,240)` and
e16 physical-seal center at `(-244,248)`, plus the retained `0x08` script
radius, 16-world-unit physical radius, and 32-unit effective player contact
radius. It proves that the complete contact circle lies inside e6:s2's unchanged
effective `36 x 40` deliberate-X envelope, the exact V229 southwest travel ray
clears the shifted disk by 5.639 world units, Forward alone cannot open the
leaf, and the full conservative sampled cut through triangles 6, 10, 11, 12,
and 13 remains closed.

Historical V231 migration coverage pins the exact 1,845,278-byte V230 field-592
source, 1,670,155-byte V231 candidate, 2,504-byte report, and all SHA-256
identities above. It proves the exact 2,505-byte decompressed whitelist: 2,201
archive-table bytes, one resident terminal-dialogue operand, 299 bytes in the
retired ID45 cavity and its width field, and four active-window pointer bytes.
It freezes component sizes, both heap gaps, walkmesh, Fei, party, GameState,
field variables, camera, every actor, terminal VM state, and every other window
byte; it also proves a cold V231 reload uses ordinary dialogue ID53. Every
nonmatching source or media identity fails closed, and the compressed round
trip is exact.

The final V231 repository discovery suite passes all 616 tests. The focused
patient-room suite passes 26 tests, the blueprint suite passes 19, the campaign
builder suite passes 62, and the V230-to-V231 migration suite passes 11.

Historical V230 migration coverage pins the exact 1,615,526-byte V229 source,
1,466,492-byte V230 candidate, 2,496-byte report, and all SHA-256 identities
above. It proves the exact seven-byte decompressed whitelist at payload offsets
`0x148DE`, `0x10C73A`, `0x10C73C`, `0x112180`, `0x112188`, `0x1EF676`, and
`0x1EF67A`, broken down as one archive-table byte and two bytes apiece in the
resident ATEL position, runtime e16 position, and cached-header position. It
also freezes e16's collision volume, Fei, party, GameState, field variables,
camera, dialogue windows, every unrelated actor, and the archive-table volatile
tail; every nonmatching source or media identity fails closed, and the
compressed round trip is exact.

Historical V229 migration coverage pins the exact 1,632,883-byte V228 source,
1,485,222-byte V229 candidate, 2,030-byte report, and all SHA-256 identities
above. It proves the exact two-byte decompressed whitelist at payload offsets
`0x10C74D` and `0x11217C`, the resident field-549 script radius and runtime e16
collision-radius changes, and the zero-byte archive-table delta after rebuilding
against V229 media. It freezes Fei, party, GameState, field variables and
backup, camera, dialogue windows, actor records, unrelated ActorData, and the
archive-table volatile tail; every nonmatching source or media identity fails
closed, and the compressed round trip is exact.

Historical V228 coverage pins the family tuple `(550,567,591,592,593,594)`, the
shared field-352 walkmesh's 1,948-byte size and SHA-256
`abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df`,
and the retained rectangle at `(0,266)` with script half-extents `(24,8)`,
physical half-extents `(48,16)`, and contact planes `z=250/282`. It proves
e0:s1 resolves to shared STOP `0x068C`, the complete retired
`0x044E..0x04A5` cavity is byte-identical to its field-352 foundation with no
active entry point, and Forward alone cannot call e17:s2. The unchanged ghost
carrier, native X action, leaf helper, destination, and office state gate remain
separately frozen. It also pins field 594's checked 1794/1795 targets, p5 return,
exact read-only Treatment Preparation text, and absence of any credential or
progression write.

It also pins one solid, talkable doctor/patient pair in each of fields
591--594, mutual doctor/patient facing, safe bed-side placements, four distinct
demihuman actor/sprite identities, four different private-area warnings, and
four different hopeful patient responses. Field 567 remains the single empty
examination room, and field 550's story population and behavior remain exact.

Historical V228 migration coverage pins the exact 1,735,278-byte V227 source,
1,735,287-byte candidate, 1,804-byte report, and their SHA-256 identities above.
It proves that exactly 2,464 payload bytes change, all within the serialized
Disc 2 archive table, and that the only changed resources are 1788, 1790, 1792,
and 1794. It freezes the resident field-621 script, hybrid loaded header, actor
data, runtime PCs, route, GameState, party, field variables, camera, windows,
dialogue, walkmesh, and volatile archive-table tail byte; every nonmatching
source or media identity fails closed.

Historical V227 migration coverage pins the exact 1,910,685-byte V226 source,
1,735,278-byte candidate, 1,809-byte report, and their SHA-256 identities above.
It proves the exact 3,033-byte decompressed whitelist: 3,031 archive-table bytes
plus the two resident `565/p3 -> 594/p0` route bytes, with zero ActorData or
runtime-PC changes. It also freezes byte-identical Fei, party, GameState, field
variables, camera, windows, loaded header, dialogue, walkmesh, and neighboring
components, requires an exact compressed round trip, and fails closed on every
nonmatching source or media identity.

Historical V226 migration coverage pins the exact 1,855,939-byte V225 source,
1,680,239-byte candidate, 1,629-byte report, 3,819,109-byte decompressed
payload, and all SHA-256 identities above. It proves the exact 70-byte payload
whitelist: four archive-table bytes, 62 equal-size resident field-592 ATEL
bytes, and four bytes confined to entity 0's two runtime PC records. The loaded
header, walkmesh, every non-controller actor, GameState, party, field variables,
camera, windows, native X carrier, closed leaf, and rectangular seal remain
byte-identical. Every nonmatching source or media identity fails closed, the
compressed encode/decode round trip is exact, and all five migration tests
pass.

Historical V225 coverage pins the family tuple `(550,567,591,592,593)`, the shared
field-352 walkmesh's 1,948-byte size and SHA-256
`abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df`,
and the rectangle at `(0,266)` with script half-extents `(24,8)`, physical
half-extents `(48,16)`, and contact planes `z=250/282`. It freezes the 87-byte
retired cavity at `0x044E..0x04A5`, its only new entity-script entry point
e0:s1, and the exact
63-byte worker: inclusive X bounds `-64..64`, reachable minimum `z=228`, the
blocking e17:s2 selector `0x22`, post-action coordinate refresh, and the
WAIT-backed disarm/retry targets at `0x0471` and `0x0487`. It also pins both
recorded off-center X/Z positions, the unchanged manual-X carrier, and the four
non-office native actions. Field 550 separately freezes the bloodwork gate's
locked, fleeing, native-exit, and already-open branches plus the success-only
ordering of sound, blocking leaf helper, seal release, and field change.
The focused worker simulator proves one action while Fei remains at or beyond
`z=228`, no repeated call across later scheduler frames, a below-threshold
rearm at `z=227`, and exactly one later call on the next approach. Simultaneous
Forward+X behavior remains an explicit manual acceptance item above. The five
guarded migration tests independently freeze the exact 87-byte payload
whitelist, resident script/header/runtime identities, saved stance, archive
policy, preservation spans, candidate/report identities, and compressed round
trip.

Historical V224 coverage pins the original e24 leaf/model-19 separation, the source apron
vertices, FT4 ordinal, indices, texture states, packet, 89-by-44 dimensions,
model-19 size/hash/counts/offsets, and its retained shifted header node. It pins
model 20's 396-byte allocation and SHA-256
`8ef50d3f377c7b8caf2fdcfa0fcaecebe3d25ce5a51a90dfa0f14a734fdf3b52`,
`15/15/2` counts, exact offsets `0x48/0x48/0xC0/0x140`, GPU arena `0x140`,
one visible whole-width FT4 with indices `(0,1,4,5)`, fourteen degenerate F3
records, local
`x=0..89,y=0,z=0..44` bounds, exact reversed node placements, co-planar leaf
origins, far-side footprints, disjoint positive-area half-spaces for model 20
and model 1's hall floor, and absence of local negative-Z or vertical geometry.
It pins the exact packet `00 00 00 2D 97 89 97 8D B6 89 B6 8D`, retaining
V223's `V=0x8D` far-depth clamp while every vertex, coordinate, texture state,
footprint, and placement remains V223-identical. The packet allocation equation,
`1 * 0x28 + 14 * 0x14 = 0x140`, proves the topology remains allocation-safe.

The OT regression pins V223 state
`b962464676e5c2b9a59918a5b9247d5d747276ab6ec0fc4a36c1f5f48ae96d24`,
Door B leaf/lower-half packets `0x1227CC/0x13B4B4`, q1 bucket `0xB2A08`, and
chain
`0xB29F4 -> 0x1255E0 -> 0x125590 -> 0x1227CC -> 0xB29F0 -> 0x13B4B4 -> 0xB29EC`.
It pins Door C leaf/lower-half packets `0x122A58/0x13B768`, q1 bucket
`0xB2AD4`, and chain
`0xB2AC0 -> 0x1259F0 -> 0x125770 -> 0x122A58 -> 0xB2ABC -> 0x13B768 -> 0xB2AB8`.
The lower half therefore draws after each leaf while its mate draws five buckets
earlier; aligned crop masks prove the same silhouette survived the V223 UV
change. Native one-FT4 apron topology and V224's one coherent centroid-depth OT
placement are covered as the correction. Coverage also pins
the 39,292-byte model archive
(`b06e38c58fcd5e1ce5033e1135f0ae7c7d745b9ef37575f44b0cba4c936c52aa`),
135,648-byte field bundle
(`011be9593a2c565e6c3bb5f325ef64ac47811592794945ce529fcb3b6eb36677`),
unchanged 10,895-byte script
(`a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c25fca52f202845ea7`),
and 1,408-byte header
(`bd8be9feef57bff074c81c885d66b329ed20456e42d3a11c6b8e03b18550598f`).
Model 2's exact native and retained V220 hashes,
groups 0 and 2 as the only disabled groups, four `POLY_F3` plus 134 `POLY_F4`
degenerate records, and textured groups 1 and 3 remain covered with packet
layout, model allocation, collision, and camera data unchanged. Media coverage
pins the 698,642,784-byte BIN, 112-byte CUE, and 119,788-byte repeat manifest
with their V224 SHA-256 identities above, proves the primary and repeat builds
match byte-for-byte, and requires the cold-load and original-versus-added apron
orbit checks above. The focused V224 suite passes all 62 tests; the complete
repository suite passes all 567 discovered tests with no failures, errors, or
skips.

Historical V224 migration coverage pins the exact 1,672,493-byte source,
1,513,683-byte candidate, 1,655-byte report, 3,819,109-byte decompressed
payload, and all SHA-256 identities above. It proves an exact 418-byte
RAM/payload whitelist: 38 resident model-20 bytes plus 380 packet-arena bytes
distributed `67/65/62/62/62/62`. It verifies disk/runtime primitive counts
`15/17` with the expected two-primitive runtime overhead, preserves the model
and packet-arena allocations, and reinitializes all six arenas for the new
topology. Field header, scripts, actors, collision, player, camera, gameplay,
and the resident archive table remain byte-identical. Every nonmatching source
or media identity fails closed, the compressed encode/decode round trip is
exact, all seven migration tests pass, and all 26 chained release tests pass.

Historical V223 coverage pins model 20's 396-byte allocation and SHA-256
`524f3d90eb72bb674cba3428a7d55b40f580e4064aaf3270b54d8f331320c98a`,
`15/14/2` counts, offsets `0x48/0x48/0xC0/0x138`, GPU arena `0x140`, two
visible FT4 packets, twelve degenerate F3 records, and exact packet payloads
`97 89 97 8D A6 89 A6 8D` and `A6 89 A6 8D B6 89 B6 8D`. It also retains
the historical 39,292-byte archive, 135,652-byte bundle, unchanged script, and
1,408-byte header identities above.

Historical V223 migration coverage pins the exact 1,677,622-byte source, 1,519,504-byte
candidate, 1,374-byte report, and all SHA-256 identities above. It proves an
exact 28-byte RAM/payload whitelist: four resident model-20 far-depth UV bytes
plus four corresponding bytes in each of six packet arenas, all `0x95` to
`0x8D`. It preserves model topology/allocation, packet-arena allocations,
field header, scripts, actors, collision, player, camera, GameState, dialogue,
walkmesh, and the resident archive table, rejects every nonmatching source or
media identity, refuses the live Slot 1 path, and requires an exact compressed
encode/decode round trip.

Historical V222 migration coverage pins the exact 1,521,337-byte source,
1,521,338-byte candidate, 2,132-byte report, their SHA-256 identities, and the
204-byte resident-payload whitelist (`14 + 129 + 49 + 8 + 4`). It requires zero
archive-table changes and preserves models, camera, GameState, dialogue,
walkmesh, collision, unrelated actors, packet arenas, and archive-table bytes.
Every nonmatching source fails closed.

Historical V221 migration coverage pins the exact 1,679,306-byte source and 1,521,337-byte
candidate identities, the 1,025-byte decompressed-payload whitelist
(`1 + 113 + 911`), all six packet arenas, and the final resident hashes. It
rejects every nonmatching source and any change to actors, headers, gameplay,
camera, scripts, collision, model 2, model-20 or packet-arena allocations, or
the volatile archive-table byte, and requires an exact encode/decode round trip.

Historical V220 coverage pins model 20's 396-byte allocation, exact inert
SHA-256, 16 degenerate `POLY_F3` records, and safe preservation of the e60-e62
resident pointers. It also pins the model-2 camera cleanup inherited by V221
through V231.

Historical V218 coverage pinned field 621's shared 396-byte tiled opaque-black
rear plate at local `z=-32`, absence of the earlier thin border, and safe
preservation of the e60-e62 resident pointers. It also retained coverage for
field 593's aperture-aligned thin rectangular doorway seal, narrow
forward-movement poll, unchanged native door action, X-button interaction, and
byte-identical retail walkmesh. Final V218 coverage totaled 530 passed tests.

Historical V217 coverage pins field 593's aperture-aligned thin rectangular
doorway seal, narrow forward-movement poll, unchanged native door action,
retained X-button interaction, and byte-identical retail walkmesh. Final V217
coverage totals were 525 passed tests and 6,218 passed subtests.

Historical V216 coverage pins field 593's repeatable post-keycard medical
diagnostics, including pulse 64, blood pressure 118/72, temperature 36.8 C,
respiration 14, and elevated neural activity. It rejects the superseded
already-removed response and verifies that the diagnostic path cannot repeat
the item sound, acquisition receipt, or credential write. Final V216 coverage
totals were 518 passed tests and 6,212 passed subtests.

Historical V215 coverage pins true wall apertures for all three field-621 examination
doors, plate-free recessed black jamb/lintel/sill returns, and full-leaf
visibility at the audited oblique camera. It also verifies field 593's
font-grid-safe Quarantine-keycard dialogue, explicit `Accept it` / `Leave it`
menu, repeatable state-neutral and silent Leave branch, and the Accept-only item
sound, acquisition receipt, and credential write. Final V215 coverage totals were
508 discovered tests and 6,212 passing subtests, with no failures, errors, or
skips.

Historical V214 coverage pins three field-550 interaction carriers to side computer-bank
static node 27/model 3 at `(80,-167)`, `(116,-167)`, and `(152,-167)`, with
encoded `0x01/0x0F` bounds and native facing gates. It exhaustively verifies
that all 1,201 reachable frontage points accept terminal-facing use, zero
frontage points accept the saved bed-facing heading, and the interaction union
remains separate from the doctor's volume. The retained patient-record
coverage checks all three registered aliases, live Fei-weight conversion, fixed
clinical vitals, the defensive missing-record path, and the read-only
`100% / PERFECT FIT` compatibility result. Historical V213 coverage also pins
the exact resident script/dialogue payloads and fail-closed V212-to-V213 Slot 1
migration.

V209 coverage freezes the 17-room, 20-pair, 40-endpoint graph; exact unused
target pairs 1788/1789, 1790/1791, and 1792/1793; all three bright field-352
clinic clones; bed and workstation preservation; disabled encounters; p7-p9
returns; the five Security-keycard-gated Intake doors; all three flush wall
planes; 444-unit straight-door spacing; the diagonal first panel's rendered
face toward the saved Fei stance; and the dedicated Quarantine-keycard test at
Intake e22. Script simulation verifies that the check-in action cannot jump to
the retail binary-code menu, every custom path natively closes the six panels,
that fields 591/592 never write the Quarantine credential, field 593 writes it
once with sound `0x37` and then reports an empty slot, and the entire final
field-588 bytecode contains no such writer. It also freezes restored
`621/p5 <-> 565/p3` and `565/p5 <-> 588/p0` routing. The campaign integration
suite passes 58 tests, the focused blueprint/room suite passes 53 tests, the
focused donor/title/room suite passes 57 tests, and isolated repeat preparation
matches all 220 staged files.

Historical V207 coverage freezes exact Disc 1 source canonicals 1711/1712 and logical
targets 1782/1783, the bright clinical shell, obvious e4 diagnostic scanner,
native e17/e18 return to `621/p5`, compound Security-keycard-plus-five-tone
entrance gate, and the no-recheck cutoff-plus-Quarantine-key award. The focused
blueprint module passes all 17 tests. V206 coverage freezes exact Disc 1 donor
canonicals 1757/1758, the compact blue
Solaris room shell, baked center-workstation nodes 11/15, e7's aligned X carrier,
retired e6/e8/e9/e10 behavior, the native animated return to `621/p5`, and the
unchanged five-tone-gated one-time Quarantine-key flow. V205 coverage freezes
the independent `621/p5 <-> 588/p0` credential room, the
reciprocal `565/p3 <-> 565/p5` internal bypass, all 34 physical endpoints, and
the unchanged tone-gated one-time key writer. V204 coverage freezes canonical
2595's exact GameState transformation, all
eleven character/form masks, the zero native sets for Chu-Chu and Maria, and
byte-identical levels, stats, and unrelated ability data. It also validates the
retained canonical 2607 level-1 requirement tables and the fail-closed separate
savestate migration path. V203 coverage adds an exact layout assertion for
receptionist dialogue ID 12 and executes both state branches: unregistered state
selects ID 11, while the saved check-in/armed state selects the new ID 12 and
restores player control. V202 coverage additionally checks that field-589 entity
9 is clue-only, both
native field-565 entity-12 success exits award tone authorization and release
the two-part passage, field-588 entity 9 denies premature use and independently
commits its cutoff and distinct Quarantine credential, and field-565 entity 10
tests `0x021A` bit 8 rather than the clinic security card. V201 coverage additionally
tracks logical field 590's donor and dummy
target identities, three audited entries, two reciprocal field-565 thresholds,
the gated reciprocal field-624 threshold, neutralized surgery logic, disabled
encounters, widened X shells, bounce-safe arrivals, and continued
`624 -> 626 -> 625 -> 622` reachability. For the V203 baseline, the focused
campaign-plus-blueprint suite passed 71 tests; adding the title/reset checks
raised that focused total to 77, and the complete repository suite passed 429
tests with no failures, errors, or skips.
The final V205 repository suite passes 447 tests, including the seven pinned
Slot-1 migration checks and all generic disc-state migration regressions.
The final V206 repository suite passes 450 tests / 5,531 subtests.
The final V207 repository suite passes all 451 discovered tests; its focused
campaign, donor, and blueprint set passes 87 tests.

The verified V200 focused campaign tests freeze room identities, state encodings, reciprocal
destinations, entry triangles, held-X spacing, model/header preservation,
dialogue continuity and byte-accurate font layout, exact cross-field physician
and security assets, player-controlled physician walks, distinct held-X-safe
refusal stages, the visible four-actor door entrance, no-Escape security
formation, bounded exterior reveal and dynamic Fei-facing, retail-proven bright
arena resources, victory recovery, connected physician exit route, reverse door
close, two-page locked-exit gating, the bounded-yet-random intake survivors,
exact hopeful waiting-area dialogue and preserved boy line, title reset behavior,
native save and battle opcodes, the relay-earned e22 shortcut and preserved
field-620 opener, both e24/e26 keycard denials and byte-preserved openers,
the victory-only item chime/receipt/flag ordering, field 567's exact static
bed/environment, sole e17 return,
  unreachable NPC/story/battle scripts, disabled encounters, the recovered
field-565 staff route, the active V194 ward donor, reciprocal route bytecode, and the
complete manifest. V197's remaining semantic execution checks cover the
Quarantine-to-e22 unlock,
ordered sorter/core/Meld progression and receipt-before-flag ordering, every
Sufal pending/epilogue/secured recovery path, non-repeatable victory, the
one-shot e12 opening action, torn secured-plus-pending recovery, and continued
control of the completed emergency-return loop. V198 additionally freezes the
runtime-observed legacy failure, all nine exact private OP17 bodies and starts,
complete 24-unit halo coverage over the layer-0 walkmesh, 50-unit pairwise
separation, actor-radius clearance, the open player/doctor aisle, preserved
native random-walk slots, untouched dialogue actions, and the exact turtle-boy
line. V199 additionally freezes the exact transit/solid OP20 bodies, phase-aware
lobby and office initialization, transition ordering before/after every walk,
32-unit collision geometry, roaming-zone clearance, and preserved player
control. V200 additionally freezes field 550's exact walkmesh size and source
hash, triangle-to-material mapping, material-0 and material-1 runtime flags,
every security and doctor route's required movement budget, the exact
actor-local set/clear traversal opcodes, security's exterior-to-deep-interior
override lifetime, the doctor's open/cross/close/hide/clear ordering, the
16-update threshold bounds, and the preserved solid e19 player seal. The base
  v173 tests remain in
  the suite to ensure the campaign layer does not regress the established door
  and animation work. The recorded V200 focused campaign run passed 67 tests
  with 1,771 subtests; the complete V200 repository suite passed 425 tests with 5,278 subtests,
with no failures, errors, or skips. Historically, V196's surface-focused
discovery set passed 136 tests, V195's recorded validation set passed 149, and
V194 passed 133.
