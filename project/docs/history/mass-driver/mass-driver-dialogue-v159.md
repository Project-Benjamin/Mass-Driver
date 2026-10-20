# Mass Driver V159 dialogue and source provenance

> Generated from the frozen active build. This transcript covers the Mass Driver standalone route, not the untouched retail Xenogears Disc 2 script outside that route.

## Scope and provenance

- Active dialogue-bearing fields: **33**
- Authored source files used by V159: **33**
- Tracked custom-dialogue JSON sources: **57** (33 active authored, 16 inactive authored, 8 legacy replacement-schema)
- Dialogue blocks: **176**
- Text pages (`<New>` delimited): **446**
- Compiled dialogue bytes: **30,868**
- Source-to-stage recompilation: **all active sources verified byte-for-byte**
- Tagged speaker cues: Elly **60**, Emeralda **26**, Citan **3**

Every transcript line below comes from the linked `*.authored.json` file. Each of those files is explicitly marked `reconstruction: true`. The listed retail field is the room/script donor used to construct the playable field; it is **not** a claim that the custom wording was copied from retail dialogue.

Control tags are rendered as follows: `<New>` becomes `next page`, `<Close>` becomes `window closes`, speaker tags become uppercase labels, and opcode/delay tags remain visible in square brackets.
A status of `compiled` means the block is present in the release dialogue component; it does not imply that every conditional branch is encountered during one playthrough. Central Control has an additional exhaustive static reference classification: `statically reachable` means an emitted VM path can reach the block under some valid flag/input state, not that a human test traversed it.

### Release source ledger

- Stage manifest: `work/mass_driver_v159_stage/manifest.json` - `f6aa96575db50a4a90a39036c072e29e777c0d28d00841868d3d4ce762700020`
- Reconstruction metadata: [reconstruction_metadata.json](../../../content/mass_driver_v2/reconstruction_metadata.json) - `7bf60528d4f8b63d5994ea4a2e7d672c5c90b67813eaa8d1e35a5a49fb739692`
- Builder mapping: [build_mass_driver_dungeon.py](../../../tools/build_mass_driver_dungeon.py) - `58983890b007c0cbda31adf7342098c0816063abde58336f202b9b3db7b9e77f`

## Active field index

| Route | V159 field | Room | Retail donor | Blocks / pages | Text source | Compiled dialogue |
|---:|---:|---|---:|---:|---|---|
| 1 | 729 | Zeboim inclined surface lift | 361 | 9 / 17 | [field_361_zeboim_access_tunnel.authored.json](../../../content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json) | 839 bytes `5a1555d220f7...` |
| 2 | 364 | Zeboim inclined-lift lower landing | 362 | 1 / 2 | [field_362_inclined_service_tunnel.authored.json](../../../content/mass_driver_v2/field_362_inclined_service_tunnel.authored.json) | 89 bytes `44207e30fc4a...` |
| 3 | 360 | Lighthouse curved employee transit tunnel | 398 | 1 / 1 | [field_398_curved_transit_tunnel.authored.json](../../../content/mass_driver_v2/field_398_curved_transit_tunnel.authored.json) | 46 bytes `552133bab0a6...` |
| 4 | 720 | Lighthouse coastal utility tunnel | 399 | 1 / 2 | [field_399_lighthouse_utility_tunnel.authored.json](../../../content/mass_driver_v2/field_399_lighthouse_utility_tunnel.authored.json) | 81 bytes `d7db0404c999...` |
| 5 | 721 | Lighthouse abandoned Zeboim subway terminus | 397 | 4 / 12 | [field_397_subway_end.authored.json](../../../content/mass_driver_v2/field_397_subway_end.authored.json) | 802 bytes `9ac63fd3538e...` |
| 6 | 363 | Zeboim launch-works service junction | 363 | 5 / 8 | [field_363_zeboim_service_junction.authored.json](../../../content/mass_driver_v2/field_363_zeboim_service_junction.authored.json) | 428 bytes `6985668e75e0...` |
| 7 | 362 | Zeboim personnel transfer airlock | 376 | 5 / 5 | [field_376_transfer_airlock.authored.json](../../../content/mass_driver_v2/field_376_transfer_airlock.authored.json) | 209 bytes `771a281f673f...` |
| 8 | 727 | Zeboim three-door operations junction | 377 | 5 / 8 | [field_377_inner_access.authored.json](../../../content/mass_driver_v2/field_377_inner_access.authored.json) | 387 bytes `167bb35a56c6...` |
| 9 | 372 | Zeboim four-door service hub | 372 | 9 / 15 | [field_372_service_hub.authored.json](../../../content/mass_driver_v2/field_372_service_hub.authored.json) | 992 bytes `523f8850a8e3...` |
| 10 | 361 | Zeboim control and research annex | 373 | 2 / 17 | [field_373_control_research_annex.authored.json](../../../content/mass_driver_v2/field_373_control_research_annex.authored.json) | 1,387 bytes `980551a72dd7...` |
| 11 | 722 | Zeboim materials storage annex | 374 | 9 / 22 | [field_374_storage_annex.authored.json](../../../content/mass_driver_v2/field_374_storage_annex.authored.json) | 1,799 bytes `2a12d6235fba...` |
| 12 | 723 | Zeboim sealed stair connector | 375 | 5 / 9 | [field_375_service_connector.authored.json](../../../content/mass_driver_v2/field_375_service_connector.authored.json) | 545 bytes `80f6b4b331f6...` |
| 13 | 375 | Zeboim post-auxiliary sealed stair connector | 375 | 5 / 9 | [field_375_post_aux_stair.authored.json](../../../content/mass_driver_v2/field_375_post_aux_stair.authored.json) | 545 bytes `80f6b4b331f6...` |
| 14 | 387 | Zeboim vertical service connector | 387 | 1 / 1 | [field_387_vertical_connector.authored.json](../../../content/mass_driver_v2/field_387_vertical_connector.authored.json) | 51 bytes `b7c1070c01d1...` |
| 15 | 725 | Zeboim magnetic conduit hall | 385 | 2 / 3 | [field_385_magnetic_conduit.authored.json](../../../content/mass_driver_v2/field_385_magnetic_conduit.authored.json) | 153 bytes `647495ef6e49...` |
| 16 | 726 | Zeboim launch-support hall | 384 | 5 / 11 | [field_384_launch_support.authored.json](../../../content/mass_driver_v2/field_384_launch_support.authored.json) | 571 bytes `4eaad7c53c09...` |
| 17 | 366 | Zeboim launch-support archive A | 378 | 2 / 10 | [field_366_archive_annex.authored.json](../../../content/mass_driver_v2/field_366_archive_annex.authored.json) | 1,016 bytes `c5e3c781b8da...` |
| 18 | 367 | Zeboim archive-branch operations junction | 377 | 1 / 1 | [field_367_archive_junction.authored.json](../../../content/mass_driver_v2/field_367_archive_junction.authored.json) | 105 bytes `e35f3e204abe...` |
| 19 | 385 | Zeboim civil-payload stores | 374 | 3 / 9 | [field_385_storage_treasure_annex.authored.json](../../../content/mass_driver_v2/field_385_storage_treasure_annex.authored.json) | 790 bytes `b8fbffffe788...` |
| 20 | 386 | Zeboim strategic-payload stores | 374 | 3 / 8 | [field_386_storage_treasure_annex.authored.json](../../../content/mass_driver_v2/field_386_storage_treasure_annex.authored.json) | 577 bytes `f3ed00a4584c...` |
| 21 | 368 | Zeboim launch-support archive C | 378 | 2 / 8 | [field_368_archive_annex.authored.json](../../../content/mass_driver_v2/field_368_archive_annex.authored.json) | 672 bytes `fb0c59b3d375...` |
| 22 | 369 | Zeboim launch-support archive D | 378 | 2 / 12 | [field_369_archive_annex.authored.json](../../../content/mass_driver_v2/field_369_archive_annex.authored.json) | 1,031 bytes `8fcf2877ad39...` |
| 23 | 370 | Zeboim launch-support archive E | 378 | 2 / 9 | [field_370_archive_annex.authored.json](../../../content/mass_driver_v2/field_370_archive_annex.authored.json) | 1,025 bytes `7f638cb5bc01...` |
| 24 | 371 | Zeboim launch-support archive F | 378 | 2 / 15 | [field_371_archive_annex.authored.json](../../../content/mass_driver_v2/field_371_archive_annex.authored.json) | 1,177 bytes `29a35967240f...` |
| 25 | 724 | Zeboim launch-support archive G | 378 | 2 / 15 | [field_724_archive_annex.authored.json](../../../content/mass_driver_v2/field_724_archive_annex.authored.json) | 1,233 bytes `5c1ab3417dbb...` |
| 26 | 376 | Zeboim autonomous-defense archive | 394 | 39 / 104 | [field_394_defense_archive.authored.json](../../../content/mass_driver_v2/field_394_defense_archive.authored.json) | 7,200 bytes `3eadb9b8fafc...` |
| 27 | 384 | Goliath Factory Gear staging and Guardian hall | 260 | 7 / 17 | [field_260_goliath_factory_hall.authored.json](../../../content/mass_driver_v2/field_260_goliath_factory_hall.authored.json) | 1,017 bytes `168bf7a52807...` |
| 28 | 377 | Containment vault 1 of 5 | 673 | 1 / 4 | [field_673_silo_vault_1.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_1.authored.json) | 236 bytes `58fdde3162c1...` |
| 29 | 378 | Containment vault 2 of 5 | 673 | 1 / 10 | [field_673_silo_vault_2.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_2.authored.json) | 736 bytes `fd19f01c182c...` |
| 30 | 379 | Containment vault 3 of 5 | 673 | 1 / 4 | [field_673_silo_vault_3.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_3.authored.json) | 238 bytes `5910fc39a0cc...` |
| 31 | 382 | Containment vault 4 of 5 | 673 | 1 / 4 | [field_673_silo_vault_4.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_4.authored.json) | 205 bytes `c4972f164662...` |
| 32 | 383 | Containment vault 5 of 5 | 673 | 1 / 4 | [field_673_silo_vault_5.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_5.authored.json) | 238 bytes `5ca5d9105a71...` |
| 33 | 728 | Zeboim Mass Driver central control | 369 | 37 / 70 | [field_369_archive_control.authored.json](../../../content/mass_driver_v2/field_369_archive_control.authored.json) | 4,448 bytes `131de29fa2c1...` |

## Complete active transcript

### 01. Field 729 - Zeboim inclined surface lift

- Dialogue text source: [field_361_zeboim_access_tunnel.authored.json](../../../content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json)
- Source SHA-256: `eb579adea39c3c8c08d35d7187c5a37295e1ae43a347dad68218d5450d4744d4`
- Retail room/script donor: field **361**, canonical bundle **1328**
- V159 destination: field **729**, canonical bundle **2064**
- Compiled component: `work/mass_driver_v159_stage/clones/field_729/07_dialogue.bin`, 839 bytes, `5a1555d220f7fb21a64dac23e052a5bc10f4c4b265d66158a2a9b2272595a09c`
- Inventory: **9 blocks / 17 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"So... this is the
Mass Driver."

----- next page -----

EMERALDA:

"Still awake...?"

----- next page -----

ELLY:

"Taura was right.
There is power here."

----- next page -----

ELLY:

"If we can reach Central
Control, the launcher can
carry his capsule into the
upper atmosphere."

----- next page -----

EMERALDA:

"Then nanomachines spread
all over world?"

----- next page -----

ELLY:

"Yes... and release the
Limiter's seal."

----- next page -----

ELLY:

"Taura's crew found another
shaft near the control wing.
They moved our Gears into
the bay below."

----- next page -----

EMERALDA:

"Then we find Gears!"

----- next page -----

ELLY:

