# Seat the punched offset plate on the press register pins

Put the plate on the pins.

```bash
TASK_DEMO=demo   # 1.0: pick the plate up, line both holes over both pins, lower it flat and let go
TASK_DEMO=short  # 0.5: lower the plate onto only one pin
TASK_DEMO=idle   # 0.0: do nothing
TASK_DEMO=naive  # 0.0: arm stays aside
```

## Setup
A short proof-press bed with two colliding register pins (14 mm diameter, 36 mm tall, chrome with red tips), bearer rings and a lead-edge clamp bar sits in the middle of the table, unpowered. A punched A5-scale aluminium plate (150 x 72 mm, about 12 mm visually) with a teal printed image, dark hole rings and four red register marks starts flat on a narrow wooden plank beside the bed, off the pins, on a taped outline with a 20 mm lateral and 25 degree yaw offset, so the plate, pins and bed are all clearly visible in the table middle. A second, yellow, unpinned plate lies on a second wooden board to the side. All props are rigid and start on fixed marks. The bed is bench-scale, not a full 40 in press.

## Scoring
As seen in the overhead video, the plate stays on both register pins. At the end, after 1 s at rest and with the gripper clear of the plate: 1.0 once the plate is on both pins, flat on the bed (within 3 mm) and has been let go; 0.5 if only one pin is engaged, or if the plate is seated but has not been let go or is not yet still; 0 for the start pose (on the board, off the pins), for a plate on the bed that misses the pins, and for idle. Possible scores: 0, 0.5, 1.0.

## Design notes
- **Why it matters.** Press operators hang a punched plate on the register pins of the plate-cylinder clamps before the clamps are tightened (PrintWiki, Plate Clamp; Printing Industries of America guidance). A plate that is not on the pins will print out of register, or it can be bent or scored as the clamps close. The skill is precise peg-in-hole alignment of a flat part: both holes have to line up over both pins before the plate is lowered.
- **Where the cue is.** The teal A5 plate starts on a wooden board in the table middle, off the chrome pins with red tips; the dark press bed sits beside it; a yellow spare plate is on a second board.
- **Distinct from.** Upstream #3470 transfers wood type from a composing stick to a galley (typography, not hanging a plate on register pins). This is not a last seating push: the plate starts off the pins and has to be aligned.
- **Honest limits.** The plate is a free rigid body, but PhysX contactOffset is 4 mm, so the collider holes are a 30 mm square gap around each 14 mm pin; scoring uses a tighter 8 mm on-pin window. The visual sheet is about 3 mm and the collider is 8 mm so a straight-down pinch can hold it. The bed is an A5-scale proof-press segment, not a full press. No ink is applied and the cylinder does not turn.

## Reset
Place the punched plate flat on the taped outline on the board beside the bed, off the pins, with the 20 mm lateral and 25 degree yaw offset. The spare yellow plate stays on the second board.

## Real trials
A small proof-press bed or a pin-register base, two plates and two pins, well under the about $100 bench-trial cost. The trial is cold and unpowered.

## Fidelity
See task.json.

## Scores
- Scripted demo (yam_arena, 320 × 176, seed 0, dev-01, v2 off-pin): 1.0, success at step 357 of 700.
- TASK_DEMO=short: 0.5 (one pin engaged).
- TASK_DEMO=idle: 0.0.
- TASK_DEMO=naive: 0.0 (arm stays aside).
- Brev visibility and Dream-1 pending.
