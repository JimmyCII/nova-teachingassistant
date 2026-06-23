import pytest
from pydantic import ValidationError
from agent.tools.spiral_homework.models import Box, WeekSpec

def _box(day="Monday", type="computation", role="current", text="2 + 2 ="):
    return Box(day=day, type=type, role=role, text=text)

def test_valid_weekspec_with_spiral_mix():
    week = WeekSpec(due_date="9/12", track="regular", boxes=[
        _box(role="current", text="1 5/6 × 4 1/2"),
        _box(role="review", type="word_problem", text="A turtle swims 7.5 km in 3 hours..."),
        Box(day="Tuesday", type="brain_break", role="current", text=""),
    ])
    assert week.due_date == "9/12"
    assert len(week.boxes) == 3

def test_spiral_mix_requires_current_and_review():
    with pytest.raises(ValidationError):
        WeekSpec(due_date="9/12", boxes=[_box(role="current"), _box(role="current")])

def test_rejects_unknown_type():
    with pytest.raises(ValidationError):
        Box(day="Monday", type="essay", role="current", text="x")

def test_brain_break_and_figure_excluded_from_mix_rule():
    # only a brain_break + one current computation -> still needs a review -> should fail
    with pytest.raises(ValidationError):
        WeekSpec(due_date="9/12", boxes=[
            _box(role="current"),
            Box(day="Tuesday", type="brain_break", role="current", text=""),
        ])

def test_role_defaults_to_current_when_null():
    b = Box(day="Monday", type="brain_break", role=None, text="")
    assert b.role == "current"
