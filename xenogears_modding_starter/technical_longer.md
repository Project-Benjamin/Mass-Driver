Xenogears scripting and scene-planning architecture

Scope

This document explains the scripting systems and authoring method used to
build the Mass Driver scenes. It covers both the formats executed by
*Xenogears* and the project-side planning layer that compiled our scene ideas
into those formats.

The distinction matters:

- **ATEL and the battle-animation VM are game systems.** They are interpreted
  by the original PlayStation executable.
- **The event planners are our build-time system.** They are immutable Python
  declarations, compiler helpers, and validation contracts. No new planner or
  interpreter is installed on the disc.
- **The result is ordinary Xenogears data.** The rebuilt disc contains field
  bundles, dialogue tables, model and sprite archives, encounter records, and
  retail VM bytecode.

This is a reverse-engineered authoring workflow, not an official Square scene
editor and not recovered deleted source. Statements about binary layout are
grounded in the repository parsers and exact donor checks. Behavioral details
are based on retail examples, Noah metadata or executable disassembly, and
runtime tests. Where a conclusion is only an inference, this document says so.

The short version

A Xenogears field scene is not one monolithic script. It is a coordinated set
of resources:

retail donor field + paired graphics + authored dialogue + scene plan
                                  |
                                  v
                 verify donor identities and old values
                                  |
                                  v
        compile plans into ATEL entity routines and resource edits
                                  |
                                  v
       rebuild the field's streams; copy or transform paired graphics
                                  |
                                  v
       validate route, doors, cameras, actors, state, and continuity
                                  |
                                  v
          emit canonical replacements and a provenance manifest
                                  |
                                  v
           rebuild the MODE2 disc and cold-load it in the game
At runtime the original game does the reverse: it loads a field, decompresses
its streams, creates its entities, schedules their ATEL entry points, and lets
those scripts coordinate dialogue, actors, cameras, models, sound, flags,
transitions, and battles.

Reading map

- Sections 1–3 describe the retail field bundle, ATEL, and dialogue formats.
- Sections 4–5 explain the project-side event planners and scene composition.
- Section 6 covers the separate battle/mecha animation VM.
- Sections 7–12 follow compilation, examples, validation, and failure lessons.
- Sections 13–14 provide inspection commands and evidence boundaries.

1. A field is a resource bundle

The packed field bundle contains a header region followed by nine
LZSS-compressed streams. The donor header is either retained or transformed
under exact checks when actor/node data changes. [`xgfield.py`](../tools/xgfield.py)
names the streams as follows:

| Index | Stream | Scene responsibility |
| ---: | --- | --- |
| 0 | `images` | Field-local image and texture data |
| 1 | `walkmesh` | Connected floor triangles and movement height |
| 2 | `models` | Static field geometry and model records |
| 3 | `actors` | Actor definitions and animation data |
| 4 | `sprites` | Sprite graphics, palettes, and frame data |
| 5 | `scripts` | ATEL event bytecode and entity entry table |
| 6 | `encounters` | Random and fixed encounter configuration |
| 7 | `dialogue` | Text blocks and their variable-length offset table |
| 8 | `triggers` | Additional trigger data used by the field |

The header stores the nine decoded sizes beginning at `0x10C` and their
four-byte-aligned packed offsets beginning at `0x130`. `parse_field()` checks
those tables and decompresses every stream. `build_field()` rebuilds the size
and offset tables and repacks the streams.

For the six current rooms with pinned packed templates, `_prepare_clone()`
uses `build_field_preserving()`. It proves that every stream declared unchanged
still decodes to the original bytes, then copies that stream's original
compressed span byte-for-byte. The other current rooms rebuild all nine
decoded streams and prove the result by reparsing it. Both paths make the
declared changes explicit and reject decoded-component drift.

Most scenes also have a paired field-graphics canonical file. Here a
**canonical ID** is the stable replacement number derived from the disc's file
allocation table, not the scene number itself. The build manifest maps target
scenes to the canonical field-bundle and graphics resources that Xenoiso must
replace.

Why retail donors mattered

We did not synthesize complete rooms from empty data. A donor provided a
coherent starting set of:

- walkable floor and collision topology;
- static geometry and textures;
- actor, sprite, and palette layouts;
- camera defaults and field-entry positions;
- useful door, lift, terminal, and animation helpers;
- a valid ATEL entity table and scheduler structure.

The planner then retired unwanted story logic, retargeted the useful
mechanisms, and installed authored events. This was both safer and more
visually consistent with the original game than inventing every resource from
scratch.

2. ATEL: the field-event virtual machine

Stream 5 is the ATEL program for a field. Its relevant top-level layout is:

0x0000..0x007F  fixed ATEL header data
0x0080          u32 entity count
0x0084          entity entry table
                entity_count * 32 little-endian u16 pointers
bytecode base   0x84 + entity_count * 0x40
                shared bytecode addressed by relative PC
Each entity owns 32 script slots, so each entity contributes `0x40` bytes to
the entry table. Pointers are unsigned 16-bit offsets relative to the shared
bytecode base. The bytecode therefore has a hard 65,536-byte address space. In
this guide, **PC** means the VM's bytecode-relative program counter.

Pointer zero has a critical special case: in slots 1–31 it marks an unused
slot, but slot 0 may legitimately point to PC 0. PC 0 is also where the audited
fields place their field-entry `FF` sentinel. A newly zero-extended entity row
is therefore temporary, not a safe inactive entity; its slot 0 must be pointed
at a real initializer or an audited STOP routine before output.

