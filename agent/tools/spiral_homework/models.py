# agent/tools/spiral_homework/models.py
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

Day = Literal["Monday", "Tuesday", "Wednesday", "Thursday"]
BoxType = Literal["computation", "word_problem", "brain_break", "figure_placeholder"]
Role = Literal["current", "review"]
Track = Literal["regular", "accelerated"]

_MATH_TYPES = {"computation", "word_problem"}

class Box(BaseModel):
    day: Day
    type: BoxType
    role: Role = "current"
    text: str = ""
    standard_code: Optional[str] = None
    figure_note: Optional[str] = None

    @field_validator("role", mode="before")
    @classmethod
    def _default_role(cls, v):
        # LLMs sometimes emit role: null (esp. brain_break) — treat as "current".
        return v if v else "current"

class WeekSpec(BaseModel):
    due_date: str
    track: Track = "regular"
    boxes: list[Box] = Field(min_length=1, max_length=24)

    @field_validator("boxes")
    @classmethod
    def _spiral_mix(cls, boxes: list[Box]) -> list[Box]:
        roles = {b.role for b in boxes if b.type in _MATH_TYPES}
        if not ({"current", "review"} <= roles):
            raise ValueError("spiral mix requires at least one 'current' and one 'review' math box")
        return boxes
