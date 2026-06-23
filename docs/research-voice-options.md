# Research — Giving Nova a Voice on Google Cloud

**Date:** 2026-06-20 · **Status:** research only (not built) · **Maps to:** Block #5 (Deployment + UX)

**Question:** Can we give Nova a real speech/voice option on Google Cloud, like the voice mode in the
Claude app? **Answer: yes** — and since TeacherMind already runs on **ADK + Gemini**, we're well
positioned. Two architectures:

## Option A — Gemini **Live API** (native audio) — RECOMMENDED, closest to Claude voice mode
Real-time, bidirectional **voice-in / voice-out**; you talk, Nova talks back, sub-second latency.
**Generally available on Vertex AI (I/O 2026)**, powered by Gemini 2.5 Flash Native Audio.
- **30 HD voices, 24+ languages**; natural intonation. Pick one that fits Nova's warm/playful vibe.
- **No separate STT/TTS pipeline** — audio in, audio out (~100–200 ms less latency per turn).
- Can also process **camera/screen** (~1 FPS) — e.g., Karrie shows a worksheet while talking.
- **ADK supports it natively:** `LiveRequestQueue` for streaming audio + **per-agent voice config**,
  so Nova can have its own designated voice. Natural upgrade from the current text loop.
- Trade-off: the live voice is one of the 30 **preset** HD voices (not a custom clone).

## Option B — Pipeline: Cloud **Speech-to-Text** → Gemini → Cloud **Text-to-Speech (Chirp 3)**
More moving parts, slightly more latency, but **maximum control of the exact voice** — and where Nova
could get a *signature* voice:
- **Chirp 3: HD voices** — 30 styles; pace/pause control; custom pronunciations. ~$30 / 1M chars.
- **Chirp 3: Instant Custom Voice** — clone a voice from **~10 seconds** of audio (EU/US). ~$60 / 1M chars.
  This is how Nova gets a *unique* voice. **Voice cloning of a real person requires consent** (Google
  consent/voice-cloning key).
- Great for non-real-time too (e.g., a "🔊 read this parent note aloud" button).

## Mapping to the goal
| Want | Use |
|------|-----|
| "Talk to Nova on my phone, like Claude voice" | **Live API via ADK** (A) |
| A distinctive / branded Nova voice | **Chirp 3 Instant Custom Voice** (B) |
| Read drafts / weekly digest aloud | **Chirp 3 HD TTS** (B, non-realtime) |
Common pattern: **both** — Live API for conversation, Chirp 3 for specific spoken artifacts.

## Caveats to verify at build time
1. **Custom voice ≠ real-time (today):** Instant Custom Voice is a TTS feature; Live API uses its 30
   presets. A cloned voice in live conversation may need the pipeline (B) — re-check if Live adds
   custom voices.
2. **Consent** required for cloning any real person's voice. Nova's *spirit* doesn't need a real
   person's voice — a warm preset HD voice fits.

## How it plugs into TeacherMind
Today `agent/agent.py` is a text CLI (`rich`). Adding voice means a client that streams audio
(web/mobile) — which is exactly the phone/computer interface in Block #5. Path of least resistance:
ADK Live streaming with a per-agent voice config for Nova.

## Sources
- Gemini Live API GA on Vertex AI — https://cloud.google.com/blog/products/ai-machine-learning/gemini-live-api-available-on-vertex-ai
- Gemini 2.5 Flash Live API — https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash-live-api
- ADK streaming / Live API toolkit — https://google.github.io/adk-docs/streaming/
- ADK audio/images/video — https://google.github.io/adk-docs/streaming/dev-guide/part5/
- Chirp 3 HD voices — https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd
- Chirp 3 Instant Custom Voice — https://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice
