How to Create a Xenogears Field Mod

Purpose

This document explains the general method used to create the Mass Driver mod. It is intended as a starting point for somebody who wants to build another scene, room, or short story sequence for the original PlayStation version of Xenogears.

The work is not done by making a new game engine. Xenogears already knows how to load a field, display models and sprites, move characters, show dialogue, operate doors, start battles, change cameras, and save progress flags. The job is to understand the data that the original engine expects and provide it with new, correctly formatted data.

What you need

You need an unmodified copy of the appropriate game disc, a way to inspect and edit binary files, Python, and an emulator such as DuckStation. You also need patience for repeated testing; most of the work is learning from small changes and comparing the result with a working retail scene.

The project already contains useful starting tools in the tools directory. The most important ones are xgfield.py for unpacking and rebuilding fields, xgdialog.py for reading and writing dialogue, and xgscript.py for inspecting and extending event scripts. The build scripts and recipes show how complete scenes are assembled. The mass_driver_portable directory contains the code used to make a user-facing patcher rather than distributing a game image.

The original game is a required input, not something that should be included with the project. The public release should contain the patch and tools needed to apply it to a verified user-owned disc image.

Start with a donor field

Building a complete field from nothing is possible in theory but is a poor first project. Select an existing retail field that already has the floor, camera, actors, graphics, door, terminal, lift, or animation behavior that is close to what you need. This is the donor field.

A field is a bundle of separate streams. In practical terms, these contain the images, walkmesh, models, actors, sprites, event scripts, encounters, dialogue, and triggers. The donor gives you a coherent set of resources that the game already knows how to use together.

Before editing anything, record the donor’s field number, disc location, file size, and SHA-256 hash. The build should refuse to modify a file if it is not the expected version. This prevents an edit intended for one retail file from silently corrupting another.

Inspect and unpack the field

Use xgfield.py to parse the field and extract its streams. The field contains nine compressed streams and a header with their sizes and offsets. Do not edit compressed bytes by hand. Decode the streams, change the decoded data, then let the builder reconstruct the header and compression layout.

A typical inspection process is conceptually:

    parse field 361
    extract streams to work/field-361/
    inspect models, actors, scripts, dialogue, and triggers
    make the planned changes
    rebuild field 361
    parse the rebuilt field again

The second parse is important. It proves that the file can be read using the same rules as the original game and catches broken offsets, sizes, and compression data early.

Plan the scene before writing bytes

The safest approach is to describe the scene in a small Python planner. The planner should say which donor field is being used, which entities are visible, where the player starts, what the doors do, which dialogue entries are added, which flags control the scene, and which event routines are installed.

A simplified plan might read like this:

    scene = {
        "donor": 361,
        "player_start": (120, 84, 0),
        "dialogue": [35, 36],
        "entry_event": "arrival_sequence",
        "terminal_event": "authorize_lift",
        "completion_flag": "lift_unlocked",
    }

Keep the plan declarative. It should describe what the scene means, while compiler helpers handle offsets, pointers, opcodes, and binary layout. This makes the scene easier to revise and makes it possible to validate the result against the plan.

Write field events

Field events run in Xenogears’ ATEL event virtual machine. An entity normally has several script slots. Common uses are an initializer, a repeating update, an action or Cross-button interaction, collision behavior, and helper or animation routines. These roles must be checked against the chosen donor; they are conventions, not universal rules.

An interaction can be planned in ordinary terms:

    wait until the player presses Cross near the terminal
    show dialogue 35
    wait for the dialogue to close
    set the completion flag
    open the lift
    return control to the player

Its compiled form is equivalent to a sequence such as:

    wait_for_cross("terminal")
    show_dialogue(35)
    wait_for_dialogue()
    set_flag("lift_unlocked")
    open_door("lift")
    return_to_player()

Those helper calls are examples of the authoring layer, not literal retail opcodes. The compiler converts them into the numeric commands used by ATEL.

