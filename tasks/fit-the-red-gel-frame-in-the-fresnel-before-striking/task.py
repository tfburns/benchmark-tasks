"""RESCUE v11 (stream E, appeal of #3700): pick a 3.75 in red gel frame up from
the bench, align it with the colour-frame holders of an Altman 100 3 in Inky
fresnel, and slide it fully in to the stop before the lamp is struck.

The submitted v6 started the frame already in both runners, 30 mm short of the
stop, and tested only the last push. v7 started the frame on the table but placed the pull tab at x=0.52, past a
reliable straight-down reach, and used a 10 mm tab that sat too low to pinch.
v8 moved the holders to open along +y so the grasp is in REACH, but a 32 mm
upright tab next to the sheet was not pinched: the arm reached the pose and
came away empty. v9 keeps that free, off-lamp start and replaces the tab with
a short post and a 16 mm pinch bar, modelled on the header-stand handle, so
the fingers can close around it without hitting the sheet. v9 picked the frame
up but then lowered it while the sheet already overlapped the holders, so the
plate sat on the lips, tilted, and scored 0.25. v10 lowers the frame while it
is still clear of the mouth, then slides it in at runner height. The robot pinches
the bar, lifts, lines the sheet up with both holders, and slides it in to the
end stop.

Sourced from the Altman Lighting CAT #100 3" Fresnel ("Inky") and 100-CFB
colour frame. See https://www.altmanlighting.com/wp-content/uploads/2016/04/100Specs.pdf
The barrel is still shortened to a 70 mm lens height (REACH: the real 190 mm
axis would put the lens out of a straight-down grip). That trade-off is flagged.
The holders are opened to about 16 mm internal height because PhysX
contactOffset is ~4 mm; a real 3-5 mm runner is not used. That trade-off is
flagged too. The pull tab is a short post and a 16 mm bar so a straight-down grip can
close around it without hitting the sheet; a real 100-CFB tab is a flatter
pull tab. That trade-off is flagged too.

The scorer has no gap between "almost at the stop" and "seated": any frame
that has entered the holders and left the start mark, but is not yet seated,
scores 0.5 (or 0.25 if it is only near the mouth).

Env: TASK_DEMO = demo | idle | short | naive
"""
from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from yam_arena.constants import FINGER_CLOSED, FINGER_OPEN  # noqa: E402
from yam_arena.demo import Waypoint  # noqa: E402
from yam_arena.task_file import TABLE_TOP  # noqa: E402

import hhkit  # noqa: E402
import mechkit as m  # noqa: E402
SCENE = "station"
TOP = TABLE_TOP[SCENE]
SCORE_OVER = "end"
INSTRUCTION = "Put the red gel in the light."

V = hhkit.demo_variant("demo")
PAD = 0.013

# Altman 100 / 100-CFB
FRAME = 0.0952          # 3.75 in colour frame
LENS_R = 0.0381         # 3 in Pyrex fresnel
FRAME_T = 0.004
GEL_T = 0.002
LENS_Z = 0.070          # REACH trade-off: real axis length is 7.5 in / 190 mm

# World: lamp in the cue zone, lens pointing +Z. Holders open toward +y.
# Red frame starts further +y, clear of the mouth, grasp still in REACH.
CX = 0.36
CY = 0.16
START_X = CX
START_Y = 0.300
LOOKS = {
    "body": m.Look(m.rgb(0.07, 0.07, 0.07), roughness=0.85),          # black epoxy sandtex
    "lens": m.Look(m.rgb(0.72, 0.80, 0.75), roughness=0.12),          # slightly green Pyrex
    "ring": m.Look(m.rgb(0.62, 0.70, 0.66), roughness=0.20),
    "yoke": m.Look(m.rgb(0.62, 0.63, 0.61), metallic=0.7, roughness=0.35),  # plated flat steel
    "clamp": m.Look(m.rgb(0.28, 0.28, 0.29), metallic=0.5, roughness=0.4),
    "knob": m.Look(m.rgb(0.10, 0.10, 0.10), roughness=0.5),            # black thumbscrews, not red
    "run": m.Look(m.rgb(0.10, 0.10, 0.10), roughness=0.7),             # integral cast holders
    "alu": m.Look(m.rgb(0.72, 0.73, 0.74), metallic=0.8, roughness=0.3),
    "red": m.Look(m.rgb(0.82, 0.05, 0.06), roughness=0.35),
    "blue": m.Look(m.rgb(0.08, 0.22, 0.70), roughness=0.35),
    "wood": m.Look(m.rgb(0.45, 0.32, 0.18), roughness=0.8),
    "cable": m.Look(m.rgb(0.06, 0.06, 0.06), roughness=0.7),
}