[`xgscript.py`](../tools/xgscript.py) is intentionally a small, lossless
editor rather than a general assembler. It:

- validates every existing entity/script pointer;
- appends an already encoded routine;
- repoints one declared entity slot to that routine; and
- refuses a result outside the 16-bit PC range.

This append-and-repoint strategy is fundamental. Inserting bytes into the
middle of retail bytecode would move later absolute PCs and require relocating
every branch, call, and entry pointer that reaches them. Appending new code
leaves the donor program stable. When an insertion is unavoidable, the builder
uses a specialized relocation routine and verifies every affected target form
that the transform declares and understands.

Entity script-slot conventions

In the audited donor fields, the common convention is:

| Slot | Common role |
| ---: | --- |
| 0 | initializer or one-shot director |
| 1 | resumable/per-frame update |
| 2 | Cross/action interaction |
| 3 | contact or collision interaction |
| 4 and above | helpers, animation routines, and cinematic subroutines |

These are useful conventions, not a universal type signature. A planner must
inspect the selected donor and prove the old pointer/body before assigning a
meaning to a slot.

Directors and updates also have different timing. An initializer can run
before the first rendered frame. Work that must yield across frames—loading a
world map, waiting for movement, or running a multi-step scene—belongs in a
resumable update or action routine. Treating a one-shot initializer like a
coroutine is a reliable way to create hangs or invisible work.

Instruction encoding

ATEL is a compact byte stream:

- a base instruction begins with a one-byte opcode;
- multi-byte operands are normally little-endian;
- `0xFE` prefixes the extended opcode table;
- jumps and calls use 16-bit bytecode-relative PCs;
- some operand types can name a field variable or a literal;
- for the common `S16OrVar`/`U16OrVar` form used by our helpers, a literal is
  encoded with bit 15 set, while an untagged even value names variable storage.

That last rule is operand-specific. Some opcodes carry separate literal flag
bytes, so it should not be applied blindly to an unknown instruction.

The partial reader in [`xgatel.py`](../tools/xgatel.py) imports opcode names,
argument sizes, and flow-breaking metadata from the Noah reverse-engineering
project's opcode-registration definitions. It also handles known
variable-length instructions and follows entry points, branches, and calls to
construct a reachable instruction set. This gives us a checked disassembler
and transition auditor, but it is not proof that every obscure opcode has been
fully characterized.

The variable operands used by the audited fields are even byte addresses into
a `0x400`-word array. Addresses `0x0000` through `0x03FE` are copied to and
from GameState across field loads; `0x0400` through `0x07FE` are field-local
working storage. The reconstruction allocates persistent words and bits
centrally and tests key non-overlap contracts, reducing the risk that unrelated
events silently claim the same state.

Frequently used field operations in this project include:

| Encoding | Project use |
| --- | --- |
| `00` | stop the current routine |
| `01 <pc:u16>` | unconditional jump |
| `02 ... <pc:u16>` | conditional branch; comparison/control form is encoded in the middle operands |
| `05 <pc:u16>` | call a bytecode routine |
| `07 <entity> <script>` | launch another entity script asynchronously in the audited forms |
| `09 <entity> <script>` | run another entity script and block in the audited forms |
| `24 <entity>` / `25 <entity>` | show or hide an entity |
| `26 <frames:imm16>` | wait/yield |
| `31 ...` | test the current frame's held-button state |
| `32 ...` | test accumulated input state |
| `33` | clear accumulated input |
| `3A ...` / `3B ...` | set or clear a variable bit |
| `5B` | permanently retire the current one-shot field update |
| `74 ...` / `75 ...` | play a sound or select music in audited donor forms |
| `98 <field> <param>` | change to another field/entry parameter |
| `D2 <dialogue:u16> 00` | actor-owned choice window |
| `F5 <dialogue:u16> <flags>` | screen-positioned dialogue, useful for hidden directors |
| `9C` | wait for the active dialogue to finish |
| `FE 53` / `FE 54` | restore controls or enter the audited cinematic-control lock |
| `FE xx ...` | extended operation |

The table is an authoring-oriented subset, not a complete opcode reference.
The builder's byte helpers are the source of truth for the exact operand form
used by a generated routine.

Waits, input edges, and softlocks

ATEL is cooperative. A long event must yield so the field, camera, actors, and
input system continue updating.

The retail wait counter has a slightly non-obvious contract. Our helper emits
`WAIT 0` for a true one-scheduler-tick yield; `WAIT 1` spans two scheduler
ticks because the handler tests and then decrements its counter.

Input is similarly stateful. If one Cross press opens an event and the script
immediately opens several windows, that same live edge can dismiss the next
window too. The automatic-dialogue compiler therefore:

1. clears accumulated input;
2. locks field control;
3. loops until Cross is physically released;
4. yields once more to drain the old edge;
5. opens one dialogue at a time with a yield between windows; and
6. explicitly restores control.

This is a good example of why a scene planner needs scheduling rules, not just
a list of desired dialogue lines.

Field-entry records

The start of ATEL bytecode contains an `FF` sentinel followed by seven-byte
field-entry records:

