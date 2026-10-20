# Mass Driver Windows player

Download **Mass_Driver_Setup.exe** from the project's GitHub release. Install it
in a writable folder, then choose **Play**. No Python, compiler, separate emulator
installation or manual patching is needed.

On the first launch, the app opens Windows file pickers for two files you supply:

1. An untouched **USA Xenogears Disc 2 BIN**, dumped from your own disc. A patched
   disc, another region, an ISO, or a compressed archive will not match.
2. A supported **512 KB USA PlayStation BIOS dump** from your own console.

The app validates both inputs, builds its separate game copy and starts the
bundled emulator. Your original files remain unchanged. Later launches use the
completed setup automatically. A missing input opens the appropriate picker.
An invalid input produces an explanation; choose Play again to select another
file.

The clean USA Disc 2 input is 688,700,880 bytes with SHA-256
`5eab85c683d4d7087d345b587472db9c44df29b35ce66553c2626d26018b947e`.
The BIOS must match a known USA firmware identity supported by the included
emulator; renaming an incompatible file does not make it valid.

The download contains the mod's patch, native installer/launcher, GPL-era
DuckStation and dependency notices. It contains **no Xenogears disc image,
PlayStation BIOS, memory card or save**. Obtain the required game and firmware
through sources you are entitled to use. This is an unofficial fan project,
unaffiliated with Square Enix or Sony.

## Playing and saving

Choose **New Game** to start Mass Driver with Elly and Emeralda. Choose
**Continue** to load an in-game memory-card save. Save normally at a memory cube;
use those saves when updating rather than carrying emulator save states between
different game revisions.

Keyboard and gamepad bindings are listed in the installed **README_PLAYER.md**.
The bundled emulator's controller settings can be used to change them. Gamepad
and keyboard controls are normal player bindings; no automation bindings ship.

`UserData` holds your BIOS copy, memory cards, settings and emulator data.
`Game` holds the generated game. Keep these folders when moving or backing up
an installation. Reinstall and repair preserve them. Do not distribute your
populated installation: it contains the game and BIOS you supplied.

If Microsoft Visual C++ runtime components are missing, Play offers Microsoft's
official installer. The download is checked for Microsoft's signature before
the standard installer opens. Complete it, then choose Play again. Our package
does not bundle Microsoft runtime DLLs.

This release is unsigned. The published SHA-256 file identifies the distributed
installer; it does not substitute for an Authenticode signature.

## Source and notices

Matching project, player, patcher and emulator source companions accompany the
release. Read [source distribution](source-distribution.md) for their scope and
build requirements, and [release QA](mass-driver-release-qa.md) for test coverage
and limitations. Preserve the included upstream licenses and notices.