_cn = [0]


def col(mesh):
    _cn[0] += 1
    return m.col_hull(f"c{_cn[0]}", mesh)


# ---- fixture body (mechanism frame), origin at (CX, CY, TOP) ----
# Local: barrel along +Z, rear cap on the table, lens face at z = LENS_Z.
# Shortened vs the real 190 mm axis (REACH); diameter ~ the real 4.25 in width.
body = m.cylinder(0.052, 0.048, (0.0, 0.0, 0.032), axis="z", segments=22)
rear = m.cylinder(0.056, 0.016, (0.0, 0.0, 0.008), axis="z", segments=18)
front = m.cylinder(0.050, 0.016, (0.0, 0.0, LENS_Z - 0.014), axis="z", segments=22)
# baffled vents on the barrel (visual only)
vents = []
for i, ang in enumerate((-0.9, -0.5, 0.5, 0.9)):
    vx, vy = 0.053 * math.cos(ang), 0.053 * math.sin(ang)
    vents.append((f"vent{i}", m.box((0.004, 0.010, 0.018), (vx, vy, 0.034)), "knob"))

# underside focus thumbscrew, sticking out on -x
focus = m.cylinder(0.009, 0.024, (-0.064, 0.0, 0.022), axis="x", segments=12)
focus_tip = m.cylinder(0.014, 0.008, (-0.078, 0.0, 0.022), axis="x", segments=10)
# hinged-door knurled knob on +x (kept off the +y insert path)
door = m.cylinder(0.010, 0.016, (0.062, 0.0, 0.036), axis="x", segments=12)

# 3 in stepped fresnel: a clear disc and concentric ridges on the face
lens = m.cylinder(LENS_R, 0.008, (0.0, 0.0, LENS_Z - 0.004), axis="z", segments=32)
rings = []
for i, r in enumerate((0.034, 0.028, 0.022, 0.016, 0.010, 0.005)):
    rings.append((
        f"ring{i}",
        m.cylinder(r, 0.0016, (0.0, 0.0, LENS_Z + 0.0004 + 0.0005 * i), axis="z", segments=24),
        "ring",
    ))

# Plated flat-steel yoke: a U around the barrel, crossbar on the table at -y
# (away from the +y insert path).
yoke_bar = m.box((0.168, 0.016, 0.010), (0.0, -0.082, 0.007))
arm_l = m.box((0.012, 0.078, 0.010), (0.078, -0.043, 0.007))
arm_r = m.box((0.012, 0.078, 0.010), (-0.078, -0.043, 0.007))
boss_l = m.cylinder(0.012, 0.016, (0.066, 0.0, 0.030), axis="x", segments=12)
boss_r = m.cylinder(0.012, 0.016, (-0.066, 0.0, 0.030), axis="x", segments=12)

# Altman 510-B style C-clamp on the yoke, opening drawn in XY so it reads from above
clamp_back = m.box((0.072, 0.016, 0.028), (0.0, -0.112, 0.016))
clamp_jaw = m.box((0.016, 0.042, 0.024), (0.028, -0.133, 0.016))
clamp_anvil = m.box((0.016, 0.030, 0.024), (-0.028, -0.127, 0.016))
clamp_screw = m.cylinder(0.006, 0.040, (0.0, -0.136, 0.016), axis="x", segments=10)
clamp_tee = m.cylinder(0.006, 0.036, (-0.040, -0.136, 0.016), axis="y", segments=10)

