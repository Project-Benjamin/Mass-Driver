# Chapter 2 scene and character pass

The new opening begins in the infirmary with Fei lying in the actual bed,
using retail field 213's special animation 0x77/program 0 and mattress entry.
A visible Kislev guard hands him over to the attendant. Hammer enters in the
following morning's scene, rather than standing in the infirmary corner.

The Champion's rooms now contain a complete, automatically staged conversation
between Rico, Suzarn and Hammer. Hammer walks off the stairs to a clear floor
position before the report continues. Suzarn stays after the introduction and
can be spoken to. All participants have independent actor routines; the later
bandage scene uses separate script slots and the same clear floor positions.

The dialogue is newly authored expansion, grounded in the retail timeline.
Fresh linen and an unchanged locked gate express the limits of Rico's status.
His orders about feeding Fei show concern filtered through pride and coercion,
without turning the Baptism into a friendly encounter. Hammer's later scenes
address the empty room and the loss of the title. Suzarn remains present until
the story's murder report identifies the fifth victim, matching retail field
211. D Block's survivors no longer repeat unresolved missing-person dialogue
after the sewer encounter, and Gramps actually supplies the drain advice that
Fei later recalls.

Suzarn's portrait follows the native sprite: swept olive-gold hair, red cloth
face covering and scarf, and dark upper-chest clothing. It retains the existing
native 64×64, 8bpp TIM format and yellow speaker-name presentation.

Adult Rico starts a new game at level 24, an approximate recruitment-era
benchmark. Retail recruitment level varies with accumulated experience.
Both experience totals and remaining-experience counters match that level,
with representative native-growth HP, EP and statistics, six AP, four early
deathblows, and the initial Spirit commands. The older level-70/full-ability
override no longer survives in Rico's starting record. Other characters'
records and the child Rico profile are preserved.

## Technical safeguards

- The guard's local sprite bank and external VRAM upload carry identical
  pixels; the external field graphics cannot overwrite the new guard atlas.
- Bed, attendant and guard placement use checked native entries and camera.
- The opening owns input until dialogue, progress commits and camera release
  complete. Old room saves retain a usable manual Hammer-report fallback.
- Opening actor slots 16–20 and bandage slots 24–28 do not overlap.
- NPCs regain immovable collision flags, keeping their interaction points
  aligned after the scene.
- No new field or global-state allocation is introduced. Miang's protected
  scene and the normalized Soylent donor remain outside the edited scope.

## Validation and play instructions

`python project.py test rico` completed 1,034 tests in 322.089 seconds: OK,
with seven skipped. The final focused pass completed 68 tests. Logs and the
independent final-disc audit are in `work/rico_scene_v4`.

The standalone audit passed both final images: every staged replacement matched
its manifest and on-disc payload. Only 16 resource payloads changed per disc
against `rico-dialogue-v3`; the remaining 3,712 Disc 1 and 3,707 Disc 2 payloads
were identical. All 17/12 opening XA movie resources were preserved. The boot
executable changed only in its verified embedded file-allocation table.
Suzarn's resource 499 was the only changed portrait: the other 18 custom and
72 native portrait resources were identical. Both guard upload paths and the
retail bed animation passed byte-level checks, as did the exact adult-Rico-only
initial progression delta.

The standalone `rico-ch2-scene-v4` release is active and its exact media and
source identities passed `project.py play rico --release rico-ch2-scene-v4
--check-only`. It was launched through that same CLI in the configured
DuckStation; boot and the opening movie were observed. The user took over
testing before Chapter 2's runtime scene acceptance, so the release remains
honestly marked `untested`. The temporary QA settings were restored
byte-for-byte with DuckStation closed before the user-facing launcher was
handed over. No user save or memory card was migrated or replaced.

Open the root `PLAY_RICO.cmd`, choose a fresh New Game, then select Chapter 2
to receive the revised initial stats. Old emulator save states retain their
resident executable, scripts and character records.
