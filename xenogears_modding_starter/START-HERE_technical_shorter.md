Xenogears field modding: scripting and scene planning

A beginner-friendly explanation of how the pieces fit together

This document explains the practical side of making a new Xenogears field scene. It covers the parts that have to agree with one another: the room, its actors, the event scripts, dialogue, doors, flags, and the disc image.

It is not an official Square development document. The original source code is not available. Some details are confirmed directly by the files, while others come from comparing retail scenes, studying community research and Noah metadata, reading disassembly, and testing changes in DuckStation.

The short version

Xenogears already has the engine needed to run a new scene. It can:

- load a room
- draw models and sprites
- move actors
- detect collision
- respond to the Cross button
- display dialogue
- move the camera
- open doors and lifts
- start battles
- remember progress with flags
- transfer the player to another field

A mod supplies new data for those existing systems.

For example, a new terminal scene does not need a new dialogue renderer. It needs:

1. A visible terminal, or a donor object that can be used as one.
2. A controller that detects the player pressing Cross (or emulated to Cross).
3. A dialogue entry.
4. An event routine that calls the dialogue.
5. A flag that records whether the terminal was used.
6. A door or lift routine that checks that flag.

The original executable runs all of it.

The tools in this starter project are build-time tools.

The Python files in the tools folder are not copied into the game. They are more like a compiler and a set of inspection utilities.

They read the original binary resources, make controlled changes, and write the result back in the format the retail executable expects.

A useful way to think about it is:

    human scene plan
            |
            v
    Python build tools
            |
            v
    Xenogears field data and bytecode
            |
            v
    original PlayStation executable

The game never sees a Python function such as show_dialogue(35). It sees the numeric ATEL instructions that the helper generated.

What a field contains

A field is a packed bundle of nine compressed streams. It is not one large script.

The streams are:

0. Images and field-local textures
1. Walkmesh, floor triangles, and movement height
2. Static models and field geometry
3. Actor definitions and animation data
4. Sprites, palettes, and frames
5. ATEL event scripts
6. Encounter data
7. Dialogue
8. Triggers

The header stores the decoded size of each stream and the packed location where each stream begins. xgfield.py reads this header, decompresses the streams, and can build the bundle again.

This is why a small visible change can involve several files. Adding an object may require an actor record, graphics, a position, collision, and a script. Changing a line of dialogue normally affects only stream 7.

Example: what happens when the player uses a terminal

    Field data:
      - terminal model in the model or actor streams
      - terminal position in the actor data
      - interaction pointer in the script stream
      - text in the dialogue stream
      - completion flag in the scene plan

    At runtime:
      - player walks near the terminal
      - controller notices Cross
      - ATEL calls dialogue block 35
      - player closes the dialogue
      - ATEL sets the completion flag
      - the lift checks the flag and opens

Start with a "donor" field.

A donor is a working retail field that provides the starting point for a new scene.

Creating a room from nothing means solving the floor, camera, graphics, actors, entry points, event scheduler, and resource layout all at once. Reusing a donor lets you change one thing at a time.

A good donor might already contain:

- the floor shape you need
- a useful camera angle
- an actor or sprite with the right animation
- a door or lift
- a terminal or other interaction
- a field-entry position
- an event routine close to the behavior you want

For example, if you want a locked elevator, it is safer to start with a retail field that already has an elevator and change its destination and flag logic than to invent a new elevator system.

Before editing a donor, record:

    field number
    source file path
    file size
    SHA-256 hash
    paired graphics file, if any

The build should check these values before modifying anything. If the source file is not exactly the expected donor, stop the build. This avoids accidentally applying offsets from one version of a field to another version.

Unpack and inspect before changing anything

Use xgfield.py to parse and extract the field. The normal sequence is:

    parse the original field
    extract its streams into a work directory
    inspect the actors, scripts, dialogue, and triggers
    make one small change
    rebuild the field
    parse the rebuilt field again

Never edit the compressed bytes by hand. Work with decoded streams and let the builder recreate the compressed bundle.

The second parse is not optional. It catches broken stream sizes, offsets, compression output, and headers before you spend time testing a bad image in the emulator.

A good first experiment is a no-change rebuild. If an untouched donor cannot be extracted, rebuilt, reparsed, and loaded, fix that process before adding a new scene.

ATEL: the field event system

The field script stream contains ATEL bytecode. ATEL is the small event virtual machine used by the original game for field behavior.

A field begins with a header, followed by an entity count and an entity entry table. Each entity has 32 script slots. The slots point into one shared bytecode area.

