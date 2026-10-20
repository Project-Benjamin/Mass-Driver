# Rico dialogue release — September 6, 2026

`rico-dialogue-v3` is the active Rico and combined release. It follows
`rico-ch2-opening-v2` and includes the Chapter 2 visibility/progression fixes,
native dialogue portraits throughout all seven Rico chapters, and yellow
speaker names with white body text.

## Changes

- Chapter 2's invisible director/hotspot dialogue now explicitly permits an
  invisible owner. Native WAIT_DIALOG could otherwise close the window and
  stop the event before its objective commit and control-unlock instructions.
  Hammer's introduction and carrier/direct interaction paths now finish those
  instructions. Suzarn is explicitly shown and given a settling interval
  before her introduction; she is hidden only after the awaited dialogue.
- The final presentation layer covers 21 Rico fields on each standalone disc
  and the corresponding relocated combined fields: 686 speaking call sites,
  compiled into 1,203 independent windows per disc. Portraits switch with the
  named speaker and the original script continuation is retained.
- Existing native portraits cover the established cast. Nineteen checked
  native slots provide young Rico and the missing NPC portraits. Sources and
  generation provenance are in the Rico dialogue portrait asset directory.
  Encoded TIMs are 64×64, 8bpp, 4,640 bytes with transparent exteriors.
- Yellow names use an opt-in USA executable renderer change, with no new RAM
  allocation or file growth. Unmarked windows retain native rendering.

## Verification

`python project.py test rico` executed 1,009 tests with seven skips. One old
Mass Driver archive test encountered an OSError while reading a file during
concurrent filesystem compression; it then passed twice in focused reruns.
There were no assertion failures. The final portrait/planner/compiler suite
passed 25 tests, and the final color/boot-verifier/release-integration suite
passed 11 tests after the last changes.

The rebuilt images passed replacement readback. The executable verifier checks
the actual ISO boot file, SYSTEM.CNF, the rebuilt embedded file table, and every
staged executable byte outside that correctly rebuilt table.

Mass Driver and Soylent were rebuilt to refresh their shared-source receipts;
their complete disc images are byte-identical to `workspace-v1`. In combined,
the full Central Control bundle 2062 and graphics 2063, all four Miang portrait
slots, and all 72 native portrait resources outside the allocated custom set
remain byte-identical to the prior active combined image. The normalized
Soylent V166 donor is unchanged.

## Runtime status

The exact active media passed `project.py play ... --check-only` and was
launched through the project CLI in the configured DuckStation. Rico Disc 1
reached its publisher/title sequence and opening movie; combined Disc 2 reached
its publisher/title sequence. Automated controller inputs did not reliably
advance to chapter selection. Suzarn's live appearance, Hammer's complete
interaction, and the rendered yellow names therefore remain unverified in an
actual chapter playthrough. The prior combined New Game black-screen report
has not been cleared; combined retains `known-issue` status.

Diagnostic memory cards and save states used a separate directory. DuckStation
was closed and its original settings restored byte-for-byte. No user save or
memory card was replaced.

Use the root `PLAY_RICO.cmd` or `PLAY_XENOGEARS_REIMAGINED.cmd` for current
registered media. Start Chapter 2 fresh from the selector for the first check;
an old emulator save state contains the old executable and resident scripts.
