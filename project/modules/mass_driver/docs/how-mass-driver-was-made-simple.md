# How the Mass Driver project was possible

## The basic idea

*Xenogears* is largely data-driven. Its original PlayStation program already
knows how to display rooms, move actors, open doors, play dialogue, control
cameras, start battles, and remember story flags. The Mass Driver project did
not replace that engine. It learned how the game's data is organized and then
built new data that the original engine could understand.

In simplified form:

```text
original game resources
        +
new scene plans and dialogue
        |
        v
compile them into Xenogears data
        |
        v
rebuild and verify a playable Disc 2 image
        |
        v
distribute only the patcher and binary differences
```

No official Square development tools or original source code were available.
The formats and behavior were learned by examining the game, comparing known
working scenes, studying community research, and testing the results in the
real game engine.

## What a scene contains

A room is not a single script. It is a bundle containing several coordinated
parts, including:

- room geometry, textures, and collision;
- actors, sprites, and animations;
- dialogue;
- event scripts;
- doors and triggers;
- encounter information; and
- persistent flags that remember what the player has done.

This made it practical to begin with a working retail room, called a donor,
instead of constructing an entire room from nothing. The project retained its
valid floor, camera setup, models, and useful mechanisms, then replaced or
extended the parts needed for the new scene.

## How the game scripts work

Each field has a small event virtual machine. Its bytecode tells the original
game to perform actions such as:

- show dialogue;
- wait for the player or for an animation;
- move or hide an actor;
- operate a door or lift;
- change the camera;
- set or test a progress flag;
- transfer to another room; or
- begin a battle.

Actors have entry points for different jobs, such as initialization,
continuous updates, Cross-button interaction, collision, and helper actions.
The project usually appended a new routine and redirected one carefully chosen
entry point to it. This was safer than inserting code into the middle of the
original script, where every later address might move.

Battles use a separate animation scripting system. It coordinates models,
bones, visual effects, cameras, damage, and the signal that returns control to
the battle menu. That system was used for additions such as El-Regulus's
AERODs attack.

## What an event planner is

The event planner is a project-side authoring tool, not something added to the
game.

It is a set of Python data declarations that describes a scene in useful
terms: which donor room to use, which actors appear, where doors lead, what
dialogue is shown, which flags control progress, and which routines must be
installed. Compiler helpers turn that plan into the exact bytecode and binary
tables expected by *Xenogears*.

For example, a planner can describe a terminal interaction like this in plain
language:

1. Wait for the player to press Cross near the terminal.
2. Show the authorization dialogue.
3. Record the completed objective in a persistent flag.
4. Unlock the next lift.
5. Return control to the player.

The compiler converts those steps into game opcodes, assigns dialogue IDs,
repoints the correct actor script, and rejects the result if it exceeds the
game's limits. A complete plan also defines what happens on repeat visits and
how control is restored if an animation, battle, or transition finishes.

## How a planned scene became playable

The build process followed the same general sequence for every scene:

1. Verify that the donor resources are the exact expected files.
2. Unpack the room into its component streams.
3. Apply the scene plan, dialogue, actor, door, camera, and encounter changes.
4. Compile new event routines and update their entry points.
5. Rebuild the resource and immediately parse it again.
6. Check routes, flags, sizes, pointers, and unchanged donor data.
7. Insert all approved replacements into a MODE2/2352 Disc 2 image.
8. Recalculate PlayStation sector error-correction data.
9. Cold-boot the result and test the complete scene in DuckStation.

The builder is deliberately strict. It checks hashes and old values before
changing them, preserves untouched data byte-for-byte, enforces archive and
script size limits, and produces a manifest describing every replacement.
Two independent builds can therefore be compared to prove that the output is
deterministic.

## How the patcher can be distributed

The public application does not contain a Xenogears disc image, emulator, or
BIOS. It requires the user to select an unmodified USA Disc 2 raw BIN and
checks its size and SHA-256 identity. It then applies an xdelta/VCDIFF patch to
create the modified game in a new location, leaving the source disc unchanged.

This works because the patch stores the differences between the clean disc
and the verified Mass Driver build rather than distributing the original game
itself. This describes the project's distribution approach; it is not legal
advice.

## In one sentence

The project was possible because the original game already contained a
powerful scene engine, and we built a guarded compiler that translated new
scene plans into the exact rooms, scripts, dialogue, models, and battle data
that engine already knew how to run.

For the full technical explanation, see
[Xenogears scripting and scene-planning architecture](../../../docs/xenogears-scripting-and-scene-planning.md).
