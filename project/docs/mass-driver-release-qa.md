# Mass Driver release acceptance

This record distinguishes native gameplay, source regression checks and Windows
packaging tests. It does not claim every possible player action, controller or
PC configuration has been tested. The finite gameplay acceptance checks below
have passed; public packaging evidence is recorded separately.

## Native gameplay coverage

A fresh **V176 New Game-to-ending run with Sony BIOS passed** on the exact
final disc. It completed mandatory powers and clues, authorization, Guardian
victory with the starting Gears, the west passage and five vaults, the protected
memory, Citan/keypad sequence, full launch movie, automatic Gear recovery and
world-map movement. No HLE CPU state or card was imported into that run. The
Guardian victory left Vierge at 5,502 HP and Crescens at 8,359 HP, without item
use or purchased upgrades. An ordinary save from this fresh Sony run was also
written before authorization and cold-loaded at field 725's normal entry, with
native entry value 2 and mission state retained. This save check and the ending
check are separate legitimate branches of the same fresh New Game run.

The main V175 run starts from New Game and completes the dungeon through the
Guardian, protected memory, capsule launch, Gear recovery and moving world-map
party. Ordinary memory-card saves were written and cold-loaded before
authorization, before and after the Guardian, and after launch. A completed
save was revisited: the boss, memory and launch did not repeat, and completed
state reports persisted.

Separate V175 runs cover both approaches to the first memory cube, repeated
saving into another slot, all three random battle formations, victories and
Escape returns, native item purchases and sales, item recovery, wrong
authorization answers, unavailable power feedback, Guardian defeat and a
cold-loaded retry victory. The Guardian victory used the supplied Gears without
buying upgrades or consuming items. Vierge's native Aerods and Ether options
were checked separately; its physical output is much lower than Crescens.
Rail-first/later-Aux operation was tested through the opened central gate;
with neither clue reader visited, the authorization console still gives the
Guidance and Materials Storage location hints.

The archive video was tested without a disk, with acquisition refused, with
acquisition accepted, on repeat examination, through all seven clips and back
to normal field control. NUKE was played through failure, retry, pause, resume,
exit and its full native mission: level 19, score 8,930. Its record was written
through the game's save menu, cold-loaded from slot 2 and verified after returning
to the archive: BEST 08930, record 08930, pilot NUKE, level 19.

V176 corrects Missile Command's Triangle input mask. V175 incorrectly responded
to Square while displaying Triangle. The final test reloaded the archive field
from the new disc and passed Triangle title exit, ignored Square, pause, Cross
resume, Circle exit from pause and normal field control. Native play also
cleared wave 1, reached wave 2, lost, entered a high-score name and retried.
The 400-point wave-2 record survived an ordinary save, fresh-process Continue
and return to the terminal. Other V175 gameplay evidence is retained under its
actual version and carried forward only where compiled content is identical.

Route coverage separately exercised **all 33 fields and all 66 directed
connections**, including the four optional archive branches. This coverage
union is attributed to V175 HLE and uses actual within-run transitions; it does
not infer movement between independent checkpoints.

## Test methods and limits

The earlier completed V175 main route, combat/economy checks and most route coverage ran
in PCSX-ReARMed's HLE mode. Separate tests used the user's unmodified USA Sony
BIOS for repeated saves and cold Continue, NUKE's complete mission and saved
record, V176 Missile Command, and the complete fresh V176 main route.
Diagnostics read game state; they did not write RAM,
alter combat data, force progression flags or manufacture saves. Serialized CPU
checkpoints shortened repeated checks within matching content. Save acceptance
used the actual memory-card menu and fresh-process Continue rather than loading
an emulator state. Long save-menu checks ran continuously in one core process.

Native Windows DuckStation, including the exact GPL-era runtime shipped in the
public player, also booted the game and cold-loaded ordinary V175 and V176 saves. The
complete main route was tested in the native libretro core. It was not replayed
in full in each emulator frontend. Physical gamepad hardware and every Windows
display/audio driver configuration were not tested. The shipped Windows player
requires the player's supported Sony firmware; it does not offer HLE mode.

## Windows player acceptance

The compiled player was tested with actual native installation and patching,
missing and invalid inputs, cancelled setup, retry, exact clean-disc
reconstruction, BIOS validation/copy, repeat setup, repair and preservation of
game, cards and settings. Native GUI first-run file pickers, bundled emulator
startup, normal shutdown and a second launch without input prompts passed.

Testing used an existing Windows x64 PC with Visual C++ runtime installed.
The optional prerequisite path downloaded Microsoft's official installer and
verified its signature and publisher; an unsigned test file was rejected.
Microsoft's installer was not executed, and a clean Windows VM was not tested.
The release is unsigned. Reproducible package checks and SHA-256 identities
establish the tested bytes; they are not a code-signing certificate.

## Preservation and scope

The final dialogue retains the approved V173 voice adjustments. The entire
protected Central Control resource, including Miang's memory, boundary dialogue,
scripts, actors, cameras, timing and sound, is unchanged by the release repairs.
Native enemy statistics and AI remain unchanged. Historical candidates, cards
and the user's existing emulator installation were preserved.

The public installer excludes game images, BIOS, memory cards, emulator states
and Microsoft runtime DLLs. It ships the mod patch and an unchanged GPL-era
DuckStation runtime with matching source and dependency notices. See the
[player guide](mass-driver-public-player.md) and
[source scope](source-distribution.md).
