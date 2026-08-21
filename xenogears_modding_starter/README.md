Xenogears modding starter files

This is the small set of tools and notes needed to begin studying and making a Xenogears field modification. It is meant to be copied into a new project and extended as the project grows.

Nothing here is a game image, emulator, BIOS, installer, or finished patch. The person using these files must provide their own clean disc image.

Where to begin

Start with "START-HERE_technical_shorter.md" -- This will get you through all you need to start modding. 

For a more detailed explanation, refer to the "technical_longer.md" document.

The tools folder contains the reusable low-level pieces:

xgfield.py reads and rebuilds the nine streams inside a field.

xgdialog.py exports and rebuilds field dialogue.

xgscript.py inspects and extends field event scripts.

xgencounter.py handles encounter data.

xgdisc.py and xgmode2.py inspect and work with PlayStation disc data.

xenoiso_build.py assembles the changed resources into an image according to a build manifest.

Starting a project

Copy this folder somewhere else and leave the original files untouched. Set the paths in config.example.json for the clean disc files you are working with. Then choose a retail field to use as a donor and make a separate working copy of its decoded resources.

The first useful milestone is a no-change rebuild that parses successfully and boots in an emulator. After that, change one dialogue entry or one small event at a time. Keep a record of the donor file hashes and test every change from a cold boot.

The tools are intentionally general, but the project still needs its own scene planner, build manifest, and validation rules. Those should live outside this starter folder once the new project has a direction.

For distribution, share only original code, new authored data, and a patch that the user applies to their own verified disc image.