s16 x, s16 z, u8 walkmesh, u8 camera direction, u8 actor direction
The transition parameter chooses one of these arrivals. Adding an entry is
harder than appending an ordinary routine because the entry table sits before
entity 0's first code. `_install_field_entry_additions()` identifies any
routines that would be overwritten, copies them into appended trampolines,
relocates their local absolute branches, repoints their owners, and then writes
the new records.

Every directed route edge also has an `ArrivalContinuity` contract: destination
parameter, position, walkmesh layer, inward-facing actor octant, and a safe
camera octant. This makes a transition a two-room agreement rather than a
single `CHANGE_FIELD` opcode.

3. Dialogue is data, not embedded script text

Stream 7 owns a variable-length offset table and zero-based dialogue blocks.
ATEL instructions refer to block IDs; they do not contain the displayed text.
As a result, a block can change length without moving its ATEL call site, as
long as its ID remains stable.

For `n` blocks, the component begins with `u32 (n - 1)`, followed by `n`
little-endian `u16` payload offsets, then `n` width/height byte pairs, and then
the variable-length encoded payloads. Offsets are strictly increasing and the
complete component must stay within its 16-bit offset space.

[`xgdialog.py`](../tools/xgdialog.py) provides a strict reversible codec. Plain
text uses the game's font encoding, while control bytes use explicit tokens,
including:

<Close> <New> <Wait> <Delay:8> <Elly> <Byte:90>
The lossless byte token prevents an unknown value from being silently erased.
The production builder also accepts a separate authored-scene format:

{
  "format": "xenogears-field-dialogue-authored-v1",
  "reconstruction": true,
  "blocks": [
    {
      "id": 0,
      "width": 42,
      "height": 3,
      "manual_wrap": true,
      "text": "AUTHORIZATION REQUIRED.<Close>"
    }
  ]
}
The `reconstruction` marker distinguishes authored fan material from a retail
text export. This `xenogears-field-dialogue-authored-v1` schema belongs to
`build_mass_driver_dungeon.py`; it is not one of the generic
`xenogears-field-dialogue-v1` or replacement schemas accepted directly by
`xgdialog.py rebuild`. The production builder validates block ordering and
dimensions; blocks declaring `manual_wrap: true` additionally receive exact
page, row, and encoded-font-unit validation. It then rebuilds and reparses the
entire component.

JSON decides **what each block says and how its window is sized**. The Python
scene plan decides **which entity presents it, when it appears, which state
branch selects it, which camera owns the moment, and what happens afterward**.

4. What we call an event planner

There is no `EventPlanner` class and no retail subsystem with that name. In
this project, “event planner” is a convenient name for the build-time layer
formed by:

- immutable event/spec dataclasses;
- route, door, progression, and continuity contracts;
- repeated-room factory functions;
- bytecode emitters and label/fixup helpers; and
- `_install_*` compilers that turn one declaration into ATEL routines and
  resource changes.

The central per-room declaration is `CloneSpec` in
[`build_mass_driver_dungeon.py`](../tools/build_mass_driver_dungeon.py). It
binds together:

- a human-readable role;
- retail donor and target scene numbers;
- source and destination canonical file IDs;
- pinned donor paths, script hashes, and graphics hashes;
- an authored dialogue file;
- checked low-level edits; and
- optional typed scene modules.

The first graybox used a smaller JSON recipe, whole-field cloning, and mostly
size-preserving patches. The production builder kept that donor-first safety
model but moved scene intent into frozen Python dataclasses. That made it
possible to append routines, extend entity tables, transplant verified assets,
express cross-room contracts, and validate a complete route without treating
the binary patch list itself as the design document.

The modules make intent explicit. Representative groups are:

| Planning concern | Example declarations |
| --- | --- |
| Low-level audited edits | `TransitionEdit`, `VariableEdit`, `ByteEdit`, `PointerEdit`, `FieldEntryAddition` |
| Navigation | `BoundaryExit`, `NativeDoorExit`, `StaticDoorExit`, `InterlockedDoorExit`, `HubGate` |
| Interaction/state | `OptionalInteraction`, `InterlockInteraction`, `AuthorizationTerminal`, `CompletionInteraction` |
| Staging/choreography | `AutoScene`, `HistoricalGhostScene`, `HistoricalCameraShot`, `FinalPartyArrival` |
| Battles | `GearBossBattle`, `BossEncounter`, `GoliathFactoryHall`, `DefenseBayScene` |
| Room-specific systems | save points, shops, archive terminals, video events, and minigame hosts |

A schematic declaration makes the separation between intent and emitted bytes
clear:

CloneSpec(
    role="Defense Archive",
    source_field=394,
    target_field=376,
    script_sha256="<audited donor hash>",
    graphics_sha256="<audited donor hash>",
    dialogue_file="field_376_defense_archive.authored.json",
    transitions=(TransitionEdit(...),),
    authorization_terminal=AuthorizationTerminal(...),
    defense_bay_lift_exit=DefenseBayLiftExit(...),
)
The declaration names ownership, prerequisites, and topology. Its installer
emits and validates the ATEL bytes.

`_RoutineBuilder` is a small absolute-PC label and fixup helper. It is useful
for authoring branches, but it is not itself the planner. The planner is the
declaration plus the compiler and its cross-scene contracts.

Compilation is guarded transformation

`_transform_clone_script()` acts as the event compiler/dispatcher:

1. It rejects a donor whose script hash is not the audited identity.
2. It applies exact size-preserving cleanup, variable, transition, and pointer
   edits.