# Colour-frame holders: C-channels open at +y, end stop at -y.
# Opened for PhysX contactOffset (~4 mm). Internal height CHAN_H, not a real 3-5 mm holder.
half = FRAME / 2
MOUTH = 0.070          # +y end of the holders, past the seated +y edge (FRAME/2)
CHAN_H = 0.020         # internal height; opened further so a 4 mm sheet can enter past ~4 mm contactOffset
FLOOR_T = 0.005
LIP_T = 0.003
run_z_floor = LENS_Z + 0.002
run_z = run_z_floor + CHAN_H / 2
run_len = half + MOUTH + 0.012
run_cy = (MOUTH - half) / 2
# Side backs (outside the sheet) and top lips; the +y end is left open (no end wall).
run_l_back = m.box((0.008, run_len, CHAN_H + FLOOR_T), ( half + 0.010, run_cy, run_z_floor + (CHAN_H + FLOOR_T) / 2 - FLOOR_T))
run_r_back = m.box((0.008, run_len, CHAN_H + FLOOR_T), (-half - 0.010, run_cy, run_z_floor + (CHAN_H + FLOOR_T) / 2 - FLOOR_T))
run_l_floor = m.box((0.016, run_len, FLOOR_T), ( half + 0.002, run_cy, run_z_floor - FLOOR_T / 2))
run_r_floor = m.box((0.016, run_len, FLOOR_T), (-half - 0.002, run_cy, run_z_floor - FLOOR_T / 2))
run_l_lip = m.box((0.014, run_len, LIP_T), ( half + 0.003, run_cy, run_z_floor + CHAN_H + LIP_T / 2))
run_r_lip = m.box((0.014, run_len, LIP_T), (-half - 0.003, run_cy, run_z_floor + CHAN_H + LIP_T / 2))
run_end = m.box((FRAME + 0.028, 0.008, CHAN_H + FLOOR_T + LIP_T), (0.0, -half - 0.008, run_z_floor + CHAN_H / 2))

# trailing fibreglass leads (visual), off the rear cap toward -y with the yoke
cable_a = m.cylinder(0.004, 0.040, (0.010, -0.070, 0.006), axis="y", segments=8)
cable_b = m.cylinder(0.004, 0.050, (0.030, -0.110, 0.006), axis="y", segments=8)

fx_parts = [
    ("body", body, "body"),
    ("rear", rear, "body"),
    ("front", front, "body"),
    *vents,
    ("focus", focus, "knob"),
    ("focust", focus_tip, "knob"),
    ("door", door, "knob"),
    ("lens", lens, "lens"),
    *rings,
    ("yokeb", yoke_bar, "yoke"),
    ("arml", arm_l, "yoke"),
    ("armr", arm_r, "yoke"),
    ("bossl", boss_l, "yoke"),
    ("bossr", boss_r, "yoke"),
    ("clback", clamp_back, "clamp"),
    ("cljaw", clamp_jaw, "clamp"),
    ("clanv", clamp_anvil, "clamp"),
    ("clscrew", clamp_screw, "clamp"),
    ("cltee", clamp_tee, "clamp"),
    ("rlb", run_l_back, "run"),
    ("rrb", run_r_back, "run"),
    ("rlf", run_l_floor, "run"),
    ("rrf", run_r_floor, "run"),
    ("rll", run_l_lip, "run"),
    ("rrl", run_r_lip, "run"),
    ("rend", run_end, "run"),
    ("caba", cable_a, "cable"),
    ("cabb", cable_b, "cable"),
]
# Body, yoke, clamp, and the holders themselves collide. Lens and leads stay visual-only.
fx_cols = [
    col(body), col(rear), col(front),
    col(yoke_bar), col(arm_l), col(arm_r),
    col(clamp_back), col(clamp_jaw), col(clamp_anvil),
    col(focus), col(door),
    col(run_l_back), col(run_r_back),
    col(run_l_floor), col(run_r_floor),
    col(run_l_lip), col(run_r_lip),
    col(run_end),
]

LIGHT = m.fixed("light", (CX, CY, TOP), fx_parts, fx_cols, LOOKS, friction=(1.0, 0.8))

