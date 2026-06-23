# Nova Voice Console (`web/`)

A voice-first "meet Nova" console — talk to Nova and she answers out loud, with an audio-reactive
**Nova Core** orb in Karrie's palette. Built to introduce Nova to Karrie.

```
web/
├── server.py             # FastAPI + WebSocket bridge to the Gemini Live API
├── nova_voice_prompt.py  # Nova's spoken persona (PII-free)
└── static/               # index.html · styles.css · app.js  (the orb console)
```

## Run
```bash
pip install -r requirements.txt          # adds fastapi + uvicorn
# .env must contain GOOGLE_API_KEY (already set)
python run_console.py                     # -> http://localhost:8000
```
Open **http://localhost:8000**, press **Begin**, allow the microphone, and say hi.

## How it works
- Browser captures mic audio → downsamples to **PCM16 / 16 kHz** → WebSocket → Gemini Live API.
- Gemini streams **PCM16 / 24 kHz** audio + transcripts back → browser plays Nova's voice and shows a
  live transcript. The orb reacts to the audio (lavender while listening, gold-amethyst while Nova talks).

## Config (.env, optional)
| Var | Default | Notes |
|-----|---------|-------|
| `NOVA_LIVE_MODEL` | `gemini-3.1-flash-live-preview` | Live model is a **preview** — swap if the API rejects it. |
| `NOVA_VOICE` | `Aoede` | Prebuilt voice (warm). Others: Puck, Charon, Kore, Fenrir, Leda, Orus, Zephyr… |

## Caveats (first-run checklist)
1. **Mic + localhost:** browsers allow mic on `http://localhost`. For any other host you need **HTTPS**.
2. **Model availability:** if you see an error about the model, set `NOVA_LIVE_MODEL` to a live model
   your key/region supports, then refresh.
3. **Voice name:** if the voice is rejected, change `NOVA_VOICE` to one from the list above.
4. **Untested audio path:** the audio capture/playback was written carefully but not yet run on real
   hardware — first run is the real test. `GET /health` confirms the key/model/voice the server sees.
5. **No student PII** ever passes through here; Nova's prompt forbids it.