3. It installs entry records and explicit arrival orientation.
4. It invokes only the typed modules declared by that room's `CloneSpec`.
5. Each installer verifies the old pointers, opcodes, actor inventory, or
   helper body that it expects to own.
6. It appends generated routines and repoints only declared entity slots.
7. It emits human-readable notes describing the transformation.
8. Especially sensitive scenes are frozen by exact PCs, bodies, sizes, and
   hashes after compilation.

The governing safety rule is: **every destructive patch is also an
assertion**. A byte edit supplies both the expected old bytes and equal-length
replacement bytes. A variable edit verifies the opcode and old operand. A
pointer edit verifies the old target. If the donor is not exactly what the plan
describes, the build stops instead of guessing.

Persistent state

Scene plans allocate persistent variables and distinct bit masks for separate
facts: authorization accepted, interlocks restored, a boss defeated, a memory
seen, a party member arrived, or completion committed. Field-local scratch is
used for transient donor logic that must not contaminate the save.

Good event state has three properties:

- **separation:** unlocking a door is not the same bit as defeating the battle
  behind it;
- **idempotence:** repeating an interaction either repeats safely or follows an
  explicit “already complete” branch; and
- **commit order:** irreversible state is written only after the required
  animation, dialogue, or battle has actually completed.

5. Building actors, doors, cameras, and scenes

Actors and entity-table alignment

ATEL entity rows, field-header actor/node records, actor archives, and sprite
archives are related but not interchangeable. When a scripted actor is added
before existing static objects, the matching header record and ATEL pointer row
must be inserted at the same logical index. A static model node, by contrast,
can exist without an ATEL entity if it never runs script.

`_extend_atel_entity_table()` inserts zeroed `0x40`-byte rows before bytecode,
which preserves all bytecode-relative PCs. Asset transplant routines validate
archive pointer monotonicity, palette and PlayStation video RAM (VRAM)
destinations, animation/frame metadata, and non-overlap before rebuilding
indexed components.

Interaction controllers

A visible console does not have to be the script owner. Many robust scenes use
three separate concepts:

- a static or sprite-backed visible body;
- a solid-only contact body; and
- a small invisible, front-facing Cross controller.

Separating them avoids oversized interaction boxes and lets one piece of
scenery remain visually authentic while a dedicated entity owns its state
machine. Controller positions are checked against walkmesh triangles and the
visible object's measured bounds.

Doors and lifts

A visible mechanical door is treated as a sequence, not merely a destination:

validate state -> lock control -> play sound -> call model helper
-> bounded party crossing -> exact endpoint snap -> change field
Open passages can use automatic boundary transitions, but a visibly closed
door should not teleport the party without playing its donor mechanism.
Finite walks and exact endpoint snaps prevent rounding or collision from
leaving a child routine alive forever.

Cameras

`HistoricalCameraShot` declares target, eye, transition duration, and the
dialogue beats owned by that composition. The field-camera operands use the
game's observed `(x, z, y)` order, not the more familiar `(x, y, z)` order.

The camera compiler uses a retail fixed-camera envelope to capture current
vectors, install target/eye tracks, configure interpolation, and begin the
move. Returning to party tracking is explicit. Every camera shot must be
validated in the actual donor room: coordinates copied from a different arena
can point through a wall even when the bytecode is perfectly valid.

A scene as a finite state machine

A useful way to read a generated event is:

idle/available
  -> check persistent prerequisites
  -> locked/already-complete/active branch
  -> drain input and lock player control
  -> stage actors and camera
  -> dialogue/movement/mechanism/battle beats
  -> wait for every blocking child to terminate
  -> commit state
  -> clean transient actors/tracks/camera
  -> restore control or transition
This model catches more bugs than thinking in terms of a linear cutscene.
Every branch, interrupt, repeat interaction, and field reload needs a defined
state.

A small generated interaction

This tested routine sets zero-based bit index 1 (mask `0x0002`) in persistent
word `0x03FE`, then safely shows dialogue block 2:

3A FE 03 01 00 40
33 FE 54
31 20 00 16 00
26 01 80
01 0B 00
26 01 80
F5 02 00 00
9C
FE 53
00
Its planner-level meaning is easier to read:

persistent_word_at(0x03FE) |= 0x0002
clear_accumulated_input()
lock_player_control()

while Cross_is_held:
    yield()

yield()                         # drain the activating edge
show_screen_dialogue(block=2)
wait_for_dialogue()
restore_player_control()
stop()                          # this action remains repeatable
The progression bit is deliberately committed before the optional prose. A
later dialogue rewrite cannot accidentally make the interlock unobtainable.

6. The battle/mecha animation VM

Battle actions do not use field ATEL. Gear attacks are driven by a separate,
word-oriented animation VM stored in nested battle archives. An attack record
selects an animation ID and supplies gameplay properties such as power and
fuel cost; the selected local animation can in turn launch an external
animation program from another resource.

The relevant archive pattern in this project is:

outer archive header and roots
  -> main animation archive
       entry 0: shared keyframe archive
       entry 1: local animation 0
       ...
       entry N: local animation N-1
  -> resource-specific secondary/model or sound region
Because entries may alias the same return stub, a program is bounded by its
pointer and the next strictly greater non-zero pointer. The El-Regulus patchers
verify each resource's audited count and roots, permitted aliases, individual
entry bounds, four-byte alignment, secondary-region boundary, exact output
size/hash, and, where applicable, sector capacity.

