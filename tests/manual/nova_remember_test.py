"""Session A of the profile-memory check: introduce Jim, save durable facts.

Follow with nova_recall_test.py in a NEW session to verify the facts persist.

Usage: python tests/manual/nova_remember_test.py [ws_url]
"""
import asyncio
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import nova_ws_test

nova_ws_test.TURNS = [
    "Hi Nova, this is Jim — Karrie's husband. I handle your technical setup.",
    "Nova, please remember that: I'm Jim, Karrie's husband, and I take care of your technical side.",
    "Also remember that Karrie likes her spiral review homework due on Thursdays.",
]

if __name__ == "__main__":
    asyncio.run(nova_ws_test.main())
