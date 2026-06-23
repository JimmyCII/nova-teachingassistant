"""
Tests for grade tools using sample Synergy export.
Run with: python -m pytest tests/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.tools.grade_tools import (
    load_grade_export,
    analyze_grade_trends,
    get_at_risk_students,
    get_class_standard_gaps,
)

SAMPLE_CSV = str(Path(__file__).parent.parent / "sample_data" / "synergy_export_sample.csv")


def test_load_grade_export():
    result = load_grade_export(SAMPLE_CSV)
    assert "error" not in result
    assert len(result["students"]) > 0
    assert len(result["records"]) > 0
    print(f"✓ Loaded {result['summary']['total_students']} students, "
          f"{result['summary']['total_assignments']} assignments")


def test_analyze_grade_trends():
    grade_data = load_grade_export(SAMPLE_CSV)
    result = analyze_grade_trends(grade_data, period="Period 2", threshold=0.70)
    assert "error" not in result
    assert "below_threshold" in result
    print(f"✓ Period 2 class avg: {result['class_avg']}%, "
          f"{result['students_below_threshold']} below 70%")
    for s in result["below_threshold"]:
        print(f"  - {s['student']}: {s['avg_pct']}%")


def test_get_at_risk_students():
    grade_data = load_grade_export(SAMPLE_CSV)
    result = get_at_risk_students(grade_data, period="Period 2")
    assert "error" not in result
    print(f"✓ At-risk students: {result['at_risk_count']}")


def test_get_class_standard_gaps():
    grade_data = load_grade_export(SAMPLE_CSV)
    result = get_class_standard_gaps(grade_data, period="Period 2")
    assert "error" not in result
    print(f"✓ Standard gaps found: {len(result['standard_gaps'])}")
    for gap in result["standard_gaps"]:
        print(f"  - {gap['standard_code']} ({gap['priority']}): {gap['avg_pct']}%")


def test_missing_file():
    result = load_grade_export("nonexistent.csv")
    assert "error" in result
    print("✓ Missing file handled correctly")


if __name__ == "__main__":
    print("=== TeacherMind Tool Tests ===\n")
    test_load_grade_export()
    test_analyze_grade_trends()
    test_get_at_risk_students()
    test_get_class_standard_gaps()
    test_missing_file()
    print("\n✅ All tests passed")
