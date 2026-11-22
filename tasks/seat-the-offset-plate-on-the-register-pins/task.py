"""v2 (stream D): pick a punched A5-scale offset plate from a board beside
the bed (off the pins, with a lateral and yaw offset), line both holes up
over both register pins, and lower it flat on the bed.

The plate is a free rigid body with gravity. The pins collide. PhysX
contactOffset is 4 mm, so the collider holes are looser than the visual
holes; scoring uses the tighter visual/geometric window (flagged).

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
INSTRUCTION = "Put the plate on the pins."

V = hhkit.demo_variant("demo")
PAD = 0.013

# Bed in the table-middle cue zone, ipsilateral.
CX = 0.32
CY = 0.22  # further ipsilateral so the left arm can hold alignment at bed height

PXL = 0.150          # plate length (x), A5-scale
PW = 0.072           # plate width (y); under the 94 mm finger aperture so a downward pinch can surround the edges
PT = 0.012           # visual plate thickness (a thick aluminium stand-in, so a downward pinch can close above the board)
COL_T = 0.020        # collider thickness, well above the board even with 4 mm contactOffset
BED_Z = 0.040        # bed top above the table
PIN_R = 0.007        # visual / colliding pin radius (14 mm diameter)
PIN_H = 0.036        # tall enough to stick through the 20 mm plate and read at 320x176
PIN_DX = 0.045       # pins split along x, centred in y
HOLE_R = 0.010       # visual hole radius
HOLE_COL = 0.018     # collider hole half-width (4 mm contactOffset + a few mm of placement slop)
ON_RAD = 0.008       # geometric "on this pin" window (tighter than the collider hole)
FLAT_Z = 0.003       # seated if the plate centre is within 3 mm of the bed
FLAT_TILT = 10.0     # deg
YAW_OK = 12.0        # deg; holes must stay lined up with the pin pair
START_YAW_DEG = 25.0
START_YAW = math.radians(START_YAW_DEG)
START_OFF_X = -0.020
START_OFF_Y = 0.008

LOOKS = {
    "bed": m.Look(m.rgb(0.18, 0.18, 0.20), metallic=0.4, roughness=0.45),
    "iron": m.Look(m.rgb(0.25, 0.22, 0.20), metallic=0.5, roughness=0.5),
    "pin": m.Look(m.rgb(0.85, 0.86, 0.82), metallic=0.9, roughness=0.2),
    "pintip": m.Look(m.rgb(0.85, 0.20, 0.12), metallic=0.6, roughness=0.3),
    "alu": m.Look(m.rgb(0.70, 0.71, 0.72), metallic=0.8, roughness=0.3),
    "image": m.Look(m.rgb(0.15, 0.42, 0.55), roughness=0.4),
    "mark": m.Look(m.rgb(0.85, 0.15, 0.12), roughness=0.4),
    "ring": m.Look(m.rgb(0.10, 0.10, 0.11), roughness=0.6),
    "wood": m.Look(m.rgb(0.45, 0.32, 0.18), roughness=0.8),
    "outline": m.Look(m.rgb(0.28, 0.20, 0.10), roughness=0.85),
    "yellow": m.Look(m.rgb(0.75, 0.62, 0.12), roughness=0.4),
}

_cn = [0]


def col(mesh):
    _cn[0] += 1
    return m.col_hull(f"c{_cn[0]}", mesh)


def holed_plate(lx, ly, t, holes, nx=36, ny=26):
    """A rectangular plate in xy with circular holes, centred at the origin."""
    xs = np.linspace(-lx / 2, lx / 2, nx)
    ys = np.linspace(-ly / 2, ly / 2, ny)
    dx, dy = xs[1] - xs[0], ys[1] - ys[0]
    pieces = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            cx = 0.5 * (xs[i] + xs[i + 1])
            cy = 0.5 * (ys[j] + ys[j + 1])
            if any((cx - hx) ** 2 + (cy - hy) ** 2 < r * r for hx, hy, r in holes):
                continue
            pieces.append(m.box((dx * 1.03, dy * 1.03, t), (cx, cy, 0.0)))
    return m.join(*pieces)


def plate_colliders():
    """Non-convex box colliders that leave a square gap at each hole.

    Gaps are HOLE_COL (15 mm half-width) so a 7 mm pin can pass given the
    4 mm PhysX contactOffset. Scoring uses the tighter ON_RAD window.
    """
    out = []
    left_w = (-PIN_DX - HOLE_COL) - (-PXL / 2)
    right_w = (PXL / 2) - (PIN_DX + HOLE_COL)
    mid_w = 2 * (PIN_DX - HOLE_COL)
    out.append(m.col_box("pl", (left_w, PW, COL_T), ((-PXL / 2 + left_w / 2), 0.0, 0.0)))
    out.append(m.col_box("pr", (right_w, PW, COL_T), ((PXL / 2 - right_w / 2), 0.0, 0.0)))
    if mid_w > 0.002:
        out.append(m.col_box("pm", (mid_w, PW, COL_T), (0.0, 0.0, 0.0)))
    rail_x = HOLE_COL * 2
    rail_y = PW / 2 - HOLE_COL
    for side, sx in (("l", -PIN_DX), ("r", PIN_DX)):
        for tb, sy in (("t", PW / 2 - rail_y / 2), ("b", -PW / 2 + rail_y / 2)):
            out.append(m.col_box(f"p{side}{tb}", (rail_x, rail_y, COL_T), (sx, sy, 0.0)))
    return out


HOLES = ((PIN_DX, 0.0, HOLE_R), (-PIN_DX, 0.0, HOLE_R))
SHEET = holed_plate(PXL, PW, PT, HOLES)
IMAGE = holed_plate(
    PXL - 0.030,
    PW - 0.030,
    0.0012,
    [(x, y, r + 0.002) for x, y, r in HOLES],
).moved((0.0, 0.0, PT / 2 + 0.0004))
RINGS = []
for i, (hx, hy, r) in enumerate(HOLES):
    RINGS.append(
        (
            f"ring{i}",
            m.cylinder(r + 0.004, 0.0010, (hx, hy, PT / 2 + 0.0007), axis="z", segments=20),
            "ring",
        )
    )
MARKS = [
    ("mk1", m.box((0.010, 0.003, 0.0012), (0.0, PW / 2 - 0.006, PT / 2 + 0.0005)), "mark"),
    ("mk2", m.box((0.010, 0.003, 0.0012), (0.0, -PW / 2 + 0.006, PT / 2 + 0.0005)), "mark"),
    ("mk3", m.box((0.003, 0.010, 0.0012), (PXL / 2 - 0.006, 0.0, PT / 2 + 0.0005)), "mark"),
    ("mk4", m.box((0.003, 0.010, 0.0012), (-PXL / 2 + 0.006, 0.0, PT / 2 + 0.0005)), "mark"),
]

bed = m.box((0.22, 0.16, BED_Z), (0.0, 0.0, BED_Z / 2))
bearer_l = m.cylinder(0.018, 0.16, (0.095, 0.0, BED_Z - 0.002), axis="y", segments=14)
bearer_r = m.cylinder(0.018, 0.16, (-0.095, 0.0, BED_Z - 0.002), axis="y", segments=14)
clamp = m.box((0.016, 0.14, 0.010), (0.095, 0.0, BED_Z + 0.005))
pin_a = m.cylinder(PIN_R, PIN_H, (PIN_DX, 0.0, BED_Z + PIN_H / 2), axis="z", segments=16)
pin_b = m.cylinder(PIN_R, PIN_H, (-PIN_DX, 0.0, BED_Z + PIN_H / 2), axis="z", segments=16)
tip_a = m.cylinder(PIN_R + 0.0005, 0.004, (PIN_DX, 0.0, BED_Z + PIN_H - 0.002), axis="z", segments=12)
tip_b = m.cylinder(PIN_R + 0.0005, 0.004, (-PIN_DX, 0.0, BED_Z + PIN_H - 0.002), axis="z", segments=12)
col_a = m.cylinder(0.012, 0.004, (PIN_DX, 0.0, BED_Z + 0.002), axis="z", segments=12)
col_b = m.cylinder(0.012, 0.004, (-PIN_DX, 0.0, BED_Z + 0.002), axis="z", segments=12)

PRESS = m.fixed(
    "press",
    (CX, CY, TOP),
    [
        ("bed", bed, "bed"),
        ("bl", bearer_l, "iron"),
        ("br", bearer_r, "iron"),
        ("clamp", clamp, "iron"),
        ("pina", pin_a, "pin"),
        ("pinb", pin_b, "pin"),
        ("tipa", tip_a, "pintip"),
        ("tipb", tip_b, "pintip"),
        ("cola", col_a, "pin"),
        ("colb", col_b, "pin"),
    ],
    [
        col(bed),
        col(bearer_l),
        col(bearer_r),
        col(clamp),
        m.col_cylinder("cpa", PIN_R, PIN_H, (PIN_DX, 0.0, BED_Z + PIN_H / 2)),
        m.col_cylinder("cpb", PIN_R, PIN_H, (-PIN_DX, 0.0, BED_Z + PIN_H / 2)),
    ],
    LOOKS,
)

BOX = (CX + 0.00, CY + 0.20, TOP)
BOARD_H = 0.008
BOARD = m.fixed(
    "board",
    BOX,
    [
        ("board", m.box((0.22, 0.050, BOARD_H), (0.0, 0.0, BOARD_H / 2)), "wood"),
        ("outline", m.box((PXL - 0.010, 0.040, 0.0012), (START_OFF_X, START_OFF_Y, BOARD_H + 0.0006)), "outline"),
    ],
    [m.col_box("board_c", (0.22, 0.050, BOARD_H), (0.0, 0.0, BOARD_H / 2))],
    LOOKS,
    yaw_deg=0.0,
)

# Sit on the collider (8 mm), not the thinner visual sheet, so the plate
# does not start intersecting the board.
PLATE_START = (
    BOX[0] + START_OFF_X,
    BOX[1] + START_OFF_Y,
    TOP + BOARD_H + COL_T / 2 + 0.0005,
)
PLATE_PARTS = [("sheet", SHEET, "alu"), ("image", IMAGE, "image")] + RINGS + MARKS
PLATE = m.free(
    "plate",
    PLATE_START,
    PLATE_PARTS,
    plate_colliders(),
    LOOKS,
    mass=0.18,
    friction=(1.0, 0.8),
    yaw_deg=START_YAW_DEG,
    solver_iters=48,
)

SPARE_BOX = (CX - 0.20, CY + 0.20, TOP)
SPARE_BOARD = m.fixed(
    "spareboard",
    SPARE_BOX,
    [("board", m.box((0.16, 0.050, BOARD_H), (0.0, 0.0, BOARD_H / 2)), "wood")],
    [m.col_box("sboard_c", (0.16, 0.050, BOARD_H), (0.0, 0.0, BOARD_H / 2))],
    LOOKS,
)
DIST = m.free(
    "spare",
    (SPARE_BOX[0], SPARE_BOX[1], TOP + BOARD_H + COL_T / 2 + 0.0005),
    [
        ("sheet", m.box((PXL, PW, PT), (0.0, 0.0, 0.0)), "alu"),
        ("image", m.box((PXL - 0.030, PW - 0.030, 0.0012), (0.0, 0.0, PT / 2 + 0.0004)), "yellow"),
    ],
    [m.col_box("spare_c", (PXL, PW, COL_T), (0.0, 0.0, 0.0))],
    LOOKS,
    mass=0.18,
    friction=(0.6, 0.5),
    yaw_deg=20.0,
)

OBJECTS = [PRESS, BOARD, PLATE, SPARE_BOARD, DIST]

PIN_WORLDS = (
    np.array([CX + PIN_DX, CY, TOP + BED_Z]),
    np.array([CX - PIN_DX, CY, TOP + BED_Z]),
)
SEAT_Z = TOP + BED_Z + COL_T / 2
PIN_TOP = TOP + BED_Z + PIN_H


def _clear(mem):
    mem.update(
        seated=False,
        one_pin=False,
        n_pins=0,
        rest=0,
        z=9,
        dz=9,
        r0=9,
        r1=9,
        tilt=99,
        yaw=99,
        vel=9,
        clear=False,
    )


TRIAL = hhkit.Trial(on_clear=_clear)


def _hole_worlds(st):
    pos = np.asarray(st.pos, float)
    R = hhkit.rot(np.asarray(st.quat_xyzw, float))
    h0 = pos + R @ np.array([PIN_DX, 0.0, 0.0])
    h1 = pos + R @ np.array([-PIN_DX, 0.0, 0.0])
    return pos, h0, h1


def _pin_metrics(st):
    pos, h0, h1 = _hole_worlds(st)
    # Unique hole-to-pin assignment: prefer the pairing that puts more
    # holes on pins, then the smaller total residual (a 90+90 vs 180+0
    # tie used to hide a valid one-pin seating).
    d00 = float(np.linalg.norm(h0[:2] - PIN_WORLDS[0][:2]))
    d11 = float(np.linalg.norm(h1[:2] - PIN_WORLDS[1][:2]))
    d01 = float(np.linalg.norm(h0[:2] - PIN_WORLDS[1][:2]))
    d10 = float(np.linalg.norm(h1[:2] - PIN_WORLDS[0][:2]))

    def _n_on(a, b):
        return int(a <= ON_RAD) + int(b <= ON_RAD)

    if _n_on(d01, d10) > _n_on(d00, d11) or (
        _n_on(d01, d10) == _n_on(d00, d11) and d01 + d10 < d00 + d11
    ):
        r0, r1 = d01, d10
    else:
        r0, r1 = d00, d11
    tilt = 0.0
    yaw = 0.0
    vel = 0.0
    try:
        tilt = float(hhkit.tilt_deg(st))
        yaw = abs(float(hhkit.yaw_deg(st)))
        if yaw > 90:
            yaw = 180 - yaw
        vel = float(np.linalg.norm(st.lin_vel))
    except Exception:
        pass
    through = float(pos[2] - COL_T / 2) < PIN_TOP - 0.006  # plate bottom at least 6 mm down the pin
    on0 = r0 <= ON_RAD and through
    on1 = r1 <= ON_RAD and through
    n_pins = int(on0) + int(on1)
    flat = abs(float(pos[2]) - SEAT_Z) <= FLAT_Z and tilt <= FLAT_TILT and yaw <= YAW_OK
    seated = n_pins == 2 and flat
    one_pin = (n_pins == 1) or (n_pins == 2 and not flat)
    return dict(
        seated=seated,
        one_pin=one_pin,
        n_pins=n_pins,
        r0=round(r0, 4),
        r1=round(r1, 4),
        z=round(float(pos[2]), 4),
        dz=round(float(pos[2]) - SEAT_Z, 4),
        tilt=round(tilt, 1),
        yaw=round(yaw, 1),
        vel=round(vel, 4),
    )


@m.on_step
def _log(env):
    if not TRIAL.once():
        return
    st = m.state(env, "plate")
    mm = _pin_metrics(st)
    grips = hhkit.grippers(env)
    if grips:
        dmin = min(
            float(np.linalg.norm(np.asarray(g["tcp"], float) - np.asarray(st.pos, float)))
            for g in grips
        )
        clear = dmin >= 0.03
    else:
        dmin, clear = 9.0, False
    rest_ok = mm["vel"] < 0.03 and mm["seated"] and clear
    TRIAL.mem["rest"] = TRIAL.mem.get("rest", 0) + 1 if rest_ok else 0
    TRIAL.mem.update(**mm, clear=clear, dmin=round(dmin, 3), rest=TRIAL.mem["rest"])
    n = TRIAL.step
    if n in (1, 2, 5) or n % 15 == 0 or mm["seated"] or mm["one_pin"]:
        g0 = grips[0]["tcp"] if grips else (0, 0, 0)
        print(
            f"[D] n {n} plate z={mm['z']:.3f} dz={mm['dz']*1000:.1f}mm "
            f"r={mm['r0']*1000:.1f}/{mm['r1']*1000:.1f}mm tilt={mm['tilt']:.0f} yaw={mm['yaw']:.0f} "
            f"pins={mm['n_pins']} seat={mm['seated']} rest={TRIAL.mem['rest']} "
            f"tcpL ({g0[0]:.3f},{g0[1]:.3f},{g0[2]-TOP:.3f})",
            flush=True,
        )


def score(objects):
    mm = TRIAL.mem or {}
    if mm.get("seated") and mm.get("clear") and mm.get("rest", 0) >= 20:
        return 1.0
    if mm.get("seated"):
        return 0.5
    if mm.get("one_pin"):
        return 0.5
    return 0.0


def success(objects):
    return score(objects) >= 1.0


def distance(objects):
    mm = TRIAL.mem or {}
    return float(abs(mm.get("r0", 9.0)) + abs(mm.get("r1", 9.0)) + abs(mm.get("dz", 9.0)))


REST_R = (0.20, -0.30, TOP + 0.18)
REST_L = (0.20, 0.30, TOP + 0.18)
Z_HIGH = TOP + 0.18
ZG_START = PLATE_START[2] + PAD
# Pads sit 13 mm past the TCP; 11 mm above the plate centre puts them in the 8 mm collider, above the board.
ZG_GRIP = PLATE_START[2] + 0.008
ZG_SEAT = SEAT_Z + PAD
ZG_ABOVE_PINS = TOP + BED_Z + PIN_H + 0.040
# Left-arm downward IK undershoots y by about 25 mm at this reach; aim long so the plate lands on the pins.
AIM_X, AIM_Y = CX, CY + 0.010


def plan_demo():
    sx, sy = PLATE_START[0], PLATE_START[1]
    return [
        Waypoint(2.0, (sx, sy, Z_HIGH), FINGER_OPEN, "high over the plate", yaw=START_YAW),
        Waypoint(1.2, (sx, sy, ZG_GRIP + 0.010), FINGER_OPEN, "down to the plate", yaw=START_YAW),
        Waypoint(0.6, (sx, sy, ZG_GRIP), FINGER_OPEN, "fingers around the edges", yaw=START_YAW),
        Waypoint(0.6, (sx, sy, ZG_GRIP), FINGER_CLOSED, "grip", yaw=START_YAW),
        Waypoint(1.2, (sx, sy, Z_HIGH), FINGER_CLOSED, "lift", yaw=START_YAW),
        Waypoint(1.2, (sx, sy, Z_HIGH), FINGER_CLOSED, "unwind yaw in place", yaw=0.0),
        Waypoint(1.6, (AIM_X, AIM_Y, Z_HIGH), FINGER_CLOSED, "over the bed", yaw=0.0),
        Waypoint(1.2, (AIM_X, AIM_Y, ZG_ABOVE_PINS), FINGER_CLOSED, "above the pins, still clear", yaw=0.0),
        Waypoint(1.0, (AIM_X, AIM_Y, ZG_ABOVE_PINS - 0.015), FINGER_CLOSED, "settle the alignment", yaw=0.0),
        Waypoint(2.0, (AIM_X, AIM_Y, ZG_SEAT - 0.004), FINGER_CLOSED, "lower onto the pins", yaw=0.0),
        Waypoint(0.8, (AIM_X, AIM_Y, ZG_SEAT - 0.004), FINGER_CLOSED, "hold seated", yaw=0.0),
        Waypoint(1.0, (AIM_X, AIM_Y, ZG_SEAT - 0.004), FINGER_OPEN, "let go, still at the plate", yaw=0.0),
        Waypoint(1.2, (AIM_X, AIM_Y, ZG_SEAT - 0.004), FINGER_OPEN, "wait while it settles", yaw=0.0),
        Waypoint(1.0, (AIM_X, AIM_Y, Z_HIGH), FINGER_OPEN, "up clear", yaw=0.0),
        Waypoint(1.4, REST_L, FINGER_OPEN, "rest", yaw=0.0),
    ]


def plan_short():
    sx, sy = PLATE_START[0], PLATE_START[1]
    ox = CX + 2 * PIN_DX  # shift by one hole spacing so only one hole lands on one pin
    return [
        Waypoint(2.0, (sx, sy, Z_HIGH), FINGER_OPEN, "high over the plate", yaw=START_YAW),
        Waypoint(1.2, (sx, sy, ZG_GRIP + 0.010), FINGER_OPEN, "down to the plate", yaw=START_YAW),
        Waypoint(0.6, (sx, sy, ZG_GRIP), FINGER_OPEN, "fingers around the edges", yaw=START_YAW),
        Waypoint(0.6, (sx, sy, ZG_GRIP), FINGER_CLOSED, "grip", yaw=START_YAW),
        Waypoint(1.2, (sx, sy, Z_HIGH), FINGER_CLOSED, "lift", yaw=START_YAW),
        Waypoint(1.2, (sx, sy, Z_HIGH), FINGER_CLOSED, "unwind yaw in place", yaw=0.0),
        Waypoint(1.6, (ox, AIM_Y, Z_HIGH), FINGER_CLOSED, "over one pin only", yaw=0.0),
        Waypoint(1.2, (ox, AIM_Y, ZG_ABOVE_PINS), FINGER_CLOSED, "above one pin", yaw=0.0),
        Waypoint(1.6, (ox, AIM_Y, ZG_SEAT - 0.004), FINGER_CLOSED, "lower onto one pin", yaw=0.0),
        Waypoint(1.0, (ox, AIM_Y, ZG_SEAT - 0.004), FINGER_OPEN, "let go on one pin", yaw=0.0),
        Waypoint(1.0, (ox, AIM_Y, Z_HIGH), FINGER_OPEN, "up", yaw=0.0),
        Waypoint(1.4, REST_L, FINGER_OPEN, "rest", yaw=0.0),
    ]


def plan_naive():
    side = (0.22, 0.30, TOP + 0.18)
    return [
        Waypoint(2.0, side, FINGER_OPEN, "aside, not over the plate", yaw=0.0),
        Waypoint(1.4, REST_L, FINGER_OPEN, "rest", yaw=0.0),
    ]


def demo():
    hold_r = [Waypoint(1.0, REST_R, FINGER_OPEN, "stay", yaw=0.0)]
    if V == "idle":
        return {"left": [Waypoint(12.0, REST_L, FINGER_OPEN, "stay", yaw=0.0)], "right": hold_r}
    if V == "short":
        return {"left": plan_short(), "right": hold_r}
    if V == "naive":
        return {"left": plan_naive(), "right": hold_r}
    return {"left": plan_demo(), "right": hold_r}