Append new routines whenever possible. Inserting bytes in the middle of an existing script moves later addresses and can invalidate branches, calls, and entity entry pointers. Appending a routine and redirecting one known script slot leaves the rest of the donor stable. The script tool should verify the old pointer before replacing it and reject code that exceeds the VM’s address space.

Remember that event timing matters. A one-shot initializer is not the same as a routine that yields and resumes over multiple frames. Movement, camera holds, world-map loading, animation waits, and multi-step sequences belong in a routine that the field scheduler can resume safely.

Create dialogue and text boxes

Dialogue lives in the field’s dialogue stream. Each entry has an ID, a box width, a box height, and encoded text. xgdialog.py converts readable text into the game’s character table and preserves special control bytes.

A simple authored entry could be represented as:

    dialogue[35] = {
        "width": 20,
        "height": 3,
        "text": "Authorization confirmed.\\nThe lift is unlocked.<Close>"
    }

The event script displays it by ID:

    show_dialogue(35)
    wait_for_dialogue()

The original engine draws and removes the text box. The mod does not need to implement a new text-box renderer. It only needs to supply valid dialogue data and call it correctly. Control codes can handle line breaks, page changes, delays, waits, speaker names, and closing the box. Use existing retail dialogue as a reference whenever a control code is uncertain.

Keep a dialogue table with stable IDs. Check the final encoded size against the field’s limits, and test long lines, multiple pages, and repeated visits. A dialogue entry that looks correct in a text file can still overflow the box or leave the event script waiting forever if its closing control is missing.

Add actors, graphics, and doors

Reuse retail actor and animation records where possible. If a new character or object is needed, add it to the appropriate actor, model, sprite, and palette streams together. A script pointing to an actor that has no valid graphics is just as broken as a graphic with no script.

Doors and lifts usually require more than a visible model. They may also need collision, an interaction script, an animation helper, a destination field, and a persistent flag. Copy a working retail mechanism and change only its destination or state logic when practical.

Use flags for anything that must survive leaving and re-entering the field. Define the first-visit behavior, the repeat-visit behavior, and the behavior when the player interacts before the objective is complete.

Build, validate, and test

The complete build should follow this order:

1. Verify the donor files and their hashes.
2. Extract the field streams.
3. Apply the scene plan, resource edits, dialogue, and scripts.
4. Rebuild the field and parse it again.
5. Check pointers, stream sizes, script limits, routes, flags, and destinations.
6. Confirm that unchanged donor streams remain byte-identical when promised.
7. Replace the correct canonical files in the Disc 2 image.
8. Recalculate the PlayStation sector data required by the rebuilt image.
9. Cold-boot the image in DuckStation and test the whole sequence.

Test from a fresh save and from a save that reaches the scene through the real game route. Test every door, interaction, dialogue branch, animation wait, battle return, and repeat visit. Emulator state saves are useful during development, but they can hide initialization problems, so cold boots are necessary before considering a scene finished.

Make builds reproducible

The builder should use explicit inputs and produce a manifest listing every changed file, old hash, new hash, size change, and reason for the change. It should fail on unexpected old bytes rather than applying a blind replacement.

Run the build twice and compare the outputs. Identical results show that the process is deterministic and that no timestamps or temporary data leaked into the image.

Distribute the result safely

The release tool should ask the user to select an unmodified USA Disc 2 BIN, verify its size and SHA-256 hash, and write the patched image to a new file. An xdelta/VCDIFF patch stores only the differences between the clean image and the finished build. This lets the project distribute the modification without redistributing the original game data.

The practical lesson

The hardest part is not drawing a text box or inventing a new engine. It is identifying the correct retail structures, preserving their relationships, and making small, verified changes. Start with one donor field, one actor, one dialogue entry, and one interaction. Once that works from a cold boot, expand the scene gradually and keep every change reproducible.