Animation IDs below `0x50` index the owner's local animation table. Once the
loader has mounted an external archive, IDs at or above `0x50` index it as
`animation_id - 0x50 + 1`. Keyframe selectors have a related but different
context rule: selectors below `0x40` use the local keyframe table, selectors at
or above `0x40` use the secondary/external table, and `FE`/`FF` select
owner-context defaults. This is why an apparently valid donor frame ID can
animate the wrong skeleton when copied to another Gear.

The attack record and the animation program also have separate jobs. The
audited attack records are `0x28` bytes; animation ID is the signed word at
`+0x02`, power is the byte at `+0x11`, and fuel cost is the word at `+0x24`.
Those values drive game mechanics. The animation VM owns presentation, timing,
the point at which the precomputed result is dispatched, and the completion
protocol.

Two layers of animation

For AERODs, the attack record selects El-Regulus animation 72 (`0x48`). That
local program runs the checked external-resource loader for canonical resource
3175, then launches external animation `0x6A`. The external program coordinates:

- model resets and a hidden Aerod gate;
- absolute seed rotations/translations for the detached pod bones;
- a deliberate scheduler tick so dirty bone matrices were composed before
  cloning;
- an El-Regulus-local owner pose;
- twelve child trajectory programs;
- launch, audio, impact, and the single damage dispatch;
- pod hide/cleanup; and
- direct completion back to the battle controller.

This split is important. The field planner can start a fixed battle, but the
battle animation itself must be authored in the battle VM and associated
resources.

The action lifecycle is approximately:

attack record selects local animation
  -> local VM performs setup and starts/polls the external load
  -> local opcode 14 launches external program 0x6A
  -> external main seeds bones and yields one update
  -> owner pose and twelve clone-child trajectories run
  -> retained effects/audio and one damage dispatch run
  -> children and visibility are cleaned
  -> recovery and damage/display settlement finish
  -> opcode 02 publishes completion to the battle controller
  -> turn controller releases the lazy external resource when safe
Common battle-animation operations used here

The battle VM reads a 16-bit command word. The low byte selects the opcode and
the high byte often acts as a mode or flags byte. Operands follow as additional
little-endian words. In the audited AERODs work, the significant operations
included:

| Opcode | Audited role |
| ---: | --- |
| `00` | terminal self-loop/end marker; it pins the VM at the current PC and does not itself signal battle completion; `77 77` is unreachable alignment padding |
| `01` | timed wait; holds at the opcode until the runtime elapsed counter passes the following word |
| `02` | publish animation completion to the battle controller |
| `04` / `05` | begin and poll/finalize a lazy external-animation resource load |
| `06` | release the loaded external resource; it is not a generic action cleanup |
| `07` / `6C` | CD/load synchronization used by the local loader |
| `08` / `0A` | release all animation tracks, or tracks selected by the command's high-byte mask |
| `0C` | zero root rotation/translation velocity and acceleration |
| `0F` | tear down/reset a scripted camera envelope; it is **not** a no-op |
| `11` | install/play authored keyframe tracks |
| `13` | interpolate the model toward a keyframe |
| `14` | launch another animation; the complete `14 FD FD 6A 00 00` instruction launches external AERODs animation `0x6A` |
| `15` | allocate/deep-copy a mecha clone, attach a selected bone subtree, and launch a child program |
| `16 FF` | complete/remove an external clone child |
| `1D` | trajectory-controller packet used by donor child programs; detailed subfields remain only partly characterized |
| `21` | animation-track synchronization barrier that may retain the PC and yield until the required track state is reached |
| `23` | show or hide a bone; the high byte selects mode, including recursive hide |
| `2F` | wait for attack-side work to settle before completion |
| `3F` | dispatch the attack's damage event |
| `43` | face the current target-position vector horizontally |
| `4A` | snap root X/Z to a selected battle entity |
| `48` | set an audited VM/mecha mode byte; stronger semantics are not claimed |
| `58` | reset movement interpolation |
| `60` | derive a target position from the formation/slot midpoint |
| `62` | edit bone rotation, translation, or scale; mode also supports audited additive/recursive forms |
| `63` | register one asynchronous event payload, used for sound/effect packets |
| `65`–`68` | camera-envelope construction/initialization family |
| `6D` | write the mecha animation active/completion flag from the command's high byte; `6D 00` clears it in the battle-entry handshake |

This is a narrow, evidence-backed subset. Other opcodes handle camera tracks,
effects, sound, formation targets, and motion. They should be copied or edited
only after their packet length and control-flow behavior are proven.

Opcode `63` deserves special caution: the audited implementation exposes one
continuation/payload slot. Two packets emitted without an intervening yield can
overwrite each other. The same general rule applies throughout the VM: packet
boundaries and scheduling behavior matter as much as opcode names.

Why model topology matters

An animation does not carry all of its visible geometry. Retail Vierge AERODs
referenced Vierge bones `0x30`–`0x37` and `0x40`–`0x43`. El-Regulus had a
different skeleton and fewer compatible visible parts. Copying the bytecode
alone therefore produced effects without readable Aerod bodies—or worse,
addressed the wrong body parts.

The working implementation added an authentic pod geometry block, texture
strip, a hidden gate bone, and twelve direct pod bones to El-Regulus's model
archive. The external programs cloned each selected subtree and remapped the
retail trajectory selectors to the new bone IDs.

