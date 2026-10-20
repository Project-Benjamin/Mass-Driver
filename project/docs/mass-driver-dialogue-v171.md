# Mass Driver V171 dialogue and source provenance

> Generated from the selected staged build. This transcript covers the Mass Driver standalone route, not the untouched retail Xenogears Disc 2 script outside that route.

## Scope and provenance

- Active dialogue-bearing fields: **33**
- Authored source files used by V171: **33**
- Tracked custom-dialogue JSON sources: **57** (33 active authored, 16 inactive authored, 8 legacy replacement-schema)
- Dialogue blocks: **184**
- Text pages (`<New>` delimited): **439**
- Compiled dialogue bytes: **28,887**
- Source-to-stage recompilation: **all active sources verified byte-for-byte**
- Tagged speaker cues: Elly **58**, Emeralda **20**, Citan **3**

Every transcript line below comes from the linked `*.authored.json` file. Each of those files is explicitly marked `reconstruction: true`. The listed retail field is the room/script donor used to construct the playable field; it is **not** a claim that the custom wording was copied from retail dialogue.

Control tags are rendered as follows: `<New>` becomes `next page`, `<Close>` becomes `window closes`, speaker tags become uppercase labels, and opcode/delay tags remain visible in square brackets.
A status of `compiled` means the block is present in the release dialogue component; it does not imply that every conditional branch is encountered during one playthrough. Central Control has an additional exhaustive static reference classification: `statically reachable` means an emitted VM path can reach the block under some valid flag/input state, not that a human test traversed it.

### Release source ledger

- Stage manifest: `builds/mass_driver/mass-driver-v171-dialogue/stage/manifest.json` - `e41697bff936d0ff09fafba5b5a88d5fc41a326c597ebf5135303d38d1219db0`
- Reconstruction metadata: [reconstruction_metadata.json](../modules/mass_driver/content/reconstruction_metadata.json) - `3eb7d435f951f3215270ef53ff537678203f0d67e017d20f6500c960aa09b0bb`
- Builder mapping: [build.py](../modules/mass_driver/build.py) - `20ef3879fb171ac0bb9c57abc8e4641438dc203e20d0092ae96d6a30e85d539c`

## Active field index

| Route | V171 field | Room | Retail donor | Blocks / pages | Text source | Compiled dialogue |
|---:|---:|---|---:|---:|---|---|
| 1 | 729 | Zeboim inclined surface lift | 361 | 9 / 15 | [field_361_zeboim_access_tunnel.authored.json](../modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json) | 770 bytes `5a92417628c7...` |
| 2 | 364 | Zeboim inclined-lift lower landing | 362 | 1 / 2 | [field_362_inclined_service_tunnel.authored.json](../modules/mass_driver/content/field_362_inclined_service_tunnel.authored.json) | 89 bytes `44207e30fc4a...` |
| 3 | 360 | Lighthouse curved employee transit tunnel | 398 | 1 / 1 | [field_398_curved_transit_tunnel.authored.json](../modules/mass_driver/content/field_398_curved_transit_tunnel.authored.json) | 46 bytes `552133bab0a6...` |
| 4 | 720 | Lighthouse coastal utility tunnel | 399 | 1 / 2 | [field_399_lighthouse_utility_tunnel.authored.json](../modules/mass_driver/content/field_399_lighthouse_utility_tunnel.authored.json) | 81 bytes `d7db0404c999...` |
| 5 | 721 | Lighthouse abandoned Zeboim subway terminus | 397 | 4 / 7 | [field_397_subway_end.authored.json](../modules/mass_driver/content/field_397_subway_end.authored.json) | 509 bytes `fe45299a3f46...` |
| 6 | 363 | Zeboim launch-works service junction | 363 | 5 / 11 | [field_363_zeboim_service_junction.authored.json](../modules/mass_driver/content/field_363_zeboim_service_junction.authored.json) | 483 bytes `a0eff0db6e74...` |
| 7 | 362 | Zeboim personnel transfer airlock | 376 | 5 / 5 | [field_376_transfer_airlock.authored.json](../modules/mass_driver/content/field_376_transfer_airlock.authored.json) | 209 bytes `771a281f673f...` |
| 8 | 727 | Zeboim three-door operations junction | 377 | 5 / 8 | [field_377_inner_access.authored.json](../modules/mass_driver/content/field_377_inner_access.authored.json) | 493 bytes `e1bfc0e3108b...` |
| 9 | 372 | Zeboim four-door service hub | 372 | 9 / 15 | [field_372_service_hub.authored.json](../modules/mass_driver/content/field_372_service_hub.authored.json) | 992 bytes `523f8850a8e3...` |
| 10 | 361 | Zeboim control and research annex | 373 | 4 / 15 | [field_373_control_research_annex.authored.json](../modules/mass_driver/content/field_373_control_research_annex.authored.json) | 1,099 bytes `7dbbacff39f8...` |
| 11 | 722 | Zeboim materials storage annex | 374 | 11 / 24 | [field_374_storage_annex.authored.json](../modules/mass_driver/content/field_374_storage_annex.authored.json) | 1,784 bytes `e54d48fc4d90...` |
| 12 | 723 | Zeboim sealed stair connector | 375 | 5 / 9 | [field_375_service_connector.authored.json](../modules/mass_driver/content/field_375_service_connector.authored.json) | 545 bytes `80f6b4b331f6...` |
| 13 | 375 | Zeboim post-auxiliary sealed stair connector | 375 | 5 / 9 | [field_375_post_aux_stair.authored.json](../modules/mass_driver/content/field_375_post_aux_stair.authored.json) | 545 bytes `80f6b4b331f6...` |
| 14 | 387 | Zeboim vertical service connector | 387 | 1 / 1 | [field_387_vertical_connector.authored.json](../modules/mass_driver/content/field_387_vertical_connector.authored.json) | 51 bytes `b7c1070c01d1...` |
| 15 | 725 | Zeboim magnetic conduit hall | 385 | 2 / 3 | [field_385_magnetic_conduit.authored.json](../modules/mass_driver/content/field_385_magnetic_conduit.authored.json) | 153 bytes `647495ef6e49...` |
| 16 | 726 | Zeboim launch-support hall | 384 | 5 / 13 | [field_384_launch_support.authored.json](../modules/mass_driver/content/field_384_launch_support.authored.json) | 760 bytes `a1c0c7652919...` |
| 17 | 366 | Zeboim launch-support archive A | 378 | 2 / 11 | [field_366_archive_annex.authored.json](../modules/mass_driver/content/field_366_archive_annex.authored.json) | 913 bytes `a5dfee2fe3b5...` |
| 18 | 367 | Zeboim archive-branch operations junction | 377 | 1 / 1 | [field_367_archive_junction.authored.json](../modules/mass_driver/content/field_367_archive_junction.authored.json) | 105 bytes `e35f3e204abe...` |
| 19 | 385 | Zeboim civil-payload stores | 374 | 3 / 11 | [field_385_storage_treasure_annex.authored.json](../modules/mass_driver/content/field_385_storage_treasure_annex.authored.json) | 648 bytes `0ead3546aeb0...` |
| 20 | 386 | Zeboim strategic-payload stores | 374 | 3 / 9 | [field_386_storage_treasure_annex.authored.json](../modules/mass_driver/content/field_386_storage_treasure_annex.authored.json) | 684 bytes `bce41a348427...` |
| 21 | 368 | Zeboim launch-support archive C | 378 | 2 / 10 | [field_368_archive_annex.authored.json](../modules/mass_driver/content/field_368_archive_annex.authored.json) | 823 bytes `90c492cbc47d...` |
| 22 | 369 | Zeboim launch-support archive D | 378 | 2 / 13 | [field_369_archive_annex.authored.json](../modules/mass_driver/content/field_369_archive_annex.authored.json) | 1,013 bytes `f889c48dc146...` |
| 23 | 370 | Zeboim launch-support archive E | 378 | 2 / 12 | [field_370_archive_annex.authored.json](../modules/mass_driver/content/field_370_archive_annex.authored.json) | 996 bytes `ba2d55072b56...` |
| 24 | 371 | Zeboim launch-support archive F | 378 | 2 / 14 | [field_371_archive_annex.authored.json](../modules/mass_driver/content/field_371_archive_annex.authored.json) | 1,043 bytes `793aa5330521...` |
| 25 | 724 | Zeboim launch-support archive G | 378 | 2 / 15 | [field_724_archive_annex.authored.json](../modules/mass_driver/content/field_724_archive_annex.authored.json) | 986 bytes `f330f55f94a7...` |
| 26 | 376 | Zeboim autonomous-defense archive | 394 | 42 / 96 | [field_394_defense_archive.authored.json](../modules/mass_driver/content/field_394_defense_archive.authored.json) | 6,930 bytes `1fe0ee2576d3...` |
| 27 | 384 | Goliath Factory Gear staging and Guardian hall | 260 | 8 / 21 | [field_260_goliath_factory_hall.authored.json](../modules/mass_driver/content/field_260_goliath_factory_hall.authored.json) | 966 bytes `bcea17f7583c...` |
| 28 | 377 | Containment vault 1 of 5 | 673 | 1 / 4 | [field_673_silo_vault_1.authored.json](../modules/mass_driver/content/field_673_silo_vault_1.authored.json) | 188 bytes `3df9676da9ba...` |
| 29 | 378 | Containment vault 2 of 5 | 673 | 1 / 4 | [field_673_silo_vault_2.authored.json](../modules/mass_driver/content/field_673_silo_vault_2.authored.json) | 254 bytes `ecba51c897da...` |
| 30 | 379 | Containment vault 3 of 5 | 673 | 1 / 5 | [field_673_silo_vault_3.authored.json](../modules/mass_driver/content/field_673_silo_vault_3.authored.json) | 317 bytes `1c57cb087523...` |
| 31 | 382 | Containment vault 4 of 5 | 673 | 1 / 3 | [field_673_silo_vault_4.authored.json](../modules/mass_driver/content/field_673_silo_vault_4.authored.json) | 171 bytes `992b6aa9124d...` |
| 32 | 383 | Containment vault 5 of 5 | 673 | 1 / 2 | [field_673_silo_vault_5.authored.json](../modules/mass_driver/content/field_673_silo_vault_5.authored.json) | 134 bytes `3af4b64ae599...` |
| 33 | 728 | Zeboim Mass Driver central control | 369 | 37 / 68 | [field_369_archive_control.authored.json](../modules/mass_driver/content/field_369_archive_control.authored.json) | 4,107 bytes `e9ed097c8018...` |

## Complete active transcript

### 01. Field 729 - Zeboim inclined surface lift

