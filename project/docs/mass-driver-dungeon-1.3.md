# Mass Driver Dungeon 1.3 — v14 Objective Loop

## Status and scope

Version 14 turns the accepted v13 structure into a complete standalone
objective dungeon. It preserves the approved 16-field route, reciprocal
doors, arrival facings, native inclined-lift sequence, two approach tunnels,
stationary subway, and Central Control return path. The v13 structure notes
remain in `mass-driver-dungeon-1.2.md` as the historical baseline.

The standalone image still cold-boots to the playable world map outside the
retail Mass Driver landmark. It does not play a story scene, require a save,
replace Taura/Torah's House, or modify the retail story progression.

The v14 player goal is:

> Restore the abandoned Zeboim Mass Driver, recover its wartime launch
> authorization, clear the launch tube in El-Regulus, and use the old payload
> system to launch Taura's nanomachine capsule.

The launch is deliberately not a nuclear strike. The facility records explain
how its payload system was used during the Zeboim nuclear war; Elly and the
party instead use that surviving infrastructure for Taura's capsule and the
retail goal of breaking the Limiter seal on humankind.

## Content boundary

All facility rooms, doors, consoles, lift machinery, archives, and launch
infrastructure remain Disc 1 Zeboim/Ethos Dig Site technology. Lighthouse
resources are limited to:

- the two underground approach tunnels;
- the abandoned employee subway platform;
- two retail Griffon enemies used as creatures occupying the launch tube.

No Solaris, Krelian, or Anima Relic room or facility technology is introduced.
El-Regulus is an explicit exception only as temporary guest equipment: Citan has
it delivered from Shevat for Elly's launch-tube battle. It is not discovered,
built, or represented as native Mass Driver technology.

## Preserved route

```text
world map -> 729 <-> 364 <-> 360 <-> 720 <-> 721
                                                |
                                                v
                              363 <-> 362 <-> 727
                                             /   \
                            361 <-> 372 <-> 723   387 <-> 725
                                    |        \     /
                                   722        726
                                               |
                                              728
                                               |
                                           world map
```

Target 726 is reached from both the sealed stair connector and the magnetic
conduit path. Target 728 remains backtrackable through its visible entity-14
door; the separate entity-13 console owns the completed launch and outside
return.

## Persistent objective state

The builder stores the objective state in persistent field variable `0x03FE`.
Each action is idempotent, so rereading a record or reactivating a switch is
safe.

| Bit | State | Field and interaction |
|---:|---|---|
| 0 | Auxiliary interlock active | 361, visible controls 13 or 16 |
| 1 | Accelerator-rail interlock active | 725, visible control 16 |
| 2 | Directive record recovered | 361, record entity 12 |
| 3 | Address record recovered | 722, record entity 15 |
| 4 | Launch authorization accepted | 722, terminal entity 14 |
| 5 | Launch-tube boss defeated | 726, central door entity 14 |
| 6 | Capsule launch completed | 728, console entity 13 |

The auxiliary switch is intentionally available on two visible donor props.
Both set bit 0 and play the same activation feedback. This preserves the room
while preventing the required objective from depending on one exact camera
angle or interaction volume.

## Objective sequence

### 1. Recover Directive 0320

The guidance archive in target 361 explains that reserve Mass Driver guidance
was placed under Directive 0320 when civil command failed. Reading it sets
bit 2.

### 2. Restore auxiliary power

Either visible auxiliary control in target 361 sets bit 0 and plays the
audited control sound. The original baked trigger has a slightly widened
interaction box; the second visible prop duplicates the same persistent
control.

### 3. Recover the four-point authority code

The maintenance record in target 722 supplies:

```text
A-2  B-5  C-8  D-4
```

Reading it sets bit 3. The record distinguishes payload guidance from warhead
handling and lets the exposition live in an inspectable facility artifact
rather than a party lecture.

### 4. Enter the authorization

Target 722's nearby entity-14 terminal first requires both recovered records.
It then asks the player to select:

- Directive `0320`;
- address set `A-2 / B-5 / C-8 / D-4`.

