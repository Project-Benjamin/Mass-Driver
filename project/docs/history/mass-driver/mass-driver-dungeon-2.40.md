# Mass Driver v63: Natural-dialogue closure

Version 63 keeps the complete v62 dungeon, mechanics, Guardian battle,
five-magazine route, and authentic retail Mass Driver handoff. Its change is
the active script: employee correspondence, party reactions, the Defense
Archive briefing, magazine scenes, and Central Control were rewritten as one
coherent dramatic arc.

This remains an original, canon-conscious fan reconstruction. It is not
recovered Square dialogue or evidence of a deleted official dungeon.

## Writing approach

The v62 script contained the correct broad facts, but too many speakers ended
their scenes with the same polished lesson about choice, fear, machines, and
the future. Version 63 separates their voices:

- Lena is a guidance engineer and Mira's mother. Her mail is personal and
  concrete.
- Aron is a systems engineer. He answers technical questions, rationalizes
  readiness, and later admits that he was wrong.
- Mara remains in Payload Safety throughout. She objects procedurally, keeps
  copies, and refuses military euphemisms.
- Government correspondence is passive, bloodless, and framed around
  continuity.
- Elly reacts to individual people and uncertain memories instead of
  explaining the theme after every terminal.
- Emeralda uses short, direct speech without being reduced to constant
  baby-talk.
- Citan qualifies uncertain conclusions and concentrates on mechanisms.
- Miang reassures the Launch Director, narrows his apparent alternatives, and
  makes the desired decision feel like his own.

The complete destruction-to-healing statement is reserved for Elly at the
launch console, where it can serve as the dungeon's emotional conclusion.

## Connected archive story

The records now form this dated sequence:

1. In 6072, Survey Carrier Three takes atmospheric instruments and an
   unmanned probe above the atmosphere. Mira asks what it will find.
2. In 6074, Mira watches a successful launch while holding Aron's paper star.
   An overseas tracking station confirms the signal.
3. In 6078, the Prime Minister's adviser brings Strategic Command to the
   launch floor. Aron answers a carrier-fit question before a colonel calls
   the proposed casing a warhead.
4. In 6079, Mara refuses Proposal MC-4. The Adviser’s office records the
   objection, assigns alternate approval, and removes Mara from the decision.
5. In 6081, Lawine destroys the central power station and half the capital
   goes dark. Aron closes the accelerator breakers while trying to believe
   readiness will prevent an attack.
6. Staff notice the same deterrence language appearing in several countries.
   Their discussion ends with Aron admitting that Mira is in Shelter Four and
   that he does not know what to do.
7. A Federal Medical Bureau bulletin records the failed emergency generator
   and the death of a child during Dr. Kim's operation. It also records the
   approximately thirty-year life span and rising infertility.
8. Kim's chronology is corrected: his molecular-machinery paper is condemned
   in 6077, Miang sponsors his private facility in 6081, and government
   Special Forces enter the research facility in 6083.
9. Directive 0320 converts lost contact into permission to complete a pending
   release. The four-point safeguard is administratively consolidated.
10. Aron's final mail reports contradictory warning stations, an active local
    countdown, and a failed local abort. The automated record then confirms
    strategic release and counterstrikes.

Lena's final unsent note asks Mira whether she remembers wondering what the
first probe would find. The archive closes on Elly admitting that she does not
know what happened to her.

## Defense Archive and magazines

The entrance now establishes that Citan is bringing the party's Gears through
a separate service shaft. His later appearance in the lower Gear bay no longer
arrives without setup.

Citan's briefing is state-neutral: he does not claim Elly recovered records
that may have been skipped. The terminal still requires:

```text
0320
A-2
B-5
C-8
D-4
```

Each value remains a separate prompt, and a partial code cannot authorize the
launch.

After the code is accepted, Citan explains that Directive 0320 was never
rescinded and that the custodian still treats the four-thousand-year-old war
as active. The post-battle scene does not call the magazines a graveyard
before Elly sees them.

The five automatic magazine scenes are shorter. Developer-facing
`FAR PASSAGE: AUTOMATIC` labels were removed. Magazine 4 now records repeated
outbound calls until grid failure without treating a failed network as proof
that every person died. Magazine 5 ends on Elly's tombstone and graveyard
image; it no longer previews the ending with another neutral-machine speech.

## Central Control

The historical figures remain translucent, non-solid apparitions. During the
vision, the Miang actor is labeled only:

```text
PRIME MINISTER'S ADVISER
```

The Systems Officer says the warning network is contradictory and has not
confirmed an enemy launch. The Director understands that retaliation will
destroy every major city. The Adviser tells him not to blame himself, assures
him that he has preserved peace, and frames hesitation as allowing the enemy
to choose for him. He executes Directive 0320. She answers:

```text
You did what was necessary.
```

Only after the vision does Elly identify the woman as Miang. Citan distinguishes
the uncertain dream-or-memory from the documented archives and observes that
Miang supplied the reasons the leaders wished to hear.

Elly's final answer is:

```text
Once, it was used to
destroy life. Now... we will
use it to heal.
```

She adds that the Limiter was forced upon humanity and that they can give back
what was taken. Taura's capsule then launches through the authentic retail
mode-17 sequence.

## Validation

All active dialogue passes the retail-codec, width, height, and explicit-page
compiler checks. The full automated suite passes **182 tests and 2,070
subtests**.

The v63 stage contains 154 replacements totaling 9,832,127 bytes. Their
canonical-ID-order aggregate SHA-256 is:

```text
082d0e53392d9463d68affe4a09763b4058af2611f10cde9f4a781d50cd094f0
```

All 154 payloads re-extract byte-identically from the final image. The audit
also confirms:

- 4,868 unique replacement sectors;
- 4,886 unique replacement/FAT/header/boot sectors;
- valid byte-exact MODE2/Form1 EDC/ECC for all 111,142 changed or added raw
  sectors;
- all 3,568 untouched archive files outside the system executable remain
  byte-identical.

## Frozen v63 artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v63.bin` | 694,881,936 | `a0c3b01305ddde2fe9365704ce2a89cd2d864a8c286eb1c474c265d1d01e385b` |
| `output/Xenogears_PW_CD2_mass_driver_standalone_v63.cue` | 106 | `45e553438fd8e3bba375d12d338f66e21bbb3d3c0d50f7d0b9dbeaf49a6ed6ea` |
| `work/mass_driver_v63_stage/manifest.json` | 170,126 | `eb1f1c13e2c69bbe97c1c10cadd57f60b37635ee347fa41e0c7b424eaf8c0b4e` |
| `output/MASS_DRIVER_V63_CONTINUE.sav` | 1,745,789 | `f9bcee4a5a308044ccb2e7d3040d13be08b2f7f423b1ec9993eb56952441776d` |

The migrated state's resident archive table SHA-256 is:

```text
7295eeb411f22956fec5c625275135da2154ec37d18118065394161bf3236d8f
```

DuckStation smoke tests kept both the v63 cold boot and v63 continuation alive
and executing for 20 seconds. Neither path reproduced the earlier immediate
close.

Use `output/PLAY_MASS_DRIVER_STANDALONE.cmd` for the full revised script. Use
`output/CONTINUE_MASS_DRIVER_V63.cmd` to begin after the Guardian and review
the five magazines and Central Control quickly.