- Dialogue text source: [field_361_zeboim_access_tunnel.authored.json](../modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json)
- Source SHA-256: `c48eac336ae5d567bef1aab11470ecbdd9d8a3d735259f49bc043fdd66fe306b`
- Retail room/script donor: field **361**, canonical bundle **1328**
- V171 destination: field **729**, canonical bundle **2064**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_729/07_dialogue.bin`, 770 bytes, `5a92417628c7d56853ec9f907474663017bd437776b11fde87c0ac2595a5c00b`
- Inventory: **9 blocks / 15 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"So this is the Mass
Driver... The power is still
on."

----- next page -----

ELLY:

"The hangar has an entrance
outside. Citan will bring our
Gears in that way."

----- next page -----

ELLY:

"He'll meet us at Central
Control. Let's get the
launcher ready."

----- next page -----

ELLY:

"We have to send Taura's
capsule into the upper
atmosphere."

----- next page -----

ELLY:

"Once the nanomachines
spread, they should remove
the Limiter."

----- next page -----

EMERALDA:

"I'm ready, Elly."

----- next page -----

ELLY:

"All right. Let's go."

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"The controls should be
somewhere below us.
Let's look for a directory."

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json -> blocks[id=2]`
- Window: 50 x 4; manual wrap: no
- Status: compiled into V171

```text
EMERALDA:

"Even after all this time...
the old lift still moves."

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json -> blocks[id=3]`
- Window: 30 x 2; manual wrap: no
- Status: compiled into V171

```text
SURFACE ACCESS LIFT
DESCENT CIRCUIT ACTIVE

[window closes]
```

#### Block 4

- Source locator: `modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json -> blocks[id=4]`
- Window: 50 x 4; manual wrap: no
- Status: compiled into V171

```text
LIFT CONTROL
LOWER LANDING SELECTED

[window closes]
```

#### Block 5

- Source locator: `modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json -> blocks[id=5]`
- Window: 48 x 4; manual wrap: no
- Status: compiled into V171

```text
CAUTION
Stand clear of the platform edge.

[window closes]
```

#### Block 6

- Source locator: `modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json -> blocks[id=6]`
- Window: 46 x 1; manual wrap: no
- Status: compiled into V171

```text
AUTHORIZED PERSONNEL ONLY

[window closes]
```

#### Block 7

- Source locator: `modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json -> blocks[id=7]`
- Window: 46 x 2; manual wrap: no
- Status: compiled into V171

```text
LIFT IN MOTION
KEEP CLEAR

[window closes]
```

#### Block 8

- Source locator: `modules/mass_driver/content/field_361_zeboim_access_tunnel.authored.json -> blocks[id=8]`
- Window: 46 x 1; manual wrap: no
- Status: compiled into V171

```text
AUTHORIZED PERSONNEL ONLY

[window closes]
```

### 02. Field 364 - Zeboim inclined-lift lower landing

- Dialogue text source: [field_362_inclined_service_tunnel.authored.json](../modules/mass_driver/content/field_362_inclined_service_tunnel.authored.json)
- Source SHA-256: `c82f8a3404bd3639bd9fb7743707269bab56ef7f70e59442d35310677088b644`
- Retail room/script donor: field **362**, canonical bundle **1330**
- V171 destination: field **364**, canonical bundle **1334**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_364/07_dialogue.bin`, 89 bytes, `44207e30fc4a93b6b6a6357d7111f3e8c17e880cf00881783fb503dcce71939b`
- Inventory: **1 blocks / 2 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_362_inclined_service_tunnel.authored.json -> blocks[id=0]`
- Window: 54 x 4; manual wrap: no
- Status: compiled into V171

```text
INCLINED TRANSIT LIFT
LOWER TERMINAL

----- next page -----

CREW ACCESS LEVEL
AUTHORIZED PERSONNEL ONLY

[window closes]
```

### 03. Field 360 - Lighthouse curved employee transit tunnel

- Dialogue text source: [field_398_curved_transit_tunnel.authored.json](../modules/mass_driver/content/field_398_curved_transit_tunnel.authored.json)
- Source SHA-256: `3989b46082211c1f5fcd81e28f39edb5088687da2b72d6b5f3ec513f32e5d515`
- Retail room/script donor: field **398**, canonical bundle **1402**
- V171 destination: field **360**, canonical bundle **1326**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_360/07_dialogue.bin`, 46 bytes, `552133bab0a6dacbe8a915d2aa98843333a1c11e6f69027d9bd61630add4cdc9`
- Inventory: **1 blocks / 1 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_398_curved_transit_tunnel.authored.json -> blocks[id=0]`
- Window: 42 x 2; manual wrap: no
- Status: compiled into V171

```text
CREW TRANSIT LINE A
MASS DRIVER WORKS

[window closes]
```

### 04. Field 720 - Lighthouse coastal utility tunnel

- Dialogue text source: [field_399_lighthouse_utility_tunnel.authored.json](../modules/mass_driver/content/field_399_lighthouse_utility_tunnel.authored.json)
- Source SHA-256: `8935bc33be0484a576e9bca64c94ff3c4d88a0e6dbce3c77b42207e6645c5bef`
- Retail room/script donor: field **399**, canonical bundle **1404**
- V171 destination: field **720**, canonical bundle **2046**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_720/07_dialogue.bin`, 81 bytes, `d7db0404c999b34154685d3fa8854ebce4558a55c06d4aad91000059fb15aac1`
- Inventory: **1 blocks / 2 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_399_lighthouse_utility_tunnel.authored.json -> blocks[id=0]`
- Window: 56 x 5; manual wrap: no
- Status: compiled into V171

```text
CREW TRANSIT LINE B
MASS DRIVER WORKS

----- next page -----

REPORT RAIL FAULTS
TO LINE CONTROL

[window closes]
```

### 05. Field 721 - Lighthouse abandoned Zeboim subway terminus

- Dialogue text source: [field_397_subway_end.authored.json](../modules/mass_driver/content/field_397_subway_end.authored.json)
- Source SHA-256: `c3988fe224997bf8e6d88b7eb85f6ed6c989c22a81cebc5b6c382a2596ae21a4`
- Retail room/script donor: field **397**, canonical bundle **1400**
- V171 destination: field **721**, canonical bundle **2048**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_721/07_dialogue.bin`, 509 bytes, `fe45299a3f468cb1c88bbff71c1202b6717a4ea1463697bc775d47509af6b1d4`
- Inventory: **4 blocks / 7 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_397_subway_end.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
PERSONNEL TRAIN
SERVICE SUSPENDED
No departures scheduled.

----- next page -----

SAVED SHIFT TIMETABLE
Arrival / Departure
06:00 / 06:15
14:00 / 14:15
22:00 / 22:15

----- next page -----

PASSENGER NOTICE
Keep aisles and doors clear.
Secure tools and loose
equipment before boarding.

----- next page -----

LAST SERVICE BULLETIN
All passenger runs cancelled.
The shift timetable is
withdrawn.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_397_subway_end.authored.json -> blocks[id=1]`
- Window: 58 x 4; manual wrap: yes
- Status: compiled into V171

```text
MAINTENANCE UNIT M-07
"Select supplies."[Delay:10]
     [Opcode:01:FF]Items
     Gear parts

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_397_subway_end.authored.json -> blocks[id=2]`
- Window: 58 x 3; manual wrap: yes
- Status: compiled into V171

```text
MAINTENANCE UNIT M-07
"Return if you require
supplies."

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_397_subway_end.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"Oh... You're still working?"

[window closes]
```

### 06. Field 363 - Zeboim launch-works service junction

- Dialogue text source: [field_363_zeboim_service_junction.authored.json](../modules/mass_driver/content/field_363_zeboim_service_junction.authored.json)
- Source SHA-256: `db0e289e494e25dad859a64783aa0a258db64d2e538deda814d5366153ef18e0`
- Retail room/script donor: field **363**, canonical bundle **1332**
- V171 destination: field **363**, canonical bundle **1332**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_363/07_dialogue.bin`, 483 bytes, `a0eff0db6e7485927a1b973fc86671c496b574e552b3acb7dcdb699d842c3299`
- Inventory: **5 blocks / 11 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_363_zeboim_service_junction.authored.json -> blocks[id=0]`
- Window: 44 x 2; manual wrap: no
- Status: compiled into V171

```text
MASS DRIVER WORKS
PERSONNEL PRESSURE LOCK

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_363_zeboim_service_junction.authored.json -> blocks[id=1]`
- Window: 48 x 4; manual wrap: no
- Status: compiled into V171

```text
SERVICE VESTIBULE
PRESSURE LOCK AHEAD

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_363_zeboim_service_junction.authored.json -> blocks[id=2]`
- Window: 52 x 4; manual wrap: no
- Status: compiled into V171

```text
CREW TRANSIT LINE
PLATFORM ACCESS

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_363_zeboim_service_junction.authored.json -> blocks[id=3]`
- Window: 46 x 3; manual wrap: no
- Status: compiled into V171

```text
LOCAL TERMINAL OFFLINE
ROUTE CONTROL UNAVAILABLE

[window closes]
```

#### Block 4

- Source locator: `modules/mass_driver/content/field_363_zeboim_service_junction.authored.json -> blocks[id=4]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V171

```text
PRESSURE-LOCK STATION
ARCHIVED DUTY LOG

----- next page -----

Shift transfer suspended.
Command line: no response.
Pressure lock: sealed.

----- next page -----

Release authorization:
pending.

----- next page -----

DUTY OFFICER

----- next page -----

Request release for the
personnel still in the
vestibule.

----- next page -----

The next shift cannot
enter while they are held
here.

----- next page -----

No later entry stored.

[window closes]
```

### 07. Field 362 - Zeboim personnel transfer airlock

- Dialogue text source: [field_376_transfer_airlock.authored.json](../modules/mass_driver/content/field_376_transfer_airlock.authored.json)
- Source SHA-256: `70df593278af5d0b804330802cababbafad7ce9f570e27eec7142d116afbf008`
- Retail room/script donor: field **376**, canonical bundle **1358**
- V171 destination: field **362**, canonical bundle **1330**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_362/07_dialogue.bin`, 209 bytes, `771a281f673fdb1433f6e8656e8c30324eacd5ce7ce0691b234be77b248f6e50`
- Inventory: **5 blocks / 5 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_376_transfer_airlock.authored.json -> blocks[id=0]`
- Window: 42 x 3; manual wrap: no
- Status: compiled into V171

```text
PRESSURE TRANSFER LOCK
ATMOSPHERE SEAL OPERABLE

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_376_transfer_airlock.authored.json -> blocks[id=1]`
- Window: 46 x 2; manual wrap: no
- Status: compiled into V171

```text
Equalizing chamber
pressure. Please wait.[Opcode:02:32]

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_376_transfer_airlock.authored.json -> blocks[id=2]`
- Window: 24 x 2; manual wrap: no
- Status: compiled into V171

```text
Equalization
complete.[Opcode:02:20]

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_376_transfer_airlock.authored.json -> blocks[id=3]`
- Window: 26 x 3; manual wrap: no
- Status: compiled into V171

```text
Venting inner
chamber.
Please wait.[Opcode:02:32]

[window closes]
```

#### Block 4

- Source locator: `modules/mass_driver/content/field_376_transfer_airlock.authored.json -> blocks[id=4]`
- Window: 26 x 2; manual wrap: no
- Status: compiled into V171

```text
Decompression
complete.[Opcode:02:20]