# ---- red frame, free, starts flat on the table, clear of the lamp. ----
# Origin = centre of the sheet (mid-thickness).
# Pinch bar on a short neck at the trailing (+y) edge, modelled on the
# header-stand handle. A 32 x 20 x 16 mm bar, centre 18 mm past the sheet and
# 40 mm above the bench. A real 100-CFB tab is a flat pull tab; this is
# chunkier so a straight-down grip can close around it without hitting the
# sheet. Flagged.
HANDLE_Y = half + 0.018
HANDLE_Z = 0.040 - FRAME_T / 2  # world z = 0.040 when the sheet sits on the bench
TAB_Y = HANDLE_Y
TAB_Z = HANDLE_Z
sheet = m.box((FRAME, FRAME, FRAME_T), (0.0, 0.0, 0.0))
gel = m.box((FRAME - 0.014, FRAME - 0.014, GEL_T), (0.0, 0.0, FRAME_T / 2 + GEL_T / 2 - 0.0005))
neck = m.box((0.012, 0.018, 0.028), (0.0, half + 0.006, 0.012))
handle = m.box((0.032, 0.020, 0.016), (0.0, HANDLE_Y, HANDLE_Z))
# Thin sheet collider, so the plate can still enter the holders; the bar stays
# on the trailing edge, outside the runners when seated.
RED = m.free(
    "red",
    (START_X, START_Y, TOP + FRAME_T / 2),
    [("sheet", sheet, "alu"), ("gel", gel, "red"), ("neck", neck, "alu"), ("handle", handle, "alu")],
    [col(sheet), col(neck), col(handle)],
    LOOKS,
    mass=0.10,
    friction=(0.55, 0.45),
    yaw_deg=0.0,
    torsional_patch=0.010,
    solver_iters=48,
)

# Blue distractor lying face-up in a shallow gel box, +x of the lamp (off the +y path).
BOX_POS = (CX + 0.16, CY, TOP)
TRAY = m.fixed(
    "tray",
    BOX_POS,
    [("tray", m.box((0.12, 0.12, 0.008), (0.0, 0.0, 0.004)), "wood")],
    [m.col_box("tray_c", (0.12, 0.12, 0.008), (0.0, 0.0, 0.004))],
    LOOKS,
)
BLUE = m.free(
    "blue",
    (BOX_POS[0], BOX_POS[1], TOP + 0.008 + FRAME_T / 2),
    [
        ("sheet", m.box((FRAME, FRAME, FRAME_T), (0.0, 0.0, 0.0)), "alu"),
        ("gel", m.box((FRAME - 0.014, FRAME - 0.014, GEL_T), (0.0, 0.0, FRAME_T / 2 + GEL_T / 2 - 0.0005)), "blue"),
    ],
    [col(m.box((FRAME, FRAME, FRAME_T), (0.0, 0.0, 0.0)))],
    LOOKS,
    mass=0.10,
    friction=(0.6, 0.5),
    yaw_deg=0.0,
)

OBJECTS = [LIGHT, TRAY, BLUE, RED]

SEAT_Z = run_z_floor + FRAME_T / 2  # 0.074
SEAT_XY = 0.008
SEAT_DZ = 0.010
SEAT_TILT = 12.0
# In the holders: on the rail height, lined up in x, and somewhere between the
# mouth and the stop (not still out on the table).
IN_Y = 0.018
IN_Z = 0.012
# Near: over the mouth or over the rails, not yet down in the channel.
NEAR_XY = 0.040
NEAR_Z = 0.030
NEAR_TILT = 20.0


def _clear(mem):
    mem.update(seated=False, in_runners=False, near=False, rest=0, dx=9, dy=9, dz=9, tilt=99, vel=9, clear=False)


TRIAL = hhkit.Trial(on_clear=_clear)


@m.on_reset
def _reset(env):
    print(
        f"[E] reset gel v11 start=({START_X:.3f},{START_Y:.3f}) seat=({CX:.3f},{CY:.3f}) "
        f"seat_z={SEAT_Z:.3f} mouth={MOUTH:.3f} variant={V}",
        flush=True,
    )


