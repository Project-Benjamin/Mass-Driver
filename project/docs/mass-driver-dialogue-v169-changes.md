# Mass Driver V169 dialogue changes

9 authored files change: 16 existing blocks revised and 1 block added.

This compares the working V168 content saved immediately before the research implementation with the V169 authored sources. These are reconstruction edits, not recovered Square dialogue. The source snapshot is `work/mass_driver_research_implementation_20260916_baseline/snapshot.json`.

The [research ledger](research/xenogears-five-pass-2026-09-16/README.md) distinguishes released-game evidence, book material, and reconstruction choices. The [candidate notes](mass-driver-v169.md) cover sequence changes and validation.

## field_260_goliath_factory_hall

A short post-launch exchange resolves the promised return for Vierge and Crescens and acknowledges Citan going ahead. The return reuses the existing hall and boarding sequence.

### Block 7

Before:

```text
(New block.)
```

After:

```text
EMERALDA:

"There they are!"

----- next page -----

ELLY:

"Citan's gone on ahead.
Let's catch up."

[window closes]
```

## field_369_archive_annex

Mara asks who signed for Safety and requests their name in writing, making her resistance concrete.

### Block 1

Before:

```text
OPERATIONS DESK TERMINAL E
EXECUTIVE CIRCULAR / 6081
TO: DEFENSE FACILITIES
SUBJECT: CONTINUITY

----- next page -----

During a strategic alert,
local readiness must not be
delayed by civil review or
an absent safety officer.

----- next page -----

The Adviser's Office may
appoint temporary authority.
Orders issued this way retain
full legal force and shall be
filed as ordinary procedure.

----- next page -----

FROM: MARA / TO: LENA
If one office chooses who
fills every empty chair, the
safeguard is only a list of
names on the same order.

[window closes]
```

After:

```text
OPERATIONS DESK TERMINAL E
EXECUTIVE CIRCULAR / 6081
TO: DEFENSE FACILITIES
SUBJECT: CONTINUITY

----- next page -----

During a strategic alert,
local readiness must not be
delayed by civil review or
an absent safety officer.

----- next page -----

The Adviser's Office may
appoint temporary authority.
Orders issued this way retain
full legal force and shall be
filed as ordinary procedure.

----- next page -----

FROM: MARA / TO: LENA
Tell me who signed for
Safety. I want a copy with
their name on it.

[window closes]
```

## field_369_archive_control

The arrival and ready-status exchanges stop repeating the mission and distinguish ready machinery from Citan's remaining guidance check. Only blocks 0 and 12 change.

### Block 0

Before:

```text
ELLY:

"So... this is Central
Control."

----- next page -----

ELLY:

"These are the controls they
used to launch those
missiles..."

----- next page -----

EMERALDA:

"Taura capsule is here?"

----- next page -----

ELLY:

"It is secured to the
remaining launcher. The
console is just ahead."

----- next page -----

ELLY:

"Then let us finish what we
came here to do."

[window closes]
```

After:

```text
ELLY:

"Central Control...
At last."

----- next page -----

EMERALDA:

"Capsule ready?"

----- next page -----

ELLY:

"The cradle shows a payload.
Let's check the launch
console."

[window closes]
```

### Block 12

Before:

```text
NANOMACHINE CAPSULE SECURED
DIRECTIVE 0320 ACCEPTED
FOUR AUTHORITY POINTS VALID
PAYLOAD LINK CONFIRMED

----- next page -----

GUIDANCE POWER NOMINAL
MAGNETIC BANKS READY
ASCENT PATH AVAILABLE

----- next page -----

EMERALDA:

"Capsule goes into sky and
nanomachines spread all over
world?"

----- next page -----

ELLY:

"Yes. The Mass Driver should
carry it into the upper
atmosphere. There, they can
multiply and spread."

----- next page -----

ELLY:

"And remove the Limiter...
if Taura's calculations are
correct."

[window closes]
```

After:

```text
NANOMACHINE CAPSULE SECURED
DIRECTIVE 0320 ACCEPTED
FOUR AUTHORITY POINTS VALID
PAYLOAD LINK CONFIRMED

----- next page -----

GUIDANCE POWER NOMINAL
MAGNETIC BANKS READY
ASCENT PATH AVAILABLE

----- next page -----

EMERALDA:

"We can send it now?"

----- next page -----

ELLY:

"Not yet. Citan still has to
check the guidance."

[window closes]
```

## field_370_archive_annex

Mara asks Aron what sending two units to the clinics would cost, grounding their disagreement in a practical choice.

### Block 1

Before:

```text
OPERATIONS DESK TERMINAL F
CIVIL REQUEST / YEAR 6081
FROM: FEDERAL MEDICAL BUREAU
TO: FACILITY DIRECTOR

----- next page -----

Request release of two
standby generators to the
capital clinics. The central
grid cannot support surgery.

----- next page -----

REPLY: FACILITY DIRECTOR
All auxiliary units assigned
to strategic readiness.
Request denied by Command.

----- next page -----

FROM: MARA / TO: ARON
They say each weapon keeps
the clinics safe. Yet clinics
lose power while our queue
carries nothing that helps.

[window closes]
```

After:

```text
OPERATIONS DESK TERMINAL F
CIVIL REQUEST / YEAR 6081
FROM: FEDERAL MEDICAL BUREAU
TO: FACILITY DIRECTOR

----- next page -----

Request release of two
standby generators to the
capital clinics. The central
grid cannot support surgery.

----- next page -----

REPLY: FACILITY DIRECTOR
All auxiliary units assigned
to strategic readiness.
Request denied by Command.

----- next page -----

FROM: MARA / TO: ARON
Aron, check those two units.
What would we actually lose
by sending them to the
clinics?

[window closes]
```

## field_371_archive_annex

Emeralda decides that she wants to leave after the Kim record; Elly responds to her. This does not add a later identity revelation.

### Block 0

Before:

```text
ARCHIVE MAIL TERMINAL G
ACADEMIC REVIEW / 6077
SUBJECT: KIM PROPOSAL
MOLECULAR MACHINERY

----- next page -----

GENETIC RECONSTRUCTION VIA
MOLECULAR MACHINERY
Proposal judged heretical.
Author expelled from the
academic society.

----- next page -----

SPONSOR LICENSE / 6081
SPONSOR: MIANG
PRIME MINISTER'S ADVISER

----- next page -----

Private research facility
approved under executive
authority.

----- next page -----

FROM: MARA / TO: LENA
Four years ago the scholars
drove him out. Now the
Adviser has given him a
laboratory.

----- next page -----

I want Kim to have it.
I only wish I knew what she
wanted from him.

----- next page -----

SECURITY ADDENDUM / 6083
GOVERNMENT SPECIAL FORCES
ENTERED RESEARCH FACILITY

----- next page -----

ASSAULT UNIT: NO RESPONSE
KIM: NOT RECOVERED
NANOMACHINE COLONY: NOT FOUND

----- next page -----

EMERALDA:

"Kim..."

----- next page -----

ELLY:

"Let us go, Emeralda."

[window closes]
```

After:

```text
ARCHIVE MAIL TERMINAL G
ACADEMIC REVIEW / 6077
SUBJECT: KIM PROPOSAL
MOLECULAR MACHINERY

----- next page -----

GENETIC RECONSTRUCTION VIA
MOLECULAR MACHINERY
Proposal judged heretical.
Author expelled from the
academic society.

----- next page -----

SPONSOR LICENSE / 6081
SPONSOR: MIANG
PRIME MINISTER'S ADVISER

----- next page -----

Private research facility
approved under executive
authority.

----- next page -----

FROM: MARA / TO: LENA
Four years ago the scholars
drove him out. Now the
Adviser has given him a
laboratory.

----- next page -----

I want Kim to have it.
I only wish I knew what she
wanted from him.

----- next page -----

SECURITY ADDENDUM / 6083
GOVERNMENT SPECIAL FORCES
ENTERED RESEARCH FACILITY

----- next page -----

ASSAULT UNIT: NO RESPONSE
KIM: NOT RECOVERED
NANOMACHINE COLONY: NOT FOUND

----- next page -----

EMERALDA:

"Kim...
I want to go, Elly."

----- next page -----

ELLY:

"...All right."

[window closes]
```

## field_385_storage_treasure_annex

Lena commits to keeping the weather package on the public manifest, connecting her response to the preceding correspondence.

### Block 2

Before:

```text
CIVIL PAYLOAD STORES / 6079
FROM: LENA / GUIDANCE
TO: FACILITY DIRECTOR

----- next page -----

The Assembly restored one
carrier appropriation. The
condition is a Defense seat
on every launch review.

----- next page -----

Strategic Command calls it
shared oversight. Their draft
gives them first claim on the
rail and every cargo bay.

----- next page -----

REPLY: FACILITY DIRECTOR
This accelerator was built
to send instruments outward,
not weapons over the horizon.

----- next page -----

Keep the weather package and
survey carrier on the public
manifest. No sealed military
payload enters these stores.

----- next page -----

FORWARDED: ADVISER'S OFFICE
Civil funding remains subject
to emergency requirements.
Prepare a dual-use schedule.

----- next page -----

FROM: LENA / TO: MARA
They can starve the launch
program, then call acceptance
our only way to save it.

[window closes]
```

After:

```text
CIVIL PAYLOAD STORES / 6079
FROM: LENA / GUIDANCE
TO: FACILITY DIRECTOR

----- next page -----

The Assembly restored one
carrier appropriation. The
condition is a Defense seat
on every launch review.

----- next page -----

Strategic Command calls it
shared oversight. Their draft
gives them first claim on the
rail and every cargo bay.

----- next page -----

REPLY: FACILITY DIRECTOR
This accelerator was built
to send instruments outward,
not weapons over the horizon.

----- next page -----

Keep the weather package and
survey carrier on the public
manifest. No sealed military
payload enters these stores.

----- next page -----

FORWARDED: ADVISER'S OFFICE
Civil funding remains subject
to emergency requirements.
Prepare a dual-use schedule.

----- next page -----

FROM: LENA / TO: MARA
The weather package is still
on the public manifest.
I will keep it there as long
as they let me.

[window closes]
```

## field_394_defense_archive

The archive explicitly labels its 6081 report and its separate 6083 emergency recording. Shorter report pages retain the social conditions while reducing repetition; playback/menu behavior is unchanged.

### Block 24

Before:

```text
VIDEO DISK ACCEPTED
ZBC EVENING REPORT ARCHIVE

----- next page -----

PLAYBACK STARTING...

[window closes]
```

After:

```text
VIDEO DISK ACCEPTED
ZBC NEWS ARCHIVE
RECORDINGS: 6081-6083

----- next page -----

PLAYBACK STARTING...

[window closes]
```

### Block 25

Before:

```text
Even as public markets empty,
private dining rooms in the
wealthiest districts remain
fully supplied.

----- next page -----

Aid groups asked their owners
to release food and fuel.
Most refused.

----- next page -----

Guarded restaurants now
overlook streets where
families wait for rations.

----- next page -----

For many outside, these rooms
have become symbols of a
crisis the rich can purchase
their way around.

[window closes]
```

After:

```text
Public markets have little
left to sell, but private
dining rooms in the wealthy
districts remain supplied.

----- next page -----

Aid groups asked the owners
to release food and fuel.
Most refused.

[window closes]
```

### Block 26

Before:

```text
Some of the nation's richest
families are commissioning
and purchasing private
fallout shelters.

----- next page -----

Builders advertise dining
rooms, gardens, clinics, and
years of private supplies.

----- next page -----

Asked to open those supplies
to families in food lines,
most owners have refused.

----- next page -----

Their money buys safety below
ground while the public is
left to face hunger and fear
above.

[window closes]
```

After:

```text
Some of the nation's richest
families are buying private
fallout shelters.

----- next page -----

Builders advertise gardens,
clinics, and enough supplies
to last for years.

[window closes]
```

### Block 27

Before:

```text
Nationwide, food lines now
begin before dawn.

----- next page -----

Farms stand abandoned, and
rail shipments no longer
reach the poorest districts.

----- next page -----

Children wait in the cold as
emergency stores run dry.

----- next page -----

Aid groups warn that hunger
will soon be impossible to
contain.

[window closes]
```

After:

```text
Nationwide, food lines begin
before dawn. Children wait
in the cold as emergency
stores run dry.

----- next page -----

Farms stand abandoned. Rail
shipments no longer reach
the poorest districts.

[window closes]
```

### Block 28

Before:

```text
That refusal has ignited open
violence across the capital.

----- next page -----

Crowds from poorer districts
are burning wealthy homes.
Some have killed the families
found inside.

----- next page -----

Police and military units
have abandoned three affluent
districts to the crowds.

----- next page -----

More fires are spreading as
retaliation gives way to
indiscriminate violence.

[window closes]
```

After:

```text
Violence is spreading across
the capital.

----- next page -----

Crowds from poorer districts
have burned wealthy homes.
Families have been killed
inside.

----- next page -----

Police and military units
have abandoned three wealthy
districts. More fires are
being reported.

[window closes]
```

### Block 29

Before:

```text
Behind this crisis lies a
longer population collapse.

----- next page -----

Births have fallen below the
replacement rate for a
twelfth straight year.

----- next page -----

Infertility and hereditary
illness continue to rise.
Life expectancy nears thirty.

----- next page -----

Officials privately warn that
the nation may not survive
another generation.

[window closes]
```

After:

```text
Births have fallen below the
replacement rate for twelve
consecutive years.

----- next page -----

Infertility and hereditary
illness continue to rise.
Life expectancy nears thirty.

----- next page -----

Officials privately warn that
the nation may not survive
another generation.

[window closes]
```

### Block 30

Before:

```text
We interrupt this report.
A nuclear missile has been
launched.

----- next page -----

Multiple nuclear-armed states
have begun retaliation.
Command links are failing.

----- next page -----

If this signal reaches you,
find shelter immediately.
This is not a drill.

[window closes]
```

