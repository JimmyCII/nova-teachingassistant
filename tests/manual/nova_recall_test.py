"""Session B of the profile-memory check: fresh session, recall saved facts.

Usage: python tests/manual/nova_recall_test.py [ws_url]
"""
import asyncio
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import nova_ws_test

nova_ws_test.TURNS = [
    "Hi Nova, it's Karrie.",
    "What do you know about Jim?",
    "And do you remember when I like spiral review homework to be due?",
]

if __name__ == "__main__":
    asyncio.run(nova_ws_test.main())