"Yes. Let us find a way
inside."

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"The controls should be
somewhere below us.
Let us look for a directory."

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json -> blocks[id=2]`
- Window: 50 x 4; manual wrap: no
- Status: compiled into V159

```text
EMERALDA:

"Even after all this time...
the old lift still moves."

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json -> blocks[id=3]`
- Window: 30 x 2; manual wrap: no
- Status: compiled into V159

```text
SURFACE ACCESS LIFT
DESCENT CIRCUIT ACTIVE

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json -> blocks[id=4]`
- Window: 50 x 4; manual wrap: no
- Status: compiled into V159

```text
LIFT CONTROL
LOWER LANDING SELECTED

[window closes]
```

#### Block 5

- Source locator: `content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json -> blocks[id=5]`
- Window: 48 x 4; manual wrap: no
- Status: compiled into V159

```text
CAUTION
Stand clear of the platform edge.

[window closes]
```

#### Block 6

- Source locator: `content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json -> blocks[id=6]`
- Window: 46 x 1; manual wrap: no
- Status: compiled into V159

```text
AUTHORIZED PERSONNEL ONLY

[window closes]
```

#### Block 7

- Source locator: `content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json -> blocks[id=7]`
- Window: 46 x 2; manual wrap: no
- Status: compiled into V159

```text
LIFT IN MOTION
KEEP CLEAR

[window closes]
```

#### Block 8

- Source locator: `content/mass_driver_v2/field_361_zeboim_access_tunnel.authored.json -> blocks[id=8]`
- Window: 46 x 1; manual wrap: no
- Status: compiled into V159

```text
AUTHORIZED PERSONNEL ONLY

[window closes]
```

### 02. Field 364 - Zeboim inclined-lift lower landing

- Dialogue text source: [field_362_inclined_service_tunnel.authored.json](../../../content/mass_driver_v2/field_362_inclined_service_tunnel.authored.json)
- Source SHA-256: `c82f8a3404bd3639bd9fb7743707269bab56ef7f70e59442d35310677088b644`
- Retail room/script donor: field **362**, canonical bundle **1330**
- V159 destination: field **364**, canonical bundle **1334**
- Compiled component: `work/mass_driver_v159_stage/clones/field_364/07_dialogue.bin`, 89 bytes, `44207e30fc4a93b6b6a6357d7111f3e8c17e880cf00881783fb503dcce71939b`
- Inventory: **1 blocks / 2 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_362_inclined_service_tunnel.authored.json -> blocks[id=0]`
- Window: 54 x 4; manual wrap: no
- Status: compiled into V159

```text
INCLINED TRANSIT LIFT
LOWER TERMINAL

----- next page -----

CREW ACCESS LEVEL
AUTHORIZED PERSONNEL ONLY

[window closes]
```

### 03. Field 360 - Lighthouse curved employee transit tunnel

- Dialogue text source: [field_398_curved_transit_tunnel.authored.json](../../../content/mass_driver_v2/field_398_curved_transit_tunnel.authored.json)
- Source SHA-256: `3989b46082211c1f5fcd81e28f39edb5088687da2b72d6b5f3ec513f32e5d515`
- Retail room/script donor: field **398**, canonical bundle **1402**
- V159 destination: field **360**, canonical bundle **1326**
- Compiled component: `work/mass_driver_v159_stage/clones/field_360/07_dialogue.bin`, 46 bytes, `552133bab0a6dacbe8a915d2aa98843333a1c11e6f69027d9bd61630add4cdc9`
- Inventory: **1 blocks / 1 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_398_curved_transit_tunnel.authored.json -> blocks[id=0]`
- Window: 42 x 2; manual wrap: no
- Status: compiled into V159

```text
CREW TRANSIT LINE A
MASS DRIVER WORKS

[window closes]
```

### 04. Field 720 - Lighthouse coastal utility tunnel

- Dialogue text source: [field_399_lighthouse_utility_tunnel.authored.json](../../../content/mass_driver_v2/field_399_lighthouse_utility_tunnel.authored.json)
- Source SHA-256: `8935bc33be0484a576e9bca64c94ff3c4d88a0e6dbce3c77b42207e6645c5bef`
- Retail room/script donor: field **399**, canonical bundle **1404**
- V159 destination: field **720**, canonical bundle **2046**
- Compiled component: `work/mass_driver_v159_stage/clones/field_720/07_dialogue.bin`, 81 bytes, `d7db0404c999b34154685d3fa8854ebce4558a55c06d4aad91000059fb15aac1`
- Inventory: **1 blocks / 2 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_399_lighthouse_utility_tunnel.authored.json -> blocks[id=0]`
- Window: 56 x 5; manual wrap: no
- Status: compiled into V159

```text
CREW TRANSIT LINE B
MASS DRIVER WORKS

----- next page -----

REPORT RAIL FAULTS
TO LINE CONTROL

[window closes]
```

### 05. Field 721 - Lighthouse abandoned Zeboim subway terminus

- Dialogue text source: [field_397_subway_end.authored.json](../../../content/mass_driver_v2/field_397_subway_end.authored.json)
- Source SHA-256: `bf13aca180ac0ba8acea179f59b6b8b00650874ba2bc5e9e700173890bb979a1`
- Retail room/script donor: field **397**, canonical bundle **1400**
- V159 destination: field **721**, canonical bundle **2048**
- Compiled component: `work/mass_driver_v159_stage/clones/field_721/07_dialogue.bin`, 802 bytes, `9ac63fd3538e58788dd188dafaa17dcfa948e46a77d04d7acad0acacef15573c`
- Inventory: **4 blocks / 12 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_397_subway_end.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
TRANSIT ARCHIVE TERMINAL
PROJECT NOTICE / YEAR 6072
SURVEY CARRIER THREE
TO: LAUNCH PERSONNEL

----- next page -----

Tomorrow's payload includes
atmospheric instruments
and an unmanned probe.

----- next page -----

The Mass Driver will carry
the probe above the
atmosphere. Its own engines
will take it from there.

----- next page -----

FROM: LENA / GUIDANCE
TO: ARON / SYSTEMS
Mira asked what the probe
would find.

----- next page -----

I told her we would not know
unless we sent it. She said
that was a good reason to
let me work late.

----- next page -----

REPLY: ARON / SYSTEMS
Tell her I saved her a seat
for the count.

----- next page -----

EMERALDA:

"Not missiles...?"

----- next page -----

ELLY:

"No. Not then."

----- next page -----

ARCHIVE RECORD END

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_397_subway_end.authored.json -> blocks[id=1]`
- Window: 58 x 4; manual wrap: no
- Status: compiled into V159

```text
MAINTENANCE UNIT M-07
"Reserve stores available."[Delay:10]
     [Opcode:01:FF]Items
     Gear parts

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_397_subway_end.authored.json -> blocks[id=2]`
- Window: 58 x 2; manual wrap: no
- Status: compiled into V159

```text
MAINTENANCE UNIT M-07
"Maintenance complete."

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_397_subway_end.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"I can't believe this robot
is still operational after
all this time..."

[window closes]
```

### 06. Field 363 - Zeboim launch-works service junction

- Dialogue text source: [field_363_zeboim_service_junction.authored.json](../../../content/mass_driver_v2/field_363_zeboim_service_junction.authored.json)
- Source SHA-256: `e265c18e8456f9b52de0bb0cf5ea82e383505a0deeb130a0da94b581b3911f8c`
- Retail room/script donor: field **363**, canonical bundle **1332**
- V159 destination: field **363**, canonical bundle **1332**
- Compiled component: `work/mass_driver_v159_stage/clones/field_363/07_dialogue.bin`, 428 bytes, `6985668e75e0db6740832a8fde2761155fa6d967a2fb583620ce399fd858a517`
- Inventory: **5 blocks / 8 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_363_zeboim_service_junction.authored.json -> blocks[id=0]`
- Window: 44 x 2; manual wrap: no
- Status: compiled into V159

```text
MASS DRIVER WORKS
PERSONNEL PRESSURE LOCK

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_363_zeboim_service_junction.authored.json -> blocks[id=1]`
- Window: 48 x 4; manual wrap: no
- Status: compiled into V159

```text
SERVICE VESTIBULE
PRESSURE LOCK AHEAD

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_363_zeboim_service_junction.authored.json -> blocks[id=2]`
- Window: 52 x 4; manual wrap: no
- Status: compiled into V159

```text
CREW TRANSIT LINE
PLATFORM ACCESS

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_363_zeboim_service_junction.authored.json -> blocks[id=3]`
- Window: 46 x 3; manual wrap: no
- Status: compiled into V159

```text
LOCAL TERMINAL OFFLINE
ROUTE CONTROL UNAVAILABLE

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_363_zeboim_service_junction.authored.json -> blocks[id=4]`
- Window: 52 x 4; manual wrap: no
- Status: compiled into V159

```text
SERVICE JUNCTION TERMINAL
DUTY LOG / FINAL ENTRY
COMMAND LINE SILENT
CREW TRANSIT SUSPENDED

----- next page -----

PRESSURE LOCK SEALED
RELEASE ORDER STILL PENDING

----- next page -----

ELLY:

"They sealed the line and
waited for an order that
never came."

----- next page -----

EMERALDA:

"Terminal waited too long."

[window closes]
```

### 07. Field 362 - Zeboim personnel transfer airlock

- Dialogue text source: [field_376_transfer_airlock.authored.json](../../../content/mass_driver_v2/field_376_transfer_airlock.authored.json)
- Source SHA-256: `70df593278af5d0b804330802cababbafad7ce9f570e27eec7142d116afbf008`
- Retail room/script donor: field **376**, canonical bundle **1358**
- V159 destination: field **362**, canonical bundle **1330**
- Compiled component: `work/mass_driver_v159_stage/clones/field_362/07_dialogue.bin`, 209 bytes, `771a281f673fdb1433f6e8656e8c30324eacd5ce7ce0691b234be77b248f6e50`
- Inventory: **5 blocks / 5 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_376_transfer_airlock.authored.json -> blocks[id=0]`
- Window: 42 x 3; manual wrap: no
- Status: compiled into V159

```text
PRESSURE TRANSFER LOCK
ATMOSPHERE SEAL OPERABLE

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_376_transfer_airlock.authored.json -> blocks[id=1]`
- Window: 46 x 2; manual wrap: no
- Status: compiled into V159

```text
Equalizing chamber
pressure. Please wait.[Opcode:02:32]

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_376_transfer_airlock.authored.json -> blocks[id=2]`
- Window: 24 x 2; manual wrap: no
- Status: compiled into V159

```text
Equalization
complete.[Opcode:02:20]

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_376_transfer_airlock.authored.json -> blocks[id=3]`
- Window: 26 x 3; manual wrap: no
- Status: compiled into V159

```text
Venting inner
chamber.
Please wait.[Opcode:02:32]

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_376_transfer_airlock.authored.json -> blocks[id=4]`
- Window: 26 x 2; manual wrap: no
- Status: compiled into V159

```text
Decompression
complete.[Opcode:02:20]

[window closes]
```

### 08. Field 727 - Zeboim three-door operations junction

- Dialogue text source: [field_377_inner_access.authored.json](../../../content/mass_driver_v2/field_377_inner_access.authored.json)
- Source SHA-256: `cb51dad083c2c3b387305cabd5d6a009bbd39a8cbeca6806a1f6fe5198465aae`
- Retail room/script donor: field **377**, canonical bundle **1360**
- V159 destination: field **727**, canonical bundle **2060**
- Compiled component: `work/mass_driver_v159_stage/clones/field_727/07_dialogue.bin`, 387 bytes, `167bb35a56c61ece95f0ca00f40795203eaea5f9b9aa2b33d810b6db3738c29d`
- Inventory: **5 blocks / 8 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_377_inner_access.authored.json -> blocks[id=0]`
- Window: 50 x 3; manual wrap: no
- Status: compiled into V159

