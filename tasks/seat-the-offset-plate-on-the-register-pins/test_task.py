"""Offline checks of task.py (no simulator): python -m pytest -q test_task.py"""

import json
import math
import pathlib
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from yam_arena.task_file import load  # noqa: E402

import hhkit  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
TASK = load(str(HERE / "task.py"))
M = TASK.module


@pytest.fixture(autouse=True)
def fresh():
    M.TRIAL.clear()
    yield


def test_instruction_matches_task_json():
    d = json.loads((HERE / "task.json").read_text())
    assert d["instruction"] == M.INSTRUCTION


def test_task_json_limits():
    d = json.loads((HERE / "task.json").read_text())
    assert len(d["title"]) <= 120
    assert len(d["fidelity"]) <= 500
    assert len(d["scores"]) <= 300
    assert len(d.get("context", "")) <= 1000
    assert len(d.get("scoring", "")) <= 600


def test_plate_starts_off_the_pins():
    assert abs(M.PLATE_START[0] - M.CX) > 0.01 or abs(M.PLATE_START[1] - M.CY) > 0.05
    assert M.START_YAW_DEG >= 15.0
    assert M.PLATE_START[1] > M.CY + 0.08


def test_start_scores_zero():
    st = SimpleNamespace(
        pos=tuple(M.PLATE_START),
        quat_xyzw=tuple(hhkit.yaw_quat(math.radians(M.START_YAW_DEG))),
        lin_vel=(0.0, 0.0, 0.0),
    )
    mm = M._pin_metrics(st)
    assert mm["n_pins"] == 0
    assert mm["seated"] is False
    M.TRIAL.mem.update(**mm, clear=False, rest=0)
    assert M.score({}) == 0.0
    assert M.success({}) is False


def test_pinless_placement_on_the_bed_scores_zero():
    # Flat on the bed, translated so both holes miss both pins.
    st = SimpleNamespace(
        pos=(M.CX + 0.04, M.CY, M.SEAT_Z),
        quat_xyzw=(0.0, 0.0, 0.0, 1.0),
        lin_vel=(0.0, 0.0, 0.0),
    )
    mm = M._pin_metrics(st)
    assert mm["n_pins"] == 0
    assert mm["seated"] is False
    assert mm["one_pin"] is False
    M.TRIAL.mem.update(**mm, clear=True, rest=20)
    assert M.score({}) == 0.0


def test_one_pin_is_half():
    M.TRIAL.mem.update(seated=False, one_pin=True, n_pins=1, clear=True, rest=20)
    assert M.score({}) == 0.5


def test_seated_but_held_is_half():
    M.TRIAL.mem.update(seated=True, one_pin=False, n_pins=2, clear=False, rest=0)
    assert M.score({}) == 0.5


def test_seated_cleared_and_still_is_full():
    st = SimpleNamespace(
        pos=(M.CX, M.CY, M.SEAT_Z),
        quat_xyzw=(0.0, 0.0, 0.0, 1.0),
        lin_vel=(0.0, 0.0, 0.0),
    )
    mm = M._pin_metrics(st)
    assert mm["n_pins"] == 2
    assert mm["seated"] is True
    M.TRIAL.mem.update(**mm, clear=True, rest=20)
    assert M.score({}) == 1.0
    assert M.success({}) is True


def test_undo_after_seating_scores_zero():
    # SCORE_OVER = end: only the final pose counts, so lifting off after a
    # perfect seat does not keep 1.0.
    assert M.SCORE_OVER == "end"
    seated = SimpleNamespace(
        pos=(M.CX, M.CY, M.SEAT_Z),
        quat_xyzw=(0.0, 0.0, 0.0, 1.0),
        lin_vel=(0.0, 0.0, 0.0),
    )
    assert M._pin_metrics(seated)["seated"] is True
    lifted = SimpleNamespace(
        pos=(M.CX, M.CY, M.SEAT_Z + 0.08),
        quat_xyzw=(0.0, 0.0, 0.0, 1.0),
        lin_vel=(0.0, 0.0, 0.0),
    )
    mm = M._pin_metrics(lifted)
    assert mm["seated"] is False
    assert mm["n_pins"] == 0
    M.TRIAL.mem.update(**mm, clear=True, rest=20)
    assert M.score({}) == 0.0


def test_one_hole_on_one_pin_is_half():
    # Plate shifted by one hole spacing: one hole sits on one pin, the
    # other misses. The unique pairing must still count that pin.
    st = SimpleNamespace(
        pos=(M.CX + 2 * M.PIN_DX, M.CY, M.SEAT_Z),
        quat_xyzw=(0.0, 0.0, 0.0, 1.0),
        lin_vel=(0.0, 0.0, 0.0),
    )
    mm = M._pin_metrics(st)
    assert mm["n_pins"] == 1
    assert mm["one_pin"] is True
    assert mm["seated"] is False
    M.TRIAL.mem.update(**mm, clear=True, rest=20)
    assert M.score({}) == 0.5
