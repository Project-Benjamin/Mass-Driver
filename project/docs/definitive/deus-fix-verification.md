# First Deus / Mahanon HP-halving camera correction

Date: 2026-09-07. Target confirmed by the user: the first Deus battle in
Mahanon, when its HP-halving move can hang from a side camera angle.
This is not a patch to the final Deus encounter.

`modules/definitive/deus_fix.py` implements a guarded, isolated correction.
**Binary and bounded CPU checks pass; emulator gameplay remains untested.**
The patch suppresses the problematic camera sequence for that one move. It
does not change HP-halving damage, enemy stats, AI choices, rewards, other
battle scripts, or the final fight.

## Exact provenance and composition

The [author's original fix commit](https://github.com/PWBuild-Team/Perfect_Works_Build/commit/c054f82f8e8dab8c6ad5106ed270d301d586aa54)
was downloaded directly and compared to the user's configured USA retail
resources. Only 158 bytes differ in the meaningful decoded battle overlay,
and one byte differs in enemy resource 2746. The source's compressed stream
also has different allocation padding; the builder imports no donor overlay.
It changes the three isolated instruction blocks in local retail data and
recompresses them with the shared retail compressor.

| Material | SHA-256 |
| --- | --- |
| Source-commit packed battle 38 | `78ce35736638b35c8cf39f73f5249f5ae9e6d1ef70e30ff6a0ab37a48bab0266` |
| Retail decoded battle 38 | `1830b4ef1fe37129972fc310dfad534f8161d6c0b123e74254c3711334a3e291` |
| Deus-only patched decoded battle, meaningful 343,936 bytes | `e315f4397bc784775ce942939012d3398e4bdd9395690a371c0c1e1092b1b8a6` |
| Retail enemy 2746 | `338b41b89491c4d53185e89b4efbacf974848f6561151573bd8406f5410d300a` |
| Deus-patched enemy 2746 | `86c439808a674c7a3a507fa675ee9ea8fb92631ec18ed3b0ea8513798d17ddc7` |

Complete modified instruction ranges are `[0xAD64,0xAD78)`,
`[0x3D0E0,0x3D0EC)`, and `[0x3E104,0x3E1A4)` in decoded canonical 38.
Canonical 2746 offset `0xC25` changes from `00` to `01` within the command
`01 00 01 00`. No other enemy-resource bytes change before optional XP edits.

The API is `build_deus_replacements(read_canonical, replacements)`. It
composes after the existing mechanics corrections and before XP changes.
Only the two known mechanics instruction differences are allowed in the
incoming battle overlay; normalization must recover the complete retail
hash. Unknown modifications, a second application, changes to the marked
enemy resource, or foreign retail inputs fail closed. Unrelated existing
replacements are retained without mutation. Double XP preserves the marked
script byte and all script contents.

## Why other battles keep their camera behavior

The native enemy command handler ignores byte 3 of command `01`; it writes
byte 2 into the selected context byte. This agrees with the independently
inspected [Noah implementation at its pinned revision](https://github.com/yaz0r/Noah/blob/d725fe231e56a895c17df0554042b9e2bd1acb78/NoahLib/battle/enemyScript.cpp).
The correction uses the previously ignored byte to mark this move.

Every aligned four-byte record was scanned from the verified first-script
boundary `0xBB2` to each resource's declared string boundary at header
`0x30`. This deliberately includes headers rather than risk omitting a
command. Both discs have 76 enemy resources and 12,407 matching command-01
records. **Every reserved byte is zero.** The only introduced nonzero value
is Deus's `2746:0xC25`. The builder repeats this scan on the source reader and
rejects any unexpected nonzero command flag.

For zero flags, the ordinary camera calculations, function-call arguments,
and final camera-state stores are preserved. The nonzero flag is cleared as
the guard is taken; a following unmarked invocation returns to the ordinary
path. The reset command also clears the flag. No flag is serialized to saved
game data or memory cards.

## Transient memory and instruction safety

The single flag byte is at `0x800C2048`, decoded overlay offset `0x52558`.
The four-byte alignment word is initially zero, immediately after the final
function's `JR ra` at `0x800C2040` and its NOP delay slot at `0x800C2044`.
Native globals begin at `0x800C204C`. The inspected retail overlay contains
no direct pointer to `0x800C2048` and no direct load, store, or address-building
immediate targeting low address `0x2048`; nearby globals use separate offsets.
The complete retail hash and the exact return/padding bytes are guarded.
This is an overlay-local transient byte, not a global field-state allocation.

Each new load has an independent instruction or NOP before its value is
consumed. Tests decode the actual words and reject immediate load consumers
in all modified blocks. The guard branch retains a valid delay-slot store
which clears the flag on both paths. All three interpreter-return jumps
still target `0x800ADEBC`.

The reset briefly uses `s5` across a call. That register is callee-saved;
at the shared interpreter join, `s5` is reassigned from the current script
pointer in the branch delay slot before it is used again. The comparison
tests execute through that reassignment.

## Verification performed

`python -m unittest modules.definitive.tests.test_deus_fix -v` passes nine
tests. Retail data from both discs is exercised. The tests cover exact
unselected-byte preservation, compression, source identities, script-flag
scan/rejection, composability with the existing fixes and XP, branch targets,
and R3000 load-delay spacing.

Unicorn executes actual patched MIPS blocks in bounded synthetic memory:

- Twelve zero-flag coordinate/angle combinations retain the original three
  calls, their arguments, result registers, and camera-state output.
- The marked path makes none of those camera calls, leaves the pre-existing
  camera state alone, clears the flag, and allows the next ordinary invocation.
- Eighteen command-handler inputs, each run in both variants, retain native context writes and
  iteration counts while capturing the requested flag.
- Three reset inputs clear transient state, and the interpreter restores
  its script-pointer register at the join.

The three camera callees are stubbed so the comparison isolates dispatch,
arguments, and caller-side state. Unicorn is a MIPS CPU engine, not a full
PlayStation: these checks do not exercise rendering, the GPU, an actual boss
save, HP processing, timing, or a complete battle. R3000 load-delay spacing
is checked separately because a MIPS32 engine alone cannot certify it.

Gameplay acceptance remains: start from a preserved copy of a pre-Mahanon
memory card, identify exact built media with `project.py play --check-only`,
exercise the first Deus HP-halving move at front and side angles repeatedly,
confirm all targets lose the expected HP, complete the battle, and continue
into the following scene. Record other normal Gear battles before and after
to cover camera-state reset. No gameplay pass is claimed until those cases
have actual results.
