# Mass Driver Dungeon 1.7 - v18 El-Regulus Ownership

Version 18 preserves the accepted v17 dungeon and Repair Bot shop correction.
It makes Elly's previously temporary Omnigear a persistent, normally
playable Gear and standardizes its English name as **El-Regulus**.

## Native Gear data

No new Gear model, animation set, battle command table, or statistics were
invented. Xenogears already contains a complete player Gear at ID 10:

- 17,000 HP and 6,600 fuel in the initialized GameState Gear record;
- field and world-map model resources;
- a native battle model and command/stat entry;
- the canonical battle-overlay label `EL-REGULUS`.

The engine gives each character one assigned Gear rather than maintaining a
Gear inventory. Elly's persistent `gearId` at GameState offset `0x03B0` is
therefore changed from Gear ID 2, Vierge, to Gear ID 10, El-Regulus. The
party's three ride-state bytes remain zero, so New Game still starts on foot.

## Name correction

Gear ID 10 uses GameState name slot 21. Version 18 replaces its old
reconstruction name with the exact ten-character string `El-Regulus`:

```text
24 48 13 31 41 43 51 48 51 4F
 E  l  -  R  e  g  u  l  u  s
```

The name is used by the normal Gear menu and dynamic dialogue-name controls.
The authored launch-support dialogue and reconstruction metadata use the same
spelling.

## Battle persistence

The launch-tube encounter still mounts Elly in Gear ID 10, removes Emeralda
and Citan only from the battle frame, and starts the fixed no-escape
two-Griffon battle. Its post-battle sequence now explicitly retains Gear ID
10 instead of restoring Vierge. It still performs the native battle
synchronization, dismounts Elly, restores both companions, and proceeds to
Central Control.

Because the assignment is part of GameState, a normal Xenogears save stores
it and reloads it. The initial GameState patch applies on a cold New Game;
old v17 hard saves keep their old name table until starting New Game, although
reaching and completing the v18 boss sequence upgrades Elly's Gear ID to 10.

## Build

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v18_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v18.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v18.cue
```

The built candidate is 690,368,448 bytes with SHA-256:

```text
d1a0c7719bfd46187377119fe189b849cd8b1ae3bc68cc7b44ca5bff3cf080a8
```

It passed 116 automated tests, 134 subtests, and a byte-for-byte extraction
comparison of all 37 injected resources. The extracted initial GameState
contains Gear ID `0A` at offset `0x03B0`, zero ride flags, and the exact
12-byte `El-Regulus` name slot.

## Runtime acceptance

Use a cold New Game rather than an old save state:

1. Open the main menu outside the Mass Driver and confirm Elly's Gear is
   named `El-Regulus`.
2. Confirm Elly and Emeralda still begin on foot.
3. Open the Repair Bot's Gear-parts menu, select Elly, and confirm
   El-Regulus accepts a normal equipment change.
4. Complete the launch authorization and enter the central gate.
5. Confirm the solo El-Regulus battle loads, its commands and animations
   work, and both Griffons can be defeated.
6. After returning to field 726, open the Gear menu and confirm El-Regulus
   remains assigned while Elly, Emeralda, and Citan are on foot.
7. Make a normal memory-card save, reload it, and confirm both the assignment
   and exact `El-Regulus` name persist.

The new BIN remains a runtime-test candidate until these checks are confirmed
in game.
