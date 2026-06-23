"""
TeacherMind: AI Concierge Agent for 6th-Grade Math Teachers

Built with Google Gemini + function calling (ADK-compatible).
Run with: python -m agent.agent
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .tools import (
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

load_dotenv()
console = Console()

# ── Tool Caching Wrappers ──────────────────────────────────────────────────────
# Since Gemini doesn't send the full grade dictionary back in tool calls,
# we cache the grade data here and inject it into the tools automatically.

conversation_grade_data = {}

def load_grade_export_wrapper(filepath: str) -> dict:
    """Load and normalize a Synergy CSV grade export from the teacher's Google Drive.
    
    Args:
        filepath: Path to the Synergy CSV file.
    """
    result = load_grade_export(filepath)
    if "error" not in result:
        conversation_grade_data["current"] = result
    return result

def analyze_grade_trends_wrapper(grade_data_id: str, period: str = None, threshold: float = 0.70) -> dict:
    """Identify students below grade threshold, grouped by class period.
    
    Args:
        grade_data_id: Use 'current' to refer to the loaded grade data.
        period: Class period filter (e.g., 'Period 2'). Omit for all.
        threshold: Grade percentage threshold (default 0.70).
    """
    data = conversation_grade_data.get(grade_data_id, conversation_grade_data.get("current", {}))
    return analyze_grade_trends(data, period, threshold)

def get_at_risk_students_wrapper(grade_data_id: str, period: str = None, threshold: float = 0.70, major_only: bool = True) -> dict:
    """Return students at risk in Major Cluster standards (6.RP, 6.NS, 6.EE).
    
    Args:
        grade_data_id: Use 'current' to refer to the loaded grade data.
        period: Class period filter.
        threshold: Grade threshold (default 0.70).
        major_only: Filter to Major Cluster standards only.
    """
    data = conversation_grade_data.get(grade_data_id, conversation_grade_data.get("current", {}))
    return get_at_risk_students(data, period, threshold, major_only)

def get_class_standard_gaps_wrapper(grade_data_id: str, period: str = None) -> dict:
    """Return class-wide average by AZ Math Standard to identify re-teaching needs.
    
    Args:
        grade_data_id: Use 'current' to refer to the loaded grade data.
        period: Class period filter.
    """
    data = conversation_grade_data.get(grade_data_id, conversation_grade_data.get("current", {}))
    return get_class_standard_gaps(data, period)

# Define the tools we want to provide to the Agent
ADK_TOOLS = [
    load_grade_export_wrapper,
    analyze_grade_trends_wrapper,
    get_at_risk_students_wrapper,
    get_class_standard_gaps_wrapper,
    map_assignment_to_standard,
    get_standard_info,
    get_all_standards,
    get_canvas_assignments,
    get_canvas_modules,
    get_canvas_students,
    draft_parent_communication,
    draft_class_digest,
]

# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are TeacherMind, an AI concierge agent for a 6th-grade Arizona mathematics teacher.

Your role is to help the teacher:
1. Understand which students are struggling and why (by AZ Math Standard)
2. Identify class-wide gaps that need re-teaching
3. Plan upcoming lessons based on Canvas assignments and standard coverage
4. Draft School-Net parent communications (for teacher review — never send automatically)
5. Answer questions about Arizona Mathematics Standards

Key facts:
- The teacher uses Synergy for grades (manual CSV export), Canvas for curriculum, and School-Net for parent communication
- AZ Math Major Clusters for Grade 6: Ratios & Proportional Relationships (6.RP), The Number System (6.NS), Expressions & Equations (6.EE)
- ADE recommends 70% of instructional time on Major Clusters
- Grade threshold for "at risk": 70% (0.70)

Behavior rules:
- Always be specific: name students, name standards, cite scores
- Never send communications automatically — always return drafts for teacher review
- When you flag at-risk students, explain which specific assignments/standards triggered the flag
- If you don't have grade data loaded yet, ask the teacher to provide the CSV file path
- Keep responses concise but actionable

When the teacher greets you or asks what you can do, briefly introduce your 5 core capabilities and ask what they'd like to tackle first."""

# ── Agent Loop ────────────────────────────────────────────────────────────────

def run_agent():
    """Main interactive agent loop using Google ADK."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        console.print("[red]Error:[/red] GOOGLE_API_KEY not set. Copy .env.example to .env and add your key.")
        return

    model_name = os.getenv("AGENT_MODEL", "gemini-2.0-flash")

    from google.adk import Agent

    agent = Agent(
        model=model_name,
        tools=ADK_TOOLS,
        system_instruction=SYSTEM_PROMPT,
    )

    console.print(Panel.fit(
        "[bold blue]TeacherMind[/bold blue] — AI Concierge for 6th-Grade Math Teachers\n"
        "[dim]Type 'quit' or 'exit' to end the session.[/dim]",
        border_style="blue",
    ))
    console.print()

    # The agent.run method in ADK often requires a session ID to maintain history if it doesn't do it automatically.
    # In simpler ADK wrappers, `agent.run(text)` maintains history internally per instance.
    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Session ended.[/dim]")
            break

        if user_input.lower() in {"quit", "exit", "bye"}:
            console.print("[dim]Goodbye! Have a great class.[/dim]")
            break

        if not user_input:
            continue

        try:
            # Dispatch to the ADK agent, which will handle tool calling internally.
            response = agent.run(user_input)
            
            console.print()
            console.print("[bold blue]TeacherMind:[/bold blue]")
            console.print(Markdown(response.text))
            console.print()
        except Exception as e:
            console.print(f"[red]Agent Error:[/red] {e}")

if __name__ == "__main__":
    run_agent()

