# Mass Driver Dungeon 2.3 - v24 El-Regulus Combat Test

> Historical v24 test build. Superseded by the v25 normal-combat correction.
> Version 24 inherited Perfect Works Story Mode combat data and does not
> represent normal enemy balance.

Version 24 preserves the accepted standalone dungeon, native Mass Driver
entrance, El-Regulus ownership, menu models, and v23 world-map animation. It
adds a repeatable native random battle near the Mass Driver and corrects the
unused El-Regulus battle-entry animation so the encounter can be played from
command selection through victory and world-map return.

## World-map encounter

The retail Mass Driver exterior resolves to world-map encounter table 12,
scenario row 2. Formation slot 0 in that row is one native Gear-scale
Tusk-Tusk, making it a contained opponent for testing El-Regulus without
changing a field formation or importing a new enemy.

Canonical Disc 2 file 37 is the packed world-map control overlay. Version 24
changes exactly three bytes after decompression:

| Decoded offset | Retail instruction | v24 instruction | Purpose |
|---|---|---|---|
| `0x5780` | `00 00 02 24` | `01 00 02 24` | Initialize one native encounter countdown slot |
| `0x6584` | `08 95 29 A0` | `08 95 20 A0` | Select formation slot 0 consistently |
| `0x210A4` | `20 00 42 30` | `60 00 42 30` | Accept X/Cross while preserving retail Circle |

The builder checks the surrounding retail instructions before applying each
edit, limits the encounter-slot count to the engine's native range of 0
through 16, recompresses the overlay, and verifies this packed SHA-256:

```text
94ccdb23e021939fab22b8f71586ced257413f2ed9ba2723e74f5e34ee606110
```

The encounter uses the normal world-map party-state handoff. If Elly mounts
El-Regulus first, she enters and returns mounted. The standalone New Game
state intentionally continues to start the party on foot. The one-slot
control setting is global to this standalone world map rather than fenced to
coordinates; outside the Mass Driver start area, the current area's native
table supplies its own slot-0 formation.

## El-Regulus battle-entry correction

Gear ID 10 already has its native battle model, stats, equipment, commands,
and attack animations. Its otherwise unused player-entry sequence in
canonical Disc 2 file 2960 did not finish when the Gear occupied a party
slot. The battle loader therefore waited forever before enabling the HUD.

The loader initializes animation 0 and then arms the Gear's animation
completion flag. Clearing that flag immediately inside initialization is too
early because the loader writes it back afterward. Version 24 replaces the
audited animation-0 tail at file offset `0x71D6`:

```text
retail:  11 FF 00 01 00 00
v24:     21 00 6D 00 00 00
```

Mecha opcode `0x0021` yields during the initialization pass. On the first
normal animation update, opcode `0x006D` clears the completion flag after the
loader has armed it, and the existing terminator ends the sequence. Only the
first four bytes of that six-byte tail change; battle geometry, attacks,
later animations, menus, equipment, and world-map art remain untouched.

```text
canonical ID:       2960
retail size:        31,808 bytes
retail SHA-256:     8ccee45222b6245fdcb4556ce15f69746bf5e2ebd88ec76aa77ec4381ab07d6d
v24 SHA-256:        82ab71b4320c1303ffcbbac15f70a4438432a62a1dc8d90dd03cffa23e665e18
```

## Build

Canonical 2960 must be available as
`work/_audit_el_regulus_battle/2960.bin` in addition to the v23 inputs.

```powershell
python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v24_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v24.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v24.cue
```

The rebuilt BIN is 690,375,504 bytes with SHA-256:

```text
78781c6834a88a6e1a80a25acff749a9b986eceb332c4d569468a2574a638053
```

It passed 122 automated tests, 139 subtests, and an exact extraction
comparison of all 41 injected resources.

## Runtime acceptance

A cold DuckStation test used natural movement to start the Tusk-Tusk
encounter. El-Regulus displayed 17,000 HP, 6,600 fuel, and its native Gear
command wheel. The Item command opened and canceled normally, El-Regulus
completed an attack, the victory screen appeared, and the game returned to
the Mass Driver exterior with Elly still mounted.

For manual acceptance:

1. Start `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Open the world-map Gear menu and tell Elly to get into El-Regulus.
3. Keep moving near the Mass Driver until the Tusk-Tusk encounter starts.
4. Confirm the Gear command HUD appears and commands can be opened, canceled,
   and selected.
5. Attack or Escape and confirm the game returns to the same exterior area
   with Elly still mounted.
6. Approach the Mass Driver label and press X/Cross to confirm the dungeon
   entrance remains available.