After:

```text
ZBC ARCHIVE / NEXT RECORDING
EMERGENCY BROADCAST / 6083

----- next page -----

We interrupt this report.
A nuclear missile has been
launched.

----- next page -----

Multiple nuclear-armed states
have begun retaliation.
Command links are failing.

----- next page -----

If this signal reaches you,
find shelter immediately.
This is not a drill.

[window closes]
```

### Block 35

Before:

```text
ZBC EVENING REPORT / 6081
CELIA REN, ANCHOR

----- next page -----

Good evening. Tonight, food
lines are lengthening while
the wealthiest buy a private
path to survival.

----- next page -----

Years of falling birth rates
have weakened the country,
and refusal to share has
turned resentment into deadly
violence.

----- next page -----

We begin in the capital,
where the divide is visible
from every street.

[window closes]
```

After:

```text
ZBC EVENING REPORT / 6081
CELIA REN, ANCHOR

----- next page -----

Good evening. Food shortages
continue across the capital,
where unrest has turned
violent.

[window closes]
```

## field_673_silo_vault_3

Aron explicitly distinguishes restoring electrical power from reconnecting the missile target link.

### Block 0

Before:

```text
RESERVE MAGAZINE 03 / 05
RECOVERED MAIL / ARON

----- next page -----

Target network lost.
I cut the link before
evacuation. If restored,
leave it that way.

----- next page -----

I have followed enough
orders.

----- next page -----

ELLY:

"The cradles still draw
power. We should keep our
distance."

[window closes]
```

After:

```text
RESERVE MAGAZINE 03 / 05
RECOVERED MAIL / ARON

----- next page -----

I cut the target link
before evacuation. If you
restore power, leave the
link disconnected.

----- next page -----

I have followed enough
orders.

----- next page -----

ELLY:

"The cradles still draw
power. We should keep our
distance."

[window closes]
```

## field_724_archive_annex

Lena recalls the probe conversation consistently with the earlier record: they would have to send it and see. Mira's fate remains unknown.

### Block 0

Before:

```text
ARCHIVE MAIL TERMINAL H
STAFF MAIL / YEAR 6083
FROM: ARON / SYSTEMS
TO: LENA / GUIDANCE

----- next page -----

SUBJECT: MIRA

----- next page -----

The warning net reports
launches from three commands.
Half the stations disagree.
No one here knows what is
real. Our countdown started.

----- next page -----

Bank Four will not accept a
local abort. I told you
readiness would keep them
from firing. I was wrong.

----- next page -----

If you can reach Mira,
take her below.
Do not wait for me.

----- next page -----

AUTOMATED LAUNCH LOG
STRATEGIC RELEASE CONFIRMED
COUNTERSTRIKES DETECTED
GUIDANCE NETWORK LOST
RESERVE MAGAZINES SEALED

----- next page -----

UNSENT DRAFT
FROM: LENA / TO: MIRA
If this reaches you...
Do you remember asking what
the probe would find?

----- next page -----

I told you something
wonderful. I am sorry, Mira.
I wanted to be right.

----- next page -----

EMERALDA:

"What happened to Mira...?"

----- next page -----

ELLY:

"I don't know..."

[window closes]
```

After:

```text
ARCHIVE MAIL TERMINAL H
STAFF MAIL / YEAR 6083
FROM: ARON / SYSTEMS
TO: LENA / GUIDANCE

----- next page -----

SUBJECT: MIRA

----- next page -----

The warning net reports
launches from three commands.
Half the stations disagree.
No one here knows what is
real. Our countdown started.

----- next page -----

Bank Four will not accept a
local abort. I told you
readiness would keep them
from firing. I was wrong.

----- next page -----

If you can reach Mira,
take her below.
Do not wait for me.

----- next page -----

AUTOMATED LAUNCH LOG
STRATEGIC RELEASE CONFIRMED
COUNTERSTRIKES DETECTED
GUIDANCE NETWORK LOST
RESERVE MAGAZINES SEALED

----- next page -----

UNSENT DRAFT
FROM: LENA / TO: MIRA
If this reaches you...
Do you remember asking what
the probe would find?

----- next page -----

I told you we would have to
send it and see. I wanted
to show you something
wonderful. I am sorry, Mira.

----- next page -----

EMERALDA:

"What happened to Mira...?"

----- next page -----

ELLY:

"I don't know..."

[window closes]
```

## Protected content

Central Control blocks 21–34 and 36 are unchanged as complete authored objects, including text, control tags, window dimensions, and wrapping. The independent generated comparison additionally checks every protected compiled block and every non-dialogue component against the saved baseline. No dormant memory explanations were enabled.
