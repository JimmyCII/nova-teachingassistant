"""Scripted typed-text conversation with the Nova voice console over its WebSocket.

Manual test harness (not collected by pytest — run it directly against a live server):
    python run_console.py                       # terminal 1
    python tests/manual/nova_ws_test.py         # terminal 2

Usage: python tests/manual/nova_ws_test.py [ws_url]
Reads CONSOLE_TOKEN from the project .env (never printed).
Sends each turn, waits for Nova's turn_complete, prints transcript + system frames.
"""
import asyncio
import json
import sys
from pathlib import Path

import websockets

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def read_token() -> str:
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("CONSOLE_TOKEN="):
            return line.split("=", 1)[1].strip()
    return ""


TURNS = [
    "Hi Nova, it's Karrie.",
    "Can you make this week's spiral homework for me? We're working on dividing fractions right now.",
    "It's due Friday August 7th, school year 2025 to 2026. For review, just pick whatever we covered recently. Regular track please.",
    "Yes, that's right, go ahead.",
]


async def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8000/ws"
    token = read_token()
    subprotocols = ["nova"] + ([f"nova-token-{token}"] if token else [])
    origin = url.replace("ws://", "http://").replace("wss://", "https://").split("/ws")[0]

    nova_line = []  # accumulate Nova transcript fragments per turn

    async with websockets.connect(
        url,
        subprotocols=subprotocols,
        additional_headers={"Origin": origin},
        max_size=None,
    ) as ws:
        turn_iter = iter(TURNS)

        async def send_next() -> bool:
            try:
                turn = next(turn_iter)
            except StopIteration:
                return False
            print(f"\n>>> KARRIE: {turn}", flush=True)
            await ws.send(json.dumps({"type": "text", "text": turn}))
            return True

        connected = False
        idle_deadline = 90  # overall safety per wait
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=idle_deadline)
            except asyncio.TimeoutError:
                print("[test] timed out waiting for server frame", flush=True)
                break
            except websockets.ConnectionClosed as e:
                print(f"[test] connection closed: {e}", flush=True)
                break
            if isinstance(msg, bytes):
                continue  # audio frames — ignore
            frame = json.loads(msg)
            ftype = frame.get("type")
            if ftype == "status":
                print(f"[status] {frame}", flush=True)
                if not connected:
                    connected = True
                    await send_next()
            elif ftype == "transcript":
                role = frame.get("role")
                text = frame.get("text", "")
                if role == "nova":
                    nova_line.append(text)
                elif role == "system":
                    print(f"[TOOL] {text}", flush=True)
                # karrie echo of our typed text is not sent for typed turns; skip
            elif ftype == "turn_complete":
                if nova_line:
                    print(f"NOVA: {''.join(nova_line)}", flush=True)
                    nova_line.clear()
                if not await send_next():
                    print("\n[test] all turns sent; closing.", flush=True)
                    break
            elif ftype == "interrupted":
                pass
            elif ftype == "error":
                print(f"[ERROR] {frame.get('message')}", flush=True)
                break
            else:
                print(f"[frame] {frame}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