```text
OPERATIONS JUNCTION
MAIN SERVICE HUB AHEAD

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_377_inner_access.authored.json -> blocks[id=1]`
- Window: 52 x 3; manual wrap: no
- Status: compiled into V159

```text
EAST PASSAGE
GUIDANCE AND MATERIALS

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_377_inner_access.authored.json -> blocks[id=2]`
- Window: 52 x 3; manual wrap: no
- Status: compiled into V159

```text
WEST PASSAGE
VERTICAL SERVICE SHAFT

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_377_inner_access.authored.json -> blocks[id=3]`
- Window: 52 x 3; manual wrap: no
- Status: compiled into V159

```text
CENTRAL PASSAGE
LAUNCH SUPPORT WORKS

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_377_inner_access.authored.json -> blocks[id=4]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
FACILITY PERSONNEL NOTICE
TIMEKEEPING / SECURITY

----- next page -----

BE SURE TO CLOCK IN AND OUT
EVERY TIME YOU ENTER OR
LEAVE THE FACILITY.

----- next page -----

REPORT TO YOUR SUPERVISOR
ANY SUSPICIOUS ACTIVITY.

----- next page -----

STAY UP TO DATE WITH
SAFETY PROTOCOLS.

[window closes]
```

### 09. Field 372 - Zeboim four-door service hub

- Dialogue text source: [field_372_service_hub.authored.json](../../../content/mass_driver_v2/field_372_service_hub.authored.json)
- Source SHA-256: `dd6064497b64d864d7c916d9253fdd3764d2978a933b9a2db41ba820dc756cd7`
- Retail room/script donor: field **372**, canonical bundle **1350**
- V159 destination: field **372**, canonical bundle **1350**
- Compiled component: `work/mass_driver_v159_stage/clones/field_372/07_dialogue.bin`, 992 bytes, `523f8850a8e322eef30899cfbc701cb733737fe59cb57a5aeddb3bd86aed9919`
- Inventory: **9 blocks / 15 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_372_service_hub.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"The directory is still
legible. Control and Research
is west. Materials Storage
is below the east wing."

----- next page -----

ELLY:

"The accelerator interlock
is north, at Archive Console
D. Central Gate lies beyond
it."

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_372_service_hub.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"Two separate systems power
the Central Gate: the
Auxiliary Grid and the
accelerator banks."

----- next page -----

ELLY:

"There is an authorization
station beyond it. The old
records in these wings may
tell us what it expects."

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_372_service_hub.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
SERVICE DIRECTORY

----- next page -----

CONTROL AND RESEARCH
ANNEX - WEST WING

----- next page -----

FOUR-POINT AUTHORITY
MATERIALS STORAGE
LOWER EAST

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_372_service_hub.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
SERVICE DIRECTORY
NORTH PASSAGE
ACCELERATOR CONDUIT

----- next page -----

BEYOND THE CONDUIT
LAUNCH SUPPORT
CENTRAL GATE

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_372_service_hub.authored.json -> blocks[id=4]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
CENTRAL GATE
AUXILIARY GRID: NO POWER
ACCELERATOR BANKS: NO POWER

[window closes]
```

#### Block 5

- Source locator: `content/mass_driver_v2/field_372_service_hub.authored.json -> blocks[id=5]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
EMERGENCY DIRECTIVE
CONTROL AND RESEARCH ANNEX
WEST WING

[window closes]
```

#### Block 6

- Source locator: `content/mass_driver_v2/field_372_service_hub.authored.json -> blocks[id=6]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
FOUR-POINT AUTHORITY
MATERIALS STORAGE
LOWER EAST

[window closes]
```

#### Block 7

- Source locator: `content/mass_driver_v2/field_372_service_hub.authored.json -> blocks[id=7]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ACCELERATOR POWER
ARCHIVE CONSOLE D
MAGNETIC BANK INTERLOCK

[window closes]
```

#### Block 8

- Source locator: `content/mass_driver_v2/field_372_service_hub.authored.json -> blocks[id=8]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
AUTHORIZATION TERMINAL
DEFENSE ARCHIVE
BEYOND CENTRAL GATE

----- next page -----

CENTRAL CONTROL
BEYOND FIVE PAYLOAD VAULTS

[window closes]
```

### 10. Field 361 - Zeboim control and research annex

- Dialogue text source: [field_373_control_research_annex.authored.json](../../../content/mass_driver_v2/field_373_control_research_annex.authored.json)
- Source SHA-256: `ea4a46d48c221909e7a4c124dac89dceaf7250bdc10a4237483daad6ed8507a3`
- Retail room/script donor: field **373**, canonical bundle **1352**
- V159 destination: field **361**, canonical bundle **1328**
- Compiled component: `work/mass_driver_v159_stage/clones/field_361/07_dialogue.bin`, 1,387 bytes, `980551a72dd726363dd8fe6126ce5cf6c74f68c15d53b02e0d9c0ca6849e31ae`
- Inventory: **2 blocks / 17 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_373_control_research_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
GUIDANCE ARCHIVE TERMINAL
EMERGENCY DIRECTIVE 0320
OFFICE MEMO / YEAR 6081
PRIME MINISTER'S ADVISER

----- next page -----

Once a strategic alert is
declared, loss of Central
Command contact shall not
suspend a pending release
request.

----- next page -----

Unless a recall is received,
the local launch director
will execute Directive 0320.

----- next page -----

UNSENT DRAFT
FROM: LENA / GUIDANCE
TO: FACILITY DIRECTOR

----- next page -----

During yesterday's test, the
command line was dead for
eleven minutes. Under 0320,
that would have counted as
permission.

----- next page -----

A dead line cannot confirm
an order. Please do not
sign this.

----- next page -----

MAINTENANCE MAIL / ARON
Guidance, Control, and Launch
Safety share the auxiliary
grid. The accelerator banks
use a separate interlock.

----- next page -----

The separation is deliberate.
Do not bridge both systems
without the launch director
present at the main board.

----- next page -----

ADDENDUM: ADVISER'S OFFICE
Physical-presence rule waived
for a Directive 0320 alert.

----- next page -----

FROM: ARON / TO: LENA
Keep the banks isolated. If
the order comes, make someone
walk into this room and give
it to us.

----- next page -----

DIRECTIVE RECORD RECOVERED
0320

----- next page -----

ELLY:

"0320... That is the number
the authorization system
needs."

----- next page -----

ELLY:

"The floor controls only
operate the Auxiliary Grid.
We should restore it now."

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_373_control_research_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
AUXILIARY GRID CONTROL
MANUAL BYPASS ACCEPTED

----- next page -----

PRIMARY BUS: STABLE
GUIDANCE: ONLINE
LAUNCH SAFETY: ONLINE

----- next page -----

AUXILIARY POWER RESTORED
CENTRAL GATE CONDITION:
SATISFIED

----- next page -----

ACCELERATOR INTERLOCK:
ARCHIVE CONSOLE D

[window closes]
```

### 11. Field 722 - Zeboim materials storage annex

- Dialogue text source: [field_374_storage_annex.authored.json](../../../content/mass_driver_v2/field_374_storage_annex.authored.json)
- Source SHA-256: `58991194baeeb79568e748a73dff17771f1d3362da186a50bf846b7ae704023c`
- Retail room/script donor: field **374**, canonical bundle **1354**
- V159 destination: field **722**, canonical bundle **2050**
- Compiled component: `work/mass_driver_v159_stage/clones/field_722/07_dialogue.bin`, 1,799 bytes, `2a12d6235fbaf6abbbff4afc0a0fd5bcdb5b19d2f262f2f6420920ce8df41a5a`
- Inventory: **9 blocks / 22 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_374_storage_annex.authored.json -> blocks[id=0]`
- Window: 34 x 2; manual wrap: no
- Status: compiled into V159

```text
You have too many
[Opcode:04:14]

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_374_storage_annex.authored.json -> blocks[id=1]`
- Window: 40 x 2; manual wrap: no
- Status: compiled into V159

```text
Received [Opcode:04:14]

[window closes]

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_374_storage_annex.authored.json -> blocks[id=2]`
- Window: 52 x 3; manual wrap: no
- Status: compiled into V159

```text
DIRECTIVE RECORD REQUIRED
GUIDANCE ARCHIVE:
CONTROL AND RESEARCH

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_374_storage_annex.authored.json -> blocks[id=3]`
- Window: 54 x 3; manual wrap: no
- Status: compiled into V159

```text
FOUR-POINT AUTHORITY
NOT RECOVERED
Read this room's record.

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_374_storage_annex.authored.json -> blocks[id=4]`
- Window: 48 x 3; manual wrap: no
- Status: compiled into V159

```text
DIRECTIVE 0320 RECORDED
AWAITING FOUR-POINT AUTHORITY

[window closes]
```

#### Block 5

- Source locator: `content/mass_driver_v2/field_374_storage_annex.authored.json -> blocks[id=5]`
- Window: 52 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]FOUR-POINT AUTHORITY
  A-2  B-5  C-8  D-4
  A-4  B-8  C-5  D-2
  A-5  B-2  C-4  D-8

[window closes]
```

#### Block 6

- Source locator: `content/mass_driver_v2/field_374_storage_annex.authored.json -> blocks[id=6]`
- Window: 50 x 3; manual wrap: no
- Status: compiled into V159

```text
DIRECTIVE 0320 ACCEPTED
FOUR-POINT AUTHORITY VERIFIED

[window closes]
```

#### Block 7

- Source locator: `content/mass_driver_v2/field_374_storage_annex.authored.json -> blocks[id=7]`
- Window: 48 x 3; manual wrap: no
- Status: compiled into V159

```text
AUTHORIZATION REJECTED
Entry does not match
archive record.

[window closes]
```

#### Block 8

- Source locator: `content/mass_driver_v2/field_374_storage_annex.authored.json -> blocks[id=8]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
PAYLOAD HANDLING MAIL / 6079
FROM: ARON / SYSTEMS
TO: MARA / PAYLOAD SAFETY

----- next page -----

Adapter test complete. The
banks took the missile frame
without modification. I was
told to enter it as a civil
compatibility test.

----- next page -----

REPLY: MARA
Do not. Write MISSILE.
If they want this done, make
them name it.

----- next page -----

ATTACHED STORAGE INVENTORY
CIVIL PAYLOADS / YEAR 6079
UNIVERSITY WEATHER PACKAGE
NEXT SURVEY CARRIER

----- next page -----

STATUS: REMOVED FROM QUEUE
REPLACEMENT: SEALED CARGO
TRANSFER: STRATEGIC COMMAND
ORDER: ADVISER'S OFFICE

----- next page -----

FROM: LENA / GUIDANCE
The public schedule still
lists the next carrier.
Its survey cradle is gone.

----- next page -----

REPLY: MARA
Archive both versions.
When they claim we agreed,
the dates will say otherwise.

----- next page -----

MATERIALS CONTROL RECORD
DIRECTIVE 0320
FOUR-POINT AUTHORITY
A-2  B-5  C-8  D-4

----- next page -----

POLICY: Payload, Guidance,
Safety, and Accelerator
Control each hold one point.
No office may hold more
than one.

----- next page -----

EMERGENCY ADDENDUM
Executive Office may fill
unavailable posts. Duplicate
credentials will be held at
Defense Archive.

----- next page -----

FROM: MARA / TO: LENA
They marked me unavailable
at 09:10. I was there.
A Strategic Command officer
signed Safety for me.

----- next page -----

My protest and the notice
that it was closed carry
the same time.

----- next page -----

AUTHORIZATION TERMINAL
DEFENSE ARCHIVE
BEYOND CENTRAL GATE
ENTER DIRECTIVE 0320
THEN A-2, B-5, C-8, D-4

----- next page -----

EMERALDA:

"A-2, B-5, C-8, D-4...
Emeralda will remember."

[window closes]
```

### 12. Field 723 - Zeboim sealed stair connector

- Dialogue text source: [field_375_service_connector.authored.json](../../../content/mass_driver_v2/field_375_service_connector.authored.json)
- Source SHA-256: `430a77ee4b4a3b5c03023663128e6b6402c4d77a75f76816e7212a5b21d06e66`
- Retail room/script donor: field **375**, canonical bundle **1356**
- V159 destination: field **723**, canonical bundle **2052**
- Compiled component: `work/mass_driver_v159_stage/clones/field_723/07_dialogue.bin`, 545 bytes, `80f6b4b331f6f2263a38211844f6810dc23b2c7bcdd3e876aafcbf6ac0a7eb02`
- Inventory: **5 blocks / 9 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_375_service_connector.authored.json -> blocks[id=0]`
- Window: 48 x 3; manual wrap: no
- Status: compiled into V159

```text
SAFETY LOCK ACTIVE
Reset emergency status at the
nearest terminal.

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_375_service_connector.authored.json -> blocks[id=1]`
- Window: 54 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]EMERGENCY STATUS
CONTAINMENT ALERT

----- next page -----

[Opcode:01:FF]A containment alarm remains
in effect.

----- next page -----

[Opcode:01:FF]Before passing the seal,
perform a local safety scan.

----- next page -----

[Opcode:01:FF]After clearance, reset the
emergency status at the next
terminal.

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_375_service_connector.authored.json -> blocks[id=2]`
- Window: 40 x 3; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]Initiate local safety scan?
     Begin scan
     Cancel

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_375_service_connector.authored.json -> blocks[id=3]`
- Window: 44 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]SCAN COMPLETE
No active contamination
found.

----- next page -----

[Opcode:01:FF]PASSAGE CLEAR
Reset emergency status at
the nearest terminal.

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_375_service_connector.authored.json -> blocks[id=4]`
- Window: 42 x 3; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]SAFETY CLEARANCE NEEDED
Complete the local scan
before passing the seal.

[window closes]
```

### 13. Field 375 - Zeboim post-auxiliary sealed stair connector

- Dialogue text source: [field_375_post_aux_stair.authored.json](../../../content/mass_driver_v2/field_375_post_aux_stair.authored.json)
- Source SHA-256: `430a77ee4b4a3b5c03023663128e6b6402c4d77a75f76816e7212a5b21d06e66`
- Retail room/script donor: field **375**, canonical bundle **1356**
- V159 destination: field **375**, canonical bundle **1356**
- Compiled component: `work/mass_driver_v159_stage/clones/field_375/07_dialogue.bin`, 545 bytes, `80f6b4b331f6f2263a38211844f6810dc23b2c7bcdd3e876aafcbf6ac0a7eb02`
- Inventory: **5 blocks / 9 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_375_post_aux_stair.authored.json -> blocks[id=0]`
- Window: 48 x 3; manual wrap: no
- Status: compiled into V159

```text
SAFETY LOCK ACTIVE
Reset emergency status at the
nearest terminal.

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_375_post_aux_stair.authored.json -> blocks[id=1]`
- Window: 54 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]EMERGENCY STATUS
CONTAINMENT ALERT

----- next page -----

[Opcode:01:FF]A containment alarm remains
in effect.

----- next page -----

[Opcode:01:FF]Before passing the seal,
perform a local safety scan.

----- next page -----

[Opcode:01:FF]After clearance, reset the
emergency status at the next
terminal.

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_375_post_aux_stair.authored.json -> blocks[id=2]`
- Window: 40 x 3; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]Initiate local safety scan?
     Begin scan
     Cancel

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_375_post_aux_stair.authored.json -> blocks[id=3]`
- Window: 44 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]SCAN COMPLETE
No active contamination
found.

----- next page -----

[Opcode:01:FF]PASSAGE CLEAR
Reset emergency status at
the nearest terminal.

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_375_post_aux_stair.authored.json -> blocks[id=4]`
- Window: 42 x 3; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]SAFETY CLEARANCE NEEDED
Complete the local scan
before passing the seal.

[window closes]
```

### 14. Field 387 - Zeboim vertical service connector

- Dialogue text source: [field_387_vertical_connector.authored.json](../../../content/mass_driver_v2/field_387_vertical_connector.authored.json)
- Source SHA-256: `3f161c1e5cc5dfa0c2d51bef293e1fa6f376104c4f5af801fd568a5acf0120a9`
- Retail room/script donor: field **387**, canonical bundle **1380**
- V159 destination: field **387**, canonical bundle **1380**
- Compiled component: `work/mass_driver_v159_stage/clones/field_387/07_dialogue.bin`, 51 bytes, `b7c1070c01d12587c0f9c9f4cd54f0c4855550e970d5d530d7b694137effa52d`
- Inventory: **1 blocks / 1 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_387_vertical_connector.authored.json -> blocks[id=0]`
- Window: 42 x 2; manual wrap: no
- Status: compiled into V159

```text
VERTICAL SERVICE SHAFT
TO MAGNETIC CONDUIT

[window closes]
```

### 15. Field 725 - Zeboim magnetic conduit hall

- Dialogue text source: [field_385_magnetic_conduit.authored.json](../../../content/mass_driver_v2/field_385_magnetic_conduit.authored.json)
- Source SHA-256: `b8f76031b8383207b36bb7eeaa9f861f59d99c44c1b2a658be2a69c2f67c79a7`
- Retail room/script donor: field **385**, canonical bundle **1376**
- V159 destination: field **725**, canonical bundle **2056**
- Compiled component: `work/mass_driver_v159_stage/clones/field_725/07_dialogue.bin`, 153 bytes, `647495ef6e491c2aaa9ef3c0a252505cb3b2fdd869b3ee5f6df15294948d14b5`
- Inventory: **2 blocks / 3 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_385_magnetic_conduit.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
LAUNCH-WORKS CONDUIT
REMOTE BANK CONTROL

----- next page -----

ARCHIVE CONSOLE D
ACCELERATOR INTERLOCK

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_385_magnetic_conduit.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
MAGNETIC JUNCTION
CENTRAL GATE AHEAD
DEFENSE ARCHIVE BEYOND

[window closes]
```

### 16. Field 726 - Zeboim launch-support hall

- Dialogue text source: [field_384_launch_support.authored.json](../../../content/mass_driver_v2/field_384_launch_support.authored.json)
- Source SHA-256: `5a8e9aea835b77588f737570d9d1efb710ac5b110e0c2ea0b3a047e4b17d0484`
- Retail room/script donor: field **384**, canonical bundle **1374**
- V159 destination: field **726**, canonical bundle **2058**
- Compiled component: `work/mass_driver_v159_stage/clones/field_726/07_dialogue.bin`, 571 bytes, `4eaad7c53c095d2083a7ad3abafef2c6013ec8d6f36803789f988df3857e56be`
- Inventory: **5 blocks / 11 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_384_launch_support.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
CENTRAL GATE SEALED
AUXILIARY POWER OFFLINE

----- next page -----

Restore the Auxiliary Grid
in the Control and Research
Annex.

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_384_launch_support.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
CENTRAL GATE SEALED
ACCELERATOR POWER OFFLINE

----- next page -----

Restore magnetic bank power
at ARCHIVE CONSOLE D:
ACCELERATOR INTERLOCK

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_384_launch_support.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
CENTRAL GATE CONTROL
AUXILIARY POWER REQUIRED
ACCELERATOR POWER REQUIRED

----- next page -----

Power opens this gate.
The launch records do not.

----- next page -----

AUTHORIZATION TERMINAL
DEFENSE ARCHIVE
BEYOND THIS GATE

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_384_launch_support.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
CENTRAL GATE CONTROL
POWER INTERLOCKS READY

----- next page -----

EAST SERVICE STAIRS
DEFENSE ARCHIVE BEYOND

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_384_launch_support.authored.json -> blocks[id=4]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
CENTRAL GATE OPEN

----- next page -----

EAST SERVICE STAIRS
TO DEFENSE ARCHIVE

[window closes]
```

### 17. Field 366 - Zeboim launch-support archive A

- Dialogue text source: [field_366_archive_annex.authored.json](../../../content/mass_driver_v2/field_366_archive_annex.authored.json)
- Source SHA-256: `f91ba82d6019850b19724adf19217734589c51ec999c7774c13bad20c202b6a0`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V159 destination: field **366**, canonical bundle **1338**
- Compiled component: `work/mass_driver_v159_stage/clones/field_366/07_dialogue.bin`, 1,016 bytes, `c5e3c781b8da6cfab78baf9cfbcf835cf41e7ca47872ffbeaa1d40783fb7ffdc`
- Inventory: **2 blocks / 10 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_366_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ARCHIVE MAIL TERMINAL B
STAFF MAIL / YEAR 6078
FROM: ARON / SYSTEMS
TO: LENA / GUIDANCE

----- next page -----

The Prime Minister's adviser
brought Strategic Command
through Bank Two. A colonel
asked whether a survey cradle
could take a denser casing.

----- next page -----

I said anything built to
the guide dimensions would
clear. Then he called it
a warhead.

----- next page -----

I answered before I let
myself understand the
question.

----- next page -----

REPLY: LENA / GUIDANCE
Send every drawing to Mara.
Make them put in writing
what they are asking us
to do.

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_366_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
OPERATIONS DESK TERMINAL B
MINISTRY MAIL / YEAR 6078
FROM: FACILITY DIRECTOR
TO: CIVIL LAUNCH BUREAU

----- next page -----

Strategic Command now holds
visitor clearance, payload
review, and access to Bank
Two. Was the charter changed?

----- next page -----

REPLY: MINISTRY LIAISON
No amendment is required.
Shared access will preserve
the space program through
the funding review.

----- next page -----

FROM: FACILITY DIRECTOR
You have made its survival
depend on the people asking
us to launch nuclear weapons.

----- next page -----

REPLY: MINISTRY LIAISON
That wording is not approved
for the official record.

[window closes]
```

### 18. Field 367 - Zeboim archive-branch operations junction

- Dialogue text source: [field_367_archive_junction.authored.json](../../../content/mass_driver_v2/field_367_archive_junction.authored.json)
- Source SHA-256: `b982dbd375ba2c6b9d9e2abbd780cd7aa95569cd59a5045ae5adbde58e022f8e`
- Retail room/script donor: field **377**, canonical bundle **1360**
- V159 destination: field **367**, canonical bundle **1340**
- Compiled component: `work/mass_driver_v159_stage/clones/field_367/07_dialogue.bin`, 105 bytes, `e35f3e204abe8727e9282786951493065b4a8b0ed11344695db0f99ec0a665df`
- Inventory: **1 blocks / 1 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_367_archive_junction.authored.json -> blocks[id=0]`
- Window: 54 x 4; manual wrap: no
- Status: compiled into V159

```text
ARCHIVE BRANCH JUNCTION
WEST: CIVIL PAYLOAD STORES
SOUTH: STRATEGIC STORES
NORTH: LAUNCH SUPPORT

[window closes]
```

### 19. Field 385 - Zeboim civil-payload stores

- Dialogue text source: [field_385_storage_treasure_annex.authored.json](../../../content/mass_driver_v2/field_385_storage_treasure_annex.authored.json)
- Source SHA-256: `c80e906cfec1bff1804b63a4b8a270604592f9dc4ca4e715175fb7ecddc852de`
- Retail room/script donor: field **374**, canonical bundle **1354**
- V159 destination: field **385**, canonical bundle **1376**
- Compiled component: `work/mass_driver_v159_stage/clones/field_385/07_dialogue.bin`, 790 bytes, `b8fbffffe7882c974d08c1708eb2f5b66b7e6e275123973b70dc7548c6042d1e`
- Inventory: **3 blocks / 9 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_385_storage_treasure_annex.authored.json -> blocks[id=0]`
- Window: 34 x 2; manual wrap: no
- Status: compiled into V159

```text
You have too many
[Opcode:04:14]

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_385_storage_treasure_annex.authored.json -> blocks[id=1]`
- Window: 40 x 2; manual wrap: no
- Status: compiled into V159

```text
Received [Opcode:04:14]

[window closes]

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_385_storage_treasure_annex.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

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

### 20. Field 386 - Zeboim strategic-payload stores

- Dialogue text source: [field_386_storage_treasure_annex.authored.json](../../../content/mass_driver_v2/field_386_storage_treasure_annex.authored.json)
- Source SHA-256: `008f356bd3b47484c762cdb1cc3bf17f309c88c8f3ae0d20f0b324d415849534`
- Retail room/script donor: field **374**, canonical bundle **1354**
- V159 destination: field **386**, canonical bundle **1378**
- Compiled component: `work/mass_driver_v159_stage/clones/field_386/07_dialogue.bin`, 577 bytes, `f3ed00a4584c2ef9b352d2e16ca9bf9be857d00acf2a90fe4725517d5ebbef92`
- Inventory: **3 blocks / 8 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_386_storage_treasure_annex.authored.json -> blocks[id=0]`
- Window: 34 x 2; manual wrap: no
- Status: compiled into V159

```text
You have too many
[Opcode:04:14]

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_386_storage_treasure_annex.authored.json -> blocks[id=1]`
- Window: 40 x 2; manual wrap: no
- Status: compiled into V159

```text
Received [Opcode:04:14]

[window closes]

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_386_storage_treasure_annex.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
STRATEGIC STORES / 6079
FROM: MARA / PAYLOAD SAFETY
TO: FACILITY DIRECTOR

----- next page -----

Proposal MC-4 replaces the
civil instrument bay with a
strategic warhead cradle.
It breaks Launch Charter 11.
I do not certify it.

----- next page -----

REPLY: ADVISER'S OFFICE
Objection recorded.
Emergency Continuity Act
permits alternate approval.
Work may proceed.

----- next page -----

FROM: MARA / TO: LENA
They thanked me for putting
my objection on record. Then
they removed my name from the
approval list.

----- next page -----

I thought no meant they had
to stop.

----- next page -----

REPLY: LENA
It should have.
Keep a copy.

[window closes]
```

### 21. Field 368 - Zeboim launch-support archive C

- Dialogue text source: [field_368_archive_annex.authored.json](../../../content/mass_driver_v2/field_368_archive_annex.authored.json)
- Source SHA-256: `43d095c3a7f4d037705a0f27108b6b6ed803b52e41043ec6c5246b7736e83ce1`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V159 destination: field **368**, canonical bundle **1342**
- Compiled component: `work/mass_driver_v159_stage/clones/field_368/07_dialogue.bin`, 672 bytes, `fb0c59b3d3753dea0ed78c7e596672ebd0d48132c77d598084005b3495281ea8`
- Inventory: **2 blocks / 8 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_368_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ARCHIVE CONSOLE D
ACCELERATOR INTERLOCK

----- next page -----

REMOTE TEST ACCEPTED
MAGNETIC BANKS RESPONDING
ACCELERATOR POWER RESTORED

----- next page -----

CENTRAL GATE INTERLOCK
RAIL CONDITION SATISFIED
RETURN TO CENTRAL GATE

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_368_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ARCHIVE MAIL TERMINAL D
SAVED MAIL / YEAR 6081
FROM: ARON / SYSTEMS
TO: LENA / GUIDANCE

----- next page -----

Lawine destroyed the central
power station before dawn.
Half the capital is dark.
Command wants the thermal
limits bypassed tonight.

----- next page -----

The Prime Minister's adviser
said on the radio that delay
invites attack.

----- next page -----

Maybe seeing every bank ready
will make them stop. I have
to believe that, Lena. I am
the one closing the breakers.

----- next page -----

SYSTEM ROUTING NOTE
ACCELERATOR INTERLOCK
CONTROL: MAIN CONSOLE

[window closes]
```

### 22. Field 369 - Zeboim launch-support archive D

- Dialogue text source: [field_369_archive_annex.authored.json](../../../content/mass_driver_v2/field_369_archive_annex.authored.json)
- Source SHA-256: `4c7f46ab57120e1806022a50e3876075957f1f93364aa6a2804e1002d7c8533b`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V159 destination: field **369**, canonical bundle **1344**
- Compiled component: `work/mass_driver_v159_stage/clones/field_369/07_dialogue.bin`, 1,031 bytes, `8fcf2877ad397636eb74ae199eb48b8d2f1d1639c7e1cbf53c81de78afd00a8f`
- Inventory: **2 blocks / 12 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_369_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ARCHIVE MAIL TERMINAL E
FORWARDED ADDRESS / 6081
PRIME MINISTER'S ADVISER
TO: DEFENSE FACILITIES

----- next page -----

The surest peace is a reply
too swift to challenge.
Readiness is not aggression.
Hesitation invites attack.

----- next page -----

LENA / GUIDANCE
Two foreign leaders used
those same words tonight.

----- next page -----

MARA / PAYLOAD SAFETY
Three. I checked the
morning replay.

----- next page -----

ARON / SYSTEMS
Maybe because the threat
is the same.

----- next page -----

LENA / GUIDANCE
Or because the advice is.

----- next page -----

ARON / SYSTEMS
I don't know. Mira is in
Shelter Four. Tell me what I
am supposed to do with that.

----- next page -----

NO FURTHER REPLIES

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_369_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

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

### 23. Field 370 - Zeboim launch-support archive E

- Dialogue text source: [field_370_archive_annex.authored.json](../../../content/mass_driver_v2/field_370_archive_annex.authored.json)
- Source SHA-256: `c8ac50bc9d20f50a26cf6bb5732f960187cd2f194b090aa6089c6ac8c0beacd0`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V159 destination: field **370**, canonical bundle **1346**
- Compiled component: `work/mass_driver_v159_stage/clones/field_370/07_dialogue.bin`, 1,025 bytes, `7f638cb5bc01354ef721c2a25576aa774d1437e665f605a7bfee1d569c0ef2f9`
- Inventory: **2 blocks / 9 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_370_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ARCHIVE MAIL TERMINAL F
FEDERAL MEDICAL BUREAU
INCIDENT BULLETIN / 6081
FORWARDED BY: MARA

----- next page -----

Central power was lost after
the Lawine attack. The
emergency generator failed
during surgery. One child
died. Attending: Dr. Kim.

----- next page -----

Average life expectancy is
about thirty. The number
unable to have children is
still rising. There is no
approved treatment.

----- next page -----

FROM: MARA / PAYLOAD SAFETY
TO: LENA / GUIDANCE
This is the public version.
The full report is worse.

----- next page -----

I read Kim's paper twice and
understood half of it.
But he is trying to repair
the damage itself.
No one else is.

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_370_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

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

### 24. Field 371 - Zeboim launch-support archive F

- Dialogue text source: [field_371_archive_annex.authored.json](../../../content/mass_driver_v2/field_371_archive_annex.authored.json)
- Source SHA-256: `cb15fc94e069b7c23bf22a5a6f593870902a06237866d1ade075644b2bd801c7`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V159 destination: field **371**, canonical bundle **1348**
- Compiled component: `work/mass_driver_v159_stage/clones/field_371/07_dialogue.bin`, 1,177 bytes, `29a35967240f1c18707eeb48f7d78ccf857243961055a243f379a1f7caee0421`
- Inventory: **2 blocks / 15 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_371_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

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

#### Block 1

- Source locator: `content/mass_driver_v2/field_371_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
OPERATIONS DESK TERMINAL G
SECURITY MAIL / YEAR 6083
FROM: HUMAN EVOLUTION OFFICE
TO: GOVERNMENT SPECIAL FORCES

----- next page -----

If Dr. Kim's laboratory is
entered, all molecular
machinery and biological
material are state property.

----- next page -----

Do not damage the colony.
Research staff may not remove
or conceal any component.

----- next page -----

FORWARDED BY: MARA
Why is Payload Safety copied
on an order for a laboratory
that is not ours?

----- next page -----

REPLY: ADVISER'S OFFICE
No action is requested.
Archive for continuity.

[window closes]
```

### 25. Field 724 - Zeboim launch-support archive G

- Dialogue text source: [field_724_archive_annex.authored.json](../../../content/mass_driver_v2/field_724_archive_annex.authored.json)
- Source SHA-256: `cbbd0e243917913f4d86b3bd92a933c7189744300133bb27126f4408b8f93867`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V159 destination: field **724**, canonical bundle **2054**
- Compiled component: `work/mass_driver_v159_stage/clones/field_724/07_dialogue.bin`, 1,233 bytes, `5c1ab3417dbb52eb2a434a3411a34ed33b3b09d49bb83878fe3c952b84ed0dad`
- Inventory: **2 blocks / 15 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_724_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

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

#### Block 1

- Source locator: `content/mass_driver_v2/field_724_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
OPERATIONS DESK TERMINAL H
PRIORITY MAIL / YEAR 6083
FROM: LAUNCH DIRECTOR
TO: ADVISER'S OFFICE

----- next page -----

Three warning stations show
different tracks. Guidance
cannot confirm an attack.
Request immediate recall of
Directive 0320.

----- next page -----

REPLY: ADVISER'S OFFICE
No recall has been issued.
Continuity remains in force.
Delay gives the enemy the
choice of first strike.

----- next page -----

UNSENT / LAUNCH DIRECTOR
There may be no enemy choice.
Only ours.

----- next page -----

DELIVERY QUEUE CLOSED
BATTERY RELEASE CONFIRMED

[window closes]
```

### 26. Field 376 - Zeboim autonomous-defense archive

- Dialogue text source: [field_394_defense_archive.authored.json](../../../content/mass_driver_v2/field_394_defense_archive.authored.json)
- Source SHA-256: `e6bf56d397b24f6861b9c32e9a81324a79eae36fe9d9acd3513d8e704dc1e5cc`
- Retail room/script donor: field **394**, canonical bundle **1394**
- V159 destination: field **376**, canonical bundle **1358**
- Compiled component: `work/mass_driver_v159_stage/clones/field_376/07_dialogue.bin`, 7,200 bytes, `3eadb9b8fafc2b1fa36c8325a604aac6d8e91e519ad317a2d4bc42988b92289d`
- Inventory: **39 blocks / 104 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"This appears to be the final
authorization station before
Central Control."

----- next page -----

EMERALDA:

"Console wants old code?"

----- next page -----

ELLY:

"Directive 0320, followed by
four separate authority
points."

----- next page -----

ELLY:

"The surviving archives
should contain them. We can
use whatever we recovered
and return for the rest."

----- next page -----

ELLY:

"Each value goes in alone.
But this place still believes
Zeboim is at war."

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
AUTHORIZATION TERMINAL
DIRECTIVE RECORD NOT FOUND

----- next page -----

Manual entry is available,
but the Directive number
must be supplied.

----- next page -----

CLUE LOCATION
CONTROL AND RESEARCH ANNEX
RETURN VIA EAST STAIRS

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
AUTHORIZATION TERMINAL
AUTHORITY RECORD NOT FOUND

----- next page -----

Manual entry is available,
but all four authority
points are required.

----- next page -----

CLUE LOCATION
MATERIALS STORAGE
RETURN VIA EAST STAIRS

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
AUTHORIZATION TERMINAL
DIRECTIVE 0320 ACCEPTED
FOUR AUTHORITY POINTS VALID
LAUNCH AUTHORIZATION ACTIVE

----- next page -----

DEFENSE BAY LIFT AVAILABLE
NORTH WALL ACCESS
CUSTODIAN STATUS BELOW

----- next page -----

WEST BULKHEAD STATUS
CHECK LOCAL INDICATOR

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=4]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]DIRECTIVE NUMBER
  0320
  0302
  3200

[window closes]
```

#### Block 5

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=5]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]AUTHORITY POINT A
  A-2
  A-4
  A-5

[window closes]
```

#### Block 6

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=6]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
DIRECTIVE 0320 ACCEPTED
AUTHORITY A-2 ACCEPTED
AUTHORITY B-5 ACCEPTED
AUTHORITY C-8 ACCEPTED
AUTHORITY D-4 ACCEPTED

----- next page -----

LAUNCH AUTHORITY RECORDED
DEFENSE BAY LIFT UNLOCKED
NORTH WALL ACCESS AVAILABLE
CUSTODIAN REVIEW BELOW

----- next page -----

ELLY:

"Our Gears should be in the
bay below. Let's use the
north lift."

[window closes]
```

#### Block 7

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=7]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
AUTHORIZATION REJECTED
ONE OR MORE ENTRIES INVALID

----- next page -----

Enter Directive 0320 first.
Then confirm A, B, C, and D
separately. A partial code
will not be accepted.

[window closes]
```

#### Block 8

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=8]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"Authorization is accepted.
The north-wall lift now leads
to the Defense Bay."

----- next page -----

EMERALDA:

"Gears are below. Emeralda
ready!"

[window closes]
```

#### Block 9

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=9]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
DEFENSE BAY LIFT
ACCESS LOCKED

----- next page -----

Complete launch authorization
at the wall console:
Directive 0320, then A, B,
C, and D.

[window closes]
```

#### Block 10

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=10]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
WEST BULKHEAD SEALED
LOCAL CONTROL REQUIRED

----- next page -----

Use the nearby west console.
The bulkhead can be opened
there after the Custodian
defense system is disabled.

[window closes]
```

#### Block 11

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=11]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"Enter 0320 first. Then A-2,
B-5, C-8, and D-4.
One value at a time."

[window closes]
```

#### Block 12

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=12]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"The defense system is down
and the bulkhead is open.
Central Control lies beyond
the fifth magazine."

[window closes]
```

#### Block 13

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=13]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]AUTHORITY POINT B
  B-2
  B-5
  B-8

[window closes]
```

#### Block 14

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=14]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]AUTHORITY POINT C
  C-4
  C-5
  C-8

[window closes]
```

#### Block 15

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=15]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V159

```text
[Opcode:01:FF]AUTHORITY POINT D
  D-2
  D-4
  D-8

[window closes]
```

#### Block 16

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=16]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
NATIONAL SECURITY BRIEF
ECONOMY: CONTRACTING
PUBLIC GRID: UNSTABLE
URBAN VIOLENCE: RISING
PUBLIC TRUST: COLLAPSING

----- next page -----

RIVAL GOVERNMENTS REPORT
THE SAME INTERNAL CRISIS
EACH BLAMES THE OTHERS
EACH EXPANDS EMERGENCY RULE

----- next page -----

ADVISER'S SUMMARY
ONLY MILITARY READINESS
CAN RESTORE STABILITY

[window closes]
```

#### Block 17

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=17]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
DEFENSE PROCUREMENT AUDIT
ORDER: WARHEAD ADAPTER STUDY
AUTHORITY: STRATEGIC COMMAND
DATE: 6078

----- next page -----

CIVIL PROGRAM HEARING
SHARED USE PROPOSAL
DATE: 6079

----- next page -----

AUDIT EXCEPTION
STUDY WAS ORDERED BEFORE
CIVIL REVIEW HAD BEGUN

----- next page -----

APPROVAL ROUTE
ADVISER'S OFFICE

[window closes]
```

#### Block 18

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=18]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
PUBLIC INFORMATION ARCHIVE
APPROVED STATEMENT / 6079
SPACE PROGRAM PRESERVED
THROUGH SHARED DEFENSE USE

----- next page -----

INTERNAL STATUS / SAME DAY
SCIENCE QUEUE: CANCELLED
CIVIL LAUNCHES: SUSPENDED
ALL BANKS: STRATEGIC

----- next page -----

EDITOR'S NOTE / UNSENT
They kept the name because
people still trusted it.

[window closes]
```

#### Block 19

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=19]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
STRATEGIC OUTCOME MODEL
LIMITED RELEASE
ESCALATION: FULL EXCHANGE

----- next page -----

FIRST STRIKE
PROJECTED: FULL EXCHANGE

----- next page -----

RETALIATORY STRIKE
PROJECTED: FULL EXCHANGE

----- next page -----

PROJECTED CIVIL SURVIVAL
BELOW RECOVERY THRESHOLD
SHELTER SYSTEM: INADEQUATE

----- next page -----

POLICY DISPOSITION
READINESS EXPANDED
REPORT SEALED FROM PUBLIC

[window closes]
```

#### Block 20

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=20]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
DIRECTIVE 0320 / DRAFT LOG
EARLY TEXT
LOST COMMAND CONTACT:
HOLD RELEASE

----- next page -----

FINAL TEXT / 6081
LOST COMMAND CONTACT:
RELEASE UNLESS RECALLED

----- next page -----

REVISION AUTHORITY
PRIME MINISTER'S ADVISER

----- next page -----

EXPIRATION CLAUSE
REMOVED
REVIEW DATE: NONE

----- next page -----

CURRENT SYSTEM STATUS
CENTRAL COMMAND: OFFLINE
RECALL: NEVER RECEIVED
DIRECTIVE: STILL ACTIVE

[window closes]
```

#### Block 21

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=21]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
EXECUTIVE ROUTING AUDIT
NAME: MIANG
TITLE: PRIME MINISTER'S
ADVISER

----- next page -----

FILES ROUTED THROUGH OFFICE
CIVIL BUDGET REDUCTION
STRATEGIC ACCESS ORDER
SAFETY WAIVERS
DIRECTIVE 0320 REVISION

----- next page -----

FINAL RELEASE RECORD
MIANG SIGNATURE: NONE
DIRECTOR SIGNATURE: VALID

----- next page -----

UNSENT / MARA
She never signs the order.
She only decides which
choices reach the person
who must sign it.

[window closes]
```

#### Block 22

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=22]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"A readable video disk...
It was left beside the
archive player."

----- next page -----

EMERALDA:

"Pictures still inside?"

----- next page -----

ELLY:

"Maybe. The computer to the
right may still be able to
read it."

[window closes]
```

#### Block 23

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=23]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ZBC ARCHIVE CONSOLE
NO MEDIA DETECTED

----- next page -----

INSERT VIDEO DISK
TO CONTINUE

[window closes]
```

#### Block 24

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=24]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
VIDEO DISK ACCEPTED
ZBC EVENING REPORT ARCHIVE

----- next page -----

PLAYBACK STARTING...

[window closes]
```

#### Block 25

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=25]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ZBC EVENING REPORT / 6081
CELIA REN, ANCHOR

----- next page -----

Good evening. Our top story:
markets continue to fall as
public services fail across
the country.

----- next page -----

The wealthiest families are
buying private shelters and
seats aboard the remaining
orbital projects.

----- next page -----

They call it survival.
Critics call it an escape
plan for the chosen few.

----- next page -----

But no shelter can outlast
the collapse of the world
that must support it.

[window closes]
```

#### Block 26

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=26]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ZBC HEALTH DESK / 6081
CELIA REN, ANCHOR

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
civilization may not survive
another generation.

----- next page -----

Appeals for more births have
caused panic, not recovery.

[window closes]
```

#### Block 27

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=27]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ZBC WORLD DESK / 6082
REPORTER: CELIA REN

----- next page -----

Foreign wars continue while
civil fighting spreads into
six more provinces.

----- next page -----

Millions are displaced.
Farms stand abandoned and
transport routes are cut.

----- next page -----

Famine grips the interior.
Food lines now stretch across
virtually every major city.

----- next page -----

Relief demand has exceeded
the national reserve.

[window closes]
```

#### Block 28

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=28]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ZBC CAPITAL LIVE / 6082
REPORTER: CELIA REN

----- next page -----

Riots have entered a third
week. The government has
extended curfew indefinitely.

----- next page -----

Police and military units
struggle to hold food depots,
power stations, and the
government district.

----- next page -----

Officials promise order will
be restored. Behind us, three
more city blocks are burning.

[window closes]
```

#### Block 29

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=29]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ZBC POLITICAL DESK / 6082
CELIA REN, ANCHOR

----- next page -----

Public anger now turns toward
Miang, the Prime Minister's
most influential adviser.

----- next page -----

Protesters say she filters
every report and every choice
placed before the government.

----- next page -----

Her name is on no order. Yet
her counsel precedes each new
expansion of emergency rule.

----- next page -----

MIANG'S OFFICE DENIES
MANIPULATING THE
PRIME MINISTER

[window closes]
```

#### Block 30

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=30]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ZBC EMERGENCY / 6083
CELIA REN, ANCHOR

----- next page -----

We have a confirmed launch.
A nuclear missile is now
airborne.

----- next page -----

Multiple nuclear-armed states
have begun retaliation.
Command links are failing.

----- next page -----

If this signal reaches you,
find shelter immediately.
This is not a drill.

----- next page -----

ARCHIVE RECOVERY NOTE
No later broadcast survives.
The retaliatory exchange
ended most of Zeboim
civilization.

[window closes]
```

#### Block 31

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=31]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
Received Video Disk

[window closes]

[window closes]
```

#### Block 32

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=32]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"The other disks are too
damaged to read."

[window closes]
```

#### Block 33

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=33]`
- Window: 40 x 3; manual wrap: yes
- Status: compiled into V159

```text
[Opcode:01:FF]INSERT VIDEO DISK?
     Insert disk
     Cancel

[window closes]
```

#### Block 34

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=34]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
ELLY:

"There is no room to carry
the Video Disk."

[window closes]
```

#### Block 35

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=35]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
FZN SIGNAL OVERRIDE / 6081
JONAS VALE, CORRESPONDENT

----- next page -----

The government is going to
destroy this country.
Every emergency decree
protects only those in power.

----- next page -----

They call our hunger order.
They call our silence peace.
If we wait, there will be
nothing left to save.

----- next page -----

It is time for the people
to revolt against the
government.

----- next page -----

END UNAUTHORIZED SIGNAL
ZBC ARCHIVE RESUMES

[window closes]
```

#### Block 36

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=36]`
- Window: 40 x 3; manual wrap: yes
- Status: compiled into V159

```text
[Opcode:01:FF]Take the Video Disk?
     Take it
     Leave it

[window closes]
```

#### Block 37

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=37]`
- Window: 40 x 4; manual wrap: yes
- Status: compiled into V159

```text
[Opcode:01:FF]ARCHIVE CONSOLE
     Arcade Games
     Video Disk
     Leave

[window closes]
```

#### Block 38

- Source locator: `content/mass_driver_v2/field_394_defense_archive.authored.json -> blocks[id=38]`
- Window: 40 x 4; manual wrap: yes
- Status: compiled into V159

```text
[Opcode:01:FF]ARCADE DIRECTORY
     Play NUKE
     Missile Command
     Back

[window closes]
```

### 27. Field 384 - Goliath Factory Gear staging and Guardian hall

- Dialogue text source: [field_260_goliath_factory_hall.authored.json](../../../content/mass_driver_v2/field_260_goliath_factory_hall.authored.json)
- Source SHA-256: `93f411fea9ef909dccaf733d773a4e6d49447398f9b82e73ee2eec9560c151d8`
- Retail room/script donor: field **260**, canonical bundle **1126**
- V159 destination: field **384**, canonical bundle **1374**
- Compiled component: `work/mass_driver_v159_stage/clones/field_384/07_dialogue.bin`, 1,017 bytes, `168bf7a52807850f7a471df89f244a562cba03e96c5468bb2a7403daaca82791`
- Inventory: **7 blocks / 17 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_260_goliath_factory_hall.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
GOLIATH FACTORY / LOWER WORKS
DEFENSE BAY 03

----- next page -----

AUTONOMOUS DEFENSE INTERFACE
STATUS: STANDBY
LOCAL DRIVE CONTROL ONLY

[window closes]
```

#### Block 1

- Source locator: `content/mass_driver_v2/field_260_goliath_factory_hall.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
El-Regulus / STANDBY
UNIT ID: EL-REGULUS
PILOT LINK: ELLY CONFIRMED

----- next page -----

Elly climbs into the cockpit.
The Gear answers at once.

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_260_goliath_factory_hall.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
CRESCENS / STANDBY
PILOT LINK:
EMERALDA CONFIRMED

----- next page -----

Emeralda boards Crescens.
The Gear comes fully online.

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_260_goliath_factory_hall.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
Elly
So... Citan left our Gears
here for us.

----- next page -----

Emeralda
The Custodian Core must have
transferred into it.

----- next page -----

Emeralda
It was guarding our Gears,
but it still considers us
intruders.

----- next page -----

Elly
Keep launch control intact!

----- next page -----

GUARDIAN CONTROL
DEFENSE INHIBIT REJECTED
CUSTODIAN FRAME DEPLOYING

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_260_goliath_factory_hall.authored.json -> blocks[id=4]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
CUSTODIAN CORE OFFLINE
WEST BULKHEAD UNLOCKED

----- next page -----

Elly
"We'll leave the Gears here
until after we launch the
capsule into the upper
atmosphere."

----- next page -----

Emeralda
"Then we'll come back
for them!"

[window closes]
```

#### Block 5

- Source locator: `content/mass_driver_v2/field_260_goliath_factory_hall.authored.json -> blocks[id=5]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
NORTH TRANSFER DOOR / ERROR
DRIVE CONTROLLER: OFFLINE
STATUS: NON-FUNCTIONAL

----- next page -----

The sealed passage cannot be
opened from this side.

[window closes]
```

#### Block 6

- Source locator: `content/mass_driver_v2/field_260_goliath_factory_hall.authored.json -> blocks[id=6]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V159

```text
SOUTH PERSONNEL ACCESS
CLEARANCE: HUMAN SCALE ONLY

[window closes]
```

### 28. Field 377 - Containment vault 1 of 5

- Dialogue text source: [field_673_silo_vault_1.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_1.authored.json)
- Source SHA-256: `2e6d9917ad4e30811202dd857b9fa0f4b45d10406e9b8ac8b4ae7ee70f9ad56b`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V159 destination: field **377**, canonical bundle **1360**
- Compiled component: `work/mass_driver_v159_stage/clones/field_377/07_dialogue.bin`, 236 bytes, `58fdde3162c171100cb4982ed8c9c6ecd45cad3866c5cba700926da1a6228719`
- Inventory: **1 blocks / 4 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_673_silo_vault_1.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V159

```text
RESERVE MAGAZINE 01 / 05
STRATEGIC ROCKET STORAGE
TARGET NETWORK: LOST
PASSAGE SENSOR: ACTIVE

----- next page -----

ELLY:

"Missiles... and gigantic
rockets..."

----- next page -----

EMERALDA:

"There are so many..."

----- next page -----

ELLY:

"A strategic reserve. The
guidance data appears to
be lost."

[window closes]
```

### 29. Field 378 - Containment vault 2 of 5

- Dialogue text source: [field_673_silo_vault_2.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_2.authored.json)
- Source SHA-256: `008c159dd05e228641c1e0f824fd43fca0facbb2ae5e81bfe562ed82034bc7d3`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V159 destination: field **378**, canonical bundle **1362**
- Compiled component: `work/mass_driver_v159_stage/clones/field_378/07_dialogue.bin`, 736 bytes, `fd19f01c182c3f034d90b2ae27a50656599575f1e3037e52debade0b30aa2270`
- Inventory: **1 blocks / 10 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_673_silo_vault_2.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V159

```text
RESERVE MAGAZINE 02 / 05
LAUNCH LOG / YEAR 6083
BATTERY RELEASE CONFIRMED
COUNTERSTRIKES DETECTED

----- next page -----

ARCHIVED MAIL / YEAR 6079
FROM: FACILITY DIRECTOR
TO: LAUNCH STAFF
SUBJECT: FUNDING REVIEW

----- next page -----

Civil funding was cut.
Strategic Command offers
to restore it for control
of the accelerator.

----- next page -----

They want final authority
over every payload.
The Adviser calls this
"shared use."

----- next page -----

MARA / PAYLOAD SAFETY
The attached manifest says
NUCLEAR WARHEAD.
I will not certify it.

----- next page -----

FROM: ARON / SYSTEMS
If we refuse, banks shut.
Maybe the space program
survives if we agree.

----- next page -----

REPLY: LENA / GUIDANCE
Mira kept the paper star
you made for her.
What do I tell her now?

----- next page -----

ELLY:

"Then they did use this
place..."

----- next page -----

EMERALDA:

"People did this?"

----- next page -----

ELLY:

"Yes... to one another."

[window closes]
```

### 30. Field 379 - Containment vault 3 of 5

- Dialogue text source: [field_673_silo_vault_3.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_3.authored.json)
- Source SHA-256: `95aa6c09c3f06458909e5f6fc1d9a153409cfb001076a6de9c51ea8317384fc8`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V159 destination: field **379**, canonical bundle **1364**
- Compiled component: `work/mass_driver_v159_stage/clones/field_379/07_dialogue.bin`, 238 bytes, `5910fc39a0cc8c331f0afc1ef2e72f05c212aa8ecc7542e666649bfd93efca96`
- Inventory: **1 blocks / 4 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_673_silo_vault_3.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V159

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

### 31. Field 382 - Containment vault 4 of 5

- Dialogue text source: [field_673_silo_vault_4.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_4.authored.json)
- Source SHA-256: `7baf3cfdd4a23f2a58ff685564465009aebb7add854d1840813775ea4e0f4456`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V159 destination: field **382**, canonical bundle **1370**
- Compiled component: `work/mass_driver_v159_stage/clones/field_382/07_dialogue.bin`, 205 bytes, `c4972f16466276880ab4382c2cd93c2cf5f2835540b2a71928a0c0c348bd2bc8`
- Inventory: **1 blocks / 4 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_673_silo_vault_4.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V159

```text
RESERVE MAGAZINE 04 / 05
OUTBOUND CALL LOG
COMMAND: NO CONNECTION
SHELTERS: NO CONNECTION

----- next page -----

CALL ATTEMPTS CONTINUED
UNTIL GRID FAILURE

----- next page -----

EMERALDA:

"Someone kept calling..."

----- next page -----

ELLY:

"Yes...
Even with no answer."

[window closes]
```

### 32. Field 383 - Containment vault 5 of 5

- Dialogue text source: [field_673_silo_vault_5.authored.json](../../../content/mass_driver_v2/field_673_silo_vault_5.authored.json)
- Source SHA-256: `8fdce9a409f8ed99343a2961b3e03addc73b98c89ae2fc6106e3a3290ffe6a88`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V159 destination: field **383**, canonical bundle **1372**
- Compiled component: `work/mass_driver_v159_stage/clones/field_383/07_dialogue.bin`, 238 bytes, `5ca5d9105a71ab7f80fca26f513f337c92636570da2cce413e14e9c2ae3a3e0f`
- Inventory: **1 blocks / 4 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_673_silo_vault_5.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V159

```text
RESERVE MAGAZINE 05 / 05
ALL TARGET DATA LOST
CENTRAL CONTROL AHEAD

----- next page -----

ELLY:

"Here in the dark...
they look like
tombstones."

----- next page -----

ELLY:

"A graveyard for people
who destroyed one
another..."

----- next page -----

ELLY:

"...all because of their
pride and arrogance."

[window closes]
```

### 33. Field 728 - Zeboim Mass Driver central control

- Dialogue text source: [field_369_archive_control.authored.json](../../../content/mass_driver_v2/field_369_archive_control.authored.json)
- Source SHA-256: `78ba34d6a6605fc91979091ae9e8fc34136dfa4caafb5e546826da9bc0bbdef5`
- Retail room/script donor: field **369**, canonical bundle **1344**
- V159 destination: field **728**, canonical bundle **2062**
- Compiled component: `work/mass_driver_v159_stage/clones/field_728/07_dialogue.bin`, 4,448 bytes, `131de29fa2c10c2f3ffd927e2900cd892e7352987a08e3835d186688816a19f0`
- Inventory: **37 blocks / 70 pages**

#### Block 0

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

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

#### Block 1

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
ELLY:

"This console looks out of
place among the other
computer terminals..."

[window closes]
```

#### Block 2

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=2]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 02
Launch weather records.

[window closes]
```

#### Block 3

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=3]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 03
Space-program guidance.

[window closes]
```

#### Block 4

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=4]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 04
Guidance calibration.

[window closes]
```

#### Block 5

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=5]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 05
Emergency power transfer.

[window closes]
```

#### Block 6

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=6]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 06
Personnel evacuation.

[window closes]
```

#### Block 7

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=7]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 07
Payload inventory.

[window closes]
```

#### Block 8

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=8]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 08
Network failure report.

[window closes]
```

#### Block 9

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=9]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 09
Final maintenance order.

[window closes]
```

#### Block 10

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=10]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; dormant/orphan-reference-only

```text
CAPSULE CRADLE
NANOMACHINE PAYLOAD SECURED
LAUNCH CONSOLE READY

[window closes]
```

#### Block 11

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=11]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
LAUNCH CONTROL LOCKED
NO ACCEPTED AUTHORIZATION

----- next page -----

Return through the five
reserve magazines to the
Defense Archive. Use the
wall console.

----- next page -----

Enter Directive 0320 first.
Then enter all four points:
A-2, B-5, C-8, and D-4.
Partial codes are rejected.

[window closes]
```

#### Block 12

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=12]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

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

#### Block 13

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=13]`
- Window: 52 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
The terminal requests an emergency Directive number.
Search the Control and Research Annex archive.

[window closes]
```

#### Block 14

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=14]`
- Window: 54 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
The terminal requires all four authority points.
Search the Materials Storage archive.

[window closes]
```

#### Block 15

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=15]`
- Window: 48 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
DIRECTIVE 0320
LAUNCH AUTHORIZATION ACTIVE

[window closes]
```

#### Block 16

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=16]`
- Window: 34 x 4; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
[Opcode:01:FF]DIRECTIVE NUMBER
  0320
  0302
  3200

[window closes]
```

#### Block 17

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=17]`
- Window: 54 x 4; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
[Opcode:01:FF]FOUR-POINT AUTHORITY
  A-2  B-5  C-8  D-4
  A-4  B-8  C-5  D-2
  A-5  B-2  C-4  D-8

[window closes]
```

#### Block 18

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=18]`
- Window: 50 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
DIRECTIVE 0320 ACCEPTED
FOUR-POINT AUTHORITY VERIFIED
Launch control released.

[window closes]
```

#### Block 19

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=19]`
- Window: 48 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
AUTHORIZATION REJECTED
The Directive or one of the four points is invalid.

[window closes]
```

#### Block 20

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=20]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
LAUNCH STATUS
LAUNCH COMPLETE
CAPSULE CLEAR
ATMOSPHERIC DISPERSAL ACTIVE

----- next page -----

CAPSULE ALREADY RELEASED
NO SECOND PAYLOAD LOADED

----- next page -----

ELLY:

"It is done..."

[window closes]
```

#### Block 21

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=21]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
ELLY:

"Wait..."

----- next page -----

EMERALDA:

"Elly...? What's wrong?"

----- next page -----

ELLY:

"The room... it is changing.
Two officers are at the
console. I can hear them..."

----- next page -----

EMERALDA:

"Emeralda sees no one.
The room is empty."

[window closes]
```

#### Block 22

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=22]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
LAUNCH DIRECTOR
"Directive 0320 confirmed.
Target data is loaded.
The Prime Minister has
authorized release."

[window closes]
```

#### Block 23

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=23]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
SYSTEMS OFFICER
"The warning net contradicts
itself. We have no confirmed
enemy launch. If we fire
now... we begin it."

[window closes]
```

#### Block 24

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=24]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
LAUNCH DIRECTOR
"And they will answer.
Every major city will be
lost... ours included."

[window closes]
```

#### Block 25

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=25]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
MIANG
"Do not blame yourself.
You did everything possible
to preserve the peace."

[window closes]
```

#### Block 26

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=26]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
SYSTEMS OFFICER
"Fallout projections exceed
every shelter limit. Once we
open the banks, there is
no recall."

[window closes]
```

#### Block 27

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=27]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
MIANG
"That is why the Prime
Minister entrusted this to
you. He knows you will
protect them."

[window closes]
```

#### Block 28

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=28]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
LAUNCH DIRECTOR
"Protect them...?
There may be no one left
to protect."

[window closes]
```

#### Block 29

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=29]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
MIANG
"If you hesitate, the enemy
will choose for you.
Is that what you want?"

[window closes]
```

#### Block 30

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=30]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
SYSTEMS OFFICER
"All four authority points
accepted. Cradles are open.
Director... we need your
final order."

[window closes]
```

#### Block 31

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=31]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
LAUNCH DIRECTOR
"...Open the banks.
Execute Directive 0320."

[window closes]
```

#### Block 32

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=32]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
EMERALDA:

"Elly..."

----- next page -----

ELLY:

(Why does this feel so
familiar?)

----- next page -----

EMERALDA:

"Elly?"

----- next page -----

ELLY:

(I remember that...from a
dream?)

----- next page -----

ELLY:

"But no matter, we have a
job to do."

[window closes]
```

#### Block 33

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=33]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; no emitted F5/D2 reference

```text
EMERALDA:

"Was it a dream?"

----- next page -----

ELLY:

"It felt like one of my
dreams... but the memory
was not mine."

----- next page -----

ELLY:

"The archives name Miang.
That voice was hers. This
was her memory."

----- next page -----

EMERALDA:

"But Miang did not give
order."

----- next page -----

ELLY:

"No. She turned every doubt
into another reason to fire.
She made the choice feel
like their own."

[window closes]
```

#### Block 34

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=34]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; no emitted F5/D2 reference

```text
EMERALDA:

"And now... we use the same
machine?"

----- next page -----

ELLY:

"Yes. Once, it was used to
destroy life. Now... we will
use it to heal."

----- next page -----

ELLY:

"The Limiter was forced upon
them. We can give back what
was taken."

----- next page -----

EMERALDA:

"Then... let us do it."

----- next page -----

ELLY:

"The console is ready. We
will activate it when we are
prepared."

[window closes]
```

#### Block 35

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=35]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
CITAN:

"Elly! I made it in time.
The guidance solution is
drifting."

----- next page -----

ELLY:

"Citan! Can you hold the
ascent path?"

----- next page -----

CITAN:

"I will set the trajectory
and hold it steady. The
capsule will open in the
upper atmosphere."

----- next page -----

LAUNCH SEQUENCE ARMED
MAGNETIC BANKS SYNCHRONIZED
CAPSULE ASCENT READY
ACCELERATOR CHARGING

----- next page -----

CITAN:

"Trajectory locked.
Commit the capsule now!"

----- next page -----

ELLY:

"Please... reach them all."

----- next page -----

EMERALDA:

"Go!"

[window closes]
```

#### Block 36

- Source locator: `content/mass_driver_v2/field_369_archive_control.authored.json -> blocks[id=36]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V159

```text
MIANG
"You did what was
necessary."

[window closes]
```

## Appendix: authored files not selected by V159

These **16** files (39 blocks / 117 pages) remain in the content directory as older, alternate, or otherwise non-selected authored sources. Their text is not part of the active V159 route and is therefore not duplicated in the main transcript.

| Authored source | Blocks | Pages | SHA-256 |
|---|---:|---:|---|
| [field_263_goliath_defense_bay.authored.json](../../../content/mass_driver_v2/field_263_goliath_defense_bay.authored.json) | 3 | 10 | `07238f1392ec1e8c9f50ad161b504c1f148676ca50c8d192dbcd157d86d46e89` |
| [field_365_archive_annex.authored.json](../../../content/mass_driver_v2/field_365_archive_annex.authored.json) | 2 | 8 | `0ac3b98608d9631938d00c99b7a4c6b6c61c60ac3c95f6e08137ca1b85d3204c` |
| [field_367_archive_annex.authored.json](../../../content/mass_driver_v2/field_367_archive_annex.authored.json) | 1 | 6 | `9c0c49cb42a325dd1cf0ffbd6f88b28da450bde8348b84ab508464b9bff12106` |
| [field_367_decontamination.authored.json](../../../content/mass_driver_v2/field_367_decontamination.authored.json) | 1 | 1 | `83739b926db9d4bea24b2930db4c0a50286eb5e2b30138d094d6e2c3d9c48068` |
| [field_370_freight_stairwell.authored.json](../../../content/mass_driver_v2/field_370_freight_stairwell.authored.json) | 1 | 1 | `2aca8c65601f21ba5b3e026445035620369fc01e39f147167f7f8165859b500a` |
| [field_382_freight_lift.authored.json](../../../content/mass_driver_v2/field_382_freight_lift.authored.json) | 2 | 6 | `6c93629bec4a90c3e6002bcdb597c94aec694d2ef996a1955874c3e288b9d2cb` |
| [field_385_missile_gallery_a.authored.json](../../../content/mass_driver_v2/field_385_missile_gallery_a.authored.json) | 1 | 7 | `55c59bba30496b35b2e590ffb9b1971c449388c68a7362be43c2f34e87ebeb53` |
| [field_385_missile_gallery_b.authored.json](../../../content/mass_driver_v2/field_385_missile_gallery_b.authored.json) | 1 | 7 | `692616f53398610acadf68f24fa33ac794487fb9f996bc8df595e552e7cdcaf5` |
| [field_385_missile_gallery_c.authored.json](../../../content/mass_driver_v2/field_385_missile_gallery_c.authored.json) | 1 | 9 | `c7ec31352147234140076479f9597b4c12734064db8a8c03e0f6ba898ec0601e` |
| [field_386_deep_access_lift.authored.json](../../../content/mass_driver_v2/field_386_deep_access_lift.authored.json) | 1 | 3 | `b07b3f60f79c73c394fc313311952349df7b9c3fc73d67f9f2f62b3016bd95fc` |
| [field_388_final_red_tunnel.authored.json](../../../content/mass_driver_v2/field_388_final_red_tunnel.authored.json) | 5 | 5 | `70df593278af5d0b804330802cababbafad7ce9f570e27eec7142d116afbf008` |
| [field_398_opening.authored.json](../../../content/mass_driver_v2/field_398_opening.authored.json) | 5 | 7 | `122b1b330836d887cd46ebb410b848b906984cbf16f79b68d9059dba3f014e60` |
| [field_399_powered_corridor.authored.json](../../../content/mass_driver_v2/field_399_powered_corridor.authored.json) | 5 | 8 | `ac9578b3a55d5a6e09ff8eb8ac64bb8ee4469b7085488a260e5d47cbbce17ec2` |
| [field_403_defense_bay.authored.json](../../../content/mass_driver_v2/field_403_defense_bay.authored.json) | 3 | 10 | `7493e7b8a9d985cbfb26361040c3fd8ed4becc4585eabbdfd8e76d4db75301af` |
| [field_403_maintenance_undercroft.authored.json](../../../content/mass_driver_v2/field_403_maintenance_undercroft.authored.json) | 1 | 3 | `98cec0fd4a35e564b24be71a59eb53a9ab0a6684da3ee851850810267f8d8fd6` |
| [field_507_krelian_lab.authored.json](../../../content/mass_driver_v2/field_507_krelian_lab.authored.json) | 6 | 26 | `ccd2ebe5ff385c6f56f9a1c9e2a16aa8dcc13e6e3b133187559d154f8262313a` |

## Appendix: legacy replacement-schema sources

These **8** files contain 164 replacement records / 223 pages. They belong to superseded Mass Driver routes or the original graybox recipe and are not consumed by the active V159 builder.

| Replacement source | Records | Pages | Bound retail source | File SHA-256 |
|---|---:|---:|---|---|
| [content/mass_driver_v2/field_629_archive.replacements.json](../../../content/mass_driver_v2/field_629_archive.replacements.json) | 21 | 21 | 815 bytes / `d40d0c513da019993b42abca25cd90aec5e429c32f4ed5ecfe9c0e6d60b25bce` | `8e8667e45fefa666dd20c8017475ccfa82215b8d02ee84e0cc2e6019ea371038` |
| [content/mass_driver_v2/field_630_code_entry.replacements.json](../../../content/mass_driver_v2/field_630_code_entry.replacements.json) | 39 | 39 | 1301 bytes / `a5191aaab54d0010a18cae05b9b24e893db5ca7ea93c1e197f1fadef361fc116` | `8871beaf19e60ed4c003454305ad2568f9870f18ad067d13cc1bc8d2b97f7b79` |
| [content/mass_driver_v2/field_631_launch_control.replacements.json](../../../content/mass_driver_v2/field_631_launch_control.replacements.json) | 6 | 8 | 465 bytes / `4a4590d9b12b127521ef5338d78e82b5c16b24b9e27d45be99fcfe43515d9f85` | `611876bcf02168f1e2f43e5db865811ea7c4256e4ef886b70edc17d575de7722` |
| [content/mass_driver_v2/field_632_missile_gallery.replacements.json](../../../content/mass_driver_v2/field_632_missile_gallery.replacements.json) | 30 | 65 | 3004 bytes / `89c2555eaa77c475aab399eb7974c36483cb60b88a36123709ba3444058cd8bd` | `c19d31ff0f0d2297fdd7be96a2b3d824bfbff7a3022bca88cc2dcb8990d8eee5` |
| [content/mass_driver_v2/field_633_cargo_service.replacements.json](../../../content/mass_driver_v2/field_633_cargo_service.replacements.json) | 3 | 3 | 142 bytes / `48496993bf04fe5b5694cbfc836f4f7de82ca45298b69632fd6e27e65acce9b8` | `b391aedcd01dc4568c28ba74bd90f4a9d9eff6a95bec0e63f0face8946cf632e` |
| [content/mass_driver_v2/field_635_authorization.replacements.json](../../../content/mass_driver_v2/field_635_authorization.replacements.json) | 49 | 49 | 2363 bytes / `1a1f3744654cca652220ef200d9f4e13f461cadea5a6cb051e55a82f17a781a4` | `099848b1b91969170a219239904098f4d5cc28bf80b3f2d391e28a9890a4f3e5` |
| [content/mass_driver_v2/field_638_boss_warning.replacements.json](../../../content/mass_driver_v2/field_638_boss_warning.replacements.json) | 10 | 28 | 639 bytes / `93de8261413501720be34f089bf47253e9bb04253e431b289888f311aab4c37e` | `da7a31a6a08b7ace25a32cb5ff8e9d49474087d63be3c76baabf2751087dc538` |
| [recipes/mass_driver_control_dialogue.json](../../../recipes/mass_driver_control_dialogue.json) | 6 | 10 | 465 bytes / `4a4590d9b12b127521ef5338d78e82b5c16b24b9e27d45be99fcfe43515d9f85` | `f79ce6681abc06d55da7f8f6bfe3d648fb2af42128833e4b31e5d39eb08412cd` |

## Reproduction

From the workspace root:

```powershell
python tools/export_mass_driver_dialogue.py
```

The exporter rejects missing sources, duplicate block IDs, a release version mismatch, a builder/manifest field mismatch, authored source that does not recompile byte-for-byte, or compiled dialogue bytes that do not match the frozen stage manifest.
