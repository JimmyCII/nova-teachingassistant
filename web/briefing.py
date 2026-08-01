"""Session-start briefing (Tier-2 memory).

Built fresh on every WebSocket connect and appended to Nova's system prompt so
she opens the conversation already knowing where Karrie left off — even after a
cold start, on any device.
"""
from datetime import date

from agent.tools.request_logger import get_recent_requests


def build_briefing() -> str:
    today = date.today().strftime("%A, %B %d, %Y")
    parts = [f"Today's date: {today}."]
    try:
        parts.append(get_recent_requests(limit=8))
    except Exception as exc:  # a briefing must never block a session
        parts.append(f"(Recent request log unavailable right now: {exc})")
    return (
        "\n\n## Session briefing (auto-generated when this conversation connected)\n"
        "Use this to pick up where you and Karrie left off — reference it naturally "
        "when relevant, don't recite it. Items with status 'Open' or 'Pending Approval' "
        "are unfinished business you may gently follow up on.\n"
        + "\n".join(parts)
    )