[window closes]
```

### 08. Field 727 - Zeboim three-door operations junction

- Dialogue text source: [field_377_inner_access.authored.json](../modules/mass_driver/content/field_377_inner_access.authored.json)
- Source SHA-256: `62c4f750ce55922429d4678b5da41803a37b2443f7032f33833979d6dbb23a9d`
- Retail room/script donor: field **377**, canonical bundle **1360**
- V171 destination: field **727**, canonical bundle **2060**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_727/07_dialogue.bin`, 493 bytes, `e1bfc0e3108b4f637db3cf380452776a6bfeac7444209ae06ca284960e243bed`
- Inventory: **5 blocks / 8 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_377_inner_access.authored.json -> blocks[id=0]`
- Window: 50 x 3; manual wrap: no
- Status: compiled into V171

```text
OPERATIONS JUNCTION
MAIN SERVICE HUB AHEAD

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_377_inner_access.authored.json -> blocks[id=1]`
- Window: 52 x 3; manual wrap: no
- Status: compiled into V171

```text
EAST PASSAGE
GUIDANCE AND MATERIALS

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_377_inner_access.authored.json -> blocks[id=2]`
- Window: 52 x 3; manual wrap: no
- Status: compiled into V171

```text
WEST PASSAGE
VERTICAL SERVICE SHAFT

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_377_inner_access.authored.json -> blocks[id=3]`
- Window: 52 x 3; manual wrap: no
- Status: compiled into V171

```text
CENTRAL PASSAGE
LAUNCH SUPPORT WORKS

[window closes]
```

#### Block 4

- Source locator: `modules/mass_driver/content/field_377_inner_access.authored.json -> blocks[id=4]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
PERSONNEL DESK
STORED SHIFT NOTICE

----- next page -----

Clock in before reporting to
your section. Record your
departure at the end of the
shift.

----- next page -----

If your relief does not
arrive, contact the shift
supervisor. Do not leave an
operating control station
unattended.

----- next page -----

Do not lend access badges.
Report a missing badge before
returning to work.

[window closes]
```

### 09. Field 372 - Zeboim four-door service hub

- Dialogue text source: [field_372_service_hub.authored.json](../modules/mass_driver/content/field_372_service_hub.authored.json)
- Source SHA-256: `dd6064497b64d864d7c916d9253fdd3764d2978a933b9a2db41ba820dc756cd7`
- Retail room/script donor: field **372**, canonical bundle **1350**
- V171 destination: field **372**, canonical bundle **1350**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_372/07_dialogue.bin`, 992 bytes, `523f8850a8e322eef30899cfbc701cb733737fe59cb57a5aeddb3bd86aed9919`
- Inventory: **9 blocks / 15 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_372_service_hub.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_372_service_hub.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_372_service_hub.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_372_service_hub.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_372_service_hub.authored.json -> blocks[id=4]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CENTRAL GATE
AUXILIARY GRID: NO POWER
ACCELERATOR BANKS: NO POWER

[window closes]
```

#### Block 5

- Source locator: `modules/mass_driver/content/field_372_service_hub.authored.json -> blocks[id=5]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
EMERGENCY DIRECTIVE
CONTROL AND RESEARCH ANNEX
WEST WING

[window closes]
```

#### Block 6

- Source locator: `modules/mass_driver/content/field_372_service_hub.authored.json -> blocks[id=6]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
FOUR-POINT AUTHORITY
MATERIALS STORAGE
LOWER EAST

[window closes]
```

#### Block 7

- Source locator: `modules/mass_driver/content/field_372_service_hub.authored.json -> blocks[id=7]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ACCELERATOR POWER
ARCHIVE CONSOLE D
MAGNETIC BANK INTERLOCK

[window closes]
```

#### Block 8

- Source locator: `modules/mass_driver/content/field_372_service_hub.authored.json -> blocks[id=8]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Dialogue text source: [field_373_control_research_annex.authored.json](../modules/mass_driver/content/field_373_control_research_annex.authored.json)
- Source SHA-256: `43fa980a397708066f824dcb4ed4443ae82cc7e0aa31a205fd67f690a8d10b74`
- Retail room/script donor: field **373**, canonical bundle **1352**
- V171 destination: field **361**, canonical bundle **1328**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_361/07_dialogue.bin`, 1,099 bytes, `7dbbacff39f8416d6ec7ec4940091e69d31281bd44290249fb9ac2f14978d211`
- Inventory: **4 blocks / 15 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_373_control_research_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CONTROL AND RESEARCH
CIRCUIT DIRECTORY

----- next page -----

The floor controls supply
Guidance, Control, and Launch
Safety through the auxiliary
grid.

----- next page -----

The accelerator banks use a
separate supply. Their
interlock is at Archive
Console D.

----- next page -----

MAINTENANCE RECORD / 6081
Command-line test
Connection lost for eleven
minutes.

----- next page -----

Local guidance remained
powered.

----- next page -----

SAFETY REVIEW
A launch order could remain
in local memory while the
command line was unable to
receive a recall.

----- next page -----

DIRECTIVE 0320

----- next page -----

During a strategic alert,
loss of contact does not
cancel a pending launch
order. Proceed unless a
recall has been received.

----- next page -----

INSTALLATION NOTE
Do not connect the auxiliary
grid to the accelerator
supply. The two circuits must
remain separate.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_373_control_research_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
AUXILIARY GRID
Manual bypass accepted.

----- next page -----

Guidance, Control, and Launch
Safety are now receiving
power.
Central Gate auxiliary
supply: ready.

----- next page -----

Accelerator supply is
controlled separately at
Archive Console D.

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_373_control_research_annex.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
EMERGENCY DIRECTIVE
0320

----- next page -----

For launch authorization,
enter this number at the
Defense Archive terminal
beyond Central Gate.

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_373_control_research_annex.authored.json -> blocks[id=3]`
- Window: 48 x 3; manual wrap: yes
- Status: compiled into V171

```text
[Opcode:01:FF]AUXILIARY RECORDS
  Close
  Read maintenance log

[window closes]
```

### 11. Field 722 - Zeboim materials storage annex

- Dialogue text source: [field_374_storage_annex.authored.json](../modules/mass_driver/content/field_374_storage_annex.authored.json)
- Source SHA-256: `2979813f35b444914c2e7852128a50a44d4af010e04524ae2b5fe73237b0b303`
- Retail room/script donor: field **374**, canonical bundle **1354**
- V171 destination: field **722**, canonical bundle **2050**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_722/07_dialogue.bin`, 1,784 bytes, `e54d48fc4d90127365d4dd35eb588cb40120cef481ff97e3041fdb9b0f5484dd`
- Inventory: **11 blocks / 24 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=0]`
- Window: 34 x 2; manual wrap: no
- Status: compiled into V171

```text
You have too many
[Opcode:04:14]

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=1]`
- Window: 40 x 2; manual wrap: no
- Status: compiled into V171

```text
Received [Opcode:04:14]

[window closes]

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=2]`
- Window: 52 x 3; manual wrap: no
- Status: compiled into V171

```text
DIRECTIVE RECORD REQUIRED
GUIDANCE ARCHIVE:
CONTROL AND RESEARCH

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=3]`
- Window: 54 x 3; manual wrap: no
- Status: compiled into V171

```text
FOUR-POINT AUTHORITY
NOT RECOVERED
Read this room's record.

[window closes]
```

#### Block 4

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=4]`
- Window: 48 x 3; manual wrap: no
- Status: compiled into V171

```text
DIRECTIVE 0320 RECORDED
AWAITING FOUR-POINT AUTHORITY

[window closes]
```

#### Block 5

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=5]`
- Window: 52 x 4; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]FOUR-POINT AUTHORITY
  A-2  B-5  C-8  D-4
  A-4  B-8  C-5  D-2
  A-5  B-2  C-4  D-8

[window closes]
```

#### Block 6

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=6]`
- Window: 50 x 3; manual wrap: no
- Status: compiled into V171

```text
DIRECTIVE 0320 ACCEPTED
FOUR-POINT AUTHORITY VERIFIED

[window closes]
```

#### Block 7

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=7]`
- Window: 48 x 3; manual wrap: no
- Status: compiled into V171

```text
AUTHORIZATION REJECTED
Entry does not match
archive record.

[window closes]
```

#### Block 8

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=8]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
MATERIALS CONTROL
PAYLOAD TRANSFER RECORD /
6079

----- next page -----

University weather package:
removed from launch queue.
Next survey carrier: removed
from launch queue.

----- next page -----

Replacement cargo: sealed.
Receiving authority:
Strategic Command.
Transfer ordered by the
Adviser's Office.

----- next page -----

MANIFEST CORRECTION

----- next page -----

The public schedule still
lists the survey carrier. Its
cradle has been removed.
Retain both schedules with
this transfer record.

----- next page -----

LAUNCH CREDENTIAL REGISTER
DIRECTIVE 0320
A-2 B-5 C-8 D-4

----- next page -----

Payload, Guidance, Safety,
and Accelerator Control each
hold one authority code. No
office may hold more than
one.

----- next page -----

EMERGENCY HANDOVER

----- next page -----

The Executive Office may
appoint replacements for
unavailable personnel.
Duplicate credentials are
held at Defense Archive.

----- next page -----

SAFETY POST / 09:10
Mara recorded as unavailable.
Replacement: Strategic
Command officer.
Authorization signed.

----- next page -----

ATTACHED CORRECTION / MARA
I was at my post at 09:10. I
did not authorize a
replacement. Please correct
the duty record.

----- next page -----

Correction request: closed.
Receipt and closure times are
identical.

----- next page -----

DEFENSE ARCHIVE TERMINAL
Enter 0320 first. Then enter
A-2, B-5, C-8, and D-4
separately.

[window closes]
```

#### Block 9

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=9]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
LAUNCH CREDENTIAL REGISTER
A-2 B-5 C-8 D-4

----- next page -----

At the Defense Archive
terminal, enter Directive
0320 first. Then enter each
authority code separately.

[window closes]
```

#### Block 10

- Source locator: `modules/mass_driver/content/field_374_storage_annex.authored.json -> blocks[id=10]`
- Window: 48 x 3; manual wrap: yes
- Status: compiled into V171

```text
[Opcode:01:FF]MATERIALS RECORDS
  Close
  Read transfer record

[window closes]
```

### 12. Field 723 - Zeboim sealed stair connector

- Dialogue text source: [field_375_service_connector.authored.json](../modules/mass_driver/content/field_375_service_connector.authored.json)
- Source SHA-256: `430a77ee4b4a3b5c03023663128e6b6402c4d77a75f76816e7212a5b21d06e66`
- Retail room/script donor: field **375**, canonical bundle **1356**
- V171 destination: field **723**, canonical bundle **2052**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_723/07_dialogue.bin`, 545 bytes, `80f6b4b331f6f2263a38211844f6810dc23b2c7bcdd3e876aafcbf6ac0a7eb02`
- Inventory: **5 blocks / 9 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_375_service_connector.authored.json -> blocks[id=0]`
- Window: 48 x 3; manual wrap: no
- Status: compiled into V171

```text
SAFETY LOCK ACTIVE
Reset emergency status at the
nearest terminal.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_375_service_connector.authored.json -> blocks[id=1]`
- Window: 54 x 4; manual wrap: no
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_375_service_connector.authored.json -> blocks[id=2]`
- Window: 40 x 3; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]Initiate local safety scan?
     Begin scan
     Cancel

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_375_service_connector.authored.json -> blocks[id=3]`
- Window: 44 x 4; manual wrap: no
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_375_service_connector.authored.json -> blocks[id=4]`
- Window: 42 x 3; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]SAFETY CLEARANCE NEEDED
Complete the local scan
before passing the seal.

