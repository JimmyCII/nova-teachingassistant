"""
Communication drafting tools for TeacherMind.

Generates School-Net-ready parent messages and class digests
based on grade data and standard gaps.
"""

from __future__ import annotations

import os
from typing import Optional

from google import genai


def _get_client() -> tuple:
    """Return (client, model_name) tuple."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY is not set.")
    return genai.Client(api_key=api_key), os.getenv("AGENT_MODEL", "gemini-2.0-flash")


# ── Templates ──────────────────────────────────────────────────────────────────

CONCERN_PROMPT = """You are a warm, professional 6th-grade math teacher drafting a parent communication
for the School-Net messaging platform.

Write a brief, supportive message (3-4 short paragraphs) to the parent/guardian of {student_name}.

Context:
- Student is currently averaging {avg_pct}% in {period}
- Struggling areas: {struggling_areas}
- Standard(s) of concern: {standard_codes}
- Teacher's tone preference: {tone}
- Additional context from teacher: {extra_context}

Requirements:
- Warm and solution-focused (not punitive)
- Mention 1-2 specific things the student can work on at home
- Offer a brief window for follow-up (office hours, email)
- End with something encouraging
- Keep it under 200 words
- Do NOT include a subject line — just the message body
- Sign off as: "With appreciation, [Teacher Name]"

Draft the message now:"""

DIGEST_PROMPT = """You are a 6th-grade math teacher's assistant. Create a brief weekly class digest
for the teacher's own records (not for parents).

Class data:
- Period: {period}
- Class average: {class_avg}%
- Students below 70%: {below_count} of {total_students}
- Top gaps by standard: {gaps}
- Upcoming assignments: {upcoming}

Write a 3-4 sentence summary the teacher can use to plan the next week:
1. Call out the most urgent standard gap
2. Name the students needing priority attention (max 4 names)
3. Suggest one instructional move for next week
Keep it direct and actionable — no fluff."""


# ── Tools ──────────────────────────────────────────────────────────────────────

def draft_parent_communication(
    student_name: str,
    avg_pct: float,
    period: str,
    struggling_areas: list[str],
    standard_codes: list[str],
    tone: str = "warm and professional",
    extra_context: str = "",
    teacher_name: str = "Your Teacher",
) -> dict:
    """
    Draft a School-Net-ready parent message for a struggling student.

    Args:
        student_name: Student's first name (or full name).
        avg_pct: Student's current grade percentage (0-100).
        period: Class period (e.g., "Period 2").
        struggling_areas: List of assignment/topic names where student is below threshold.
        standard_codes: List of AZ standard codes of concern (e.g., ["6.NS.A.1"]).
        tone: Tone preference ("warm and professional", "urgent", "encouraging").
        extra_context: Any additional context the teacher wants included.
        teacher_name: Teacher's name for sign-off.

    Returns:
        dict with draft_message and metadata.
    """
    try:
        client, model_name = _get_client()
    except EnvironmentError as e:
        return {"error": str(e)}

    prompt = CONCERN_PROMPT.format(
        student_name=student_name,
        avg_pct=round(avg_pct, 1),
        period=period,
        struggling_areas=", ".join(struggling_areas[:3]) if struggling_areas else "recent assignments",
        standard_codes=", ".join(standard_codes) if standard_codes else "general math skills",
        tone=tone,
        extra_context=extra_context or "None provided.",
    ).replace("[Teacher Name]", teacher_name)

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        message = response.text.strip()
        return {
            "student_name": student_name,
            "draft_message": message,
            "word_count": len(message.split()),
            "standards_referenced": standard_codes,
            "note": "Review and personalize before sending via School-Net.",
        }
    except Exception as e:
        return {"error": f"Generation failed: {e}"}


def draft_class_digest(
    period: str,
    class_avg: float,
    total_students: int,
    below_count: int,
    gaps: list[dict],
    upcoming_assignments: list[str],
) -> dict:
    """
    Generate a brief weekly digest for the teacher's planning.

    Args:
        period: Class period label.
        class_avg: Class average percentage.
        total_students: Total students in the period.
        below_count: Students below 70%.
        gaps: List of {standard_code, avg_pct} from get_class_standard_gaps.
        upcoming_assignments: List of upcoming assignment names from Canvas.

    Returns:
        dict with digest text and key stats.
    """
    try:
        client, model_name = _get_client()
    except EnvironmentError as e:
        return {"error": str(e)}

    gaps_str = ", ".join(
        f"{g['standard_code']} ({g['avg_pct']}%)" for g in gaps[:4]
    ) if gaps else "no standard-level data available"

    upcoming_str = ", ".join(upcoming_assignments[:4]) if upcoming_assignments else "none pulled from Canvas"

    prompt = DIGEST_PROMPT.format(
        period=period,
        class_avg=round(class_avg, 1),
        below_count=below_count,
        total_students=total_students,
        gaps=gaps_str,
        upcoming=upcoming_str,
    )

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        digest = response.text.strip()
        return {
            "period": period,
            "digest": digest,
            "stats": {
                "class_avg": class_avg,
                "students_below_70": below_count,
                "total_students": total_students,
                "top_gap": gaps[0]["standard_code"] if gaps else None,
            },
        }
    except Exception as e:
        return {"error": f"Generation failed: {e}"}
