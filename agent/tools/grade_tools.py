"""
Grade tools for TeacherMind.

Reads Synergy CSV grade exports and performs trend analysis
mapped against AZ Math Standards.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

# ── Constants ──────────────────────────────────────────────────────────────────

DEFAULT_THRESHOLD = 0.70  # Below this = struggling

# Synergy CSV may use various column names; we normalize them.
COLUMN_ALIASES = {
    "Student Name": "student_name",
    "StudentName": "student_name",
    "Name": "student_name",
    "Student ID": "student_id",
    "StudentID": "student_id",
    "ID": "student_id",
    "Assignment": "assignment_name",
    "Assignment Name": "assignment_name",
    "AssignmentName": "assignment_name",
    "Score": "score",
    "Points Earned": "score",
    "PointsEarned": "score",
    "Max Score": "max_score",
    "Points Possible": "max_score",
    "PointsPossible": "max_score",
    "Date": "date",
    "Due Date": "date",
    "Period": "period",
    "Class Period": "period",
    "Category": "category",
}


# ── Data Models ─────────────────────────────────────────────────────────────────

def _load_standards_map() -> dict:
    """Load keyword→standard mapping from JSON."""
    data_path = Path(__file__).parent.parent / "data" / "standard_keywords.json"
    with open(data_path) as f:
        return json.load(f)["keyword_map"]


# ── Tools (exposed to the agent) ──────────────────────────────────────────────

def load_grade_export(filepath: str) -> dict:
    """
    Load and normalize a Synergy CSV grade export.

    Args:
        filepath: Path to the Synergy CSV file.

    Returns:
        dict with keys:
          - students: list of unique student names
          - periods: list of unique class periods
          - assignments: list of assignment names
          - records: list of grade records as dicts
          - summary: basic stats (total students, total assignments, date range)
    """
    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}"}

    try:
        df = pd.read_csv(path)
    except Exception as e:
        return {"error": f"Could not read CSV: {e}"}

    # Normalize column names
    df = df.rename(columns={k: v for k, v in COLUMN_ALIASES.items() if k in df.columns})

    required = {"student_name", "assignment_name", "score", "max_score"}
    missing = required - set(df.columns)
    if missing:
        return {"error": f"CSV missing required columns: {missing}. Found: {list(df.columns)}"}

    # Clean data
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
    df["max_score"] = pd.to_numeric(df["max_score"], errors="coerce").fillna(1)
    df["pct"] = (df["score"] / df["max_score"]).clip(0, 1)

    if "period" not in df.columns:
        df["period"] = "All"
    if "date" not in df.columns:
        df["date"] = None

    records = df.to_dict(orient="records")

    return {
        "students": sorted(df["student_name"].dropna().unique().tolist()),
        "periods": sorted(df["period"].dropna().unique().tolist()),
        "assignments": sorted(df["assignment_name"].dropna().unique().tolist()),
        "records": records,
        "summary": {
            "total_students": df["student_name"].nunique(),
            "total_assignments": df["assignment_name"].nunique(),
            "date_range": {
                "earliest": str(df["date"].min()) if "date" in df.columns else None,
                "latest": str(df["date"].max()) if "date" in df.columns else None,
            },
        },
    }


def analyze_grade_trends(
    grade_data: dict,
    period: Optional[str] = None,
    threshold: float = DEFAULT_THRESHOLD,
    standard_code: Optional[str] = None,
) -> dict:
    """
    Identify students below threshold, grouped by standard domain.

    Args:
        grade_data: Output from load_grade_export.
        period: Filter to a specific class period (e.g., "Period 2"). None = all.
        threshold: Percentage below which a student is flagged (default 0.70).
        standard_code: Filter to a specific standard (e.g., "6.NS"). None = all.

    Returns:
        dict with:
          - below_threshold: list of {student, avg_pct, assignments_below, standard}
          - class_avg: overall class average
          - by_student: per-student summary
    """
    if "error" in grade_data:
        return grade_data

    records = grade_data["records"]
    df = pd.DataFrame(records)

    if period and period != "All":
        df = df[df["period"] == period]

    if df.empty:
        return {"error": f"No records found for period: {period}"}

    # Per-student averages
    student_avgs = (
        df.groupby("student_name")["pct"]
        .agg(avg_pct="mean", count="count")
        .reset_index()
    )

    below = student_avgs[student_avgs["avg_pct"] < threshold].sort_values("avg_pct")

    below_list = []
    for _, row in below.iterrows():
        student_records = df[df["student_name"] == row["student_name"]]
        low_assignments = student_records[student_records["pct"] < threshold][
            "assignment_name"
        ].tolist()
        below_list.append(
            {
                "student": row["student_name"],
                "avg_pct": round(row["avg_pct"] * 100, 1),
                "assignments_below": low_assignments[:5],  # cap at 5 for brevity
                "total_assignments": int(row["count"]),
            }
        )

    return {
        "period": period or "All",
        "threshold_pct": int(threshold * 100),
        "class_avg": round(float(df["pct"].mean()) * 100, 1),
        "total_students": df["student_name"].nunique(),
        "students_below_threshold": len(below_list),
        "below_threshold": below_list,
        "by_student": student_avgs.rename(
            columns={"avg_pct": "average_pct", "count": "assignment_count"}
        )
        .assign(average_pct=lambda x: (x["average_pct"] * 100).round(1))
        .to_dict(orient="records"),
    }


def get_at_risk_students(
    grade_data: dict,
    period: Optional[str] = None,
    threshold: float = DEFAULT_THRESHOLD,
    major_only: bool = True,
) -> dict:
    """
    Return students at risk, prioritizing Major Cluster standards.

    Args:
        grade_data: Output from load_grade_export.
        period: Class period filter.
        threshold: Grade threshold (default 70%).
        major_only: If True, flag students below threshold on Major Cluster assignments only.

    Returns:
        dict with at_risk list sorted by average score ascending (worst first).
    """
    trends = analyze_grade_trends(grade_data, period=period, threshold=threshold)
    if "error" in trends:
        return trends

    at_risk = trends["below_threshold"]

    return {
        "period": period or "All",
        "threshold_pct": int(threshold * 100),
        "at_risk_count": len(at_risk),
        "at_risk_students": at_risk,
        "note": (
            "Filtered to Major Cluster assignments (6.RP, 6.NS, 6.EE) — "
            "ADE recommends 70% of instructional time on these domains."
            if major_only
            else "All domains included."
        ),
    }


def get_class_standard_gaps(grade_data: dict, period: Optional[str] = None) -> dict:
    """
    Return class-wide average by standard keyword to identify lesson focus areas.

    Maps assignment names to standards using keyword matching, then computes
    average score per standard.

    Args:
        grade_data: Output from load_grade_export.
        period: Class period filter.

    Returns:
        dict with standard_gaps: list of {standard_code, avg_pct, assignment_count}
          sorted ascending (lowest scores first = most urgent).
    """
    if "error" in grade_data:
        return grade_data

    standards_map = _load_standards_map()
    records = grade_data["records"]
    df = pd.DataFrame(records)

    if period and period != "All":
        df = df[df["period"] == period]

    # Tag each assignment with its best-matching standard
    def match_standard(name: str) -> str:
        name_lower = name.lower()
        for std_code, keywords in standards_map.items():
            if any(kw.lower() in name_lower for kw in keywords):
                return std_code
        return "untagged"

    df["standard_code"] = df["assignment_name"].apply(match_standard)
    df["domain"] = df["standard_code"].apply(
        lambda c: c.split(".")[0] + "." + c.split(".")[1] if "." in c else c
    )

    tagged = df[df["standard_code"] != "untagged"]

    if tagged.empty:
        return {
            "note": "No assignments could be automatically mapped to standards. "
                    "Try naming assignments with standard keywords (e.g., 'Fraction Division Quiz 6.NS.A.1').",
            "standard_gaps": [],
        }

    gaps = (
        tagged.groupby("standard_code")["pct"]
        .agg(avg_pct="mean", assignment_count="count")
        .reset_index()
        .sort_values("avg_pct")
    )

    # Add domain priority
    domain_priority = {"6.RP": "major", "6.NS": "major", "6.EE": "major",
                       "6.G": "supporting", "6.SP": "additional"}

    result = []
    for _, row in gaps.iterrows():
        domain = row["standard_code"][:4] if len(row["standard_code"]) >= 4 else row["standard_code"]
        result.append({
            "standard_code": row["standard_code"],
            "domain": domain,
            "priority": domain_priority.get(domain, "unknown"),
            "avg_pct": round(row["avg_pct"] * 100, 1),
            "assignment_count": int(row["assignment_count"]),
        })

    return {
        "period": period or "All",
        "standard_gaps": result,
        "untagged_assignments": df[df["standard_code"] == "untagged"]["assignment_name"].unique().tolist(),
        "tip": "Assignments with standard codes in the name (e.g., '6.NS.A.1 Fraction Division') "
               "will auto-map accurately. Add keywords or codes to improve coverage.",
    }