[window closes]
```

### 13. Field 375 - Zeboim post-auxiliary sealed stair connector

- Dialogue text source: [field_375_post_aux_stair.authored.json](../modules/mass_driver/content/field_375_post_aux_stair.authored.json)
- Source SHA-256: `430a77ee4b4a3b5c03023663128e6b6402c4d77a75f76816e7212a5b21d06e66`
- Retail room/script donor: field **375**, canonical bundle **1356**
- V171 destination: field **375**, canonical bundle **1356**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_375/07_dialogue.bin`, 545 bytes, `80f6b4b331f6f2263a38211844f6810dc23b2c7bcdd3e876aafcbf6ac0a7eb02`
- Inventory: **5 blocks / 9 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_375_post_aux_stair.authored.json -> blocks[id=0]`
- Window: 48 x 3; manual wrap: no
- Status: compiled into V171

```text
SAFETY LOCK ACTIVE
Reset emergency status at the
nearest terminal.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_375_post_aux_stair.authored.json -> blocks[id=1]`
- Window: 54 x 4; manual wrap: no
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_375_post_aux_stair.authored.json -> blocks[id=2]`
- Window: 40 x 3; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]Initiate local safety scan?
     Begin scan
     Cancel

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_375_post_aux_stair.authored.json -> blocks[id=3]`
- Window: 44 x 4; manual wrap: no
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_375_post_aux_stair.authored.json -> blocks[id=4]`
- Window: 42 x 3; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]SAFETY CLEARANCE NEEDED
Complete the local scan
before passing the seal.

[window closes]
```

### 14. Field 387 - Zeboim vertical service connector

- Dialogue text source: [field_387_vertical_connector.authored.json](../modules/mass_driver/content/field_387_vertical_connector.authored.json)
- Source SHA-256: `3f161c1e5cc5dfa0c2d51bef293e1fa6f376104c4f5af801fd568a5acf0120a9`
- Retail room/script donor: field **387**, canonical bundle **1380**
- V171 destination: field **387**, canonical bundle **1380**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_387/07_dialogue.bin`, 51 bytes, `b7c1070c01d12587c0f9c9f4cd54f0c4855550e970d5d530d7b694137effa52d`
- Inventory: **1 blocks / 1 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_387_vertical_connector.authored.json -> blocks[id=0]`
- Window: 42 x 2; manual wrap: no
- Status: compiled into V171

```text
VERTICAL SERVICE SHAFT
TO MAGNETIC CONDUIT

[window closes]
```

### 15. Field 725 - Zeboim magnetic conduit hall

- Dialogue text source: [field_385_magnetic_conduit.authored.json](../modules/mass_driver/content/field_385_magnetic_conduit.authored.json)
- Source SHA-256: `b8f76031b8383207b36bb7eeaa9f861f59d99c44c1b2a658be2a69c2f67c79a7`
- Retail room/script donor: field **385**, canonical bundle **1376**
- V171 destination: field **725**, canonical bundle **2056**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_725/07_dialogue.bin`, 153 bytes, `647495ef6e491c2aaa9ef3c0a252505cb3b2fdd869b3ee5f6df15294948d14b5`
- Inventory: **2 blocks / 3 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_385_magnetic_conduit.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
LAUNCH-WORKS CONDUIT
REMOTE BANK CONTROL

----- next page -----

ARCHIVE CONSOLE D
ACCELERATOR INTERLOCK

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_385_magnetic_conduit.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
MAGNETIC JUNCTION
CENTRAL GATE AHEAD
DEFENSE ARCHIVE BEYOND

[window closes]
```

### 16. Field 726 - Zeboim launch-support hall

- Dialogue text source: [field_384_launch_support.authored.json](../modules/mass_driver/content/field_384_launch_support.authored.json)
- Source SHA-256: `269af24546a5ccc0c85472a36e36d231fed7ca93c6fc1e195bf15495b60f1cbf`
- Retail room/script donor: field **384**, canonical bundle **1374**
- V171 destination: field **726**, canonical bundle **2058**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_726/07_dialogue.bin`, 760 bytes, `a1c0c7652919ff9cb4b9355cfe4e81d4a4725e2f4231300328932031ea9e4b85`
- Inventory: **5 blocks / 13 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_384_launch_support.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CENTRAL GATE
Opening inhibited.
Auxiliary supply unavailable.

----- next page -----

SUPPLY CONTROL
Control and Research Annex
Auxiliary grid floor controls

----- next page -----

Both the auxiliary supply and
accelerator power are
required to open this gate.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_384_launch_support.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CENTRAL GATE
Opening inhibited.
Accelerator supply
unavailable.

----- next page -----

SUPPLY CONTROL
Archive Console D
Accelerator interlock

----- next page -----

Both the auxiliary supply and
accelerator power are
required to open this gate.

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_384_launch_support.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_384_launch_support.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CENTRAL GATE CONTROL
POWER INTERLOCKS READY

----- next page -----

EAST SERVICE STAIRS
DEFENSE ARCHIVE BEYOND

[window closes]
```

#### Block 4

- Source locator: `modules/mass_driver/content/field_384_launch_support.authored.json -> blocks[id=4]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CENTRAL GATE OPEN

----- next page -----

EAST SERVICE STAIRS
TO DEFENSE ARCHIVE

[window closes]
```

### 17. Field 366 - Zeboim launch-support archive A

- Dialogue text source: [field_366_archive_annex.authored.json](../modules/mass_driver/content/field_366_archive_annex.authored.json)
- Source SHA-256: `168f38d97c183d8463965c7dee24061244c02b0b51cd858533ba13aa22017c74`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V171 destination: field **366**, canonical bundle **1338**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_366/07_dialogue.bin`, 913 bytes, `a5dfee2fe3b54085d14ecfdb3e21185e9a7a1a2e6476908a3ae4ac2d023a1ba5`
- Inventory: **2 blocks / 11 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_366_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
PAYLOAD TEST STATION
ARCHIVED TEST / 6078
BANK TWO: SURVEY CRADLE

----- next page -----

TEST LOAD: INERT CASING
Guide clearance: acceptable
Cradle locks: secure
No damage found after
removal.

----- next page -----

ARON / SYSTEMS

----- next page -----

The new casing fits. Its
contents weren't listed on
the test request. Please send
the payload specifications
before we approve a launch.

----- next page -----

REQUEST AMENDED
PAYLOAD: STRATEGIC WARHEAD
Referred to Payload Safety.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_366_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
LAUNCH EQUIPMENT DESK
ARCHIVED WORK ORDER / 6079
BANK TWO CONVERSION

----- next page -----

Remove the survey cradle.
Install the MC-4 assembly and
check the guide clearance
before returning the bank to
service.

----- next page -----

Removed equipment is to be
returned to Civil Payload
Stores. Do not discard the
cradle or its instrument
connections.

----- next page -----

COMPLETION NOTE
MC-4 assembly installed.
Survey cradle packed for
storage.

----- next page -----

STORES REPLY

----- next page -----

The crate arrived without the
instrument connections. We
still need those if the
survey carrier is to fly
again.

[window closes]
```

### 18. Field 367 - Zeboim archive-branch operations junction

- Dialogue text source: [field_367_archive_junction.authored.json](../modules/mass_driver/content/field_367_archive_junction.authored.json)
- Source SHA-256: `b982dbd375ba2c6b9d9e2abbd780cd7aa95569cd59a5045ae5adbde58e022f8e`
- Retail room/script donor: field **377**, canonical bundle **1360**
- V171 destination: field **367**, canonical bundle **1340**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_367/07_dialogue.bin`, 105 bytes, `e35f3e204abe8727e9282786951493065b4a8b0ed11344695db0f99ec0a665df`
- Inventory: **1 blocks / 1 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_367_archive_junction.authored.json -> blocks[id=0]`
- Window: 54 x 4; manual wrap: no
- Status: compiled into V171

```text
ARCHIVE BRANCH JUNCTION
WEST: CIVIL PAYLOAD STORES
SOUTH: STRATEGIC STORES
NORTH: LAUNCH SUPPORT

[window closes]
```

### 19. Field 385 - Zeboim civil-payload stores

- Dialogue text source: [field_385_storage_treasure_annex.authored.json](../modules/mass_driver/content/field_385_storage_treasure_annex.authored.json)
- Source SHA-256: `33b4364c56a2dbd592e4c1aa9ad5a0aade4e9a77217c89189a08096693059fdb`
- Retail room/script donor: field **374**, canonical bundle **1354**
- V171 destination: field **385**, canonical bundle **1376**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_385/07_dialogue.bin`, 648 bytes, `0ead3546aeb07dc8e54c34b7f57df91895534f313dba8ba0d6bab98a87f99d83`
- Inventory: **3 blocks / 11 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_385_storage_treasure_annex.authored.json -> blocks[id=0]`
- Window: 34 x 2; manual wrap: no
- Status: compiled into V171

```text
You have too many
[Opcode:04:14]

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_385_storage_treasure_annex.authored.json -> blocks[id=1]`
- Window: 40 x 2; manual wrap: no
- Status: compiled into V171

```text
Received [Opcode:04:14]

[window closes]

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_385_storage_treasure_annex.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CIVIL PAYLOAD STORES
ARCHIVED SHIPPING RECORDS
YEAR 6072

----- next page -----

SURVEY CARRIER THREE

----- next page -----

Atmospheric instruments and
unmanned probe checked and
packed. The probe will use
its own engines above the
atmosphere.

----- next page -----

DISPATCH: LAUNCH CREW
Received in good condition.

----- next page -----

LENA / TO: ARON

----- next page -----

Mira wants to know what the
probe will find. I said we
had to send it first. Now she
wants to watch the launch. Is
there room for her?

----- next page -----

ARON / SYSTEMS
I'll save her a seat.

----- next page -----

YEAR 6079 / STOCK UPDATE
Survey cradle returned from
Bank Two. Instrument
connections missing.

----- next page -----

Weather package retained in
storage. No launch date
assigned.

