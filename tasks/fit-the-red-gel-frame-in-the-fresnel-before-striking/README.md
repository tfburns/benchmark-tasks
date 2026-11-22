# Fit the red gel frame in a 3 in fresnel before the lamp is struck

Put the red gel in the light.

```bash
TASK_DEMO=demo   # 1.0: pick up the red frame, slide it to the stop and let go
TASK_DEMO=short  # 0.5: enter the holders but stop short of the stop
TASK_DEMO=idle   # 0.0: do nothing
TASK_DEMO=naive  # 0.0: pick it up and set it down away from the lamp
```

## Setup
An Altman Lighting CAT #100 3 in Inky sits on the bench on its back, lens pointing up, as when a lamp is gelled before it is hung. It is unpowered. Its colour-frame holders open along +y, with a stop at -y. A 3.75 × 3.75 in (Altman 100-CFB size) aluminium colour frame already holds a pre-cut red gel and starts flat on the bench, further +y, clear of both holders. A short post and pinch bar on the trailing edge are for a straight-down grip. A second, blue, frame lies in a shallow gel box beside the lamp and is not in the holders. All props are rigid and start on fixed marks.

## Scoring
As seen in the overhead video, the red frame is in both colour-frame holders. At the end, after 1 s at rest and with the gripper clear of the frame: 1.0 once the frame is on the stop and has been let go; 0.5 if the frame has entered the holders but is still short of the stop, or if it is on the stop but has not been let go or is not yet still; 0.25 if it is only near the mouth; 0 for the start pose on the bench and for any path that never enters the holders. Possible scores: 0, 0.25, 0.5, 1.0.

## Design notes
- **Why it matters.** A colour frame holding gel gets hot once an incandescent fixture has been on. Gels have to sit in the fixture's colour runners, not on the lens (CINE-340; University of Rochester lighting-lab notes). Pre-hang practice is to fit the framed gel while the lamp is still on the bench, before it is struck, so the accessory is in place before the fixture can become a fire risk.
- **Where the cue is.** The 95 mm red gel starts as a horizontal square in the table middle, with the black body, yoke, C-clamp and blue distractor around it.
- **Distinct from.** Upstream #1330 stacks gels on a lightbox to match a colour; that is colour matching, not seating a frame in a fixture's runners.
- **Honest limits / REACH trade-off.** The real Altman 100 is about 7.5 in (190 mm) along its axis. Sitting that barrel on its back would put the lens out of a straight-down grip, so the lamp body is 70 mm high. That is a REACH trade-off, flagged, not a hidden shrink. The holders are opened to about 20 mm because PhysX contactOffset is 4 mm; a real 3–5 mm runner is not used. The pull tab is a short post and a 16 mm bar, chunkier than a real 100-CFB tab, so a straight-down grip can close around it without hitting the sheet. The red frame is free, not a slider. No lamp is struck; the trial is cold.

## Reset
Put the red frame back on its start mark on the bench, flat and clear of both holders. The blue frame stays in the gel box. The lamp is unpowered.

## Real trials
A used 3 in fresnel, two colour frames and pre-cut gel, well under the about $100 bench-trial cost. The trial is cold and unpowered.

## Fidelity
See task.json.

## Scores
- Scripted demo (yam_arena, 320 × 176, seed 0, Brev L40S, v11): 1.0, success at step 340 of 500 (seated at 74.0 mm, tilt 0°, 1 s rest, gripper clear).
- TASK_DEMO=short: 0.5.
- TASK_DEMO=idle: 0.0.
- TASK_DEMO=naive: 0.0 (picked up and set down away from the lamp).
- Dream-1 (dreamlabs/dream-1-beta-flash, seed 1, 320 × 176, 22 Nov 2026 on a Brev L40S): 0.0 in 500 steps, not refused (20 requests, 27 attempts, term=max_steps). The frame never left the start mark.
