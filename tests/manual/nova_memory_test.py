"""Cross-session memory check: does Nova recall recent work from her briefing?

Run against a FRESH connection (new session = new briefing). Nova should answer
from the session briefing without needing tool calls, referencing the topics in
the request log (e.g. dividing fractions).

Usage: python tests/manual/nova_memory_test.py [ws_url]
"""
import asyncio
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import nova_ws_test

nova_ws_test.TURNS = [
    "Hi Nova, it's Karrie.",
    "Remind me — what have we been working on together recently?",
    "Is there anything still open or waiting on me?",
]

if __name__ == "__main__":
    asyncio.run(nova_ws_test.main())