[window closes]
```

### 20. Field 386 - Zeboim strategic-payload stores

- Dialogue text source: [field_386_storage_treasure_annex.authored.json](../modules/mass_driver/content/field_386_storage_treasure_annex.authored.json)
- Source SHA-256: `ca1a1dac4cea9888561791752a09022bd7a35377fda778b42fdd7530ab7fdd1e`
- Retail room/script donor: field **374**, canonical bundle **1354**
- V171 destination: field **386**, canonical bundle **1378**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_386/07_dialogue.bin`, 684 bytes, `bce41a348427915504eabed50c142c3d3e2c337721310eb032e382ef97507adc`
- Inventory: **3 blocks / 9 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_386_storage_treasure_annex.authored.json -> blocks[id=0]`
- Window: 34 x 2; manual wrap: no
- Status: compiled into V171

```text
You have too many
[Opcode:04:14]

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_386_storage_treasure_annex.authored.json -> blocks[id=1]`
- Window: 40 x 2; manual wrap: no
- Status: compiled into V171

```text
Received [Opcode:04:14]

[window closes]

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_386_storage_treasure_annex.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
STRATEGIC PAYLOAD STORES
ARCHIVED RECEIPT / 6079
MC-4 CRADLE ASSEMBLY

----- next page -----

Received from Strategic
Command. Shipping seals
intact. Mounting points
checked against the Bank Two
drawings.

----- next page -----

SAFETY REVIEW / MARA
Mechanical fit is acceptable.
Launch certification is
refused.

----- next page -----

MC-4 replaces a civil
instrument bay with a
strategic warhead cradle, in
violation of Launch Charter
11.

----- next page -----

TRANSFER RECORD
Assembly issued to Bank Two
under alternate approval.
Safety refusal retained with
receipt.

----- next page -----

STORES NOTE

----- next page -----

The civil cradle came back in
the same crate. Its packing
list still says MC-4. Please
correct the label before
anyone sends it out again.

[window closes]
```

### 21. Field 368 - Zeboim launch-support archive C

- Dialogue text source: [field_368_archive_annex.authored.json](../modules/mass_driver/content/field_368_archive_annex.authored.json)
- Source SHA-256: `a593854dc7bedb9558039b59a3533045af7ceabf708977abf1e9ded65cc47c19`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V171 destination: field **368**, canonical bundle **1342**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_368/07_dialogue.bin`, 823 bytes, `90c492cbc47d35ac4dcece222c5bb1083d2e3e3d93274419bdafbe04ce462616`
- Inventory: **2 blocks / 10 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_368_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ARCHIVE CONSOLE D
ACCELERATOR INTERLOCK

----- next page -----

Bank test accepted.
Accelerator supply restored.
Magnetic banks responding.

----- next page -----

CENTRAL GATE
Accelerator power requirement
satisfied.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_368_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ACCELERATOR SERVICE RECORD
ARCHIVED SHIFT LOG / 6081
OPERATOR: ARON

----- next page -----

Cooling pumps checked after
the power failure. Bank Two
stopped at the thermal limit
during the recharge test. No
damage found.

----- next page -----

Command has requested
continuous readiness. That
requires bypassing the
thermal cutoff.

----- next page -----

Cooling time between charges
is still necessary.

----- next page -----

SHIFT ADDENDUM
Bypass fitted by Aron.
Temperature must be watched
from the control desk while
the bank is charging.

----- next page -----

ARON / TO: LENA
I told them it was ready.
Perhaps that will be enough.
I don't want to find out how
long we can keep doing this.

----- next page -----

TERMINAL DIRECTORY
ACCELERATOR INTERLOCK
CONTROL: MAIN CONSOLE

[window closes]
```

### 22. Field 369 - Zeboim launch-support archive D

- Dialogue text source: [field_369_archive_annex.authored.json](../modules/mass_driver/content/field_369_archive_annex.authored.json)
- Source SHA-256: `f87e5fae000400cb2a47ff5f837a9026c295975bf47fcc92c34c0095a17c852a`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V171 destination: field **369**, canonical bundle **1344**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_369/07_dialogue.bin`, 1,013 bytes, `f889c48dc146107e1794a057eebf8add522acfa22e34c0b8706e42e62053cf84`
- Inventory: **2 blocks / 13 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_369_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
GUIDANCE DATA STATION
ARCHIVED FILE INDEX / 6079
LAUNCH COURSES

----- next page -----

SURVEY CARRIER THREE
Transferred to civil archive.
WEATHER PACKAGE
Transferred to civil archive.

----- next page -----

STRATEGIC TARGET TABLES
Loaded for testing.

----- next page -----

GUIDANCE NOTE / LENA

----- next page -----

The new tables use the same
carrier numbers as the survey
flights. The name on the
screen no longer tells us
what we're launching.

----- next page -----

Request separate names for
the strategic loads. Until
then, check the payload
manifest against the course
file before every test.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_369_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
GUIDANCE CONTROL DESK
ARCHIVED HANDOVER / 6081
FROM: LENA / GUIDANCE

----- next page -----

Bank Two's bearing display
lagged during the alignment
test. The position sensor was
correct.

----- next page -----

The display has been replaced
and the test repeated.

----- next page -----

Do not copy the test results
to Bank Four. That bank has
not been checked.

----- next page -----

COMMAND REQUEST
Report both banks ready. Bank
Four passed its previous
inspection.

----- next page -----

LENA / GUIDANCE

----- next page -----

That was before the power
failure. Bank Two passed
then, too. I'm leaving Bank
Four off the report until
someone checks it.

[window closes]
```

### 23. Field 370 - Zeboim launch-support archive E

- Dialogue text source: [field_370_archive_annex.authored.json](../modules/mass_driver/content/field_370_archive_annex.authored.json)
- Source SHA-256: `4663eac440b8a3f08739d1dd070ac84858ee27ea7f60caec4552b0efc6fb4d8f`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V171 destination: field **370**, canonical bundle **1346**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_370/07_dialogue.bin`, 996 bytes, `ba2d55072b560e093e49d3f116cb5b029adab7f596b871eb2ba1b35854bc1149`
- Inventory: **2 blocks / 12 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_370_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
AUXILIARY POWER STATION
ARCHIVED INSPECTION / 6081
STANDBY GENERATORS

----- next page -----

Two portable units tested
under load. Both started
normally and held their
output for the full test.

----- next page -----

One outlet cover is missing.
Replacement requested. Cables
and fuel lines have been
packed with the units.

----- next page -----

DESTINATION: CAPITAL CLINICS
Prepared for collection.
Transport release pending.

----- next page -----

HANDOVER NOTE

----- next page -----

The clinic crew needs the
cables as well as the
generators. They cannot use
the units without them. Check
both crates before loading.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_370_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
EQUIPMENT DISPATCH DESK
ARCHIVED TRANSFER / 6081
TWO STANDBY GENERATORS

----- next page -----

REQUEST: MEDICAL BUREAU

----- next page -----

The capital's clinics cannot
rely on the damaged power
grid. Please release the two
units prepared for
collection.

----- next page -----

DISPATCH STATUS

----- next page -----

Transfer cancelled by
Command. Units retained for
control-room backup power.
Clinic crew departed without
equipment.

----- next page -----

MARA / PAYLOAD SAFETY
The units were tested and
packed. Remove 'equipment
unavailable' from the reply.
Command decided to keep them.

[window closes]
```

### 24. Field 371 - Zeboim launch-support archive F

- Dialogue text source: [field_371_archive_annex.authored.json](../modules/mass_driver/content/field_371_archive_annex.authored.json)
- Source SHA-256: `b020dda7e8a0ea7dd5a6e5f917b9854cf4bc4b410b32042240446b22b03cca2a`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V171 destination: field **371**, canonical bundle **1348**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_371/07_dialogue.bin`, 1,043 bytes, `793aa5330521c72ce4b490d6cd3b7853dbfed4c403eb28afd7737a2f7387ad38`
- Inventory: **2 blocks / 14 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_371_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
PAYLOAD SAFETY STATION
ARCHIVED INSPECTION / 6079
INSPECTOR: MARA

----- next page -----

A loaded cradle was moved
while a technician was still
checking its locks. No injury
reported.

----- next page -----

The movement was ordered from
the control desk.

----- next page -----

The operator could see the
cradle on the monitor. He
could not see the technician
behind it.

----- next page -----

Do not accept a camera check
in place of clearance from
the loading crew.

----- next page -----

Keep the movement key at the
cradle until the inspection
is finished.

----- next page -----

FOLLOW-UP

----- next page -----

Movement key retained by the
loading crew during the next
test. No further movement
orders received before
clearance.

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_371_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
PERSONNEL ACCESS DESK
ARCHIVED REGISTER / 6081
STRATEGIC LOADING AREA

----- next page -----

ACCESS LIST REVISED
Civil project passes no
longer permit entry.
Strategic Command must
approve each visit.

----- next page -----

ENTRY REFUSED
Lena / Guidance
Purpose: recover survey
equipment.

----- next page -----

DESK NOTE

----- next page -----

Her name is on the equipment
record, but not the access
list. Stores has confirmed
that the equipment belongs to
the civil project.

----- next page -----

Request sent to Command. No
reply recorded before the end
of the shift.

[window closes]
```

### 25. Field 724 - Zeboim launch-support archive G

- Dialogue text source: [field_724_archive_annex.authored.json](../modules/mass_driver/content/field_724_archive_annex.authored.json)
- Source SHA-256: `f373018959c0237f6cd38df3ecacf9386bfd6c8dfb1d4720fbb27380deb9891d`
- Retail room/script donor: field **378**, canonical bundle **1362**
- V171 destination: field **724**, canonical bundle **2054**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_724/07_dialogue.bin`, 986 bytes, `f330f55f94a71bba58511a199a43f089d283d9f51ef47f4f0e403ea3739a641f`
- Inventory: **2 blocks / 15 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_724_archive_annex.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
LAUNCH DUTY STATION
ARCHIVED FINAL SHIFT / 6083
OPERATOR: ARON

----- next page -----

Release order received. Bank
Four banks opened. Local
abort refused. Request for
recall sent to Central
Control.

----- next page -----

STAFF MESSAGE
FROM: ARON / TO: LENA

----- next page -----

Mira is in Shelter Four. If
you can reach her, stay with
her. Don't come back here for
me.

----- next page -----

UNSENT / LENA
Mira, it's Lena. Are you
there? Please answer.

----- next page -----

TRANSMISSION LOST
No later entry recovered.

----- next page -----

EMERALDA:

"What happened to Mira...?"

----- next page -----

ELLY:

"I don't know..."

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_724_archive_annex.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
LAUNCH CONTROL DESK
ARCHIVED RECALL RECORD / 6083
DIRECTIVE 0320

----- next page -----

GUIDANCE REPORT
Warning stations show
different tracks. An attack
cannot be confirmed from
these reports.

----- next page -----

LAUNCH DIRECTOR
Request recall of Directive
0320 pending confirmation.

----- next page -----

EXECUTIVE ORDER
Recall not authorized.
Continue launch preparations.

----- next page -----

LAUNCH RECORD
Final order: Launch Director
Authority points: accepted
Strategic release: confirmed

----- next page -----

BANK FOUR
Local abort requested.
REPLY: BANKS ALREADY OPEN

----- next page -----

COMMAND LINK LOST
RESERVE MAGAZINES SEALED

