"""Voice Console Tool Registry and Schemas for Live API."""
import json
from google.genai import types as genai_types

from agent.tools import (
    load_grade_export,
    analyze_grade_trends,
    get_at_risk_students,
    get_class_standard_gaps,
    map_assignment_to_standard,
    get_standard_info,
    get_all_standards,
    get_canvas_assignments,
    get_canvas_modules,
    get_canvas_students,
    draft_parent_communication,
    draft_class_digest,
)
from agent.tools.spiral_homework.__main__ import generate_spiral_homework
from agent.tools.request_logger import log_nova_task, update_task_status, get_recent_requests
from agent.tools.weekly_quiz import generate_weekly_quiz
from agent.tools.group_activities import generate_dok_activity
from agent.tools.comms_tools import check_pending_approvals

VOICE_TOOL_REGISTRY = {
    "load_grade_export": load_grade_export,
    "analyze_grade_trends": analyze_grade_trends,
    "get_at_risk_students": get_at_risk_students,
    "get_class_standard_gaps": get_class_standard_gaps,
    "map_assignment_to_standard": map_assignment_to_standard,
    "get_standard_info": get_standard_info,
    "get_all_standards": get_all_standards,
    "get_canvas_assignments": get_canvas_assignments,
    "get_canvas_modules": get_canvas_modules,
    "get_canvas_students": get_canvas_students,
    "draft_parent_communication": draft_parent_communication,
    "draft_class_digest": draft_class_digest,
    "generate_spiral_homework": generate_spiral_homework,
    "log_nova_task": log_nova_task,
    "update_task_status": update_task_status,
    "get_recent_requests": get_recent_requests,
    "generate_weekly_quiz": generate_weekly_quiz,
    "generate_dok_activity": generate_dok_activity,
    "check_pending_approvals": check_pending_approvals,
}

