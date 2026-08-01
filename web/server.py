"""Nova Voice Console — FastAPI + Gemini Live API bridge.

Bridges browser audio to the Gemini Live API:
  - browser mic  -> PCM16 mono 16 kHz  -> Live API
  - Live API     -> PCM16 mono 24 kHz  -> browser playback
plus streamed input/output transcripts as JSON text frames.

Run:  python run_console.py      (or)   uvicorn web.server:app --reload
Open: http://localhost:8000
"""
from __future__ import annotations

import asyncio
import contextlib
import hmac
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types

from .briefing import build_briefing
from .nova_voice_prompt import NOVA_VOICE_PROMPT
from agent.voice_tools import VOICE_TOOLS_API, execute_voice_tool
from mcp_servers.comms_server.server import send_admin_alert_email

load_dotenv()

# Windows consoles default to cp1252, where the emoji in the [Orchestrator] prints raise
# UnicodeEncodeError and kill the session coroutine at the FIRST tool call. line_buffering
# matters on Cloud Run: without it, stdout is block-buffered and the [Orchestrator] lines
# never reach the logs in time to be useful.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
# Live model + voice are configurable because the live model is a preview that changes.
LIVE_MODEL = os.getenv("NOVA_LIVE_MODEL", "gemini-3.1-flash-live-preview").strip()
NOVA_VOICE = os.getenv("NOVA_VOICE", "Aoede").strip()  # warm prebuilt voice
# Shared secret required on /ws when the console is exposed beyond localhost (LAN/tunnel).
# Empty = no token check (loopback default). Passed via WS subprotocol, not the URL.
CONSOLE_TOKEN = os.getenv("CONSOLE_TOKEN", "").strip()
# Extra browser origins permitted to open the WebSocket (comma-separated). Same-origin is
# always allowed; this is only for unusual cross-origin hosting.
ALLOWED_ORIGINS = {o.strip() for o in os.getenv("CONSOLE_ALLOWED_ORIGINS", "").split(",") if o.strip()}
# Admin email for security alerts (e.g. rate limit exceeded)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com").strip()
# Max number of queries a single session can make before getting disconnected.
MAX_TURNS_PER_SESSION = int(os.getenv("MAX_TURNS_PER_SESSION", "40"))


def _origin_allowed(ws: "WebSocket") -> bool:
    """CSWSH guard: only same-origin browsers (or an explicit allowlist) may connect."""
    origin = ws.headers.get("origin")
    if not origin:
        return False  # browsers always send Origin on WS; reject if absent
    if urlparse(origin).netloc == ws.headers.get("host", ""):
        return True   # same origin as the page that served the console
    return origin in ALLOWED_ORIGINS


def _token_from_subprotocols(ws: "WebSocket") -> str:
    for sp in ws.scope.get("subprotocols", []):
        if sp.startswith("nova-token-"):
            return sp[len("nova-token-"):]
    return ""

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Nova Voice Console")
_client = genai.Client(api_key=API_KEY) if API_KEY else None


