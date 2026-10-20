# Mass Driver Dungeon 2.4 - v25 Normal Combat

Version 25 preserves the accepted standalone dungeon and El-Regulus work
while removing the one-hit combat setting inherited from the source image.
No player stat cheat was present: the standalone GameState already contained
normal late-game Elly and El-Regulus values. The altered enemy resources were
the cause.

## Root cause

The Perfect Works 0.10.2 source disc was built with its **Story mode** option.
Perfect Works describes that option as disabling random encounters and
making every enemy killable in one hit. Its build log also records that the
Story-mode directory was used.

All 76 even-numbered enemy resources from canonical Disc 2 IDs 2618 through
2768 matched `gamefiles/storyfiles_script_cd2`. The Mass Driver Tusk-Tusk
record in canonical 2760 illustrates the change:

| Resource | SHA-256 | Current/max HP |
|---|---|---:|
| Story-mode 2760 | `bd49d0c67918224e3b6883d4b82001e5068bb33c87bdad5db6cee9031ac9eabf` | 0 / 0 |
| Normal 2760 | `cbfe597d0b5d136380c9fbfb7c3623609fea5db9b001d9b28cb3b13a2ebd513a` | 6,200 / 6,200 |

Canonical 2614 also differed. That resource contains shared enemy battle
statistics, including attack power; Story mode zeroed those values. Canonical
47 is the Battle Arena resource and was restored as well so the standalone
disc contains no remaining Story-mode combat variant.

## Normal resource set

`tools/prepare_mass_driver_normal_combat.py` prepares 78 checked resources:

- canonical 47 from `script2`;
- canonical 2614 from `script2`;
- all 76 even canonical IDs from 2618 through 2768, selecting `script2` when
  its translated resource exists and otherwise selecting `og_monsters`.

The helper deliberately excludes `monsters_script`, which is the separate
optional rebalanced-enemies feature rather than normal Perfect Works combat.

| Contract | Value |
|---|---|
| Resource count | 78 |
| Total size | 441,537 bytes |
| Normal aggregate SHA-256 | `831d6a8c4514e9c0ae9acd45fd7a920563e397922d722c1e474e986b25b6fbe5` |
| Enemy-only count | 76 |
| Enemy-only aggregate SHA-256 | `781a39824b10c4724c8b27e009b7ed9db5259e985b9f3a2fe8ef2d5afa3a068f` |
| Rejected Story aggregate | `2496389c6b107aa2e69d7e7af5462ec5750835ffe058d106d5ae3ad7f8640ba6` |
| Normal canonical 47 SHA-256 | `ca7a9e4ae3daf598192c80431079ded82cf0aefe4977ec4025cf70ce2f06076f` |
| Normal canonical 2614 SHA-256 | `9e78aaaff33d4c92f3228553cf772c10b0d70c53d083f9ee34c661b76dee6014` |

The dungeon builder checks the count, total size, aggregates, support hashes,
and representative HP fields before it materializes any replacement.

## Mass Driver test encounter

A normal Tusk-Tusk has only 6,200 HP, so El-Regulus could still legitimately
defeat it with one attack after Story mode was removed. Version 25 therefore
uses the native Dragon already present in the same enemy resource and
world-map battle set. Its normal current/max HP is 18,000.

The active Mass Driver formation is table 12, scenario row 2, slot 0 at
canonical 4052 decoded offset `0x30F58`. Only its first Gear enemy selector at
`0x30F60` changes:

```text
v24: 80  (Gear flag + enemy 0, Tusk-Tusk)
v25: 81  (Gear flag + enemy 1, Dragon)
```

The arena byte remains `0x2C`, so the Mass Driver battle backdrop is
preserved. The duplicate formation in table 14 and every other world-map
formation remain untouched.

```text
canonical 4052 packed SHA-256:
68d0b5f60acc5c5a7b7a55a1fba85438115dbe025b75434d25e17f7bbcefbf2d

canonical 4052 decoded SHA-256:
6fe98b51e5c49e23d8ca0b221e7ac9a42b1a29c176374e98d5487cd2140ecad4
```

## Build

```powershell
python tools/prepare_mass_driver_normal_combat.py `
  --perfect-works-gamefiles C:/path/to/Perfect_Works_Build/gamefiles `
  --output work/normal_combat_resources `
  --force

python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v25_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v25.bin
```

The playable cue is:

```text
output/Xenogears_PW_CD2_mass_driver_standalone_v25.cue
```

The rebuilt BIN is 690,375,504 bytes with SHA-256:

```text
ef78454cb026d69b5d08eb2ae1f0a68d9da0380c2620d8fac8bdff2fcc999cf5
```

It passed 124 automated tests, 139 subtests, and an exact post-build
comparison of all 119 injected resources. Disc extraction independently
confirmed the normal hashes for canonical 47, 2614, and 2760, plus the
one-byte Dragon selector in canonical 4052.

## Runtime acceptance

A cold DuckStation test mounted Elly in El-Regulus, naturally entered the
Mass Driver Dragon encounter, and displayed El-Regulus's normal 17,000 HP
and 6,600 fuel. The Dragon survived instead of disappearing in one hit and
executed a normal turn. Manual acceptance independently confirmed that the
former one-hit-kill behavior is gone and combat now behaves normally.

For repeat testing:

1. Start `output/PLAY_MASS_DRIVER_STANDALONE.cmd`.
2. Open the world-map Gear menu and tell Elly to enter El-Regulus.
3. Move near the Mass Driver until the Dragon encounter starts.
4. Use the weakest one-point attack and confirm the Dragon survives.
5. Confirm the Dragon can act, then win or Escape.
6. Confirm the game returns to the same exterior position with Elly mounted
   and the Mass Driver entrance still responds to X/Cross.