The original Vierge pods inherited transforms through multi-bone parent
chains. The new direct children did not. Their starting poses were collapsed
relative to El-Regulus runtime bone `0x01`, then written as absolute local
rotation and translation values before cloning. A one-tick hidden settle then
allowed the model updater to compose the matrices before any pod became
visible.

That settle follows from the actual update order: the engine composes matrices,
updates existing tracks, and only then runs more animation bytecode. An
opcode-`62` seed dirties a bone too late for an opcode-`15` clone executed in
the same pass. Yielding once while the visibility gate remains hidden makes the
composed pose available to every child without a startup flash.

Owner motion and cameras are separate choreography

Copying Vierge's owner keyframes onto El-Regulus was unsafe because keyframes
are skeleton-specific. The accepted action instead used El-Regulus's own local
keyframes inside the same retail-style play/interpolate/wait envelope. That
gave Elly a restrained launch pose without invoking an unrelated beam or
deathblow animation.

The transplanted Vierge camera packets were not portable to the
El-Regulus/Guardian setup: at runtime they framed a wall and cut the target out
of the impact. The final program structurally removes the audited camera-only
spans from the main program and the two camera-owning child trajectories,
leaving the normal encounter camera in control and keeping El-Regulus and the
Guardian framed through launch and impact.

Completion is a protocol

“The animation bytes reached their end” is not enough. The battle controller
waits for an explicit completion signal. One rejected version handed off
through the local cleanup path before the external main published direct
completion. Runtime memory inspection and executable analysis then diagnosed
a null controller pointer after fuel had been spent, with the battle still
executing.

The corrected main preserves enough timeline for every child envelope to
finish, restores the owner, waits for attack-side damage/display settlement,
and executes opcode `02` while the controller pointer is still valid. Runtime
acceptance then checks all of the following:

- one fuel charge;
- one damage event;
- normal command-menu return;
- no live child slots;
- owner PC and wait state returned to idle;
- battle controller cleared to `0`, completion signal asserted at `1`, and
  battle execution state `m2DB` returned to `0`; and
- a second use succeeds after another turn.

This is the battle-VM equivalent of restoring field control after an ATEL
cutscene.

7. From a plan to a playable field

`_prepare_clone()` is the complete field compiler. In simplified order it:

1. Loads the donor header and nine decoded streams.
2. Verifies donor script, graphics, and any specialized asset identities.
3. Applies requested actor, sprite, model, header, VRAM, and walkmesh changes.
4. Calls `_transform_clone_script()` to compile the event plan.
5. Neutralizes a declared ATEL encounter initializer and/or installs a fixed
   encounter record as declared.
6. Compiles the dialogue component.
7. Rebuilds the packed field, preserving unchanged packed streams where
   possible.
8. Reparses the result and compares every decoded component.
9. Enforces practical field-loader and special-room size budgets.
10. Returns an immutable `PreparedReplacement` with notes and identities.

`prepare_all()` combines every field clone with global resources such as
world-map data, overlays, GameState, menus, battle models, battle animations,
and combat balance. It rejects duplicate canonical replacement IDs.

`materialize()` writes inspectable clone directories, packed replacement
files, and a manifest containing canonical IDs, filenames, sizes, hashes,
script/dialogue identities, and transformation notes. The manifest's identity
records are build provenance; it is not itself the complete on-disc FAT. Its
narrative subfields are descriptive, while the frozen builder transformations
and tests remain the executable specification.

For the field directory used here, the bundle's local file number is
`0xB8 + 2 * scene`, and the paired graphics file follows it. The disc parser
then resolves `FAT index = directory_first_file + local_file - 2` and uses
`canonical ID = FAT index + 5` for the Disc 2 replacement mapping. Keeping
**scene ID**, **directory-local file number**, **FAT index**, and **canonical
replacement ID** distinct prevents a valid resource from being written to the
wrong slot.

Xenoiso consumes the canonical-ID mapping, rebuilds physical allocation and
filesystem references as necessary, and writes a raw-sector PlayStation
MODE2/2352 disc image. Separate disc tools then re-extract final payloads,
check FAT/layout deltas, validate the sectors' error-detection and
error-correction data (EDC/ECC), and verify the native boot sector.

8. Worked example: the Central Control finale

Central Control is a useful example because it combines most of the system.

Plan

Its `CloneSpec` chooses a coherent retail archive-control room, pins the donor
script and graphics, assigns a new target field and canonical resources, and
links an authored dialogue document.

Low-level edits retarget the return door, retire unrelated story and treasure
logic, and isolate standalone variables. Typed declarations then describe:

- a broad invisible completion-console controller;
- prerequisite, already-complete, and commit state;
- two visible officer apparitions plus a hidden Miang point-of-view/spatial
  anchor, with their native asset donors;
- per-dialogue facing cues;
- reaction, apparition, present-day, arrival, and final camera shots;
- fades, sound, transparency, and color grading;
- Citan's hidden staging point, native-door entrance, bounded waypoints,
  conversation facing, and terminal-operation helper; and
- the final launch handoff.

Asset preparation

The compiler installs verified actor and sprite banks for the historical cast,
updates matching header records and VRAM mappings, and imports a genuine
standing keypad as a static model. The keypad's visible model, solid collider,
repeatable observation controller, and finale controller remain separate
owners.