The pointers are 16-bit values relative to the start of the bytecode. This gives the script area a maximum address range of 0x0000 through 0xFFFF. A large scene can run out of space even when the disc still has room for other data.

The slots often follow this pattern:

    slot 0       initialization or one-time director
    slot 1       repeating or resumable update
    slot 2       Cross-button interaction
    slot 3       contact or collision behavior
    slot 4+      helper, animation, or cinematic routines

This is a pattern seen in the examined fields, not a guarantee built into the format. Inspect the donor before reusing a slot.

A simple interaction:

In plain language, the interaction might be:

    Wait until the player presses Cross near the terminal.
    Show dialogue 35.
    Wait until the dialogue closes.
    Set the lift-unlocked flag.
    Open the lift.
    Give control back to the player.

The authoring layer might describe it like this:

    event = [
        wait_for_cross("terminal"),
        show_dialogue(35),
        wait_for_dialogue(),
        set_flag("lift_unlocked"),
        open_door("lift"),
        return_to_player(),
    ]

That is a readable plan, not the format stored on the disc. The compiler turns each helper into ATEL opcodes and operands.

The safest way to install the routine is usually:

1. Confirm the donor script and the old pointer.
2. Encode the new routine.
3. Append it to the existing bytecode.
4. Redirect one chosen script slot to the appended routine.
5. Reparse the result and verify the new pointer.

Appending is safer than inserting. If bytes are inserted in the middle of the donor script, every later address may move. Branches, calls, and entity pointers can then point to the wrong location.

Why timing matters

ATEL routines run over game frames. Some routines finish immediately. Others wait, yield control, and resume later.

A setup routine might do this:

    hide an actor
    set a starting position
    set a camera
    finish

A resumable routine might do this:

    start an animation
    wait 30 frames
    move an actor
    wait for the movement to finish
    show dialogue
    wait for the dialogue
    restore the camera
    finish

Putting the second routine into an entry point that is only intended to run once can cause the scene to freeze, skip work, or run at the wrong time.

Whenever a script waits, ask what releases the wait:

    wait for Cross       -> the player must press Cross
    wait for dialogue    -> dialogue must close
    wait for movement    -> movement must be started and reach its target
    wait for animation   -> the animation must exist and complete
    wait for battle      -> the battle must return its completion signal
    wait for frames      -> the scheduler must keep calling the routine

If there is no clear answer, the event is incomplete.

Instruction encoding

The tools can decode known retail instructions and emit the sequences used by the project. The general rules are:

- An instruction starts with an opcode byte.
- Extended instructions use the 0xFE prefix.
- Multi-byte values are usually little-endian.
- Calls and jumps use bytecode-relative addresses.
- Some operands are literal numbers.
- Other operands refer to field variables.
- Wait commands return to the field scheduler and resume later.

Do not choose an opcode because its name sounds right. Find a working retail example, decode it, make the smallest possible variation, and test it.

For example, if a retail terminal already opens a door after dialogue, first copy the shape of that routine. Change the dialogue ID or destination only after the copied version works.

Dialogue and text boxes

Dialogue is stored in stream 7. It is separate from the ATEL script that calls it.

A dialogue block has an ID, dimensions, and encoded text. xgdialog.py converts between the game’s character codes and a readable representation.

A simple entry might look like:

    dialogue[35] = {
        "width": 20,
        "height": 3,
        "text": "Authorization confirmed.\\nThe lift is unlocked.<Close>"
    }

The event routine refers to the block by ID:

    show_dialogue(35)
    wait_for_dialogue()

The original engine draws the box, handles the text, and removes the box when the close command is reached. The mod does not need to create a new text renderer.

Useful dialogue controls include:

    \\n              line break
    <New>           new page
    <Close>         close the dialogue box
    <Wait>          wait for input or timing
    <Delay:8>       delay for a number of frames
    character tags  show a speaker name or portrait-related control

The exact controls should be confirmed against existing retail dialogue. A missing close command can leave the event waiting forever. A line can also be validly encoded but too long for the selected box width.

A good workflow is:

1. Export a retail dialogue block.
2. Change only a few words.
3. Rebuild the dialogue stream.
4. Parse it again.
5. Load the field and check the box in the emulator.
6. Only then add new pages or control codes.

Changing dialogue usually does not require changing the event script if the existing ID is reused.

Planning a scene

A scene plan is a readable description of what the room should do. It keeps high-level decisions separate from raw offsets and bytecode.