[window closes]
```

### 26. Field 376 - Zeboim autonomous-defense archive

- Dialogue text source: [field_394_defense_archive.authored.json](../modules/mass_driver/content/field_394_defense_archive.authored.json)
- Source SHA-256: `e9f943e5946e99e8ebea56eadc7bdca197b75854aa16bc2eb6253d4bb4b3c88e`
- Retail room/script donor: field **394**, canonical bundle **1394**
- V171 destination: field **376**, canonical bundle **1358**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_376/07_dialogue.bin`, 6,930 bytes, `1fe0ee2576d3860f9fb84179d990882e6eb4b8eae0c9b5f662116e8f1ecb15ad`
- Inventory: **42 blocks / 96 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
DIRECTIVE NUMBER REQUIRED
No recovered directive
record.

----- next page -----

You may enter the number
manually. A copy is kept in
the Control and Research
Annex, back through the east
stairs.

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
FOUR AUTHORITY CODES REQUIRED
No recovered credential
record.

----- next page -----

You may enter the codes
manually. A copy is kept in
Materials Storage, back
through the east stairs.

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
LAUNCH AUTHORIZATION
Directive 0320 accepted.
All four authority codes
verified.

----- next page -----

Defense Bay lift: unlocked.
Use the lift on the north
wall.

----- next page -----

West bulkhead status is
displayed at the local
control panel.

[window closes]
```

#### Block 4

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=4]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]DIRECTIVE NUMBER
  0320
  0302
  3200

[window closes]
```

#### Block 5

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=5]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]AUTHORITY POINT A
  A-2
  A-4
  A-5

[window closes]
```

#### Block 6

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=6]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
DIRECTIVE 0320 ACCEPTED
A-2 B-5 C-8 D-4
AUTHORITY VERIFIED

----- next page -----

Launch authorization
recorded.
North-wall lift unlocked.
Custodian defense: active.

----- next page -----

ELLY:

"The lift is working. But the
defense system is still
active..."

----- next page -----

ELLY:

"We'd better check our
equipment before we go down."

[window closes]
```

#### Block 7

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=7]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CODE ERROR
One or more entries are
incorrect.

----- next page -----

Enter Directive 0320 first,
then each authority code in
order from A to D.

[window closes]
```

#### Block 8

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=8]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=9]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
DEFENSE BAY LIFT
Access locked.

----- next page -----

Enter Directive 0320 and the
four authority codes at the
wall console.

[window closes]
```

#### Block 10

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=10]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
WEST BULKHEAD
Local release required.

----- next page -----

Use the west control panel
after the Custodian defense
system has been disabled.

[window closes]
```

#### Block 11

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=11]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"Enter 0320 first. Then A-2,
B-5, C-8, and D-4.
One value at a time."

[window closes]
```

#### Block 12

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=12]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"The defense system is down
and the bulkhead is open.
Central Control lies beyond
the fifth magazine."

[window closes]
```

#### Block 13

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=13]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]AUTHORITY POINT B
  B-2
  B-5
  B-8

[window closes]
```

#### Block 14

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=14]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]AUTHORITY POINT C
  C-4
  C-5
  C-8

[window closes]
```

#### Block 15

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=15]`
- Window: 34 x 4; manual wrap: no
- Status: compiled into V171

```text
[Opcode:01:FF]AUTHORITY POINT D
  D-2
  D-4
  D-8

[window closes]
```

#### Block 16

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=16]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CIVIL DEFENSE
SAVED SITUATION REPORT

----- next page -----

Public power failures are
becoming more frequent. Urban
violence is disrupting food
distribution. The economy
continues to contract.

----- next page -----

Rival governments report
similar failures. Each
attributes the crisis to
foreign interference.

----- next page -----

Emergency powers have been
expanded.

----- next page -----

DIRECTOR'S BRIEFING

----- next page -----

The Adviser's Office has
requested increased military
readiness. No expansion of
shelter capacity is included
in the order.

[window closes]
```

#### Block 17

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=17]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=18]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
DEFENSE BAY
ACCESS INSTRUCTIONS

----- next page -----

Complete launch authorization
at the wall console to unlock
the north lift.

----- next page -----

Authorization grants access
to the bay. It does not shut
down the Custodian defense
system.

----- next page -----

The west bulkhead has a
separate control panel. Its
release is locked while
Custodian defense remains
active.

[window closes]
```

#### Block 19

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=19]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
WEST BULKHEAD
ARCHIVED CIVIL DEFENSE REVIEW

----- next page -----

This bulkhead separates the
control room from the reserve
magazines. Closing it does
not make this room a public
fallout shelter.

----- next page -----

The shelter plan does not
provide enough space for the
civilian population. Sealing
the magazines will not
correct that shortage.

----- next page -----

STRATEGIC ASSESSMENT
Limited strike, first strike,
and retaliation all lead to a
full nuclear exchange in the
current model.

----- next page -----

Projected civilian survival
is too low to sustain
recovery.

----- next page -----

DISPOSITION
Military readiness increased.
Report withheld from public
release.

[window closes]
```

#### Block 20

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=20]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
LAUNCH ORDER CONTROL
DIRECTIVE 0320

----- next page -----

CURRENT STATUS
Central Command: no
connection.
Recall order: not received.
Directive: active.

----- next page -----

REVISION HISTORY / 6081
Previous instruction: suspend
a pending launch if contact
with Central Command is lost.

----- next page -----

Replacement instruction:
carry out the pending launch
order unless a recall has
been received.

----- next page -----

Revision authority: Prime
Minister's Adviser.
Expiration clause removed.
No review date.

[window closes]
```

#### Block 21

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=21]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
LAUNCH DUTY REGISTER
SAVED RELEASE RECORD

----- next page -----

Release authorized by:
Facility Director.
Director's signature:
verified.

----- next page -----

Supporting orders:
Strategic access order.
Safety waivers.
Directive 0320 revision.

----- next page -----

All supporting orders were
routed through the Prime
Minister's Adviser.

----- next page -----

Adviser's signature on
release: none.

----- next page -----

RECORD QUERY / MARA

----- next page -----

Please send the authorization
for the Safety waiver. The
release record names the
director, but the waiver came
from the Adviser's Office.

[window closes]
```

#### Block 22

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=22]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"A video disk... This one
looks all right."

----- next page -----

ELLY:

"We could try playing it on
the computer to the right."

[window closes]
```

#### Block 23

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=23]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ZBC ARCHIVE
Insert a Video Disk.

[window closes]
```

#### Block 24

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=24]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ZBC NEWS ARCHIVE
RECORDINGS: 6081-6083

----- next page -----

Video Disk accepted.
Starting playback...

[window closes]
```

#### Block 25

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=25]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
Food is disappearing from the
capital's markets. Private
dining rooms in the wealthy
districts, however, remain
well supplied.

----- next page -----

Aid groups have asked their
owners to release food and
fuel for public distribution.
Most have refused.

[window closes]
```

#### Block 26

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=26]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
Meanwhile, the country's
wealthiest families are
buying private fallout
shelters.

----- next page -----

Builders advertise gardens,
medical facilities, and
provisions to last for years.

[window closes]
```

#### Block 27

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=27]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
Across the country, food
lines begin before dawn.

----- next page -----

Children wait in the cold
outside distribution centers
with nothing left to give
them.

----- next page -----

Farmland lies abandoned. Rail
deliveries to the poorest
districts have stopped.

[window closes]
```

#### Block 28

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=28]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
In the capital, crowds from
poorer districts have set
fire to homes in wealthy
neighborhoods. Families have
been killed inside.

----- next page -----

Police and military units
have withdrawn from three
wealthy districts. Further
fires are being reported.

[window closes]
```

#### Block 29

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=29]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
Births have remained below
replacement level for twelve
years. Infertility and
hereditary illness continue
to increase.

----- next page -----

Average life expectancy is
now approaching thirty.

----- next page -----

Officials have warned
privately that the nation may
not survive another
generation.

[window closes]
```

#### Block 30

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=30]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ZBC ARCHIVE / NEXT RECORDING
EMERGENCY BROADCAST / 6083

----- next page -----

We interrupt this program. A
nuclear missile has been
launched.

----- next page -----

Retaliatory launches are
being reported by several
nuclear-armed states. We are
losing contact with military
command.

----- next page -----

Take shelter immediately.
Anyone receiving this
broadcast, take shelter. This
is not a drill.

[window closes]
```

#### Block 31

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=31]`
- Window: 40 x 2; manual wrap: yes
- Status: compiled into V171

```text
Received Video Disk

[window closes]

[window closes]
```

#### Block 32

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=32]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"The other disks are too
badly damaged."

[window closes]
```

#### Block 33

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=33]`
- Window: 40 x 3; manual wrap: yes
- Status: compiled into V171

```text
[Opcode:01:FF]INSERT VIDEO DISK?
     Insert disk
     Cancel

[window closes]
```

#### Block 34

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=34]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"We don't have room for the
Video Disk."

[window closes]
```

#### Block 35

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=35]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ZBC EVENING REPORT / 6081
CELIA REN, ANCHOR

----- next page -----

Good evening. Food shortages
continue in the capital,
where unrest has turned
violent.

[window closes]
```

#### Block 36

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=36]`
- Window: 40 x 3; manual wrap: yes
- Status: compiled into V171

```text
[Opcode:01:FF]Take the Video Disk?
     Take it
     Leave it

[window closes]
```

#### Block 37

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=37]`
- Window: 40 x 4; manual wrap: yes
- Status: compiled into V171

```text
[Opcode:01:FF]MEDIA TERMINAL
     Arcade Games
     Video Disk
     Leave

[window closes]
```

#### Block 38

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=38]`
- Window: 40 x 4; manual wrap: yes
- Status: compiled into V171

```text
[Opcode:01:FF]ARCADE DIRECTORY
     Play NUKE
     Missile Command
     Back

[window closes]
```

#### Block 39

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=39]`
- Window: 58 x 4; manual wrap: yes
- Status: compiled into V171

```text
[Opcode:01:FF]WEST BULKHEAD CONTROL
     Operate bulkhead
     Read safety report
     Leave

[window closes]
```

#### Block 40

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=40]`
- Window: 58 x 2; manual wrap: yes
- Status: compiled into V171

```text
CUSTODIAN DEFENSE ACTIVE
BULKHEAD RELEASE LOCKED

[window closes]
```

#### Block 41

- Source locator: `modules/mass_driver/content/field_394_defense_archive.authored.json -> blocks[id=41]`
- Window: 42 x 1; manual wrap: yes
- Status: compiled into V171

```text
WEST BULKHEAD OPEN

[window closes]
```

### 27. Field 384 - Goliath Factory Gear staging and Guardian hall

