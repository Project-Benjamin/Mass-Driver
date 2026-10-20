# Mass Driver V170 dialogue changes

These are changes to the mod's authored V169 text, following the approved final review. No recovered Square draft is implied. The Central Control script and protected memory are preserved.

## field_369_archive_control.authored.json

[Authored source](../modules/mass_driver/content/field_369_archive_control.authored.json)

### Block 0

**V169**

```text
<Elly>
"Central Control...
At last."

--- next page ---

<Emeralda>
"Capsule ready?"

--- next page ---

<Elly>
"The cradle shows a payload.
Let's check the launch
console."
[window closes]
```

**V170**

```text
<Elly>
"Central Control..."

--- next page ---

<Emeralda>
"Elly... the console."

--- next page ---

<Elly>
"Let's take a look."
[window closes]
```

## field_394_defense_archive.authored.json

[Authored source](../modules/mass_driver/content/field_394_defense_archive.authored.json)

### Block 6

**V169**

```text
DIRECTIVE 0320 ACCEPTED
AUTHORITY A-2 ACCEPTED
AUTHORITY B-5 ACCEPTED
AUTHORITY C-8 ACCEPTED
AUTHORITY D-4 ACCEPTED

--- next page ---

LAUNCH AUTHORITY RECORDED
DEFENSE BAY LIFT UNLOCKED
NORTH WALL ACCESS AVAILABLE
CUSTODIAN REVIEW BELOW

--- next page ---

<Elly>
"Our Gears should be in the
bay below. Let's use the
north lift."
[window closes]
```

**V170**

```text
DIRECTIVE 0320 ACCEPTED
AUTHORITY A-2 ACCEPTED
AUTHORITY B-5 ACCEPTED
AUTHORITY C-8 ACCEPTED
AUTHORITY D-4 ACCEPTED

--- next page ---

LAUNCH AUTHORITY RECORDED
DEFENSE BAY LIFT UNLOCKED
NORTH WALL ACCESS AVAILABLE
CUSTODIAN DEFENSE ACTIVE

--- next page ---

<Elly>
"Our Gears should be in the
bay below."

--- next page ---

<Elly>
"The defense system is still
active. Let's check our
equipment before we go down."
[window closes]
```

### Block 39

**V169**

New menu/status block.

**V170**

```text
<Opcode:01:FF>WEST BULKHEAD CONTROL
     Operate bulkhead
     Read archived report
     Leave
[window closes]
```

### Block 40

**V169**

New menu/status block.

**V170**

```text
CUSTODIAN DEFENSE ACTIVE
BULKHEAD RELEASE LOCKED
[window closes]
```

### Block 41

**V169**

New menu/status block.

**V170**

```text
WEST BULKHEAD OPEN
[window closes]
```

## Research archive: block 0, final page

[Authored source](../modules/mass_driver/content/field_373_control_research_annex.authored.json). The rest of this block is unchanged. The old instruction could appear after auxiliary power was already restored.

**V169**

```text
<Elly>
"The floor controls only
operate the Auxiliary Grid.
We should restore it now."
```

**V170**

```text
<Elly>
"The floor controls only
operate the Auxiliary Grid.
The accelerator banks have
a separate interlock."
```

## Event changes

- Surface field 729 skips its mission briefing when the existing launch-completed flag is set; its lower-lift return exception remains.
- The west-panel menu separates door operation from report 19. Reading the report returns to the menu; Leave returns control; only Operate can run the existing guarded opening.
- Authorization success includes the preparation warning before the existing Guardian approach trigger.