_SCHEMA_DEFS = [
    {
        "name": "load_grade_export",
        "description": "Load and normalize a Synergy CSV grade export from the teacher's Google Drive.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the Synergy CSV file."}
            },
            "required": ["filepath"],
        },
    },
    {
        "name": "analyze_grade_trends",
        "description": "Identify students below grade threshold, grouped by class period.",
        "parameters": {
            "type": "object",
            "properties": {
                "grade_data": {"type": "string", "description": "Pass empty string for current grade data."},
                "period": {"type": "string", "description": "Class period filter (e.g., 'Period 2'). Omit for all."},
                "threshold": {"type": "number", "description": "Grade percentage threshold (default 0.70)."},
            },
        },
    },
    {
        "name": "get_at_risk_students",
        "description": "Return students at risk in Major Cluster standards, sorted by lowest score.",
        "parameters": {
            "type": "object",
            "properties": {
                "grade_data": {"type": "string", "description": "Pass empty string for current grade data."},
                "period": {"type": "string", "description": "Class period filter."},
                "threshold": {"type": "number", "description": "Grade threshold (default 0.70)."},
                "major_only": {"type": "boolean", "description": "Filter to Major Cluster standards only."},
            },
        },
    },
    {
        "name": "get_class_standard_gaps",
        "description": "Return class-wide average by AZ Math Standard to identify which standards need re-teaching.",
        "parameters": {
            "type": "object",
            "properties": {
                "grade_data": {"type": "string", "description": "Pass empty string for current grade data."},
                "period": {"type": "string", "description": "Class period filter."},
            },
        },
    },
    {
        "name": "map_assignment_to_standard",
        "description": "Map an assignment name to the best-matching Arizona Mathematics Standard code.",
        "parameters": {
            "type": "object",
            "properties": {
                "assignment_name": {"type": "string", "description": "Name of the assignment."},
                "description": {"type": "string", "description": "Optional assignment description."},
                "use_llm": {"type": "boolean", "description": "Use Gemini as fallback if no keyword match."},
            },
            "required": ["assignment_name"],
        },
    },
    {
        "name": "get_standard_info",
        "description": "Get detailed information about a specific AZ Math Standard code.",
        "parameters": {
            "type": "object",
            "properties": {
                "standard_code": {"type": "string", "description": "AZ Math standard code."}
            },
            "required": ["standard_code"],
        },
    },
    {
        "name": "get_all_standards",
        "description": "Return all Arizona Grade 6 Mathematics Standards with codes, descriptions, and priority levels.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_canvas_assignments",
        "description": "Fetch upcoming and recent Canvas LMS assignments with due dates for a course.",
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {"type": "string", "description": "Canvas course ID."},
                "days_ahead": {"type": "integer", "description": "How many days ahead to fetch (default 14)."},
            },
            "required": ["course_id"],
        },
    },
    {
        "name": "get_canvas_modules",
        "description": "Fetch Canvas course modules and their curriculum items.",
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {"type": "string", "description": "Canvas course ID."}
            },
            "required": ["course_id"],
        },
    },
    {
        "name": "get_canvas_students",
        "description": "Fetch the student roster for a Canvas course.",
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {"type": "string", "description": "Canvas course ID."}
            },
            "required": ["course_id"],
        },
    },
    {
        "name": "draft_parent_communication",
        "description": "Draft a warm, School-Net-ready parent message for a student who is struggling.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_name": {"type": "string", "description": "Student's name."},
                "avg_pct": {"type": "number", "description": "Student's current grade percentage (0-100)."},
                "period": {"type": "string", "description": "Class period."},
                "struggling_areas": {"type": "array", "items": {"type": "string"}, "description": "Assignment names where student is below threshold."},
                "standard_codes": {"type": "array", "items": {"type": "string"}, "description": "AZ standard codes of concern."},
                "tone": {"type": "string", "description": "Tone: 'warm and professional', 'urgent', 'encouraging'."},
                "extra_context": {"type": "string", "description": "Additional context to include."},
                "teacher_name": {"type": "string", "description": "Teacher name for sign-off."},
            },
            "required": ["student_name", "avg_pct", "period"],
        },
    },
    {
        "name": "draft_class_digest",
        "description": "Generate a brief weekly planning digest for the teacher summarizing class health and next steps.",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "Class period label."},
                "class_avg": {"type": "number", "description": "Class average percentage."},
                "total_students": {"type": "integer", "description": "Total students."},
                "below_count": {"type": "integer", "description": "Students below 70%. (Provide 0 if unknown)."},
            },
            "required": ["period", "class_avg", "total_students", "below_count"],
        },
    },
    {
        "name": "generate_spiral_homework",
        "description": "Generate, render to Excel, and upload a weekly Spiral Homework to Google Drive.",
        "parameters": {
            "type": "object",
            "properties": {
                "current_topic": {"type": "string", "description": "Topic currently being taught."},
                "current_standards": {"type": "array", "items": {"type": "string"}, "description": "List of current AZ standard codes."},
                "review_standards": {"type": "array", "items": {"type": "string"}, "description": "Optional review standard codes. Omit to auto-select from recently logged standards."},
                "due_date": {"type": "string", "description": "Due date label for the top of the homework sheet — plain language is fine (e.g., 'Friday August 7th' or '10/24')."},
                "school_year": {"type": "string", "description": "Optional school year folder for Google Drive (e.g., '2025-2026'). Omit to default to the current school year."},
                "track": {"type": "string", "description": "Track: 'regular' or 'accelerated'."},
            },
            "required": ["current_topic", "current_standards", "due_date"],
        },
    },
    {
        "name": "log_nova_task",
        "description": "Log a new request/task into the Nova Request Log.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Plain language topic requested."},
                "standard_code": {"type": "string", "description": "Mapped AZ standard code."},
                "status": {"type": "string", "description": "Status, should default to 'Open'."},
            },
            "required": ["topic", "standard_code"],
        },
    },
    {
        "name": "update_task_status",
        "description": "Update the status of an existing task in the Nova Request Log (e.g., to 'Completed' or 'Approved').",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The Task_ID of the request to update."},
                "new_status": {"type": "string", "description": "The new status (e.g., 'Completed' or 'Approved')."},
            },
            "required": ["task_id", "new_status"],
        },
    },
    {
        "name": "get_recent_requests",
        "description": "Fetch the most recent requests logged in the Nova Request Log, to recall what standards or topics Karrie has been focusing on.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of recent requests to return (default 5)."}
            }
        },
    },
    {
        "name": "generate_weekly_quiz",
        "description": "Generate a 4-5 question Weekly Quiz at DOK 2 level based on standard codes, run it through the Pedagogy Critic, and save it to Google Drive as a Word Document.",
        "parameters": {
            "type": "object",
            "properties": {
                "standards": {"type": "array", "items": {"type": "string"}, "description": "List of AZ standard codes."},
                "title": {"type": "string", "description": "Title of the quiz (e.g., 'Week 4 Quiz')."},
            },
            "required": ["standards", "title"],
        },
    },
    {
        "name": "generate_dok_activity",
        "description": "Generate a DOK-leveled small group activity (DOK 1-3) based on a topic and standard code.",
        "parameters": {
            "type": "object",
            "properties": {
                "standard": {"type": "string", "description": "AZ standard code."},
                "topic": {"type": "string", "description": "Topic of the activity."},
            },
            "required": ["standard", "topic"],
        },
    },
    {
        "name": "check_pending_approvals",
        "description": "Check if Karrie has approved any pending drafts by moving them into the 03_Approved folder on Google Drive. Updates the Request Log status to 'Approved'.",
        "parameters": {"type": "object", "properties": {}},
    },
]

VOICE_TOOLS_API = [genai_types.Tool(function_declarations=[
    genai_types.FunctionDeclaration(**fd) for fd in _SCHEMA_DEFS
])]

VOICE_SESSION_CACHE = {}

def execute_voice_tool(fn_name: str, fn_args: dict, session_id: str = "default") -> dict:
    if fn_name not in VOICE_TOOL_REGISTRY:
        return {"error": f"Unknown tool: {fn_name}"}
    
    # Handle grade data caching explicitly for the voice session state
    if "grade_data" in fn_args:
        fn_args["grade_data"] = VOICE_SESSION_CACHE.get(session_id, {}).get("grade_export", {})
    
    try:
        result = VOICE_TOOL_REGISTRY[fn_name](**fn_args)
        if fn_name == "load_grade_export" and "error" not in result:
            if session_id not in VOICE_SESSION_CACHE:
                VOICE_SESSION_CACHE[session_id] = {}
            VOICE_SESSION_CACHE[session_id]["grade_export"] = result
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}