- Dialogue text source: [field_260_goliath_factory_hall.authored.json](../modules/mass_driver/content/field_260_goliath_factory_hall.authored.json)
- Source SHA-256: `b1cea069cce875ce7631bf57e159a227e5f8cf8c2d4c142d7c04b87200dbc10a`
- Retail room/script donor: field **260**, canonical bundle **1126**
- V171 destination: field **384**, canonical bundle **1374**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_384/07_dialogue.bin`, 966 bytes, `bcea17f7583c8190e9a7815a82ee73929df5960ff0a72d076e961a833ad03682`
- Inventory: **8 blocks / 21 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_260_goliath_factory_hall.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

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

- Source locator: `modules/mass_driver/content/field_260_goliath_factory_hall.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
VIERGE
PILOT LINK: ELLY
READY

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_260_goliath_factory_hall.authored.json -> blocks[id=2]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
CRESCENS
PILOT LINK: EMERALDA
READY

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_260_goliath_factory_hall.authored.json -> blocks[id=3]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"There they are. Citan got
them inside."

----- next page -----

EMERALDA:

"Crescens!"

----- next page -----

GUARDIAN CONTROL
Defense inhibit rejected.
Custodian frame deploying.

----- next page -----

ELLY:

"Emeralda, get to Crescens!"

----- next page -----

EMERALDA:

"Hurry, Elly!"

----- next page -----

ELLY:

"I'm coming!"

[window closes]
```

#### Block 4

- Source locator: `modules/mass_driver/content/field_260_goliath_factory_hall.authored.json -> blocks[id=4]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
ELLY:

"Emeralda, are you all
right?"

----- next page -----

EMERALDA:

"I'm all right. Elly?"

----- next page -----

ELLY:

"Yes..."

----- next page -----

Custodian core offline.
West bulkhead release
enabled.

----- next page -----

ELLY:

"We can open the west
bulkhead now. The control
panel is upstairs."

----- next page -----

ELLY:

"We'll have to leave the
Gears here. They won't fit
through the passage
upstairs."

----- next page -----

ELLY:

"We'll come back for them
after the launch."

[window closes]
```

#### Block 5

- Source locator: `modules/mass_driver/content/field_260_goliath_factory_hall.authored.json -> blocks[id=5]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
NORTH TRANSFER DOOR
Local controls unavailable.
Door cannot be opened here.

[window closes]
```

#### Block 6

- Source locator: `modules/mass_driver/content/field_260_goliath_factory_hall.authored.json -> blocks[id=6]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
SOUTH PERSONNEL ACCESS
CLEARANCE: HUMAN SCALE ONLY

[window closes]
```

#### Block 7

- Source locator: `modules/mass_driver/content/field_260_goliath_factory_hall.authored.json -> blocks[id=7]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled into V171

```text
EMERALDA:

"Elly... I want to tell Fei."

----- next page -----

ELLY:

"So do I... Come on. Citan's
gone on ahead."

[window closes]
```

### 28. Field 377 - Containment vault 1 of 5

- Dialogue text source: [field_673_silo_vault_1.authored.json](../modules/mass_driver/content/field_673_silo_vault_1.authored.json)
- Source SHA-256: `5a25117d91e95823c3f7581731644539920b32a678bdd7e1112b1fc3231f3ea9`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V171 destination: field **377**, canonical bundle **1360**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_377/07_dialogue.bin`, 188 bytes, `3df9676da9ba74d8823ca160e237a17a09a94dffbfd360446862d50350ab364d`
- Inventory: **1 blocks / 4 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_673_silo_vault_1.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V171

```text
RESERVE MAGAZINE 01 / 05
STORAGE INVENTORY
Strategic missiles and
rockets.

----- next page -----

Target network: no
connection.

----- next page -----

ELLY:

"Missiles... And look at
the size of those
rockets!"

----- next page -----

EMERALDA:

"So many..."

[window closes]
```

### 29. Field 378 - Containment vault 2 of 5

- Dialogue text source: [field_673_silo_vault_2.authored.json](../modules/mass_driver/content/field_673_silo_vault_2.authored.json)
- Source SHA-256: `f5148d92a740463fbf71cd7cd533c627f7c30c64d2463c28de17b4c128759762`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V171 destination: field **378**, canonical bundle **1362**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_378/07_dialogue.bin`, 254 bytes, `ecba51c897daad7eaf3abaffdfcf3f05d2a5293a61ca34db7211980ee564a2a2`
- Inventory: **1 blocks / 4 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_673_silo_vault_2.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V171

```text
RESERVE MAGAZINE 02 / 05
PAYLOAD HANDLING NOTICE

----- next page -----

Launch authorization does
not make a stored warhead
safe to handle.

----- next page -----

Leave loaded rockets in
their cradles.

----- next page -----

DISPATCH RECORD / 6083
Battery release confirmed.
Counterstrikes detected.
End of record.

[window closes]
```

### 30. Field 379 - Containment vault 3 of 5

- Dialogue text source: [field_673_silo_vault_3.authored.json](../modules/mass_driver/content/field_673_silo_vault_3.authored.json)
- Source SHA-256: `9c7825da21cdd10d17e68a7a75f844d88bfff8c6e544744ace1d63c06931910f`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V171 destination: field **379**, canonical bundle **1364**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_379/07_dialogue.bin`, 317 bytes, `1c57cb0875239937ca755e16589657c925a7e38d59a80eef3c4226911102c63f`
- Inventory: **1 blocks / 5 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_673_silo_vault_3.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V171

```text
RESERVE MAGAZINE 03 / 05
TARGETING LINK:
DISCONNECTED
STORAGE CRADLES: POWERED

----- next page -----

MAINTENANCE ENTRY / ARON

----- next page -----

Targeting link
disconnected before
evacuation.

----- next page -----

Leave it disconnected when
restoring power. The
storage cradles use a
separate circuit.

----- next page -----

ELLY:

"There's still power in
the cradles. Don't touch
them, Emeralda."

[window closes]
```

### 31. Field 382 - Containment vault 4 of 5

- Dialogue text source: [field_673_silo_vault_4.authored.json](../modules/mass_driver/content/field_673_silo_vault_4.authored.json)
- Source SHA-256: `aeab9ee53218c52dde93930692889097835712852c56385f5d175459202de693`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V171 destination: field **382**, canonical bundle **1370**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_382/07_dialogue.bin`, 171 bytes, `992b6aa9124dd0641f5f7351e88c6f9c4bb17cea074fade189e3c479f66a8710`
- Inventory: **1 blocks / 3 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_673_silo_vault_4.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V171

```text
RESERVE MAGAZINE 04 / 05
COMMUNICATIONS RECORD

----- next page -----

Central Command: no
connection.
Shelters: no connection.
Repeated calls: no reply.

----- next page -----

Recording ended at grid
failure.

[window closes]
```

### 32. Field 383 - Containment vault 5 of 5

- Dialogue text source: [field_673_silo_vault_5.authored.json](../modules/mass_driver/content/field_673_silo_vault_5.authored.json)
- Source SHA-256: `721ddbc7fd10af714c627d071590bf1d6e55a856871808b04841cdafdc64dc9c`
- Retail room/script donor: field **673**, canonical bundle **1952**
- V171 destination: field **383**, canonical bundle **1372**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_383/07_dialogue.bin`, 134 bytes, `3af4b64ae599d271a9bf48c5f58e73c92c07b6576010066516b7a29b2bc60b61`
- Inventory: **1 blocks / 2 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_673_silo_vault_5.authored.json -> blocks[id=0]`
- Window: 52 x 4; manual wrap: yes
- Status: compiled into V171

```text
RESERVE MAGAZINE 05 / 05
Target data: lost.
Central Control: north
exit.

----- next page -----

ELLY:

"Here in the dark... they
look like tombstones."

[window closes]
```

### 33. Field 728 - Zeboim Mass Driver central control

- Dialogue text source: [field_369_archive_control.authored.json](../modules/mass_driver/content/field_369_archive_control.authored.json)
- Source SHA-256: `2878714bd1b3f080abba6ebca9b61e4af3e5ac924c4b797e94d1285cfdc52d9d`
- Retail room/script donor: field **369**, canonical bundle **1344**
- V171 destination: field **728**, canonical bundle **2062**
- Compiled component: `builds/mass_driver/mass-driver-v171-dialogue/stage/clones/field_728/07_dialogue.bin`, 4,107 bytes, `e9ed097c8018189f5cded7cffac3885578a2b6ecad4e06e85e0be45fe63d2d99`
- Inventory: **37 blocks / 68 pages**

#### Block 0

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=0]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
ELLY:

"Central Control..."

[window closes]
```

#### Block 1

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=1]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
ELLY:

"This one... It doesn't look
like the other terminals."

[window closes]
```

#### Block 2

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=2]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 02
Launch weather records.

[window closes]
```

#### Block 3

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=3]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 03
Space-program guidance.

[window closes]
```

#### Block 4

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=4]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 04
Guidance calibration.

[window closes]
```

#### Block 5

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=5]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 05
Emergency power transfer.

[window closes]
```

#### Block 6

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=6]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 06
Personnel evacuation.

[window closes]
```

#### Block 7

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=7]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 07
Payload inventory.

[window closes]
```

#### Block 8

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=8]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 08
Network failure report.

[window closes]
```

#### Block 9

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=9]`
- Window: 46 x 2; manual wrap: no
- Status: compiled; dormant/orphan-reference-only

```text
ARCHIVE INDEX 09
Final maintenance order.

[window closes]
```

#### Block 10

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=10]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; dormant/orphan-reference-only

```text
CAPSULE CRADLE
NANOMACHINE PAYLOAD SECURED
LAUNCH CONSOLE READY

[window closes]
```

#### Block 11

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=11]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
LAUNCH CONTROL
Release authorization not
received.

----- next page -----

Authorize at the Defense
Archive wall console.
Directive: 0320
Codes: A-2 / B-5 / C-8 / D-4

----- next page -----

ACCESS ROUTE
Return through the five
reserve magazines.

[window closes]
```

#### Block 12

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=12]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
NANOMACHINE CAPSULE SECURED
Launch authorization
confirmed.
Payload link established.

----- next page -----

Guidance power normal.
Magnetic banks ready.
Ascent path clear.

----- next page -----

ELLY:

"The capsule's connected.
Now, the guidance..."

----- next page -----

EMERALDA:

"Elly?"

----- next page -----

ELLY:

"It keeps drifting. If we
launch like this, we could
lose the capsule."

----- next page -----

ELLY:

"Citan should be here soon.
I'd like him to look at it."

[window closes]
```

#### Block 13

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=13]`
- Window: 52 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
The terminal requests an emergency Directive number.
Search the Control and Research Annex archive.

[window closes]
```

#### Block 14

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=14]`
- Window: 54 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
The terminal requires all four authority points.
Search the Materials Storage archive.

[window closes]
```

#### Block 15

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=15]`
- Window: 48 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
DIRECTIVE 0320
LAUNCH AUTHORIZATION ACTIVE

[window closes]
```

#### Block 16

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=16]`
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

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=17]`
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

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=18]`
- Window: 50 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
DIRECTIVE 0320 ACCEPTED
FOUR-POINT AUTHORITY VERIFIED
Launch control released.

[window closes]
```

#### Block 19

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=19]`
- Window: 48 x 3; manual wrap: no
- Status: compiled; no emitted F5/D2 reference

```text
AUTHORIZATION REJECTED
The Directive or one of the four points is invalid.

