"""
Quick-start runner for TeacherMind.

Usage:
    python run.py

Requirements:
    1. Copy .env.example to .env
    2. Add your GOOGLE_API_KEY (from https://aistudio.google.com)
    3. Optionally add CANVAS_API_URL and CANVAS_API_TOKEN
    4. pip install -r requirements.txt
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.agent import run_agent

if __name__ == "__main__":
    run_agent()
