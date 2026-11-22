"""Offline checks of task.py (no simulator): python -m pytest -q test_task.py"""

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from yam_arena.task_file import load  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
TASK = load(str(HERE / "task.py"))
M = TASK.module


@pytest.fixture(autouse=True)
def fresh():
    if hasattr(M.TRIAL, "clear"):
        M.TRIAL.clear()
    M.TRIAL.mem = {}
    yield


def test_start_or_idle_scores_zero():
    M.TRIAL.mem = {"seated": False, "in_runners": False, "near": False, "clear": False, "rest": 0}
    assert M.score({}) == 0.0 and M.success({}) is False


def test_near_is_quarter():
    M.TRIAL.mem = {"seated": False, "in_runners": False, "near": True, "clear": False, "rest": 0}
    assert M.score({}) == 0.25


def test_in_runners_short_of_stop_is_half():
    # This is the old 3-5 mm hole: in the holders, not yet seated.
    M.TRIAL.mem = {"seated": False, "in_runners": True, "near": False, "clear": False, "rest": 0, "dy": 0.004}
    assert M.score({}) == 0.5 and M.success({}) is False


def test_seated_but_held_is_half():
    M.TRIAL.mem = {"seated": True, "in_runners": False, "near": False, "clear": False, "rest": 0}
    assert M.score({}) == 0.5


def test_seated_clear_needs_one_second():
    M.TRIAL.mem = {"seated": True, "clear": True, "rest": 19}
    assert M.score({}) == 0.5 and M.success({}) is False


def test_seated_clear_and_still_is_full():
    M.TRIAL.mem = {"seated": True, "clear": True, "rest": 20}
    assert M.score({}) == 1.0 and M.success({}) is True


def test_no_scorer_gap_between_three_and_five_mm():
    # Positions 3 mm and 5 mm from the stop must not fall through to 0.
    for dy in (0.003, 0.004, 0.005, 0.008):
        if dy < M.SEAT_XY:
            M.TRIAL.mem = {"seated": True, "in_runners": False, "near": False, "clear": False, "rest": 0, "dy": dy}
        else:
            M.TRIAL.mem = {"seated": False, "in_runners": True, "near": False, "clear": False, "rest": 0, "dy": dy}
        assert M.score({}) == 0.5, dy


def test_instruction_and_start_are_off_the_lamp():
    assert M.INSTRUCTION == "Put the red gel in the light."
    # Frame centre starts well clear of the open mouth; leading edge is also clear.
    assert M.START_Y - (M.CY + M.MOUTH) > 0.04
    assert (M.START_Y - M.FRAME / 2) - (M.CY + M.MOUTH) > 0.015


def test_task_json_limits():
    d = json.loads((HERE / "task.json").read_text())
    assert len(d["title"]) <= 120
    assert len(d["fidelity"]) <= 500
    assert len(d["scores"]) <= 300
    assert len(d.get("context") or "") <= 1000
    assert d["instruction"] == M.INSTRUCTION
