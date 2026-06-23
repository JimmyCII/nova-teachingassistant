"""Spiral Review homework generator (Gemini -> WeekSpec -> .xlsx -> Drive).

Public entry point: `agent.tools.spiral_homework.__main__.generate_spiral_homework`
(or the CLI: `python -m agent.tools.spiral_homework ...`).
"""
# Note: intentionally NO `from .__main__ import ...` here — importing __main__ from
# __init__ triggers a RuntimeWarning when running `python -m agent.tools.spiral_homework`.