@m.on_step
def _log(env):
    if not TRIAL.once():
        return
    st = m.state(env, "red")
    p = np.asarray(st.pos, float)
    r = hhkit.rot(st.quat_xyzw)
    up = r[:, 2]
    up_err = math.degrees(math.acos(max(-1.0, min(1.0, float(up[2])))))
    dx, dy, dz = p[0] - CX, p[1] - CY, p[2] - (TOP + SEAT_Z)
    vel = float(np.linalg.norm(st.lin_vel))
    seated = (
        abs(dx) < SEAT_XY
        and abs(dy) < SEAT_XY
        and abs(dz) < SEAT_DZ
        and up_err < SEAT_TILT
    )
    # Entered the holders and left the start mark, but not yet on the stop.
    # Lower bound on y is the seated window, so there is no 3-5 mm hole.
    in_runners = (
        not seated
        and SEAT_XY <= dy <= MOUTH + 0.010
        and abs(dx) < IN_Y
        and abs(dz) < IN_Z
        and up_err < SEAT_TILT
    )
    near = (
        not seated
        and not in_runners
        and abs(p[1] - (CY + MOUTH / 2)) < NEAR_XY
        and abs(dx) < NEAR_XY
        and abs(p[2] - (TOP + SEAT_Z)) < NEAR_Z
        and up_err < NEAR_TILT
    )
    grips = hhkit.grippers(env)
    lefts = [g for g in grips if float(np.asarray(g["tcp"], float)[1]) > 0.0]
    if lefts:
        tcp = np.asarray(lefts[0]["tcp"], float)
        dmin = float(np.linalg.norm(tcp - p))
        tcp_h = float(tcp[2] - TOP)
        clear = dmin >= 0.16 and tcp_h >= 0.155
    else:
        dmin, clear = 9.0, False
    rest_ok = vel < 0.03 and seated and clear
    TRIAL.mem["rest"] = TRIAL.mem.get("rest", 0) + 1 if rest_ok else 0
    TRIAL.mem.update(
        seated=seated, in_runners=in_runners, near=near,
        tilt=round(up_err, 1),
        dx=round(dx, 4), dy=round(dy, 4), dz=round(dz, 4),
        vel=round(vel, 4), clear=clear, dmin=round(dmin, 3),
        x=round(p[0], 4), y=round(p[1], 4), z=round(p[2] - TOP, 4),
    )
    n = TRIAL.step
    if n in (1, 2, 5) or n % 15 == 0 or seated or in_runners or near:
        g0 = lefts[0]["tcp"] if lefts else (0, 0, 0)
        print(
            f"[E] n {n} red ({p[0]:.3f},{p[1]:.3f},{(p[2]-TOP)*1000:.1f}mm) "
            f"dxyz ({dx*1000:.1f},{dy*1000:.1f},{dz*1000:.1f}) "
            f"up {up_err:.1f} near={near} in={in_runners} seat={seated} "
            f"rest={TRIAL.mem['rest']} clear={int(clear)} "
            f"tcpL ({g0[0]:.3f},{g0[1]:.3f},{g0[2]-TOP:.3f})",
            flush=True,
        )


def score(objects):
    """No gap: seated (and not yet clear) is 0.5; in the holders short of the
    stop is also 0.5; near the mouth is 0.25; the start mark is 0."""
    mm = TRIAL.mem or {}
    if mm.get("seated") and mm.get("clear") and mm.get("rest", 0) >= 20:
        return 1.0
    if mm.get("seated") or mm.get("in_runners"):
        return 0.5
    if mm.get("near"):
        return 0.25
    return 0.0


def success(objects):
    return score(objects) >= 1.0


def distance(objects):
    mm = TRIAL.mem or {}
    return float(abs(mm.get("dx", 9.0)) + abs(mm.get("dy", 9.0)) + abs(mm.get("dz", 9.0)))


# Pinch the pull tab, lift, align with the open mouth, lower in, slide to the stop.
REST_R = (0.20, -0.30, TOP + 0.18)
REST_L = (0.20, 0.30, TOP + 0.18)
YAW = 0.0


