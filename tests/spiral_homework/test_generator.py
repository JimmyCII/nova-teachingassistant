# tests/spiral_homework/test_generator.py
import json
import pytest
from agent.tools.spiral_homework.generator import generate_week_spec
from agent.tools.spiral_homework.models import WeekSpec

_GOOD = {
    "due_date": "9/12", "track": "regular",
    "boxes": [
        {"day": "Monday", "type": "computation", "role": "current", "text": "1 5/6 × 4 1/2"},
        {"day": "Monday", "type": "computation", "role": "review", "text": "246.75 ÷ 2.5 ="},
        {"day": "Tuesday", "type": "word_problem", "role": "review",
         "text": "A turtle swims 7.5 km in 3 hours. Unit rate?"},
        {"day": "Wednesday", "type": "brain_break", "role": "current", "text": ""},
    ],
}

def test_generates_valid_weekspec_from_model_json():
    calls = []
    def fake_call(prompt, model):
        calls.append((prompt, model))
        return "```json\n" + json.dumps(_GOOD) + "\n```"
    week = generate_week_spec("Fractions", ["6.NS.A.1"], ["6.NS.B.3"], "9/12",
                              track="regular", _call=fake_call)
    assert isinstance(week, WeekSpec)
    assert week.due_date == "9/12"
    assert "Fractions" in calls[0][0]  # topic made it into the prompt

def test_retries_once_then_raises_on_garbage():
    attempts = {"n": 0}
    def fake_call(prompt, model):
        attempts["n"] += 1
        return "not json at all"
    with pytest.raises(ValueError):
        generate_week_spec("Fractions", ["6.NS.A.1"], ["6.NS.B.3"], "9/12", _call=fake_call)
    assert attempts["n"] == 2  # one retry