Each menu has decoy answers. A wrong answer displays a rejection and leaves
the records intact. The correct pair sets bit 4. Reusing the authorized
terminal reports its existing state instead of replaying the puzzle.

### 5. Restore the accelerator rail

Target 725's visible entity-16 control sets bit 1 and plays its native
activation feedback.

### 6. Open the three-condition gate

Target 726's central entity-14 mechanical door requires bits 0, 1, and 4. It
reports the missing condition separately:

- auxiliary power interlock;
- accelerator-rail interlock;
- launch authorization.

When all three are present, the door performs its native sound, helper
animation, and movement before the first-clear scene. Later uses take the
ordinary animated door path because the boss-completion bit is already set.

## Elly's El-Regulus boss encounter

On the first authorized opening, Citan joins and explains that Shevat brought
El-Regulus to the service bay. Emeralda and Citan remain outside the narrow
launch tube, giving Elly a solo playable Gear encounter.

The encounter contract is:

- field: target 726;
- fixed battle configuration: 15;
- Elly's temporary Gear: El-Regulus, Gear ID 10;
- opponents: two retail Lighthouse Griffons;
- Escape: disabled by the formation flag;
- return mode: same field;
- post-battle synchronization: the retail Gear-battle return path;
- cleanup: restore Elly to Vierge, Gear ID 2, restore Emeralda and Citan's
  frame masks, then set bit 5.

The opponent formation is copied from the audited Lighthouse encounter donor
and installed only in unused formation slot 15. Random encounter weight stays
zero, so the Griffons cannot appear as a roaming battle elsewhere in the
dungeon.

Victory dialogue occurs back in target 726. The already-open route then enters
Central Control. Subsequent approaches skip the boss and use the normal
reciprocal mechanical door.

## Central Control and completion

Target 728 contains Zeboim nuclear-war archive material and Taura capsule
preparation records. Elly interprets the evidence while Emeralda and Citan
respond briefly; the historical facts remain attached to consoles and logs.

The entity-13 console requires bit 5. Before the boss, it reports that the
launch tube must be cleared. Afterward it:

1. secures Taura's nanomachine capsule;
2. accepts Directive 0320;
3. charges the accelerator;
4. launches the capsule;
5. sets bit 6;
6. returns the party to the world map outside the Mass Driver.

The visible entity-14 room door remains an ordinary animated backtrack route
to target 726 and never performs the completion action.

## Build

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v14_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v14.bin
```

The release CUE is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v14.cue
```

Do not record a v14 BIN hash until the final image has been rebuilt and both
the automated and runtime acceptance checks pass.

## Acceptance contract

Automated validation must cover the preserved v13 traversal contract plus:

- both visible auxiliary controls setting the same persistent bit;
- the Directive and address records setting distinct bits;
- both authorization menus, correct and incorrect branches;
- three distinct missing-condition branches at the Central Control door;
- exact formation-15 Griffon bytes, zero random weight, and no Escape;
- Citan joining before the scene;
- solo El-Regulus assignment and fixed same-field battle;
- post-battle synchronization, Vierge restoration, companion restoration,
  and boss-completion bit;
- Central Control console gating, capsule launch bit, and outside return.

Focused runtime acceptance should verify:

1. A clean boot appears outside the retail Mass Driver.
2. The full inclined lift completes both halves and stops its motor at the
   native lower landing.
3. Exactly two tunnels precede the stationary subway; the existing container
   displays rail-safety rules and awards no item.
4. Every visible mechanical door still opens with X, plays its native
   sound/animation, and receives the party facing away from the door.
5. The required record and switch in target 361 are easy to see and operate.
6. A deliberately wrong terminal answer in target 722 is rejected; `0320`
   and `A-2 / B-5 / C-8 / D-4` succeed.
7. The central door identifies each missing objective and opens only when all
   three conditions are satisfied.
8. Citan appears, Elly alone enters El-Regulus, Escape is unavailable, and the
   two-Griffon battle is playable to completion.
9. Victory returns to target 726 without a crash, lingering motor/battle
   sound, hidden companion, or wrong Gear assignment.
10. Central Control remains backtrackable, and the separate console launches
    Taura's capsule before returning outside.
