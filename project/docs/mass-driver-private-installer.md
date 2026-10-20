# Mass Driver private installer

**V173 has a confirmed release blocker:** its demo title disables native Continue. The native game can write a save, but that title cannot load it. V174 repairs this menu; the V173 artifacts and startup evidence below are retained as history, not final release acceptance.

The [Windows installer](../dist/private/mass-driver-v173-standalone-20261019/Mass_Driver_Private_V173_Setup.exe) contains the V173 Mass Driver game image, the locally supplied BIOS, the unmodified game runtime, its assets, and six required Microsoft runtime DLLs. The player does not need to patch a disc, locate an emulator or BIOS, or install Python. This is a private local test package; public redistribution has not been cleared. It is unsigned.

Open the installer, select **Install**, then **Play**. Later, use the installed **Play Mass Driver.exe** or its optional Start menu shortcut. The default folder is `%LOCALAPPDATA%\Xenogears Mass Driver Private`. **Change location** selects another folder. The installer checks folder length before writing files because the runtime failed to initialize from an earlier deeply nested layout; the compact final layout passed startup in the same test directory.

Keyboard: arrows move; K is Cross, L Circle, J Square, I Triangle; Enter is Start, Backspace Select, Q/E L1/R1, and 1/3 L2/R2. A standard SDL controller mapping is included. Escape opens the pause menu and F11 changes fullscreen mode. Physical keyboard and controller acceptance remain pending.

Cards, saved states, settings and other mutable files are under **UserData** in the chosen installation folder. Preserve that folder when keeping or moving saves. Reinstallation and repair preserve it; the package uses its own settings instead of the user's global emulator configuration.

The installer is **560,399,157 bytes**, SHA-256 `c21ff569cfc24f606d2481f55f13038742c83b984f7fd138e43456b4c55a0a01`. It installs 268 payload files totaling 869,942,578 bytes, plus the small Play launcher and generated user data. The embedded game BIN remains `d78294b5db653231bde3d29ff1acd3509af91cef2a4aefbac13f737e674193b1`.

Acceptance completed:

- Exact full-payload extraction, integrity checks, cancellation/retry, corruption repair, and preservation of private cards/settings.
- An independent build produced the identical installer and Play launcher.
- Migration from the earlier internal layout preserved old content and UserData.
- The final installed package rendered the native intro movie. All six Microsoft runtime DLLs loaded from its own runtime folder.
- Normal runtime and launcher exit synchronized settings back to UserData, retained the correct BIOS and mutable-folder paths, and generated a resume state in the private save-state folder.
- The installer window was visually reviewed. Its shared native install function was exercised through its headless test interface.

These checks do not establish clean-machine compatibility, a native game save/Continue cycle, or a full dungeon playthrough. The shutdown test changed only its owned QA copy's exit-confirmation preference; shipped defaults retain normal confirmation. The game remains a release candidate. See [V173 game notes](mass-driver-v173.md) for content and remaining gameplay acceptance.

The [installer source companion](../dist/private/mass-driver-v173-standalone-20261019/Mass_Driver_Private_V173_Installer_Source.zip) contains the native installer sources and preparation/build scripts, without a game image, BIOS, or runtime payload. Rebuilding requires the canonical project and the separately supplied pinned inputs described by those scripts. Exact runtime licenses and dependency notices are retained inside the installed runtime and its `licenses` folder.
