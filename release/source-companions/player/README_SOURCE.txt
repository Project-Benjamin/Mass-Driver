Mass Driver public player V176 - Windows x64 source companion

This archive contains the shared native installer/Play launcher source, public
and historical private build modes, preparation/QA scripts and license notices.
No game image, BIOS, emulator binary, Microsoft binary, patch payload, user data
or compiler is included. The public mode asks each player for their own Disc 2
and BIOS and constructs a separate local game. It never modifies source inputs.

Read tools/mass_driver_standalone/README.md. The public entry points are
prepare_public_payload.py, build.py --public and verify_public.py. The runtime
is official GPL DuckStation v0.1-7371, exact source commit:
b2577ef8bdaae99840874b6dae8146f0316357b4.
Its matching full source/dependency archive is a separate Emulator_Source
companion supplied next to the player download. Runtime notices and the GPL
license are retained in the installed program. No endorsement is implied.

The portable patcher's own source companion and matching complete Mass Driver
project-source companion are separate. Reconstructing a game patch requires
their external original-disc and extracted-data inputs. This source archive
does not contain copyrighted retail game/firmware bytes.

To use a modified GPL emulator or Qt library, replace the appropriate files in
an independently prepared payload, update its descriptive player-release.json,
then run build.py --public. The builder pins the bytes of YOUR payload; no
signing key or password is needed. You may also run the upstream emulator
directly, independently of the Mass Driver integrity-checking launcher.
Preserve the component licenses/notices when making changes. This archive
does not restrict the rights granted by those licenses.

Official compiler: llvm-mingw 20261006 UCRT x86_64 portable distribution:
https://github.com/mstorsjo/llvm-mingw/releases/download/20261006/llvm-mingw-20261006-ucrt-x86_64.zip
SHA256: 317492c456aa27ee607a5919f1d2d38dcdc1112516a24d0bf4b00d078f52d17a
The compiler and prepared payload remain external build-time inputs.

Fixed ZIP metadata and source-manifest.json make this companion reproducible.
Hashes identify bytes, not a publisher signature or full gameplay acceptance.
