# Rico dialogue and Suzarn portrait correction

This revision follows the user's playtest of `rico-ch2-scene-v4`. The user
approved Fei's infirmary staging and rejected the dialogue. They also identified
Suzarn's headgear correctly as a helmet and goggles; the earlier portrait's
swept-hair interpretation was wrong.

The infirmary exchange is now a medical handoff. The attendant asks how long
Fei has been unconscious and whether he woke during transport, observes his
breathing, and accepts his care. The escort supplies the little information
available and passes on custody instructions. Fei remains silent and in bed.
The next scene starts four days later, following the recovery interval in
retail field 213.

In the Champion's rooms, Suzarn brings the next bout card, Rico checks Stier's
readiness, and Hammer reports that Fei has woken. Their exchange establishes
Hammer's contact with Fei and Rico's interest in the unknown Gear pilot.
Hammer objects to bringing someone fresh out of the infirmary to the yard;
Rico overrides him. This keeps the coming Baptism coercive. The earlier food
orders, conflicting meeting destinations, landing remark, and gate-key speech
are removed.

The Baptism dialogue now answers Fei's protest directly. It no longer tells
the group to go outside when they are already in the yard, or narrates Rico
walking away when the actor remains in place. These are text corrections;
the approved actor staging, cameras, bed animation and guard graphics remain
unchanged.

Suzarn's corrected portrait must represent the native helmet, conspicuous
goggles, red lower-face/neck cloth, dark upper garment and a dark bomb collar
with separated rectangular lights. The only portrait
resource allowed to change is 499 (selector 37). All other portraits and the
protected Mass Driver, Miang and Soylent content must remain unchanged.

Rico's level-24 new-game profile remains in place. Existing save states are
not migrated. Use the current Rico launcher, choose New Game and Chapter 2.

Final build, source, native-disc and test evidence is recorded in
`work/rico_dialogue_v6`. Runtime acceptance beyond the user's approved v4
infirmary staging must be reported separately from those automated checks.

On September 6, 2026, `rico-dialogue-v6` was built and activated for the Rico
profile after the launcher rejected the stale v4 release. The full profile
suite passed: 1,035 tests in 332.227 seconds, with seven skipped. Both discs
passed the native audit; all 87 staged replacements match the packaged bytes.
The approved staging, guard graphics, bed animation, level-24 starting state
and 90 other portraits remain unchanged.

The default `project.py play rico --check-only` passed. The user-facing
`Play Rico.cmd` then exited successfully and opened the verified v6 playlist
in DuckStation; the running process and visible Squaresoft boot screen were
observed. Gameplay acceptance remains untested. No controller settings,
memory cards or existing save states were changed for this launch.

The larger Rico-only Chapter 2 restructuring in `rico-chapter-02-pov-plan.md`
remains a proposal and is not part of this release.