ATEL compilation

The scene compiler:

1. extends the entity table;
2. emits hidden, non-solid apparition initializers;
3. reserves independent stage, walk, and terminal-operation slots for Citan;
4. drains input and locks control;
5. runs present-day dialogue;
6. hides the party, keeps the Miang anchor hidden, and reveals the two officers
   under fixed cameras;
7. advances camera/facing/dialogue beats;
8. fades and cleans the apparitions;
9. restores the party and present-day camera;
10. runs Citan's bounded entrance and finite terminal performance;
11. commits progression; and
12. enters the retail Mass Driver launch flow.

Every new body is appended and repointed to an explicit owner. Sensitive
routines and asset identities are frozen after transformation. The route,
return door, arrivals, walkmesh positions, camera ownership, dialogue calls,
and persistent-state order are all checked before the canonical files are
emitted.

The key result is that we did not invent a new cutscene format. We described a
scene as checked build-time data and compiled it into the retail field VM while
reusing authenticated retail spatial, visual, and behavioral resources.

9. Worked example: authorization and the Guardian handoff

The Defense Archive and Goliath Factory show how multiple fields cooperate.

The authorization planner assigns one architectural terminal a five-step code
flow and a persistent authorization bit. The north lift owns a separate
prerequisite check and locked response. Its transition enters a factory hall
whose planner parks El-Regulus and Crescens, detects the party's bounded
approach, stages boarding, selects the battle music, and invokes one fixed
Guardian encounter.

The responsibilities remain separated:

- dialogue component: prompts, clues, accepted/locked/victory text;
- field ATEL: terminal state machine, door/lift mechanism, party movement,
  boarding, and fixed-battle handoff;
- encounter data: Guardian formation and no-escape policy;
- battle attack tables: power, fuel, animation ID;
- battle model/animation/external archives: El-Regulus and AERODs visuals;
- persistent state: authorization and boss-defeated bits;
- field reload: post-battle actor state and onward navigation.

This division explains why a scene can be field-correct but battle-wrong, or
why a visually complete attack can still softlock its caller. Each layer has
its own completion protocol.

10. Validation layers

The build treats validation as part of authoring, not a release afterthought.

Source and patch checks

- Pin donor size and SHA-256.
- Verify old bytes, opcodes, pointers, IDs, and bounds before editing.
- Require equal lengths for in-place patches.
- Prove appended PCs stay within `0xFFFF`.
- Reparse every changed archive and prove untouched entries are byte-identical.

Field checks

- Reparse all nine streams after packing.
- Prove header/entity/model indexes remain aligned.
- Check actor, sprite, palette, texture, and VRAM ownership.
- Check controller positions against walkmesh and visible object bounds.
- Enforce field loader budgets.

Cross-scene checks

Before materialization, `build_dungeon()` runs:

1. route-transition verification;
2. visible-door contract verification;
3. save-point visual/ownership verification;
4. control and archive-terminal role verification; and
5. scene-continuity verification.

The route checker rejects both missing successors and retained off-route
transitions. Arrival checks ensure unique parameters and explicit inward actor
and safe camera directions. Door checks ensure a visible door has the expected
helper, sound, bounded movement, and reciprocal destination.

Disc checks

- Build twice from fresh paths and compare outputs.
- Extract every declared replacement from each final disc.
- Compare FAT descriptors and all relocated payloads.
- Validate MODE2/Form1 EDC/ECC.
- Verify the native publisher/title boot sector.

Runtime checks

- Cold-load from a field/prebattle state that contains none of the edited
  resident resources.
- Confirm the emulator log names the intended CUE and BIN.
- Test real entry, interaction, camera, dialogue, battle, return, and reload.
- Exercise repeat paths, not just the first successful use.
- Inspect state read-only when useful, but treat visible gameplay and normal
  control return as required evidence.

Savestates can restore old mounted media, resident fields, models, and external
animation programs. A static hash match or an in-battle savestate is therefore
not proof that a new disc supplied the behavior being observed.

11. Practical recipe for authoring another scene

1. **Choose a coherent retail donor.** Prefer a room whose geometry,
   walkmesh, actor capacity, camera defaults, and native mechanisms already
   resemble the desired scene.
2. **Unpack and inventory it.** Record bundle/graphics identities, entity
   count, all active script slots, reachable transitions, dialogue IDs,
   models, actors, sprites, encounters, and field entries.
3. **Define the target topology.** Add the route edge and reciprocal arrival
   contract before writing the event.
4. **Allocate state deliberately.** Separate persistent facts from scratch
   variables and reserve distinct bits for distinct facts.
5. **Write dialogue as stable blocks.** Keep IDs explicit and validate actual
   encoded wrapping.
6. **Declare a `CloneSpec`.** Pin the donor and add only the required typed
   modules and checked edits.
7. **Compile small finite routines.** Drain input, yield across frames, bound
   movement, terminate child helpers, clean temporary state, and restore
   control.
8. **Prepare matching assets.** Keep ATEL rows, header records, actor/sprite
   indexes, models, palette uploads, and VRAM regions synchronized.
9. **Freeze sensitive output.** Assert important routine bodies, pointers,
   sizes, hashes, and unchanged source entries.
10. **Run field and cross-field validators.** Do not proceed while topology,
    door, camera, or continuity contracts disagree.
11. **Build and audit final media.** Re-extract from the disc instead of
    trusting staging alone.