def _live_config() -> types.LiveConnectConfig:
    # Fresh briefing per connection (Tier-2 memory); never let it block a session.
    system_prompt = NOVA_VOICE_PROMPT
    try:
        system_prompt += build_briefing()
    except Exception as exc:
        print(f"[Briefing] skipped: {exc}")
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=system_prompt,
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=NOVA_VOICE)
            )
        ),
        tools=VOICE_TOOLS_API,
        # Stream both sides as text so the UI can show a live transcript.
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict:
    # Deliberately does NOT advertise whether a key is configured (don't help scanners).
    return {"ok": True, "model": LIVE_MODEL, "voice": NOVA_VOICE}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    # Security checks BEFORE accepting the upgrade:
    # 1) CSWSH guard — only same-origin (or allowlisted) browsers.
    if not _origin_allowed(ws):
        await ws.close(code=1008)
        return
    # 2) Shared token (constant-time), carried in the WS subprotocol, not the URL.
    if CONSOLE_TOKEN and not hmac.compare_digest(_token_from_subprotocols(ws), CONSOLE_TOKEN):
        await ws.close(code=1008)
        return
    offered = ws.scope.get("subprotocols", [])
    await ws.accept(subprotocol="nova" if "nova" in offered else None)
    if not _client:
        await ws.send_text(json.dumps({"type": "error",
                                       "message": "GOOGLE_API_KEY not set in .env"}))
        await ws.close()
        return

    turn_count = [0]  # List used to allow mutation inside inner function

    try:
        live_config = await asyncio.to_thread(_live_config)  # briefing does I/O; keep it off the event loop
        async with _client.aio.live.connect(model=LIVE_MODEL, config=live_config) as session:
            await ws.send_text(json.dumps({"type": "status", "state": "connected",
                                           "voice": NOVA_VOICE}))

            async def browser_to_gemini() -> None:
                """Forward mic audio (and optional typed text) from the browser to Gemini."""
                try:
                    while True:
                        msg = await ws.receive()
                        if msg.get("type") == "websocket.disconnect":
                            break
                        data = msg.get("bytes")
                        if data is not None:
                            await session.send_realtime_input(
                                audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                            )
                            continue
                        text = msg.get("text")
                        if text is not None:
                            payload = json.loads(text)
                            if payload.get("type") == "text" and payload.get("text"):
                                # Typed turns use client content (not realtime audio input).
                                await session.send_client_content(
                                    turns=types.Content(
                                        role="user",
                                        parts=[types.Part(text=payload["text"])],
                                    ),
                                    turn_complete=True,
                                )
                except (WebSocketDisconnect, RuntimeError):
                    pass

            async def gemini_to_browser() -> None:
                """Forward Nova's audio + transcripts to the browser, across MANY turns.

                session.receive() yields one turn's stream and then returns; we loop so the
                session stays open for a continuous, hands-free conversation.
                """
                while True:
                    received = False
                    async for response in session.receive():
                        received = True
                        # Raw audio bytes (PCM16 @ 24 kHz)
                        if getattr(response, "data", None):
                            await ws.send_bytes(response.data)

                        # Handle tool calls coming from the model
                        tool_call_batch = getattr(response, "tool_call", None)
                        if tool_call_batch and tool_call_batch.function_calls:
                            responses = []
                            for fc in tool_call_batch.function_calls:
                                # Print to the console for the cinematic demo effect, differentiating tools from Sub-Agents!
                                _sub_agents = {"generate_spiral_homework", "generate_weekly_quiz", "generate_dok_activity"}
                                if fc.name in _sub_agents:
                                    msg = f"🚀 Invoking Agentic Pipeline: {fc.name} ..."
                                else:
                                    msg = f"⚙️ Executing Data Tool: {fc.name} ..."
                                print(f"\n[Orchestrator] {msg}")
                                
                                await ws.send_text(json.dumps({
                                    "type": "transcript",
                                    "role": "system",
                                    "text": msg
                                }))
                                
                                fn_args = dict(fc.args) if fc.args else {}
                                result = await asyncio.to_thread(execute_voice_tool, fc.name, fn_args)
                                
                                if fc.name in _sub_agents:
                                    print(f"[Orchestrator] ✅ Sub-Agent '{fc.name}' returned successfully.")
                                else:
                                    print(f"[Orchestrator] ✅ Data Tool '{fc.name}' returned successfully.")
                                responses.append(types.FunctionResponse(
                                    name=fc.name,
                                    response=result,
                                    id=fc.id,
                                ))
                            await session.send_tool_response(function_responses=responses)
                            continue

                        sc = getattr(response, "server_content", None)
                        if not sc:
                            continue
                        out_tx = getattr(sc, "output_transcription", None)
                        if out_tx and out_tx.text:
                            await ws.send_text(json.dumps(
                                {"type": "transcript", "role": "nova", "text": out_tx.text}))
                        in_tx = getattr(sc, "input_transcription", None)
                        if in_tx and in_tx.text:
                            await ws.send_text(json.dumps(
                                {"type": "transcript", "role": "karrie", "text": in_tx.text}))
                        if getattr(sc, "interrupted", None):
                            await ws.send_text(json.dumps({"type": "interrupted"}))
                        if getattr(sc, "turn_complete", None):
                            turn_count[0] += 1
                            if turn_count[0] > MAX_TURNS_PER_SESSION:
                                print(f"[Security] Rate limit exceeded ({turn_count[0]} turns). Disconnecting client and alerting {ADMIN_EMAIL}.")
                                await ws.send_text(json.dumps({"type": "error", "message": "Rate limit exceeded. Connection closed."}))
                                await asyncio.to_thread(
                                    send_admin_alert_email,
                                    ADMIN_EMAIL,
                                    f"A WebSocket session exceeded the maximum allowed turns ({MAX_TURNS_PER_SESSION}). The connection was forcefully closed to prevent token exhaustion."
                                )
                                await ws.close(code=1008)
                                return
                            await ws.send_text(json.dumps({"type": "turn_complete"}))
                    if not received:
                        await asyncio.sleep(0.05)  # avoid a busy spin between turns

            up = asyncio.create_task(browser_to_gemini())
            down = asyncio.create_task(gemini_to_browser())
            _, pending = await asyncio.wait({up, down}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
    except Exception as exc:  # surface the real error to the UI instead of a silent close
        with contextlib.suppress(Exception):
            await ws.send_text(json.dumps(
                {"type": "error", "message": f"{type(exc).__name__}: {exc}"}))
    finally:
        with contextlib.suppress(Exception):
            await ws.close()


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
