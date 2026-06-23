# agent/tools/spiral_homework/generator.py
from __future__ import annotations
import json
import os
import re
from typing import Callable
from .models import WeekSpec

_MODEL = os.getenv("HOMEWORK_MODEL", "gemini-2.5-flash")

_PROMPT = """You create ONE week of a 6th-grade Arizona math teacher's "Spiral Review" homework.
Format: 4 columns (Monday–Thursday), about 14–16 boxes total (~4 per day). Each box is one item.

Spiral mix: about half the math boxes are the CURRENT topic and about half are REVIEW of earlier
standards. Include 2–4 "word_problem" boxes with real-world contexts and rotating FICTIONAL names
(never a real student). Include exactly ONE "brain_break" box (text "" ). For a problem that needs a
picture, use type "figure_placeholder" with a short "figure_note" (e.g. "number line 0-10").
Use plain editable text math (e.g. "1 5/6 × 4 1/2", "z ÷ 6 = 1.5"). NO student data.

current_topic: {topic}
current_standards: {current}
review_standards: {review}
due_date (header label): {due}
track: {track}   (if "accelerated": drop basic computation warm-ups, add more conceptual/algebra)

Return ONLY JSON (no prose) with this exact shape:
{{"due_date": "{due}", "track": "{track}", "boxes": [
  {{"day": "Monday|Tuesday|Wednesday|Thursday",
    "type": "computation|word_problem|brain_break|figure_placeholder",
    "role": "current|review", "text": "...", "standard_code": "6.XX.X.X" or null,
    "figure_note": "..." or null}} ]}}"""

def _call_gemini(prompt: str, model: str) -> str:
    from google import genai  # imported lazily so tests need no network/SDK call
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return client.models.generate_content(model=model, contents=prompt).text

def _extract_json(raw: str) -> dict | None:
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

def generate_week_spec(current_topic: str, current_standards: list[str],
                       review_standards: list[str], due_date: str, track: str = "regular",
                       model: str = _MODEL,
                       _call: Callable[[str, str], str] = _call_gemini) -> WeekSpec:
    prompt = _PROMPT.format(topic=current_topic, current=", ".join(current_standards),
                            review=", ".join(review_standards), due=due_date, track=track)
    last_err = "no response"
    for _ in range(2):
        data = _extract_json(_call(prompt, model))
        if data is not None:
            try:
                return WeekSpec.model_validate(data)
            except Exception as e:  # validation failure -> retry
                last_err = str(e)
    raise ValueError(f"Gemini did not return a valid WeekSpec after retry: {last_err}")
