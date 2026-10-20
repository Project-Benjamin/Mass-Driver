# Mass Driver Dungeon 2.25 - v46 Field-Entry Branch Repair

Version 46 fixes the black-and-white striped corruption after the save point
and Magnetic Conduit at its actual script-control-flow source. It retains
v45's accepted arrival orientation, v44's dedicated post-auxiliary
staircase, and every other dungeon route.

## Reproduced route

The failing transition is:

```text
target 725, entity 12
        |
        v
target 726, parameter 0
```

The destination finished loading and left controls enabled. The giant white
and black bands were not a door model, a failed transition, or a camera view
through the wall. Runtime state showed that the field had unexpectedly
selected a 640-pixel framebuffer.

## Root cause

Target 726 adds eight seven-byte field-entry records. Those records occupy
the retail entity-0/entity-1/entity-2 initializer prefix, so the builder
copies the affected routines to appended space and repoints their script
slots.

The relocator already rewrote ordinary `JUMP` and `JUMP_IF` targets, but it
missed the entity-0 initializer's `IF_GAMEPROGRESS_EQUAL` (`0x86`) target:

```text
retail entity-0 initializer: PC 0x000F
retail conditional:          PC 0x0020
retail target:               PC 0x002B

relocated initializer:       PC 0x032D
relocated conditional:       PC 0x033E
stale v35-v45 bytes:          86 A6 80 2B 00
correct v46 bytes:            86 A6 80 49 03
correct relocated target:    PC 0x0349
target bytes:                 75 1A 80
```

Standalone progress does not equal `0x00A6`, so the stale target was taken.
PC `0x002B` had been overwritten by parameter 6:

```text
A7 FE DF FD 00 06 06
```

`A7` is one byte. Execution therefore continued at accidental extended
opcode `FE DF`; its `FD 00` operand resolved to mode 0. That engine operation
cleared VRAM and switched both draw and display environments to width 640.
The field's Zeboim textures occupy pages beginning at x=320, so the
framebuffer rasterized directly over them every frame and produced the
striped image that looked like a crash.

The timeline explains why the fault appeared later than the original
relocation:

```text
v34: target 0x002B still contains the retail alternate music path; safe.
v35: stale branch exists, but parameter data starts F8 FE DF FD and F8
     consumes the following bytes as operands; the renderer is not changed.
v36+: parameter 6 starts A7 FE DF FD, exposing FE DF as an opcode.
```

## Repair and regression coverage

The field-entry installer now relocates an audited `0x86` local target at
operand offset `+3`, just as it relocates the audited `0x01` and `0x02`
targets. For target 726:

```text
entity-0 copied body: 0x032D..0x034C
0x86 destination:     0x0349
ordinary jump:        0x0346 -> 0x034C
entity-1 copied body: 0x034F..0x0358
entity-2 copied body: 0x035A..0x0363
overwritten records:  0x000F..0x0046
```

All 32 script-pointer slots for every entity are checked. No pointer or
audited branch target enters the overwritten record interval. Focused tests
also preserve the exact relocated bytes and reject the former `0x002B`
destination.

## Runtime forensic proof

A diagnostic state with the same target-726 room was repaired in memory by:

1. restoring both draw and display widths to 320;
2. restoring the serialized GPU mode and draw area; and
3. replaying all five canonical field-graphics uploads.

It then ran without movement for more than 75 seconds. The ending state
remained at 320 pixels, its draw area was `(0,256)-(319,479)`, and every
graphics rectangle still matched its canonical payload byte-for-byte:

```text
(0,480)   256x4
(320,0)   128x256
(448,0)    96x192
(832,0)    64x144
(544,64)   32x128
```

This isolates the renderer mode as the mechanism and confirms that removing
the accidental `FE DF` path preserves the room's texture pages.

## Packed change from v45

Only one of the 140 staged canonical replacements differs:

```text
canonical 2058, target 726 bundle
size: 23,240 bytes

v45 SHA-256:
97e2f48f6c38b30fced09e82fefafe963ba9bd5a3227f7d2ee223e24a92b484e

v46 SHA-256:
7457ac568f1173eb0b927e1661cda416bc13e026f6c7c57712c045bd30b16f45
```

## Release validation

```text
image:
output/Xenogears_PW_CD2_mass_driver_standalone_v46.bin

BIN size: 693,263,760 bytes
raw sectors: 294,755
BIN SHA-256:
7385bfb08ca4e87f4fb5fb3b90c045351994d58455e2412afbd9843fe9777b33

CUE SHA-256:
5d8d71da5c2c29dca48f1d0b179d4db04f83be1bb33635ad74f857d56c60bbc3

packed staged replacement comparison:
140/140 exact, totaling 8,152,642 bytes

standalone boot LBA: 172938
boot sector SHA-256:
79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc
MODE2/Form1 boot EDC/ECC: valid

automated tests: 149 passed, 1,891 subtests passed
```

These checks establish the control-flow fix, packing, and image integrity.
A fresh cold-boot traversal remains the final runtime acceptance test.

## Focused manual acceptance

1. Close DuckStation completely.
2. Run `output/PLAY_MASS_DRIVER_STANDALONE.cmd` and confirm its title says
   v46.
3. Choose New Game. Do not load an F1/F2 state made with an older build; it
   restores that build's mounted disc and already-loaded field/GPU state.
4. Reach the golden save point and Magnetic Conduit.
5. Use the west door into the next Zeboim hall.
6. Confirm the native door animation and sound complete, the destination
   renders normally, Elly faces into the hall, and movement remains enabled.
7. Turn around and use the door behind Elly. Confirm it returns normally.
8. Confirm the separate post-auxiliary north door still crosses its complete
   stairwell and reaches the save-point hall.
9. If the west-door test fails, press F2 immediately before X, press X once,
   then press F2 again while the fault is visible. Preserve the screenshot
   and both generations of the state.