def tab_xyz(origin_x, origin_y, origin_z):
    """Pinch-bar centre in world when the frame origin is at (origin_x, origin_y, TOP+origin_z)."""
    return origin_x, origin_y + TAB_Y, TOP + origin_z + TAB_Z


START_Z = FRAME_T / 2
TX, TY_START, TZ_START = tab_xyz(START_X, START_Y, START_Z)
# Lower while the leading edge is still clear of the runner ends, then slide in
# at runner height. Lowering over TY_MOUTH (frame centre at the mouth) put the
# sheet on top of the lips in v9.
RUNNER_END_Y = CY + MOUTH + 0.006  # +y end of the floor/lip boxes
CLEAR_Y = RUNNER_END_Y + (FRAME / 2) + 0.016
MOUTH_Y = CY + MOUTH - 0.012
_, TY_CLEAR, TZ_SEAT = tab_xyz(CX, CLEAR_Y, SEAT_Z)
_, TY_MOUTH, _ = tab_xyz(CX, MOUTH_Y, SEAT_Z)
_, TY_SEAT, _ = tab_xyz(CX, CY, SEAT_Z)
_, TY_PUSH, _ = tab_xyz(CX, CY - 0.006, SEAT_Z)
ZG_START = TZ_START + PAD
ZG_GRIP = ZG_START - 0.010  # drop around the bar, as on the winch handle
# v10 lowered to ZG_SEAT and the frame sat at ~69 mm, under the 72 mm floors, then
# hit the runner ends and dropped. Slide at mid-channel height (empirical grip
# offset is ~54 mm, a few mm more than TAB_Z+PAD).
APPROACH_Z = run_z_floor + 0.010  # 0.082, mid-ish in the 20 mm channel
ZG_SLIDE = TOP + APPROACH_Z + TAB_Z + PAD + 0.004
ZG_SEAT = TZ_SEAT + PAD + 0.004
ZG_LIFT = TOP + 0.175
ZG_HIGH = TOP + 0.200


def plan_demo():
    return {
        "left": [
            Waypoint(2.0, (TX, TY_START, ZG_HIGH), FINGER_OPEN, "high over the red frame, fingers open", yaw=YAW),
            Waypoint(1.2, (TX, TY_START, ZG_START + 0.010), FINGER_OPEN, "down, still open", yaw=YAW),
            Waypoint(0.8, (TX, TY_START, ZG_GRIP), FINGER_OPEN, "fingers around the pull tab", yaw=YAW),
            Waypoint(0.6, (TX, TY_START, ZG_GRIP), FINGER_CLOSED, "pinch the tab", yaw=YAW),
            Waypoint(0.8, (TX, TY_START, ZG_LIFT), FINGER_CLOSED, "lift off the table", yaw=YAW),
            Waypoint(0.5, (TX, TY_START, ZG_LIFT), FINGER_CLOSED, "hold the lift", yaw=YAW),
            Waypoint(1.0, (TX, TY_CLEAR, ZG_LIFT), FINGER_CLOSED, "still clear of the open holders", yaw=YAW),
            Waypoint(1.4, (TX, TY_CLEAR, ZG_SLIDE), FINGER_CLOSED, "lower to mid-channel height, still clear", yaw=YAW),
            Waypoint(0.6, (TX, TY_CLEAR, ZG_SLIDE), FINGER_CLOSED, "hold the height", yaw=YAW),
            Waypoint(2.2, (TX, TY_PUSH, ZG_SLIDE), FINGER_CLOSED, "slide into the holders, to the stop", yaw=YAW),
            Waypoint(0.8, (TX, TY_PUSH, ZG_SEAT), FINGER_CLOSED, "ease down onto the runner floors", yaw=YAW),
            Waypoint(1.0, (TX, TY_PUSH, ZG_SEAT), FINGER_CLOSED, "hold seated", yaw=YAW),
            Waypoint(0.6, (TX, TY_PUSH, ZG_SEAT), FINGER_OPEN, "release", yaw=YAW),
            Waypoint(1.0, (TX, TY_PUSH, ZG_HIGH), FINGER_OPEN, "up clear", yaw=YAW),
            Waypoint(1.4, REST_L, FINGER_OPEN, "rest", yaw=YAW),
        ],
        "right": [Waypoint(14.0, REST_R, FINGER_OPEN, "stay", yaw=0.0)],
    }