For example:

    scene = {
        "donor": 361,
        "player_start": (120, 84, 0),
        "dialogue": [35, 36],
        "entry_event": "arrival_sequence",
        "terminal_event": "authorize_lift",
        "completion_flag": "lift_unlocked",
    }

A fuller plan should identify:

- the donor field
- the target field and disc file
- expected source hashes
- visible actors
- invisible controllers
- player start and return positions
- camera positions and modes
- dialogue IDs
- doors and destination fields
- flags and their meanings
- event routines
- encounters
- model, sprite, texture, or animation changes

The plan should answer “what should happen?” The compiler should answer “which bytes and pointers implement it?”

For example:

    Good plan:
    “After the player confirms authorization, unlock the east lift.”

    Bad plan:
    “Write 0x13 to offset 0x2A91, then replace pointer 0x1840 with 0x1F22.”

The second kind of information is sometimes necessary, but keep it inside a checked transform with a known old value and an explanation of why it is safe.

A scene is a state machine

Even a short scene has states. Write them down before writing the event script.

Example: a locked terminal and lift

    state 0: authorization not obtained
      terminal shows the locked message
      lift does not activate

    state 1: player has confirmed authorization
      terminal shows the accepted message
      lift opens
      completion flag is set

    state 2: player returns later
      lift remains available
      terminal does not repeat the introduction

The event should make each state explicit. Do not rely on an animation having played earlier as proof that the player completed the objective. Use a persistent flag.

Use separate flags for separate facts. These should not share one bit:

    authorization received
    battle defeated
    door unlocked
    cinematic completed

Commit a flag after the required action has finished. If the flag is set before a battle starts and the game crashes or the player reloads, the scene may incorrectly act as if the battle was completed.

Make repeat visits safe. Decide what happens if the player:

- presses Cross twice
- leaves during dialogue
- returns after the objective
- enters from an unexpected route
- reloads from a save made before the interaction
- reloads from a save made after the interaction

Actors, graphics, and controllers

An actor is not only the model seen on screen. It may involve:

- an actor definition
- model or sprite data
- animation records
- palette data
- a script table entry
- a position
- collision behavior
- an interaction role

It is often easier to separate those jobs.

Example terminal setup:

    visible terminal:
      displays the terminal model

    collision body:
      blocks the player if the terminal should be solid

    interaction controller:
      is positioned in front of the terminal
      faces the player
      owns the Cross-button script

    helper routine:
      runs the terminal animation after authorization

A small invisible controller is often more reliable than trying to make a large visible model handle every kind of interaction.

If you add a visible actor, make sure all related resources agree. A script pointing to an actor with no valid model can crash or display nothing. A model with no valid actor entry will not be positioned or animated correctly.

Doors and lifts

A door or lift normally involves several pieces:

- a visible model
- collision
- an interaction script
- an opening or closing animation
- a destination field
- a destination position
- a progression flag
- arrival behavior in the next field

Copy a working retail mechanism when possible.

Example locked lift:

    if lift_unlocked is false:
        show "The lift is locked."
        return

    play lift opening animation
    transfer player to field 380
    place player at the arrival marker

Test both ends. A door can appear to work while leaving the player inside a wall, facing the wrong direction, or arriving with a camera mode left over from the previous field.

Cameras

Camera changes are part of the event, not decoration added afterward.

A short scene might use:

    use normal player camera
    player presses Cross
    switch to a close-up camera
    show dialogue
    hold the camera during an animation
    restore the player camera
    return control

Always define what camera mode is active when the event ends. A scene can appear frozen when the real problem is that player control returned while the camera was still locked to a cinematic target.

Keep camera changes near the event that owns them. If a helper changes the camera, document who restores it and what happens if the helper is skipped because the scene is already complete.

Battles and battle animations

Field ATEL and battle animation scripts are different systems.

A field routine can start a battle and wait for it to return. The battle animation system then handles models, bones, effects, cameras, sound, damage, and completion.

A custom attack is a sequence, not a single animation file. It may need to:

1. Reset the models.
2. Put bones and objects in known starting positions.
3. Wait for transforms to be composed.
4. Run child trajectories or effects.
5. Play sound.
6. Dispatch damage exactly once.
7. Hide temporary objects.
8. Return the owner to an idle state.
9. Signal the battle controller that the animation is finished.

If the completion signal is missing, the battle menu may never return. If damage is dispatched in a loop, the attack may hit multiple times.

Model hierarchy matters too. An animation that expects a pod bone at one index will not behave correctly on a model with a different hierarchy, even if the model loads successfully.

Building the field

A normal build should follow a predictable order:

1. Verify the donor files and hashes.
2. Extract and decode the field.
3. Load the scene plan.
4. Apply resource changes.
5. Compile and install event routines.
6. Rebuild the field.
7. Parse the rebuilt field again.
8. Check pointers, sizes, routes, flags, and unchanged data.
9. Insert the approved replacement into the disc image.
10. Validate the PlayStation sector data.
11. Boot the result from a cold start in DuckStation.

The builder should keep a manifest. A useful manifest entry looks like:

    file: field-361
    source_sha256: <hash of clean donor>
    output_sha256: <hash of rebuilt field>
    changed_streams: scripts, dialogue
    reason: added terminal authorization sequence

A manifest makes it possible to review what changed and to reproduce the build later.

Run two clean builds and compare them. If the outputs differ, look for timestamps, random values, unstable file ordering, or untracked input files.

Validation

Check the work at several levels.

Source checks

- Is the donor the expected file?
- Are old bytes and old pointers what the transform expects?
- Are all IDs and indexes in range?
- Does the new script fit inside the 16-bit address space?
- Did an in-place edit accidentally change its length?

Field checks

- Can all nine streams be decoded?
- Do the header sizes match the streams?
- Do actor, model, sprite, palette, and texture indexes still agree?
- Are controllers on the walkmesh or where the scene expects them?
- Did unchanged streams remain unchanged?

Route checks

- Does every door lead to the right field?
- Is the arrival position walkable?
- Does the return route work?
- Do flags have one clear meaning?
- Does the field behave correctly before and after the objective?

Disc checks

- Does the rebuilt image contain the intended replacement?
- Are file allocation entries correct?
- Does the image pass MODE2/Form 1 EDC and ECC validation?
- Does the disc boot from a clean emulator state?

Runtime checks

- Enter through the normal game route.
- Test the first visit.
- Test the locked or incomplete path.
- Test the completed path.
- Test dialogue, waits, animations, cameras, battles, and transfers.
- Leave and return.
- Cold-boot instead of relying only on emulator save states.

A good first project

Keep the first scene small.

Start with one donor field and one interaction:

1. Parse and rebuild the donor without changes.
2. Replace one short dialogue entry.
3. Confirm the text appears.
4. Add one Cross-button routine.
5. Set one temporary flag.
6. Make one door or object respond to the flag.
7. Test from a cold boot.
8. Add actors, camera work, animations, and battles later.

This order gives every failure a smaller search area. If a no-change donor will not boot, there is no reason to debug a new event on top of it.

Useful inspection workflow

The exact command-line options may change, but the intended sequence is:

    xgfield.py parse <field>
    xgfield.py extract <field> <output-directory>
    xgscript.py inspect <script>
    xgdialog.py export <dialogue> <json>
    xgdialog.py rebuild <json> <dialogue>
    xgdisc.py inspect <disc-image>
    xenoiso_build.py build <manifest>

The command names are less important than the habit: decode, inspect, make one small change, rebuild, parse again, and test.



++----++

Mistakes I've learned from:


Editing compressed bytes directly usually breaks offsets or makes the result impossible to reproduce.

Inserting code into the middle of a retail script usually breaks pointers to later routines. Append and redirect instead.

Using an initializer as a long-running coroutine often causes a hang because it does not resume the way an update or action routine does.

Forgetting a dialogue close command leaves the event waiting.

Setting a completion flag before the required action is finished makes reloads behave incorrectly.

Adding a visible model without its actor, palette, animation, or script relationship makes an object invisible or inert.

Returning from a cinematic without restoring the camera can make the player appear trapped.

Testing only from an emulator save state can hide initialization problems that appear during a real boot.

What is confirmed and what is still interpretation

The tools directly confirm the nine-stream field layout, the LZSS framing, the ATEL entity table, the relative pointer model, the dialogue component structure, and the bytecode emitted by the project’s helpers.

Some instruction names come from Noah or decompilation metadata. They describe observed behavior; they are not official Square documentation. Entity script-slot roles are conventions found in donor fields, not types stored in the file. Some camera, scheduler, interaction-volume, and control-byte meanings were established through runtime tests. xgatel.py is a partial disassembler, not a complete decompiler.

Keep notes about which conclusions are directly verified and which are inferred. When possible, tie each claim to a retail file, a decoded sequence, or a repeatable emulator test.


The main rule:

Make the smallest change that proves the next part of the system.

Keep the donor intact. Append code instead of relocating it. Verify every old value before changing it. Rebuild and parse immediately. Test from a cold boot. Xenogears already provides the engine; successful modding is the careful process of giving that engine data it can safely run.

