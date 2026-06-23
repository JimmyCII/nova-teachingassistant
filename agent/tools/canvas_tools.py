"""
Canvas LMS tools for TeacherMind.

Uses the Canvas REST API to pull assignments, modules, and student roster.
Requires CANVAS_API_URL and CANVAS_API_TOKEN environment variables.

Get your Canvas API token:
  Canvas → Account → Settings → New Access Token
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

import httpx


# ── Canvas API Client ─────────────────────────────────────────────────────────

def _canvas_get(endpoint: str, params: Optional[dict] = None) -> list | dict:
    """Make a paginated GET request to the Canvas API."""
    base_url = os.getenv("CANVAS_API_URL", "").rstrip("/")
    token = os.getenv("CANVAS_API_TOKEN", "")

    if not base_url or not token:
        return {"error": "Set CANVAS_API_URL and CANVAS_API_TOKEN in your .env file."}

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{base_url}{endpoint}"
    results = []

    with httpx.Client(timeout=30) as client:
        while url:
            try:
                resp = client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    results.extend(data)
                else:
                    return data
                # Handle pagination via Link header
                link = resp.headers.get("Link", "")
                next_url = None
                for part in link.split(","):
                    if 'rel="next"' in part:
                        next_url = part.split(";")[0].strip().strip("<>")
                url = next_url
                params = None  # params already embedded in next URL
            except httpx.HTTPStatusError as e:
                return {"error": f"Canvas API error {e.response.status_code}: {e.response.text}"}
            except Exception as e:
                return {"error": f"Request failed: {e}"}

    return results


# ── Tools ──────────────────────────────────────────────────────────────────────

def get_canvas_courses() -> dict:
    """
    List all active courses for the authenticated teacher.

    Returns:
        dict with courses list containing id, name, course_code.
    """
    data = _canvas_get("/api/v1/courses", params={"enrollment_type": "teacher", "state[]": "available"})
    if isinstance(data, dict) and "error" in data:
        return data

    courses = [
        {
            "id": str(c.get("id")),
            "name": c.get("name"),
            "course_code": c.get("course_code"),
            "students_count": c.get("total_students"),
        }
        for c in data
        if c.get("workflow_state") == "available"
    ]
    return {"courses": courses, "count": len(courses)}


def get_canvas_assignments(course_id: str, days_ahead: int = 14) -> dict:
    """
    Fetch upcoming Canvas assignments with due dates.

    Args:
        course_id: Canvas course ID.
        days_ahead: How many days ahead to look for upcoming assignments (default 14).

    Returns:
        dict with assignments list containing name, due_at, points_possible, description.
    """
    data = _canvas_get(
        f"/api/v1/courses/{course_id}/assignments",
        params={"order_by": "due_at", "per_page": 50},
    )
    if isinstance(data, dict) and "error" in data:
        return data

    now = datetime.now(timezone.utc)
    upcoming = []
    past = []

    for a in data:
        due_raw = a.get("due_at")
        due_str = None
        is_upcoming = False

        if due_raw:
            try:
                due_dt = datetime.fromisoformat(due_raw.replace("Z", "+00:00"))
                due_str = due_dt.strftime("%Y-%m-%d")
                days_until = (due_dt - now).days
                is_upcoming = 0 <= days_until <= days_ahead
            except Exception:
                due_str = due_raw

        entry = {
            "id": str(a.get("id")),
            "name": a.get("name"),
            "due_at": due_str,
            "points_possible": a.get("points_possible"),
            "submission_types": a.get("submission_types", []),
            "published": a.get("published", False),
            "description_snippet": (a.get("description") or "")[:200].strip(),
        }

        if is_upcoming:
            upcoming.append(entry)
        else:
            past.append(entry)

    return {
        "course_id": course_id,
        "upcoming_assignments": upcoming,
        "upcoming_count": len(upcoming),
        "past_assignments": past[:10],  # last 10 past assignments
        "total_assignments": len(data),
    }


def get_canvas_modules(course_id: str) -> dict:
    """
    Fetch Canvas course modules and their items.

    Args:
        course_id: Canvas course ID.

    Returns:
        dict with modules list containing name, position, items.
    """
    modules = _canvas_get(
        f"/api/v1/courses/{course_id}/modules",
        params={"include[]": "items", "per_page": 50},
    )
    if isinstance(modules, dict) and "error" in modules:
        return modules

    result = []
    for m in modules:
        items = [
            {
                "title": item.get("title"),
                "type": item.get("type"),
                "url": item.get("html_url"),
            }
            for item in m.get("items", [])
        ]
        result.append(
            {
                "id": str(m.get("id")),
                "name": m.get("name"),
                "position": m.get("position"),
                "published": m.get("published", False),
                "items": items,
                "item_count": len(items),
            }
        )

    return {"course_id": course_id, "modules": result, "module_count": len(result)}


def get_canvas_students(course_id: str) -> dict:
    """
    Fetch the student roster for a Canvas course.

    Args:
        course_id: Canvas course ID.

    Returns:
        dict with students list containing id, name, sortable_name.
    """
    data = _canvas_get(
        f"/api/v1/courses/{course_id}/users",
        params={"enrollment_type[]": "student", "per_page": 100},
    )
    if isinstance(data, dict) and "error" in data:
        return data

    students = [
        {
            "id": str(s.get("id")),
            "name": s.get("name"),
            "sortable_name": s.get("sortable_name"),
        }
        for s in data
    ]
    return {
        "course_id": course_id,
        "students": students,
        "count": len(students),
    }