def plan_naive():
    park = (TX + 0.03, TY_START, ZG_START)
    return {
        "left": [
            Waypoint(2.0, (TX, TY_START, ZG_HIGH), FINGER_OPEN, "high over the red frame, fingers open", yaw=YAW),
            Waypoint(1.2, (TX, TY_START, ZG_START + 0.010), FINGER_OPEN, "down, still open", yaw=YAW),
            Waypoint(0.8, (TX, TY_START, ZG_GRIP), FINGER_OPEN, "fingers around the pull tab", yaw=YAW),
            Waypoint(0.6, (TX, TY_START, ZG_GRIP), FINGER_CLOSED, "pinch the tab", yaw=YAW),
            Waypoint(0.8, (TX, TY_START, ZG_LIFT), FINGER_CLOSED, "lift", yaw=YAW),
            Waypoint(1.6, (park[0], park[1], ZG_LIFT), FINGER_CLOSED, "carry it away from the lamp", yaw=YAW),
            Waypoint(1.0, park, FINGER_CLOSED, "set it down away from the holders", yaw=YAW),
            Waypoint(0.6, park, FINGER_OPEN, "release", yaw=YAW),
            Waypoint(0.8, (park[0], park[1], ZG_HIGH), FINGER_OPEN, "up", yaw=YAW),
            Waypoint(1.4, REST_L, FINGER_OPEN, "rest", yaw=YAW),
        ],
        "right": [Waypoint(14.0, REST_R, FINGER_OPEN, "stay", yaw=0.0)],
    }


def plan_short():
    # Insert into the mouth but stop about 40 mm short of the seat.
    short_y = CY + 0.040
    _, ty, _ = tab_xyz(CX, short_y, SEAT_Z)
    return {
        "left": [
            Waypoint(2.0, (TX, TY_START, ZG_HIGH), FINGER_OPEN, "high over the red frame, fingers open", yaw=YAW),
            Waypoint(1.2, (TX, TY_START, ZG_START + 0.010), FINGER_OPEN, "down, still open", yaw=YAW),
            Waypoint(0.8, (TX, TY_START, ZG_GRIP), FINGER_OPEN, "fingers around the pull tab", yaw=YAW),
            Waypoint(0.6, (TX, TY_START, ZG_GRIP), FINGER_CLOSED, "pinch the tab", yaw=YAW),
            Waypoint(0.8, (TX, TY_START, ZG_LIFT), FINGER_CLOSED, "lift off the table", yaw=YAW),
            Waypoint(1.0, (TX, TY_CLEAR, ZG_LIFT), FINGER_CLOSED, "still clear of the open holders", yaw=YAW),
            Waypoint(1.4, (TX, TY_CLEAR, ZG_SLIDE), FINGER_CLOSED, "lower to mid-channel height, still clear", yaw=YAW),
            Waypoint(1.4, (TX, ty, ZG_SLIDE), FINGER_CLOSED, "slide only part way, 40 mm short of the stop", yaw=YAW),
            Waypoint(0.6, (TX, ty, ZG_SLIDE), FINGER_OPEN, "release short of the stop", yaw=YAW),
            Waypoint(1.0, (TX, ty, ZG_HIGH), FINGER_OPEN, "up", yaw=YAW),
            Waypoint(1.4, REST_L, FINGER_OPEN, "rest", yaw=YAW),
        ],
        "right": [Waypoint(14.0, REST_R, FINGER_OPEN, "stay", yaw=0.0)],
    }


def demo():
    hold_r = [Waypoint(1.0, REST_R, FINGER_OPEN, "stay", yaw=0.0)]
    if V in ("idle", "hold"):
        return {"left": [Waypoint(14.0, REST_L, FINGER_OPEN, "stay", yaw=0.0)], "right": hold_r}
    if V == "naive":
        return plan_naive()
    if V == "short":
        return plan_short()
    return plan_demo()