[window closes]
```

#### Block 20

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=20]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
LAUNCH COMPLETE
Capsule clear.
Atmospheric dispersal active.

----- next page -----

No further payload available.

----- next page -----

ELLY:

"The nanomachines... They
should be spreading by now."

[window closes]
```

#### Block 21

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=21]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

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

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=22]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
LAUNCH DIRECTOR
"Directive 0320 confirmed.
Target data is loaded.
The Prime Minister has
authorized release."

[window closes]
```

#### Block 23

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=23]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
SYSTEMS OFFICER
"The warning net contradicts
itself. We have no confirmed
enemy launch. If we fire
now... we begin it."

[window closes]
```

#### Block 24

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=24]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
LAUNCH DIRECTOR
"And they will answer.
Every major city will be
lost... ours included."

[window closes]
```

#### Block 25

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=25]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
MIANG
"Do not blame yourself.
You did everything possible
to preserve the peace."

[window closes]
```

#### Block 26

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=26]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
SYSTEMS OFFICER
"Fallout projections exceed
every shelter limit. Once we
open the banks, there is
no recall."

[window closes]
```

#### Block 27

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=27]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
MIANG
"That is why the Prime
Minister entrusted this to
you. He knows you will
protect them."

[window closes]
```

#### Block 28

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=28]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
LAUNCH DIRECTOR
"Protect them...?
There may be no one left
to protect."

[window closes]
```

#### Block 29

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=29]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
MIANG
"If you hesitate, the enemy
will choose for you.
Is that what you want?"

[window closes]
```

#### Block 30

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=30]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
SYSTEMS OFFICER
"All four authority points
accepted. Cradles are open.
Director... we need your
final order."

[window closes]
```

#### Block 31

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=31]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
LAUNCH DIRECTOR
"...Open the banks.
Execute Directive 0320."

[window closes]
```

#### Block 32

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=32]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

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

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=33]`
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

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=34]`
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

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=35]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
CITAN:

"Elly! You have the capsule
connected, then?"

----- next page -----

ELLY:

"Yes. But I can't get the
guidance to hold steady."

----- next page -----

CITAN:

"Let me see... I can adjust
it from here. Will you take
the launch controls?"

----- next page -----

ELLY:

"I'm ready."

----- next page -----

LAUNCH SEQUENCE ARMED
Magnetic banks synchronized.
Capsule ascent ready.
Accelerator charging.

----- next page -----

CITAN:

"There... The course is
holding. Elly, now!"

----- next page -----

ELLY:

"Please... let it reach
everyone."

----- next page -----

EMERALDA:

"Go!"

[window closes]
```

#### Block 36

- Source locator: `modules/mass_driver/content/field_369_archive_control.authored.json -> blocks[id=36]`
- Window: 58 x 5; manual wrap: yes
- Status: compiled; statically reachable in V171

```text
MIANG
"You did what was
necessary."

[window closes]
```

## Appendix: authored files not selected by V171

These **16** files (39 blocks / 117 pages) remain in the content directory as older, alternate, or otherwise non-selected authored sources. Their text is not part of the active V171 route and is therefore not duplicated in the main transcript.

| Authored source | Blocks | Pages | SHA-256 |
|---|---:|---:|---|
| [field_263_goliath_defense_bay.authored.json](../modules/mass_driver/content/field_263_goliath_defense_bay.authored.json) | 3 | 10 | `07238f1392ec1e8c9f50ad161b504c1f148676ca50c8d192dbcd157d86d46e89` |
| [field_365_archive_annex.authored.json](../modules/mass_driver/content/field_365_archive_annex.authored.json) | 2 | 8 | `0ac3b98608d9631938d00c99b7a4c6b6c61c60ac3c95f6e08137ca1b85d3204c` |
| [field_367_archive_annex.authored.json](../modules/mass_driver/content/field_367_archive_annex.authored.json) | 1 | 6 | `9c0c49cb42a325dd1cf0ffbd6f88b28da450bde8348b84ab508464b9bff12106` |
| [field_367_decontamination.authored.json](../modules/mass_driver/content/field_367_decontamination.authored.json) | 1 | 1 | `83739b926db9d4bea24b2930db4c0a50286eb5e2b30138d094d6e2c3d9c48068` |
| [field_370_freight_stairwell.authored.json](../modules/mass_driver/content/field_370_freight_stairwell.authored.json) | 1 | 1 | `2aca8c65601f21ba5b3e026445035620369fc01e39f147167f7f8165859b500a` |
| [field_382_freight_lift.authored.json](../modules/mass_driver/content/field_382_freight_lift.authored.json) | 2 | 6 | `6c93629bec4a90c3e6002bcdb597c94aec694d2ef996a1955874c3e288b9d2cb` |
| [field_385_missile_gallery_a.authored.json](../modules/mass_driver/content/field_385_missile_gallery_a.authored.json) | 1 | 7 | `55c59bba30496b35b2e590ffb9b1971c449388c68a7362be43c2f34e87ebeb53` |
| [field_385_missile_gallery_b.authored.json](../modules/mass_driver/content/field_385_missile_gallery_b.authored.json) | 1 | 7 | `692616f53398610acadf68f24fa33ac794487fb9f996bc8df595e552e7cdcaf5` |
| [field_385_missile_gallery_c.authored.json](../modules/mass_driver/content/field_385_missile_gallery_c.authored.json) | 1 | 9 | `c7ec31352147234140076479f9597b4c12734064db8a8c03e0f6ba898ec0601e` |
| [field_386_deep_access_lift.authored.json](../modules/mass_driver/content/field_386_deep_access_lift.authored.json) | 1 | 3 | `b07b3f60f79c73c394fc313311952349df7b9c3fc73d67f9f2f62b3016bd95fc` |
| [field_388_final_red_tunnel.authored.json](../modules/mass_driver/content/field_388_final_red_tunnel.authored.json) | 5 | 5 | `70df593278af5d0b804330802cababbafad7ce9f570e27eec7142d116afbf008` |
| [field_398_opening.authored.json](../modules/mass_driver/content/field_398_opening.authored.json) | 5 | 7 | `122b1b330836d887cd46ebb410b848b906984cbf16f79b68d9059dba3f014e60` |
| [field_399_powered_corridor.authored.json](../modules/mass_driver/content/field_399_powered_corridor.authored.json) | 5 | 8 | `ac9578b3a55d5a6e09ff8eb8ac64bb8ee4469b7085488a260e5d47cbbce17ec2` |
| [field_403_defense_bay.authored.json](../modules/mass_driver/content/field_403_defense_bay.authored.json) | 3 | 10 | `7493e7b8a9d985cbfb26361040c3fd8ed4becc4585eabbdfd8e76d4db75301af` |
| [field_403_maintenance_undercroft.authored.json](../modules/mass_driver/content/field_403_maintenance_undercroft.authored.json) | 1 | 3 | `98cec0fd4a35e564b24be71a59eb53a9ab0a6684da3ee851850810267f8d8fd6` |
| [field_507_krelian_lab.authored.json](../modules/mass_driver/content/field_507_krelian_lab.authored.json) | 6 | 26 | `ccd2ebe5ff385c6f56f9a1c9e2a16aa8dcc13e6e3b133187559d154f8262313a` |

## Appendix: legacy replacement-schema sources

These **8** files contain 164 replacement records / 223 pages. They belong to superseded Mass Driver routes or the original graybox recipe and are not consumed by the active V171 builder.

| Replacement source | Records | Pages | Bound retail source | File SHA-256 |
|---|---:|---:|---|---|
| [modules/mass_driver/content/field_629_archive.replacements.json](../modules/mass_driver/content/field_629_archive.replacements.json) | 21 | 21 | 815 bytes / `d40d0c513da019993b42abca25cd90aec5e429c32f4ed5ecfe9c0e6d60b25bce` | `8e8667e45fefa666dd20c8017475ccfa82215b8d02ee84e0cc2e6019ea371038` |
| [modules/mass_driver/content/field_630_code_entry.replacements.json](../modules/mass_driver/content/field_630_code_entry.replacements.json) | 39 | 39 | 1301 bytes / `a5191aaab54d0010a18cae05b9b24e893db5ca7ea93c1e197f1fadef361fc116` | `8871beaf19e60ed4c003454305ad2568f9870f18ad067d13cc1bc8d2b97f7b79` |
| [modules/mass_driver/content/field_631_launch_control.replacements.json](../modules/mass_driver/content/field_631_launch_control.replacements.json) | 6 | 8 | 465 bytes / `4a4590d9b12b127521ef5338d78e82b5c16b24b9e27d45be99fcfe43515d9f85` | `611876bcf02168f1e2f43e5db865811ea7c4256e4ef886b70edc17d575de7722` |
| [modules/mass_driver/content/field_632_missile_gallery.replacements.json](../modules/mass_driver/content/field_632_missile_gallery.replacements.json) | 30 | 65 | 3004 bytes / `89c2555eaa77c475aab399eb7974c36483cb60b88a36123709ba3444058cd8bd` | `c19d31ff0f0d2297fdd7be96a2b3d824bfbff7a3022bca88cc2dcb8990d8eee5` |
| [modules/mass_driver/content/field_633_cargo_service.replacements.json](../modules/mass_driver/content/field_633_cargo_service.replacements.json) | 3 | 3 | 142 bytes / `48496993bf04fe5b5694cbfc836f4f7de82ca45298b69632fd6e27e65acce9b8` | `b391aedcd01dc4568c28ba74bd90f4a9d9eff6a95bec0e63f0face8946cf632e` |
| [modules/mass_driver/content/field_635_authorization.replacements.json](../modules/mass_driver/content/field_635_authorization.replacements.json) | 49 | 49 | 2363 bytes / `1a1f3744654cca652220ef200d9f4e13f461cadea5a6cb051e55a82f17a781a4` | `099848b1b91969170a219239904098f4d5cc28bf80b3f2d391e28a9890a4f3e5` |
| [modules/mass_driver/content/field_638_boss_warning.replacements.json](../modules/mass_driver/content/field_638_boss_warning.replacements.json) | 10 | 28 | 639 bytes / `93de8261413501720be34f089bf47253e9bb04253e431b289888f311aab4c37e` | `da7a31a6a08b7ace25a32cb5ff8e9d49474087d63be3c76baabf2751087dc538` |
| [recipes/mass_driver_control_dialogue.json](../recipes/mass_driver_control_dialogue.json) | 6 | 10 | 465 bytes / `4a4590d9b12b127521ef5338d78e82b5c16b24b9e27d45be99fcfe43515d9f85` | `f79ce6681abc06d55da7f8f6bfe3d648fb2af42128833e4b31e5d39eb08412cd` |

## Reproduction

From the workspace root:

```powershell
python tools/export_mass_driver_dialogue.py
```

The exporter rejects missing sources, duplicate block IDs, a release version mismatch, a builder/manifest field mismatch, authored source that does not recompile byte-for-byte, or compiled dialogue bytes that do not match the selected stage manifest.
