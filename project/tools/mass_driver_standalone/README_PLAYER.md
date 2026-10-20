# Mass Driver

Run **Mass_Driver_Setup.exe**, choose **Install**, then **Play**. You need Windows
10/11 x64, an untouched USA Xenogears Disc 2 BIN dumped from your own disc, and a
512 KB NTSC-U PlayStation BIOS dumped from your own console. The game and BIOS
are not included. No Python, patch commands or separate emulator setup is needed.

On first Play, Explorer asks you to select the Disc 2 BIN and then your BIOS.
The original files remain unchanged. Mass Driver builds its own game copy and
keeps your selected BIOS in its own UserData/bios folder. A patched Perfect Works
image, Disc 1, another region, or an unrecognized BIOS will be rejected clearly.

If you do not have a BIOS dump, cancel setup and dump the firmware from your own
PlayStation; do not download someone else's firmware. DuckStation's official
documentation explains the BIOS requirement:
https://github.com/stenzek/duckstation/tree/b2577ef8bdaae99840874b6dae8146f0316357b4
Common supported USA consoles include SCPH-1001, SCPH-5501, SCPH-7001 and SCPH-101.
Return to Play when your files are ready. Canceling a file picker changes nothing.

The installer includes GPL DuckStation v0.1-7371. If its Microsoft Visual C++
runtime is missing, Play offers to download the official x64 installer directly
from Microsoft. Its Microsoft signature and publisher are checked before it is
opened. Microsoft shows its normal license/setup window and may ask for Windows
administrator approval. You can decline and retry Play later. Our download
contains no Microsoft runtime DLLs; this step requires an internet connection.
Official download: https://aka.ms/vs/17/release/vc_redist.x64.exe

After setup, use **Play Mass Driver.exe** or the optional Start menu shortcut.
Keyboard: arrows move, K confirms/Cross, L cancels/Circle, J is Square, I is
Triangle, Enter is Start, Backspace is Select, Q/E are L1/R1, and 1/3 are L2/R2.
Space pauses, Escape opens the pause menu, and F11 toggles fullscreen. A standard
SDL controller is mapped automatically; physical controller acceptance is tested
separately. Use the game's memory cube to save and **Continue** to reload.

Cards, settings, states and the BIOS stay in the installation's **UserData**
folder. Reinstall/repair preserves them and your generated game. Keep a backup
of UserData when moving to another PC. Repair fixes installed program files; it
does not rewrite an old malformed game save.

This is an unsigned fan-made release candidate. A published SHA256 checks file
identity; it is not a code signature or a promise of complete gameplay testing.
The emulator's developers did not create or endorse this dungeon. See
runtime/LICENSE.txt, runtime/resources/thirdparty.html and licenses for notices.
Matching player/project/emulator source companions are separate downloads.
