# Mass Driver Dungeon 2.5 - v26 El-Regulus Standard Attacks

Version 26 preserves the accepted dungeon, world-map El-Regulus, and v25
normal-combat correction while improving El-Regulus's Triangle, Square, and X
attacks. The change is isolated to player Gear 10 in canonical resources 2594
and 2960.

## Damage balance

Canonical 2594 is the player battle/Gear attack-stat archive. It must not be
confused with canonical 2614, which is the shared enemy-stat resource restored
by v25.

Gear 10 is archive entry 26. Its decoded table is 1,640 bytes, arranged as 41
records of `0x28` bytes. The first three records are the standard attacks:

| Button | Animation | Old power | v26 power | Fuel |
|---|---:|---:|---:|---:|
| Triangle | 32 | 5 | 6 | 10 |
| Square | 33 | 10 | 12 | 20 |
| X | 34 | 20 | 24 | 30 |

The `6/12/24` values are a uniform 20-percent increase. They preserve the
retail 1:2:4 power-to-fuel progression and avoid recreating the removed
one-hit-kill behavior. Accuracy, elements, status data, attack names, fuel
costs, and every other character and Gear record remain unchanged.

The patched decoded payload is recompressed with the retail complete-command-
group LZSS rule. One backreference is split into two equivalent adjacent
references, allowing the stream to end on an eight-command boundary while
still declaring exactly 1,640 decoded bytes. It occupies 440 bytes and is
zero-padded to the original 448-byte archive slot, so no outer pointer moves.

```text
canonical 2594 source SHA-256:
b59e5cf492f6e70be1b38390021bb229eca00146f19870dac5e6e4215ed7e054

canonical 2594 patched SHA-256:
cb902074fe68f7876f5e8791e87daa64fa9cc42c9b660be4a675a9047f5e7a43
```

## Battle animation construction

Retail El-Regulus programs 32, 33, and 34 were only 44 bytes each. They
selected native clips `0x40`, `0x41`, and `0x42`, emitted one `0x003F` damage
event, and returned, but lacked the camera envelope used by normal playable
Gears.

Version 26 keeps those El-Regulus-specific clips and wraps each in a distinct
model-independent camera sequence audited from the adjacent retail player-Gear
archive. It does not transplant donor movement, model frames, effects, or bone
operations. The camera-less `0x002F` return becomes the native `0x003A` camera
synchronization return.

| Program | Role | Size | SHA-256 |
|---|---|---:|---|
| 32 | Triangle, compact framing | 112 | `05360b3562680d6bf1fcf14ea5b2019b4372c590c992fbce3276733d705a2632` |
| 33 | Square, broader framing | 120 | `becc7c03322e0426147c48a9c306aab0d534d2c1226cd5a762129c6d61e5bec5` |
| 34 | X, strongest framing | 112 | `6eff1d284793dbae0dfa22a8c5f7704b05f1e46c488adf6749c28e8b41f03afc` |

The three programs expand from 132 to 344 bytes. The builder directly
relocates the nested animation pointers because the retail table intentionally
contains null and alias entries that a naive archive rebuild would destroy.
The final nested sentinel moves to `0x79B8`; the outer model-data pointer and
EOF sentinel move to `0x79C8` and `0x7D14`. All later animation bytes and the
secondary model-data segment remain identical after relocation.

The existing animation-0 player-entry completion fix remains applied.

```text
canonical 2960 source SHA-256:
8ccee45222b6245fdcb4556ce15f69746bf5e2ebd88ec76aa77ec4381ab07d6d

canonical 2960 patched SHA-256:
532603a56c9b26eacd6c1182404d84330749fb221cfd08903e7c42d2857e58ec
```

## Build and binary validation

```powershell
python tools/xgdisc.py extract $sourceDisc work/_audit_el_regulus_damage `
  --canonical-disc2 2594 --force

python tools/build_mass_driver_dungeon.py `
  --input-root work `
  --dialogue-root content/mass_driver_v2 `
  --output work/mass_driver_v26_stage `
  --force `
  --build-disc `
  --xenoiso C:/path/to/xenoiso.exe `
  --source-disc C:/path/to/Xenogears_PW_CD2.bin `
  --disc-output output/Xenogears_PW_CD2_mass_driver_standalone_v26.bin
```

The v26 build passed 127 automated tests and 207 subtests. All 120 injected
resources were then independently re-extracted from the final disc and
matched the staged replacements byte-for-byte. The Xenoiso wrapper now
removes a stale output BIN when `--force` is explicit; this prevents legacy
Xenoiso from reporting success while retaining an older same-named image.

```text
BIN size: 690,375,504 bytes
BIN SHA-256:
9d98f7f5d6751f3870b1756c68f003b33f9e4ce18fca8d17ce504f05c99b9142
```

## Runtime acceptance

From a fresh boot, mount El-Regulus outside the Mass Driver and trigger the
native Dragon encounter. Triangle, Square, and X must each:

1. use a visibly distinct camera path;
2. run the correct El-Regulus motion clip;
3. display exactly one damage result;
4. return El-Regulus to its ready stance;
5. restore the normal battle camera and command menu.

The displayed damage should increase in Triangle, Square, X order. The Dragon
must survive the weak attack, take normal turns, and retain its normal
18,000 HP combat behavior.