12. **Cold-play both first and repeat paths.** A scene is complete only when
    control, state, and resources remain correct after it has already run.

12. Common failure modes and what they taught us

| Failure | Cause | Authoring rule |
| --- | --- | --- |
| Dialogue advances or disappears immediately | Triggering Cross edge remains live | Drain release state and yield between windows |
| Field loads but actor is missing or wrong | ATEL, header, actor, and sprite indexes disagree | Treat entity/resource insertion as one transaction |
| Door teleports or traps the party | Destination patched without preserving/bounding mechanism helpers | Plan the full door sequence and reciprocal arrival |
| Scene hangs after movement | Blocking child never terminates or endpoint is unreachable | Use bounded motion, exact snap, and checked termination |
| Cutscene camera points into scenery | Camera coordinates transplanted from incompatible staging | Validate shots in the target room with final actor positions |
| Attack effects appear without objects | Bytecode references model-specific bones that do not exist on the new owner | Port model topology and remap selectors, not just effects |
| Battle spends fuel and never returns | Completion callback runs after its controller was destroyed | Treat cleanup and completion as an ordered protocol |
| Second use fails even though first use worked | Residual state, input ambiguity, or incomplete cleanup was never exercised | Make repeat-use runtime QA an acceptance gate |
| New build appears unchanged | Savestate restored old media or resident resources | Cold-load before edited resources enter RAM |

13. Inspection workflow

The small format tools can be used independently of the production builder:

Split a packed field into its header and nine decoded streams.
python tools/xgfield.py unpack FIELD.BIN unpacked_field

Show entities and declared entry points (including valid slot-0 PC 0).
python tools/xgatel.py inspect unpacked_field/05_scripts.bin

Decode from a known PC using Noah's opcode-registration metadata.
$noahMetadata = 'C:\path\to\NoahLib\field\fieldDebugger\atelOpcodes.cpp'
python tools/xgatel.py disassemble unpacked_field/05_scripts.bin `
  --metadata $noahMetadata `
  --start 0x0456 --count 20

List field transitions and whether the reachable decoder proved them.
python tools/xgatel.py transitions unpacked_field/05_scripts.bin `
  --metadata $noahMetadata

Export the dialogue blocks to a reversible JSON representation.
python tools/xgdialog.py dump unpacked_field/07_dialogue.bin dialogue.json
Adjust `$noahMetadata` to the local Noah checkout. `xgatel.py` hardcodes the
dynamic lengths of the variable base opcodes `02`, `10`, and `57`, plus
extended forms `FE 27`, `FE 5C`, and `FE 77`. The transitions/reachability
command reports unknown instructions as decoder warnings; direct disassembly
stops at an unknown instruction. Its raw transition scan is useful discovery
evidence, but a matching byte pattern is not by itself proof that the byte is
reachable code; the route validator separately checks the declared scene
graph.

14. Confirmed facts and interpretation boundaries

Confirmed by the repository parsers, exact emitted bytes, tests, and accepted
runtime behavior:

- the nine-stream field layout and LZSS framing;
- the ATEL entity count, 32-entry pointer rows, bytecode-relative PC model,
  and 16-bit address limit;
- the dialogue component layout and codec;
- the precise instruction sequences emitted by the project's helpers;
- the project's state allocation, route, door, camera, and scene contracts;
- the checked behavior of the specific retail donors used here; and
- the battle-resource and completion behavior exercised by accepted AERODs
  runtime tests.

Reverse-engineered or context-dependent:

- opcode names come from Noah/decompilation metadata and are descriptive, not
  original Square documentation;
- the common entity-slot roles are strong donor conventions, not types stored
  in ATEL;
- camera, scheduler, interaction-volume, and several control-byte meanings
  combine donor comparison, executable analysis, and runtime probes;
- the first `0x80` bytes of ATEL remain opaque to the focused tools;
- `xgatel.py` is a partial disassembler, not a complete decompiler; and
- battle opcode descriptions in this guide cover the audited attack paths,
  not the entire battle overlay.

The method succeeded without pretending those unknowns were solved. We used
retail scenes as executable templates, represented new intent with typed
plans, emitted only instruction forms that had been audited, and surrounded
every edit with structural, cross-scene, disc, and runtime validation.

Source map

- [`tools/xgfield.py`](../tools/xgfield.py): field bundle and LZSS parser/rebuilder.
- [`tools/xgscript.py`](../tools/xgscript.py): bounds-checked ATEL append/repoint editor.
- [`tools/xgatel.py`](../tools/xgatel.py): partial metadata-driven disassembler, reachability analysis, and transition patching.
- [`tools/xgdialog.py`](../tools/xgdialog.py): dialogue codec and deterministic block rebuilding.
- [`tools/build_mass_driver_dungeon.py`](../tools/build_mass_driver_dungeon.py): declarative scene catalog, event compilers, asset transforms, validators, battle-resource patches, and manifest production.
- [`tools/xgdisc.py`](../tools/xgdisc.py): canonical file/FAT parsing and final-disc extraction.
- [`docs/graybox-v0.1.md`](graybox-v0.1.md): the initial three-room proof of the method.
- [`docs/vertical-slice.md`](vertical-slice.md): route and donor architecture of the first standalone slice.

The builder and tests remain the executable specification. This document is
the conceptual map for reading them and for extending the scene system without
losing the invariants that made the final game data reliable.
